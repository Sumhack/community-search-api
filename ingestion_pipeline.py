"""
Ingestion Pipeline for Community Member Search System
Loads CSV data into PostgreSQL database
"""

import csv
import json
import os
from typing import Tuple, Optional, List, Dict
from db_config import get_db_connection, close_db_connection

CSV_PATH = "data.csv"

# ============================================================================
# HELPER FUNCTIONS (defined first)
# ============================================================================

def parse_location(location_str: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Parse location string like "Seattle, Washington, United States"
    Returns: (city, state, country)
    """
    if not location_str:
        return None, None, None
    
    parts = [p.strip() for p in location_str.split(",")]
    
    if len(parts) == 3:
        return parts[0], parts[1], parts[2]
    elif len(parts) == 2:
        return parts[0], None, parts[1]
    elif len(parts) == 1:
        return parts[0], None, None
    else:
        return None, None, None

def insert_member(cursor, member_id: str, uri: str, first_name: str, 
                 last_name: str, bio: str, title: str):
    """Insert member into database"""
    cursor.execute("""
    INSERT INTO members 
    (member_id, uri, first_name, last_name, bio, title)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (member_id) DO UPDATE
    SET uri = %s, first_name = %s, last_name = %s, bio = %s, title = %s
    """, (member_id, uri, first_name, last_name, bio, title,
          uri, first_name, last_name, bio, title))

def insert_experience(cursor, member_id: str, company: str, role: str, 
                     industry: str, city: str, state: str, country: str,
                     from_date: str, to_date: str, is_current: bool,
                     description: str, company_size: str, 
                     company_website: str, company_linkedin: str):
    """Insert experience into database"""
    cursor.execute("""
    INSERT INTO experiences 
    (member_id, company, role, industry, city, state, country, 
     from_date, to_date, is_current, description, company_size, 
     company_website, company_linkedin)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (member_id, company, role, industry, city, state, country,
          from_date, to_date, is_current, description, company_size,
          company_website, company_linkedin))

def insert_education(cursor, member_id: str, degree: str, institute: str,
                    course: str, from_date: str, to_date: str):
    """Insert education into database"""
    cursor.execute("""
    INSERT INTO education 
    (member_id, degree, institute, course, from_date, to_date)
    VALUES (%s, %s, %s, %s, %s, %s)
    """, (member_id, degree, institute, course, from_date, to_date))

def insert_domain(cursor, member_id: str, domain_name: str):
    """Insert domain into database"""
    cursor.execute("""
    INSERT INTO domains (member_id, domain_name)
    VALUES (%s, %s)
    """, (member_id, domain_name))

def insert_content(cursor, member_id: str, content_text: str):
    """Insert content into database"""
    cursor.execute("""
    INSERT INTO content (member_id, content_text)
    VALUES (%s, %s)
    ON CONFLICT (member_id) DO UPDATE
    SET content_text = %s
    """, (member_id, content_text, content_text))

# ============================================================================
# MAIN INGESTION LOGIC
# ============================================================================

