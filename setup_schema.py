import sqlite3
import os

# Define the database file path
DB_FILE = 'legisq.db'

def get_db_connection():
    """Returns a connection object to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    # Allows column names to be accessed like dictionary keys
    conn.row_factory = sqlite3.Row 
    return conn

def initialize_database():
    """Creates all necessary tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # --- 1. Ministries Table (Metadata)
    # Used for codes (XX in BL-XX-YYYY) and filtering
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ministries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT UNIQUE NOT NULL
        )
    """)

    # --- 2. States Table (Metadata)
    # Used for State Assemblies and codes (ZZ in ZZ-XX-YYYY)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT UNIQUE NOT NULL
        )
    """)
    
    # --- 3. Bills Table (Lok Sabha, Rajya Sabha, State Assemblies)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_code TEXT UNIQUE NOT NULL,
            bill_name TEXT NOT NULL,
            introduced_by TEXT,
            ministry_code TEXT,
            legislative_body TEXT NOT NULL, -- 'Lok Sabha', 'Rajya Sabha', 'State Assembly'
            state_code TEXT, -- NULL for Lok/Rajya Sabha
            votes_favour INTEGER DEFAULT 0,
            votes_against INTEGER DEFAULT 0,
            current_status TEXT NOT NULL, -- 'Passed', 'Not Passed', 'Pending'
            approval_status TEXT, -- 'President Approval' or 'Governor Approval'
            approval_result TEXT, -- 'Yes', 'No', 'Pending'
            is_money_bill BOOLEAN, -- Constraint check here (Rajya Sabha cannot introduce)
            pdf_path TEXT,
            introduced_date DATE,
            FOREIGN KEY (ministry_code) REFERENCES ministries(code),
            FOREIGN KEY (state_code) REFERENCES states(code)
        )
    """)

    # --- 4. Questions Table (Lok Sabha, Rajya Sabha, State Assemblies)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_code TEXT UNIQUE NOT NULL,
            question_title TEXT NOT NULL,
            introduced_by TEXT,
            ministry_code TEXT,
            legislative_body TEXT NOT NULL, 
            state_code TEXT,
            q_type TEXT, -- 'Starred' or 'Unstarred'
            current_status TEXT NOT NULL, -- 'Answered', 'Not Answered'
            pdf_path TEXT,
            introduced_date DATE,
            FOREIGN KEY (ministry_code) REFERENCES ministries(code),
            FOREIGN KEY (state_code) REFERENCES states(code)
        )
    """)

    # --- 5. Current Affairs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS current_affairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            url TEXT,
            pdf_path TEXT,
            published_date DATE
        )
    """)

    conn.commit()
    conn.close()
    
    print(f"Database {DB_FILE} initialized successfully.")

# Execute initialization when this script is run directly
if __name__ == '__main__':
    initialize_database()