# NewsFindr - Lessons Learned & Best Practices

Complete documentation of all lessons, pitfalls, and best practices from this deployment.

---

## 🎓 Executive Summary

This document captures critical lessons from developing and deploying NewsFindr to production. Key insights:

1. **Library Compatibility Issues** - Third-party library versions can break unexpectedly
2. **Testing Saves Time** - Comprehensive tests caught issues early
3. **Documentation Matters** - Users need clear guides, MLOps needs operational docs
4. **Checklists Prevent Disasters** - Pre-deployment checklists save hours of debugging
5. **Fallbacks Are Essential** - Always have backup approaches for external dependencies

---

## 🔴 Critical Issues & Solutions

### Issue 1: DuckDuckGo Libraries Throwing BuilderError

**Problem:**
- `ddgs==9.6.1` and `duckduckgo_search==5.1.0` both threw `BuilderError`
- Blocking all news retrieval functionality
- Happened at deployment time, not development

**Root Cause:**
- Library API incompatibility with DuckDuckGo endpoints
- No upstream support or updates available
- Version pinning locked to broken versions

**Solution Implemented:**
1. Removed both broken libraries from requirements.txt
2. Switched to Google News RSS with `feedparser`
3. No authentication needed
4. More reliable for production use

**Lessons:**
- [ ] Avoid dependencies with low maintenance
- [ ] Test dependencies in production environment
- [ ] Have fallback search strategies ready
- [ ] Monitor dependency health regularly
- [ ] Use `pip-audit` for vulnerability checks

**Prevention for Future:**
```python
# Instead of relying on single library:
# Implement multiple search backends with graceful fallback

search_backends = [
    GoogleNewsRSS,      # Primary (feedparser)
    NewsAPIClient,      # Secondary (if funded)
    DuckDuckGoSearch,   # Tertiary (if library fixed)
]

for backend in search_backends:
    try:
        results = backend.search(query)
        if results:
            return results
    except Exception:
        continue
```

---

### Issue 2: Wrong Data Format from Search Function

**Problem:**
- `ddg_search()` returned JSON string instead of Python list
- Code called `json.loads()` on already-loaded data
- Type inconsistency between function definition and usage

**Root Cause:**
- Function docstring said one thing, implementation did another
- No type hints to catch mismatch
- Tests didn't validate return types strictly

**Solution:**
1. Added proper type hints: `-> List[Dict[str, str]]`
2. Actual return value matches type hint
3. Updated caller in pipeline.py to not call json.loads()

**Lessons:**
- [ ] Always add type hints to functions
- [ ] Match return types to documentation
- [ ] Use MyPy for static type checking
- [ ] Test return types strictly

**Prevention for Future:**
```python
# GOOD - Type hints catch mismatches
def search(query: str) -> List[Dict[str, str]]:
    """Return list of article dicts."""
    # Implementation MUST return List[Dict[str, str]]

# BAD - No type hints, inconsistency possible
def search(query):
    """Search for news."""
    # Could return list, dict, string, JSON - unclear
```

---

### Issue 3: Database Column Name Mismatch

**Problem:**
- Code referenced column `email_id` which didn't exist
- Database had column `email` instead
- Test suite failed with "no such column" error

**Root Cause:**
- Schema documentation not synced with actual database
- Manual database inspection skipped during setup
- Tests didn't validate schema before running

**Solution:**
1. Inspected actual database schema: `PRAGMA table_info(customers)`
2. Found correct columns: `email`, `customer_id`, `interests`
3. Updated all SQL queries to use correct column names
4. Added schema validation test

**Lessons:**
- [ ] Always inspect actual database before coding
- [ ] Document actual schema, not assumptions
- [ ] Add schema validation tests
- [ ] Use database initialization scripts
- [ ] Version control database dumps

**Prevention for Future:**
```python
# Add schema validation on startup
import sqlite3

def validate_database_schema():
    """Verify database has required columns."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(customers)")
    columns = {row[1] for row in cursor.fetchall()}
    
    required = {'email', 'interests', 'customer_id'}
    missing = required - columns
    
    if missing:
        raise ValueError(f"Missing columns: {missing}")
```

---

### Issue 4: Encyclopedia Results Instead of News

**Problem:**
- DuckDuckGo instant API returned encyclopedia entries
- Credibility filter rejected encyclopedia entries
- Result: "No credible sources found" message

**Root Cause:**
- API was designed for search, not news retrieval
- Wrong endpoint for news data
- Test data wasn't validated before deployment

**Solution:**
1. Switched to Google News RSS endpoint
2. Verified it returns actual news articles
3. Added validation that results contain news-like data
4. Added logging to see what's being returned

