"""Generate a realistic sample CV PDF for the showcase."""

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

LINES = [
    ("Helvetica-Bold", 16, "ALEX MORGAN"),
    ("Helvetica", 10, "alex.morgan@email.com  |  +1 (555) 482-1190  |  Boston, MA"),
    ("", 0, ""),
    ("Helvetica-Bold", 12, "SUMMARY"),
    ("Helvetica", 10, "Software engineer with 7 years building web applications and"),
    ("Helvetica", 10, "internal tools. Comfortable across the stack but strongest on"),
    ("Helvetica", 10, "the backend. Has shipped products in Java, Python, and Node.js."),
    ("", 0, ""),
    ("Helvetica-Bold", 12, "EXPERIENCE"),
    ("Helvetica-Bold", 10, "Software Engineer — Northwind Retail (2019-2024)"),
    ("Helvetica", 10, "- Maintained a Java/Spring order-management monolith."),
    ("Helvetica", 10, "- Built internal reporting dashboards in React."),
    ("Helvetica", 10, "- Wrote Python scripts to reconcile inventory data nightly."),
    ("Helvetica", 10, "- Mentored two junior engineers on code review practices."),
    ("Helvetica-Bold", 10, "Junior Developer — Bluefin Software (2017-2019)"),
    ("Helvetica", 10, "- Implemented REST endpoints in Node.js and Express."),
    ("Helvetica", 10, "- Fixed bugs and added tests to a legacy PHP codebase."),
    ("", 0, ""),
    ("Helvetica-Bold", 12, "SKILLS"),
    ("Helvetica", 10, "Java, Spring, Python, JavaScript, Node.js, React, SQL, Git, Docker"),
    ("", 0, ""),
    ("Helvetica-Bold", 12, "EDUCATION"),
    ("Helvetica", 10, "BSc Computer Science — Northeastern University (2013-2017)"),
]


def main():
    c = canvas.Canvas("sample_cv.pdf", pagesize=A4)
    y = 790
    for font, size, text in LINES:
        if not text:
            y -= 10
            continue
        c.setFont(font, size)
        c.drawString(56, y, text)
        y -= size + 6
    c.showPage()
    c.save()
    print("Wrote showcase/sample_cv.pdf")


if __name__ == "__main__":
    main()
