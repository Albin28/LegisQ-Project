import streamlit as st
import sqlite3
import random
import os
import pandas as pd
from database_ops import get_db_connection, fetch_metadata, save_bill_record, fetch_bills, fetch_questions, fetch_current_affairs, delete_record

# ==============================================================================
# 1. METADATA MANAGEMENT (C & R)
# ==============================================================================

def render_manage_metadata():
    """Renders the UI for managing Ministries and States (Metadata)."""
    st.header("⚙️ Manage Metadata")
    st.subheader("Manage data required for Bill/Question coding and filtering.")

    tab_ministry, tab_state = st.tabs(["🏛️ Ministries", "🗺️ States"])

    # --- Ministry Management Tab
    with tab_ministry:
        st.subheader("Add New Ministry")
        with st.form("add_ministry_form", clear_on_submit=True):
            m_code = st.text_input("Ministry Code (e.g., MN)", max_chars=2, help="Two-letter code for the ministry.")
            m_name = st.text_input("Ministry Name (e.g., Ministry of Finance)")
            
            submitted = st.form_submit_button("Add Ministry")
            if submitted:
                if m_code and m_name:
                    try:
                        conn = get_db_connection()
                        conn.execute("INSERT INTO ministries (code, name) VALUES (?, ?)", (m_code.upper(), m_name))
                        conn.commit()
                        st.success(f"Ministry '{m_name}' ({m_code.upper()}) added successfully!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Error: Ministry Code or Name already exists.")
                    finally:
                        conn.close()
                else:
                    st.error("Please enter both Code and Name.")
        
        st.markdown("---")
        st.subheader("Existing Ministries")
        conn = get_db_connection()
        df_ministries = pd.read_sql_query("SELECT code, name FROM ministries ORDER BY code", conn)
        conn.close()
        st.dataframe(df_ministries, use_container_width=True)

    # --- State Management Tab
    with tab_state:
        st.subheader("Add New State")
        with st.form("add_state_form", clear_on_submit=True):
            s_code = st.text_input("State Code (e.g., MH, KA)", max_chars=2, help="Two-letter code for the state.")
            s_name = st.text_input("State Name (e.g., Maharashtra)")
            
            submitted = st.form_submit_button("Add State")
            if submitted:
                if s_code and s_name:
                    try:
                        conn = get_db_connection()
                        conn.execute("INSERT INTO states (code, name) VALUES (?, ?)", (s_code.upper(), s_name))
                        conn.commit()
                        st.success(f"State '{s_name}' ({s_code.upper()}) added successfully!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Error: State Code or Name already exists.")
                    finally:
                        conn.close()
                else:
                    st.error("Please enter both Code and Name.")

        st.markdown("---")
        st.subheader("Existing States")
        conn = get_db_connection()
        df_states = pd.read_sql_query("SELECT code, name FROM states ORDER BY code", conn)
        conn.close()
        st.dataframe(df_states, use_container_width=True)


# ==============================================================================
# 2. BILLS & QUESTIONS CREATION FORMS (CREATE)
# ==============================================================================

