"""CV PDF text extraction and section segmentation."""

import re

import pdfplumber

SECTION_KEYWORDS = [
    "summary",
    "objective",
    "experience",
    "education",
    "skills",
    "projects",
    "certifications",
    "languages",
]


def extract_text(pdf_path: str) -> str:
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            pages.append(page_text)

    text = "\n".join(pages)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    if len(text) < 50:
        raise ValueError(
            "Could not extract text from this PDF. Try a text-based PDF."
        )

    return text


def _is_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False

    letters = [c for c in stripped if c.isalpha()]
    if letters and all(c.isupper() for c in letters) and len(stripped) <= 60:
        return True

    normalized = stripped.lower().strip(":").strip()
    return normalized in SECTION_KEYWORDS


def segment_sections(text: str) -> dict[str, str]:
    lines = text.splitlines()
    sections: dict[str, list[str]] = {}
    current = None

    for line in lines:
        if _is_heading(line):
            current = line.strip().rstrip(":").upper()
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(line)

    result = {
        key: "\n".join(body).strip()
        for key, body in sections.items()
        if "\n".join(body).strip()
    }

    if not result:
        return {"FULL_TEXT": text}

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python cv_parser.py path/to/cv.pdf")
        sys.exit(1)

    cv_text = extract_text(sys.argv[1])
    print(f"Extracted {len(cv_text)} characters.")
    print(f"Detected sections: {list(segment_sections(cv_text).keys())}")
