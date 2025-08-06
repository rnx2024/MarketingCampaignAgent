import requests
import streamlit as st
from io import BytesIO
from fpdf import FPDF

# -------------------------------------------------------
# Config
# -------------------------------------------------------
st.set_page_config(page_title="Marketing Agent", layout="centered", page_icon="📣")
API_BASE = "https://marketing-agent-latest.onrender.com"
TIMEOUT = 90

# -------------------------------------------------------
# Styles
# -------------------------------------------------------
st.markdown("""
<style>
  .stApp { background: linear-gradient(120deg, #f8fbff, #e4ecf7); }
  div[data-testid="stForm"] {
    background-color:#fff; border-radius:12px; padding:24px;
    box-shadow:0 4px 14px rgba(0,0,0,0.1);
  }
  .box {
    background:#fff; border:1px solid #d9e2ec; border-radius:10px;
    padding:16px; height:420px; overflow-y:auto; white-space:pre-wrap;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    font-size:14px;
  }
</style>
""", unsafe_allow_html=True)

st.markdown("<h2>Marketing Agent</h2>", unsafe_allow_html=True)
st.caption("Minimal UI → choose output type, paste a few lines, generate.")

# -------------------------------------------------------
# Helpers
# -------------------------------------------------------
def call_api(path: str, payload: dict):
    url = f"{API_BASE}{path}"
    resp = requests.post(url, json=payload, timeout=TIMEOUT)
    data = resp.json() if "application/json" in resp.headers.get("content-type", "") else {"raw": resp.text}
    return resp.ok, data, resp.status_code

def pdf_bytes(text: str) -> BytesIO:
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
    return BytesIO(pdf.output(dest="S").encode("latin-1"))

def parse_csv_box(value: str, expected: int):
    parts = [p.strip() for p in value.split(",") if p.strip()] if value else []
    if len(parts) != expected:
        return None, f"Expected {expected} comma-separated values, got {len(parts)}."
    return parts, None

# -------------------------------------------------------
# UI
# -------------------------------------------------------
action = st.selectbox("Output Type", ["Campaign Plan", "Social Posts", "TikTok Script"], index=0)

with st.form("minimal_form", clear_on_submit=False):
    st.markdown("#### Brand, Product, Price")
    brand_product_price = st.text_area(
        "Format: brand, product, price",
        placeholder="Acme Inc., Reusable Water Bottle, $25",
        height=60
    )

    st.markdown("#### Audience, Location, Duration, Budget")
    aud_loc_dur_budget = st.text_area(
        "Format: target audience, location, duration, campaign budget",
        placeholder="Environmentally conscious millennials and Gen Z, USA, 2 weeks, $5000",
        height=60
    )

    st.markdown("#### Tone & CTA")
    tone_choice = st.selectbox(
        "Tone",
        ["", "Playful", "Professional", "Bold", "Minimalist", "Inspiring", "Friendly"],
        index=0
    )
    cta_text = st.text_input("Call to Action (optional)", placeholder="Shop now")

    st.markdown("#### Extra Notes")
    extra_notes = st.text_area(
        "Any extra guidance, constraints, or context",
        placeholder="Back-to-school and work-mode promotion up to 20% off. No overclaiming or over-promising.",
        height=80
    )

    submitted = st.form_submit_button("Generate")

# -------------------------------------------------------
# Submit
# -------------------------------------------------------
if submitted:
    # Parse the two required boxes
    bpp, err1 = parse_csv_box(brand_product_price, expected=3)
    aldb, err2 = parse_csv_box(aud_loc_dur_budget, expected=4)

    if err1:
        st.error(f"Brand/Product/Price: {err1}")
        st.stop()
    if err2:
        st.error(f"Audience/Location/Duration/Budget: {err2}")
        st.stop()

    brand, product, price = bpp
    audience, location, duration, budget = aldb

    base = {
        "brand": brand,
        "brand_overview": None,
        "product": product,
        "product_features": None,
        "product_pricing": price,
        "brief": extra_notes.strip() or "General campaign brief.",
        "persona": audience,
        "location": location,
        "tone": tone_choice or None,
        "goal": None,
        "cta": cta_text.strip() or None,
        "constraints": None,
        "notes": None,
    }

    if action == "Campaign Plan":
        payload = dict(base)
        payload.update({
            "channels": ["Instagram", "TikTok"],
            "budget": budget,
            "duration": duration
        })
        ok, data, code = call_api("/marketing/campaign", payload)
        if not ok:
            st.error({"status": code, "detail": data})
        else:
            plan = data.get("plan", "")
            execution = data.get("execution", "")
            review = data.get("review", "")
            out = f"PLAN\n\n{plan}\n\nEXECUTION\n\n{execution}\n\nREVIEW\n\n{review}"
            st.markdown("#### Result")
            st.markdown(f"<div class='box'>{out}</div>", unsafe_allow_html=True)
            st.download_button("Download as PDF", data=pdf_bytes(out), file_name="campaign.pdf", mime="application/pdf")

    elif action == "Social Posts":
        payload = dict(base)
        payload.update({
            "platforms": ["Instagram", "TikTok"],
            "posts_per_platform": 3,
            "include_hashtags": True,
            "include_emojis": False,
            "length": "short"
        })
        ok, data, code = call_api("/marketing/social-posts", payload)
        if not ok:
            st.error({"status": code, "detail": data})
        else:
            posts = data.get("posts", {})
            if "raw" in posts:
                text = posts["raw"][0] if isinstance(posts["raw"], list) else str(posts["raw"])
            else:
                lines = []
                for platform, items in posts.items():
                    lines.append(f"=== {platform} ===")
                    lines.extend(items)
                    lines.append("")
                text = "\n".join(lines)
            st.markdown("#### Result")
            st.markdown(f"<div class='box'>{text}</div>", unsafe_allow_html=True)
            st.download_button("Download as PDF", data=pdf_bytes(text), file_name="social_posts.pdf", mime="application/pdf")

    else:  # TikTok Script
        payload = dict(base)
        payload.update({
            "duration_seconds": 30,
            "hook_style": "benefit",
            "include_shot_list": True,
            "include_captions": True,
            "include_voiceover": True
        })
        ok, data, code = call_api("/marketing/tiktok-script", payload)
        if not ok:
            st.error({"status": code, "detail": data})
        else:
            parts = []
            if data.get("storyboard"):
                parts.append("STORYBOARD\n" + "\n".join(data["storyboard"]))
            if data.get("voiceover"):
                parts.append("VOICEOVER\n" + data["voiceover"])
            if data.get("captions"):
                parts.append("CAPTIONS\n" + "\n".join(data["captions"]))
            if data.get("posting_notes"):
                parts.append("POSTING NOTES\n" + data["posting_notes"])
            text = "\n\n".join(parts) if parts else str(data)
            st.markdown("#### Result")
            st.markdown(f"<div class='box'>{text}</div>", unsafe_allow_html=True)
            st.download_button("Download as PDF", data=pdf_bytes(text), file_name="tiktok_script.pdf", mime="application/pdf")
