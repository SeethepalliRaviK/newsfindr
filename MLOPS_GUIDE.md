# NewsFindr - MLOps & DevOps Engineer Guide

Complete operational, monitoring, and maintenance guide for production deployment.

---

## 📋 Table of Contents

1. [System Architecture](#system-architecture)
2. [Deployment Infrastructure](#deployment-infrastructure)
3. [Monitoring & Observability](#monitoring--observability)
4. [Performance Metrics](#performance-metrics)
5. [Rate Limiting & Throttling](#rate-limiting--throttling)
6. [Error Handling & Recovery](#error-handling--recovery)
7. [Scaling Considerations](#scaling-considerations)
8. [Security & Secrets Management](#security--secrets-management)
9. [Maintenance Procedures](#maintenance-procedures)
10. [Cost Optimization](#cost-optimization)
11. [Incident Response](#incident-response)
12. [Deployment Checklist](#deployment-checklist)

---

## System Architecture

### Technology Stack

```
Frontend: Streamlit (Python web framework)
├── Port: 8501 (default)
├── Framework: Streamlit 1.28.0+
└── Deployed: Streamlit Cloud (serverless)

Backend Services:
├── LLM Service: Groq API (groq.com)
│   ├── Model: openai/gpt-oss-120b
│   ├── Fallback: llama-3.1-70b-versatile
│   ├── Rate Limit: 8000 TPM (tokens per minute)
│   └── Auth: API key required
├── Search Service: Google News RSS
│   ├── Source: https://news.google.com/rss/search
│   ├── No authentication needed
│   └── Rate limit: Friendly (no official limit)
└── Database: SQLite
    ├── Location: data/customer.db
    ├── Size: ~20 KB (15 customer records)
    └── Schema: customers table

Libraries & Dependencies:
├── langchain==0.3.27 (LLM orchestration)
├── langchain-core==0.3.75
├── langchain-community==0.3.27
├── langchain-groq==0.3.8 (Groq integration)
├── langgraph==0.6.6 (ReAct agent)
├── feedparser>=6.0.0 (RSS parsing)
├── tenacity==8.2.3 (retry logic)
└── pydantic>=2.0.0 (validation)
```

### Data Flow

```
User Input
    ↓
Email Selection (from SQLite)
    ↓
Fetch User Interests (from SQLite)
    ↓
Expand Query (via Groq LLM)
    ↓
Search News (Google News RSS)
    ↓
Filter by Credibility (Groq LLM)
    ↓
Summarize Results (Groq LLM)
    ↓
Display to User
```

### Component Responsibilities

**Frontend (Streamlit)**
- User interface & interaction
- Session state management
- Result display & formatting
- Error message display

**Pipeline (Python Core)**
- Query expansion logic
- Search orchestration
- Result aggregation
- Credibility filtering

**LLM Service (Groq)**
- Query expansion
- Credibility evaluation
- Result summarization
- Response generation

**Search Service (Google News)**
- News article retrieval
- RSS feed parsing
- URL normalization

**Database (SQLite)**
- Customer profile storage
- Interest management
- Cache for search results

---

## Deployment Infrastructure

### Streamlit Cloud Configuration

**Current Setup:**
- **Platform**: Streamlit Cloud (PaaS)
- **Auto-Deploy**: Enabled (GitHub webhook)
- **Repository**: https://github.com/SeethepalliRaviK/newsfindr
- **Branch**: main
- **Python Version**: 3.11.9
- **Startup Command**: `streamlit run newsfindr_app.py`

**Secrets Configuration:**
```
# .streamlit/secrets.toml (local) or Streamlit Cloud Secrets
GROQ_API_KEY = "gsk_..." (masked in logs)
```

**Config File:**
```
# .streamlit/config.toml
[client]
showErrorDetails = true

[server]
port = 8501
headless = true
runOnSave = true

[theme]
primaryColor = "#0066cc"
backgroundColor = "#f5f5f5"
secondaryBackgroundColor = "#ffffff"
textColor = "#333333"
```

### Deployment Steps

1. **Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Streamlit Cloud Auto-Deploy**
   - Webhook triggers deployment
   - Dependencies installed from requirements.txt
   - Secrets loaded from platform
   - App starts automatically

3. **Health Check**
   ```bash
   curl https://newsfindr.streamlit.app
   # Should return HTTP 200
   ```

---

## Monitoring & Observability

### Key Metrics to Monitor

**1. Application Performance**
```
- Response Time: Target <10s per query
- Search Latency: <3s (Groq + Google News)
- Error Rate: <0.5% of requests
- Uptime: 99.9% target
```

**2. LLM (Groq) Metrics**
```
- Tokens Per Minute (TPM): Monitor against 8000 limit
- API Availability: Should be >99.9%
- Response Latency: <1s typical
- Error Rate: Watch for sudden spikes
```

**3. Search Metrics**
```
- Results Per Query: 3-50 articles
- Freshness: Articles updated within 24 hours
- Success Rate: 95%+ queries return results
- Duplicate Rate: <5% after deduplication
```

**4. System Health**
```
- Memory Usage: <200 MB typical
- CPU Usage: <50% average
- Disk Usage: Minimal (no persistent storage)
- Connection Pool: <10 concurrent connections
```

### Logging Strategy

**Current Implementation:**
```python
# utils/llm.py - Rate limiter logging
print(f"[RATE LIMIT] Tokens reserved: {tokens}, Available: {self.available}")

# utils/search.py - Search logging
print(f"[news search] Found {len(results)} articles for: {query}")
print(f"[ddg_search failed] Error: {type(e).__name__}")

# core/pipeline.py - Pipeline logging
print(f"Queries: {queries}")
print(f"Raw results: {len(combined)}")
```

**Recommended Enhancements:**
```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"Query expanded: {query} → {queries}")
logger.warning(f"Rate limit approaching: {used_tokens}/{TPM_LIMIT}")
logger.error(f"Search failed for query: {query}", exc_info=True)
```

**Log Levels:**
- DEBUG: Token budget updates, cache hits
- INFO: Query processing, results count
- WARNING: Rate limit warnings, unusual patterns
- ERROR: API failures, search failures
- CRITICAL: System failures, cascading errors

### Monitoring Dashboards

**Recommended Tools:**
1. **Streamlit Cloud Dashboard**
   - Built-in app logs
   - Deployment history
   - Error tracking

2. **External Monitoring**
   - Uptime monitoring (Pingdom, UptimeRobot)
   - Error tracking (Sentry, Rollbar)
   - Performance monitoring (New Relic)

---

## Performance Metrics

### Expected Performance

| Operation | Latency | Notes |
|-----------|---------|-------|
| Load app | <2s | First load |
| Select email | <0.1s | Database lookup |
| Expand query | 0.5-2s | Groq LLM |
| Search news | 0.5-3s | Google News RSS |
| Filter credibility | 1-3s | Groq LLM |
| Summarize | 1-5s | Groq LLM |
| **Total End-to-End** | **4-15s** | Typical range |

### Bottleneck Analysis

**Current Bottlenecks (in order):**
1. **Summarization** (3-5s) - Most LLM tokens used
2. **Query Expansion** (1-2s) - LLM inference
3. **Credibility Filter** (1-3s) - LLM inference
4. **Search** (0.5-3s) - Network latency

**Optimization Opportunities:**
- Cache common queries (Redis)
- Parallel processing (async/await)
- Summarization length reduction
- Batch operations

---

## Rate Limiting & Throttling

### Groq API Rate Limits

**Current Configuration:**
```python
# core/config.py
TPM_LIMIT = 8000  # Tokens per minute
TPM_SAFETY = 0.80  # Use only 80% = 6400 TPM
RATE_RETRIES = 6  # Max retry attempts
```

**Token Budget Implementation:**
```python
# utils/llm.py - TokenBudget class

class TokenBudget:
    def __init__(self, tokens_per_minute: int):
        self.limit = tokens_per_minute
        self.tokens_available = tokens_per_minute
        self.refill_time = time.time()
    
    def reserve(self, tokens: int) -> bool:
        """Check if tokens available, reserve them"""
        # 60-second rolling window
        # Returns True if reservation successful
    
    def settle(self, actual_tokens: int):
        """Record actual tokens used"""
    
    def penalize(self, factor=0.9):
        """Reduce limit on errors"""
```

### Handling Rate Limits

**Error Response:** `429 Too Many Requests`

**Automatic Recovery:**
```python
# tenacity library with exponential backoff
@retry(
    stop=stop_after_attempt(6),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(RateLimitError)
)
```

**Rate Limit Incidents:**
1. Check current TPM usage
2. Review query patterns for spikes
3. Implement query caching
4. Reduce result count if needed
5. Contact Groq support if persistent

---

## Error Handling & Recovery

### Error Categories

**1. LLM Service Errors**
```
RateLimitError (429)    → Retry with backoff
AuthenticationError     → Check API key
TimeoutError           → Retry
BadRequestError        → Log & skip query
```

**2. Search Errors**
```
NetworkError           → Retry with backoff
TimeoutError          → Return cached results
ParsingError          → Log & continue
```

**3. Database Errors**
```
FileNotFoundError     → Use fallback paths
ConnectionError       → Return empty profile
```

**4. Application Errors**
```
ValueError            → Validate inputs
KeyError             → Defensive checks
TypeError            → Type validation
```

### Recovery Strategies

| Error | Strategy | Max Retries | Backoff |
|-------|----------|-------------|---------|
| Rate Limit | Exponential | 6 | 4-10s |
| Network | Exponential | 3 | 2-8s |
| Timeout | Linear | 2 | 2s |
| Auth | None | 0 | N/A |
| Validation | None | 0 | N/A |

### Fallback Mechanisms

**Query Expansion Failure:**
- Use original query
- Skip expansion, search directly

**Search Failure:**
- Return cached results
- Show "no results" message

**Summarization Failure:**
- Return raw search results
- Show disclaimer about summary

**Database Failure:**
- Load sample interests
- Create default profile

---

## Scaling Considerations

### Current Capacity

**Single Instance:**
- Concurrent users: ~10-50
- Requests per minute: 20-30
- Database size: 20 KB (negligible)
- Memory footprint: 150-200 MB

### Scaling Strategies

**1. Horizontal Scaling (Streamlit Cloud)**
- Streamlit Cloud handles auto-scaling
- Multiple app instances behind load balancer
- Session state isolated per instance

**2. Caching Layer**
```
Implement Redis for:
- Query expansion results
- News search results (24h cache)
- Summarization results (48h cache)
- Interest profiles (refresh weekly)
```

**3. Database Scaling**
- Current: SQLite (20 KB) - fine for <100 users
- Growth: PostgreSQL if >1000 users
- Consider: User profile caching

**4. LLM Service Scaling**
- Groq provides higher limits for paid plans
- Current: 8000 TPM (free tier)
- Upgrade: 30,000-300,000 TPM available

### Load Testing Results

**Recommended Load Test Setup:**
```bash
# Simulate 10 concurrent users
locust -f loadtest.py --clients 10 --hatch-rate 2 -u newsfindr.streamlit.app
```

**Expected Results:**
- Response time: 95th percentile <15s
- Error rate: <1%
- Throughput: 100+ requests/minute

---

## Security & Secrets Management

### API Key Management

**Current Implementation:**
```python
# utils/llm.py
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not set")
```

**Best Practices:**
1. **Never commit secrets** - .gitignore excludes secrets.toml
2. **Use environment variables** - Streamlit Cloud secrets
3. **Rotate regularly** - Every 90 days
4. **Monitor usage** - Check Groq API dashboard
5. **Restrict scope** - API key only for news endpoints

**Secrets Storage:**
```
Local Development: .streamlit/secrets.toml (gitignored)
Production: Streamlit Cloud Secrets UI
Backup: Never commit or log
```

### Data Security

**Data in Transit:**
- ✅ HTTPS for all connections
- ✅ TLS 1.2+ required
- ✅ Encrypted secrets in transit

**Data at Rest:**
- ✅ SQLite database encrypted via OS
- ✅ No PII stored (emails are for profile lookup)
- ✅ No payment data
- ✅ No sensitive credentials in DB

**Access Control:**
- Public app (no authentication)
- Optional: Add email-based auth for restricted access
- Database: Read-only for queries

---

## Maintenance Procedures

### Daily Checks

```bash
# Check app status
curl https://newsfindr.streamlit.app/health

# Review logs
# Streamlit Cloud: Dashboard → Logs tab

# Monitor Groq API
# Visit: https://console.groq.com/keys
# Check usage vs quota
```

### Weekly Maintenance

1. **Performance Review**
   - Average response time
   - Error rate trends
   - Cache hit rates

2. **Dependency Updates**
   ```bash
   pip list --outdated
   # Update non-breaking updates
   ```

3. **Security Audit**
   - Review recent Groq API usage
   - Check for unusual patterns
   - Rotate API keys if needed

### Monthly Maintenance

1. **Full System Test**
   - Test all search topics
   - Test all user profiles
   - Verify error handling

2. **Database Maintenance**
   ```bash
   sqlite3 data/customer.db
   VACUUM;  # Compact database
   ANALYZE; # Optimize queries
   ```

3. **Documentation Review**
   - Update troubleshooting guide
   - Document new patterns
   - Update architecture diagrams

### Quarterly Maintenance

1. **Dependency Updates**
   - Update all major dependencies
   - Test thoroughly
   - Deploy to staging first

2. **Infrastructure Review**
   - Evaluate scaling needs
   - Review cost optimization
   - Plan for growth

3. **Security Review**
   - Penetration testing
   - API key rotation
   - Access control audit

---

## Cost Optimization

### Current Costs

**Breakdown:**
- Streamlit Cloud: Free tier (generous limits)
- Groq API: Free tier (8000 TPM)
- Google News RSS: Free (no API key)
- SQLite: Free (local storage)
- **Total: $0/month**

### Cost Growth Scenarios

| Users | Queries/Month | Groq Cost | Total |
|-------|---------------|-----------|-------|
| 10 | 300 | Free | $0 |
| 50 | 1,500 | Free | $0 |
| 100 | 3,000 | Free | $0 |
| 500 | 15,000 | $0.30/1M tokens | $30 |
| 1000 | 30,000 | | $60 |
| 5000 | 150,000 | | $300 |

### Cost Reduction Strategies

1. **Caching** (Biggest impact)
   - Cache query expansions (same results)
   - Cache search results (reuse within 24h)
   - Cache summaries (reuse within 48h)
   - Estimated savings: 60-70%

2. **Model Optimization**
   - Use faster/cheaper models for routing
   - Smaller context windows
   - Batch processing
   - Estimated savings: 10-20%

3. **Infrastructure**
   - Keep using free tier as long as possible
   - Use Streamlit Cloud (no additional cost)
   - Avoid external databases (use SQLite)
   - Estimated savings: 30-40%

---

## Incident Response

### Common Incidents

**Incident: App is Down**
```
1. Check Streamlit Cloud status
2. Review recent deployments
3. Check logs for errors
4. Rollback if needed: git revert, git push
5. Notify users if >1 hour down
```

**Incident: Groq API Rate Limit Exceeded**
```
1. Check TPM usage in Groq console
2. Analyze query patterns for spike
3. Enable response caching
4. Contact Groq support for limit increase
5. Implement query batching
```

**Incident: Search Results Empty**
```
1. Test Google News RSS manually
2. Check internet connectivity
3. Verify feedparser installation
4. Try different query terms
5. Check for Google blocking requests
```

**Incident: High Error Rate**
```
1. Check recent code changes
2. Review error logs
3. Check dependencies versions
4. Test with sample queries
5. Rollback if necessary
```

### Incident Severity Levels

| Level | Definition | Response Time | Actions |
|-------|------------|---|---------|
| P1 | App down, no workaround | 15 min | Immediate rollback/fix |
| P2 | Core feature broken | 1 hour | Urgent debugging |
| P3 | Degraded performance | 4 hours | Investigation |
| P4 | Minor bug | 1 day | Schedule fix |

---

## Deployment Checklist

**Before Deploying to Production:**

### Code Quality
- [ ] All 18 unit/integration tests passing
- [ ] No hardcoded secrets or credentials
- [ ] Code follows PEP 8 style guide
- [ ] All imports are used
- [ ] Error handling implemented
- [ ] Logging configured
- [ ] Type hints added where applicable

### Dependencies
- [ ] requirements.txt updated
- [ ] No security vulnerabilities: `pip-audit`
- [ ] All dependencies pinned to versions
- [ ] Tested with Python 3.11.9

### Documentation
- [ ] README.md updated
- [ ] Docstrings added to functions
- [ ] Deployment guide updated
- [ ] Known issues documented

### Testing
- [ ] Unit tests pass locally
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Error scenarios tested
- [ ] Performance acceptable

### Secrets Management
- [ ] GROQ_API_KEY configured in Streamlit Cloud
- [ ] .streamlit/secrets.toml in .gitignore
- [ ] No secrets in git history
- [ ] Secrets rotation schedule set

### Monitoring
- [ ] Logging configured
- [ ] Error tracking enabled
- [ ] Performance monitoring ready
- [ ] Uptime monitoring configured

### Rollback Plan
- [ ] Previous version tested and ready
- [ ] Rollback procedure documented
- [ ] Team trained on rollback
- [ ] Communication plan ready

---

## Production Runbook

### Deployment
```bash
1. git push origin main
2. Wait 2-3 minutes for Streamlit Cloud deployment
3. Visit https://newsfindr.streamlit.app
4. Test: Run 3-5 queries
5. Verify: Check logs for errors
6. Notify: Inform users if major update
```

### Rollback
```bash
1. git revert [commit-hash]
2. git push origin main
3. Wait 2-3 minutes for deployment
4. Verify app is stable
5. Post-mortem: Analyze what went wrong
```

### Incident Response
```bash
1. Assess severity (P1-P4)
2. Notify team if P1 or P2
3. Check logs: Streamlit Cloud dashboard
4. Implement fix or rollback
5. Monitor closely for 1 hour
6. Post-incident review
```

---

**Last Updated**: 2026-10-02  
**Author**: NewsFindr DevOps Team  
**Next Review**: 2026-11-02
