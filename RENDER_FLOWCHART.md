# Render Deployment - Visual Flowchart

## Step-by-Step Visual Guide

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    RENDER DEPLOYMENT PROCESS                            │
└─────────────────────────────────────────────────────────────────────────┘

PHASE 1: GITHUB SETUP
────────────────────────────────────────────────────────────────────────

Step 1: Create GitHub Repo
   └─> Go to github.com/new
   └─> Name: community-search-api
   └─> Choose: Public
   └─> Create ✓

Step 2: Push Code
   └─> git init
   └─> git add .
   └─> git commit -m "..."
   └─> git remote add origin https://github.com/USERNAME/...
   └─> git push -u origin main ✓

       ⏱️ Time: ~5 minutes


PHASE 2: RENDER DATABASE SETUP
────────────────────────────────────────────────────────────────────────

Step 1: Login to Render
   └─> https://render.com/dashboard ✓

Step 2: Create PostgreSQL
   └─> New + → PostgreSQL
   └─> Name: community-db
   └─> Database: community_members_db
   └─> User: postgres
   └─> Region: (pick yours)
   └─> Create Database ✓
   └─> ⏳ Wait 2-3 minutes...

Step 3: Save Credentials
   └─> Copy Host, Password
   └─> Save somewhere safe ✓

       ⏱️ Time: ~5 minutes


PHASE 3: RENDER WEB SERVICE SETUP
────────────────────────────────────────────────────────────────────────

Step 1: Connect GitHub
   └─> New + → Web Service
   └─> Select: community-search-api
   └─> Connect ✓

Step 2: Configure Service
   └─> Name: community-search-api
   └─> Runtime: Python 3
   └─> Build: pip install -r requirements.txt
   └─> Start: uvicorn main:app --host 0.0.0.0 --port $PORT
   └─> Region: (same as DB) ✓

Step 3: Add Environment Variables
   └─> Click: Advanced
   └─> Add variables:
       ├─ DB_HOST = <from PostgreSQL>
       ├─ DB_PORT = 5432
       ├─ DB_USER = postgres
       ├─ DB_PASSWORD = <your password>
       ├─ DB_NAME = community_members_db
       ├─ GEMINI_API_KEY = AIzaSyBOouWbG7RN6...
       ├─ ADMIN_SECRET_KEY = your-secret
       └─ PYTHONUNBUFFERED = true ✓

Step 4: Deploy
   └─> Create Web Service
   └─> ⏳ Wait for "Live" status... (2-5 min)
   └─> ✓ Service is Live!

       ⏱️ Time: ~5 minutes


PHASE 4: DATABASE INITIALIZATION
────────────────────────────────────────────────────────────────────────

Step 1: Initialize Schema
   └─> curl -X POST "https://YOUR_URL/admin/setup-db?admin_key=YOUR_KEY"
   └─> ✓ Tables created!

Step 2: Load Data
   └─> curl -X POST "https://YOUR_URL/admin/ingest-data?admin_key=YOUR_KEY"
   └─> ✓ Data loaded!

       ⏱️ Time: ~2 minutes


PHASE 5: TEST & VERIFY
────────────────────────────────────────────────────────────────────────

Test 1: Health Check
   └─> curl https://YOUR_URL/health
   └─> Response: {"status": "healthy", ...} ✓

Test 2: Query Endpoint
   └─> curl -X POST "https://YOUR_URL/query" \
          -H "Content-Type: application/json" \
          -d '{"query": "Who worked at Stripe?"}'
   └─> Response: {"success": true, "results": [...]} ✓

Test 3: API Docs
   └─> Open: https://YOUR_URL/docs
   └─> Swagger UI loads ✓

       ⏱️ Time: ~1 minute


SUCCESS! ✨
────────────────────────────────────────────────────────────────────────

Your API is now LIVE at:
   https://community-search-api-XXXXX.onrender.com

You can:
   ✓ Share the URL with others
   ✓ Make queries from anywhere
   ✓ Monitor logs in dashboard
   ✓ Scale up if needed


