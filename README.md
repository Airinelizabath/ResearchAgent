# Research Brief Agent

An AI research assistant powered by the Google Agent Development Kit (ADK) that investigates queries, gathers web insights, extracts page content, and synthesizes cited research briefs with automated security and validation guardrails.

---

## What It Does

The Research Brief Agent operates a structured research pipeline to ensure accuracy and cite references properly:

1. **Input Guardrails**: Validates the query to block empty prompts, short questions (under 3 characters), and suspected prompt injection attempts.
2. **Web Search**: Queries DuckDuckGo (via the `ddgs` package) to locate 4–6 relevant sources. It enforces a 1.5-second delay between consecutive calls to avoid rate limits and caps search reformulations to a maximum of 2 (3 unique queries total).
3. **Content Extraction**: Fetches and parses webpage text from the top results. Requests use standard browser-like headers (modern User-Agent and languages) to bypass bot blocking, and network failures are handled gracefully by skipping broken pages rather than crashing.
4. **Synthesis & Retries**: Passes findings to the Google Gemini model (`gemini-2.5-flash`) to generate a Markdown brief. Model calls are configured with a custom error handler that translates API 503 errors into retries with exponential backoff (retrying up to 3 times with exactly 2s, 4s, and 8s delays).
5. **Output Guardrails**: Scans the completed brief to verify that at least one inline citation exists in the text and that every citation (e.g., `[1]`) matches a valid URL in the final Sources list. Failing validation prepends an unverified claims warning.

---

## File & Architecture Breakdown

The project structure is split into modular Python files and template resources:

- **[tools.py](file:///home/archeron/ANTIGRAVITY_PROJ/tools.py)**: Contains the core tool functions used by the agent:
  - `search_tool`: Enforces rate delays, query counts, and calls DuckDuckGo.
  - `read_page_tool`: Scrapes pages using `BeautifulSoup` and cleans body text.
  - `reset_search_state`: Clears the query history log between executions.
- **[agent.py](file:///home/archeron/ANTIGRAVITY_PROJ/agent.py)**: Configures the Google ADK `Agent` instance:
  - Defines the system instructions and formatting templates.
  - Declares the custom `Gemini503Error` exception.
  - Registers the `handle_model_error` callback and binds the `RetryConfig` settings.
- **[main.py](file:///home/archeron/ANTIGRAVITY_PROJ/main.py)**: CLI entrypoint and utility file:
  - Exposes interactive prompts and command line flags.
  - Contains `validate_input` and `validate_output` validation guardrails.
  - Executes the agent run asynchronously using `runner.run_async()` so crashes propagate directly to the main thread's exception handler.
- **[app.py](file:///home/archeron/ANTIGRAVITY_PROJ/app.py)**: A FastAPI server that hosts the web interface and exposes a GET `/research` Server-Sent Events (SSE) streaming API.
- **[templates/index.html](file:///home/archeron/ANTIGRAVITY_PROJ/templates/index.html)**: Frontend template designed with deep indigo gradients and glassmorphism. It parses Markdown on the fly via `marked.js` and updates an execution log console.
- **[requirements.txt](file:///home/archeron/ANTIGRAVITY_PROJ/requirements.txt)**: Lists pinned Python dependencies, including `google-adk`, `ddgs`, `fastapi`, `uvicorn`, and `jinja2`.
- **[Dockerfile](file:///home/archeron/ANTIGRAVITY_PROJ/Dockerfile)**: Docker container configuration for FastAPI web deployment.
- **[.dockerignore](file:///home/archeron/ANTIGRAVITY_PROJ/.dockerignore)**: Excludes local environment files, cache folders, and virtual environments from build contexts.
- **[test_tools.py](file:///home/archeron/ANTIGRAVITY_PROJ/test_tools.py)** / **[test_limits.py](file:///home/archeron/ANTIGRAVITY_PROJ/test_limits.py)** / **[test_guardrails.py](file:///home/archeron/ANTIGRAVITY_PROJ/test_guardrails.py)**: Automated verification test harnesses.

---

## Security Guardrails

### 1. Input Validation (`validate_input`)
Before running the agent, the input query is sanitized and verified:
- Rejects empty queries or queries containing only whitespace.
- Rejects queries under 3 characters.
- Detects prompt injection attempts by checking the text against regex patterns looking for commands such as `ignore instructions`, `ignore system prompt`, `bypass instructions`, `system override`, or `reset instructions`. 

### 2. Output Citation Verification (`validate_output`)
After the brief is generated, the layout is checked for structural integrity:
- Splits the text between the main body and the `# Sources` section.
- Extracts all inline references (matching `[1]`, `[2]`, etc.) from the body.
- Matches them against numbers extracted from lines starting with links in the Sources section (matching `[1] https://...`, `1. http://...`, etc.).
- If no citations are found, or if a citation references an out-of-bounds or non-existent index, it flags the brief with the warning: `⚠️ This brief may contain unverified claims`.

---

## Local Setup

### Prerequisites
- Python 3.10 or later
- Access to a Google Gemini API Key

### 1. Install Dependencies
Initialize a virtual environment and install the required libraries:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Credentials
Copy the environment variables template:
```bash
cp .env.example .env
```
Open `.env` and fill in your Gemini API key:
```ini
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Run the CLI Application
To start the agent in interactive mode:
```bash
python main.py
```
Or specify your question directly as an argument:
```bash
python main.py --question "What are the latest developments in image similarity metrics?"
```

### 4. Run the Web Application
To start the FastAPI server:
```bash
python app.py
```
Once started, open **`http://127.0.0.1:8080`** in your browser.

---

## Deployment

The application is fully containerized and ready for cloud deployment.

### Container Build
You can build the Docker container locally:
```bash
docker build -t research-brief-agent .
```

### Cloud Run Deployment
To deploy directly to Google Cloud Run, run:
```bash
gcloud run deploy research-brief-agent \
  --source . \
  --env-vars-file .env \
  --allow-unauthenticated
```
*Live URL: https://research-brief-agent-990655675970.us-central1.run.app*

---

## Limitations & Future Work

- **Search Indexing**: The agent relies on a scraper parser for scraping page bodies, which may occasionally fail on heavy client-side JavaScript sites (future versions could integrate headless headless browser options).
- **Session History**: In the current CLI/single-endpoint layout, research sessions are treated as stateless. Multi-turn historical context could be added by hooking into a persistent database session store.
- No persistent memory across sessions yet
- Not yet exposed as an MCP server or integrated with Agents CLI
