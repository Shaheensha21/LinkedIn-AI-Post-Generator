# ==================================================
# app.py – AI LinkedIn Post Generator + Auto Poster
# ==================================================

import streamlit as st
from PIL import Image
from text_generator import generate_linkedin_post
from image_prompt_generator import generate_flux_image_prompt
from image_generator import generate_image

st.set_page_config(
    page_title="🤖 AI LinkedIn Post Generator",
    layout="centered",
    page_icon="🤖"
)

st.title("🤖 AI LinkedIn Post Generator")
st.caption("Step 1: Login → Step 2: Generate content → Step 3: Post to LinkedIn")

# -------------------------------
# SESSION STATE INIT
# -------------------------------
for key, default in {
    "linkedin_logged_in": False,
    "linkedin_token": None,
    "generated_text": "",
    "image_path": None,
    "has_content": False
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# -------------------------------
# STEP 1: LOGIN
# -------------------------------
st.subheader("🔐 Step 1: Login with LinkedIn")

CLIENT_ID = st.secrets["LINKEDIN_CLIENT_ID"]
REDIRECT_URI = st.secrets["LINKEDIN_REDIRECT_URI"]
SCOPE = "openid profile w_member_social"

AUTH_URL = (
    f"https://www.linkedin.com/oauth/v2/authorization?"
    f"response_type=code&client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&scope={SCOPE}"
)

if not st.session_state.linkedin_logged_in:
    st.markdown(f"[🔑 Login with LinkedIn]({AUTH_URL})")
    st.info("You must login first to generate content and post.")
else:
    st.success("✅ Logged in successfully! You can generate content now.")

# -------------------------------
# STEP 2: GENERATE CONTENT
# -------------------------------
st.divider()
st.subheader("📝 Step 2: Generate Post & Image")

topic = st.text_input(
    "Enter LinkedIn post topic",
    "How AI is helping students build real-world projects"
)

if st.session_state.linkedin_logged_in:
    if st.button("Generate Post & Image"):
        with st.spinner("Generating AI content..."):
            # Generate post text
            post_text = generate_linkedin_post(topic)
            st.session_state.generated_text = post_text

            # Generate image prompt & image
            image_prompt = generate_flux_image_prompt(post_text)
            image_path = generate_image(image_prompt)
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
# STEP 3: POST TO LINKEDIN
# -------------------------------
st.divider()
st.subheader("🚀 Step 3: Post to LinkedIn")

import requests

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
                "serviceRelationships": [ {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                } ]
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
                    "media": [{"status": "READY","media": asset}]
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
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
