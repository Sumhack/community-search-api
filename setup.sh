#!/bin/bash
# Quick Start Script for PostgreSQL Setup

echo "🚀 Community Member Search - PostgreSQL Setup"
echo "=============================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Desktop."
    exit 1
fi

echo "✅ Docker and Docker Compose found"
echo ""

# Step 1: Start PostgreSQL
echo "📦 Step 1: Starting PostgreSQL with Docker..."
docker-compose up -d

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to start..."
sleep 5

# Check if PostgreSQL is running
if docker ps | grep -q community_db; then
    echo "✅ PostgreSQL is running"
else
    echo "❌ PostgreSQL failed to start"
    echo "Run: docker-compose logs postgres"
    exit 1
fi

echo ""
echo "📝 Step 2: Installing Python packages..."
pip install psycopg2-binary google-generativeai fuzzywuzzy python-Levenshtein fastapi uvicorn 2>/dev/null

echo ""
echo "🗄️  Step 3: Creating database schema..."
python database_setup.py

echo ""
echo "📥 Step 4: Ingesting data from CSV..."
python ingestion_pipeline.py

echo ""
echo "✅ Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Start the API:"
echo "   uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "2. Test the API:"
echo "   curl -X POST http://localhost:8000/query \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"query\": \"Who worked at Stripe?\"}'"
echo ""
echo "3. View API documentation:"
echo "   http://localhost:8000/docs"
echo ""
echo "Useful commands:"
echo "  - View logs:          docker-compose logs postgres"
echo "  - Stop database:      docker-compose down"
echo "  - Reset database:     docker-compose down -v"
echo "  - Access PostgreSQL:  psql -h localhost -U postgres -d community_members_db"
