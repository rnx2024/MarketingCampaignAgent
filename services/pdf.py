# services/pdf.py
from io import BytesIO
from datetime import datetime
from typing import Optional, Dict

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

def _p(text: str, style_name: str, styles):
    # Normalize newlines, escape, then allow <br/> for line breaks
    safe = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    safe = safe.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe = safe.replace("\n", "<br/>")
    return Paragraph(safe, styles[style_name])

def build_campaign_pdf(
    *,
    company_name: str,
    meta: Dict[str, Optional[str]],
    brand_context: str,
    past_insights: str,
    plan: str,
) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title=f"Campaign Plan - {company_name}",
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="H1", parent=styles["Heading1"], spaceAfter=8))
    styles.add(ParagraphStyle(name="H2", parent=styles["Heading2"], spaceBefore=8, spaceAfter=6))
    styles.add(ParagraphStyle(name="Body", parent=styles["BodyText"], leading=14))

    flow = []
    flow.append(_p("Campaign Plan", "H1", styles))
    when = datetime.now().strftime("%Y-%m-%d %H:%M")
    flow.append(_p(f"Company: {company_name}", "Body", styles))
    flow.append(_p(
        " | ".join([
            f"Product: {meta.get('product') or '—'}",
            f"Type: {meta.get('campaign_type') or '—'}",
            f"Channel: {meta.get('channel') or '—'}",
            f"Output: {meta.get('output_type') or '—'}",
            f"Duration: {meta.get('duration') or '—'}",
            f"Budget: {meta.get('budget') or '—'}",
            f"Generated: {when}",
        ]),
        "Body", styles,
    ))
    flow.append(Spacer(1, 0.6 * cm))

    flow.append(_p("Brand Context", "H2", styles))
    flow.append(_p(brand_context, "Body", styles))
    flow.append(Spacer(1, 0.4 * cm))

    flow.append(_p("Past Insights", "H2", styles))
    flow.append(_p(past_insights, "Body", styles))
    flow.append(Spacer(1, 0.4 * cm))

    flow.append(_p("Plan", "H2", styles))
    flow.append(_p(plan, "Body", styles))

    doc.build(flow)
    return buf.getvalue()
