import streamlit as st
import os
from pypdf import PdfReader
from google import genai
from google.genai import types 
from google.genai.errors import APIError 

# NOTE: REPLACE THIS placeholder with your actual key for summarization to work!
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE" 

# --- CRITICAL FIX: Load key from environment variable ---
# This ensures the app uses the key stored securely in Streamlit Cloud Secrets.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") 
# If the key is not found in the environment, use a fallback (the placeholder string)
if not GEMINI_API_KEY:
    GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
# --- END FIX ---

def extract_text_from_pdf(pdf_path):
    """Extracts text content from a local PDF file."""
    text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

def get_ai_summary(pdf_path):
    """Connects to the Gemini API to summarize the text extracted from the PDF."""
    if not pdf_path or not os.path.exists(pdf_path):
        st.warning("No PDF document available for summarization.")
        return

    bill_text = extract_text_from_pdf(pdf_path)
    if not bill_text or len(bill_text) < 100:
        st.warning("The PDF text extracted is too short to generate a meaningful summary.")
        return

    with st.spinner('🧠 Contacting Gemini AI to summarize the document...'):
        try:
            if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE" or not GEMINI_API_KEY:
                 st.error("🚨 API Key Error: Please replace 'YOUR_GEMINI_API_KEY_HERE' with your actual key.")
                 return
            
            client = genai.Client(api_key=GEMINI_API_KEY)
            
            system_prompt = (
                "You are a legislative analyst. Summarize the provided text of an Indian Bill or Question. "
                "Provide a concise summary (max 100 words) covering the document's key objectives, "
                "main provisions, and intended impact. Use clear, formal language."
            )
            
            user_prompt = f"Please summarize the following text:\n\n---\n\n{bill_text}"
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[user_prompt],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt
                )
            )

            st.markdown("### 🌟 AI Summary")
            st.info(response.text)
            st.success("Analysis Complete.")

        except APIError as e:
            st.error(f"Gemini API Error: Failed to generate summary. Details: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred during summarization: {e}")