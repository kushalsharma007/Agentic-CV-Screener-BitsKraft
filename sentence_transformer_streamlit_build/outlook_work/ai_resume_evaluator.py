# ai_resume_evaluator.py
import pandas as pd
from pathlib import Path
from model_handling import UniversalResumeAnalyzer

class AIResumeEvaluator:
    def __init__(self):
        self.analyzer = UniversalResumeAnalyzer()

    def evaluate_resumes(self, resumes_files, job_description):
        results = []
        for file in resumes_files:
            filename = Path(file["FilePath"]).name
            with open(file["FilePath"], "rb") as f:
                content = f.read()
            file_format = "pdf" if filename.lower().endswith(".pdf") else "docx"
            text = self.analyzer.extract_text(content, file_format)
            
            # ✅ Removed split_keywords argument
            analysis = self.analyzer.analyze_resume(text, job_description)

            results.append({
                "Name": file.get("Name", "Unknown"),
                "Email": file.get("Email", "Unknown"),
                "Phone": file.get("Phone", "Unknown"),
                "LinkedIn": file.get("LinkedIn", "Unknown"),
                "GitHub": file.get("GitHub", "Unknown"),
                "Resume Name": filename,
                "Overall Match Score": analysis.get("overall_match_score", 0.0),
                "Keywords Matched": ", ".join(analysis.get("keywords_matched", [])),
                "Semantic Relevance": analysis.get("semantic_relevance", 0.0),
                "Summary": analysis.get("summary", "No summary available")
            })

        df = pd.DataFrame(results)
        df['Rank'] = df['Overall Match Score'].rank(ascending=False, method='first').astype(int)
        df = df.sort_values("Overall Match Score", ascending=False).reset_index(drop=True)
        return df
