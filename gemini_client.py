"""Gemini API wrapper: prompt builder and tailored CV generation.

The key is supplied at runtime via configure() — the GUI resolves it from
%APPDATA% or its first-run dialog — so importing this module never fails for a
missing key.
"""

import google.generativeai as genai

from config import GEMINI_MODEL

_model = None


def configure(api_key: str) -> None:
    """Point the client at the given API key. Call once before generating."""
    genai.configure(api_key=api_key)
    global _model
    _model = genai.GenerativeModel(GEMINI_MODEL)


def is_configured() -> bool:
    return _model is not None


def validate_api_key(api_key: str) -> bool:
    """Return True if the key authenticates against the Gemini API.

    Used by the first-run dialog to give immediate feedback. Lists models,
    a lightweight authenticated call that does not consume generation quota.
    """
    try:
        genai.configure(api_key=api_key)
        next(iter(genai.list_models()))
        return True
    except Exception:
        return False


def build_prompt(cv_text: str, job_description: str) -> str:
    return f"""You are an expert resume writer and ATS (Applicant Tracking System) optimization
specialist. Rewrite the candidate's CV so it is the strongest possible match for ONE specific
job — maximizing relevance, keyword alignment, and impact — while staying strictly truthful.

TRUTHFULNESS RULES (non-negotiable):
- Use ONLY facts present in the original CV: employers, job titles, dates, education, and the
  candidate's real responsibilities and achievements.
- You MAY rephrase, reframe, reorder, merge, and emphasize existing content, and you may adopt
  the job description's terminology to describe experience the candidate genuinely has.
- You MUST NOT invent or imply any skill, tool, employer, title, date, certification, or metric
  that is not in the original CV. Never add numbers or results that were not stated.

STEP 1 — Analyze the job (silently, do not output this):
Identify the target job title, the must-have hard skills and tools, and the recurring keywords
and phrases the employer uses.

STEP 2 — Rewrite the CV applying ALL of these:
1. Keep the candidate's name and contact details at the very top, unchanged.
2. SUMMARY: Write a sharp 2-3 sentence professional summary positioning the candidate for THIS
   exact role and title, leading with the most relevant matching strengths and using the
   employer's language.
3. EXPERIENCE: Keep every employer, title, and date exactly as written. Within each role,
   reorder bullets so the most job-relevant work comes first, and rewrite each bullet to
   (a) open with a strong action verb, (b) mirror the job's terminology where the candidate
   truly did that work, and (c) preserve any real metrics. Down-rank or remove bullets
   irrelevant to this job.
4. SKILLS: Reorder so skills named in the job description appear first; keep all real skills.
5. Keep all other original sections (Education, Certifications, Languages, etc.), reordered only
   for relevance.

KEYWORD EMPHASIS:
Wrap in double asterisks every phrase that is BOTH part of the candidate's real experience AND a
key requirement from the job, like **FastAPI** or **REST APIs**. Bold only genuine matches — do
not bold everything, and never bold a keyword the candidate does not actually have.

OUTPUT FORMAT:
- Plain text only. Section titles in ALL CAPS on their own line (SUMMARY, EXPERIENCE, SKILLS...).
- Bullet lines start with "- ".
- Use **double asterisks** only for the matched-keyword emphasis described above.
- Output ONLY the finished CV — no preamble, no commentary, no explanation.

CV:
{cv_text}

JOB DESCRIPTION:
{job_description}"""


def generate_tailored_cv(cv_text: str, job_description: str) -> str:
    if _model is None:
        raise RuntimeError("Gemini API key not configured. Call configure() first.")
    prompt = build_prompt(cv_text, job_description)
    response = _model.generate_content(prompt)
    return response.text


if __name__ == "__main__":
    from dotenv import load_dotenv

    import key_store

    load_dotenv(override=True)
    _key = key_store.get_api_key()
    if not _key:
        raise SystemExit("No API key found. Set GEMINI_API_KEY or run the app once.")
    configure(_key)

    sample_cv = (
        "JANE DOE\n"
        "SUMMARY\nBackend engineer with 6 years of Python experience.\n"
        "EXPERIENCE\nSenior Engineer at Acme: built REST APIs in Python and FastAPI.\n"
        "SKILLS\nPython, FastAPI, AWS, PostgreSQL, Docker\n"
        "EDUCATION\nBSc Computer Science, State University\n"
    )
    sample_jd = (
        "Seeking a senior Python backend developer experienced with FastAPI, "
        "cloud platforms (AWS), and containerization (Docker) to build scalable APIs."
    )
    result = generate_tailored_cv(sample_cv, sample_jd)
    print(result[:500])