def ingest_data():
    """Main ingestion pipeline"""
    
    print("\n" + "="*60)
    print("INGESTION PIPELINE - CSV to PostgreSQL")
    print("="*60)
    
    # Check if files exist
    if not os.path.exists(CSV_PATH):
        print(f"❌ CSV file not found: {CSV_PATH}")
        return
    
    # Connect to database
    print(f"\n✓ Connecting to database...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
    except Exception as e:
        print(f"❌ Failed to connect to database: {str(e)}")
        print("Make sure PostgreSQL is running: docker-compose up -d")
        return
    
    # Statistics
    stats = {
        "members": 0,
        "experiences": 0,
        "education": 0,
        "domains": 0,
        "content": 0,
        "errors": []
    }
    
    # Read and process CSV
    print(f"✓ Reading CSV file: {CSV_PATH}\n")
    
    try:
        with open(CSV_PATH, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, start=2):  # start=2 (row 1 is header)
                try:
                    # Extract basic member info
                    member_id = (row.get("uri") or "").strip()
                    first_name = (row.get("first_name") or "").strip()
                    last_name = (row.get("last_name") or "").strip()
                    bio = (row.get("bio") or "").strip()
                    title = (row.get("title") or "").strip()
                    
                    if not member_id:
                        stats["errors"].append(f"Row {row_num}: Missing member_id/uri")
                        continue
                    
                    # Insert member
                    insert_member(cursor, member_id, member_id, first_name, 
                                 last_name, bio, title)
                    stats["members"] += 1
                    
                    # Parse and insert experiences
                    experience_str = row.get("experience", "[]").strip()
                    if experience_str:
                        try:
                            experiences = json.loads(experience_str)
                            for exp in experiences:
                                company = (exp.get("company") or "").strip()
                                if not company:  # Skip if no company
                                    continue
                                
                                role = (exp.get("role") or "").strip()
                                industry = (exp.get("enrichment", {}).get("industry") or "").strip()
                                from_date = exp.get("from_date")
                                to_date = exp.get("to_date")
                                is_current = exp.get("is_current", False)
                                description = (exp.get("description") or "").strip()
                                company_size = (exp.get("enrichment", {}).get("size") or "").strip()
                                company_website = (exp.get("enrichment", {}).get("website") or "").strip()
                                company_linkedin = (exp.get("enrichment", {}).get("linkedin_url") or "").strip()
                                
                                # Parse location
                                location_str = (exp.get("enrichment", {}).get("location") or "").strip()
                                city, state, country = parse_location(location_str)
                                
                                insert_experience(cursor, member_id, company, role, industry,
                                                city, state, country, from_date, to_date,
                                                is_current, description, company_size,
                                                company_website, company_linkedin)
                                stats["experiences"] += 1
                        except json.JSONDecodeError as e:
                            stats["errors"].append(f"Row {row_num}: Invalid experience JSON - {str(e)}")
                    
                    # Parse and insert education
                    education_str = row.get("education", "[]").strip()
                    if education_str:
                        try:
                            education_list = json.loads(education_str)
                            for edu in education_list:
                                institute = (edu.get("institute") or "").strip()
                                if not institute:  # Skip if no institute
                                    continue
                                
                                degree = (edu.get("degree") or "").strip()
                                course = (edu.get("course") or "").strip()
                                from_date = edu.get("from_date")
                                to_date = edu.get("to_date")
                                
                                insert_education(cursor, member_id, degree, institute,
                                               course, from_date, to_date)
                                stats["education"] += 1
                        except json.JSONDecodeError as e:
                            stats["errors"].append(f"Row {row_num}: Invalid education JSON - {str(e)}")
                    
                    # Parse and insert domains
                    domains_str = row.get("domains_of_exploration", "[]").strip()
                    if domains_str:
                        try:
                            # Try as JSON first
                            if domains_str.startswith("["):
                                domains_list = json.loads(domains_str)
                            else:
                                # Or comma-separated
                                domains_list = [d.strip() for d in domains_str.split(",")]
                            
                            for domain in domains_list:
                                domain = domain.strip()
                                if domain:
                                    insert_domain(cursor, member_id, domain)
                                    stats["domains"] += 1
                        except json.JSONDecodeError as e:
                            stats["errors"].append(f"Row {row_num}: Invalid domains JSON - {str(e)}")
                    
                    # Insert content
                    content = (row.get("content") or "").strip()
                    if content:
                        insert_content(cursor, member_id, content)
                        stats["content"] += 1
                    
                    if row_num % 100 == 0:
                        print(f"  Processed {row_num} rows...")
                
                except Exception as e:
                    stats["errors"].append(f"Row {row_num}: {str(e)}")
                    continue
        
        # Commit all changes
        conn.commit()
        
    except FileNotFoundError:
        print(f"❌ CSV file not found: {CSV_PATH}")
        cursor.close()
        close_db_connection(conn)
        return
    except Exception as e:
        print(f"❌ Error reading CSV: {str(e)}")
        cursor.close()
        close_db_connection(conn)
        return
    
    cursor.close()
    close_db_connection(conn)
    
    # Print results
    print("\n" + "="*60)
    print("INGESTION RESULTS")
    print("="*60)
    print(f"Members: {stats['members']}")
    print(f"Experiences: {stats['experiences']}")
    print(f"Education: {stats['education']}")
    print(f"Domains: {stats['domains']}")
    print(f"Content: {stats['content']}")
    
    if stats["errors"]:
        print(f"\n⚠️  Errors ({len(stats['errors'])}):")
        for error in stats["errors"][:10]:  # Show first 10
            print(f"  • {error}")
    
    # Verify
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    tables = ["members", "experiences", "education", "domains", "content"]
    print("\nRecord counts:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  • {table}: {count}")
    
    # Sample query
    print("\nSample data:")
    cursor.execute("""
    SELECT m.first_name, m.last_name, e.company, e.city
    FROM members m
    LEFT JOIN experiences e ON m.member_id = e.member_id
    WHERE e.company IS NOT NULL
    LIMIT 5
    """)
    
    for row in cursor.fetchall():
        print(f"  {row[0]} {row[1]} worked at {row[2]} ({row[3] if row[3] else 'Location N/A'})")
    
    cursor.close()
    close_db_connection(conn)
    
    print("\n" + "="*60)
    print("✅ INGESTION COMPLETE!")
    print("="*60 + "\n")

if __name__ == "__main__":
    ingest_data()