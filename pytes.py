import sqlite3
import os
from datetime import datetime

# Database file location
DB_PATH = "south_park_commons_members.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
 SELECT DISTINCT T1.member_id, T1.first_name, T1.last_name, T1.title, T1.bio, T2.company, T2.role, T2.city FROM members AS T1 INNER JOIN experiences AS T2 ON T1.member_id = T2.member_id WHERE T2.role IN ('Founder', 'CEO / Co-Founder', 'Advocate and Co-Founder', 'Advisor, Founder', 'CEO / Founder', 'CEO & co-founder', 'CEO and Co-founder', 'CEO & Founder', 'C.E.O. - Founder') AND T2.city = 'Bangalore' ORDER BY T1.first_name, T1.last_name LIMIT 100
    """)
results = cursor.fetchall()
for row in results:
    print(row)
