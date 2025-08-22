# Project Structure - CLEANED

## Active Files (4 Python files only)

1. **main.py** - FastAPI backend server
   - Handles document upload
   - Calls simple_extraction for AI processing
   - Persists to database

2. **simple_extraction.py** - AI extraction logic
   - extract_with_gemini_simple() - Direct Gemini extraction
   - two_stage_extraction() - Fallback method
   - three_lane_ai_analysis() - Not currently used

3. **persist_extraction.py** - Database persistence
   - Saves extraction results to PostgreSQL

4. **db_selftest.py** - Database health check endpoint

## Support Files

- **Dockerfile** - Container definition
- **docker-compose.yml** - Service orchestration (postgres, redis, app)
- **requirements.txt** - Python dependencies
- **web-interface.html** - Upload UI
- **.env** - Environment variables (GOOGLE_API_KEY, etc)
- **sql/** - Database schema

## Archive (2 files)
- Previous versions of main.py for reference only

## Data
- Sample contracts for testing

---

Total: 4 active Python files (down from 130+ created during debugging)
