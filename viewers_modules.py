import streamlit as st
import pandas as pd
import os
from database_ops import fetch_bills, fetch_search_suggestions, fetch_current_affairs, fetch_questions
from ai_services import get_ai_summary

# ==============================================================================
# 1. BILLS VIEWER (R)
# ==============================================================================

def render_bills_viewer(legislative_body):
    """Generic viewer renderer for all Bill types (Lok Sabha, Rajya Sabha, State Assembly)."""
    
    st.header(f"🏛️ {legislative_body} Bills")
    st.markdown("Filter, sort, and analyze legislation.")

    is_state_assembly = legislative_body == 'State Assembly'
    
    # --- Search, Filter, and Sorting Controls ---
    col_filter, col_search, col_sort = st.columns([1, 2, 1] if is_state_assembly else [0.1, 3, 1])
    
    selected_state_name = "-- All States --"
    if is_state_assembly:
        # Assuming fetch_metadata is imported/available if needed, but fetch_bills provides state_name
        states_data = {'-- All States --': None} # Mock for selection check
        with col_filter:
            # Note: For simplicity and to avoid a complex import dependency, 
            # we rely on the data already fetched by fetch_bills to show state names.
            st.markdown("**(Filter is based on search/sort)**") 
        
    with col_search:
        raw_search_query = st.text_input("Search Bills by Code, Name, or Ministry", 
                                        key=f"{legislative_body}_search_input", 
                                        placeholder="Start typing to see suggestions...")

        suggestions = fetch_search_suggestions(legislative_body, raw_search_query)

        if suggestions:
            selected_suggestion = st.selectbox("Did you mean?", options=[''] + suggestions, index=0, key=f"{legislative_body}_suggestion")
            final_search_query = selected_suggestion if selected_suggestion else raw_search_query
        else:
            final_search_query = raw_search_query
            st.info("No suggestions found or start typing (min 2 characters).")


    with col_sort:
        sort_by = st.selectbox("Sort By", ["Introduced Date (Newest)", "Status", "Alphabetical (Bill Name)"], key=f"{legislative_body}_sort")
    
    # --- Fetch and Filter Data ---
    df_bills = fetch_bills(legislative_body, final_search_query) 

    # Note: State filtering is handled effectively by the search/query in fetch_bills
    
    if df_bills.empty:
        st.warning("No Bills found matching your criteria.")
        return

    # --- Apply Client-Side Sorting ---
    if sort_by == "Status":
        status_order = ['Passed', 'Pending', 'Not Passed']
        df_bills['status_sort'] = pd.Categorical(df_bills['current_status'], categories=status_order, ordered=True)
        df_bills = df_bills.sort_values('status_sort')
    elif sort_by == "Alphabetical (Bill Name)":
        df_bills = df_bills.sort_values('bill_name')

    st.markdown(f"**Showing {len(df_bills)} Bills**")
    st.markdown("---")


    # --- Display Results ---
    for index, row in df_bills.iterrows():
        
        display_name = f" - State: {row['state_name']}" if is_state_assembly else ""
        
        with st.expander(f"**{row['bill_code']}** - {row['bill_name']} {display_name}"):
            
            if row['current_status'] == 'Passed': status_icon = "🟢 Passed"
            elif row['current_status'] == 'Not Passed': status_icon = "🔴 Not Passed"
            else: status_icon = "🟡 Pending"
            
            st.markdown(f"### {row['bill_name']} {display_name}")
            st.markdown(f"**Introduced By:** {row['introduced_by']}")
            st.markdown(f"**Ministry:** {row['ministry_name']}")
            st.markdown(f"**Date Introduced:** {row['introduced_date']}")
            st.markdown(f"**Current Status:** {status_icon}")

            st.markdown("---")
            
            col_detail_1, col_detail_2, col_detail_3 = st.columns(3)
            
            with col_detail_1:
                st.metric("Votes in Favour", row['votes_favour'])
            with col_detail_2:
                st.metric("Votes Against", row['votes_against'])
            with col_detail_3:
                approval_icon = "✅" if row['approval_result'] == 'Yes' else ("❌" if row['approval_result'] == 'No' else "❓")
                st.metric(row['approval_status'], f"{approval_icon} {row['approval_result']}")
            
            st.markdown("---")

            pdf_path = row['pdf_path']
            col_pdf_dl, col_ai = st.columns(2)

            with col_pdf_dl:
                if pdf_path and os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as file:
                        st.download_button(
                            label="⬇️ Download Bill PDF",
                            data=file,
                            file_name=os.path.basename(pdf_path),
                            mime="application/pdf",
                            key=f"dl_bill_{row['bill_code']}" 
                        )
                else:
                    st.warning("No downloadable PDF available.")

            with col_ai:
                if st.button("🧠 Get AI Summary", key=f"ai_summary_bill_{row['bill_code']}", disabled=(not pdf_path or not os.path.exists(pdf_path))):
                    get_ai_summary(pdf_path) 


