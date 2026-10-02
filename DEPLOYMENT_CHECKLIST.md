# NewsFindr - Pre-Deployment Checklists

Complete checklists for deploying to GitHub and Streamlit Cloud.

---

## ✅ Pre-GitHub Deployment Checklist

### Code Quality (MANDATORY)

- [ ] All tests passing locally
  ```bash
  pytest tests/ -v
  # Expected: 18/18 PASSED
  ```

- [ ] No hardcoded secrets or API keys
  ```bash
  grep -r "gsk_" . --include="*.py"
  grep -r "groq_api" . --include="*.py"
  # Expected: No results (except in comments)
  ```

- [ ] No .env file contains secrets
  ```bash
  cat .env
  # Should be empty or contain only non-secret variables
  ```

- [ ] .gitignore configured correctly
  ```bash
  git check-ignore .streamlit/secrets.toml
  git check-ignore .env
  # Expected: Both files ignored
  ```

- [ ] Code follows Python standards
  ```bash
  pip install black flake8
  black . --check
  flake8 . --max-line-length=100
  ```

- [ ] All imports used
  ```bash
  pip install vulture
  vulture . --min-confidence 80
  # Expected: No unused imports
  ```

- [ ] Type hints present in functions
  ```bash
  grep -r "def " core/ utils/ --include="*.py"
  # Check: Function signatures have type hints
  ```

- [ ] Docstrings present
  ```bash
  grep -r '"""' core/pipeline.py
  # Expected: All functions have docstrings
  ```

### Dependencies (MANDATORY)

- [ ] requirements.txt exists and complete
  ```bash
  cat requirements.txt
  # All packages listed with pinned versions
  ```

- [ ] No security vulnerabilities
  ```bash
  pip-audit
  # Expected: No vulnerabilities found
  ```

- [ ] No unused dependencies
  ```bash
  grep -r "^import\|^from" --include="*.py" > /tmp/imports.txt
  # Verify each in requirements.txt
  ```

- [ ] Python version specified
  ```bash
  cat runtime.txt
  # Expected: python-3.11.9 or similar
  ```

### Database (MANDATORY)

- [ ] SQLite database included
  ```bash
  ls -lh data/customer.db
  # Expected: ~20 KB file exists
  ```

- [ ] Database in git
  ```bash
  git ls-files | grep customer.db
  # Expected: data/customer.db listed
  ```

- [ ] Database can be read
  ```bash
  sqlite3 data/customer.db "SELECT COUNT(*) FROM customers;"
  # Expected: 15 (rows count)
  ```

- [ ] Sample data verified
  ```bash
  python -c "from utils.database import get_all_emails; print(len(get_all_emails()))"
  # Expected: 15
  ```

### Documentation (RECOMMENDED)

- [ ] README.md complete
  ```bash
  wc -l README.md
  # Expected: 50+ lines
  ```

- [ ] USER_GUIDE.md complete
  ```bash
  wc -l USER_GUIDE.md
  # Expected: 200+ lines
  ```

- [ ] MLOPS_GUIDE.md complete
  ```bash
  wc -l MLOPS_GUIDE.md
  # Expected: 500+ lines
  ```

- [ ] Architecture documented
  - [ ] Data flow diagram described
  - [ ] Component responsibilities listed
  - [ ] Dependencies documented

### Configuration (MANDATORY)

- [ ] .streamlit/config.toml exists
  ```bash
  cat .streamlit/config.toml
  # Expected: Port, theme, settings configured
  ```

- [ ] .gitignore excludes secrets
  ```bash
  grep "secrets.toml\|\.env" .gitignore
  # Expected: Both patterns present
  ```

### Git History (MANDATORY)

- [ ] No secrets in git history
  ```bash
  git log --all -p | grep -i "gsk_\|api_key\|password"
  # Expected: No results
  ```

- [ ] Meaningful commit messages
  ```bash
  git log --oneline | head -10
  # Expected: Clear, descriptive messages
  ```

- [ ] All changes committed
  ```bash
  git status
  # Expected: working tree clean
  ```

### Pre-Push Verification

