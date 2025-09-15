# streamlit_app.py
import streamlit as st
import pandas as pd

# Import model
from model_handling import UniversalResumeAnalyzer

# -------------------------------
# App Config
# -------------------------------
st.set_page_config(page_title="🚀 Universal Resume Evaluator", layout="wide")
st.title("📄 BitsKraft AI Resume Filter")

# Cache model
@st.cache_resource
def get_analyzer():
    st.info("📥 Loading AI model... (first run may take ~30 sec)")
    return UniversalResumeAnalyzer()

analyzer = get_analyzer()

# -------------------------------
# Job Requirements Input
# -------------------------------
st.markdown("### 📝 Enter Job Requirements")
job_description = st.text_area(
    "Describe the ideal candidate (skills, experience, tools, education, etc.)",
    height=200,
    placeholder="E.g., We are looking for a Senior Data Scientist with 5+ years of experience in machine learning, Python, TensorFlow, and AWS..."
)

if not job_description.strip():
    st.info("💡 Please enter job requirements to begin.")
else:
    # -------------------------------
    # Upload Resumes
    # -------------------------------
    st.markdown("### 📎 Upload Resumes (PDF/DOCX)")
    uploaded_files = st.file_uploader(
        "Upload up to 1,000 resumes",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        help="Max 1,000 files supported"
    )

    if not uploaded_files:
        st.warning("📤 Please upload at least one resume.")
    else:
        if len(uploaded_files) > 1000:
            st.error("❌ Maximum 1,000 resumes allowed. Please reduce the number.")
        else:
            # Button to start analysis
            if st.button("🚀 Start Evaluation", type="primary"):
                # Read all files
                files_data = []
                for file in uploaded_files:
                    file.seek(0)
                    files_data.append((file.read(), file.type))

                # Progress bar
                total = len(files_data)
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Analyze all resumes
                results = []
                for i, (content, file_type) in enumerate(files_data):
                    status_text.text(f"Processing {i+1}/{total}: {uploaded_files[i].name}")
                    text = analyzer.extract_text(content, file_type)

                    if not text.strip():
                        result = {
                            "Resume Name": uploaded_files[i].name,
                            "Error": "Text extraction failed"
                        }
                    else:
                        analysis = analyzer.analyze_resume(text, job_description)
                        result = {
                            "Resume Name": uploaded_files[i].name,
                            "Overall Match Score": analysis["overall_match_score"],
                            "Keywords Matched": ", ".join(analysis["keywords_matched"]),
                            "Semantic Relevance": analysis["semantic_relevance"],
                            "Summary": analysis["summary"]
                        }
                    results.append(result)
                    progress_bar.progress((i + 1) / total)

                # Save results to session state
                df = pd.DataFrame(results)
                # df = df[df["Error"] != "Text extraction failed"]  # Remove failed
                df = df[df.apply(lambda row: row.get("Error") != "Failed to extract text", axis=1)]
                df = df.sort_values("Overall Match Score", ascending=False).reset_index(drop=True)
                df["Rank"] = df.index.map(lambda x: f"{x+1}{'st' if x==0 else 'nd' if x==1 else 'rd' if x==2 else 'th'}")

                st.session_state['results_df'] = df
                st.session_state['analysis_done'] = True

                status_text.text("✅ Analysis complete!")
                progress_bar.empty()

    # -------------------------------
    # Dynamic Display: Show only if analysis was done
    # -------------------------------
    if st.session_state.get('analysis_done', False):
        df = st.session_state['results_df']

        st.markdown("### 📊 Evaluation Results")

        # 🔁 This dropdown now works dynamically!
        top_options = [1, 2, 3, 5, 10, 20, 50, 100, "All"]
        choice = st.selectbox(
            "🔽 Show top candidates:",
            top_options,
            index=3,  # Default: Top 10
            key="top_n_selector"  # Unique key to track changes
        )

        # Dynamic filtering based on selection
        if choice == "All":
            display_df = df.copy()
        else:
            display_df = df.head(choice).copy()

        st.dataframe(display_df, use_container_width=True)

        # Stats
        st.caption(f"✅ Total processed: {len(df)} | Top match: {df['Overall Match Score'].iloc[0] if len(df) > 0 else 'N/A'}")

        # Export
        csv = df.to_csv(index=False)
        st.download_button(
            "⬇️ Download Full Report (CSV)",
            data=csv,
            file_name="resume_evaluation_results.csv",
            mime="text/csv",
            disabled=False
        )

        # Expandable raw view
        with st.expander("🔍 View Raw JSON Results"):
            st.json(df.to_dict("records"))