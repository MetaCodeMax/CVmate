"""Render tailored CV plain text to a clean professional PDF."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

_MARGIN = 2 * cm
_HEADER_FONT = ("Helvetica-Bold", 11)
_BODY_FONT = ("Helvetica", 10)
_BODY_LEADING = 14
_HEADER_SPACE_ABOVE = 2
_BLANK_SPACER = 4


def _is_header(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    letters = [c for c in stripped if c.isalpha()]
    return bool(letters) and all(c.isupper() for c in letters)


def _wrap(c, text, font_name, font_size, max_width):
    words = text.split()
    if not words:
        return [""]
    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if c.stringWidth(candidate, font_name, font_size) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def export_pdf(cv_text: str, output_path: str) -> None:
    try:
        c = canvas.Canvas(output_path, pagesize=A4)
        page_width, page_height = A4
        content_width = page_width - 2 * _MARGIN
        top = page_height - _MARGIN
        bottom = _MARGIN
        y = top

        def new_page_if_needed(needed):
            nonlocal y
            if y - needed < bottom:
                c.showPage()
                y = top

        for raw_line in cv_text.splitlines():
            line = raw_line.rstrip()

            if not line.strip():
                y -= _BLANK_SPACER
                continue

            if _is_header(line):
                y -= _HEADER_SPACE_ABOVE
                new_page_if_needed(_HEADER_FONT[1] + 6)
                c.setFont(*_HEADER_FONT)
                c.drawString(_MARGIN, y, line.strip())
                y -= _HEADER_FONT[1] + 2
                c.setLineWidth(1)
                c.line(_MARGIN, y, _MARGIN + content_width, y)
                y -= 6
            else:
                for wrapped in _wrap(c, line, _BODY_FONT[0], _BODY_FONT[1], content_width):
                    new_page_if_needed(_BODY_LEADING)
                    c.setFont(*_BODY_FONT)
                    c.drawString(_MARGIN, y, wrapped)
                    y -= _BODY_LEADING

        c.save()
    except (OSError, IOError) as e:
        raise IOError(f"Could not write PDF to {output_path}: {e}")


if __name__ == "__main__":
    sample = (
        "JANE DOE\n"
        "jane.doe@email.com | +1 555 0100\n"
        "\n"
        "SUMMARY\n"
        "Backend engineer with 6 years building Python services and scalable APIs.\n"
        "\n"
        "EXPERIENCE\n"
        "Senior Engineer, Acme Corp (2020-2024)\n"
        "- Built REST APIs in Python and FastAPI serving 2M requests per day.\n"
        "- Led migration from a monolith to microservices on AWS.\n"
        "\n"
        "SKILLS\n"
        "Python, FastAPI, AWS, PostgreSQL, Docker, Airflow, Git\n"
    )
    export_pdf(sample, "test_output.pdf")
    print("Exported to test_output.pdf")