def render_bill_form(legislative_body):
    """Renders a generic bill creation form with body-specific constraints."""
    
    is_lok_sabha = legislative_body == 'Lok Sabha'
    is_rajya_sabha = legislative_body == 'Rajya Sabha'
    is_state_assembly = legislative_body == 'State Assembly'
    
    ministries_data = fetch_metadata('ministries')
    ministry_names = list(ministries_data.keys())
    states_data = fetch_metadata('states')
    state_names = list(states_data.keys())
    
    if not ministry_names or (is_state_assembly and not state_names):
        st.error("🚨 Prerequisite: You must add Ministries and States (for State Assembly) first (Manage Metadata).")
        return

    with st.form(f"{legislative_body}_bill_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        
        with col_a:
            bill_name = st.text_input("Bill Name", key=f"{legislative_body}_name")
            introduced_by = st.text_input("Introduced By", key=f"{legislative_body}_intro")
            introduced_date = st.date_input("Date Introduced", value="today", key=f"{legislative_body}_date")
            
            st.markdown("---")
            
            if is_state_assembly:
                selected_state_name = st.selectbox("State Name (ZZ Code)", ["-- Select State --"] + state_names, key=f"{legislative_body}_state")
            else:
                selected_state_name = None
            
            selected_ministry_name = st.selectbox("Ministry/Department (XX Code)", ["-- Select Ministry --"] + ministry_names, key=f"{legislative_body}_min")
            
            st.info("💡 AI helper will suggest ministry based on Bill Name here.")

        with col_b:
            current_status = st.selectbox("Current Status", ['Pending', 'Passed', 'Not Passed'], key=f"{legislative_body}_status")
            
            approval_label = "Governor Approval" if is_state_assembly else "President Approval"
            approval_status = approval_label
            approval_result = st.selectbox(approval_label, ['Pending', 'Yes', 'No'], key=f"{legislative_body}_approval_res")
            
            if is_rajya_sabha:
                is_money_bill = False
                st.warning("Cannot be a Money Bill (Constraint enforced).")
            else:
                is_money_bill = st.checkbox("Is this a Money Bill?", value=False, key=f"{legislative_body}_money")
            
            st.markdown("---")
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                votes_favour = st.number_input("Votes in Favour", min_value=0, step=1, key=f"{legislative_body}_favour")
            with col_v2:
                votes_against = st.number_input("Votes Against", min_value=0, step=1, key=f"{legislative_body}_against")

            st.markdown("---")
            bill_pdf = st.file_uploader("Upload Bill PDF Document", type=['pdf'], key=f"{legislative_body}_pdf")
        
        submitted = st.form_submit_button(f"Create New {legislative_body} Bill")

        if submitted:
            if selected_ministry_name == "-- Select Ministry --" or (is_state_assembly and selected_state_name == "-- Select State --"):
                st.error("Please fill in all required fields.")
                return

            state_code = states_data.get(selected_state_name) if is_state_assembly else None
            ministry_code = ministries_data.get(selected_ministry_name)
            
            random_num = random.randint(1000, 9999)
            if is_state_assembly:
                bill_code = f"{state_code}-{ministry_code}-{random_num}"
            else:
                bill_code = f"BL-{ministry_code}-{random_num}"
            
            pdf_path = None
            if bill_pdf is not None:
                os.makedirs('pdfs', exist_ok=True) 
                pdf_filename = f"{bill_code}_bill.pdf"
                pdf_path = os.path.join('pdfs', pdf_filename)
                try:
                    with open(pdf_path, "wb") as f:
                        f.write(bill_pdf.getbuffer())
                except Exception as e:
                    st.error(f"Error saving PDF file: {e}")
                    return

            bill_data = (
                bill_code, bill_name, introduced_by, ministry_code, legislative_body, 
                state_code, votes_favour, votes_against, current_status, approval_status, 
                approval_result, is_money_bill, pdf_path, introduced_date.strftime('%Y-%m-%d')
            )
            save_bill_record(bill_data)


def render_question_form(legislative_body):
    """Renders the form for creating a new Question (Reusable for all bodies)."""
    
    ministries_data = fetch_metadata('ministries')
    ministry_names = list(ministries_data.keys())
    states_data = fetch_metadata('states')
    state_names = list(states_data.keys())

    is_state_assembly = legislative_body == 'State Assembly'
    
    if not ministry_names or (is_state_assembly and not state_names):
        st.error("🚨 Prerequisite: You must add Ministries and States (for State Assembly) first (Manage Metadata).")
        return

    with st.form(f"{legislative_body}_question_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        
        with col_a:
            question_title = st.text_input("Question Title", key=f"qn_{legislative_body}_title")
            introduced_by = st.text_input("Asked By", key=f"qn_{legislative_body}_by")
            introduced_date = st.date_input("Date Introduced", value="today", key=f"qn_{legislative_body}_date")
            
            st.markdown("---")
            if is_state_assembly:
                selected_state_name = st.selectbox("State Name (ZZ Code)", ["-- Select State --"] + state_names, key=f"qn_{legislative_body}_state")
            else:
                selected_state_name = None

            selected_ministry_name = st.selectbox("Ministry/Department (XX Code)", ["-- Select Ministry --"] + ministry_names, key=f"qn_{legislative_body}_min")

        with col_b:
            q_type = st.selectbox("Question Type", ['Starred', 'Unstarred'], key=f"qn_{legislative_body}_type")
            current_status = st.selectbox("Current Status", ['Answered', 'Not Answered'], key=f"qn_{legislative_body}_status")
            
            st.markdown("---")
            question_pdf = st.file_uploader("Upload Question PDF Document (Answer/Text)", type=['pdf'], key=f"qn_{legislative_body}_pdf")
        
        submitted = st.form_submit_button(f"Create New {legislative_body} Question")

        if submitted:
            if selected_ministry_name == "-- Select Ministry --" or (is_state_assembly and selected_state_name == "-- Select State --"):
                st.error("Please fill in all required fields.")
                return

            state_code = states_data.get(selected_state_name) if is_state_assembly else None
            ministry_code = ministries_data.get(selected_ministry_name)
            
            random_num = random.randint(1000, 9999)
            if is_state_assembly:
                question_code = f"{state_code}-{ministry_code}-{random_num}"
            else:
                question_code = f"QN-{ministry_code}-{random_num}"
            
            pdf_path = None
            if question_pdf is not None:
                os.makedirs('pdfs', exist_ok=True) 
                pdf_filename = f"{question_code}_qn.pdf"
                pdf_path = os.path.join('pdfs', pdf_filename)
                try:
                    with open(pdf_path, "wb") as f:
                        f.write(question_pdf.getbuffer())
                except Exception as e:
                    st.error(f"Error saving PDF file: {e}")
                    return

            try:
                conn = get_db_connection()
                conn.execute("""
                    INSERT INTO questions (
                        question_code, question_title, introduced_by, ministry_code, legislative_body, 
                        state_code, q_type, current_status, pdf_path, introduced_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    question_code, question_title, introduced_by, ministry_code, legislative_body, 
                    state_code, q_type, current_status, pdf_path, introduced_date.strftime('%Y-%m-%d')
                ))
                conn.commit()
                st.success(f"{legislative_body} Question '{question_title}' created successfully! Code: **{question_code}**")
                st.rerun() # Force a rerun to clear form fields better
            except sqlite3.Error as e:
                st.error(f"Database Error: Could not save question. Details: {e}") 
            finally:
                conn.close()


# ==============================================================================
# 3. BILLS & QUESTIONS UPDATE/DELETE UI (U & D)
# ==============================================================================

def render_update_delete_ui(df, body_type, is_bill):
    """
    Renders the Read/Update/Delete table and forms for a given DataFrame (Bills or Questions).
    CRITICAL: Includes debug checks to verify the ID being used.
    """
    
    st.markdown("### Existing Records (Update/Delete)")
    
    table_name = 'bills' if is_bill else 'questions'
    code_col = 'bill_code' if is_bill else 'question_code'
    
    df_display = df.copy()
    
    # ... (code for displaying the table remains the same) ...
    
    if 'state_name' in df_display.columns:
        df_display['Legislature'] = df_display['state_name'].fillna(body_type)
        cols_to_show = [code_col, 'bill_name' if is_bill else 'question_title', 'ministry_name', 'Legislature', 'current_status', 'introduced_date']
    else:
        cols_to_show = [code_col, 'bill_name' if is_bill else 'question_title', 'ministry_name', 'current_status', 'introduced_date']
        
    st.dataframe(df_display[cols_to_show], use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    record_codes = df_display[code_col].tolist()
    
    selected_code = st.selectbox(f"Select {body_type.split()[0]} Code to Edit/Delete:", ['-- Select Code --'] + record_codes, key=f"select_{body_type}_{table_name}_ud")
    
    if selected_code != '-- Select Code --':
        record = df[df[code_col] == selected_code].iloc[0]
        
        # --- CRITICAL DEBUG CHECK ---
        record_id = int(record['id']) if record['id'] is not None else None 
        st.warning(f"DEBUG: Selected Record ID (must be integer > 0): {record_id}")
        
        if record_id is None:
            st.error("Cannot proceed: Record ID is missing or invalid.")
            return
        # --- END DEBUG CHECK ---

        st.subheader(f"Actions for: {selected_code}")
        col_u, col_d = st.columns(2)
        
        # --- DELETE BUTTON ---
        with col_d:
            if st.button(f"🔴 Permanently Delete {selected_code}", use_container_width=True, key=f"delete_{selected_code}"):
                
                # We are moving the delete logic inside the try/except for better isolation
                conn = get_db_connection()
                try:
                    conn.execute(f"DELETE FROM {table_name} WHERE id = ?", (record_id,))
                    conn.commit()
                    st.success(f"Record {selected_code} deleted successfully from {table_name}! Refreshing...")
                    st.rerun() 
                except sqlite3.Error as e:
                    st.error(f"Error executing DELETE SQL: {e}")
                finally:
                    conn.close()
        
        # --- UPDATE FORM ---
        with col_u:
            with st.form(f"update_form_{selected_code}", clear_on_submit=True):
                st.markdown("#### Update Status")
                
                # ... (update options selection remains the same) ...
                
                if is_bill:
                    status_options = ['Pending', 'Passed', 'Not Passed']
                    approval_options = ['Pending', 'Yes', 'No']
                    
                    new_status = st.selectbox("New Current Status", status_options, 
                                            index=status_options.index(record['current_status']), key=f"status_{selected_code}")
                    
                    if record['approval_status']:
                         new_approval = st.selectbox(f"New {record['approval_status']} Result", approval_options, 
                                                     index=approval_options.index(record['approval_result']), key=f"approval_{selected_code}")
                    else:
                         new_approval = record.get('approval_result') # Use .get for safety

                else: 
                    status_options = ['Answered', 'Not Answered']
                    new_status = st.selectbox("New Current Status", status_options, 
                                            index=status_options.index(record['current_status']), key=f"status_{selected_code}")
                    new_approval = None 
                
                update_submitted = st.form_submit_button("Update Record Status")
                
                if update_submitted:
                    conn = get_db_connection()
                    try:
                        if is_bill:
                            conn.execute("UPDATE bills SET current_status = ?, approval_result = ? WHERE id = ?", 
                                        (new_status, new_approval, record_id)) # Use validated record_id
                        else: 
                            conn.execute("UPDATE questions SET current_status = ? WHERE id = ?", 
                                        (new_status, record_id)) # Use validated record_id
                        
                        conn.commit()
                        st.success(f"Record {selected_code} updated successfully! Refreshing...")
                        st.rerun() 
                    except sqlite3.Error as e:
                        st.error(f"Error executing UPDATE SQL: {e}")
                    finally:
                        conn.close()

# ==============================================================================
# 4. CURRENT AFFAIRS MANAGEMENT (C & D)
# ==============================================================================

def render_current_affairs_form():
    """Renders the form for creating a new Current Affairs record."""
    
    st.subheader("Add New Current Affairs Record")
    
    with st.form("current_affairs_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        
        with col_a:
            title = st.text_input("Title of Article/Update")
            published_date = st.date_input("Date Published", value="today")
            url = st.text_input("External URL Link (Optional)")
        
        with col_b:
            description = st.text_area("Short Description/Summary")
            pdf = st.file_uploader("Upload Summary PDF (Optional)", type=['pdf'])
        
        submitted = st.form_submit_button("Publish Current Affair")

        if submitted:
            if not title or not description:
                st.error("Title and Description are required.")
                return

            pdf_path = None
            if pdf is not None:
                os.makedirs('pdfs', exist_ok=True) 
                pdf_filename = f"CA_{title.replace(' ', '_')}_{random.randint(100, 999)}.pdf"
                pdf_path = os.path.join('pdfs', pdf_filename)
                try:
                    with open(pdf_path, "wb") as f:
                        f.write(pdf.getbuffer())
                except Exception as e:
                    st.error(f"Error saving PDF file: {e}")
                    return
            
            try:
                conn = get_db_connection()
                conn.execute("""
                    INSERT INTO current_affairs (title, description, url, pdf_path, published_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (title, description, url, pdf_path, published_date.strftime('%Y-%m-%d')))
                conn.commit()
                st.success(f"Current Affair '{title}' published successfully.")
                st.rerun() # Rerun on success
            except sqlite3.Error as e:
                st.error(f"Database Error: Could not save Current Affair. Details: {e}") 
            finally:
                conn.close()

def render_manage_ca():
    """Renders the Admin UI for managing Current Affairs."""
    st.header("📰 Manage Current Affairs")
    
    render_current_affairs_form()
    st.markdown("---")
    
    st.subheader("Existing Current Affairs (Delete)")
    df_ca = fetch_current_affairs()
    if not df_ca.empty:
        st.dataframe(df_ca[['published_date', 'title', 'url', 'pdf_path']], use_container_width=True)
        
        ca_titles = df_ca['title'].tolist()
        selected_title = st.selectbox("Select CA to Delete", ['-- Select Title --'] + ca_titles)
        if selected_title != '-- Select Title --':
            record = df_ca[df_ca['title'] == selected_title].iloc[0]
            if st.button(f"🔴 Delete '{selected_title}'", key='delete_ca_btn'):
                delete_record('current_affairs', record['id'], selected_title) 
                st.rerun() # Rerun on delete
    else:
        st.info("No current affairs records found.")


# ==============================================================================
# 5. MASTER ADMIN NAVIGATION (The Hub)
# ==============================================================================

def render_manage_data():
    """Renders the Admin UI for managing Bills and Questions across all bodies (CRUD)."""
    st.header("🗃️ Manage Bills & Questions")
    
    tab_bill_c, tab_qn_c, tab_bill_ud, tab_qn_ud = st.tabs([
        "CREATE Bills", 
        "CREATE Questions", 
        "UPDATE/DELETE Bills", 
        "UPDATE/DELETE Questions"
    ])
    
    # --- CREATE BILLS ---
    with tab_bill_c:
        st.subheader("Select Legislative Body for New Bill")
        body = st.selectbox("Body Type", ['Lok Sabha', 'Rajya Sabha', 'State Assembly'], key='bill_create_body')
        render_bill_form(body) 

        
    # --- CREATE QUESTIONS ---
    with tab_qn_c:
        st.subheader("Select Legislative Body for New Question")
        body = st.selectbox("Body Type", ['Lok Sabha', 'Rajya Sabha', 'State Assembly'], key='qn_create_body')
        render_question_form(body) 
        
    # --- UPDATE / DELETE BILLS ---
    with tab_bill_ud:
        st.subheader("Update/Delete Bills")
        body_type = st.selectbox("Filter Bills by Legislative Body", ['Lok Sabha', 'Rajya Sabha', 'State Assembly'], key='ud_bill_body')
        df_bills = fetch_bills(body_type)
        if not df_bills.empty:
            render_update_delete_ui(df_bills, body_type, is_bill=True) 
        else:
            st.info(f"No {body_type} Bills found for management.")

    # --- UPDATE / DELETE QUESTIONS ---
    with tab_qn_ud:
        st.subheader("Update/Delete Questions")
        body_type = st.selectbox("Filter Questions by Legislative Body", ['Lok Sabha', 'Rajya Sabha', 'State Assembly'], key='ud_qn_body')
        df_questions = fetch_questions(body_type)
        if not df_questions.empty:
            render_update_delete_ui(df_questions, f"{body_type} Questions", is_bill=False) 
        else:
            st.info(f"No {body_type} Questions found for management.")