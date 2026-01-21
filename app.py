# ================================
# app.py – AI LinkedIn Auto Poster
# ================================

import time
import requests
import streamlit as st
from PIL import Image

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from huggingface_hub import InferenceClient

# -------------------------------
# STREAMLIT CONFIG
# -------------------------------
st.set_page_config(
    page_title="AI LinkedIn Auto Poster",
    layout="centered"
)

st.title("🤖 AI LinkedIn Auto Poster")
st.caption("Generate AI content and post it directly to LinkedIn")

# -------------------------------
# SECRETS (STREAMLIT CLOUD)
# -------------------------------
GEMINI_API_KEY = st.secrets["GOOGLE_API_KEY"]
HF_API_KEY = st.secrets["HUGGINGFACE_API_KEY"]

CLIENT_ID = st.secrets["LINKEDIN_CLIENT_ID"]
CLIENT_SECRET = st.secrets["LINKEDIN_CLIENT_SECRET"]

# 🔴 MUST MATCH LINKEDIN DASHBOARD EXACTLY
REDIRECT_URI = "https://linkedin-ai-post-generator-m6wsoanuahm6kvq6lvcppd.streamlit.app"

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

# -------------------------------
# SESSION STATE INIT
# -------------------------------
if "has_content" not in st.session_state:
    st.session_state.has_content = False

if "linkedin_logged_in" not in st.session_state:
    st.session_state.linkedin_logged_in = False

if "linkedin_token" not in st.session_state:
    st.session_state.linkedin_token = None

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

    response = llm.invoke(prompt.format(topic=topic))
    return response.content

# -------------------------------
# IMAGE GENERATION (HF)
# -------------------------------
def generate_image(prompt, output_path="generated_image.png"):
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
# AI PIPELINE
# -------------------------------
def ai_generate_pipeline(query):
    text = generate_text(query)
    image_path = generate_image(
        f"Professional illustration representing {query}"
    )
    return text, image_path

# -------------------------------
# LINKEDIN OAUTH HELPERS
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
        return r.json()["access_token"]
    return None


def get_user_urn(token):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers)
    data = r.json()
    return f"urn:li:person:{data['sub']}"

# -------------------------------
# LINKEDIN POST HELPERS
# -------------------------------
def upload_image_to_linkedin(token, image_path, owner_urn):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    register_payload = {
        "registerUploadRequest": {
            "owner": owner_urn,
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "serviceRelationships": [{
                "relationshipType": "OWNER",
                "identifier": "urn:li:userGeneratedContent"
            }]
        }
    }

    r = requests.post(
        "https://api.linkedin.com/v2/assets?action=registerUpload",
        headers=headers,
        json=register_payload
    )

    upload_url = r.json()["value"]["uploadMechanism"][
        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
    ]["uploadUrl"]

    asset = r.json()["value"]["asset"]

    with open(image_path, "rb") as f:
        requests.put(upload_url, data=f.read())

    return asset


def create_linkedin_post(token, owner_urn, text, asset):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "author": owner_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "IMAGE",
                "media": [{
                    "status": "READY",
                    "media": asset
                }]
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    r = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers=headers,
        json=payload
    )

    return r.status_code

# ===============================
# UI: GENERATE CONTENT
# ===============================
query = st.text_input("Enter your topic")

if st.button("Generate"):
    if query.strip():
        with st.spinner("Generating AI content..."):
            text, image_path = ai_generate_pipeline(query)

        st.session_state.generated_text = text
        st.session_state.image_path = image_path
        st.session_state.has_content = True
    else:
        st.warning("Please enter a topic")

# -------------------------------
# DISPLAY GENERATED CONTENT
# -------------------------------
if st.session_state.has_content:
    st.subheader("📝 Generated Text")
    st.write(st.session_state.generated_text)

    st.subheader("🖼️ Generated Image")
    st.image(
        Image.open(st.session_state.image_path),
        use_container_width=True
    )

# ===============================
# LINKEDIN AUTH
# ===============================
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

if "code" in query_params and not st.session_state.linkedin_logged_in:
    token = get_access_token(query_params["code"])
    if token:
        st.session_state.linkedin_token = token
        st.session_state.linkedin_logged_in = True
        st.success("LinkedIn authorization successful!")

        # 🔥 CRITICAL FIX: STOP REFRESH LOOP
        st.query_params.clear()

# ===============================
# UPLOAD TO LINKEDIN
# ===============================
upload_disabled = not (
    st.session_state.has_content and
    st.session_state.linkedin_logged_in
)

if st.button("Upload to LinkedIn", disabled=upload_disabled):
    with st.spinner("Posting to LinkedIn..."):
        owner_urn = get_user_urn(st.session_state.linkedin_token)
        asset = upload_image_to_linkedin(
            st.session_state.linkedin_token,
            st.session_state.image_path,
            owner_urn
        )
        status = create_linkedin_post(
            st.session_state.linkedin_token,
            owner_urn,
            st.session_state.generated_text,
            asset
        )

    if status == 201:
        st.success("🎉 Posted successfully on LinkedIn!")
    else:
        st.error("❌ Failed to post on LinkedIn")
