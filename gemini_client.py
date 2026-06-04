"""Gemini API wrapper: prompt builder and tailored CV generation."""

import google.generativeai as genai

from config import GEMINI_MODEL

_model = None


def configure(api_key: str) -> None:
    genai.configure(api_key=api_key)
    global _model
    _model = genai.GenerativeModel(GEMINI_MODEL)


def is_configured() -> bool:
    return _model is not None


def validate_api_key(api_key: str) -> bool:
    try:
        genai.configure(api_key=api_key)
        next(iter(genai.list_models()))
        return True
    except Exception:
        return False


def build_prompt(cv_text: str, job_description: str) -> str:
    return f"""SYSTEM:
You are a professional CV writer. You must only use information already present in the
provided CV. Do not invent, add, or imply any skills, roles, tools, or achievements
that are not explicitly stated in the CV.

CV:
{cv_text}

JOB DESCRIPTION:
{job_description}

TASK:
Rewrite the CV above to best match the job description. Follow these rules:
- Prioritize and lead with experience most relevant to the job.
- Use keywords from the job description naturally where they match existing experience.
- Reorder and rephrase bullet points to highlight the most relevant work first.
- Keep all original sections: Summary, Experience, Skills, Education (and any others present).
- Do not add any experience, skills, or tools not present in the original CV.
- Return the result as plain text with clear ALL-CAPS section headers.
- Do not include any commentary, preamble, or explanation — output only the CV."""


def generate_tailored_cv(cv_text: str, job_description: str) -> str:
    if _model is None:
        raise RuntimeError("Gemini API key not configured. Call configure() first.")
    prompt = build_prompt(cv_text, job_description)
    response = _model.generate_content(prompt)
    return response.text


if __name__ == "__main__":
    from dotenv import load_dotenv

    import env_store

    load_dotenv(override=True)
    configure(env_store.get_api_key())
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
