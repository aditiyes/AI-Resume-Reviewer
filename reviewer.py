"""Resume extraction and structured role-alignment review."""

from __future__ import annotations

import json
import re
from io import BytesIO
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, ValidationError


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Evidence(StrictModel):
    skill: str
    evidence: str


class Gap(StrictModel):
    requirement: str
    priority: str
    explanation: str


class KeywordMatch(StrictModel):
    keyword: str
    status: str
    evidence: str


class RequirementMapping(StrictModel):
    requirement: str
    priority: Literal["Must-have", "Preferred", "Unspecified"]
    status: Literal["Evidence found", "Mention only", "Not found"]
    resume_evidence: str


class BulletFeedback(StrictModel):
    original: str
    observation: str
    suggested_rewrite: str


class RecommendedEdit(StrictModel):
    section: str
    change: str
    rationale: str


class ReviewReport(StrictModel):
    role_alignment: str
    supported_skills: list[Evidence]
    gaps: list[Gap]
    keyword_matches: list[KeywordMatch]
    requirement_mapping: list[RequirementMapping]
    experience_bullets: list[BulletFeedback]
    project_relevance: list[str]
    readability_issues: list[str]
    interview_questions: list[str]
    recommended_edits: list[RecommendedEdit]


SECTION_ALIASES = {
    "Summary": {"summary", "professional summary", "profile", "career summary", "objective", "about me"},
    "Experience": {"experience", "work experience", "professional experience", "employment", "employment history", "work history", "internships", "internship"},
    "Education": {"education", "educational background", "academic background"},
    "Skills": {"skills", "technical skills", "core skills", "key skills", "competencies", "technical competencies"},
    "Projects": {"projects", "personal projects", "academic projects", "selected projects"},
    "Certifications": {"certifications", "certificates", "licenses", "licenses and certifications"},
    "Awards": {"awards", "honors and awards", "achievements", "honors"},
}


SKILL_TERMS = (
    "python", "sql", "excel", "tableau", "power bi", "pandas", "numpy",
    "scikit-learn", "machine learning", "deep learning", "data analysis",
    "data visualization", "statistics", "etl", "data modeling", "spark",
    "aws", "azure", "gcp", "docker", "kubernetes", "git", "linux",
    "javascript", "typescript", "react", "node.js", "fastapi", "django",
    "flask", "rest api", "postgresql", "mysql", "mongodb", "html", "css",
    "project management", "agile", "scrum", "communication", "leadership",
    "stakeholder management", "problem solving", "forecasting", "r",
    "communication skills", "customer service", "salesforce", "financial analysis",
)


def extract_resume_text(filename: str, content: bytes) -> str:
    """Extract text from PDF, DOCX, or plain-text resume files."""
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if suffix == "pdf":
        from pypdf import PdfReader

        pages = PdfReader(BytesIO(content)).pages
        text = "\n".join(page.extract_text() or "" for page in pages)
    elif suffix == "docx":
        from docx import Document

        document = Document(BytesIO(content))
        paragraphs = [paragraph.text for paragraph in document.paragraphs]
        table_text = [cell.text for table in document.tables for row in table.rows for cell in row.cells]
        text = "\n".join(paragraphs + table_text)
    elif suffix == "txt":
        text = content.decode("utf-8-sig", errors="replace")
    else:
        raise ValueError("Upload a PDF, DOCX, or TXT resume.")

    text = re.sub(r"[ \t]+", " ", text).strip()
    if not text:
        raise ValueError("No text could be extracted. The file may be scanned; try an OCR-enabled PDF.")
    return text


def extract_resume_sections(resume: str) -> dict[str, str]:
    """Split extracted resume text at common section headings, preserving its content."""
    heading_lookup = {
        re.sub(r"[^a-z0-9 ]", "", alias.casefold()).strip(): label
        for label, aliases in SECTION_ALIASES.items()
        for alias in aliases
    }
    sections: dict[str, list[str]] = {}
    current = "Other"
    for line in resume.splitlines():
        normalized = re.sub(r"[^a-z0-9 ]", "", line.casefold()).strip()
        label = heading_lookup.get(normalized) if len(normalized) <= 50 else None
        if label:
            current = label
            sections.setdefault(current, [])
        elif line.strip():
            sections.setdefault(current, []).append(line.strip())
    return {label: "\n".join(lines).strip() for label, lines in sections.items() if lines and "\n".join(lines).strip()}


