"""Render tailored CV plain text to a clean professional PDF."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

_MARGIN = 2 * cm
_HEADER_FONT = ("Helvetica-Bold", 11)
_BODY_FONT = ("Helvetica", 10)
_BODY_BOLD_FONT = ("Helvetica-Bold", 10)
_BODY_LEADING = 14
_HEADER_SPACE_ABOVE = 10
_HEADER_RULE_GAP = 5
_HEADER_BODY_GAP = 13
_BLANK_SPACER = 4


def _is_header(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    letters = [c for c in stripped if c.isalpha()]
    return bool(letters) and all(c.isupper() for c in letters)


def _strip_marks(text: str) -> str:
    return text.replace("**", "")


def _styled_words(text: str):
    """Split a line into words; each word is a list of (substring, is_bold) runs.

    Bold spans are wrapped in **...**. Punctuation that abuts a bold span stays glued
    to it (no stray space) because splitting happens at real whitespace, not at marks.
    """
    styled_chars = []
    for i, segment in enumerate(text.split("**")):
        is_bold = i % 2 == 1
        for ch in segment:
            styled_chars.append((ch, is_bold))

    words = []
    current = []
    for ch, is_bold in styled_chars:
        if ch.isspace():
            if current:
                words.append(_group_runs(current))
                current = []
        else:
            current.append((ch, is_bold))
    if current:
        words.append(_group_runs(current))
    return words


def _group_runs(chars):
    runs = []
    for ch, is_bold in chars:
        if runs and runs[-1][1] == is_bold:
            runs[-1] = (runs[-1][0] + ch, is_bold)
        else:
            runs.append((ch, is_bold))
    return runs


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

        def draw_body(text):
            nonlocal y
            name, size = _BODY_FONT
            bold_name = _BODY_BOLD_FONT[0]
            space_w = c.stringWidth(" ", name, size)

            def font_of(is_bold):
                return bold_name if is_bold else name

            def word_width(runs):
                return sum(c.stringWidth(t, font_of(b), size) for t, b in runs)

            words = _styled_words(text)
            if not words:
                return
            line = []
            line_w = 0

            def flush():
                nonlocal y, line, line_w
                new_page_if_needed(_BODY_LEADING)
                x = _MARGIN
                for j, (runs, w) in enumerate(line):
                    if j:
                        x += space_w
                    for t, b in runs:
                        c.setFont(font_of(b), size)
                        c.drawString(x, y, t)
                        x += c.stringWidth(t, font_of(b), size)
                y -= _BODY_LEADING
                line = []
                line_w = 0

            for runs in words:
                w = word_width(runs)
                add = w if not line else space_w + w
                if line and line_w + add > content_width:
                    flush()
                    add = w
                line.append((runs, w))
                line_w += add
            if line:
                flush()

        for raw_line in cv_text.splitlines():
            line = raw_line.rstrip()

            if not line.strip():
                y -= _BLANK_SPACER
                continue

            if _is_header(line):
                y -= _HEADER_SPACE_ABOVE
                new_page_if_needed(_HEADER_FONT[1] + _HEADER_RULE_GAP + _HEADER_BODY_GAP)
                c.setFont(*_HEADER_FONT)
                c.drawString(_MARGIN, y, _strip_marks(line.strip()))
                y -= _HEADER_RULE_GAP
                c.setLineWidth(0.75)
                c.line(_MARGIN, y, _MARGIN + content_width, y)
                y -= _HEADER_BODY_GAP
            else:
                draw_body(line)

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
