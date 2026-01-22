# ================================
# app.py – AI LinkedIn Auto Poster (Login First Flow)
# ================================

import os
import time
import requests
import streamlit as st
from PIL import Image

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from huggingface_hub import InferenceClient

# -------------------------------
# STREAMLIT SECRETS
# -------------------------------
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
HF_API_KEY = st.secrets["HF_API_KEY"]
CLIENT_ID = st.secrets["CLIENT_ID"]
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
REDIRECT_URI = "https://linkedinpostgenerator1234.streamlit.app/"

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

# -------------------------------
# STREAMLIT CONFIG & STYLING
# -------------------------------
st.set_page_config(page_title="AI LinkedIn Auto Poster", layout="centered")

st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #007182 20%, #001699 100%); color: white; }
h1, h2, h3, h4, h5, h6 { font-size: 2.2em !important; font-weight: 800 !important; color: #FFD700 !important; }
.stButton>button { background-color: #FF5733 !important; color: white !important; border-radius: 8px !important; font-size: 1.1em !important; font-weight: bold !important; }
.stButton>button:hover { background-color: #FFC300 !important; color: black !important; }
</style>
""", unsafe_allow_html=True)

st.title("🤖 AI LinkedIn Auto Poster")
st.caption("Login first, then generate AI content and post directly to LinkedIn")

# -------------------------------
# SESSION STATE INIT
# -------------------------------
for key in ["linkedin_logged_in", "linkedin_token", "has_content", "generated_text", "image_path"]:
    if key not in st.session_state:
        st.session_state[key] = False if "logged_in" in key or "has_content" in key else None

# -------------------------------
# LINKEDIN AUTH HELPERS
# -------------------------------
def get_access_token(auth_code):
    payload = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    r = requests.post(TOKEN_URL, data=payload)
    if r.status_code == 200:
        return r.json().get("access_token")
    return None

def get_user_urn(token):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers)
    data = r.json()
    return f"urn:li:person:{data['sub']}"

# -------------------------------
# TEXT GENERATION (GEMINI)
# -------------------------------
def generate_text(topic: str) -> str:
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-2.5-flash",
        api_key=GEMINI_API_KEY,
        temperature=0.7
    )
    prompt = PromptTemplate(
        input_variables=["topic"],
        template="""
Write a professional and engaging LinkedIn post (100–120 words) about:
"{topic}"

Tone: professional, inspiring, positive.
"""
    )
    formatted_prompt = prompt.format(topic=topic)
    response = llm.invoke(formatted_prompt)
    return response.content

# -------------------------------
# IMAGE GENERATION (HF)
# -------------------------------
def generate_image(prompt, output_path="generated_image.png"):
    client = InferenceClient(model="black-forest-labs/FLUX.1-schnell", token=HF_API_KEY)
    for attempt in range(3):
        try:
            image = client.text_to_image(prompt)
            image.save(output_path)
            return output_path
        except Exception as e:
            print(f"Image retry {attempt+1}: {e}")
            time.sleep(5)
    raise RuntimeError("Image generation failed")

# -------------------------------
# AI PIPELINE
# -------------------------------
def ai_generate_pipeline(query):
    text = generate_text(query)
    image_path = generate_image(f"Professional illustration representing {query}")
    return text, image_path

# -------------------------------
# LINKEDIN POST HELPERS
# -------------------------------
def upload_image_to_linkedin(token, image_path, owner_urn):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    register_payload = {
        "registerUploadRequest": {
            "owner": owner_urn,
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "serviceRelationships": [{"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}]
        }
    }
    r = requests.post("https://api.linkedin.com/v2/assets?action=registerUpload", headers=headers, json=register_payload)
    upload_url = r.json()["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    asset = r.json()["value"]["asset"]
    with open(image_path, "rb") as f:
        requests.put(upload_url, data=f.read())
    return asset

def create_linkedin_post(token, owner_urn, text, asset):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "author": owner_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {"com.linkedin.ugc.ShareContent": {"shareCommentary": {"text": text}, "shareMediaCategory": "IMAGE", "media": [{"status": "READY", "media": asset}]}},
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
    r = requests.post("https://api.linkedin.com/v2/ugcPosts", headers=headers, json=payload)
    return r.status_code

# ===============================
# LINKEDIN LOGIN FLOW (FIRST)
# ===============================
st.subheader("🔐 LinkedIn Login Required")
login_url = f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=openid%20profile%20w_member_social"
st.markdown(f"[Login with LinkedIn]({login_url})")

query_params = st.query_params
if "code" in query_params and not st.session_state.linkedin_logged_in:
    token = get_access_token(query_params["code"])
    if token:
        st.session_state.linkedin_token = token
        st.session_state.linkedin_logged_in = True
        st.success("✅ LinkedIn login successful!")

# ===============================
# ONLY SHOW CONTENT AFTER LOGIN
# ===============================
if st.session_state.linkedin_logged_in:

    # AI CONTENT GENERATION
    st.subheader("📝 Generate LinkedIn Content")
    topic = st.text_input("Enter your topic")

    if st.button("Generate"):
        if topic.strip() == "":
            st.warning("Please enter a topic")
        else:
            with st.spinner("Generating AI content..."):
                text, image_path = ai_generate_pipeline(topic)
            st.session_state.generated_text = text
            st.session_state.image_path = image_path
            st.session_state.has_content = True

    # DISPLAY GENERATED CONTENT
    if st.session_state.has_content:
        st.subheader("📝 Generated Text")
        st.write(st.session_state.generated_text)

        st.subheader("🖼️ Generated Image")
        st.image(Image.open(st.session_state.image_path), use_container_width=True)

        # UPLOAD TO LINKEDIN
        if st.button("Upload to LinkedIn"):
            with st.spinner("Posting to LinkedIn..."):
                owner_urn = get_user_urn(st.session_state.linkedin_token)
                asset = upload_image_to_linkedin(st.session_state.linkedin_token, st.session_state.image_path, owner_urn)
                status = create_linkedin_post(st.session_state.linkedin_token, owner_urn, st.session_state.generated_text, asset)

            if status == 201:
                st.success("🎉 Posted successfully on LinkedIn!")
            else:
                st.error("❌ Failed to post on LinkedIn")
else:
    st.info("Please login with LinkedIn to generate and post content.")
