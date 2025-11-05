# app.py
import streamlit as st
import pdfplumber
import docx2txt
import re
import json
from io import BytesIO
from reportlab.pdfgen import canvas
from difflib import SequenceMatcher

# ---------------- page config & css ----------------
st.set_page_config(page_title="AI Resume Analyzer Pro", layout="wide", page_icon="🧾")

st.markdown("""
    <style>
        body { background: linear-gradient(135deg,#f3f6fb,#eef2f7); font-family: "Segoe UI", Roboto, Arial; }
        .card { background: rgba(255,255,255,0.86); padding: 20px; border-radius: 12px; box-shadow: 0 8px 25px rgba(30,40,50,0.06); }
        .muted { color: #6b7280; }
        .score { font-size: 48px; color: #0645AD; font-weight:700; }
    </style>
""", unsafe_allow_html=True)


# ---------------- helpers: text extraction ----------------
def extract_text(file):
    ext = file.name.split(".")[-1].lower()
    if ext == "pdf":
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    elif ext == "docx":
        return docx2txt.process(file)
    elif ext == "txt":
        return file.read().decode("utf-8", errors="ignore")
    return ""


# ---------------- simple tokenizer ----------------
def simple_tokenize(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\+\#\s]', ' ', text)
    tokens = [t for t in text.split() if t]
    return tokens


# ---------------- skill/job database ----------------
JOB_ROLES = {
    "Data Scientist": ["python", "pandas", "numpy", "scikit-learn", "machine learning", "sql", "data analysis", "visualization"],
    "Machine Learning Engineer": ["python", "tensorflow", "keras", "pytorch", "model", "training", "deployment", "docker"],
    "Backend Developer": ["python", "java", "node", "sql", "api", "rest", "django", "flask"],
    "Frontend Developer": ["html", "css", "javascript", "react", "ui", "typescript"],
    "Data Analyst": ["excel", "sql", "power bi", "tableau", "pandas", "data visualization"],
    "Product Manager": ["product", "roadmap", "communication", "stakeholder", "leadership"]
}

# normalized flat skill keywords (for quick extraction)
SKILL_KEYWORDS = sorted({kw for skills in JOB_ROLES.values() for kw in skills})

# ---------------- extraction functions ----------------
def extract_skills_from_text(text):
    t = text.lower()
    found = []
    for kw in SKILL_KEYWORDS:
        if kw in t:
            found.append(kw)
    # also capture common single-word tokens like 'python', 'sql' etc.
    tokens = set(simple_tokenize(text))
    for tok in tokens:
        if tok in SKILL_KEYWORDS and tok not in found:
            found.append(tok)
    return sorted(set(found))


def extract_education(text):
    patterns = [
        r"\b(b\.?tech|bachelor of technology|btech|b\.tech)\b",
        r"\b(m\.?tech|master of technology|mtech|m\.tech)\b",
        r"\b(b\.?sc|bachelor of science|bsc)\b",
        r"\b(m\.?sc|master of science|msc)\b",
        r"\b(mba|master of business administration)\b",
        r"\b(diploma)\b"
    ]
    found = []
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            found.append(re.search(p, text, re.IGNORECASE).group(0))
    return [f.title() for f in sorted(set(found))]


def extract_experience_mentions(text):
    # returns years mentions and role keywords (simple)
    yrs = re.findall(r"(\d+)\s*\+?\s*(years?)", text, re.IGNORECASE)
    years = [int(m[0]) for m in yrs] if yrs else []
    roles = []
    for role_kw in ["engineer", "developer", "analyst", "manager", "intern", "consultant", "scientist"]:
        if re.search(r"\b" + re.escape(role_kw) + r"\b", text, re.IGNORECASE):
            roles.append(role_kw.title())
    return {"years_mentioned": years, "roles_mentioned": roles}


# ---------------- scoring logic ----------------
def resume_score(skills, education, experience_info, full_text):
    # weights (tweakable)
    w_skills = 0.45
    w_education = 0.15
    w_experience = 0.25
    w_format = 0.15

    # skills score: proportion of matched skills vs a notional desired number (6)
    skill_count = len(skills)
    skills_score = min(skill_count / 6.0, 1.0) * 100  # 0-100

    # education score simple: presence gives full points
    edu_score = 100 if education else 0

    # experience score: if years mentioned >0 give partial
    yrs = experience_info.get("years_mentioned", [])
    exp_score = 0
    if yrs:
        max_years = max(yrs)
        exp_score = min(max_years / 8.0, 1.0) * 100  # treat 8+ years as full

    # format score: contact info + sections + length
    format_score = 0
    contact = bool(re.search(r"\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b", full_text)) and bool(re.search(r"\+?\d[\d\-\s]{7,}\d', full_text))
    # fallback simpler checks:
    email = bool(re.search(r"[\w\.-]+@[\w\.-]+\.\w{2,4}", full_text))
    phone = bool(re.search(r"\+?\d[\d\-\s]{7,}\d", full_text))
    has_sections = all(re.search(r"\b" + sec + r"\b", full_text, re.IGNORECASE) for sec in ["experience", "education", "skills"])
    length_words = len(simple_tokenize(full_text))
    length_ok = 200 <= length_words <= 2000

    # simple formatting heuristics
    fs_points = 0
    fs_points += 40 if email and phone else 0
    fs_points += 30 if has_sections else 0
    fs_points += 30 if length_ok else 0
    format_score = fs_points  # 0-100

    # combine
    final = (skills_score * w_skills) + (edu_score * w_education) + (exp_score * w_experience) + (format_score * w_format)
    return {
        "score": round(final, 1),
        "breakdown": {
            "skills_score": round(skills_score,1),
            "education_score": round(edu_score,1),
            "experience_score": round(exp_score,1),
            "format_score": round(format_score,1)
        }
    }


# ---------------- job role matching ----------------
def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def job_role_matches(extracted_skills):
    # For each role, compute overlap ratio and a simple similarity
    results = []
    for role, req_skills in JOB_ROLES.items():
        req_set = set([s.lower() for s in req_skills])
        found_set = set([s.lower() for s in extracted_skills])
        common = req_set.intersection(found_set)
        overlap_ratio = len(common) / max(len(req_set),1)
        # also compute token similarity (not heavy)
        sim = sum(similarity(r, ' '.join(found_set)) for r in req_set) / max(len(req_set),1)
        score = round((overlap_ratio * 0.75 + sim * 0.25)*100,1)
        missing = sorted(list(req_set - found_set))
        results.append({"role": role, "match_score": score, "matched_skills": sorted(list(common)), "missing_skills": missing})
    # sort by score desc
    results = sorted(results, key=lambda x: x["match_score"], reverse=True)
    return results


# ---------------- ATS checker ----------------
def ats_check(text, extracted_skills):
    issues = []
    # contact info
    if not re.search(r"[\w\.-]+@[\w\.-]+\.\w{2,4}", text):
        issues.append(("Missing email", "Add an email address"))
    if not re.search(r"\+?\d[\d\-\s]{7,}\d", text):
        issues.append(("Missing phone", "Add phone number with country code if possible"))
    # essential sections
    for sec in ["experience", "education", "skills"]:
        if not re.search(r"\b" + sec + r"\b", text, re.IGNORECASE):
            issues.append((f"Missing section: {sec.title()}", f"Add a {sec} section with bullets"))
    # too short or too long
    words = len(simple_tokenize(text))
    if words < 150:
        issues.append(("Resume too short", "Try to add more accomplishments or details"))
    if words > 4000:
        issues.append(("Resume too long", "Trim down to 1-2 pages"))
    # bullets
    bullets = len(re.findall(r"(^|\n)\s*[-•\u2022]\s+", text))
    if bullets < 3:
        issues.append(("Few bullet points", "Use bullet points for achievements under each role"))
    # keyword density warning if few skills
    if len(extracted_skills) < 3:
        issues.append(("Few detected skills", "Add more relevant skill keywords (tools, languages, frameworks)"))
    return issues


# ---------------- report generation ----------------
def generate_pdf_report(data):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(595, 842))  # A4-ish
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, 800, "AI Resume Analyzer Report")
    c.setFont("Helvetica", 12)
    y = 770
    for k, v in data.items():
        c.drawString(40, y, f"{k}:")
        y -= 18
        if isinstance(v, list):
            for item in v:
                c.drawString(60, y, f"- {item}")
                y -= 14
        else:
            c.drawString(60, y, str(v))
            y -= 20
        y -= 6
        if y < 80:
            c.showPage()
            y = 800
    c.save()
    buffer.seek(0)
    return buffer


# ---------------- UI ----------------
st.title("🧾 AI Resume Analyzer — Pro Features")
col1, col2 = st.columns([2,1])

with col1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload resume (PDF/DOCX/TXT)", type=["pdf","docx","txt"])
    if uploaded:
        st.success("File uploaded")
        text = extract_text(uploaded)
        if st.button("Analyze"):
            # extract
            skills = extract_skills_from_text(text)
            education = extract_education(text)
            experience_info = extract_experience_mentions(text)
            score_obj = resume_score(skills, education, experience_info, text)
            matches = job_role_matches(skills)
            ats_issues = ats_check(text, skills)

            # show results
            st.markdown("## Summary")
            st.markdown(f"<div class='card'><div style='display:flex;align-items:center;justify-content:space-between'>"
                        f"<div><strong>Overall Score</strong><div class='score'>{score_obj['score']}</div></div>"
                        f"<div style='text-align:right'><small class='muted'>Skills: {score_obj['breakdown']['skills_score']} | "
                        f"Edu: {score_obj['breakdown']['education_score']} | Exp: {score_obj['breakdown']['experience_score']} | "
                        f"Format: {score_obj['breakdown']['format_score']}</small></div></div></div>", unsafe_allow_html=True)

            st.markdown("### 🔎 Top matched job roles")
            for r in matches[:4]:
                st.markdown(f"- **{r['role']}** — Match: **{r['match_score']}%** — Matched: {', '.join(r['matched_skills']) or '—'}")

            st.markdown("### 🛠 Detected skills")
            st.write(", ".join([s.title() for s in skills]) or "None detected")

            st.markdown("### 🎓 Education found")
            st.write(", ".join(education) or "None detected")

            st.markdown("### 💼 Experience mentions")
            st.write(f"Years mentioned: {experience_info.get('years_mentioned', [])} | Roles: {', '.join(experience_info.get('roles_mentioned',[])) or '—'}")

            st.markdown("### ⚠ ATS Checklist")
            if ats_issues:
                for i,issue in enumerate(ats_issues,1):
                    st.markdown(f"{i}. **{issue[0]}** — {issue[1]}")
            else:
                st.success("Looks good for automated ATS parsing!")

            # download data
            result_data = {
                "score": score_obj,
                "skills": skills,
                "education": education,
                "experience_info": experience_info,
                "job_matches": matches,
                "ats_issues": ats_issues
            }
            st.download_button("Download JSON report", json.dumps(result_data, indent=2), "resume_report.json")

            pdf_buf = generate_pdf_report({
                "Score": f"{score_obj['score']}",
                "Skills": [s.title() for s in skills],
                "Education": education,
                "Experience": experience_info.get("years_mentioned", []),
                "Top Role": matches[0]["role"] if matches else ""
            })
            st.download_button("Download PDF summary", pdf_buf, "resume_summary.pdf")

            # Suggest missing skills UI
            st.markdown("### 🧭 Suggest missing skills for a role")
            role_options = [m["role"] for m in matches[:6]]
            role_options += [r for r in JOB_ROLES.keys() if r not in role_options]
            selected = st.selectbox("Choose a job role to compare", role_options)
            reqs = JOB_ROLES[selected]
            missing = [r for r in reqs if r.lower() not in skills]
            if missing:
                st.warning(f"Missing skills for {selected}: {', '.join(missing)}")
            else:
                st.success(f"You have most required skills for {selected}!")

    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("How Score is calculated")
    st.markdown("""
    - **Skills (45%)** — number of detected relevant skills (6+ = full)  
    - **Education (15%)** — presence of degree keywords  
    - **Experience (25%)** — years mentioned in resume  
    - **Format (15%)** — contact info, sections, reasonable length, bullets  
    """)
    st.info("Tip: Use clear section headings (Experience, Education, Skills) and add 6+ key skills relevant to the job.")
    st.markdown("</div>", unsafe_allow_html=True)
