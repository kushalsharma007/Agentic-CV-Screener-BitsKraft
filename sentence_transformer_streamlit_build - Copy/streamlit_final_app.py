# streamlit_final_app.py
import streamlit as st
from pathlib import Path
import pandas as pd
from outlook_work.resume_Parse import ResumeParser  # ✅ Corrected import
from outlook_work.ai_resume_evaluator import AIResumeEvaluator

# -----------------------------
# Step 0: Setup directories
# -----------------------------
SAVE_DIR = Path("uploads/resumes")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Step 1: Upload Resumes
# -----------------------------
st.set_page_config(page_title="AI Resume Screening", layout="wide")
st.title("📝 AI Resume Screening Dashboard")
st.markdown(
    """
    Upload your candidates' resumes (PDF) and get AI-based evaluation and ranking.
    """
)

uploaded_files = st.file_uploader(
    "Upload Resumes (PDF)", type=["pdf"], accept_multiple_files=True
)

for file in uploaded_files:
    save_path = SAVE_DIR / file.name
    with open(save_path, "wb") as f:
        f.write(file.getbuffer())

st.success(f"✅ Uploaded {len(uploaded_files)} resumes." if uploaded_files else "")

# -----------------------------
# Step 2: Job Description
# -----------------------------
st.sidebar.header("Job Description")
job_description = st.sidebar.text_area(
    "Paste Job Description here", height=200
)

# -----------------------------
# Step 3: Parse Resumes
# -----------------------------
st.sidebar.header("Step 3: Parse & Evaluate")
parser = ResumeParser(save_dir=SAVE_DIR)

if st.sidebar.button("Parse & Evaluate Resumes"):
    with st.spinner("⏳ Parsing resumes..."):
        parser.parse_pdfs()  # Make sure your ResumeParser has this method
        parsed_data = parser.df

        if parsed_data.empty:
            st.warning("⚠️ No resumes parsed.")
        else:
            st.success(f"✅ Parsed {len(parsed_data)} resumes.")
            st.subheader("📄 Parsed Resume Details")
            st.dataframe(parsed_data)

            # -----------------------------
            # Step 4: AI Evaluation
            # -----------------------------
            evaluator = AIResumeEvaluator()
            with st.spinner("🤖 Evaluating resumes with AI..."):
                resume_files = list(SAVE_DIR.glob("*.pdf"))
                df_results = evaluator.evaluate_resumes(resume_files, job_description)

                st.subheader("🤖 AI Evaluation Results")
                st.dataframe(df_results)

                # -----------------------------
                # Step 5: AI Ranking (Key Details)
                # -----------------------------
                st.subheader("🔝 AI Ranking - Key Candidate Info")
                ranking_cols = ["Rank", "Name", "FileName", "Phone", "Email", "LinkedIn", "GitHub"]

                # Merge rank with parsed data
                if "Rank" not in parsed_data.columns:
                    parsed_data["Rank"] = df_results["Rank"]  # Add rank from AI evaluation

                ranked_df = parsed_data.merge(
                    df_results[["Resume Name", "Overall Match Score", "Rank"]],
                    left_on="FileName",
                    right_on="Resume Name",
                    how="left"
                )

                st.dataframe(ranked_df[ranking_cols].sort_values("Rank"))

st.sidebar.markdown(
    """
    ---
    Made with ❤️ by AI Resume Screening
    """
)
