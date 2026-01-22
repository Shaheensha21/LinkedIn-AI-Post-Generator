import streamlit as st
import requests
from PIL import Image

from text_generator import generate_linkedin_post
from image_prompt_generator import generate_flux_image_prompt
from image_generator import generate_image

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="AI LinkedIn Auto Poster",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 AI LinkedIn Auto Poster")

# --------------------------------------------------
# SECRETS
# --------------------------------------------------
CLIENT_ID = st.secrets["LINKEDIN_CLIENT_ID"]
CLIENT_SECRET = st.secrets["LINKEDIN_CLIENT_SECRET"]
REDIRECT_URI = st.secrets["LINKEDIN_REDIRECT_URI"]

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
defaults = {
    "linkedin_logged_in": False,
    "linkedin_token": None,
    "post_text": "",
    "image_path": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --------------------------------------------------
# STEP 1: HANDLE OAUTH CALLBACK
# --------------------------------------------------
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
        },
        timeout=10,
    )

    if token_res.status_code == 200:
        st.session_state.linkedin_token = token_res.json()["access_token"]
        st.session_state.linkedin_logged_in = True
        st.query_params.clear()
        st.success("✅ Login successful!")
    else:
        st.error("❌ LinkedIn authentication failed")

# --------------------------------------------------
# STEP 2: LOGIN UI
# --------------------------------------------------
if not st.session_state.linkedin_logged_in:
    login_url = (
        f"{AUTH_URL}"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=w_member_social"
    )

    st.warning("⚠️ You must login to LinkedIn first.")
    st.markdown(f"### 🔐 [Login with LinkedIn]({login_url})")
    st.stop()

# --------------------------------------------------
# STEP 3: GENERATE CONTENT
# --------------------------------------------------
st.success("🔓 Authentication successful")

topic = st.text_input(
    "Enter LinkedIn post topic",
    "How AI is helping students build real-world projects"
)

if st.button("✨ Generate Post & Image"):
    with st.spinner("Generating content..."):
        st.session_state.post_text = generate_linkedin_post(topic)
        prompt = generate_flux_image_prompt(st.session_state.post_text)
        st.session_state.image_path = generate_image(prompt)

# --------------------------------------------------
# DISPLAY CONTENT
# --------------------------------------------------
if st.session_state.post_text:
    st.subheader("✍️ Generated Post")
    st.write(st.session_state.post_text)

if st.session_state.image_path:
    st.subheader("🖼️ Generated Image")
    img = Image.open(st.session_state.image_path)
    st.image(img, use_container_width=True)

# --------------------------------------------------
# STEP 4: POST TO LINKEDIN
# --------------------------------------------------
def get_user_urn(token):
    r = requests.get(
        "https://api.linkedin.com/v2/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    return f"urn:li:person:{r.json()['id']}"

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
        },
        timeout=10,
    ).json()

    upload_url = reg["value"]["uploadMechanism"][
        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
    ]["uploadUrl"]

    asset = reg["value"]["asset"]

    with open(image_path, "rb") as f:
        requests.put(upload_url, data=f, timeout=10)

    return asset

def post_to_linkedin(token, owner, text, asset):
    return requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "author": owner,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "IMAGE",
                    "media": [{"status": "READY", "media": asset}],
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        },
        timeout=10,
    )

if st.session_state.post_text and st.session_state.image_path:
    if st.button("🚀 Post on LinkedIn"):
        with st.spinner("Posting to LinkedIn..."):
            owner = get_user_urn(st.session_state.linkedin_token)
            asset = upload_image(
                st.session_state.linkedin_token,
                st.session_state.image_path,
                owner,
            )
            res = post_to_linkedin(
                st.session_state.linkedin_token,
                owner,
                st.session_state.post_text,
                asset,
            )

            if res.status_code == 201:
                st.success("🎉 Posted successfully on LinkedIn!")
            else:
                st.error("❌ Failed to post on LinkedIn")
