import requests
import streamlit as st
from io import BytesIO
from fpdf import FPDF

# =========================
# Config
# =========================
st.set_page_config(page_title="Marketing Agent", layout="centered", page_icon="📣")
API_BASE = "https://marketing-agent-latest.onrender.com"
TIMEOUT = 120

ALLOWED_PLATFORMS = {"Facebook", "Instagram", "Twitter", "LinkedIn", "TikTok"}
ALLOWED_LENGTHS = {"short", "medium", "long"}
ALLOWED_HOOKS = {"problem", "surprise", "stat", "benefit"}

# =========================
# Styles
# =========================
st.markdown("""
<style>
  .stApp { background: linear-gradient(120deg, #f8fbff, #e4ecf7); }
  div[data-testid="stForm"] {
    background:#fff; border-radius:12px; padding:24px;
    box-shadow:0 4px 14px rgba(0,0,0,0.1);
  }
  .box {
    background:#fff; border:1px solid #d9e2ec; border-radius:10px;
    padding:16px; height:440px; overflow-y:auto; white-space:pre-wrap;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    font-size:14px;
  }
</style>
""", unsafe_allow_html=True)

st.markdown("<h2>Marketing Agent</h2>", unsafe_allow_html=True)
st.caption("Frontend aligned with FastAPI models (Campaign, Social Posts, TikTok Script)")

# =========================
# Helpers
# =========================
def call_api(path: str, payload: dict):
    url = f"{API_BASE}{path}"
    try:
        resp = requests.post(url, json=payload, timeout=TIMEOUT)
        ct = resp.headers.get("content-type", "")
        data = resp.json() if "application/json" in ct else {"raw": resp.text}
        return resp.ok, data, resp.status_code, resp.text
    except requests.RequestException as e:
        return False, {"error": str(e)}, 0, str(e)

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

def parse_csv(s: str):
    return [x.strip() for x in s.split(",") if x.strip()] if s else []

def parse_lines(s: str):
    return [x.strip() for x in s.splitlines() if x.strip()] if s else []

# =========================
# UI
# =========================
action = st.selectbox("Select Endpoint", ["Campaign Plan", "Social Posts", "TikTok Script"], index=0)

with st.form("form", clear_on_submit=False):
    st.subheader("Base Brief")

    col1, col2 = st.columns(2)
    with col1:
        brand = st.text_input("Brand *", placeholder="Acme Inc.")
        product = st.text_input("Product/Service *", placeholder="Reusable Water Bottle")
        product_pricing = st.text_input("Product Pricing/Tier (optional)", placeholder="$25")
        persona = st.text_input("Persona (optional)", placeholder="Environmentally conscious millennials and Gen Z")
        location = st.text_input("Location (optional)", placeholder="USA")
        tone = st.selectbox("Tone (optional)", ["", "Playful", "Professional", "Bold", "Minimalist", "Inspiring", "Friendly"], index=0)
        cta = st.text_input("CTA (optional)", placeholder="Shop now")
    with col2:
        brand_overview = st.text_area("Brand Overview (optional)", height=90, placeholder="Short brand description or mission...")
        product_features = st.text_area("Product Features (one per line, optional)", height=90)
        constraints = st.text_area("Constraints (one per line, optional)", height=90, placeholder="No overclaiming\nNo over-promising")
        notes = st.text_area("Notes (optional)", height=90)

    brief = st.text_area("Brief *", height=80, placeholder="Back-to-school and work-mode promotion up to 20% off...")

    if action == "Campaign Plan":
        st.subheader("CampaignRequest")
        channels_csv = st.text_input("Channels (CSV, optional)", placeholder="Instagram, TikTok")
        budget = st.text_input("Budget (optional)", placeholder="$5000")
        duration = st.text_input("Duration (optional)", placeholder="2 weeks")

    elif action == "Social Posts":
        st.subheader("SocialPostsRequest")
        platforms_csv = st.text_input("Platforms (CSV, required - Facebook, Instagram, Twitter, LinkedIn, TikTok)", placeholder="Instagram, TikTok")
        posts_per_platform = st.number_input("Posts per platform (1–10)", min_value=1, max_value=10, value=3, step=1)
        include_hashtags = st.checkbox("Include hashtags", value=True)
        include_emojis = st.checkbox("Include emojis", value=False)
        length = st.selectbox("Length", ["short", "medium", "long"], index=0)

    else:  # TikTok Script
        st.subheader("TikTokScriptRequest")
        duration_seconds = st.number_input("Duration seconds (10–90)", min_value=10, max_value=90, value=30, step=5)
        hook_style = st.selectbox("Hook style", ["problem", "surprise", "stat", "benefit"], index=3)
        include_shot_list = st.checkbox("Include shot list", value=True)
        include_captions = st.checkbox("Include captions", value=True)
        include_voiceover = st.checkbox("Include voiceover", value=True)

    submitted = st.form_submit_button("Generate")

