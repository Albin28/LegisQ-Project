import sqlite3
import pandas as pd
import streamlit as st # Used for error messages and success/fail banners

# --- Configuration ---
DB_FILE = 'legisq.db'

# --- Database Connection ---
def get_db_connection():
    """Returns a connection object to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row 
    return conn

# --- Metadata Fetchers ---
def fetch_metadata(table_name):
    """Fetches all records from a given metadata table (ministries/states)."""
    conn = get_db_connection()
    df = pd.read_sql_query(f"SELECT code, name FROM {table_name} ORDER BY name", conn)
    conn.close()
    return {row['name']: row['code'] for index, row in df.iterrows()}

# --- Fetch Bills ---
def fetch_bills(legislative_body, search_term=""):
    """
    Fetches bills for a specific legislative body, filtered by search_term.
    Uses b.* to ensure the 'id' column is included for CRUD operations.
    """
    conn = get_db_connection()
    
    query = """
        SELECT 
            b.*, 
            m.name AS ministry_name, 
            s.name AS state_name 
        FROM bills b
        JOIN ministries m ON b.ministry_code = m.code 
        LEFT JOIN states s ON b.state_code = s.code 
        WHERE b.legislative_body = ?
    """
    
    params = [legislative_body]
    
    if search_term:
        search_like = f"%{search_term.lower()}%"
        query += """
            AND (
                LOWER(b.bill_code) LIKE ? OR 
                LOWER(b.bill_name) LIKE ? OR 
                LOWER(m.name) LIKE ?
            )
        """
        params.extend([search_like, search_like, search_like])
        
    query += " ORDER BY b.introduced_date DESC"
    
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Database Query Failed in fetch_bills. Error: {e}")
        st.code(query)
        return pd.DataFrame()
    finally:
        conn.close()

# --- Fetch Questions ---
def fetch_questions(legislative_body, search_term=""):
    """Fetches questions for a specific legislative body, filtered by search_term."""
    conn = get_db_connection()
    
    query = """
        SELECT 
            q.*, 
            m.name AS ministry_name, 
            s.name AS state_name 
        FROM questions q
        JOIN ministries m ON q.ministry_code = m.code 
        LEFT JOIN states s ON q.state_code = s.code 
        WHERE q.legislative_body = ?
    """
    params = [legislative_body]
    
    if search_term:
        search_like = f"%{search_term.lower()}%"
        query += """
            AND (
                LOWER(q.question_code) LIKE ? OR 
                LOWER(q.question_title) LIKE ? OR 
                LOWER(m.name) LIKE ?
            )
        """
        params.extend([search_like, search_like, search_like])
        
    query += " ORDER BY q.introduced_date DESC"
    
    try:
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Database Query Failed in fetch_questions. Error: {e}")
        st.code(query)
        return pd.DataFrame()
    finally:
        conn.close()

# --- Fetch Current Affairs ---
def fetch_current_affairs():
    """Fetches all current affairs records."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM current_affairs ORDER BY published_date DESC", conn)
    conn.close()
    return df

# --- Fetch Search Suggestions ---
def fetch_search_suggestions(legislative_body, search_term):
    """Fetches suggestions for bill/question codes, names, and ministries."""
    if not search_term or len(search_term) < 2:
        return []
    
    conn = get_db_connection()
    search_like = f"%{search_term.lower()}%"
    
    if 'Bill' in legislative_body: 
        table = 'bills'
        code_col = 'bill_code'
        name_col = 'bill_name'
    else: 
        table = 'questions'
        code_col = 'question_code'
        name_col = 'question_title'

    query = f"""
        SELECT 
            b.{code_col}, 
            b.{name_col}, 
            m.name AS ministry_name 
        FROM {table} b
        JOIN ministries m ON b.ministry_code = m.code
        WHERE b.legislative_body = ?
        AND (
            LOWER(b.{code_col}) LIKE ? OR 
            LOWER(b.{name_col}) LIKE ? OR 
            LOWER(m.name) LIKE ?
        )
        LIMIT 10 
    """
    
    params = [legislative_body, search_like, search_like, search_like]
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    suggestions = set()
    for _, row in df.iterrows():
        suggestions.add(row[code_col])
        suggestions.add(row[name_col])
        suggestions.add(row['ministry_name'])
        
    return sorted(list(suggestions))

# --- CREATE/DELETE Helpers ---
def save_bill_record(bill_data):
    """Reusable function to save any bill type."""
    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO bills (
                bill_code, bill_name, introduced_by, ministry_code, legislative_body, 
                state_code, votes_favour, votes_against, current_status, approval_status, 
                approval_result, is_money_bill, pdf_path, introduced_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, bill_data)
        conn.commit()
        st.success(f"{bill_data[4]} Bill '{bill_data[1]}' created successfully! Code: **{bill_data[0]}**")
    except sqlite3.Error as e:
        st.error(f"Database Error: Could not save bill. Details: {e}") 
    finally:
        conn.close()

def delete_record(table, record_id, record_code):
    """Handles deletion of a record from tables."""
    conn = get_db_connection()
    try:
        if record_id is None:
            st.error(f"Error: Could not determine ID for record {record_code}.")
            return

        conn.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
        conn.commit()
        st.success(f"Record {record_code} deleted successfully from {table}. Refreshing...")
    except sqlite3.Error as e:
        st.error(f"Error deleting record: {e}")
    finally:
        conn.close()
        # st.rerun() -- Rerun handled by calling module (Admin Form)