import streamlit as st
import docx2txt
import pdfplumber
import re

# -------------------------
# ✅ Page Design
# -------------------------
st.set_page_config(page_title="Resume Skill Extractor", page_icon="✅", layout="centered")

st.markdown("""
    <style>
        body {
            background-color: #F4F6F9;
        }
        .main-card {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            animation: fadeIn 1.2s ease;
        }
        @keyframes fadeIn {
            from {opacity: 0; transform: translateY(20px);}
            to {opacity: 1; transform: translateY(0);}
        }
        .result-box {
            background: #E8F0FE;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
            box-shadow: 0 3px 12px rgba(0,0,0,0.1);
        }
    </style>
""", unsafe_allow_html=True)


# -------------------------
# ✅ Function: Extract text
# -------------------------
def extract_text(file):
    ext = file.name.split(".")[-1]

    if ext == "pdf":
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text

    elif ext == "docx":
        return docx2txt.process(file)

    elif ext == "txt":
        return file.read().decode("utf-8")

    else:
        return ""


# -------------------------
# ✅ Function: Extract Skills
# -------------------------
def extract_skills(text):
    skill_keywords = [
        "python", "java", "c", "c++", "html", "css", "javascript", "sql",
        "excel", "power bi", "machine learning", "data analysis",
        "react", "node", "tableau", "deep learning", "communication",
        "leadership", "teamwork", "problem solving"
    ]

    text_lower = text.lower()
    skills = [s.title() for s in skill_keywords if s in text_lower]
    return skills


# -------------------------
# ✅ Function: Extract Education
# -------------------------
def extract_education(text):
    patterns = [
        r"(B\.?Tech|Bachelor of Technology)",
        r"(M\.?Tech|Master of Technology)",
        r"(B\.?Sc|Bachelor of Science)",
        r"(M\.?Sc|Master of Science)",
        r"(B\.?Com|Bachelor of Commerce)",
        r"(MBA|Master of Business Administration)",
        r"(Diploma)",
        r"(Intermediate|12th|HSC)",
        r"(10th|SSC)"
    ]

    found = []
    for p in patterns:
        match = re.findall(p, text, re.IGNORECASE)
        found.extend(match)

    return list(set([x.title() for x in found]))


# -------------------------
# ✅ Function: Extract Experience
# -------------------------
def extract_experience(text):
    exp_patterns = [
        r"(\d+\s+years?\s+experience)",
        r"(\d+\+?\s+years)",
        r"(experience\s+of\s+\d+\s+years)",
        r"(intern|internship)",
        r"(software engineer|developer|analyst|manager|designer)"
    ]

    found = []
    for p in exp_patterns:
        match = re.findall(p, text, re.IGNORECASE)
        found.extend(match)

    return list(set([x.title() for x in found]))


# -------------------------
# ✅ UI Layout
# -------------------------
st.markdown("<div class='main-card'>", unsafe_allow_html=True)

st.title("📄 Resume Analyzer (Skills + Education + Experience)")
st.write("Upload your resume to extract structured information.")

uploaded_file = st.file_uploader("Upload Resume", type=["pdf", "docx", "txt"])

if uploaded_file:
    st.success("✅ File uploaded successfully!")

    text = extract_text(uploaded_file)

    if st.button("Extract Information"):
        skills = extract_skills(text)
        education = extract_education(text)
        experience = extract_experience(text)

        st.markdown("<div class='result-box'>", unsafe_allow_html=True)

        st.subheader("✅ Extracted Skills")
        st.write(skills if skills else "No skills found.")

        st.subheader("🎓 Extracted Education")
        st.write(education if education else "No education found.")

        st.subheader("💼 Extracted Experience")
        st.write(experience if experience else "No experience found.")

        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
