# Render Deployment Checklist

## Before Deployment
- [ ] All code changes tested locally
- [ ] `requirements.txt` created
- [ ] `Dockerfile` created
- [ ] `render.yaml` created
- [ ] `.gitignore` created
- [ ] Admin endpoints added to `main.py`

## GitHub Setup
- [ ] GitHub account created
- [ ] Repository created (`community-search-api`)
- [ ] Code pushed to GitHub main branch
- [ ] Verify all files are in repository

## Render Database Setup
- [ ] Render account created
- [ ] PostgreSQL database created
- [ ] Database name: `community_members_db`
- [ ] Save connection credentials securely

## Render Web Service Setup
- [ ] GitHub repository connected to Render
- [ ] Web service name: `community-search-api`
- [ ] Build command set correctly
- [ ] Start command set correctly
- [ ] Environment variables added:
  - [ ] `DB_HOST`
  - [ ] `DB_PORT`
  - [ ] `DB_USER`
  - [ ] `DB_PASSWORD`
  - [ ] `DB_NAME`
  - [ ] `GEMINI_API_KEY`
  - [ ] `ADMIN_SECRET_KEY`
  - [ ] `PYTHONUNBUFFERED`

## After Deployment
- [ ] Web service shows "Live" status
- [ ] Copy your Render URL
- [ ] Test `/health` endpoint
- [ ] Test `/admin/setup-db?admin_key=YOUR_SECRET_KEY`
- [ ] Test `/admin/ingest-data?admin_key=YOUR_SECRET_KEY`
- [ ] Test `/query` endpoint with sample query
- [ ] Access `/docs` for API documentation
- [ ] Check logs for any errors

## Production Ready
- [ ] All endpoints working
- [ ] Health check returning data
- [ ] Queries returning results
- [ ] No errors in logs
- [ ] API URL bookmarked
- [ ] Documentation reviewed

## Monitoring
- [ ] Check logs regularly
- [ ] Monitor error rates
- [ ] Track response times
- [ ] Watch database usage

---

## Your Render URL
Once deployed, your API will be available at:
```
https://community-search-api-XXXXX.onrender.com
```

Share this URL with anyone who wants to use your API!

## Quick Test Commands

### Health Check
```bash
curl https://YOUR_RENDER_URL.onrender.com/health
```

### Initialize Database
```bash
curl -X POST "https://YOUR_RENDER_URL.onrender.com/admin/setup-db?admin_key=YOUR_SECRET_KEY"
```

### Ingest Data
```bash
curl -X POST "https://YOUR_RENDER_URL.onrender.com/admin/ingest-data?admin_key=YOUR_SECRET_KEY"
```

### Test Query
```bash
curl -X POST "https://YOUR_RENDER_URL.onrender.com/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Who worked at Stripe?"}'
```

### View API Docs
```
https://YOUR_RENDER_URL.onrender.com/docs
```

---

## Support

If you encounter issues:

1. Check Render logs: Dashboard → Your service → Logs
2. Verify environment variables are set
3. Ensure database is in "Available" status
4. Run `/admin/setup-db` before `/admin/ingest-data`
5. Check `data.csv` is in your repository

Good luck! 🚀
