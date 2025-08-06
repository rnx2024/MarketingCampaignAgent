import os
from io import BytesIO
import uuid
import requests
import streamlit as st
from fpdf import FPDF

# --------------------------------------------------------------------
# Config
# --------------------------------------------------------------------
st.set_page_config(page_title="Marketing Agent", layout="centered", page_icon="📣")
API_BASE = "https://marketing-agent-latest.onrender.com"  # change if needed
TIMEOUT = 90

# --------------------------------------------------------------------
# Styles
# --------------------------------------------------------------------
st.markdown("""
<style>
  .stApp { background: linear-gradient(120deg, #f8fbff, #e4ecf7); }
  div[data-testid="stForm"] {
    background-color: #fff; border-radius: 12px; padding: 24px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.1);
  }
  .box {
    background:#fff; border:1px solid #d9e2ec; border-radius:10px;
    padding:16px; height:480px; overflow-y:auto; white-space:pre-wrap;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    font-size:14px;
  }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style='display:flex;align-items:center;gap:10px;'>
  <img src='https://cdn-icons-png.flaticon.com/512/10616/10616845.png' width='36' />
  <h1 style='margin:0;'>Marketing Agent</h1>
</div>
""", unsafe_allow_html=True)
st.caption("Frontend for your FastAPI Marketing Agent")

# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------
def call_api(path: str, payload: dict):
    url = f"{API_BASE}{path}"
    try:
        resp = requests.post(url, json=payload, timeout=TIMEOUT)
        content_type = resp.headers.get("content-type", "")
        data = resp.json() if "application/json" in content_type else {"raw": resp.text}
        return resp.ok, data, resp.status_code
    except requests.RequestException as e:
        return False, {"error": str(e)}, 0

def generate_pdf(text: str) -> BytesIO:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Marketing Output", ln=True)
    pdf.ln(6)
    pdf.set_font("Arial", "", 12)
    safe_text = text.encode("latin-1", errors="replace").decode("latin-1")
    for line in safe_text.splitlines():
        pdf.multi_cell(0, 7, line)
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    return BytesIO(pdf_bytes)

def parse_multiline(value: str):
    return [v.strip() for v in value.splitlines() if v.strip()] if value else None

def flatten_posts(posts: dict) -> str:
    if "raw" in posts:
        x = posts["raw"]
        return x[0] if isinstance(x, list) else str(x)
    out = []
    for platform, lines in posts.items():
        out.append(f"=== {platform} ===")
        for ln in lines:
            out.append(ln)
        out.append("")
    return "\n".join(out)

# --------------------------------------------------------------------
# UI
# --------------------------------------------------------------------
ACTION = st.selectbox(
    "Select Action",
    ["Campaign Plan", "Social Posts", "TikTok Script"],
    index=0
)

with st.form("main_form", clear_on_submit=False):
    # --- Common brand/product/brief fields (BaseBrief) ---
    col1, col2 = st.columns(2)
    with col1:
        brand = st.text_input("Brand", placeholder="Acme Inc.")
        brand_overview = st.text_area("Brand Overview", placeholder="Short mission or brand context...", height=80)
        product = st.text_input("Product/Service", placeholder="Reusable Water Bottle")
        product_pricing = st.text_input("Pricing/Tiers", placeholder="$25 or Starter/Growth/Enterprise")
    with col2:
        product_features = st.text_area("Key Features (one per line)", height=120)
        persona = st.text_input("Persona", placeholder="Environmentally conscious millennials and Gen Z")
        location = st.text_input("Location", placeholder="USA")
        tone = st.text_input("Tone", placeholder="Inspiring")

    brief = st.text_area("Brief (required)", height=100, placeholder="Back-to-school and work-mode promotion up to 20% off.")
    cta = st.text_input("CTA", placeholder="Shop now")
    constraints = st.text_area("Constraints (one per line)", placeholder="No overclaiming\nNo over-promising", height=80)
    notes = st.text_area("Extra Notes", placeholder="Leverage eco communities and school season timing", height=80)

    # --- Endpoint-specific fields ---
    if ACTION == "Campaign Plan":
        colA, colB = st.columns(2)
        with colA:
            channels = st.multiselect("Channels", ["TikTok", "Facebook", "Instagram", "Twitter", "LinkedIn"])
            budget = st.text_input("Budget", placeholder="$5000")
        with colB:
            duration = st.text_input("Duration", placeholder="2 weeks")

    elif ACTION == "Social Posts":
        colA, colB = st.columns(2)
        with colA:
            platforms = st.multiselect(
                "Platforms",
                ["Facebook", "Instagram", "Twitter", "LinkedIn", "TikTok"],
                default=["Instagram", "TikTok"]
            )
            posts_per_platform = st.number_input("Posts per platform", min_value=1, max_value=10, value=3, step=1)
        with colB:
            include_hashtags = st.checkbox("Include hashtags", value=True)
            include_emojis = st.checkbox("Include emojis", value=False)
            length = st.selectbox("Length", ["short", "medium", "long"], index=0)

    else:  # TikTok Script
        colA, colB = st.columns(2)
        with colA:
            duration_seconds = st.number_input("Duration (seconds)", min_value=10, max_value=90, value=30, step=5)
            hook_style = st.selectbox("Hook style", ["problem", "surprise", "stat", "benefit"], index=3)
        with colB:
            include_shot_list = st.checkbox("Include shot list", value=True)
            include_captions = st.checkbox("Include captions", value=True)
            include_voiceover = st.checkbox("Include voiceover", value=True)

    submitted = st.form_submit_button("Generate")

