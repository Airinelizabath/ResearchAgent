import os
import sys
import argparse
import asyncio
import re
from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai import types

from agent import create_research_agent
from tools import reset_search_state

# Load environment variables from a .env file if it exists
load_dotenv()

def print_banner():
    banner = """
==================================================
        RESEARCH BRIEF AGENT (Google ADK)
==================================================
    """
    print(banner)

def verify_credentials():
    """Verify that GEMINI_API_KEY is available, or help the user set it."""
    if "GEMINI_API_KEY" not in os.environ:
        print("❌ Error: GEMINI_API_KEY environment variable not found.", file=sys.stderr)
        print("\nTo resolve this:", file=sys.stderr)
        print("1. Set it in your shell environment:", file=sys.stderr)
        print("   export GEMINI_API_KEY='your-api-key-here'", file=sys.stderr)
        print("2. Or create a '.env' file in this directory with the line:", file=sys.stderr)
        print("   GEMINI_API_KEY=your-api-key-here", file=sys.stderr)
        sys.exit(1)

def validate_input(query: str) -> tuple[bool, str]:
    """Validates the input query for basic security and sanity constraints.

    Returns:
        A tuple of (is_valid, error_message).
    """
    if not query or not query.strip():
        return False, "Query cannot be empty."
        
    query_stripped = query.strip()
    if len(query_stripped) < 3:
        return False, "Query must be at least 3 characters long."
        
    # Standard prompt injection patterns (case-insensitive)
    injection_patterns = [
        r"ignore\s+(?:previous|above|system)?\s*instructions",
        r"ignore\s+(?:previous|above|system)?\s*prompt",
        r"bypass\s*instructions",
        r"system\s*override",
        r"you\s+must\s+ignore",
        r"reset\s+instructions"
    ]
    
    for pattern in injection_patterns:
        if re.search(pattern, query_stripped, re.IGNORECASE):
            return False, "Input rejected due to suspected prompt injection attempt."
            
    return True, ""

def validate_output(brief: str) -> tuple[bool, str]:
    """Validates the generated brief to check if it contains valid citations.

    Returns:
        A tuple of (is_valid, log_message).
    """
    if not brief:
        return False, "Brief is empty."

    # Split brief by "sources" section to separate the body citations from the sources list
    parts = re.split(r"(?:##+|\*\*)\s*Sources", brief, flags=re.IGNORECASE)
    body_text = parts[0]
    sources_text = parts[1] if len(parts) > 1 else ""

    # Find citations in the body text (excluding the sources section)
    citations = re.findall(r"\[(\d+)\]", body_text)
    citation_set = {int(c) for c in citations}

    # Find sources declared in the sources section
    # Match patterns like "[1] https://..." or "1. https://..." or "[2] pypi.org"
    source_indexes = re.findall(r"^\s*\[?(\d+)\]?[\s\.\:]+\s*\S+", sources_text, re.MULTILINE)
    source_set = {int(s) for s in source_indexes}

    if not citation_set:
        return False, "Zero inline citations found in the brief body."

    if not source_set:
        return False, "No source items parsed from the Sources section."

    # Check if any cited index in the body doesn't exist in the Sources section
    invalid_citations = citation_set - source_set
    if invalid_citations:
        return False, f"Brief references citation index(es) {list(invalid_citations)} that do not exist in the Sources section."

    return True, ""

async def run_agent(question: str):
    """Orchestrates the agent run, prints intermediate steps, and streams the final brief."""
    print(f"\n🚀 Initiating research for: '{question}'\n")
    
    # Reset search state for a clean run
    reset_search_state()
    
    # Create the agent using the approved config
    agent = create_research_agent()
    
    # Initialize the runner
    runner = InMemoryRunner(agent=agent)
    runner.auto_create_session = True
    
    # Create the initial user message object
    msg = types.Content(
        role="user",
        parts=[types.Part.from_text(text=question)]
    )
    
    # Print header for execution log
    print("----------------- Agent Execution -----------------")
    
    text_started = False
    brief_chunks = []
    
    try:
        # Run the agent asynchronously and iterate over the yielded events.
        # This propagates background exceptions directly to our try-except block.
        async for event in runner.run_async(
            user_id="cli_user",
            session_id="research_session",
            new_message=msg
        ):
            if not event.content or not event.content.parts:
                continue
                
            for part in event.content.parts:
                # Handle tool calls (function execution requests)
                if part.function_call:
                    name = part.function_call.name
                    args = part.function_call.args
                    if name == "search_tool":
                        query = args.get("query", "")
                        print(f"🔍 Searching the web for: '{query}'...")
                    elif name == "read_page_tool":
                        url = args.get("url", "")
                        print(f"📖 Reading content from source: {url}")
                    else:
                        print(f"⚙️ Running tool {name}...")
                        
                # Handle tool execution results (responses)
                elif part.function_response:
                    name = part.function_response.name
                    response = part.function_response.response
                    if name == "search_tool":
                        if isinstance(response, list):
                            if response and "error" in response[0]:
                                print(f"  ❌ Search failed: {response[0]['error']}")
                            else:
                                print(f"  ✅ Retrieved {len(response)} potential sources.")
                    elif name == "read_page_tool":
                        # Surface the actual error details instead of generic "extraction failed"
                        # If the scalar string is wrapped in a dict by ADK serialization, unwrap it
                        extracted_text = response
                        if isinstance(response, dict) and "result" in response:
                            extracted_text = response["result"]
                            
                        if isinstance(extracted_text, str) and not extracted_text.startswith("Error"):
                            print(f"  ✅ Extracted and summarized text content.")
                        else:
                            print(f"  ❌ Webpage extraction failed: {extracted_text}")
                            
                # Handle actual text generation (the brief synthesis)
                elif part.text:
                    if not text_started:
                        print("\n----------------- Research Brief -----------------")
                        text_started = True
                    print(part.text, end="", flush=True)
                    brief_chunks.append(part.text)
                    
        print("\n---------------------------------------------------")
        
        # Output Guardrails Validation
        full_brief = "".join(brief_chunks)
        is_valid_output, output_error = validate_output(full_brief)
        
        if is_valid_output:
            print("✅ Citation check passed")
            print("✅ Research task completed successfully.")
        else:
            print(f"⚠️ Citation check failed: {output_error}")
            print("⚠️ This brief may contain unverified claims")
            print("---------------------------------------------------")
            print("✅ Research task completed with warnings.")
        
    except Exception as e:
        print("\n---------------------------------------------------")
        print(f"\n❌ An error occurred during agent execution: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    print_banner()
    
    parser = argparse.ArgumentParser(description="Research Brief Agent CLI")
    parser.add_argument(
        "--question", "-q", 
        type=str, 
        help="The research question to investigate"
    )
    
    args = parser.parse_args()
    
    # Prompt interactively if the question was not provided via arguments
    question = args.question
    if not question:
        try:
            question = input("📝 Enter your research question: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            sys.exit(0)
            
    # Input Guardrail Validation
    is_valid_input, input_error = validate_input(question)
    if not is_valid_input:
        print(f"❌ Input validation failed: {input_error}", file=sys.stderr)
        sys.exit(1)
        
    print("✅ Input validated")
    verify_credentials()
    
    # Execute the async run_agent wrapper using asyncio.run
    try:
        asyncio.run(run_agent(question))
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
    main()
