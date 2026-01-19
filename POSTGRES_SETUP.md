# PostgreSQL Setup Guide

## Prerequisites
- Docker and Docker Compose installed on your machine
- Python 3.8+ with virtual environment activated

## Step 1: Install Required Python Packages

```bash
pip install psycopg2-binary google-generativeai fuzzywuzzy python-Levenshtein
```

## Step 2: Start PostgreSQL with Docker

```bash
docker-compose up -d
```

This will:
- Create a PostgreSQL 15 container named `community_db`
- Expose it on `localhost:5432`
- Create the database `community_members_db` with default credentials (postgres/postgres)

Verify PostgreSQL is running:
```bash
docker ps
```

You should see the `community_db` container running.

## Step 3: Create Database Schema

Run the database setup script:
```bash
python database_setup.py
```

This will:
- Create all required tables
- Create indices for performance
- Verify the database connection

## Step 4: Ingest Data from CSV

Run the ingestion pipeline:
```bash
python ingestion_pipeline.py
```

This will:
- Read data from `data.csv`
- Insert data into PostgreSQL
- Verify the data was loaded correctly

## Step 5: Start the FastAPI Application

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

### API Endpoints:
- **POST /query** - Search for members using natural language
- **GET /health** - Health check endpoint
- **GET /docs** - Swagger UI documentation
- **GET /redoc** - ReDoc documentation

## Testing the API

### Example Query:
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Who worked at Stripe?"}'
```

## Docker Commands Reference

```bash
# Start PostgreSQL
docker-compose up -d

# Stop PostgreSQL
docker-compose down

# View PostgreSQL logs
docker-compose logs postgres

# Access PostgreSQL CLI
psql -h localhost -U postgres -d community_members_db

# Stop and remove volumes (reset database)
docker-compose down -v
```

## Environment Variables (Optional)

Create a `.env` file to override defaults:
```
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=community_members_db
GEMINI_API_KEY=your_api_key_here
```

## Troubleshooting

### "Connection refused" error
- Ensure Docker is running: `docker ps`
- Ensure PostgreSQL container is running: `docker-compose up -d`
- Wait a few seconds for PostgreSQL to start completely

### "Database does not exist" error
- Run `python database_setup.py` first to create tables

### "No data" in results
- Run `python ingestion_pipeline.py` to load data from CSV

### Check database status
```bash
psql -h localhost -U postgres -d community_members_db -c "SELECT COUNT(*) FROM members;"
```

## Moving to Production

For production deployment:

1. **Use AWS RDS, Azure Database, or similar managed PostgreSQL service**
   - More reliable, automatic backups, scaling
   - No Docker needed for database

2. **Update DB credentials in environment variables**
   - Set `DB_HOST` to your RDS endpoint
   - Set secure `DB_PASSWORD`

3. **Deploy FastAPI to cloud** (AWS Lambda, Heroku, GCP, etc.)
   - Container support (keep Docker for FastAPI)
   - Auto-scaling, monitoring, logging

4. **No code changes needed** - Just update environment variables!

The beauty of this setup is that the same Python code works everywhere.
