# resume_Parse.py
import os
from pathlib import Path
import pandas as pd
import fitz  # PyMuPDF
import re

class ResumeParser:
    def __init__(self, save_dir="uploads/resumes"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.df = pd.DataFrame()  # store parsed data

    def extract_text_from_pdf(self, file_path):
        text = ""
        try:
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        return text

    def normalize_phone(self, num):
        digits = re.sub(r'\D', '', num)
        if digits.startswith("977") and len(digits) == 13:
            return "+977" + digits[3:]
        elif len(digits) == 10:
            return digits
        return None

    def extract_emails(self, text):
        return re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)

    def extract_linkedin(self, text):
        matches = re.findall(r'(?:https?://)?(?:www\.)?linkedin\.com/[A-Za-z0-9_/.-]+', text)
        return matches[0] if matches else ""

    def extract_github(self, text):
        matches = re.findall(r'(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9_-]+', text)
        return matches[0] if matches else ""

    def parse_pdfs(self):
        data = []
        for file in self.save_dir.glob("*.pdf"):
            try:
                text = self.extract_text_from_pdf(file)
                emails = self.extract_emails(text)
                phones = [self.normalize_phone(p) for p in re.findall(r'(\+?977\d{10}|\b\d{10}\b)', text)]
                linkedin = self.extract_linkedin(text)
                github = self.extract_github(text)
                
                # Extract Name (simple heuristic)
                name = None
                for line in text.splitlines():
                    if 'name' in line.lower():
                        name = line.split(":")[-1].strip()
                        break
                if not name:
                    for line in text.splitlines():
                        if line.strip():
                            name = line.strip()
                            break

                data.append({
                    "Name": name or "Unknown",
                    "Email": ", ".join(emails) if emails else "Unknown",
                    "Phone": ", ".join([p for p in phones if p]) if phones else "Unknown",
                    "LinkedIn": linkedin or "Unknown",
                    "GitHub": github or "Unknown",
                    "FileName": file.name
                })
            except Exception as e:
                print(f"Error parsing {file.name}: {e}")
        self.df = pd.DataFrame(data)
        print(f"📄 Parsed {len(self.df)} resumes.")
