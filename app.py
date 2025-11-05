import streamlit as st
import docx2txt
import pdfplumber
import re

# -----------------------------------------------------------
# ✅ UI SETTINGS
# -----------------------------------------------------------
st.set_page_config(page_title="AI Resume Analyzer", page_icon="🧠", layout="wide")

st.markdown("""
<style>
body { background-color: #F4F7FB; }
.main-card {
    background: white;
    padding: 40px;
    border-radius: 18px;
    box-shadow: 0 5px 25px rgba(0,0,0,0.12);
    animation: fadeIn 1s ease;
}
@keyframes fadeIn {
    from {opacity: 0; transform: translateY(20px);}
    to {opacity: 1; transform: translateY(0);}
}
.result-box {
    background: #EDF2FE;
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0 3px 15px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------
# ✅ Extract Text
# -----------------------------------------------------------
def extract_text(file):
    ext = file.name.split(".")[-1]

    if ext == "pdf":
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                try:
                    t = page.extract_text()
                except:
                    t = ""
                if t:
                    text += t + "\n"
        return text

    elif ext == "docx":
        return docx2txt.process(file)

    elif ext == "txt":
        return file.read().decode("utf-8")

    else:
        return ""

# -----------------------------------------------------------
# ✅ Skills list (expandable)
# -----------------------------------------------------------
SKILL_KEYWORDS = [
    "python", "java", "c", "c++", "html", "css", "javascript", "react", "node",
    "sql", "machine learning", "deep learning", "power bi", "tableau",
    "excel", "communication", "leadership", "data analysis", "teamwork",
    "django", "flask", "nlp", "ui/ux", "testing", "cloud", "aws", "github"
]

# -----------------------------------------------------------
# ✅ Extract Skills
# -----------------------------------------------------------
def extract_skills(text):
    text_lower = text.lower()
    found = [s.title() for s in SKILL_KEYWORDS if s in text_lower]
    return list(set(found))

# -----------------------------------------------------------
# ✅ ✅ FIXED — Extract Education
# -----------------------------------------------------------
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
        matches = re.findall(p, text, re.IGNORECASE)

        for m in matches:
            if isinstance(m, tuple):
                found.append(m[0].title())
            else:
                found.append(m.title())

    return list(set(found))

# -----------------------------------------------------------
# ✅ Extract Experience
# -----------------------------------------------------------
def extract_experience(text):
    patterns = [
        r"(\d+\s+years?\s+experience)",
        r"(\d+\+?\s+years)",
        r"(intern|internship)",
        r"(software engineer|developer|analyst|manager|designer)"
    ]
    found = []

    for p in patterns:
        matches = re.findall(p, text, re.IGNORECASE)

        for m in matches:
            if isinstance(m, tuple):
                found.append(m[0].title())
            else:
                found.append(m.title())

    return list(set(found))

# -----------------------------------------------------------
# ✅ ATS Resume Score (Rule-based)
# -----------------------------------------------------------
def resume_score(skills, edu, exp, full_text):
    score = 0

    # Skills  
    score += len(skills) * 5

    # Education
    if edu:
        score += 10

    # Experience
    if exp:
        score += 15

    # ✅ FIXED CONTACT REGEX
    contact = (
        bool(re.search(r"\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b", full_text))
        and bool(re.search(r"\+?\d[\d\-\s]{7,}\d", full_text))
    )

    if contact:
        score += 15

    return min(score, 100)

# -----------------------------------------------------------
# ✅ Missing Skills Suggestion
# -----------------------------------------------------------
def missing_skills(skills):
    return [s.title() for s in SKILL_KEYWORDS if s.title() not in skills]

# -----------------------------------------------------------
# ✅ Job Role Matching
# -----------------------------------------------------------
JOB_ROLES = {
    "Software Developer": ["python", "java", "c++", "github", "sql"],
    "Web Developer": ["html", "css", "javascript", "react", "node"],
    "Data Analyst": ["excel", "sql", "power bi", "tableau", "python"],
    "ML Engineer": ["python", "machine learning", "deep learning", "nlp"],
}

def match_job_role(skills):
    best_match = "Not Enough Info"
    best_score = 0

    for role, req_skills in JOB_ROLES.items():
        score = len([s for s in req_skills if s.title() in skills])
        if score > best_score:
            best_score = score
            best_match = role

    return best_match

# -----------------------------------------------------------
# ✅ UI LAYOUT
# -----------------------------------------------------------
st.markdown("<div class='main-card'>", unsafe_allow_html=True)

st.title("🧠 AI Resume Analyzer")
st.write("Upload your resume to get Skills, Education, Experience, ATS Score, Job Match & Missing Skills.")

uploaded_file = st.file_uploader("Upload Resume", type=["pdf", "docx", "txt"])

if uploaded_file:
    st.success("✅ File uploaded successfully!")

    full_text = extract_text(uploaded_file)

    if st.button("🔍 Analyze Resume"):
        skills = extract_skills(full_text)
        edu = extract_education(full_text)
        exp = extract_experience(full_text)
        score = resume_score(skills, edu, exp, full_text)
        missing = missing_skills(skills)
        matched_role = match_job_role(skills)

        st.markdown("<div class='result-box'>", unsafe_allow_html=True)

        st.subheader("✅ Extracted Skills")
        st.write(skills)

        st.subheader("🎓 Education")
        st.write(edu)

        st.subheader("💼 Experience")
        st.write(exp)

        st.subheader("📊 ATS Resume Score")
        st.success(f"⭐ Your Resume Score: **{score}/100**")

        st.subheader("✅ Job Role Match")
        st.info(f"Best Match: **{matched_role}**")

        st.subheader("🚀 Missing Skills To Improve Your Resume")
        st.warning(missing)

        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