TOTAL TIME: ~18 minutes
```

---

## Decision Tree

```
Are you ready to deploy?
│
├─ NO
│  └─> Make sure you have:
│     ├─ GitHub account
│     ├─ Render account
│     └─ data.csv file
│
└─ YES
   │
   ├─ Step 1: GitHub Setup (5 min)
   │  └─> Push code to GitHub
   │
   ├─ Step 2: Database (5 min)
   │  └─> Create PostgreSQL on Render
   │  └─> Save credentials
   │
   ├─ Step 3: Web Service (5 min)
   │  └─> Connect GitHub to Render
   │  └─> Set environment variables
   │
   ├─ Step 4: Initialize (2 min)
   │  └─> Run /admin/setup-db
   │  └─> Run /admin/ingest-data
   │
   └─ Step 5: Test (1 min)
      └─> Test /health endpoint
      └─> Test /query endpoint
      
      ✅ DONE! Your API is LIVE!
```

---

## What Happens Behind the Scenes

```
LOCAL MACHINE
┌────────────────────────────┐
│ Your Python Files          │
│ ├─ main.py                 │
│ ├─ trial_text2sql.py       │
│ ├─ fuzzy_matching.py       │
│ ├─ requirements.txt        │
│ └─ data.csv                │
└────────────────┬───────────┘
                 │ git push
                 ↓
GITHUB
┌────────────────────────────┐
│ Repository Stored          │
│ community-search-api       │
└────────────────┬───────────┘
                 │ webhook
                 ↓
RENDER.COM
┌────────────────────────────┐
│ Build Container            │
│ ├─ Read Dockerfile         │
│ ├─ Install requirements    │
│ ├─ Build image             │
│ └─ Start uvicorn app       │
└────────────────┬───────────┘
                 │
        ┌────────┴────────┐
        ↓                 ↓
    WEB SERVICE      POSTGRESQL DB
    (Python App)     (Your Data)
    Port 8000        Port 5432
                 │
                 ↓
           INTERNET
           (HTTPS)
                 │
                 ↓
            YOUR USERS
       (Can call your API)
```

---

## Environment Variables Flow

```
Local .env (for development)
         ↓
Render Environment Variables (for production)
         ↓
Python Code (reads environment variables)
         ↓
Connects to Database
         ↓
API Ready to Serve Requests
```

---

## URL Structure After Deployment

```
https://community-search-api-XXXXX.onrender.com
│          │                       │
│          │                       └─ Render.com domain
│          └────────────────────────── Your service name
└─────────────────────────────────────── HTTPS (secure)


Example Full URLs:

Health Check:
https://community-search-api-abc123.onrender.com/health

Query:
https://community-search-api-abc123.onrender.com/query

Docs:
https://community-search-api-abc123.onrender.com/docs

Admin Setup:
https://community-search-api-abc123.onrender.com/admin/setup-db?admin_key=YOUR_KEY
```

---

## What Each Phase Does

```
┌─────────────┐
│   Phase 1   │
│   GitHub    │ ──> Stores your code where Render can access it
└─────────────┘

┌─────────────┐
│   Phase 2   │ ──> Creates a PostgreSQL database server in the cloud
│   Database  │     where your data will be stored
└─────────────┘

┌─────────────┐
│   Phase 3   │ ──> Creates the web service that runs your FastAPI app
│   Web Svc   │     and connects it to the database
└─────────────┘

┌─────────────┐
│   Phase 4   │ ──> Creates the database tables and loads your data
│   Init DB   │     into the cloud database
└─────────────┘

┌─────────────┐
│   Phase 5   │ ──> Verifies everything works correctly
│   Testing   │     before sharing with others
└─────────────┘
```

---

## Status Indicators to Look For

```
✓ Green "Live"          → Web service is running
✓ "Available"           → PostgreSQL is ready
✓ No errors in logs     → Everything is working
✓ /health returns 200   → API is responding
✓ /query returns data   → Database is connected
```

---

Ready to start? Begin with **RENDER_QUICK_START.md**!