# --------------------------------------------------------------------
# Submit
# --------------------------------------------------------------------
if submitted:
    # Build BaseBrief payload
    base = {
        "brand": brand.strip(),
        "brand_overview": (brand_overview.strip() or None),
        "product": product.strip(),
        "product_features": parse_multiline(product_features),
        "product_pricing": (product_pricing.strip() or None),
        "brief": brief.strip(),
        "persona": (persona.strip() or None),
        "location": (location.strip() or None),
        "tone": (tone.strip() or None),
        "goal": None,  # optional in your model
        "cta": (cta.strip() or None),
        "constraints": parse_multiline(constraints),
        "notes": (notes.strip() or None),
    }

    # Basic validation (to avoid FastAPI 422)
    if not base["brief"]:
        st.error("Brief is required.")
        st.stop()
    if not base["brand"] or not base["product"]:
        st.error("Brand and Product are required.")
        st.stop()

    if ACTION == "Campaign Plan":
        payload = dict(base)
        payload["channels"] = channels or None
        payload["budget"] = budget or None
        payload["duration"] = duration or None
        ok, data, code = call_api("/marketing/campaign", payload)
        if not ok:
            st.error({"status": code, "detail": data})
        else:
            plan = data.get("plan", "")
            execution = data.get("execution", "")
            review = data.get("review", "")
            full_text = "PLAN\n\n" + plan + "\n\nEXECUTION\n\n" + execution + "\n\nREVIEW\n\n" + review
            st.markdown("#### Result")
            st.markdown(f"<div class='box'>{full_text}</div>", unsafe_allow_html=True)
            pdf = generate_pdf(full_text)
            st.download_button(
                label="Download as PDF",
                data=pdf,
                file_name=f"campaign_{uuid.uuid4().hex[:6]}.pdf",
                mime="application/pdf"
            )

    elif ACTION == "Social Posts":
        payload = dict(base)
        payload.update({
            "platforms": platforms,
            "posts_per_platform": int(posts_per_platform),
            "include_hashtags": bool(include_hashtags),
            "include_emojis": bool(include_emojis),
            "length": length
        })
        ok, data, code = call_api("/marketing/social-posts", payload)
        if not ok:
            st.error({"status": code, "detail": data})
        else:
            posts = data.get("posts", {})
            text = flatten_posts(posts)
            st.markdown("#### Result")
            st.markdown(f"<div class='box'>{text}</div>", unsafe_allow_html=True)
            pdf = generate_pdf(text)
            st.download_button(
                label="Download as PDF",
                data=pdf,
                file_name=f"social_posts_{uuid.uuid4().hex[:6]}.pdf",
                mime="application/pdf"
            )

    else:  # TikTok Script
        payload = dict(base)
        payload.update({
            "duration_seconds": int(duration_seconds),
            "hook_style": hook_style,
            "include_shot_list": bool(include_shot_list),
            "include_captions": bool(include_captions),
            "include_voiceover": bool(include_voiceover),
        })
        ok, data, code = call_api("/marketing/tiktok-script", payload)
        if not ok:
            st.error({"status": code, "detail": data})
        else:
            parts = []
            sb = data.get("storyboard") or []
            if sb:
                parts.append("STORYBOARD\n" + "\n".join(sb))
            if data.get("voiceover"):
                parts.append("VOICEOVER\n" + data["voiceover"])
            caps = data.get("captions") or []
            if caps:
                parts.append("CAPTIONS\n" + "\n".join(caps))
            if data.get("posting_notes"):
                parts.append("POSTING NOTES\n" + data["posting_notes"])
            text = "\n\n".join(parts) if parts else str(data)
            st.markdown("#### Result")
            st.markdown(f"<div class='box'>{text}</div>", unsafe_allow_html=True)
            pdf = generate_pdf(text)
            st.download_button(
                label="Download as PDF",
                data=pdf,
                file_name=f"tiktok_{uuid.uuid4().hex[:6]}.pdf",
                mime="application/pdf"
            )