- [ ] Run full test suite one more time
  ```bash
  pytest tests/ -v
  # Expected: 18/18 PASSED
  ```

- [ ] Verify database loads
  ```bash
  python newsfindr_app.py --logger.level=error
  # Let it start, then Ctrl+C
  ```

- [ ] Test imports work
  ```bash
  python -c "
  from core.pipeline import query_response
  from utils.database import get_all_emails
  from utils.search import ddg_search
  print('All imports OK')
  "
  # Expected: All imports OK
  ```

---

## ✅ Pre-Streamlit Cloud Deployment Checklist

### Streamlit Cloud Preparation (MANDATORY)

- [ ] Repository pushed to GitHub
  ```bash
  git remote -v | grep origin
  # Expected: https://github.com/[user]/newsfindr listed
  ```

- [ ] Repository is public (or you have access)
  ```bash
  visit: https://github.com/SeethepalliRaviK/newsfindr
  # Expected: Page loads, code visible
  ```

- [ ] Branch is main
  ```bash
  git rev-parse --abbrev-ref HEAD
  # Expected: main
  ```

- [ ] Commit is pushed
  ```bash
  git log -1 --oneline
  git push origin main --dry-run
  # Expected: Already up to date
  ```

### Secrets Configuration (MANDATORY)

- [ ] Groq API key obtained
  ```bash
  Visit: https://console.groq.com/settings/apikeys
  Copy: Your API key (starts with gsk_)
  ```

- [ ] Not stored locally in code
  ```bash
  grep -r "gsk_" . --include="*.py"
  # Expected: No results
  ```

- [ ] Ready to add to Streamlit Cloud
  ```bash
  # Will be added in Streamlit Cloud UI:
  # Settings → Secrets → Add GROQ_API_KEY
  ```

### App Testing (MANDATORY)

- [ ] Test app locally one more time
  ```bash
  streamlit run newsfindr_app.py
  # Should load without errors at localhost:8501
  ```

- [ ] Test all user emails load
  ```
  App shows dropdown with 15 emails
  ```

- [ ] Test search works
  ```
  Query: "artificial intelligence"
  Expected: News summary returns
  ```

- [ ] Test different queries
  ```
  "technology news" → Results
  "business" → Results
  "sports" → Results
  All should work without errors
  ```

- [ ] Check error handling
  ```
  Try invalid input
  Expected: Graceful error message (not crash)
  ```

### Requirements.txt (MANDATORY)

- [ ] All dependencies listed
  ```bash
  cat requirements.txt
  # Expected: 11+ lines, all versions pinned
  ```

- [ ] Tested on Python 3.11.9
  ```bash
  python --version
  # Expected: Python 3.11.9 or compatible
  ```

- [ ] No development dependencies
  ```bash
  cat requirements.txt | grep -E "black|flake8|pytest-dev|ipython"
  # Expected: No development tools
  ```

- [ ] Optional: Test in fresh venv
  ```bash
  python -m venv test_env
  source test_env/bin/activate
  pip install -r requirements.txt
  python -c "import streamlit; import pydantic; import feedparser"
  # Expected: All imports succeed
  ```

### Environment Variables (MANDATORY)

- [ ] Only GROQ_API_KEY needed
  ```bash
  grep "os.environ.get" core/pipeline.py newsfindr_app.py
  # Expected: Only GROQ_API_KEY referenced
  ```

- [ ] Fallback handling present
  ```bash
  grep -A2 'GROQ_API_KEY' core/pipeline.py
  # Expected: Error handling if not set
  ```

### Performance Baseline (RECOMMENDED)

- [ ] Measure startup time
  ```bash
  time streamlit run newsfindr_app.py
  # Expected: <3 seconds to first output
  ```

- [ ] Measure query response time
  ```
  Query: "artificial intelligence"
  Expected: <15 seconds total
  ```

- [ ] Check memory usage
  ```bash
  ps aux | grep streamlit
  # Expected: <200 MB memory
  ```

### Final Safety Checks (MANDATORY)

- [ ] No hardcoded test credentials
  ```bash
  grep -r "test_\|dummy_\|fake_\|example" . --include="*.py" | grep -v "# example"
  # Expected: No suspicious credentials
  ```