# ==============================================================================
# 2. QUESTIONS VIEWER (R)
# ==============================================================================

def render_questions_viewer():
    """Renders the viewer module for all Questions, allowing filtering by body."""
    st.header("❓ Legislative Questions & Answers")
    
    col_body, col_search, col_sort = st.columns([1, 2, 1])
    
    with col_body:
        body_type = st.selectbox("Filter by Legislative Body", ['Lok Sabha', 'Rajya Sabha', 'State Assembly'], key='qn_viewer_body')
    
    with col_search:
        raw_search_query = st.text_input("Search Questions by Code, Title, or Ministry", key='qn_search_input', placeholder="Start typing...")
        
        # NOTE: Search suggestions for questions is simplified here
        suggestions = fetch_search_suggestions(body_type, raw_search_query) 

        if suggestions:
            selected_suggestion = st.selectbox("Did you mean?", options=[''] + suggestions, index=0, key='qn_suggestion')
            final_search_query = selected_suggestion if selected_suggestion else raw_search_query
        else:
            final_search_query = raw_search_query
            st.info("No suggestions found.")

    with col_sort:
        sort_by = st.selectbox("Sort By", ["Date (Newest)", "Status", "Type"], key='qn_sort')
    
    df_qns = fetch_questions(body_type, final_search_query)
    
    if df_qns.empty:
        st.warning(f"No {body_type} Questions found matching your criteria.")
        return

    # --- Apply Client-Side Sorting ---
    if sort_by == "Status":
        status_order = ['Answered', 'Not Answered']
        df_qns['status_sort'] = pd.Categorical(df_qns['current_status'], categories=status_order, ordered=True)
        df_qns = df_qns.sort_values('status_sort', ascending=False)
    elif sort_by == "Type":
        df_qns = df_qns.sort_values('q_type')

    st.markdown(f"**Showing {len(df_qns)} Questions**")
    st.markdown("---")

    for index, row in df_qns.iterrows():
        display_state = f" - State: {row['state_name']}" if row['state_name'] else ""
        
        with st.expander(f"**{row['question_code']}** - {row['question_title']} {display_state}"):
            
            status_icon = "✅" if row['current_status'] == 'Answered' else "❌"
            
            st.markdown(f"### {row['question_title']}")
            st.markdown(f"**Body:** {body_type}{display_state}")
            st.markdown(f"**Type:** {row['q_type']} ({status_icon})")
            st.markdown(f"**Asked By:** {row['introduced_by']}")
            st.markdown(f"**Ministry:** {row['ministry_name']}")
            st.markdown(f"**Date Introduced:** {row['introduced_date']}")

            st.markdown("---")
            
            pdf_path = row['pdf_path']
            col_pdf_dl, col_ai = st.columns(2)

            with col_pdf_dl:
                if pdf_path and os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as file:
                        st.download_button(
                            label="⬇️ Download Answer/Text PDF",
                            data=file,
                            file_name=os.path.basename(pdf_path),
                            mime="application/pdf",
                            key=f"dl_qn_{row['question_code']}" 
                        )
                else:
                    st.warning("No downloadable PDF available.")

            with col_ai:
                if st.button("🧠 Get AI Summary", key=f"ai_summary_qn_{row['question_code']}", disabled=(not pdf_path or not os.path.exists(pdf_path))):
                    get_ai_summary(pdf_path) 


# ==============================================================================
# 3. CURRENT AFFAIRS VIEWER (R)
# ==============================================================================
def render_ca_viewer():
    """Renders the public viewer for Current Affairs."""
    st.header("📰 Current Affairs & Updates")
    st.markdown("External links and summaries of current legislative affairs.")
    st.markdown("---")
    
    df_ca = fetch_current_affairs()
    
    if df_ca.empty:
        st.info("No current affairs records available.")
        return

    for index, row in df_ca.iterrows():
        with st.container(border=True):
            st.markdown(f"**{row['published_date']}** | ## {row['title']}")
            st.write(row['description'])
            
            col_link, col_pdf = st.columns(2)
            
            if row['url']:
                with col_link:
                    st.link_button("🌐 Read Full Article", row['url'], use_container_width=True)
            
            pdf_path = row['pdf_path']
            if pdf_path and os.path.exists(pdf_path):
                 with col_pdf:
                    with open(pdf_path, "rb") as file:
                        st.download_button(
                            label="⬇️ Download Summary PDF",
                            data=file,
                            file_name=os.path.basename(pdf_path),
                            mime="application/pdf",
                            key=f"dl_ca_{row['id']}" 
                        )