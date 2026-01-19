# Render.com Deployment Guide

## Complete Step-by-Step Instructions

### **Phase 1: Prepare Your Code (Local)**

#### Step 1.1: Push Code to GitHub

```bash
# Initialize git (if not already done)
cd /Users/sumanacharya0075/developer/python
git init
git add .
git commit -m "Ready for production deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

Replace:
- `YOUR_USERNAME` with your GitHub username
- `YOUR_REPO_NAME` with your desired repo name

**Create repo on GitHub first:**
1. Go to [github.com/new](https://github.com/new)
2. Repository name: `community-search-api`
3. Choose **Public** (Render needs to access it)
4. Click **Create repository**
5. Then push your code using the commands above

---

### **Phase 2: Set Up PostgreSQL Database on Render**

#### Step 2.1: Login to Render Dashboard
1. Go to [render.com](https://render.com)
2. Sign in with your account
3. Dashboard should load

#### Step 2.2: Create PostgreSQL Database
1. Click **New +** button (top right)
2. Select **PostgreSQL**
3. Fill in the form:
   - **Name**: `community-db`
   - **Database**: `community_members_db`
   - **User**: `postgres`
   - **Region**: Select closest to you (e.g., `oregon` for US)
   - **PostgreSQL Version**: `15`
   - **Datadog API Key**: Leave blank
4. Click **Create Database**

⏳ **Wait 2-3 minutes** for the database to be ready

#### Step 2.3: Save Database Credentials
Once created, you'll see a page with connection details. **Copy and save these:**

```
Host: <something>.render.com
Port: 5432
Database: community_members_db
User: postgres
Password: <long_password>
Connection String: postgresql://postgres:<password>@<host>.render.com:5432/community_members_db
```

**Save these somewhere safe** - you'll need them in the next step.

---

### **Phase 3: Create Web Service on Render**

#### Step 3.1: Create New Web Service
1. Click **New +** → **Web Service**
2. **Connect your GitHub repository**:
   - Click **Connect Account** if prompted
   - Select your `community-search-api` repo
   - Click **Connect**

#### Step 3.2: Configure Web Service
Fill in the settings:

**Basic Settings:**
- **Name**: `community-search-api`
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Region**: Same as your database
- **Branch**: `main`

#### Step 3.3: Add Environment Variables
Click **Advanced** → **Add Environment Variable** for each:

```
DB_HOST = <from your PostgreSQL connection>
DB_PORT = 5432
DB_USER = postgres
DB_PASSWORD = <your postgres password>
DB_NAME = community_members_db
GEMINI_API_KEY = AIzaSyBOouWbG7RN6fPgDu2vaUebz3vrYm0G4WU
PYTHONUNBUFFERED = true
```

⚠️ **IMPORTANT**: Use exact values from your PostgreSQL database connection

#### Step 3.4: Deploy
Click **Create Web Service**

**Render will now:**
- Build your application
- Install dependencies
- Start your API
- Give you a public URL

✅ Wait for it to say **"Live"** (usually 2-5 minutes)

---

### **Phase 4: Initialize Database Schema**

Once your API is live, you need to create tables and load data.

#### Option A: Using the Management Endpoint (Recommended)

Add this to your `main.py` (before the `if __name__` block):

```python
# ============================================================================
# ADMIN ENDPOINTS (For Production Setup)
# ============================================================================

