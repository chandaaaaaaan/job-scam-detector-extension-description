import sqlite3
import json
from datetime import datetime

DB_FILE = "scam_jobs.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scam_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            job_title TEXT NOT NULL,
            description TEXT,
            label TEXT NOT NULL,
            risk_score INTEGER,
            reasons TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    try:
        cursor.execute("ALTER TABLE scam_jobs ADD COLUMN full_response TEXT")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()

def check_memory(company_name, job_title):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Fuzzy match could be implemented here; for simplicity, using exact match/lowercase
    # Or ILIKE style with LOWER
    cursor.execute('''
        SELECT label, risk_score, reasons, full_response
        FROM scam_jobs 
        WHERE LOWER(company_name) = LOWER(?) 
          AND LOWER(job_title) = LOWER(?)
        ORDER BY id DESC LIMIT 1
    ''', (company_name, job_title))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        full_resp = json.loads(result[3]) if len(result) > 3 and result[3] else {}
        response = {
            "label": result[0],
            "score": result[1],
            "reasons": json.loads(result[2]) if result[2] else [],
            "source": "memory",
            **full_resp
        }
        return response
    return None

def save_to_memory(company_name, job_title, description, label, risk_score, reasons, full_response=None):
    # Avoid duplicate exact entries
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id FROM scam_jobs 
        WHERE LOWER(company_name) = LOWER(?) 
          AND LOWER(job_title) = LOWER(?)
    ''', (company_name, job_title))
    
    if cursor.fetchone():
        conn.close()
        return False # Already exists

    reasons_str = json.dumps(reasons)
    full_response_str = json.dumps(full_response) if full_response else None
    cursor.execute('''
        INSERT INTO scam_jobs (company_name, job_title, description, label, risk_score, reasons, full_response, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (company_name, job_title, description, label, risk_score, reasons_str, full_response_str, datetime.now()))
    
    conn.commit()
    conn.close()
    return True

def get_report_count(company_name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM scam_jobs
        WHERE LOWER(company_name) = LOWER(?) AND label = 'Fake'
    ''', (company_name,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_company_job_count(company_name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(DISTINCT job_title) FROM scam_jobs
        WHERE LOWER(company_name) = LOWER(?)
    ''', (company_name,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_company_reports(company_name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT reasons FROM scam_jobs
        WHERE LOWER(company_name) = LOWER(?) AND label = 'Fake'
    ''', (company_name,))
    rows = cursor.fetchall()
    conn.close()
    
    past_feedbacks = []
    for r in rows:
        if r[0]:
            try:
                # reasons is stored as JSON array string
                past_feedbacks.extend(json.loads(r[0]))
            except:
                pass
    # return unique
    return list(set(past_feedbacks))

def get_company_positive_feedback(company_name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT reasons FROM scam_jobs
        WHERE LOWER(company_name) = LOWER(?) AND label = 'Real'
    ''', (company_name,))
    rows = cursor.fetchall()
    conn.close()
    
    past_feedbacks = []
    for r in rows:
        if r[0]:
            try:
                past_feedbacks.extend(json.loads(r[0]))
            except:
                pass
    return list(set(past_feedbacks))

def get_all_scams():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, company_name, job_title, label, risk_score, reasons, created_at, full_response
        FROM scam_jobs
        ORDER BY created_at DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        results.append({
            "id": r[0],
            "company_name": r[1],
            "job_title": r[2],
            "label": r[3],
            "risk_score": r[4],
            "reasons": json.loads(r[5]) if r[5] else [],
            "created_at": r[6]
        })
    return results
