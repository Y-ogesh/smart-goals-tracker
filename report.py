# report.py — PDF builder

from io import BytesIO
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def _wrap(text, width=90):
    import textwrap
    return textwrap.wrap(text or "", width)

def build_pdf(goal_title: str, streak: int, steps, summary_text: str | None):
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    w, h = LETTER
    y = h - 72

    def line(txt, indent=0, leading=14):
        nonlocal y
        for ln in _wrap(txt, 95 - indent//5):
            c.drawString(72 + indent, y, ln)
            y -= leading

    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, y, f"Progress Report — {goal_title}")
    y -= 24
    c.setFont("Helvetica", 11)
    line(f"Current streak: {streak} day(s)")
    y -= 10

    c.setFont("Helvetica-Bold", 13); line("Plan")
    c.setFont("Helvetica", 11)
    for s in steps:
        line(f"• {s.get('title','')}")
        if s.get("detail"):
            line(f"   How: {s['detail']}", indent=12)
        if s.get("metric"):
            line(f"   Metric: {s['metric']}", indent=12)
        if s.get("duration_min"):
            line(f"   Duration: {s['duration_min']} min", indent=12)
        if s.get("why"):
            line(f"   Why: {s['why']}", indent=12)
        if s.get("due_date"):
            line(f"   Due: {s['due_date']}", indent=12)
        y -= 6
        if y < 120:
            c.showPage(); y = h - 72; c.setFont("Helvetica", 11)

    y -= 6
    c.setFont("Helvetica-Bold", 13); line("Weekly Summary")
    c.setFont("Helvetica", 11)
    line(summary_text or "No summary yet.")
    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()