- [ ] No print debugging statements
  ```bash
  grep -r "print(" core/ utils/ newsfindr_app.py
  # Expected: Only controlled logging
  ```

- [ ] No commented code blocks
  ```bash
  grep -r "# .*=" core/ utils/ | wc -l
  # Expected: <5 instances (acceptable)
  ```

- [ ] Proper error messages (no internal stack traces)
  ```
  Test app with invalid input
  Expected: User-friendly message
  ```

---

## ✅ Streamlit Cloud Setup Checklist

### Create App (Step-by-Step)

1. [ ] Visit https://share.streamlit.io
2. [ ] Click "New app"
3. [ ] Sign in with GitHub
4. [ ] Select repository: `SeethepalliRaviK/newsfindr`
5. [ ] Select branch: `main`
6. [ ] Select main file: `newsfindr_app.py`
7. [ ] Click "Deploy"

### Add Secrets (While Deploying)

1. [ ] Wait for initial deployment
2. [ ] Click "Manage app" (bottom right)
3. [ ] Go to "Settings"
4. [ ] Click "Secrets"
5. [ ] Add secret:
   ```
   Key: GROQ_API_KEY
   Value: gsk_[your_actual_key]
   ```
6. [ ] Click "Save"
7. [ ] App will restart automatically

### Post-Deployment Testing

- [ ] App loads without errors
  ```
  Visit: https://newsfindr.streamlit.app
  Expected: Page loads in <5 seconds
  ```

- [ ] No error messages in interface
  ```
  Expected: Clean UI, no Python errors visible
  ```

- [ ] Email dropdown populates
  ```
  Expected: 15 emails shown
  ```

- [ ] Search works
  ```
  Query: "artificial intelligence"
  Expected: News summary returns
  ```

- [ ] Different users work
  ```
  Select different email
  Query again
  Expected: Works for multiple users
  ```

- [ ] Error handling works
  ```
  Refresh during processing
  Expected: Graceful recovery
  ```

### Monitor After Deployment

- [ ] Check app logs
  ```
  Streamlit Cloud: Manage app → Logs
  Expected: No error messages
  ```

- [ ] Monitor for 1 hour
  ```
  Test every 10 minutes
  Expected: Consistent performance
  ```

- [ ] Check Groq API usage
  ```
  Visit: https://console.groq.com/usage
  Expected: Usage increasing normally
  ```

---

## ✅ Rollback Procedure (If Needed)

If deployment fails, follow this checklist:

1. [ ] Identify the issue
   - [ ] Check logs: Streamlit Cloud Logs tab
   - [ ] Note error message
   - [ ] Test locally with same code

2. [ ] Fix the issue
   - [ ] Make changes locally
   - [ ] Run tests: `pytest tests/ -v`
   - [ ] Verify: `streamlit run newsfindr_app.py`

3. [ ] Rollback temporarily (if urgent)
   ```bash
   git revert HEAD
   git push origin main
   # Wait 2-3 minutes for Streamlit Cloud to redeploy
   ```

4. [ ] Monitor recovery
   - [ ] App loads successfully
   - [ ] All tests pass
   - [ ] Search functionality works

5. [ ] Post-incident review
   - [ ] Document what went wrong
   - [ ] Update checklist if needed
   - [ ] Share learnings with team

---

## ✅ Success Criteria

### Minimum Deployment Success

- [x] App loads without errors
- [x] All 15 users in dropdown
- [x] Search returns results
- [x] 5+ test queries successful
- [x] No Python errors visible
- [x] Logs show normal operation

### Optimal Deployment Success

- [x] All above criteria met
- [x] Response time <10 seconds
- [x] Memory usage <200 MB
- [x] No warning messages
- [x] Zero error rate for first hour
- [x] Documentation complete

---

## 📝 Deployment Sign-Off

**Deployer Name**: ___________________  
**Date**: ___________________  
**All Checklists Passed**: Yes ☐ No ☐  

**Notes**:
```
[Space for notes on deployment]
```

---

**Last Updated**: 2026-10-02  
**Next Review**: Before next deployment