def extract_job_keywords(job_description: str) -> list[str]:
    normalized = job_description.casefold()
    return [term for term in SKILL_TERMS if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", normalized)]


def _requirement_priority(job_description: str, requirement: str) -> str:
    for line in re.split(r"[\n.;]+", job_description):
        if not re.search(rf"(?<!\w){re.escape(requirement)}(?!\w)", line, re.I):
            continue
        if re.search(r"\b(preferred|nice[- ]to[- ]have|bonus|desirable|a plus)\b", line, re.I):
            return "Preferred"
        if re.search(r"\b(required|must[- ]have|mandatory|must|required to|minimum)\b", line, re.I):
            return "Must-have"
    return "Unspecified"


def _local_review(resume: str, job_description: str, target_role: str) -> ReviewReport:
    resume_lower = resume.casefold()
    keywords = extract_job_keywords(job_description)
    matches = [term for term in keywords if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", resume_lower)]
    missing = [term for term in keywords if term not in matches]
    all_resume_lines = [line.strip(" •\t-") for line in resume.splitlines() if line.strip(" •\t-")]
    resume_lines = [line.strip(" •\t-") for line in resume.splitlines() if len(line.strip(" •\t-")) > 35]
    bullets = [line for line in resume_lines if re.search(r"\b(developed|built|led|created|analyzed|improved|managed|designed|implemented|increased|reduced)\b", line, re.I)]
    quantified = [line for line in bullets if re.search(r"\d+\s*%|\$\s?\d|\b\d+\s+(users|clients|customers|projects|hours|records)\b", line, re.I)]
    requirement_mapping = []
    for term in keywords:
        term_pattern = rf"(?<!\w){re.escape(term)}(?!\w)"
        contextual_evidence = next(
            (
                line
                for line in all_resume_lines
                if re.search(term_pattern, line, re.I)
                and len(line) > 35
                and re.search(r"\b(used|applied|built|created|analyzed|improved|managed|designed|implemented|led|developed|worked with)\b", line, re.I)
            ),
            None,
        )
        mentioned_evidence = next((line for line in all_resume_lines if re.search(term_pattern, line, re.I)), None)
        requirement_mapping.append(
            RequirementMapping(
                requirement=term,
                priority=_requirement_priority(job_description, term),
                status="Evidence found" if contextual_evidence else "Mention only" if mentioned_evidence else "Not found",
                resume_evidence=contextual_evidence or mentioned_evidence or "No direct mention found in the extracted resume text.",
            )
        )

    supported = [
        Evidence(skill=term, evidence=next((line for line in resume_lines if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", line, re.I)), f"Listed in resume: {term}"))
        for term in matches
    ]
    gaps = [
        Gap(requirement=term, priority="Review", explanation="This job-description term was not found in the resume text. Add it only if you have relevant experience.")
        for term in missing
    ]
    keyword_matches = [
        KeywordMatch(keyword=term, status="Found", evidence=next((line for line in resume_lines if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", line, re.I)), "Present in resume text."))
        for term in matches
    ] + [KeywordMatch(keyword=term, status="Not found", evidence="No direct mention found; verify whether equivalent experience is described.") for term in missing]

    feedback = [
        BulletFeedback(
            original=line,
            observation="No measurable result detected. Consider adding scale, outcome, or a concrete example if accurate.",
            suggested_rewrite=f"{line.rstrip('.')}; add a verified metric or outcome that shows the impact.",
        )
        for line in bullets[:4]
    ]
    if not bullets and resume_lines:
        feedback = [BulletFeedback(original=resume_lines[0], observation="This line may benefit from a clear action and outcome.", suggested_rewrite=f"Start with a specific action, then explain the result: {resume_lines[0]}")]

    edits = [RecommendedEdit(section="Experience", change="Add a verified result or scope to action-led bullets that currently describe responsibilities only.", rationale="Specific evidence makes the connection to role requirements easier to assess.")]
    if missing:
        edits.insert(0, RecommendedEdit(section="Skills and experience", change=f"Review the missing terms: {', '.join(missing[:8])}.", rationale="Include only skills supported by real experience, ideally with evidence in a project or work bullet."))
    if not quantified:
        edits.append(RecommendedEdit(section="Experience and projects", change="Look for truthful numbers that show scale, frequency, time saved, quality, or outcomes.", rationale="The extracted resume text contains no clear quantified outcomes."))

    readability_issues = []
    if len(resume) > 9000:
        readability_issues.append("The extracted resume is long; check that the most role-relevant evidence appears early.")
    if not re.search(r"\b(experience|employment|work history)\b", resume, re.I):
        readability_issues.append("A clearly labeled experience section was not detected in the extracted text.")
    if not re.search(r"\b(education|degree|university|college)\b", resume, re.I):
        readability_issues.append("An education section was not detected in the extracted text.")
    if not readability_issues:
        readability_issues.append("No obvious structure issue was detected by the local text check; review the original layout for spacing and consistency.")

    return ReviewReport(
        role_alignment=(f"Local text comparison found {len(matches)} of {len(keywords)} recognized job-description skill terms in the resume" if keywords else f"A local keyword comparison was completed for {target_role or 'the target role'}, but no terms from the reviewer's built-in skill list were recognized."),
        supported_skills=supported,
        gaps=gaps,
        keyword_matches=keyword_matches,
        requirement_mapping=requirement_mapping,
        experience_bullets=feedback,
        project_relevance=["Local mode cannot reliably judge project relevance. Compare each project with the role's main responsibilities and surface the closest match first."],
        readability_issues=readability_issues,
        interview_questions=[f"Which example best demonstrates your experience with {term}?" for term in matches[:3]] or ["Which project or experience is most relevant to this role, and what was your specific contribution?"],
        recommended_edits=edits,
    )


def review_resume(
    resume: str,
    job_description: str,
    target_role: str = "",
    api_key: str = "",
    model: str = "gpt-4o-mini",
) -> tuple[ReviewReport, str]:
    """Return a validated review and the analysis mode used."""
    if not resume.strip() or not job_description.strip():
        raise ValueError("Both resume text and job description are required.")
    if not api_key.strip():
        return _local_review(resume, job_description, target_role), "Local keyword review"

    from openai import OpenAI

    client = OpenAI(api_key=api_key.strip())
    schema: dict[str, Any] = ReviewReport.model_json_schema()
    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an advisory resume reviewer. Compare the resume with the target role and return only the requested structured report. "
                    "Map every important job requirement to direct resume evidence. Set priority to Must-have only when the job description explicitly requires it, Preferred when it marks it preferred/nice-to-have, otherwise Unspecified. "
                    "Set status to Evidence found for contextual experience, Mention only for a bare skills-list mention, or Not found when absent. Quote concise evidence from the resume and do not infer equivalence without saying so. "
                    "Distinguish missing evidence from missing skill, and never invent qualifications or metrics. "
                    "Rewrite suggestions must preserve the candidate's facts; use placeholders or ask for verified outcomes instead of fabricating them. "
                    "Do not claim to predict ATS scores, hiring outcomes, or interviews. Be concise and specific."
                ),
            },
            {
                "role": "user",
                "content": json.dumps({"target_role": target_role, "job_description": job_description[:12000], "resume_sections": extract_resume_sections(resume)}),
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "resume_review", "strict": True, "schema": schema},
        },
    )
    content = response.choices[0].message.content
    if not content:
        raise ValueError("The analysis service returned an empty report.")
    try:
        return ReviewReport.model_validate_json(content), f"AI-assisted review ({model})"
    except ValidationError as exc:
        raise ValueError("The analysis response did not match the required report structure.") from exc


def report_to_markdown(report: ReviewReport, target_role: str) -> str:
    sections = ["# Resume Review", f"**Target role:** {target_role or 'Not specified'}", "", "> Advisory feedback only. This review does not predict an ATS score, hiring decision, or interview outcome.", "", "## Target-role alignment", report.role_alignment]
    sections.extend(["", "## Skills supported by evidence"])
    sections.extend([f"- **{item.skill}:** {item.evidence}" for item in report.supported_skills] or ["- No supported skills identified."])
    sections.extend(["", "## Missing or weak evidence"])
    sections.extend([f"- **{item.requirement} ({item.priority}):** {item.explanation}" for item in report.gaps] or ["- No gaps listed."])
    sections.extend(["", "## Keyword comparison"])
    sections.extend([f"- **{item.keyword}** - {item.status}: {item.evidence}" for item in report.keyword_matches] or ["- No recognized keywords."])
    sections.extend(["", "## Requirement-to-evidence map", "| Requirement | Priority | Status | Resume evidence |", "| --- | --- | --- | --- |"])
    if report.requirement_mapping:
        sections.extend(
            "| {} | {} | {} | {} |".format(
                item.requirement.replace("|", "\\|"),
                item.priority,
                item.status,
                item.resume_evidence.replace("|", "\\|").replace("\n", " "),
            )
            for item in report.requirement_mapping
        )
    else:
        sections.append("No requirements could be mapped.")
    sections.extend(["", "## Experience bullets"])
    for item in report.experience_bullets:
        sections.extend([f"- Original: {item.original}", f"  - Observation: {item.observation}", f"  - Suggested rewrite: {item.suggested_rewrite}"])
    sections.extend(["", "## Project relevance"])
    sections.extend([f"- {item}" for item in report.project_relevance] or ["- No notes."])
    sections.extend(["", "## Readability and structure"])
    sections.extend([f"- {item}" for item in report.readability_issues] or ["- No issues listed."])
    sections.extend(["", "## Questions to prepare"])
    sections.extend([f"- {item}" for item in report.interview_questions] or ["- No questions listed."])
    sections.extend(["", "## Suggested next edits"])
    sections.extend([f"- **{item.section}:** {item.change} _{item.rationale}_" for item in report.recommended_edits] or ["- No edits listed."])
    return "\n".join(sections)