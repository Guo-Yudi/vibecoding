"""Streamlit version of the AI Travel Planner using OpenRouter (gpt-oss-20b)."""
import os
import textwrap
from typing import Optional

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    val = os.getenv(name, default)
    if isinstance(val, str):
        val = val.strip()
    return val

# Prefer Streamlit secrets, then environment (.env) fallback
OPENROUTER_API_KEY = (
    (st.secrets.get("OPENROUTER_API_KEY") if hasattr(st, "secrets") else None)
    or _get_env("OPENROUTER_API_KEY")
)
if isinstance(OPENROUTER_API_KEY, str):
    OPENROUTER_API_KEY = OPENROUTER_API_KEY.strip()

SITE_URL = (
    (st.secrets.get("SITE_URL") if hasattr(st, "secrets") else None)
    or _get_env("SITE_URL", "http://localhost:8501")
)
SITE_NAME = (
    (st.secrets.get("SITE_NAME") if hasattr(st, "secrets") else None)
    or _get_env("SITE_NAME", "AI Travel Planner")
)


def build_prompt(
    city: str,
    days: int,
    budget: str,
    interests: str,
    people: Optional[int] = None,
    pace: Optional[str] = None,
    dietary: Optional[str] = None,
) -> str:
    interests_text = interests.strip() or "history, food, culture, hidden gems"
    budget_text = budget.strip() or "moderate"
    city_text = city.strip()
    people_text = people if (isinstance(people, int) and people > 0) else 1
    pace_text = (pace or "balanced").strip()
    dietary_text = (dietary or "none").strip()

    prompt = f"""
    You are a friendly, student-focused travel planner. Create a detailed, practical, day-wise itinerary.

    City: {city_text}
    Number of days: {days}
    People: {people_text}
    Budget level: {budget_text} (student-friendly)
    Interests: {interests_text}
    Travel pace: {pace_text}  (options: relaxed | balanced | packed)
    Dietary preferences: {dietary_text}

    Output must be valid, minimal HTML (no markdown asterisks):
    - Use <h2> and <strong> for headings (no leading * characters anywhere).
    - Include a short <section> overview.
    - Include a <section> "Trip Summary" with a small <ul> or <table> (City, Days, People, Budget, Pace, Interests, Dietary).
    - Include a <section> "Day-by-Day Timeline" with a table for each day (Day N). For each row include:
        • Time range (e.g., 09:00–10:30)
        • Activity (place name in <strong>)
        • Area / Neighborhood
        • Food stop (what and where) if relevant
        • Transit note (metro station/bus/walk)
        • Approx student cost (local currency)
    - Include a <section> "Food & Transit Tips" with a compact table of 4–6 recommended spots (Where, What to eat, Cost, Transit tip).
    - End with a <section> "Safety & Money-Saving Tips" containing 3 concise tips.
    - Keep it concise but specific. Prefer bullet tables and short lines.
    - Ensure headings are bold (use <strong> inside <h2> if needed) and there are no asterisks used for bullets.
    - Do not include outer <html>/<body> tags; return only the inner HTML for rendering.
    """
    return textwrap.dedent(prompt).strip()


def call_openrouter(prompt: str, model: Optional[str] = None) -> str:
    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY not set. Add it via Streamlit Secrets or .env (never commit it)."
        )
    try:
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": SITE_URL or "",  # Optional ranking headers
                "X-Title": SITE_NAME or "",
            },
            extra_body={},
            model=model or "openai/gpt-oss-20b:free",
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:  # Network or auth level errors
        msg = str(e)
        # Provide friendlier guidance if this looks like auth
        if "401" in msg or "User not found" in msg:
            raise RuntimeError(
                "Authentication failed (401). Double-check that your OpenRouter key is valid, not expired, and copied without extra spaces."
            ) from e
        raise

    content = completion.choices[0].message.content if completion.choices else ""
    content = (content or "").strip()
    if not content:
        raise RuntimeError("OpenRouter response had no message content.")
    return content


st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="✈️",
    layout="wide",
)

