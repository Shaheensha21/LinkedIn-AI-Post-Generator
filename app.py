# ==========================================
# app.py – AI LinkedIn Auto Poster (Integrated)
# ==========================================

import os
import time
import requests
import streamlit as st
from PIL import Image

from text_generator import generate_linkedin_post
from image_prompt_generator import generate_flux_image_prompt
from image_generator import generate_image

# -------------------------------
# Streamlit Page Config
# -------------------------------
st.set_page_config(
    page_title="AI LinkedIn Post Generator",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI-Powered LinkedIn Post Generator")
st.caption("Generate LinkedIn content, login, and post—all in one page")

# -------------------------------
# LinkedIn OAuth Secrets
# -------------------------------
CLIENT_ID = st.secrets["LINKEDIN_CLIENT_ID"]
CLIENT_SECRET = st.secrets["LINKEDIN_CLIENT_SECRET"]
REDIRECT_URI = st.secrets["LINKEDIN_REDIRECT_URI"]  # e.g., your Streamlit app URL
AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

# -------------------------------
# Session State Initialization
# -------------------------------
if "topic" not in st.session_state:
    st.session_state.topic = ""
if "linkedin_post" not in st.session_state:
    st.session_state.linkedin_post = ""
if "image_prompt" not in st.session_state:
    st.session_state.image_prompt = ""
if "image_path" not in st.session_state:
    st.session_state.image_path = None
if "linkedin_token" not in st.session_state:
    st.session_state.linkedin_token = None
if "linkedin_logged_in" not in st.session_state:
    st.session_state.linkedin_logged_in = False

# -------------------------------
# Step 1: Generate LinkedIn Post & Image
# -------------------------------
st.header("Step 1: Generate Content")

topic = st.text_input(
    "Enter topic for your LinkedIn post:",
    st.session_state.topic
)

if st.button("Generate Post & Image"):
    if not topic.strip():
        st.warning("Please enter a topic")
    else:
        st.session_state.topic = topic
        with st.spinner("Generating LinkedIn post..."):
            st.session_state.linkedin_post = generate_linkedin_post(topic)

        with st.spinner("Generating FLUX image prompt..."):
            st.session_state.image_prompt = generate_flux_image_prompt(st.session_state.linkedin_post)

        with st.spinner("Generating professional image..."):
            st.session_state.image_path = generate_image(st.session_state.image_prompt)

        st.success("✅ Content and image generated successfully!")

# Display Generated Post & Image
if st.session_state.linkedin_post:
    st.subheader("🔹 LinkedIn Post")
    st.text_area("Generated Post", st.session_state.linkedin_post, height=200)
    st.download_button(
        "Download Post Text",
        st.session_state.linkedin_post,
        file_name="linkedin_post.txt"
    )

if st.session_state.image_path:
    st.subheader("🔹 Generated Image")
    img = Image.open(st.session_state.image_path)
    st.image(img, caption="Generated LinkedIn Post Image", use_column_width=True)
    st.download_button(
        "Download Image",
        data=open(st.session_state.image_path, "rb").read(),
        file_name="linkedin_post_image.webp",
        mime="image/webp"
    )

# -------------------------------
# Step 2: LinkedIn Login
# -------------------------------
st.header("Step 2: LinkedIn Login")

if not st.session_state.linkedin_logged_in:
    login_url = (
        f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}&scope=openid%20profile%20w_member_social"
    )
    st.markdown(f"[Login with LinkedIn]({login_url})")
    st.info("Click above to login. After successful login, come back here to post.")

    # Check for 'code' in query params after redirect
    query_params = st.experimental_get_query_params()
    if "code" in query_params:
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
            st.session_state.linkedin_token = r.json()["access_token"]
            st.session_state.linkedin_logged_in = True
            st.success("✅ LinkedIn login successful! You can now post.")
        else:
            st.error("❌ Failed to get LinkedIn token. Check your redirect URL and credentials.")

# -------------------------------
# Step 3: Post to LinkedIn
# -------------------------------
st.header("Step 3: Post to LinkedIn")

if st.session_state.linkedin_logged_in and st.session_state.linkedin_post and st.session_state.image_path:

    def get_user_urn(token):
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get("https://api.linkedin.com/v2/me", headers=headers)
        data = r.json()
        return f"urn:li:person:{data['id']}"

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
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "IMAGE",
                    "media": [{"status": "READY", "media": asset}]
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
        }
        r = requests.post("https://api.linkedin.com/v2/ugcPosts", headers=headers, json=payload)
        return r.status_code

    if st.button("Post to LinkedIn"):
        with st.spinner("Posting to LinkedIn..."):
            try:
                owner_urn = get_user_urn(st.session_state.linkedin_token)
                asset = upload_image_to_linkedin(
                    st.session_state.linkedin_token,
                    st.session_state.image_path,
                    owner_urn
                )
                status = create_linkedin_post(
                    st.session_state.linkedin_token,
                    owner_urn,
                    st.session_state.linkedin_post,
                    asset
                )
                if status == 201:
                    st.success("🎉 Posted successfully on LinkedIn!")
                else:
                    st.error(f"❌ Failed to post. Status code: {status}")
            except Exception as e:
                st.error(f"❌ Error while posting: {e}")
