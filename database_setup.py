"""
Database Setup Script for Community Member Search System
Creates PostgreSQL database with normalized schema
Run this script to initialize the database locally
"""

import psycopg2
from psycopg2 import sql
import os
from datetime import datetime
from db_config import get_db_connection, close_db_connection, DatabasePool

def create_tables(conn):
    """Create all tables in PostgreSQL database"""
    
    cursor = conn.cursor()
    
    print("Creating tables...")
    
    # 1. MEMBERS Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS members (
        member_id TEXT PRIMARY KEY,
        uri TEXT UNIQUE NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        bio TEXT,
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("✓ Created MEMBERS table")
    
    # 2. EXPERIENCES Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS experiences (
        experience_id SERIAL PRIMARY KEY,
        member_id TEXT NOT NULL,
        company TEXT NOT NULL,
        role TEXT,
        industry TEXT,
        city TEXT,
        state TEXT,
        country TEXT,
        from_date DATE,
        to_date DATE,
        is_current BOOLEAN DEFAULT FALSE,
        description TEXT,
        company_size TEXT,
        company_website TEXT,
        company_linkedin TEXT,
        FOREIGN KEY (member_id) REFERENCES members(member_id) ON DELETE CASCADE
    )
    """)
    print("✓ Created EXPERIENCES table")
    
    # 3. EDUCATION Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS education (
        education_id SERIAL PRIMARY KEY,
        member_id TEXT NOT NULL,
        degree TEXT,
        institute TEXT NOT NULL,
        course TEXT,
        from_date DATE,
        to_date DATE,
        FOREIGN KEY (member_id) REFERENCES members(member_id) ON DELETE CASCADE
    )
    """)
    print("✓ Created EDUCATION table")
    
    # 4. DOMAINS Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS domains (
        domain_id SERIAL PRIMARY KEY,
        member_id TEXT NOT NULL,
        domain_name TEXT NOT NULL,
        FOREIGN KEY (member_id) REFERENCES members(member_id) ON DELETE CASCADE
    )
    """)
    print("✓ Created DOMAINS table")
    
    # 5. CONTENT Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS content (
        content_id SERIAL PRIMARY KEY,
        member_id TEXT NOT NULL UNIQUE,
        content_text TEXT,
        FOREIGN KEY (member_id) REFERENCES members(member_id) ON DELETE CASCADE
    )
    """)
    print("✓ Created CONTENT table")
    
    # 6. SEARCH_QUERIES Table (Logging)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS search_queries (
        query_id SERIAL PRIMARY KEY,
        original_query TEXT NOT NULL,
        generated_sql TEXT,
        results_count INTEGER,
        execution_time_ms INTEGER,
        error_message TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ip_address TEXT,
        user_agent TEXT
    )
    """)
    print("✓ Created SEARCH_QUERIES table")
    
    # 7. QUERY_RESULTS Table (Logging)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS query_results (
        result_id SERIAL PRIMARY KEY,
        query_id INTEGER NOT NULL,
        member_id TEXT NOT NULL,
        relevance_score REAL,
        FOREIGN KEY (query_id) REFERENCES search_queries(query_id) ON DELETE CASCADE,
        FOREIGN KEY (member_id) REFERENCES members(member_id)
    )
    """)
    print("✓ Created QUERY_RESULTS table")
    
    conn.commit()
    print("\n✅ All tables created successfully!")
    
    # Create indices for better query performance
    create_indices(cursor, conn)
    
    