hide_streamlit_style = """
<style>
header, footer, .stDeployButton {visibility: hidden;}
.block-container {padding-top: 1.2rem; padding-bottom: 3rem;}
body, .stApp {background: radial-gradient(1000px 1000px at 10% 10%, rgba(255,255,255,0.05), transparent),
                        radial-gradient(800px 800px at 90% 20%, rgba(255,255,255,0.06), transparent),
                        linear-gradient(135deg,#1e0935,#2a0e4a,#3b145f);}
.planner-title {font-family: 'Playwrite DE SAS','BBH Sans Bogle','Poppins',sans-serif; font-size: 2.6rem; background: linear-gradient(90deg,#d6b5ff,#c9a4ff,#b48bff); -webkit-background-clip:text; background-clip:text; color:transparent; margin-bottom: .3rem;}
.planner-sub {font-family: 'Quicksand','Poppins',sans-serif; font-weight:500; color:#cdbdea; margin-top:0; margin-bottom:1.2rem;}
.result-card {background:#24123d; border:1px solid rgba(255,255,255,0.08); padding:1.4rem 1.2rem; border-radius:14px; box-shadow:0 10px 30px rgba(0,0,0,.35);} 
.result-card table {width:100%; border-collapse:collapse; margin:10px 0 16px;} 
.result-card th,.result-card td {border:1px solid rgba(255,255,255,0.08); padding:8px 10px; vertical-align:top; font-size:.9rem;} 
.result-card th {background:rgba(255,255,255,0.07);} 
.provider-chip {display:inline-block; background:rgba(138,92,246,0.18); border:1px solid rgba(138,92,246,0.35); color:#e9ddff; padding:4px 10px; border-radius:999px; font-size:.65rem; letter-spacing:1px; text-transform:uppercase; margin-left:.6rem;} 
.stTextInput>div>div>input, .stNumberInput input, .stSelectbox>div>div>select, textarea {background:#1b0e2e !important; color:#e6e1ee !important; border-radius:10px !important;}
.stButton button {background:#8a5cf6; color:#fff; border-radius:12px; font-weight:600; border:1px solid #8a5cf6; box-shadow:0 6px 16px rgba(138,92,246,.35);} 
.stButton button:hover {background:#7442f0; border-color:#7442f0;} 
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.markdown("<h1 class='planner-title'>AI Travel Planner</h1>", unsafe_allow_html=True)
st.markdown("<p class='planner-sub'>Plan smarter, travel cheaper, and explore more.</p>", unsafe_allow_html=True)

with st.form("planner_form"):
    col1, col2, col3 = st.columns([3,1,2])
    with col1:
        city = st.text_input("City", placeholder="Paris", value="")
    with col2:
        days = st.number_input("Days", min_value=1, max_value=30, value=3, step=1)
    with col3:
        budget = st.selectbox("Budget", ["budget", "moderate", "comfortable"], index=0)

    col4, col5, col6 = st.columns([1.2,1.2,2])
    with col4:
        people = st.number_input("People", min_value=1, max_value=20, value=1, step=1)
    with col5:
        pace = st.selectbox("Pace", ["relaxed", "balanced", "packed"], index=1)
    with col6:
        dietary = st.text_input("Dietary Prefs", placeholder="vegetarian, vegan, none")

    interests = st.text_input("Interests", placeholder="history, street food, museums, hidden gems")

    submitted = st.form_submit_button("Generate Itinerary ✈️")

if submitted:
    if not city.strip():
        st.error("Please enter a city.")
    else:
        with st.spinner("Planning your adventure..."):
            try:
                prompt = build_prompt(city, days, budget, interests, people=people, pace=pace, dietary=dietary)
                html = call_openrouter(prompt)
                st.markdown(
                    f"<div class='result-card'><div><strong>Provider:</strong> OpenRouter (gpt-oss-20b)<span class='provider-chip'>LLM</span></div>{html}</div>",
                    unsafe_allow_html=True,
                )
            except Exception as e:
                st.error(str(e))
                with st.expander("Troubleshooting", expanded=False):
                    st.markdown(
                        """
                        **Potential fixes:**
                        - Ensure you added `OPENROUTER_API_KEY` in Streamlit Secrets (Settings → Secrets).
                        - Remove any leading/trailing spaces when copying the key.
                        - Keys are per account; create a fresh one if unsure.
                        - Confirm the model slug `openai/gpt-oss-20b:free` is still available.
                        - If rate-limited, wait a minute and retry.
                        """
                    )

st.markdown("<p style='text-align:center; margin-top:2rem; opacity:0.7;'>Made for Students ✈️</p>", unsafe_allow_html=True)