**Lessons:**
- [ ] Validate API data quality before deploying
- [ ] Use purpose-built services for specific tasks
- [ ] Test with real-world data before launch
- [ ] Log data samples for debugging
- [ ] Document data format expectations

**Prevention for Future:**
```python
def validate_search_results(results):
    """Verify search returns news articles, not reference material."""
    if not results:
        raise ValueError("No results returned")
    
    for result in results[:3]:
        title = result.get('title', '')
        url = result.get('url', '')
        
        # News URLs usually contain dates, sources
        if not any(x in url for x in ['news', '.com', 'article']):
            logger.warning(f"Suspicious URL format: {url}")
        
        # Title should be descriptive
        if len(title) < 10 or len(title) > 200:
            logger.warning(f"Suspicious title length: {title}")
```

---

## 🟡 Operational Lessons

### Testing Strategy

**What Worked:**
- [ ] 18 comprehensive tests covering core, utils, integration
- [ ] Tests caught most issues before deployment
- [ ] 100% pass rate before launch

**What Could Improve:**
- [ ] Add end-to-end tests (full query → response)
- [ ] Add performance tests (response time < 10s)
- [ ] Add real-world data tests (actual Groq API, Google News)
- [ ] Add schema validation tests
- [ ] Add secrets scanning in CI/CD

**Best Practice:**
```python
# Test pyramid approach
# 60% unit tests (fast, isolated)
# 30% integration tests (module interaction)
# 10% end-to-end tests (full flow)

tests/
├── test_core.py          # Unit: config, models
├── test_utils.py         # Unit: functions
├── test_integration.py   # Integration: database, search
└── test_e2e.py          # E2E: full query pipeline
```

---

### Dependency Management

**What Worked:**
- [ ] requirements.txt with pinned versions
- [ ] Clear dependency list
- [ ] Regular pip audits

**What Could Improve:**
- [ ] Use Poetry or Pipenv for better resolution
- [ ] Test dependencies in CI/CD
- [ ] Monthly dependency updates
- [ ] Security scanning (pip-audit, Snyk)

**Best Practice:**
```
requirements.txt:
- Pin major versions only for non-critical deps
- Pin exact versions for critical deps
- Pin critical: langchain, groq, pydantic
- Allow: pandas>=2.0.0, feedparser>=6.0.0

requirements-dev.txt:
- Testing: pytest, pytest-cov
- Linting: black, flake8, mypy
- Security: pip-audit, bandit
```

---

### Documentation Quality

**What Worked:**
- [ ] README with setup instructions
- [ ] Architecture explanation
- [ ] Clear usage examples

**What We Added:**
- [ ] USER_GUIDE.md - For end users
- [ ] MLOPS_GUIDE.md - For operations
- [ ] DEPLOYMENT_CHECKLIST.md - Pre-flight checks
- [ ] LEARNINGS.md - Best practices (this doc)

**Best Practice:**
```
All projects should have:
├── README.md            - Overview & quick start
├── USER_GUIDE.md        - How to use the app
├── MLOPS_GUIDE.md       - How to operate it
├── TECHNICAL_DOCS.md    - Architecture & code
├── DEPLOYMENT_GUIDE.md  - Deploy procedures
└── LEARNINGS.md         - Lessons & best practices
```

---

## 🟢 Best Practices Going Forward

### Code Quality Standards

**Mandatory:**
1. [ ] Type hints on all functions
   ```python
   def search(query: str) -> List[Dict[str, str]]:
   ```

2. [ ] Docstrings on all public functions
   ```python
   def search(query: str) -> List[Dict[str, str]]:
       """Search Google News RSS for articles.
       
       Args:
           query: Search term (e.g., 'artificial intelligence')
       
       Returns:
           List of articles with title, url, body, date
       
       Raises:
           ValueError: If query is empty
       """
   ```

3. [ ] Error handling with meaningful messages
   ```python
   try:
       results = search(query)
   except ValueError as e:
       logger.error(f"Invalid query: {e}")
       return []
   ```

4. [ ] Logging at appropriate levels
   ```python
   logger.debug("Expanded query: {query}")
   logger.info(f"Found {len(results)} articles")
   logger.warning("Rate limit approaching")
   logger.error("Search failed", exc_info=True)
   ```

**Recommended:**
- [ ] Pre-commit hooks (black, flake8, mypy)
- [ ] Type checking with MyPy
- [ ] Code coverage reports
- [ ] Security scanning (bandit)

### Testing Strategy

**Unit Tests:**
- Test individual functions in isolation
- Mock external dependencies (Groq, Google News)
- Test both success and error cases
- Current: 8 tests in test_utils.py + test_core.py

**Integration Tests:**
- Test modules working together
- Use real database but mock external APIs
- Test data flow through system
- Current: 5 tests in test_integration.py

