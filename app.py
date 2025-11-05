import streamlit as st
import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from PyPDF2 import PdfReader
from docx import Document

# Download required NLTK resources
nltk.download('punkt')
nltk.download('stopwords')

# Skill keywords
SKILL_KEYWORDS = {
    "Python": ["python", "py"],
    "Java": ["java"],
    "C": ["c programming"],
    "C++": ["cpp", "c++"],
    "HTML": ["html"],
    "CSS": ["css"],
    "JavaScript": ["javascript", "js"],
    "Data Analysis": ["data analysis", "data analyst", "excel", "power bi"],
    "Machine Learning": ["machine learning", "ml"],
    "SQL": ["sql", "mysql"],
}

def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_text_from_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_skills(text):
    text = text.lower()
    words = word_tokenize(text)

    stop_words = set(stopwords.words("english"))
    words = [w for w in words if w not in stop_words]

    found_skills = []

    for skill, keywords in SKILL_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                found_skills.append(skill)
                break

    return list(set(found_skills))

# ------------------------------------------------------------
# Streamlit Website UI
# ------------------------------------------------------------
st.title("📄 Resume Skill Extractor")
st.write("Upload your **PDF or DOCX resume** and extract your skills automatically!")

uploaded_file = st.file_uploader("Upload your Resume", type=["pdf", "docx"])

if uploaded_file:
    st.success("✅ File uploaded successfully!")

    # Read text
    if uploaded_file.type == "application/pdf":
        resume_text = extract_text_from_pdf(uploaded_file)
    else:
        resume_text = extract_text_from_docx(uploaded_file)

    st.subheader("📌 Extracted Skills:")
    skills = extract_skills(resume_text)

    if skills:
        st.write(", ".join(skills))
    else:
        st.write("No skills found 😕")

    st.subheader("📄 Extracted Text (Preview)")
    st.text_area("Resume text:", resume_text[:2000])
