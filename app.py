# ==========================================
# app.py – AI LinkedIn Auto Poster (FINAL)
# ==========================================

import streamlit as st
import requests
import time
from PIL import Image

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from huggingface_hub import InferenceClient

# ------------------------------------------
# STREAMLIT PAGE CONFIG
# ------------------------------------------
st.set_page_config(
    page_title="AI LinkedIn Auto Poster",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 AI LinkedIn Auto Poster")
st.caption("Generate AI content and post directly to LinkedIn")

# ------------------------------------------
# LOAD SECRETS (STREAMLIT CLOUD)
# ------------------------------------------
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
HF_API_KEY = st.secrets["HUGGINGFACE_API_KEY"]

CLIENT_ID = st.secrets["LINKEDIN_CLIENT_ID"]
CLIENT_SECRET = st.secrets["LINKEDIN_CLIENT_SECRET"]
REDIRECT_URI = st.secrets["LINKEDIN_REDIRECT_URI"]

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

# ------------------------------------------
# SESSION STATE INIT (🔥 CRITICAL FIX)
# ------------------------------------------
defaults = {
    "has_content": False,
    "generated_text": "",
    "image_path": None,
    "linkedin_logged_in": False,
    "linkedin_token": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ------------------------------------------
# TEXT GENERATION (GEMINI)
# ------------------------------------------
def generate_text(topic: str) -> str:
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-2.5-flash",
        api_key=GOOGLE_API_KEY,
        temperature=0.7,
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

# ------------------------------------------
# IMAGE GENERATION (HUGGING FACE)
# ------------------------------------------
def generate_image(prompt, output_path="generated_image.png"):
    client = InferenceClient(
        model="black-forest-labs/FLUX.1-schnell",
        token=HF_API_KEY
    )

    for attempt in range(3):
        try:
            image = client.text_to_image(prompt)
            image.save(output_path)
            return output_path
        except Exception:
            time.sleep(5)

    raise RuntimeError("Image generation failed")

# ------------------------------------------
# LINKEDIN OAUTH HELPERS
# ------------------------------------------
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

# ------------------------------------------
# LINKEDIN POST HELPERS
# ------------------------------------------
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

# ------------------------------------------
# UI – GENERATE CONTENT
# ------------------------------------------
topic = st.text_input("Enter your LinkedIn topic")

if st.button("🚀 Generate"):
    if topic.strip():
        with st.spinner("Generating content..."):
            text = generate_text(topic)
            image_path = generate_image(
                f"Professional illustration representing {topic}"
            )

        st.session_state.generated_text = text
        st.session_state.image_path = image_path
        st.session_state.has_content = True
    else:
        st.warning("Please enter a topic")

# ------------------------------------------
# DISPLAY CONTENT
# ------------------------------------------
if st.session_state.has_content:
    st.subheader("📝 Generated Post")
    st.write(st.session_state.generated_text)

    if st.session_state.image_path:
        st.subheader("🖼️ Generated Image")
        st.image(Image.open(st.session_state.image_path), use_container_width=True)

# ------------------------------------------
# LINKEDIN AUTH
# ------------------------------------------
# ------------------------------------------
# LINKEDIN AUTH (FIXED FLOW)
# ------------------------------------------
st.divider()
st.subheader("🔐 LinkedIn Authorization")

if not st.session_state.linkedin_logged_in:
    login_url = (
        f"{AUTH_URL}"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=openid%20profile%20w_member_social"
    )
    st.markdown(f"[🔑 Login with LinkedIn]({login_url})")
else:
    st.success("✅ LinkedIn logged in successfully")

# --- HANDLE REDIRECT ---
query_params = st.query_params

if "code" in query_params and not st.session_state.linkedin_logged_in:
    with st.spinner("Authenticating with LinkedIn..."):
        token = get_access_token(query_params["code"])

        if token:
            st.session_state.linkedin_token = token
            st.session_state.linkedin_logged_in = True

            # 🔥 CLEAR QUERY PARAMS (IMPORTANT)
            st.query_params.clear()

            # 🔥 FORCE RERUN SO UI UPDATES
            st.rerun()

# ------------------------------------------
# POST TO LINKEDIN
# ------------------------------------------
if st.button(
    "📤 Upload to LinkedIn",
    disabled=not (
        st.session_state.linkedin_logged_in
        and st.session_state.has_content
    ),
):
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