**End-to-End Tests (NEW):**
- Test full flow: query → summarized results
- Use real APIs (Groq, Google News)
- Expensive (real API calls), run fewer times
- Example test:
  ```python
  def test_full_news_flow():
      results = query_response(
          email="test@example.com",
          user_query="artificial intelligence"
      )
      assert "title" in results or "no credible" in results.lower()
  ```

### Deployment Best Practices

**Pre-Deployment:**
1. [ ] Run all tests: `pytest tests/ -v`
2. [ ] Check for secrets: `grep -r "gsk_\|password\|api" .`
3. [ ] Type checking: `mypy . --strict`
4. [ ] Security scan: `pip-audit` and `bandit`
5. [ ] Update documentation
6. [ ] Review git history for secrets

**During Deployment:**
1. [ ] Use deployment checklist (see DEPLOYMENT_CHECKLIST.md)
2. [ ] Test in staging first
3. [ ] Monitor app logs closely
4. [ ] Test with real users immediately
5. [ ] Have rollback plan ready

**Post-Deployment:**
1. [ ] Monitor for 1 hour constantly
2. [ ] Check API usage (Groq dashboard)
3. [ ] Review error logs
4. [ ] Get user feedback
5. [ ] Document any issues
6. [ ] Post-mortem if anything goes wrong

### Monitoring Strategy

**Key Metrics:**
- [ ] Response time (< 10s for full query)
- [ ] Error rate (< 0.5%)
- [ ] Uptime (99.9% target)
- [ ] Groq TPM usage (current: <100 TPM average)
- [ ] Search result quality (credible sources found %)

**Logging Strategy:**
- [ ] Log query and response time
- [ ] Log errors with full context
- [ ] Log Groq API usage
- [ ] Log search result counts
- [ ] Log user interactions (anonymized)

**Example Logging:**
```python
import logging
import time

logger = logging.getLogger(__name__)

start = time.time()
results = search(query)
elapsed = time.time() - start

logger.info(
    "Query processed",
    extra={
        "query": query,
        "results": len(results),
        "elapsed_seconds": round(elapsed, 2),
        "user_email": email,
    }
)
```

---

## 📊 Performance Lessons

### Current Performance

```
Operation              Latency    Notes
─────────────────────────────────────────────
App load               <2s        First-time cold start
Select email           <0.1s      Database lookup
Expand query (LLM)     0.5-2s     Groq API call
Search news            0.5-3s     Google News RSS + parse
Filter credibility     1-3s       Groq API call
Summarize (LLM)        3-5s       Groq API call (most tokens)
────────────────────────────────────
TOTAL                  4-15s      Acceptable for news app
```

### Bottleneck Analysis

**Top Bottleneck:** Summarization (40% of time)
- Most LLM tokens consumed
- Can optimize by:
  - Reducing token context window
  - Using faster/smaller model
  - Parallelizing requests

**Second Bottleneck:** Query Expansion (10%)
- Could be cached (same queries often repeated)
- Pre-compute for common interests

**Optimization Opportunities:**
1. [ ] Cache query expansions (1 week TTL)
2. [ ] Cache search results (1 day TTL)
3. [ ] Parallel processing (async/await)
4. [ ] Summary caching (48 hour TTL)
- Estimated improvement: 50-60% faster

---

## 🔒 Security Lessons

### API Key Management

**Current Implementation:**
- [ ] Keys in environment variables only
- [ ] Streamlit Cloud secrets UI for storage
- [ ] Never logged or echoed
- [ ] Rotation every 90 days

**Learned from Incident:**
- Almost committed API key to git (caught by .gitignore)
- Importance of pre-commit hooks
- Need for secrets scanning in CI/CD

**Future Security:**
```
1. Use git pre-commit hooks
   - git/hooks/pre-commit: grep -r "gsk_"
   - Prevent secrets from being committed

2. Use Snyk or similar
   - Continuous dependency scanning
   - Automated alerts for vulnerabilities

3. Regular security audit
   - Quarterly review of access
   - Quarterly API key rotation
   - Penetration testing (annual)
```

---

## 🚀 Scaling Lessons

### Current Limitations

**Streamlit Cloud Free Tier:**
- 1 GB memory per app
- No SLA (best effort)
- Auto-sleep after 7 days of inactivity
- Sufficient for 50-100 users

**Groq Free Tier:**
- 8000 TPM (tokens per minute)
- Sufficient for 20-30 concurrent users
- Paid tiers available (30K-300K TPM)

**SQLite Database:**
- Suitable for <1000 user profiles
- After 1000: migrate to PostgreSQL
- Currently: 20 KB (15 profiles)

### Scaling Path

**Phase 1 (Current):** Free tiers
- Streamlit Cloud free
- Groq free (8000 TPM)
- SQLite local storage

