import sqlite3
from datetime import datetime

DB_PATH = "memory.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_trace (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                file_type TEXT,
                intent TEXT,
                agent TEXT,
                extracted_fields TEXT,
                action TEXT,
                timestamp TEXT
            )
        ''')
        conn.commit()

def log_trace(filename, file_type, intent, agent, extracted_fields, action):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO agent_trace (filename, file_type, intent, agent, extracted_fields, action, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            filename,
            file_type,
            intent,
            agent,
            str(extracted_fields),  # or json.dumps()
            action,
            datetime.now().isoformat()
        ))
        conn.commit()

def get_all_traces():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM agent_trace")
        return cursor.fetchall()
