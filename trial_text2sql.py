"""
Integrated Query Processor
Combines fuzzy matching + Text2SQL engine for end-to-end query processing
"""

import google.generativeai as genai
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Import the fuzzy matching components
from fuzzy_matching import QueryNormalizer
from db_config import get_db_connection, close_db_connection

MAX_RETRIES = 3
RETRY_DELAY = 2

# ============================================================================
# SCHEMA PROVIDER (for Text2SQL context)
# ============================================================================

class SchemaProvider:
    """Provides database schema context for LLM"""
    
    def __init__(self):
        pass
    
    def get_schema_context(self) -> str:
        """Get database schema as formatted text"""
        
        schema = """
# DATABASE SCHEMA

## Table: members
- member_id (TEXT, PRIMARY KEY): Unique identifier
- uri (TEXT, UNIQUE): URI identifier
- first_name (TEXT): Member's first name
- last_name (TEXT): Member's last name
- bio (TEXT): Short bio/description
- title (TEXT): Current or primary title

## Table: experiences
- member_id (TEXT, FOREIGN KEY): References members
- company (TEXT): Company name
- role (TEXT): Job title
- industry (TEXT): Industry classification
- city (TEXT): City of work location
- state (TEXT): State/Province
- country (TEXT): Country
- from_date (DATE): Employment start date
- to_date (DATE): Employment end date (NULL if current)
- is_current (BOOLEAN): Current role indicator
- description (TEXT): Role description

## Table: education
- member_id (TEXT, FOREIGN KEY): References members
- degree (TEXT): Degree type
- institute (TEXT): University/college name
- course (TEXT): Field of study
- from_date (DATE): Start date
- to_date (DATE): End date

## Table: domains
- member_id (TEXT, FOREIGN KEY): References members
- domain_name (TEXT): Domain/area of interest

## Table: content
- member_id (TEXT, FOREIGN KEY): References members
- content_text (TEXT): Member's bio/introduction

# IMPORTANT RULES FOR SQL GENERATION
1. Always use DISTINCT to avoid duplicate members
2. Use LEFT JOIN for experiences/education/domains (some members may not have all)
3. Use exact match for company names: company = '[exact_name]'
4. Use LIKE for text fields with fuzzy values
5. Order results by first_name, last_name
6. Use LIMIT 100 to prevent data overload
7. Write valid SQLite syntax
"""
        return schema

# ============================================================================
# TEXT2SQL ENGINE (Gemini-based)
# ============================================================================

class Text2SQLEngine:
    """Generate and execute SQL using Gemini API"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')
        self.schema_provider = SchemaProvider()
    
    def generate_sql(self, user_query: str, normalized_entities: Dict, 
                    retry_count: int = 0) -> Optional[str]:
        """
        Generate SQL from natural language query with normalized entities
        Retries on failure up to MAX_RETRIES times
        """
        
        if retry_count >= MAX_RETRIES:
            print(f"❌ Failed to generate SQL after {MAX_RETRIES} retries")
            return None
        
        try:
            schema_context = self.schema_provider.get_schema_context()
            
            # Build entity context for the prompt
            entity_context = self._build_entity_context(normalized_entities)
            
            prompt = f"""{schema_context}

# USER QUERY
{user_query}

# NORMALIZED ENTITIES (extracted and fuzzy-matched)
{entity_context}

# INSTRUCTIONS
1. Use the original query to understand user intent
2. Use normalized entities as exact filter values in WHERE clause
3. Generate ONLY valid SQLite SQL query
4. Use DISTINCT to avoid duplicates
5. Include member info and relevant details
6. Order by first_name, last_name
7. Do NOT include explanations or markdown
8. Return only the raw SQL query

