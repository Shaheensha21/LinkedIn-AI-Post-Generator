import streamlit as st
import urllib.parse
import requests
from PIL import Image
import io

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="AI-Powered LinkedIn Post Generator",
    page_icon="🤖",
    layout="wide"
)

# ---------------- AI Modules ----------------
from text_generator import generate_linkedin_post
from image_prompt_generator import generate_image_prompt
from image_generator import generate_image

# ---------------- Secrets ----------------
CLIENT_ID = st.secrets["LINKEDIN_CLIENT_ID"]
CLIENT_SECRET = st.secrets["LINKEDIN_CLIENT_SECRET"]
REDIRECT_URI = st.secrets["LINKEDIN_REDIRECT_URI"]

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

# ---------------- Session State ----------------
defaults = {
    "generated": False,
    "linkedin_post": "",
    "image": None,
    "image_path": None,
    "linkedin_token": None,
    "linkedin_logged_in": False
}

for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# ---------------- UI ----------------
st.title("🤖 AI-Powered LinkedIn Content Generator")
st.markdown(
    "Create **professional LinkedIn posts and visuals** and post them **directly to LinkedIn** using OAuth."
)

topic = st.text_input(
    "🔹 Enter your LinkedIn topic",
    placeholder="Completed AICTE internship on AI & Digital Literacy"
)

# ---------------- Generate Content ----------------
if st.button("🚀 Generate Post & Image"):
    if not topic.strip():
        st.warning("Please enter a topic.")
    else:
        with st.spinner("Generating LinkedIn post..."):
            st.session_state.linkedin_post = generate_linkedin_post(topic)

        with st.spinner("Generating image prompt..."):
            img_prompt = generate_image_prompt(
                st.session_state.linkedin_post +
                " | professional, realistic, LinkedIn style"
            )

        with st.spinner("Generating image..."):
            path = generate_image(img_prompt)
            st.session_state.image_path = path
            st.session_state.image = Image.open(path)

        st.session_state.generated = True
        st.success("✅ Content generated successfully!")

# ---------------- Display Output ----------------
if st.session_state.generated:

    st.divider()
    st.subheader("📝 Generated LinkedIn Post")

    st.text_area(
        "LinkedIn Script",
        value=st.session_state.linkedin_post,
        height=200
    )

    st.subheader("🖼️ Generated Image")
    st.image(st.session_state.image, width=520)

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

# ---------------- OAuth Callback ----------------
params = st.query_params

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

def upload_image(token, image_path, owner):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    register_payload = {
        "registerUploadRequest": {
            "owner": owner,
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

def create_post(token, owner, text, asset):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    payload = {
        "author": owner,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "IMAGE",
                "media": [{"status": "READY", "media": asset}]
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

if "code" in params and not st.session_state.linkedin_logged_in:
    token = get_access_token(params["code"])
    if token:
        st.session_state.linkedin_token = token
        st.session_state.linkedin_logged_in = True
        st.query_params.clear()
        st.success("✅ LinkedIn authenticated!")

# ---------------- Post to LinkedIn ----------------
if st.session_state.linkedin_logged_in and st.session_state.generated:
    if st.button("🚀 Post Directly to LinkedIn"):
        with st.spinner("Posting to LinkedIn..."):
            owner = get_user_urn(st.session_state.linkedin_token)
            asset = upload_image(
                st.session_state.linkedin_token,
                st.session_state.image_path,
                owner
            )
            status = create_post(
                st.session_state.linkedin_token,
                owner,
                st.session_state.linkedin_post,
                asset
            )

        if status == 201:
            st.success("🎉 Posted successfully on LinkedIn!")
        else:
            st.error("❌ Failed to post on LinkedIn")
