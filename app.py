# ==========================================
# app.py – AI LinkedIn Auto Poster (Final)
# ==========================================

import os
import json
import time
import requests
import streamlit as st
from PIL import Image
from text_generator import generate_linkedin_post
from image_prompt_generator import generate_image_prompt
from image_generator import generate_image

# -------------------------------
# STREAMLIT CONFIG
# -------------------------------
st.set_page_config(page_title="AI LinkedIn Auto Poster", layout="centered")
st.title("🤖 AI LinkedIn Auto Poster")
st.caption("Generate content, login to LinkedIn, and post directly")

# -------------------------------
# LINKEDIN CREDENTIALS (SECRETS)
# -------------------------------
CLIENT_ID = st.secrets["CLIENT_ID"]
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
REDIRECT_URI = st.secrets["REDIRECT_URI"]

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

TOKEN_FILE = "linkedin_token.json"  # temporary storage for token

# -------------------------------
# SESSION STATE INIT
# -------------------------------
if "generated_text" not in st.session_state:
    st.session_state.generated_text = ""
if "image_path" not in st.session_state:
    st.session_state.image_path = None
if "has_content" not in st.session_state:
    st.session_state.has_content = False
if "linkedin_logged_in" not in st.session_state:
    st.session_state.linkedin_logged_in = False
if "linkedin_token" not in st.session_state:
    st.session_state.linkedin_token = None

# -------------------------------
# STEP 1 – GENERATE POST & IMAGE
# -------------------------------
st.subheader("Step 1 – Generate LinkedIn Post & Image")
topic = st.text_input("Enter topic for LinkedIn post:")

if st.button("Generate Post & Image"):
    if topic.strip() == "":
        st.warning("Please enter a topic")
    else:
        with st.spinner("Generating content..."):
            # Generate LinkedIn post
            linkedin_post = generate_linkedin_post(topic)
            st.session_state.generated_text = linkedin_post

            # Generate image prompt
            image_prompt = generate_image_prompt(linkedin_post)

            # Generate image
            image_path = generate_image(image_prompt)
            st.session_state.image_path = image_path
            st.session_state.has_content = True

# Display generated content
if st.session_state.has_content:
    st.subheader("Generated Text:")
    st.write(st.session_state.generated_text)
    st.download_button("Download Post Text", st.session_state.generated_text)

    st.subheader("Generated Image:")
    img = Image.open(st.session_state.image_path)
    st.image(img, caption="LinkedIn Post Image", use_column_width=True)
    st.download_button(
        "Download Image",
        data=open(st.session_state.image_path, "rb").read(),
        file_name="linkedin_post_image.webp"
    )

# -------------------------------
# STEP 2 – LINKEDIN LOGIN
# -------------------------------
st.divider()
st.subheader("Step 2 – Login with LinkedIn")

login_url = (
    f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}&scope=openid%20profile%20w_member_social"
)

st.markdown(f"[Login with LinkedIn]({login_url})")

# Function to store token in a temporary file
def save_token(token):
    with open(TOKEN_FILE, "w") as f:
        json.dump({"access_token": token}, f)

# Load token if exists
def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)
        st.session_state.linkedin_token = data.get("access_token")
        st.session_state.linkedin_logged_in = True

# Handle redirect back from LinkedIn
query_params = st.experimental_get_query_params()
if "code" in query_params and not st.session_state.linkedin_logged_in:
    auth_code = query_params["code"][0]
    payload = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    r = requests.post(TOKEN_URL, data=payload)
    if r.status_code == 200:
        token = r.json()["access_token"]
        save_token(token)
        st.session_state.linkedin_token = token
        st.session_state.linkedin_logged_in = True
        st.success("LinkedIn login successful! You can now post.")

load_token()

if not st.session_state.linkedin_logged_in:
    st.info("After logging in on LinkedIn, click 'Check Login / Enable Post'.")

if st.button("Check Login / Enable Post"):
    load_token()
    if st.session_state.linkedin_logged_in:
        st.success("✅ LinkedIn login confirmed!")
    else:
        st.warning("⚠️ No login detected yet. Make sure you completed LinkedIn login.")

# -------------------------------
# STEP 3 – POST TO LINKEDIN
# -------------------------------
def get_user_urn(token):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers)
    data = r.json()
    return f"urn:li:person:{data['sub']}"

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
                "media": [{"status": "READY", "media": asset}]
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
    r = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers=headers,
        json=payload
    )
    return r.status_code

# Enable post button only after login + content
if st.session_state.has_content and st.session_state.linkedin_logged_in:
    if st.button("Post to LinkedIn"):
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
            st.success("🎉 Successfully posted to LinkedIn!")
        else:
            st.error("❌ Failed to post on LinkedIn")
