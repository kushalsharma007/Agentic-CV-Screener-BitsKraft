# model_handling.py
import io
import fitz  # PyMuPDF
from docx import Document
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
import pytesseract
from pdf2image import convert_from_bytes
from typing import List, Dict, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional: Set Tesseract path if not in PATH
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class UniversalResumeAnalyzer:

    def __init__(self):
        """
        Initialize the analyzer with a lightweight sentence transformer model.
        """
        try:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ SentenceTransformer model loaded.")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise

    def extract_text_from_pdf(self, content: bytes) -> str:
        """
        Extract text from PDF using PyMuPDF.
        Falls back to OCR if no text found.
        """
        try:
            pdf_stream = io.BytesIO(content)
            doc = fitz.open(stream=pdf_stream, filetype="pdf")
            text = ""
            for page in doc:
                page_text = page.get_text("text")
                if page_text.strip():
                    text += page_text + "\n"
            doc.close()

            if text.strip():
                logger.info(f"✅ Extracted {len(text)} characters from PDF (text-based)")
                return text
            else:
                logger.info("📄 No extractable text in PDF. Trying OCR...")
                return self.extract_text_with_ocr(content)
        except Exception as e:
            logger.warning(f"PDF text extraction failed: {e}")
            return ""

    def extract_text_from_docx(self, content: bytes) -> str:
        """
        Extract text from .docx file.
        """
        try:
            doc = Document(io.BytesIO(content))
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            text = "\n".join(paragraphs)
            logger.info(f"✅ Extracted {len(text)} characters from DOCX")
            return text
        except Exception as e:
            logger.warning(f"DOCX extraction failed: {e}")
            return ""

    def extract_text_with_ocr(self, content: bytes) -> str:
        """
        Use OCR to extract text from scanned PDFs.
        Converts PDF pages to images and runs Tesseract OCR.
        """
        try:
            # Convert PDF to list of PIL images
            images = convert_from_bytes(content, dpi=200)  # High DPI for clarity
            text = ""
            for i, img in enumerate(images):
                # Preprocess: Convert to grayscale for better OCR
                img = img.convert("L")
                # Optional: Apply threshold to make text clearer
                # img = img.point(lambda x: 0 if x < 140 else 255, mode='1')

                page_text = pytesseract.image_to_string(img, lang='eng')
                if page_text.strip():
                    text += f"Page {i+1}:\n{page_text}\n\n"
                else:
                    logger.info(f"❌ OCR found no text on page {i+1}")
            text = text.strip()
            if text:
                logger.info(f"✅ OCR succeeded: extracted {len(text)} characters")
            else:
                logger.warning("❌ OCR returned no text")
            return text
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""

    def extract_text(self, content: bytes, file_format: str) -> str:

        if not content or len(content) == 0:
            logger.warning("Empty file content.")
            return ""

        try:
            if file_format == "pdf":
                return self.extract_text_from_pdf(content)
            elif file_format == "docx":
                return self.extract_text_from_docx(content)
            else:
                logger.warning(f"Unsupported format: {file_format}")
                return ""
        except Exception as e:
            logger.error(f"Error in extract_text: {e}")
            return ""

    def preprocess_text(self, text: str) -> str:
        """
        Clean and normalize text.
        """
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = re.sub(r'[^\w\s\-]', '', text)  # Remove punctuation
        return text.lower().strip()

    def extract_keywords(self, job_desc: str, top_n: int = 30) -> List[str]:
        """
        Extract potential keywords from job description.
        """
        # Extract proper nouns (capitalized words)
        proper_nouns = re.findall(r'\b[A-Z][a-z]{2,}\b', job_desc)

        # Common tech keywords (case-insensitive)
        tech_keywords = re.findall(
            r'(?i)\b(Python|Java|C\+\+|JavaScript|TypeScript|React|Angular|Vue|Node\.js|Django|Flask|'
            r'Spring|Hibernate|PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch|Docker|Kubernetes|'
            r'AWS|Azure|GCP|Lambda|S3|EC2|Terraform|Ansible|Jenkins|Git|GitHub|GitLab|CI/CD|'
            r'Agile|Scrum|Kanban|REST|API|GraphQL|Microservices|Serverless|Linux|Bash|Shell|'
            r'TensorFlow|PyTorch|Keras|Pandas|NumPy|Scikit-learn|NLP|ML|AI|Data Science)\b',
            job_desc
        )

        # Combine and deduplicate
        combined = list(set(proper_nouns + [kw.title() for kw in tech_keywords]))
        return combined[:top_n]

    def get_embedding(self, text: str) -> np.ndarray:
        """
        Get sentence embedding.
        """
        if not text.strip():
            return self.model.encode("")
        return self.model.encode(text)

    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        Compute cosine similarity between two texts.
        """
        if not text1.strip() or not text2.strip():
            return 0.0
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)
        return cosine_similarity([emb1], [emb2])[0][0]

    def analyze_resume(self, resume_text: str, job_description: str) -> Dict:
        """
        Analyze a single resume against the job description.
        """
        clean_resume = self.preprocess_text(resume_text)
        clean_job = self.preprocess_text(job_description)

        # 1. Semantic Relevance (60% weight)
        semantic_sim = self.compute_similarity(clean_resume, clean_job)
        semantic_score = semantic_sim * 100  # Scale to 0–100

        # 2. Keyword Matching (40% weight)
        keywords = self.extract_keywords(job_description, top_n=30)
        matched = [kw for kw in keywords if kw.lower() in clean_resume]
        keyword_score = (len(matched) / len(keywords)) * 100 if keywords else 0

        # Final weighted score
        final_score = 0.60 * semantic_score + 0.40 * keyword_score
        final_score = round(min(final_score, 100), 1)

        return {
            "overall_match_score": final_score,
            "keywords_matched": matched,
            "keywords_total": keywords,
            "semantic_relevance": round(semantic_score, 1),
            "summary": (
                "Outstanding Match" if final_score > 80 else
                "Strong Match" if final_score > 65 else
                "Moderate Match" if final_score > 50 else
                "Needs Improvement" if final_score > 35 else
                "Unsatisfactory"
            )
        }

    def batch_analyze(self, files: List[Tuple[bytes, str]], job_description: str) -> List[Dict]:
        """
        Analyze multiple resumes in batch.
        :param files: List of (content, format) tuples, format in ['pdf', 'docx']
        :param job_description: Job description text
        :return: List of analysis results
        """
        results = []
        for i, (content, file_format) in enumerate(files):
            try:
                text = self.extract_text(content, file_format)
                if not text.strip():
                    result = {
                        "Error": "No text extracted",
                        "overall_match_score": 0.0,
                        "keywords_matched": [],
                        "semantic_relevance": 0.0,
                        "summary": "No content detected"
                    }
                else:
                    analysis = self.analyze_resume(text, job_description)
                    result = {
                        "overall_match_score": analysis["overall_match_score"],
                        "keywords_matched": analysis["keywords_matched"],
                        "semantic_relevance": analysis["semantic_relevance"],
                        "summary": analysis["summary"]
                    }
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process file {i}: {e}")
                results.append({
                    "Error": str(e),
                    "overall_match_score": 0.0,
                    "keywords_matched": [],
                    "semantic_relevance": 0.0,
                    "summary": "Processing failed"
                })
        return results