**Phase 2 (100-500 users):**
- Streamlit Cloud (paid) - $5-20/month
- Groq upgrade - 30K TPM - $0.30/1M tokens
- PostgreSQL - $15-30/month
- Estimated cost: $50-100/month

**Phase 3 (500-5000 users):**
- Kubernetes cluster - $500+/month
- Dedicated Groq inference - $1000+/month
- Enterprise database - $500+/month
- Load balancing, caching, monitoring
- Estimated cost: $2000+/month

---

## 📝 Skill Updates & Recommendations

### For srk-local-git-streamlit-pipeline Skill

**Add Section: Dependency Testing**
```markdown
### Step: Test Dependencies in Production Environment

Before deploying:
1. Create fresh venv with requirements.txt
2. Test all major components
3. Test with real API calls (if possible)
4. Document any version-specific issues

This would have caught the ddgs BuilderError
```

**Add Section: Data Quality Validation**
```markdown
### Step: Validate External API Data

For each external service (search, LLM):
1. Test with real queries
2. Validate response format
3. Check data completeness
4. Document expected structure
5. Add schema validation tests

This would have caught encyclopedia vs news issue
```

**Add Section: Pre-Deployment Checklists**
```markdown
### Step: Run Deployment Checklists

Before GitHub push:
- Code quality checks
- Secrets scanning
- Type checking
- Documentation review

Before Streamlit deploy:
- Requirements.txt verified
- Secrets configured
- Local tests passing
- Real API testing

This would have prevented all issues
```

**Add Section: Monitoring Setup**
```markdown
### Step: Configure Monitoring

After deployment:
- Error tracking (Sentry/Rollbar)
- Performance monitoring (New Relic)
- Uptime monitoring (UptimeRobot)
- API usage tracking

Critical for production apps
```

---

## 🎯 Recommendations for Future Projects

### Project Planning

1. **Architecture Review**
   - Review dependency health
   - Identify single points of failure
   - Plan fallback strategies
   - Document external service dependencies

2. **Testing Strategy**
   - Unit tests (>80% coverage)
   - Integration tests (key workflows)
   - E2E tests (full user flow)
   - Performance tests (response time)
   - Security tests (secrets scanning)

3. **Documentation**
   - README for developers
   - USER_GUIDE for end users
   - MLOPS_GUIDE for operators
   - DEPLOYMENT_CHECKLIST for safety
   - LEARNINGS for future projects

### Development Best Practices

1. **Code Quality**
   - Type hints everywhere
   - Comprehensive docstrings
   - Meaningful error messages
   - Proper logging

2. **Testing**
   - Test early, test often
   - Test with real data
   - Test error cases
   - Test external dependencies

3. **Security**
   - Never commit secrets
   - Use environment variables
   - Scan dependencies regularly
   - Rotate API keys

### Deployment Best Practices

1. **Pre-Deployment**
   - Use comprehensive checklists
   - Test in staging first
   - Verify all external dependencies
   - Prepare rollback plan

2. **Monitoring**
   - Log important events
   - Monitor error rates
   - Track API usage
   - Alert on anomalies

3. **Incident Response**
   - Document procedures
   - Practice rollbacks
   - Post-mortem all incidents
   - Share learnings

---

## 📚 Resources & References

### Tools & Libraries
- **Type Checking**: MyPy (pip install mypy)
- **Code Formatting**: Black (pip install black)
- **Linting**: Flake8 (pip install flake8)
- **Security**: Bandit (pip install bandit)
- **Testing**: Pytest (pip install pytest)
- **Dependency Audit**: pip-audit (pip install pip-audit)

### Testing Resources
- PyTest documentation: https://docs.pytest.org/
- Testing best practices: https://testdriven.io/
- Fixture guide: https://docs.pytest.org/en/stable/fixture.html

### Deployment Resources
- Streamlit documentation: https://docs.streamlit.io/
- Python deployment: https://realpython.com/deployment/
- Git pre-commit: https://pre-commit.com/

---

## ✅ Checklist for Next Projects

- [ ] Add type hints to all functions
- [ ] Write comprehensive docstrings
- [ ] Create USER_GUIDE.md for users
- [ ] Create MLOPS_GUIDE.md for operators
- [ ] Create DEPLOYMENT_CHECKLIST.md
- [ ] Set up pre-commit hooks
- [ ] Configure secrets scanning
- [ ] Add type checking (MyPy)
- [ ] Create E2E tests
- [ ] Set up monitoring/logging
- [ ] Document architecture
- [ ] Document all external dependencies
- [ ] Plan fallback strategies
- [ ] Create deployment procedures

---

**Document Version**: 1.0  
**Last Updated**: 2026-10-02  
**Next Review**: 2026-01-02  
**Author**: NewsFindr Development & Operations Teams
