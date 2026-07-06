from google.adk import Agent
from google.adk.workflow import RetryConfig
from google.genai.errors import APIError
from tools import search_tool, read_page_tool

# Custom exception specifically for 503 service unavailable errors
class Gemini503Error(Exception):
    """Exception raised specifically when the Gemini API returns a 503 Service Unavailable status."""
    pass

async def handle_model_error(callback_context, llm_request, error):
    """Callback triggered on model call failures. 
    Intercepts 503 errors and translates them to Gemini503Error to trigger retries.
    """
    # Check if the error is a 503 ServerError/APIError
    if isinstance(error, APIError) and error.code == 503:
        raise Gemini503Error(f"Gemini API 503 error encountered: {error.message}")
    elif hasattr(error, "code") and getattr(error, "code") == 503:
        raise Gemini503Error(f"Gemini API 503 error encountered: {error}")
    
    # Other errors are raised directly so they propagate without retrying
    raise error

# System instructions guiding the agent on search, reading, citation, and structural requirements
INSTRUCTION = """You are a Research Brief Agent. Your task is to investigate a research question, gather facts from the web, and write a structured research brief.

Follow these steps exactly:
1. Use `search_tool` with a search query relevant to the user's research question to find 4-6 relevant sources.
2. Review the search results. Select the most relevant URLs (aim for at least 4 and up to 6 unique sources) and fetch their full content using `read_page_tool`. Do not read the same page twice.
3. Read and analyze the content from the pages you fetched.
4. Synthesize your findings and write a structured research brief with the following sections:
   - **Summary**: A high-level overview of the developments and findings regarding the topic.
   - **Key Findings**: A bulleted list of key findings, where EACH bullet point MUST end with one or more inline citations like [1] or [2] matching the source index from the Sources section.
   - **Open Questions**: A bulleted list of unresolved issues, challenges, or future research directions.
   - **Sources**: A numbered list of all unique source URLs used in your research, indexed as [1], [2], etc., corresponding to your inline citations.

Ensure your brief is professional, detailed, and highly objective. Cite only sources that you actually read with the page-reading tool.
"""

def create_research_agent(model_name: str = "gemini-2.5-flash") -> Agent:
    """Creates and returns the Research Brief Agent instance with retry policies.
    
    Args:
        model_name: The Gemini model to use for reasoning.
        
    Returns:
        The configured ADK Agent instance.
    """
    # Retry policy: max 4 attempts (1 original + 3 retries)
    # Delays: 2s, 4s, 8s (exponential backoff factor 2.0, no jitter)
    retry_conf = RetryConfig(
        max_attempts=4,
        initial_delay=2.0,
        backoff_factor=2.0,
        jitter=0.0,
        exceptions=[Gemini503Error]
    )
    
    return Agent(
        name="research_brief_agent",
        model=model_name,
        instruction=INSTRUCTION,
        tools=[search_tool, read_page_tool],
        retry_config=retry_conf,
        on_model_error_callback=handle_model_error
    )
