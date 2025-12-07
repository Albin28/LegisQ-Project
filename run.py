import streamlit as st
from admin_forms import render_manage_metadata, render_manage_data, render_manage_ca
from viewers_modules import render_bills_viewer, render_questions_viewer, render_ca_viewer
import sqlite3 # Import for database initialization check
from database_ops import get_db_connection

# --- Configuration & Setup ---
st.set_page_config(layout="wide", page_title="LegisQ - Legislative Information System")
ADMIN_PASSWORD = "admin" # Change this for production!

# ==============================================================================
# 1. INITIALIZATION CHECK (CRUCIAL!)
# ==============================================================================

# This helper function is usually run once externally (python database.py),
# but this check ensures the DB file exists before running queries.
def check_database_exists():
    try:
        conn = get_db_connection()
        # Try to read a table to check if the database structure is initialized
        conn.execute("SELECT 1 FROM bills LIMIT 1") 
        conn.close()
        return True
    except sqlite3.OperationalError:
        # If the table doesn't exist, prompt the user to run setup script
        return False
    except Exception:
        return False


# --- Admin Login/Logout Logic ---
st.sidebar.title("👤 Admin Panel")

if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if password == ADMIN_PASSWORD:
            st.session_state['authenticated'] = True
            st.success("Logged in successfully!")
            st.rerun() 
        else:
            st.sidebar.error("Incorrect password")
else:
    st.sidebar.success("Welcome, Admin!")
    if st.sidebar.button("Logout"):
        st.session_state['authenticated'] = False
        st.rerun()

# --- Admin Menu (If Authenticated) ---
if st.session_state['authenticated']:
    st.sidebar.subheader("Data Management")
    if st.sidebar.button("Manage Metadata"):
        st.session_state['page'] = 'manage_metadata'
    if st.sidebar.button("Manage Bills/Questions"):
        st.session_state['page'] = 'manage_data'
    if st.sidebar.button("Manage Current Affairs"):
        st.session_state['page'] = 'manage_ca'
    st.sidebar.markdown("---")

# --- Page Selection Logic (Initialize default page) ---
if 'page' not in st.session_state:
    st.session_state['page'] = 'home'

# ==============================================================================
# 2. HOMEPAGE NAVIGATION (Always Visible)
# ==============================================================================

st.title("🇮🇳 LegisQ: Legislative Information System")
st.markdown("### Browse Legislative Data")
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

def navigate(target_page):
    st.session_state['page'] = target_page

with col1:
    st.header("🏛️ Lok Sabha Bills")
    st.info("View Bills and search by code, name, or ministry.")
    if st.button("Explore Lok Sabha", key='nav_ls', use_container_width=True):
        navigate('lok_sabha')

with col2:
    st.header("❓ Legislative Questions")
    st.info("Search and filter questions from all assemblies.")
    if st.button("Explore Questions", key='nav_qn', use_container_width=True):
        navigate('questions')

with col3:
    st.header("🗺️ State Assembly Bills")
    st.info("View Bills specific to state assemblies.")
    if st.button("Explore State Assemblies", key='nav_sa', use_container_width=True):
        navigate('state_assemblies')

with col4:
    st.header("📰 Current Affairs")
    st.info("Latest legislative news and updates.")
    if st.button("Explore Current Affairs", key='nav_ca', use_container_width=True):
        navigate('current_affairs')

st.markdown("---")

# ==============================================================================
# 3. MAIN PAGE ROUTER
# ==============================================================================

# Check for database initialization state
# if not check_database_exists():
#     st.error("🚨 Database Error: The 'legisq.db' file or tables were not found.")
#     st.info("Please ensure you run the setup script before starting the app.")
#     st.stop() # Stops execution until database is fixed

# --- Admin Pages ---
if st.session_state['authenticated']:
    if st.session_state['page'] == 'manage_metadata':
        render_manage_metadata()
    elif st.session_state['page'] == 'manage_data':
        render_manage_data()
    elif st.session_state['page'] == 'manage_ca':
        render_manage_ca() 
    else:
        # Default view for authenticated user
        st.markdown("### Welcome to the Admin Dashboard.")


# --- Viewer Pages ---
else:
    if st.session_state['page'] == 'lok_sabha':
        render_bills_viewer('Lok Sabha')
    elif st.session_state['page'] == 'rajya_sabha':
        # Rajya Sabha Bills are now accessed here
        render_bills_viewer('Rajya Sabha')
    elif st.session_state['page'] == 'state_assemblies':
        render_bills_viewer('State Assembly')
    elif st.session_state['page'] == 'questions':
        # Dedicated Questions Viewer
        render_questions_viewer()
    elif st.session_state['page'] == 'current_affairs':
        render_ca_viewer()
    elif st.session_state['page'] == 'home':
        pass