@app.post("/admin/setup-db")
async def setup_database(admin_key: str):
    """Initialize database schema - requires admin key"""
    
    admin_secret = os.getenv("ADMIN_SECRET_KEY", "change-me-in-production")
    
    if admin_key != admin_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        from database_setup import create_tables, create_indices
        from db_config import get_db_connection, close_db_connection
        
        print("Initializing database...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        create_tables(conn)
        create_indices(cursor, conn)
        
        cursor.close()
        close_db_connection(conn)
        
        return {
            "success": True,
            "message": "Database schema created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Setup failed: {str(e)}")

@app.post("/admin/ingest-data")
async def ingest_data_endpoint(admin_key: str):
    """Ingest data from CSV - requires admin key"""
    
    admin_secret = os.getenv("ADMIN_SECRET_KEY", "change-me-in-production")
    
    if admin_key != admin_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        from ingestion_pipeline import ingest_data
        
        print("Starting data ingestion...")
        ingest_data()
        
        return {
            "success": True,
            "message": "Data ingestion completed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
```

Then:

1. Add to Render environment variables:
   ```
   ADMIN_SECRET_KEY = your-secret-key-here
   ```

2. Call the setup endpoints:
   ```bash
   # Initialize database
   curl -X POST "https://YOUR_RENDER_URL.onrender.com/admin/setup-db?admin_key=your-secret-key-here"
   
   # Ingest data
   curl -X POST "https://YOUR_RENDER_URL.onrender.com/admin/ingest-data?admin_key=your-secret-key-here"
   ```

Replace:
- `YOUR_RENDER_URL` with your Render domain (e.g., `community-search-api-xyz.onrender.com`)
- `your-secret-key-here` with your admin key

---

### **Phase 5: Test Your API**

#### Test 1: Health Check
```bash
curl https://YOUR_RENDER_URL.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-19T12:00:00.000000"
}
```

#### Test 2: Query Endpoint
```bash
curl -X POST "https://YOUR_RENDER_URL.onrender.com/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Who worked at Stripe?"}'
```

#### Test 3: View API Documentation
```
https://YOUR_RENDER_URL.onrender.com/docs
```

Open in browser to see interactive Swagger UI.

---

## **Troubleshooting**

### **Database Connection Failed**
- Check environment variables match exactly
- Verify PostgreSQL database is in "Available" state on Render
- Check IP whitelist in Render PostgreSQL settings (should allow all)

### **Build Fails**
- Check logs in Render dashboard
- Run `pip install -r requirements.txt` locally to verify
- Check Python version is 3.11

### **Data Not Showing**
- Run `/admin/setup-db` endpoint first
- Run `/admin/ingest-data` endpoint second
- Check `data.csv` is in your repository

### **Slow Responses**
- Render free tier spins down after 15 minutes of inactivity
- First request after spin-down takes longer
- Upgrade to paid plan if you need always-on

### **View Logs**
In Render dashboard:
1. Click your web service
2. Click **Logs** tab
3. See real-time logs

---

## **Next Steps After Deployment**

1. ✅ Verify API works
2. ✅ Test with sample queries
3. 📊 Monitor logs for errors
4. 🔐 Change `ADMIN_SECRET_KEY` to something secure
5. 💰 Consider upgrading to paid plan if needed
6. 📝 Document API usage for users

---

## **Getting Your Public URL**

After deployment is "Live":

1. Click your web service
2. At the top, you'll see: `https://community-search-api-xyz.onrender.com`
3. This is your public API URL!
4. Share this with users

---

## **Cost Breakdown**

| Component | Cost |
|-----------|------|
| Web Service (Free) | $0 |
| PostgreSQL (Free) | $0 |
| **Total** | **$0** |

⚠️ Free tier limitations:
- Web service spins down after 15 minutes of inactivity
- PostgreSQL limited to 1GB (should be enough for your data)
- If you need always-on: $7/month web service

---

## **Production Checklist**

- [ ] Code pushed to GitHub
- [ ] `requirements.txt` created and updated
- [ ] Render account created
- [ ] PostgreSQL database created on Render
- [ ] Web service created on Render
- [ ] Environment variables set correctly
- [ ] Deployment completes (shows "Live")
- [ ] `/health` endpoint returns healthy
- [ ] `/admin/setup-db` called successfully
- [ ] `/admin/ingest-data` called successfully
- [ ] `/query` endpoint returns results
- [ ] API documentation accessible at `/docs`

Once all checked ✅ - **You're live on the internet!** 🚀
