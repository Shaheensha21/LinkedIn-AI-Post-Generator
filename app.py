# ==================================================
# app.py – AI LinkedIn Post Generator + Auto Poster
# ==================================================

import streamlit as st
import requests
from PIL import Image

from text_generator import generate_linkedin_post
from image_prompt_generator import generate_flux_image_prompt
from image_generator import generate_image

# -------------------------------
# STREAMLIT CONFIG
# -------------------------------
st.set_page_config(
    page_title="AI LinkedIn Auto Poster",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 AI LinkedIn Auto Poster")
st.caption("Generate content → Login → Post to LinkedIn")

# -------------------------------
# SECRETS
# -------------------------------
CLIENT_ID = st.secrets["LINKEDIN_CLIENT_ID"]
CLIENT_SECRET = st.secrets["LINKEDIN_CLIENT_SECRET"]
REDIRECT_URI = st.secrets["LINKEDIN_REDIRECT_URI"]

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

# -------------------------------
# SESSION STATE
# -------------------------------
for key, default in {
    "generated_text": "",
    "image_path": None,
    "has_content": False,
    "linkedin_token": None,
    "linkedin_logged_in": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# -------------------------------
# STEP 1: GENERATE CONTENT
# -------------------------------
st.subheader("📝 Step 1: Generate Content")

topic = st.text_input(
    "Enter LinkedIn post topic",
    "How AI is helping students build real-world projects"
)

if st.button("Generate Post & Image"):
    with st.spinner("Generating content..."):
        post_text = generate_linkedin_post(topic)

        image_prompt = generate_flux_image_prompt(post_text)

        image_path = generate_image(image_prompt)

        st.session_state.generated_text = post_text
        st.session_state.image_path = image_path
        st.session_state.has_content = True

# -------------------------------
# DISPLAY GENERATED CONTENT
# -------------------------------
if st.session_state.has_content:
    st.markdown("### ✍️ Generated LinkedIn Post")
    st.write(st.session_state.generated_text)

    st.download_button(
        "⬇️ Download Post Text",
        st.session_state.generated_text,
        file_name="linkedin_post.txt"
    )

    st.markdown("### 🖼️ Generated Image")
    img = Image.open(st.session_state.image_path)
    st.image(img, use_container_width=True)

    with open(st.session_state.image_path, "rb") as f:
        st.download_button(
            "⬇️ Download Image",
            f,
            file_name="linkedin_post_image.webp"
        )

# -------------------------------
# STEP 2: LINKEDIN LOGIN
# -------------------------------
st.divider()
st.subheader("🔐 Step 2: Login with LinkedIn")

login_url = (
    f"{AUTH_URL}"
    f"?response_type=code"
    f"&client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&scope=openid%20profile%20w_member_social"
)

st.markdown(f"👉 [Login with LinkedIn]({login_url})")

query_params = st.query_params

if "code" in query_params and not st.session_state.linkedin_logged_in:
    auth_code = query_params["code"]

    token_res = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }
    )

    if token_res.status_code == 200:
        st.session_state.linkedin_token = token_res.json()["access_token"]
        st.session_state.linkedin_logged_in = True
        st.success("✅ LinkedIn login successful!")

# -------------------------------
# STEP 3: POST TO LINKEDIN
# -------------------------------
st.divider()
st.subheader("🚀 Step 3: Post to LinkedIn")

def get_user_urn(token):
    r = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {token}"}
    )
    return f"urn:li:person:{r.json()['sub']}"

def upload_image(token, image_path, owner):
    headers = {"Authorization": f"Bearer {token}"}

    reg = requests.post(
        "https://api.linkedin.com/v2/assets?action=registerUpload",
        headers=headers,
        json={
            "registerUploadRequest": {
                "owner": owner,
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "serviceRelationships": [{
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }]
            }
        }
    ).json()

    upload_url = reg["value"]["uploadMechanism"][
        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
    ]["uploadUrl"]

    asset = reg["value"]["asset"]

    with open(image_path, "rb") as f:
        requests.put(upload_url, data=f)

    return asset

def post_to_linkedin(token, owner, text, asset):
    return requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "author": owner,
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
    )

post_disabled = not (
    st.session_state.has_content and
    st.session_state.linkedin_logged_in
)

if st.button("📤 Post on LinkedIn", disabled=post_disabled):
    with st.spinner("Posting to LinkedIn..."):
        owner = get_user_urn(st.session_state.linkedin_token)
        asset = upload_image(
            st.session_state.linkedin_token,
            st.session_state.image_path,
            owner
        )
        res = post_to_linkedin(
            st.session_state.linkedin_token,
            owner,
            st.session_state.generated_text,
            asset
        )

    if res.status_code == 201:
        st.success("🎉 Posted successfully on LinkedIn!")
    else:
        st.error("❌ Failed to post")
