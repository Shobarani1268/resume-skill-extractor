import streamlit as st
from PyPDF2 import PdfReader
from docx import Document
import re

# ---------------------------
# Simple tokenizer & helpers
# ---------------------------
def simple_tokenize(text):
    # Lowercase and split on whitespace and punctuation
    # Keeps things safe and portable for deployment
    text = text.lower()
    # replace non-alphanumeric characters with space (keep + and # if you like)
    text = re.sub(r'[^a-z0-9\+\#\s]', ' ', text)
    tokens = [t for t in text.split() if t]
    return tokens

# ---------------------------
# Skill keywords (adjustable)
# ---------------------------
SKILL_KEYWORDS = {
    "Python": ["python"],
    "Java": ["java"],
    "C": ["c programming", "c "],
    "C++": ["c++", "cpp"],
    "HTML": ["html"],
    "CSS": ["css"],
    "JavaScript": ["javascript", "js"],
    "Data Analysis": ["data analysis", "data analyst", "excel", "power bi"],
    "Machine Learning": ["machine learning", "ml"],
    "SQL": ["sql", "mysql"],
}

# ---------------------------
# Extract text from uploads
# ---------------------------
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def extract_text_from_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

# ---------------------------
# Skill extraction logic
# ---------------------------
def extract_skills(text):
    text_lower = text.lower()
    tokens = simple_tokenize(text_lower)

    found_skills = []
    for skill, keywords in SKILL_KEYWORDS.items():
        for keyword in keywords:
            # for multi-word keywords use substring search
            if " " in keyword:
                if keyword in text_lower:
                    found_skills.append(skill)
                    break
            else:
                # single word: check token membership
                if keyword in tokens:
                    found_skills.append(skill)
                    break
    return sorted(set(found_skills))

# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title="Resume Skill Extractor", layout="centered")
st.title("📄 Resume Skill Extractor")
st.write("Upload a PDF or DOCX resume to extract skills.")

uploaded_file = st.file_uploader("Upload resume", type=["pdf", "docx"])

if uploaded_file:
    st.success("File uploaded")
    # Extract text depending on type
    if uploaded_file.type == "application/pdf" or uploaded_file.name.lower().endswith(".pdf"):
        resume_text = extract_text_from_pdf(uploaded_file)
    else:
        resume_text = extract_text_from_docx(uploaded_file)

    if not resume_text or len(resume_text.strip()) < 10:
        st.warning("Extracted very little text. If your resume is a scanned image PDF, OCR is required.")
    else:
        skills = extract_skills(resume_text)
        st.subheader("📌 Extracted Skills")
        if skills:
            st.write(", ".join(skills))
        else:
            st.write("No skills detected. Try expanding SKILL_KEYWORDS in the code.")

        st.subheader("📄 Resume text preview")
        st.text_area("Preview", resume_text[:4000], height=200)
