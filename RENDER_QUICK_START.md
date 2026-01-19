# Quick Start: Render Deployment (5 Steps)

## Step 1: Push Code to GitHub (2 minutes)

```bash
cd /Users/sumanacharya0075/developer/python
git init
git add .
git commit -m "Production ready"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/community-search-api.git
git push -u origin main
```

**First, create an empty repo on GitHub:**
- Go to https://github.com/new
- Name: `community-search-api`
- Public
- Create
- Then run above commands

---

## Step 2: Create Database on Render (2 minutes)

1. Go to https://render.com/dashboard
2. Click **New +** → **PostgreSQL**
3. Fill:
   - Name: `community-db`
   - Database: `community_members_db`
   - User: `postgres`
   - Region: Closest to you
4. Click **Create Database**
5. ⏳ Wait 2-3 minutes
6. **Copy the connection details** and save them

---

## Step 3: Create Web Service on Render (3 minutes)

1. Click **New +** → **Web Service**
2. Connect your GitHub repo: `community-search-api`
3. Fill:
   - Name: `community-search-api`
   - Runtime: Python 3
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Click **Advanced**
5. Add Environment Variables:

```
DB_HOST = your-postgres-host.render.com
DB_PORT = 5432
DB_USER = postgres
DB_PASSWORD = your-postgres-password
DB_NAME = community_members_db
GEMINI_API_KEY = AIzaSyBOouWbG7RN6fPgDu2vaUebz3vrYm0G4WU
ADMIN_SECRET_KEY = your-secret-key-here
PYTHONUNBUFFERED = true
```

6. Click **Create Web Service**
7. Wait for "Live" status (2-5 minutes)

---

## Step 4: Initialize Database (1 minute)

Once "Live", run these commands:

```bash
# Get your Render URL (from dashboard)
YOUR_URL="https://community-search-api-xxxxx.onrender.com"
SECRET_KEY="your-secret-key-here"

# Initialize database
curl -X POST "$YOUR_URL/admin/setup-db?admin_key=$SECRET_KEY"

# Ingest data
curl -X POST "$YOUR_URL/admin/ingest-data?admin_key=$SECRET_KEY"
```

---

## Step 5: Test Your API (1 minute)

```bash
# Health check
curl $YOUR_URL/health

# Test query
curl -X POST "$YOUR_URL/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Who worked at Stripe?"}'

# View docs
# Open in browser: $YOUR_URL/docs
```

---

## ✅ You're Live!

Your API is now available at:
```
https://community-search-api-xxxxx.onrender.com
```

Share this URL and people can use your API! 🚀

---

## Common Issues

| Issue | Solution |
|-------|----------|
| Database connection failed | Check environment variables match exactly |
| Build fails | Run `pip install -r requirements.txt` locally |
| No data in results | Run `/admin/ingest-data` endpoint |
| Slow first request | Render free tier spins down - expected |
| API returns 502 | Check logs in Render dashboard |

---

## Files Needed

Make sure these are in your GitHub repo:
- ✅ `main.py` - Your FastAPI app
- ✅ `trial_text2sql.py` - Text2SQL engine
- ✅ `fuzzy_matching.py` - Entity matching
- ✅ `database_setup.py` - Database schema
- ✅ `ingestion_pipeline.py` - Data loading
- ✅ `db_config.py` - Database config
- ✅ `requirements.txt` - Dependencies
- ✅ `render.yaml` - Render config
- ✅ `Dockerfile` - Container config
- ✅ `data.csv` - Your data
- ✅ `.gitignore` - Ignore files

---

## Next Steps

1. ✅ Verify all endpoints work
2. 📊 Monitor logs for errors
3. 💡 Share your API URL with users
4. 🔐 Keep `ADMIN_SECRET_KEY` secure
5. 💰 Upgrade to paid if needed (free tier spins down)

**Estimated deployment time: 10-15 minutes**

Need help? Check `RENDER_DEPLOYMENT.md` for detailed instructions.
