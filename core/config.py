"""Configuration settings for NewsFindr application"""

# Groq free-tier rate limits
TPM_LIMIT = 8000  # tokens per minute
TPM_SAFETY = 0.80  # safety factor (80% allocation)
RATE_RETRIES = 6  # maximum retry attempts

# Token budget controls
MAX_INTERESTS = 2  # user interests queried from database
MAX_RESULTS_PER_QUERY = 3  # DuckDuckGo results per query
MAX_BODY_CHARS = 1000  # character limit per result snippet
MAX_RESULTS_TO_FILTER = 8  # results passed to credibility filter
MAX_URLS_TO_SUMMARIZE = 4  # URLs passed to summarization
AGENT_RECURSION_LIMIT = 12  # max ReAct loop steps
LLM_MAX_TOKENS = 2000  # max response tokens

# Model configuration
MODEL_NAME = "openai/gpt-oss-120b"  # Primary model
MODEL_FALLBACK = "llama-3.1-70b-versatile"  # Fallback model

# Database configuration
DB_PATH = "data/customer.db"

# Streamlit configuration
STREAMLIT_PORT = 8501
STREAMLIT_THEME = "light"

# Strategy switch: True = ReAct agent, False = direct pipeline
USE_AGENT = True