# =========================
# Submit
# =========================
if submitted:
    # Required base fields
    if not brand.strip():
        st.error("Brand is required.")
        st.stop()
    if not product.strip():
        st.error("Product/Service is required.")
        st.stop()
    if not brief.strip():
        st.error("Brief is required.")
        st.stop()

    base = {
        "brand": brand.strip(),
        "brand_overview": (brand_overview.strip() or None) if brand_overview else None,
        "product": product.strip(),
        "product_features": parse_lines(product_features) or None,  # Optional[List[str]]
        "product_pricing": product_pricing.strip() or None,
        "brief": brief.strip(),
        "persona": persona.strip() or None,
        "location": location.strip() or None,
        "tone": (tone or None) if tone else None,
        "goal": None,
        "cta": cta.strip() or None,
        "constraints": parse_lines(constraints) or None,            # Optional[List[str]]
        "notes": notes.strip() or None,
    }

    if action == "Campaign Plan":
        payload = dict(base)
        channels = parse_csv(channels_csv)
        payload.update({
            "channels": channels or None,   # Optional[List[str]]
            "budget": budget.strip() or None,
            "duration": duration.strip() or None
        })
        ok, data, code, raw = call_api("/marketing/campaign", payload)
        if not ok:
            st.error({"status": code, "detail": data, "raw": raw})
        else:
            plan = data.get("plan", "")
            execution = data.get("execution", "")
            review = data.get("review", "")
            out = f"PLAN\n\n{plan}\n\nEXECUTION\n\n{execution}\n\nREVIEW\n\n{review}"
            st.markdown("#### Result")
            st.markdown(f"<div class='box'>{out}</div>", unsafe_allow_html=True)
            st.download_button("Download as PDF", data=pdf_bytes(out), file_name="campaign.pdf", mime="application/pdf")

    elif action == "Social Posts":
        platforms = [p for p in parse_csv(platforms_csv) if p in ALLOWED_PLATFORMS]
        if not platforms:
            st.error("At least one valid platform is required (Facebook, Instagram, Twitter, LinkedIn, TikTok).")
            st.stop()
        if posts_per_platform < 1 or posts_per_platform > 10:
            st.error("posts_per_platform must be between 1 and 10.")
            st.stop()
        if length not in ALLOWED_LENGTHS:
            st.error("length must be one of: short, medium, long.")
            st.stop()

        payload = dict(base)
        payload.update({
            "platforms": platforms,                              # List[Literal[…]]
            "posts_per_platform": int(posts_per_platform),       # 1..10
            "include_hashtags": bool(include_hashtags),
            "include_emojis": bool(include_emojis),
            "length": length                                     # Literal[…]
        })
        ok, data, code, raw = call_api("/marketing/social-posts", payload)
        if not ok:
            st.error({"status": code, "detail": data, "raw": raw})
        else:
            # posts: dict or {"raw":[text]}
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
        if int(duration_seconds) < 10 or int(duration_seconds) > 90:
            st.error("duration_seconds must be 10–90.")
            st.stop()
        if hook_style not in ALLOWED_HOOKS:
            st.error("hook_style must be one of: problem, surprise, stat, benefit.")
            st.stop()

        payload = dict(base)
        payload.update({
            "duration_seconds": int(duration_seconds),
            "hook_style": hook_style,
            "include_shot_list": bool(include_shot_list),
            "include_captions": bool(include_captions),
            "include_voiceover": bool(include_voiceover)
        })
        ok, data, code, raw = call_api("/marketing/tiktok-script", payload)
        if not ok:
            st.error({"status": code, "detail": data, "raw": raw})
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
