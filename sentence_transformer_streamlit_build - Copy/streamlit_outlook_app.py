# streamlit_app_01.py
import streamlit as st
import os
import pandas as pd
import pythoncom
from outlook_work.downloader import OutlookCVFetcher
from outlook_work.resume_Parse import ResumeParser
from outlook_work.config import get_save_directory


# -------------------------------
# Helper: Read saved path
# -------------------------------
def get_save_path():
    try:
        with open("cv_save_path.txt", "r", encoding="utf-8") as f:
            path = f.read().strip()
        return os.path.abspath(path) if path and os.path.exists(path) else None
    except Exception:
        return None

# -------------------------------
# Helper: Save selected path
# -------------------------------
def save_path_to_config(path):
    try:
        with open("cv_save_path.txt", "w", encoding="utf-8") as f:
            f.write(path)
        return True
    except Exception as e:
        st.error(f"❌ Failed to save path: {e}")
        return False

# -------------------------------
# Set page config
# -------------------------------
st.set_page_config(page_title="📬 CV Scanner", layout="wide")
st.title("📬 Job Applicant Manager")

# -------------------------------
# Folder Selection Section
# -------------------------------
st.header("📁 Select CV Save Location")

current_path = get_save_path()

if current_path:
    st.success(f"✅ Current Save Folder:\n\n`{current_path}`")
else:
    st.info("No folder selected yet. Please set one below.")

st.markdown("### 📂 Enter or Paste Folder Path")
folder_input = st.text_input(
    "Paste the path where you want to save CVs:",
    value=current_path or "",
    placeholder="e.g., C:\\Users\\YourName\\Documents\\Resumes"
)

if st.button("✅ Use This Folder"):
    if folder_input:
        folder_input = folder_input.strip()
        folder_input = os.path.abspath(folder_input)
        try:
            os.makedirs(folder_input, exist_ok=True)
            if save_path_to_config(folder_input):
                st.success(f"📁 Save path updated to:\n\n`{folder_input}`")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Cannot use this path: {e}")
    else:
        st.warning("Please enter a valid path.")

# -------------------------------
# Define SAVE_DIR and OUTPUT_CSV
# -------------------------------
SAVE_DIR = get_save_path() or r"C:\Users\BijayaThebe\Downloads\Resume_folder"
OUTPUT_CSV = os.path.join(SAVE_DIR, "candidates.csv")
os.makedirs(SAVE_DIR, exist_ok=True)

# -------------------------------
# Main: Outlook & Parsing Buttons
# -------------------------------
st.header("📧 Outlook & Parsing")

email_account = st.text_input(
    "Enter Your Outlook Email",
    value="name@bitskraft.com"
)

# Fetch from Outlook
if st.checkbox("✅ Enable Outlook Integration", key="enable_outlook"):
    if st.button("📥 Fetch CVs from Outlook", key="fetch"):
        with st.spinner("🔗 Connecting to Outlook..."):
            try:
                pythoncom.CoInitialize()
                fetcher = OutlookCVFetcher(email_account=email_account, save_dir=SAVE_DIR)
                fetcher.process_jobbox()
                st.success("✅ CVs downloaded!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Outlook error: {e}")
            finally:
                pythoncom.CoUninitialize()

# Parse Resumes
if st.button("🔄 Parse All Resumes", key="parse"):
    with st.spinner("🔍 Parsing PDFs..."):
        try:
            parser = ResumeParser(save_dir=SAVE_DIR, output_file="candidates.csv")
            parser.parse_pdfs()
            parser.save_to_excel()
            st.success("✅ Parsing complete!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Parsing failed: {e}")

# -------------------------------
# 🔍 View Details Button (At the End)
# -------------------------------
st.markdown("---")
if st.button("🔍 View Parsed Candidate Details"):
    if os.path.exists(OUTPUT_CSV):
        try:
            df = pd.read_csv(OUTPUT_CSV)
            if not df.empty:
                st.subheader("📋 Parsed Candidate Data")
                st.dataframe(df, use_container_width=True)
                st.success(f"✅ Found {len(df)} candidate(s)")
            else:
                st.info("📭 No data in `candidates.csv`.")
        except Exception as e:
            st.error(f"❌ Could not read CSV: {e}")
    else:
        st.warning("⚠️ `candidates.csv` not found. Run the parser first.")