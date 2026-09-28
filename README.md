# Resume Review Studio

A Streamlit workflow for comparing a PDF, DOCX, or TXT resume with a target job description. It extracts resume text, checks role-specific evidence, and produces a structured, downloadable Markdown report.

## Run locally

```powershell
cd AI-Resume-Reviewer
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

OpenAI analysis is optional. Add `OPENAI_API_KEY` to the environment or enter a key in the app's settings panel. Without a key, the app uses a local keyword and structure review; this is intentionally more limited and does not assess semantic fit as deeply as the AI-assisted mode. In AI-assisted mode, the supplied resume and job description are sent to OpenAI for analysis.

## Report contents

Target-role alignment, skills supported by resume evidence, missing or weak requirements, a must-have/preferred requirement-to-evidence map, keyword comparison, experience-bullet feedback, project relevance, readability notes, interview-preparation questions, and prioritized next edits. The report uses a Pydantic schema in both analysis modes and is advisory; it does not claim to calculate an ATS score or predict an interview or hiring outcome.

## Verify

```powershell
python -m unittest -v
```