import os
import json
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from google.adk.runners import InMemoryRunner
from google.genai import types

from agent import create_research_agent
from tools import reset_search_state
from main import validate_input, validate_output

# Load environment variables from a .env file if it exists
load_dotenv()

app = FastAPI(title="Research Brief Agent API")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Renders the single page HTML form for the research agent."""
    return templates.TemplateResponse(request, "index.html")

@app.get("/research")
async def research(question: str):
    """Executes the research agent and streams progress updates and findings using SSE."""
    
    # 1. Verification of API credentials
    if "GEMINI_API_KEY" not in os.environ:
        async def credential_error_gen():
            payload = {'type': 'error', 'message': 'GEMINI_API_KEY environment variable not found. Please set it in your .env file.'}
            yield f"data: {json.dumps(payload)}\n\n"
        return StreamingResponse(credential_error_gen(), media_type="text/event-stream")

    # 2. Input Guardrail validation
    is_valid_input, input_error = validate_input(question)
    if not is_valid_input:
        async def input_error_gen():
            payload = {'type': 'error', 'message': f'Input Rejected: {input_error}'}
            yield f"data: {json.dumps(payload)}\n\n"
        return StreamingResponse(input_error_gen(), media_type="text/event-stream")

    async def sse_generator():
        # Reset search state for a clean run
        reset_search_state()
        
        # Create agent & runner
        agent = create_research_agent()
        runner = InMemoryRunner(agent=agent)
        runner.auto_create_session = True
        
        msg = types.Content(
            role="user",
            parts=[types.Part.from_text(text=question)]
        )
        
        brief_chunks = []
        
        try:
            init_payload = {'type': 'status', 'message': '🚀 Research Brief Agent initialized.'}
            yield f"data: {json.dumps(init_payload)}\n\n"
            await asyncio.sleep(0.1) # small pause to let UI render initial state
            
            # Execute runner asynchronously and stream events
            async for event in runner.run_async(
                user_id="web_user",
                session_id="web_session",
                new_message=msg
            ):
                if not event.content or not event.content.parts:
                    continue
                    
                for part in event.content.parts:
                    # Capture and stream tool execution calls
                    if part.function_call:
                        name = part.function_call.name
                        args = part.function_call.args
                        if name == "search_tool":
                            query = args.get("query", "")
                            payload = {'type': 'status', 'message': f"🔍 Searching the web for: '{query}'..."}
                            yield f"data: {json.dumps(payload)}\n\n"
                        elif name == "read_page_tool":
                            url = args.get("url", "")
                            payload = {'type': 'status', 'message': f"📖 Reading content from source: {url}"}
                            yield f"data: {json.dumps(payload)}\n\n"
                            
                    # Capture and stream tool execution responses
                    elif part.function_response:
                        name = part.function_response.name
                        response = part.function_response.response
                        if name == "search_tool":
                            if isinstance(response, list) and response and "error" in response[0]:
                                err_msg = response[0]['error']
                                payload = {'type': 'status', 'message': f"  ❌ Search failed: {err_msg}"}
                                yield f"data: {json.dumps(payload)}\n\n"
                            else:
                                count = len(response) if isinstance(response, list) else 0
                                payload = {'type': 'status', 'message': f"  ✅ Retrieved {count} potential sources."}
                                yield f"data: {json.dumps(payload)}\n\n"
                        elif name == "read_page_tool":
                            extracted_text = response
                            if isinstance(response, dict) and "result" in response:
                                extracted_text = response["result"]
                                
                            if isinstance(extracted_text, str) and not extracted_text.startswith("Error"):
                                payload = {'type': 'status', 'message': '  ✅ Extracted and analyzed text content.'}
                                yield f"data: {json.dumps(payload)}\n\n"
                            else:
                                issue_msg = str(extracted_text)[:80]
                                payload = {'type': 'status', 'message': f"  ⚠️ Webpage extraction issue: {issue_msg}..."}
                                yield f"data: {json.dumps(payload)}\n\n"
                                
                    # Stream text chunk generations
                    elif part.text:
                        brief_chunks.append(part.text)
                        payload = {'type': 'text', 'content': part.text}
                        yield f"data: {json.dumps(payload)}\n\n"
            
            # 3. Output Guardrail validation
            full_brief = "".join(brief_chunks)
            is_valid_output, output_error = validate_output(full_brief)
            
            if is_valid_output:
                guardrail_payload = {'type': 'citation_check', 'status': 'success', 'message': '✅ Citation check passed. Claims verified.'}
            else:
                guardrail_payload = {'type': 'citation_check', 'status': 'warning', 'message': f'⚠️ Citation check failed: {output_error}'}
                
            yield f"data: {json.dumps(guardrail_payload)}\n\n"
            
            done_payload = {'type': 'done'}
            yield f"data: {json.dumps(done_payload)}\n\n"
            
        except Exception as e:
            error_payload = {'type': 'error', 'message': f'Execution failed: {str(e)}'}
            yield f"data: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    # Read port from env if present, default to 8080
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting web application server on http://127.0.0.1:{port}")
    uvicorn.run("app:app", host="127.0.0.1", port=port, reload=True)