# RESPONSE
Generate the SQL query:"""
            
            response = self.model.generate_content(prompt)
            sql = response.text.strip()
            
            # Clean up response
            sql = sql.replace("```sql", "").replace("```", "").strip()
            
            # Basic validation
            if not sql or len(sql) < 10:
                print(f"⚠️  Invalid SQL generated, retrying... (attempt {retry_count + 1})")
                time.sleep(RETRY_DELAY)
                return self.generate_sql(user_query, normalized_entities, retry_count + 1)
            
            if "SELECT" not in sql.upper():
                print(f"⚠️  SQL missing SELECT, retrying... (attempt {retry_count + 1})")
                time.sleep(RETRY_DELAY)
                return self.generate_sql(user_query, normalized_entities, retry_count + 1)
            
            return sql
        
        except Exception as e:
            print(f"⚠️  Error generating SQL: {str(e)}, retrying... (attempt {retry_count + 1})")
            time.sleep(RETRY_DELAY)
            return self.generate_sql(user_query, normalized_entities, retry_count + 1)
    
    def _build_entity_context(self, normalized_entities: Dict) -> str:
        """Build human-readable entity context for prompt"""
        
        if not normalized_entities:
            return "No entities found"
        
        lines = []
        for entity_type, entities in normalized_entities.items():
            if entities:
                lines.append(f"- {entity_type.title()}:")
                for original, matches in entities.items():
                    matches_str = ", ".join(f"'{m}'" for m in matches)
                    lines.append(f"  '{original}' → [{matches_str}]")
        
        return "\n".join(lines) if lines else "No entities found"
    
    def validate_sql(self, sql: str) -> bool:
        """Validate SQL syntax without executing"""
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(f"EXPLAIN {sql}")
            cursor.close()
            close_db_connection(conn)
            return True
        except Exception as e:
            print(f"❌ SQL Validation Error: {str(e)}")
            return False
    
    def execute_sql(self, sql: str) -> Tuple[Optional[List[Dict]], int]:
        """
        Execute SQL and return results
        Returns: (results, execution_time_ms)
        """
        
        start_time = time.time()
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(sql)
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            # Fetch results and convert to dicts
            rows = cursor.fetchall()
            results = [dict(zip(columns, row)) for row in rows]
            
            cursor.close()
            close_db_connection(conn)
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            return results, execution_time_ms
        
        except Exception as e:
            print(f"❌ Execution Error: {str(e)}")
            return None, int((time.time() - start_time) * 1000)

# ============================================================================
# QUERY PROCESSOR (Main Orchestrator)
# ============================================================================

class QueryProcessor:
    """
    Integrated query processor that combines:
    1. Fuzzy matching + entity extraction
    2. Text2SQL generation
    3. SQL execution
    4. Logging
    """
    
    def __init__(self, gemini_api_key: str):
        self.fuzzy_matcher = QueryNormalizer()
        self.text2sql = Text2SQLEngine(gemini_api_key)
    
    def process_query(self, user_query: str) -> Dict:
        """
        End-to-end query processing pipeline
        
        Returns:
        {
            "success": bool,
            "original_query": str,
            "extracted_entities": dict,
            "normalized_entities": dict,
            "generated_sql": str,
            "results": list,
            "results_count": int,
            "execution_time_ms": int,
            "error_message": str or None
        }
        """
        
        print(f"\n{'='*70}")
        print(f"PROCESSING QUERY: {user_query}")
        print(f"{'='*70}")
        
        start_time = time.time()
        
        # Step 1: Extract and normalize entities
        print("\n[Step 1] Extracting and normalizing entities...")
        normalization_result = self.fuzzy_matcher.normalize_query(user_query)
        
        extracted_entities = normalization_result["extracted_entities"]
        normalized_entities = normalization_result["normalized_entities"]
        
        print(f"  Extracted: {extracted_entities}")
        print(f"  Normalized: {normalized_entities}")
        
        # Step 2: Generate SQL
        print("\n[Step 2] Generating SQL...")
        sql = self.text2sql.generate_sql(user_query, normalized_entities)
        
        if not sql:
            print("❌ Failed to generate SQL")
            error_msg = "Failed to generate SQL query"
            self._log_query(user_query, None, 0, error_msg)
            return self._failed_response(user_query, error_msg)
        
        print(f"Generated SQL:\n{sql}\n")
        
        # Step 3: Validate SQL
        print("[Step 3] Validating SQL...")
        if not self.text2sql.validate_sql(sql):
            print("❌ SQL validation failed")
            error_msg = "Generated SQL is invalid"
            self._log_query(user_query, sql, 0, error_msg)
            return self._failed_response(user_query, error_msg)
        
        print("✓ SQL is valid\n")
        
        # Step 4: Execute SQL
        print("[Step 4] Executing SQL...")
        results, execution_time_ms = self.text2sql.execute_sql(sql)
        
        if results is None:
            print("❌ SQL execution failed")
            error_msg = "SQL execution failed"
            self._log_query(user_query, sql, execution_time_ms, error_msg)
            return self._failed_response(user_query, error_msg)
        
        print(f"✓ Query executed successfully")
        print(f"✓ Results: {len(results)} rows")
        print(f"✓ Execution time: {execution_time_ms}ms\n")
        
        # Step 5: Log query
        print("[Step 5] Logging query...")
        self._log_query(user_query, sql, execution_time_ms, None, results)
        
        total_time_ms = int((time.time() - start_time) * 1000)
        
        # Build response
        response = {
            "success": True,
            "original_query": user_query,
            "extracted_entities": extracted_entities,
            "normalized_entities": normalized_entities,
            "generated_sql": sql,
            "results": results,
            "results_count": len(results),
            "execution_time_ms": execution_time_ms,
            "total_time_ms": total_time_ms,
            "error_message": None
        }
        
        print(f"{'='*70}")
        print(f"✅ QUERY PROCESSED SUCCESSFULLY")
        print(f"{'='*70}\n")
        
        return response
    
    def _failed_response(self, user_query: str, error_message: str) -> Dict:
        """Return failed response"""
        
        return {
            "success": False,
            "original_query": user_query,
            "extracted_entities": {},
            "normalized_entities": {},
            "generated_sql": None,
            "results": [],
            "results_count": 0,
            "execution_time_ms": 0,
            "total_time_ms": 0,
            "error_message": error_message
        }
    
    def _log_query(self, user_query: str, sql: str, execution_time_ms: int, 
                  error_message: str = None, results: List[Dict] = None):
        """Log query to database"""
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            results_count = len(results) if results else 0
            
            cursor.execute("""
            INSERT INTO search_queries 
            (original_query, generated_sql, results_count, execution_time_ms, 
             error_message, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                user_query,
                sql,
                results_count,
                execution_time_ms,
                error_message,
                datetime.now().isoformat()
            ))
            
            # Log individual results
            if results:
                cursor.execute("SELECT lastval()")
                query_id = cursor.fetchone()[0]
                
                for result in results:
                    member_id = result.get("member_id")
                    if member_id:
                        cursor.execute("""
                        INSERT INTO query_results (query_id, member_id)
                        VALUES (%s, %s)
                        """, (query_id, member_id))
            
            conn.commit()
            cursor.close()
            close_db_connection(conn)
            
            print("✓ Query logged to database")
        
        except Exception as e:
            print(f"⚠️  Warning: Could not log query - {str(e)}")

# ============================================================================
# TESTING
# ============================================================================

def main():
    """Test the integrated query processor"""
    
    # Get API key
    api_key = "AIzaSyBOouWbG7RN6fPgDu2vaUebz3vrYm0G4WU"
    
    if not api_key:
        print("❌ API key is required")
        return
    
    # Initialize processor
    processor = QueryProcessor(api_key, DB_PATH)
    
    # Test queries
    test_queries = [
        "Who worked at Stripe?",
        "Who studied at IIT B?",
        "Who are founders in Bangalore?",
        "Who works on AI & ML?",
        "Who studied at MIT?",
    ]
    
    print("\n" + "="*70)
    print("INTEGRATED QUERY PROCESSOR - TEST")
    print("="*70)
    
    for query in test_queries:
        response = processor.process_query(query)
        
        print(f"Query: {query}")
        print(f"Success: {response['success']}")
        print(f"Results: {response['results_count']} rows")
        
        if response["results"]:
            print("Sample results:")
            for result in response["results"][:2]:
                print(f"  - {result.get('first_name')} {result.get('last_name')}")
        
        if response["error_message"]:
            print(f"Error: {response['error_message']}")
        
        print("\n" + "-"*70 + "\n")

if __name__ == "__main__":
    main()