# ================================
# app.py – AI LinkedIn Auto Poster (Fixed)
# ================================

import time
import requests
import streamlit as st
from PIL import Image

from langchain.chat_models import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage
from huggingface_hub import InferenceClient

# -------------------------------
# SECRETS (from Streamlit Cloud)
# -------------------------------
GEMINI_API_KEY = st.secrets["GOOGLE_API_KEY"]
HF_API_KEY = st.secrets["HUGGINGFACE_API_KEY"]
CLIENT_ID = st.secrets["LINKEDIN_CLIENT_ID"]
CLIENT_SECRET = st.secrets["LINKEDIN_CLIENT_SECRET"]
REDIRECT_URI = st.secrets["LINKEDIN_REDIRECT_URI"]

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

# -------------------------------
# STREAMLIT CONFIG & STYLING
# -------------------------------
st.set_page_config(page_title="AI LinkedIn Auto Poster", layout="centered")
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #007182 20%, #001699 100%); color: white; }
h1, h2, h3 { color: #FFD700 !important; font-weight: 800 !important; }
.stButton>button { background-color: #FF5733 !important; color: white !important; border-radius: 8px; font-weight: bold; }
.stButton>button:hover { background-color: #FFC300 !important; color: black !important; }
</style>
""", unsafe_allow_html=True)

st.title("🤖 AI LinkedIn Auto Poster")
st.caption("Generate AI content and post directly to LinkedIn")

# -------------------------------
# SESSION STATE INIT
# -------------------------------
for key in ["has_content", "linkedin_logged_in", "linkedin_token", "generated_text", "image_path"]:
    if key not in st.session_state:
        st.session_state[key] = False if "logged_in" in key or "has_content" in key else ""

# ================================
# TEXT GENERATION (GEMINI FIXED)
# ================================
def generate_text(topic: str) -> str:
    llm = ChatGoogleGenerativeAI(
        model="chat-bison-001",  # stable LLM for production
        temperature=0.7,
        max_output_tokens=512,
        api_key=GEMINI_API_KEY
    )

    prompt = ChatPromptTemplate.from_template(
        """Write a professional and engaging LinkedIn post (100–120 words) about:
"{topic}"

Tone: professional, inspiring, positive."""
    )
    # Convert to messages
    messages = prompt.format_prompt(topic=topic).to_messages()
    response = llm.invoke(messages)
    return response.content

# ================================
# IMAGE GENERATION (HF FLUX)
# ================================
def generate_image(prompt, output_path="linkedin_image.webp"):
    client = InferenceClient(model="black-forest-labs/FLUX.1-schnell", token=HF_API_KEY)
    for attempt in range(3):
        try:
            image = client.text_to_image(prompt)
            image.save(output_path)
            return output_path
        except Exception as e:
            print(f"Retry {attempt+1}: {e}")
            time.sleep(5)
    raise RuntimeError("Image generation failed")

# ================================
# LINKEDIN OAUTH HELPERS
# ================================
def get_access_token(auth_code):
    payload = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    r = requests.post(TOKEN_URL, data=payload, timeout=10)
    return r.json().get("access_token")

def get_user_urn(token):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get("https://api.linkedin.com/v2/me", headers=headers, timeout=10)
    return f"urn:li:person:{r.json()['id']}"

def upload_image_to_linkedin(token, image_path, owner_urn):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    register_payload = {
        "registerUploadRequest": {
            "owner": owner_urn,
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "serviceRelationships": [{"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}]
        }
    }
    r = requests.post("https://api.linkedin.com/v2/assets?action=registerUpload",
                      headers=headers, json=register_payload, timeout=10)
    upload_url = r.json()["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    asset = r.json()["value"]["asset"]
    with open(image_path, "rb") as f:
        requests.put(upload_url, data=f.read(), timeout=10)
    return asset

def create_linkedin_post(token, owner_urn, text, asset):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "author": owner_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {"com.linkedin.ugc.ShareContent": {"shareCommentary": {"text": text}, "shareMediaCategory": "IMAGE", "media": [{"status": "READY", "media": asset}]}},
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
    r = requests.post("https://api.linkedin.com/v2/ugcPosts", headers=headers, json=payload, timeout=10)
    return r.status_code

# ================================
# LINKEDIN OAUTH FLOW
# ================================
st.divider()
st.subheader("🔐 LinkedIn Authorization")
login_url = f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=openid%20profile%20w_member_social"
st.markdown(f"[Login with LinkedIn]({login_url})")

query_params = st.query_params
if "code" in query_params and not st.session_state.linkedin_logged_in:
    token = get_access_token(query_params["code"])
    if token:
        st.session_state.linkedin_token = token
        st.session_state.linkedin_logged_in = True
        st.success("LinkedIn authorization successful!")

# ================================
# AI CONTENT GENERATION
# ================================
topic = st.text_input("Enter LinkedIn post topic")
if st.button("Generate"):
    if topic.strip():
        with st.spinner("Generating content..."):
            st.session_state.generated_text = generate_text(topic)
            st.session_state.image_path = generate_image(f"Professional illustration representing {topic}")
            st.session_state.has_content = True
    else:
        st.warning("Please enter a topic")

# ================================
# DISPLAY GENERATED CONTENT
# ================================
if st.session_state.has_content:
    st.subheader("📝 Generated Text")
    st.write(st.session_state.generated_text)

    st.subheader("🖼️ Generated Image")
    st.image(Image.open(st.session_state.image_path), use_container_width=True)

# ================================
# POST TO LINKEDIN
# ================================
upload_disabled = not (st.session_state.has_content and st.session_state.linkedin_logged_in)
if st.button("Upload to LinkedIn", disabled=upload_disabled):
    with st.spinner("Posting to LinkedIn..."):
        owner_urn = get_user_urn(st.session_state.linkedin_token)
        asset = upload_image_to_linkedin(st.session_state.linkedin_token, st.session_state.image_path, owner_urn)
        status = create_linkedin_post(st.session_state.linkedin_token, owner_urn, st.session_state.generated_text, asset)
    if status == 201:
        st.success("🎉 Posted successfully on LinkedIn!")
    else:
        st.error("❌ Failed to post on LinkedIn")