def create_indices(cursor, conn):
    """Create indices for frequently searched columns"""
    
    print("\nCreating indices...")
    
    indices = [
        # MEMBERS indices
        ("CREATE INDEX IF NOT EXISTS idx_members_first_name ON members(first_name)", "members.first_name"),
        ("CREATE INDEX IF NOT EXISTS idx_members_last_name ON members(last_name)", "members.last_name"),
        
        # EXPERIENCES indices
        ("CREATE INDEX IF NOT EXISTS idx_exp_member_id ON experiences(member_id)", "experiences.member_id"),
        ("CREATE INDEX IF NOT EXISTS idx_exp_company ON experiences(company)", "experiences.company"),
        ("CREATE INDEX IF NOT EXISTS idx_exp_city ON experiences(city)", "experiences.city"),
        ("CREATE INDEX IF NOT EXISTS idx_exp_state ON experiences(state)", "experiences.state"),
        ("CREATE INDEX IF NOT EXISTS idx_exp_country ON experiences(country)", "experiences.country"),
        ("CREATE INDEX IF NOT EXISTS idx_exp_role ON experiences(role)", "experiences.role"),
        ("CREATE INDEX IF NOT EXISTS idx_exp_industry ON experiences(industry)", "experiences.industry"),
        ("CREATE INDEX IF NOT EXISTS idx_exp_is_current ON experiences(is_current)", "experiences.is_current"),
        
        # EDUCATION indices
        ("CREATE INDEX IF NOT EXISTS idx_edu_member_id ON education(member_id)", "education.member_id"),
        ("CREATE INDEX IF NOT EXISTS idx_edu_institute ON education(institute)", "education.institute"),
        ("CREATE INDEX IF NOT EXISTS idx_edu_degree ON education(degree)", "education.degree"),
        
        # DOMAINS indices
        ("CREATE INDEX IF NOT EXISTS idx_dom_member_id ON domains(member_id)", "domains.member_id"),
        ("CREATE INDEX IF NOT EXISTS idx_dom_name ON domains(domain_name)", "domains.domain_name"),
        
        # CONTENT indices
        ("CREATE INDEX IF NOT EXISTS idx_content_member_id ON content(member_id)", "content.member_id"),
        
        # SEARCH_QUERIES indices
        ("CREATE INDEX IF NOT EXISTS idx_sq_timestamp ON search_queries(timestamp)", "search_queries.timestamp"),
        
        # QUERY_RESULTS indices
        ("CREATE INDEX IF NOT EXISTS idx_qr_query_id ON query_results(query_id)", "query_results.query_id"),
        ("CREATE INDEX IF NOT EXISTS idx_qr_member_id ON query_results(member_id)", "query_results.member_id"),
    ]
    
    for sql, index_name in indices:
        cursor.execute(sql)
        print(f"✓ Created index: {index_name}")
    
    conn.commit()

def insert_sample_data(conn):
    """Insert sample data for testing (from the provided record)"""
    
    cursor = conn.cursor()
    print("\nInserting sample data...")
    
    # Sample member - Deepak Joy Cheenath
    cursor.execute("""
    INSERT INTO members 
    (member_id, uri, first_name, last_name, bio, title)
    VALUES ('cPnobU', 'cPnobU', 'Deepak', 'Cheenath', 
          'Co-founder @ Quizizz', 'Co-founder @ Quizizz')
    """)
    
    #sample experiences

    experiences = [
        ("cPnobU", "Quizizz Inc.", "Co-Founder", "E-Learning", 
         "Santa Monica", "California", "United States", 
         "2015-02-01", None, True, 
         "Quizizz empowers teachers to engage and motivate their students.",
         "201-500", "https://quizizz.com", "https://www.linkedin.com/company/quizizz/"),
        
        ("cPnobU", "WizenWorld", "Co-Founder", "E-Learning",
         None, None, None,
         "2013-06-01", "2015-01-01", False,
         "WizenWorld is role-playing style game to learn middle school mathematics.",
         "1-10", "https://wizenworld.com", "https://www.linkedin.com/company/wizen-world/"),
        
        ("cPnobU", "Amazon", "Software Development Engineer", "Internet",
         "Seattle", "Washington", "United States",
         "2011-12-01", "2013-06-01", False,
         "Worked on marketing activities targeted at Amazon Sellers, including SEO, UI design, A/B testing and analytics.",
         "10001+", "https://amazon.com", "https://www.linkedin.com/company/amazon/"),
        
        ("cPnobU", "SAP Labs", "Intern", "Computer Software",
         None, None, "Germany",
         "2010-06-01", "2010-12-01", False,
         "Worked on creating a spreadsheet module for SAP Streamwork online collaboration suite.",
         "10001+", "https://sap.com", "https://www.linkedin.com/company/sap/"),
    ]
    
    for exp in experiences:
        cursor.execute("""
        INSERT INTO experiences 
        (member_id, company, role, industry, city, state, country, 
         from_date, to_date, is_current, description, company_size, 
         company_website, company_linkedin)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       
        """, exp)
    
    # # Sample education
    # education_data = [
    #     ("cPnobU", "M.Sc. (tech)", "Information Systems", 
    #      "2007-01-01", "2011-01-01", 
    #      "Birla Institute of Technology and Science, Pilani"),
        
    #     ("cPnobU", "12th board CBSE", None,
    #      "2005-01-01", "2007-01-01",
    #      "Delhi Public School - R. K. Puram"),
    # ]
    
    # for edu in education_data:
    #     cursor.execute("""
    #     INSERT INTO education 
    #     (member_id, degree, course, from_date, to_date, institute)
    #     VALUES (?, ?, ?, ?, ?, ?)
    #     """, edu)
    
    # # Sample domains
    # domains = ["SaaS", "E-Learning"]
    # for domain in domains:
    #     cursor.execute("""
    #     INSERT INTO domains (member_id, domain_name)
    #     VALUES (?, ?)
    #     """, ("cPnobU", domain))
    
    # # Sample content
    # cursor.execute("""
    # INSERT INTO content (member_id, content_text)
    # VALUES (?, ?)
    # """, ("cPnobU", "Co-founder at Quizizz. Previously worked at Amazon and SAP."))
    
    # conn.commit()
    # print("✓ Sample data inserted successfully!")

