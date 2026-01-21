# ================================
# app.py – AI LinkedIn Post Generator
# ================================

import streamlit as st
import requests
import urllib.parse
import io
import time
from PIL import Image

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from huggingface_hub import InferenceClient


# -------------------------------
# LOAD ENV VARIABLES
# -------------------------------
load_dotenv()

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
HF_API_KEY = st.secrets["HF_API_KEY"]

CLIENT_ID = st.secrets["LINKEDIN_CLIENT_ID"]
CLIENT_SECRET = st.secrets["LINKEDIN_CLIENT_SECRET"]
REDIRECT_URI = st.secrets["LINKEDIN_REDIRECT_URI"]

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

# -------------------------------
# STREAMLIT CONFIG
# -------------------------------
st.set_page_config(
    page_title="AI-Powered LinkedIn Content Generator",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI-Powered LinkedIn Content Generator")
st.caption("Generate AI posts, images, and publish directly to LinkedIn")

# -------------------------------
# SESSION STATE
# -------------------------------
if "generated" not in st.session_state:
    st.session_state.generated = False

if "linkedin_post" not in st.session_state:
    st.session_state.linkedin_post = ""

if "image_path" not in st.session_state:
    st.session_state.image_path = None

if "linkedin_token" not in st.session_state:
    st.session_state.linkedin_token = None

# -------------------------------
# TEXT GENERATION (GEMINI)
# -------------------------------
def generate_linkedin_post(topic: str) -> str:
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-2.5-flash",
        api_key=GEMINI_API_KEY,
        temperature=0.7
    )

    prompt = PromptTemplate(
        input_variables=["topic"],
        template="""
        Write a professional LinkedIn post (100–120 words) about:
        "{topic}"

        Tone: professional, inspiring, positive.
        """
    )

    response = llm.invoke(prompt.format(topic=topic))
    return response.content

# -------------------------------
# IMAGE GENERATION (HF)
# -------------------------------
def generate_image(prompt: str, output_path="linkedin_image.png") -> str:
    client = InferenceClient(
        model="black-forest-labs/FLUX.1-schnell",
        token=HF_API_KEY
    )

    for _ in range(3):
        try:
            image = client.text_to_image(prompt)
            image.save(output_path)
            return output_path
        except Exception:
            time.sleep(5)

    raise RuntimeError("Image generation failed")

# -------------------------------
# LINKEDIN HELPERS
# -------------------------------
def get_access_token(code):
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    r = requests.post(TOKEN_URL, data=payload)
    if r.status_code == 200:
        return r.json()["access_token"]
    return None


def get_user_urn(token):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers)
    return f"urn:li:person:{r.json()['sub']}"

# -------------------------------
# UI INPUT
# -------------------------------
topic = st.text_input(
    "🔹 Enter your LinkedIn topic",
    placeholder="Completed AICTE internship on AI & Digital Literacy"
)

# -------------------------------
# GENERATE CONTENT
# -------------------------------
if st.button("🚀 Generate Post & Image"):
    if not topic.strip():
        st.warning("Please enter a topic.")
    else:
        with st.spinner("Generating LinkedIn post..."):
            st.session_state.linkedin_post = generate_linkedin_post(topic)

        with st.spinner("Generating image..."):
            st.session_state.image_path = generate_image(
                f"Professional LinkedIn illustration about {topic}"
            )

        st.session_state.generated = True
        st.success("Content generated successfully!")

# -------------------------------
# DISPLAY OUTPUT
# -------------------------------
if st.session_state.generated:
    st.divider()

    st.subheader("📝 LinkedIn Post")
    st.text_area(
        "Copy & edit if needed",
        st.session_state.linkedin_post,
        height=180
    )

    st.subheader("🖼️ Image")
    st.image(
        Image.open(st.session_state.image_path),
        width=500
    )

# -------------------------------
# LINKEDIN AUTH
# -------------------------------
st.divider()
st.subheader("🔐 LinkedIn Authorization")

login_url = (
    f"{AUTH_URL}"
    f"?response_type=code"
    f"&client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&scope=openid%20profile%20w_member_social"
)

st.markdown(f"[Login with LinkedIn]({login_url})")

query_params = st.query_params
if "code" in query_params and not st.session_state.linkedin_token:
    token = get_access_token(query_params["code"])
    if token:
        st.session_state.linkedin_token = token
        st.success("LinkedIn login successful!")

# -------------------------------
# FINAL NOTE
# -------------------------------
st.divider()
st.info(
    "If posting fails: your LinkedIn app must be **approved** for "
    "`w_member_social`. This is a LinkedIn policy restriction."
)
