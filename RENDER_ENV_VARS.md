# Render Environment Variables Reference

## Overview
These are the environment variables you need to set in Render for your deployment.

## How to Set Them in Render

1. Go to your Web Service Dashboard
2. Click **Settings**
3. Scroll to **Environment**
4. Click **Add Environment Variable**
5. Enter each key-value pair below

---

## Database Variables

### DB_HOST
- **Value**: From your PostgreSQL connection string
- **Example**: `dpgXXXXXXXXXXXXXXXXXX.render.com`
- **Where to find**: Render PostgreSQL dashboard → Connection string (before the `:`)

### DB_PORT
- **Value**: `5432`
- **Note**: Always this for PostgreSQL

### DB_USER
- **Value**: `postgres`
- **Note**: Default PostgreSQL user

### DB_PASSWORD
- **Value**: Your PostgreSQL password
- **Example**: `aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890`
- **Where to find**: Render PostgreSQL dashboard → Connection details

### DB_NAME
- **Value**: `community_members_db`
- **Note**: Must match what you created in PostgreSQL

---

## API Keys

### GEMINI_API_KEY
- **Value**: `AIzaSyBOouWbG7RN6fPgDu2vaUebz3vrYm0G4WU`
- **Note**: Existing key from your code

### ADMIN_SECRET_KEY
- **Value**: Create your own secure key
- **Example**: `super_secret_key_12345`
- **Note**: You'll use this to access `/admin/setup-db` and `/admin/ingest-data`
- **⚠️ IMPORTANT**: Keep this secret, don't share it!

---

## Application Variables

### PYTHONUNBUFFERED
- **Value**: `true`
- **Note**: Shows logs in real-time

### PYTHON_VERSION (optional)
- **Value**: `3.11`
- **Note**: Already in render.yaml

---

## Complete Environment Variables List

Add these exactly as shown (copy-paste):

```
DB_HOST=<your-postgres-host>
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=<your-postgres-password>
DB_NAME=community_members_db
GEMINI_API_KEY=AIzaSyBOouWbG7RN6fPgDu2vaUebz3vrYm0G4WU
ADMIN_SECRET_KEY=<your-secret-key>
PYTHONUNBUFFERED=true
```

---

## Finding Your PostgreSQL Connection Details

1. Go to Render Dashboard
2. Click on your PostgreSQL database (`community-db`)
3. Look for the **External Connection String**
4. Format is: `postgresql://postgres:PASSWORD@HOST:5432/community_members_db`

From this string, extract:
- **DB_HOST**: `HOST` part
- **DB_PASSWORD**: `PASSWORD` part
- Everything else is fixed

---

## Testing Environment Variables

After adding all variables, test they're set correctly:

```bash
# This checks if your web service can connect to database
curl https://your-render-url.onrender.com/health
```

Expected response (if variables are correct):
```json
{
  "status": "healthy",
  "timestamp": "2026-01-19T..."
}
```

If error, double-check:
- Database is in "Available" status
- All variables match exactly (case-sensitive)
- No extra spaces in values

---

## Securing Sensitive Data

⚠️ **IMPORTANT**:
- Never commit `.env` files to GitHub
- Don't share your `ADMIN_SECRET_KEY`
- Don't share your `DB_PASSWORD`
- `.gitignore` already configured to exclude `.env`

---

## Example: What Render Dashboard Looks Like

```
Environment
├── DB_HOST             → dpgXXXXXXXXXXXXXX.render.com
├── DB_PORT             → 5432
├── DB_USER             → postgres
├── DB_PASSWORD         → aBcDeFgHiJkLmNoPqRs...
├── DB_NAME             → community_members_db
├── GEMINI_API_KEY      → AIzaSyBOouWbG7RN6fPgDu2vaUebz3vrYm0G4WU
├── ADMIN_SECRET_KEY    → super_secret_key_12345
└── PYTHONUNBUFFERED    → true
```

---

## Troubleshooting

### "Database connection failed"
- Check `DB_HOST` doesn't include `postgresql://` prefix
- Check `DB_PASSWORD` is the full password
- Verify PostgreSQL is in "Available" status

### "Environment variable not found"
- Variables must be added in Render dashboard, not in code
- Case-sensitive: `DB_HOST` ≠ `db_host`
- No spaces around `=`

### Still having issues?
1. Check logs in Render dashboard
2. Look for error messages
3. Verify each variable one by one

---

## After Deployment

Once variables are set and service is Live:

```bash
# Initialize database
curl -X POST "https://your-url.onrender.com/admin/setup-db?admin_key=YOUR_ADMIN_SECRET_KEY"

# Load data
curl -X POST "https://your-url.onrender.com/admin/ingest-data?admin_key=YOUR_ADMIN_SECRET_KEY"

# Test query
curl -X POST "https://your-url.onrender.com/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Who worked at Stripe?"}'
```

Replace `YOUR_ADMIN_SECRET_KEY` with the value you set for `ADMIN_SECRET_KEY`.

---

## Summary Checklist

- [ ] DB_HOST set (from PostgreSQL connection)
- [ ] DB_PORT set to 5432
- [ ] DB_USER set to postgres
- [ ] DB_PASSWORD set (from PostgreSQL)
- [ ] DB_NAME set to community_members_db
- [ ] GEMINI_API_KEY set
- [ ] ADMIN_SECRET_KEY set (your choice)
- [ ] PYTHONUNBUFFERED set to true
- [ ] All variables saved in Render
- [ ] Service redeployed after changes

Once all set, you're ready to deploy! 🚀
