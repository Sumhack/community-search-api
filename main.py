"""
FastAPI REST API for Community Member Search System
Integrates fuzzy matching and Text2SQL for natural language queries
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import time
import logging
import os

from trial_text2sql import QueryProcessor
# from db_config import GEMINI_API_KEY as API_KEY_ENV

# ============================================================================
# CONFIGURATION
# ============================================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBOouWbG7RN6fPgDu2vaUebz3vrYm0G4WU")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# PYDANTIC MODELS (Request/Response)
# ============================================================================

class QueryRequest(BaseModel):
    """Request model for /query endpoint"""
    query: str

class QueryResult(BaseModel):
    """Single search result"""
    member_id: str
    first_name: str
    last_name: str
    title: Optional[str] = None
    bio: Optional[str] = None

class QueryResponse(BaseModel):
    """Response model for /query endpoint"""
    success: bool
    original_query: str
    results: List[Dict]
    results_count: int
    extracted_entities: Optional[Dict] = None
    normalized_entities: Optional[Dict] = None
    generated_sql: Optional[str] = None
    execution_time_ms: Optional[int] = None
    total_time_ms: Optional[int] = None
    timestamp: str
    error_message: Optional[str] = None

class HealthResponse(BaseModel):
    """Response model for /health endpoint"""
    status: str
    timestamp: str

# ============================================================================
# FASTAPI APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title="Community Member Search API",
    description="Search community members using natural language queries",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (change for production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# INITIALIZE COMPONENTS
# ============================================================================

# logger.info("Initializing QueryNormalizer...")
# normalizer = QueryNormalizer(DB_PATH)

# logger.info("Initializing Text2SQLEngine...")
# text2sql = Text2SQLEngine(GEMINI_API_KEY, DB_PATH)

# logger.info("Initialization complete")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def log_query_to_db(user_query: str, generated_sql: str, results_count: int,
                   execution_time_ms: int, error_message: str = None,
                   results: List[Dict] = None):
    """Log query and results to database"""
    
    # Logging is now handled by QueryProcessor._log_query()
    logger.info(f"Query logged: {user_query[:50]}...")

def create_error_response(query: str, error_message: str) -> Dict:
    """Create error response"""
    
    return {
        "success": False,
        "query": query,
        "results": [],
        "results_count": 0,
        "extracted_entities": None,
        "normalized_entities": None,
        "execution_time_ms": None,
        "timestamp": datetime.now().isoformat(),
        "error_message": error_message
    }

def create_success_response(query: str, results: List[Dict],
                          extracted_entities: Dict,
                          normalized_entities: Dict,
                          execution_time_ms: int,
                          generated_sql: str = None) -> Dict:
    """Create success response"""
    
    return {
        "success": True,
        "query": query,
        "results": results,
        "results_count": len(results),
        "extracted_entities": extracted_entities,
        "normalized_entities": normalized_entities,
        "execution_time_ms": execution_time_ms,
        "timestamp": datetime.now().isoformat(),
        "error_message": None
    }

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post("/query", response_model=QueryResponse)
async def search_query(request: QueryRequest):
    """
    Search for community members using natural language query
    
    Example:
    {
        "query": "Who worked at Stripe in Bangalore?"
    }
    
    Returns:
    - List of matching members
    - Extracted and normalized entities
    - Generated SQL query
    - Execution time
    - Timestamp
    """
    
    user_query = request.query.strip()
    
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    logger.info(f"Processing query: {user_query}")
    start_time = time.time()
    
    try:
        processor = QueryProcessor(GEMINI_API_KEY)
        response = processor.process_query(user_query)
        
        # Add timestamp to response
        response["timestamp"] = datetime.now().isoformat()
        
        if response["results"]:
            logger.info(f"Query returned {len(response['results'])} results")
            for result in response["results"][:2]:
                logger.info(f"  - {result.get('first_name')} {result.get('last_name')}")
        
        return response
    
    except Exception as e:
        error_msg = f"Internal server error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        return {
            "success": False,
            "original_query": user_query,
            "results": [],
            "results_count": 0,
            "extracted_entities": None,
            "normalized_entities": None,
            "generated_sql": None,
            "execution_time_ms": execution_time_ms,
            "total_time_ms": None,
            "timestamp": datetime.now().isoformat(),
            "error_message": error_msg
        }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns:
    - status: "healthy" if API is running
    - timestamp: Current timestamp
    """
    
    logger.info("Health check requested")
    
    try:
        # Try to connect to database
        from db_config import get_db_connection, close_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM members")
        member_count = cursor.fetchone()[0]
        cursor.close()
        close_db_connection(conn)
        
        logger.info(f"Database healthy: {member_count} members")
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection failed")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    
    return {
        "message": "Community Member Search API",
        "version": "1.0.0",
        "endpoints": {
            "search": "POST /query",
            "health": "GET /health",
            "docs": "GET /docs",
            "redoc": "GET /redoc"
        }
    }

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    
    logger.error(f"HTTP Exception: {exc.detail}")
    
    return {
        "success": False,
        "error_message": exc.detail,
        "timestamp": datetime.now().isoformat()
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    
    logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
    
    return {
        "success": False,
        "error_message": "An unexpected error occurred",
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# ADMIN ENDPOINTS (For Production Setup)
# ============================================================================

@app.post("/admin/setup-db")
async def setup_database(admin_key: str):
    """
    Initialize database schema - requires admin key
    
    Usage:
    curl -X POST "https://your-domain.onrender.com/admin/setup-db?admin_key=YOUR_SECRET_KEY"
    """
    
    admin_secret = os.getenv("ADMIN_SECRET_KEY", "change-me-in-production")
    
    if admin_key != admin_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        from database_setup import create_tables, create_indices
        from db_config import get_db_connection, close_db_connection
        
        logger.info("Initializing database...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        create_tables(conn)
        create_indices(cursor, conn)
        
        cursor.close()
        close_db_connection(conn)
        
        logger.info("Database schema created successfully")
        
        return {
            "success": True,
            "message": "Database schema created successfully"
        }
    except Exception as e:
        logger.error(f"Setup failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Setup failed: {str(e)}")

@app.post("/admin/ingest-data")
async def ingest_data_endpoint(admin_key: str):
    """
    Ingest data from CSV - requires admin key
    
    Usage:
    curl -X POST "https://your-domain.onrender.com/admin/ingest-data?admin_key=YOUR_SECRET_KEY"
    """
    
    admin_secret = os.getenv("ADMIN_SECRET_KEY", "change-me-in-production")
    
    if admin_key != admin_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        from ingestion_pipeline import ingest_data
        
        logger.info("Starting data ingestion...")
        ingest_data()
        
        logger.info("Data ingestion completed")
        
        return {
            "success": True,
            "message": "Data ingestion completed"
        }
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on API startup"""
    
    logger.info("=" * 70)
    logger.info("Community Member Search API Starting Up")
    logger.info("=" * 70)
    logger.info("Database: PostgreSQL (Docker)")
    logger.info(f"Fuzzy Matcher: Initialized")
    logger.info(f"Text2SQL Engine: Initialized")
    logger.info("API Ready to accept requests")
    logger.info("=" * 70)

@app.on_event("shutdown")
async def shutdown_event():
    """Run on API shutdown"""
    
    logger.info("=" * 70)
    logger.info("Community Member Search API Shutting Down")
    logger.info("=" * 70)

# ============================================================================
# RUN LOCALLY
# ============================================================================

# if __name__ == "__main__":
#     import uvicorn
    
#     uvicorn.run(
#         "main:app",
#         host="0.0.0.0",
#         port=8000,
#         reload=True,
#         log_level="info"
#     )

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )