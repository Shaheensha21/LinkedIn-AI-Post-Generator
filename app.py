import streamlit as st
import requests
import urllib.parse
from PIL import Image
import json

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="AI-Powered LinkedIn Post Generator",
    page_icon="🤖",
    layout="wide"
)

# ---------------- Secrets ----------------
CLIENT_ID = st.secrets["LINKEDIN_CLIENT_ID"]
CLIENT_SECRET = st.secrets["LINKEDIN_CLIENT_SECRET"]
REDIRECT_URI = st.secrets["LINKEDIN_REDIRECT_URI"]

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

# ✅ CORRECT scopes
SCOPE = "r_liteprofile r_emailaddress w_member_social"

# ---------------- Session Init ----------------
if "linkedin_token" not in st.session_state:
    st.session_state.linkedin_token = None

if "linkedin_post" not in st.session_state:
    st.session_state.linkedin_post = ""

if "image" not in st.session_state:
    st.session_state.image = None

# ---------------- OAuth URL ----------------
def linkedin_auth_url():
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

# ---------------- Exchange Token ----------------
def exchange_token(code):
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    res = requests.post(TOKEN_URL, data=data, headers=headers)
    res.raise_for_status()
    return res.json()["access_token"]

# ---------------- Handle Redirect ----------------
params = st.query_params
if "code" in params and st.session_state.linkedin_token is None:
    try:
        token = exchange_token(params["code"])
        st.session_state.linkedin_token = token
        st.query_params.clear()
        st.success("✅ LinkedIn connected successfully!")
    except Exception as e:
        st.error(f"OAuth failed: {e}")

# ---------------- UI ----------------
st.title("🤖 AI-Powered LinkedIn Content Generator")

topic = st.text_input(
    "Enter LinkedIn topic",
    "How AI is helping students build real-world projects"
)

if st.button("Generate Post"):
    st.session_state.linkedin_post = f"""🚀 {topic}

AI is transforming how students learn, build, and innovate.
From real-world projects to industry-ready skills, the impact is real.

#AI #Students #Learning #Technology
"""
    st.success("Post generated!")

if st.session_state.linkedin_post:
    st.subheader("Generated Post")
    st.markdown(st.session_state.linkedin_post)

st.divider()

if st.session_state.linkedin_token is None:
    st.markdown("### 🔐 Connect your LinkedIn account")
    st.markdown(f"[🔗 Connect to LinkedIn]({linkedin_auth_url()})")
else:
    st.success("LinkedIn connected 🎉")
    st.info("You can now post directly (API posting logic can be added safely).")