def verify_database(conn):
    """Verify database was created and print basic stats"""
    
    cursor = conn.cursor()
    
    print("\n" + "="*50)
    print("DATABASE VERIFICATION")
    print("="*50)
    
    # Get all tables
    cursor.execute("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_schema = 'public' ORDER BY table_name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"\nTables created: {len(tables)}")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  • {table}: {count} records")
    
    # Sample query
    print("\n" + "="*50)
    print("SAMPLE QUERY TEST")
    print("="*50)
    print("\nQuery: SELECT * FROM members WHERE first_name = 'Deepak'")
    
    cursor.execute("""
    SELECT *
    FROM experiences
   
    """)
    # WHERE first_name = 'Deepak'
    result = cursor.fetchone()
    if result:
        print(f"Result: {result}")
        print("✅ Database query works!")
    else:
        print("No results found (expected if no data loaded yet)")
    
    

def clear_sample_data(conn):
    """Clear all sample data from tables"""
    
    cursor = conn.cursor()
    print("\nClearing existing sample data...")
    
    # Delete in reverse order of foreign key dependencies
    cursor.execute("DELETE FROM query_results")
    cursor.execute("DELETE FROM search_queries")
    cursor.execute("DELETE FROM content")
    cursor.execute("DELETE FROM domains")
    cursor.execute("DELETE FROM education")
    cursor.execute("DELETE FROM experiences")
    cursor.execute("DELETE FROM members")
    
    conn.commit()
    print("✓ All sample data cleared!")

def main():
    """Main execution"""
    
    print("\n" + "="*60)
    print("COMMUNITY MEMBER SEARCH SYSTEM - DATABASE SETUP")
    print("="*60)
    
    try:
        conn = get_db_connection()
        print(conn)
        # Create tables
        #create_tables(conn)

        # #insert sample data
        # insert_sample_data(conn)

        
        # # Verify
        # verify_database(conn)
        
        # #clear sample data
        # clear_sample_data(conn)

        # close db connection
        #close_db_connection(conn)
        
        print("\n" + "="*60)
        print(f"✅ DATABASE SETUP COMPLETE!")
        print("="*60 + "\n")
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nMake sure PostgreSQL is running with Docker:")
        print("  docker-compose up -d")
        print("\nAnd environment variables are set correctly.")


if __name__ == "__main__":
    main()