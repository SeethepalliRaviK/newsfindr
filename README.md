# NewsFindr Assistant

🚀 AI-powered personalized news retrieval system

## Overview

NewsFindr is a production-ready application that retrieves, filters, and summarizes news articles based on user interests using:
- **LLM**: Groq (OpenAI/gpt-oss-120b)
- **Search**: DuckDuckGo with intelligent retry logic
- **Database**: SQLite with customer profiles
- **Architecture**: Modular Python with Streamlit web interface

## Features

✅ **User Profiles**: Load interests from SQLite database  
✅ **Smart Search**: Expand interests into targeted queries  
✅ **Web Search**: Real-time DuckDuckGo news integration  
✅ **Credibility Filtering**: LLM-powered source validation  
✅ **News Summarization**: AI-generated briefings with citations  
✅ **Rate Limiting**: Built-in token budget management  
✅ **Error Recovery**: Automatic retry with exponential backoff  

## Project Structure

```
newsfindr-app/
├── newsfindr_app.py           # Streamlit web application
├── newsfindr_notebook.ipynb   # iPython notebook version
├── core/
│   ├── config.py              # Configuration constants
│   ├── models.py              # Pydantic data models
│   └── pipeline.py            # News retrieval pipeline
├── utils/
│   ├── llm.py                 # Groq LLM wrapper with rate limiting
│   ├── database.py            # SQLite operations
│   ├── search.py              # DuckDuckGo search integration
│   └── formatting.py          # Text filtering and summarization
├── data/
│   └── customer.db            # SQLite database
├── requirements.txt           # Python dependencies
├── .streamlit/config.toml     # Streamlit configuration
└── .gitignore                 # Git ignore rules
```

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export GROQ_API_KEY="your-groq-api-key"
```

Or in Streamlit:
- Go to Settings → Add API key in the web interface

### 3. Verify Database

The system auto-detects and copies `customer.db` if not present. If missing, place it in `data/` folder.

## Usage

### Run as Streamlit App

```bash
streamlit run newsfindr_app.py
```

Then visit: `http://localhost:8501`

### Run as iPython Notebook

Open `newsfindr_notebook.ipynb` in Jupyter and run cells sequentially.

### Programmatic Usage

```python
from core.pipeline import query_response

result = query_response(
    email="user@example.com",
    user_query="latest news on artificial intelligence"
)
print(result)
```

## Configuration

Edit `core/config.py` to adjust:

- `TPM_LIMIT`: Groq rate limit (tokens/minute)
- `MAX_RESULTS_PER_QUERY`: Search results per query
- `MODEL_NAME`: LLM model selection
- `USE_AGENT`: Enable/disable ReAct agent mode

## API Keys Required

- **GROQ_API_KEY**: Get from https://console.groq.com

## Database Schema

```sql
CREATE TABLE customers (
    email_id TEXT PRIMARY KEY,
    interests TEXT,  -- Comma-separated interests
    ...
);
```

## Error Handling

- Rate limits: Auto-retry with exponential backoff
- Database errors: Fallback to direct SQL queries
- LLM failures: Fall back to direct pipeline
- Search failures: Retry up to 6 times

## Performance

- **Direct Pipeline**: ~30-60 seconds per query
- **Agent Mode**: ~60-120 seconds per query
- **Token Usage**: ~800-1500 tokens per search

## Security

- API keys never stored in code
- Stored in environment variables or Streamlit Secrets
- .gitignore prevents accidental commits
- Credentials never logged

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `GROQ_API_KEY not set` | Add to environment or Streamlit settings |
| `Database not found` | Place customer.db in data/ folder |
| `Rate limit (429)` | Wait, system auto-retries |
| `No results` | Check DuckDuckGo availability |
| `LLM timeout` | Retry with lower token limit |

## Next Steps

1. **Test Locally**: Run Streamlit app and test with sample users
2. **Deploy**: Use `srk-local-git-streamlit-pipeline` skill for GitHub + Cloud
3. **Monitor**: Check logs and token usage
4. **Scale**: Add more users to database

---

**Status**: ✅ Production Ready  
**Version**: 1.0.0  
**Author**: NewsFindr Team
