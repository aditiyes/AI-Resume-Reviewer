import os

import streamlit as st

from reviewer import extract_resume_sections, extract_resume_text, report_to_markdown, review_resume


st.set_page_config(page_title="Resume Review Studio", page_icon="R", layout="wide")
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
    :root { --ink:#1c2b28; --muted:#687771; --paper:#f5f5ef; --line:#dce3dc; --green:#1e6651; --green-dark:#143e34; --lime:#c8ed87; --coral:#e28b67; }
    html, body, [class*="css"] { font-family:'DM Sans',sans-serif; color:var(--ink); }
    .stApp { background:var(--paper); }
    h1,h2,h3 { font-family:'Manrope',sans-serif !important; color:var(--ink); letter-spacing:0 !important; }
    .block-container { max-width:1180px; padding-top:2rem; padding-bottom:4rem; }
    .hero { position:relative; overflow:hidden; background:var(--green-dark); color:#f6f7f0; padding:1.65rem 2rem 1.8rem; margin-bottom:2rem; border-bottom:5px solid var(--lime); animation:arrive .55s ease-out both; }
    .hero:after { content:'R'; position:absolute; right:2.4rem; bottom:-5.8rem; color:rgba(255,255,255,.055); font:800 15rem/1 'Manrope',sans-serif; pointer-events:none; }
    .hero-topline { display:flex; align-items:center; gap:.65rem; margin-bottom:.9rem; }
    .hero-mark { display:grid; place-items:center; width:28px; height:28px; background:var(--lime); color:var(--green-dark); font:500 .8rem 'DM Mono',monospace; }
    .eyebrow { font-family:'DM Mono',monospace; font-size:.72rem; text-transform:uppercase; color:var(--lime); }
    .hero h1 { color:#f6f7f0; font-size:2.8rem; line-height:1.06; margin:.25rem 0 .55rem; }
    .hero p { color:#c9d6ce; max-width:650px; margin:0; font-size:1rem; }
    .step-label { display:flex; align-items:center; gap:.55rem; font-family:'DM Mono',monospace; font-size:.73rem; color:var(--green); text-transform:uppercase; margin-bottom:.5rem; }
    .step-count { display:grid; place-items:center; width:25px; height:25px; background:var(--lime); color:var(--green-dark); font-size:.68rem; }
    .stButton>button[kind="primary"] { background:var(--green); border:0; border-radius:3px; color:white; font-weight:700; min-height:3.15rem; box-shadow:0 3px 0 var(--green-dark); transition:transform .16s ease, box-shadow .16s ease, background .16s ease; }
    .stButton>button[kind="primary"]:hover { background:#28795f; color:white; transform:translateY(-2px); box-shadow:0 5px 0 var(--green-dark); }
    [data-testid="stFileUploader"] { background:#fff; border:1px dashed #8da99a; border-radius:3px; transition:border-color .18s ease, background .18s ease; }
    [data-testid="stFileUploader"]:hover { border-color:var(--green); background:#fbfdf8; }
    [data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input { background:#fff; border-color:var(--line); border-radius:3px; }
    [data-testid="stTextArea"] textarea:focus, [data-testid="stTextInput"] input:focus { border-color:var(--green); box-shadow:0 0 0 1px var(--green); }
    .scope-list { margin-top:1.25rem; border-top:1px solid var(--line); }
    .scope-row { display:grid; grid-template-columns:36px 1fr; align-items:center; gap:.3rem; min-height:52px; border-bottom:1px solid var(--line); }
    .scope-index { color:var(--coral); font:500 .72rem 'DM Mono',monospace; }
    .scope-name { color:var(--ink); font:600 .92rem 'Manrope',sans-serif; }
    .scope-detail { display:block; color:var(--muted); font-size:.78rem; margin-top:1px; }
    .mode-indicator { display:flex; align-items:baseline; flex-wrap:wrap; gap:.25rem .6rem; background:#fff; border-left:3px solid var(--coral); padding:.7rem .8rem; margin:.9rem 0 1rem; }
    .mode-indicator.ai { border-left-color:var(--green); }
    .mode-eyebrow { color:var(--muted); font:500 .68rem 'DM Mono',monospace; text-transform:uppercase; }
    .mode-indicator strong { color:var(--ink); font:700 .85rem 'Manrope',sans-serif; }
    .mode-description { flex-basis:100%; color:var(--muted); font-size:.78rem; }
    .stTabs [data-baseweb="tab-list"] { gap:1.2rem; border-bottom:1px solid var(--line); }
    .stTabs [data-baseweb="tab"] { color:var(--muted); }
    .stTabs [aria-selected="true"] { color:var(--green) !important; }
    div[data-testid="stExpander"] { border-color:var(--line); border-radius:3px; background:#fff; }
    .note { color:var(--muted); font-size:.85rem; border-left:3px solid var(--coral); padding:.65rem .8rem; background:#fff; }
    @keyframes arrive { from { opacity:0; transform:translateY(9px); } to { opacity:1; transform:translateY(0); } }
    @media (max-width:640px) { .hero { padding:1.35rem 1.2rem 1.5rem; } .hero h1 { font-size:2rem; } .hero:after { right:.2rem; font-size:10rem; } .block-container { padding-top:1rem; } }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    "<div class='hero'><div class='hero-topline'><span class='hero-mark'>R/</span><span class='eyebrow'>Career toolkit&nbsp; / &nbsp;01</span></div><h1>Resume Review Studio</h1><p>Clear evidence. Better edits. A focused review of your experience against the role you want.</p></div>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("<div class='eyebrow' style='color:#1e6651;margin-bottom:.55rem'>Workspace / Settings</div>", unsafe_allow_html=True)
    st.markdown("### Review settings")
    api_key = st.text_input("OpenAI API key", value=os.getenv("OPENAI_API_KEY", ""), type="password", help="Optional. Without a key, the app uses a local keyword and structure review.")
    model = st.text_input("Model", value="gpt-4o-mini", disabled=not bool(api_key))
    st.markdown("<div class='note'>Your resume is processed for this review and is not saved by this app. AI-assisted analysis sends the supplied text to OpenAI.</div>", unsafe_allow_html=True)

left, right = st.columns([0.94, 1.06], gap="large")
with left:
    st.markdown("<div class='step-label'><span class='step-count'>01</span><span>Your resume</span></div>", unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload a resume", type=["pdf", "docx", "txt"], help="PDF, DOCX, or plain text. Scanned PDFs may need OCR first.")
    if uploaded:
        st.caption(f"{uploaded.name} · {uploaded.size / 1024:.0f} KB")
    st.markdown("<div class='step-label' style='margin-top:1.2rem'><span class='step-count'>02</span><span>Target role</span></div>", unsafe_allow_html=True)
    target_role = st.text_input("Role title", placeholder="e.g. Junior Data Analyst", label_visibility="collapsed")
    job_description = st.text_area("Paste the job description", height=290, placeholder="Include the responsibilities and qualifications so the review can compare evidence against the full role.")

with right:
    st.markdown("<div class='step-label'><span class='step-count'>03</span><span>Review scope</span></div>", unsafe_allow_html=True)
    st.markdown("### A closer read")
    if api_key.strip():
        mode_class = "ai"
        mode_name = "AI-assisted review"
        mode_description = "Structured analysis uses OpenAI; your resume text is sent to that service."
    else:
        mode_class = "local"
        mode_name = "Local keyword review"
        mode_description = "Uses built-in skill matching and structure checks; it does not perform semantic AI analysis."
    st.markdown(f"<div class='mode-indicator {mode_class}'><span class='mode-eyebrow'>Current mode</span><strong>{mode_name}</strong><span class='mode-description'>{mode_description}</span></div>", unsafe_allow_html=True)
    st.markdown("<div class='scope-list'><div class='scope-row'><span class='scope-index'>01</span><span><span class='scope-name'>Evidence & alignment</span><span class='scope-detail'>Skills, role needs, and supporting proof</span></span></div><div class='scope-row'><span class='scope-index'>02</span><span><span class='scope-name'>Experience & projects</span><span class='scope-detail'>Bullet strength and relevant work</span></span></div><div class='scope-row'><span class='scope-index'>03</span><span><span class='scope-name'>Structure & preparation</span><span class='scope-detail'>Readability, next edits, and questions</span></span></div></div>", unsafe_allow_html=True)
    st.markdown("<div class='note'>Suggestions are advisory. Keep every edit accurate to your experience; the reviewer will not invent credentials, outcomes, or metrics.</div>", unsafe_allow_html=True)
    run_review = st.button("Review resume", type="primary", use_container_width=True)

if run_review:
    if uploaded is None:
        st.error("Upload your resume to continue.")
    elif not job_description.strip():
        st.error("Paste the target job description to continue.")
    else:
        try:
            resume_text = extract_resume_text(uploaded.name, uploaded.getvalue())
            resume_sections = extract_resume_sections(resume_text)
            with st.spinner("Comparing resume evidence with the role..."):
                report, mode = review_resume(resume_text, job_description, target_role, api_key, model)
            st.session_state["review_report"] = report
            st.session_state["resume_sections"] = resume_sections
            st.session_state["review_role"] = target_role
            st.session_state["review_mode"] = mode
        except Exception as exc:
            st.error(f"Review could not be completed: {exc}")

if "review_report" in st.session_state:
    report = st.session_state["review_report"]
    st.divider()
    st.caption(f"{st.session_state['review_mode']} · Advisory feedback, not an ATS score or hiring prediction")
    st.subheader("Target-role alignment")
    st.write(report.role_alignment)

    tabs = st.tabs(["Resume sections", "Evidence & gaps", "Experience & projects", "Structure & next steps", "Interview prep"])
    with tabs[0]:
        st.markdown("#### Extracted resume sections")
        for section, content in st.session_state["resume_sections"].items():
            with st.expander(section, expanded=section in {"Summary", "Experience", "Skills"}):
                st.text(content)
    with tabs[1]:
        st.markdown("#### Requirement-to-evidence map")
        if report.requirement_mapping:
            st.dataframe(
                [
                    {
                        "Requirement": item.requirement,
                        "Priority": item.priority,
                        "Match": item.status,
                        "Resume evidence": item.resume_evidence,
                    }
                    for item in report.requirement_mapping
                ],
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.write("No recognized requirements were available to map.")
        a, b = st.columns(2, gap="large")
        with a:
            st.markdown("#### Supported skills")
            if report.supported_skills:
                for item in report.supported_skills:
                    with st.expander(item.skill):
                        st.write(item.evidence)
            else:
                st.write("No supported skills listed.")
        with b:
            st.markdown("#### Missing or weak evidence")
            if report.gaps:
                for item in report.gaps:
                    with st.expander(f"{item.requirement} · {item.priority}"):
                        st.write(item.explanation)
            else:
                st.write("No gaps listed.")
        with st.expander("Keyword comparison", expanded=False):
            if report.keyword_matches:
                st.dataframe([item.model_dump() for item in report.keyword_matches], hide_index=True, use_container_width=True)
            else:
                st.write("No keyword matches to show.")

    with tabs[2]:
        st.markdown("#### Experience bullet quality")
        if report.experience_bullets:
            for item in report.experience_bullets:
                with st.expander(item.original[:100]):
                    st.write(item.observation)
                    st.markdown("**Possible rewrite**")
                    st.write(item.suggested_rewrite)
        else:
            st.write("No specific bullet feedback was returned.")
        st.markdown("#### Project relevance")
        for item in report.project_relevance or ["No project notes returned."]:
            st.markdown(f"- {item}")

    with tabs[3]:
        st.markdown("#### Readability and structure")
        for item in report.readability_issues or ["No structure notes returned."]:
            st.markdown(f"- {item}")
        st.markdown("#### Suggested next edits")
        for index, item in enumerate(report.recommended_edits, 1):
            st.markdown(f"**{index}. {item.section}**  \n{item.change}  \n_{item.rationale}_")

    with tabs[4]:
        st.markdown("#### Questions to prepare")
        for item in report.interview_questions or ["No interview questions returned."]:
            st.markdown(f"- {item}")

    markdown_report = report_to_markdown(report, st.session_state["review_role"])
    st.download_button("Download review report", data=markdown_report, file_name="resume-review.md", mime="text/markdown")