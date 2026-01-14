import streamlit as st
from text_generator import generate_linkedin_post
from image_prompt_generator import generate_image_prompt
from image_generator import generate_image
from PIL import Image
import io
import zipfile
import requests
import urllib.parse
import json

# ------------------- Page Config -------------------
st.set_page_config(
    page_title="AI-Powered LinkedIn Post Generator",
    page_icon="🤖",
    layout="wide"
)

# ------------------- LinkedIn Config -------------------
LINKEDIN_CLIENT_ID = st.secrets["LINKEDIN_CLIENT_ID"]
LINKEDIN_CLIENT_SECRET = st.secrets["LINKEDIN_CLIENT_SECRET"]
LINKEDIN_REDIRECT_URI = st.secrets["LINKEDIN_REDIRECT_URI"]

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
POST_URL = "https://api.linkedin.com/v2/ugcPosts"
UPLOAD_URL = "https://api.linkedin.com/v2/assets?action=registerUpload"
SCOPE = "openid profile email w_member_social"

# ------------------- Session State Init (CRITICAL) -------------------
if "generated" not in st.session_state:
    st.session_state.generated = False

if "linkedin_token" not in st.session_state:
    st.session_state.linkedin_token = None

if "linkedin_post" not in st.session_state:
    st.session_state.linkedin_post = ""

if "image" not in st.session_state:
    st.session_state.image = None

if "image_path" not in st.session_state:
    st.session_state.image_path = None

# ------------------- OAuth Helpers -------------------
def get_linkedin_auth_url():
    params = {
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,
        "redirect_uri": LINKEDIN_REDIRECT_URI,
        "scope": SCOPE,
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

def exchange_code_for_token(code):
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": LINKEDIN_REDIRECT_URI,
        "client_id": LINKEDIN_CLIENT_ID,
        "client_secret": LINKEDIN_CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    res = requests.post(TOKEN_URL, data=data, headers=headers)
    res.raise_for_status()
    return res.json()["access_token"]

def get_linkedin_urn(token):
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get("https://api.linkedin.com/v2/me", headers=headers)
    res.raise_for_status()
    return res.json()["id"]

def upload_image(image_path, token):
    owner = f"urn:li:person:{get_linkedin_urn(token)}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    register_payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": owner,
            "serviceRelationships": [
                {"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}
            ]
        }
    }

    res = requests.post(UPLOAD_URL, headers=headers, data=json.dumps(register_payload))
    res.raise_for_status()

    upload_url = res.json()["value"]["uploadMechanism"][
        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
    ]["uploadUrl"]

    asset = res.json()["value"]["asset"]

    with open(image_path, "rb") as f:
        img_data = f.read()

    requests.put(upload_url, data=img_data)

    return asset

def post_to_linkedin(text, image_path, token):
    author = f"urn:li:person:{get_linkedin_urn(token)}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    asset_urn = upload_image(image_path, token)

    payload = {
        "author": author,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "IMAGE",
                "media": [{
                    "status": "READY",
                    "media": asset_urn,
                    "title": {"text": "AI Generated Image"}
                }]
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }

    res = requests.post(POST_URL, headers=headers, data=json.dumps(payload))
    res.raise_for_status()

# ------------------- Handle OAuth Redirect -------------------
query_params = st.query_params

if "code" in query_params and st.session_state.linkedin_token is None:
    with st.spinner("Connecting to LinkedIn..."):
        try:
            st.session_state.linkedin_token = exchange_code_for_token(query_params["code"][0])
            st.success("✅ LinkedIn connected successfully!")
        except Exception as e:
            st.error(f"❌ LinkedIn auth failed: {e}")

# ------------------- UI -------------------
st.title("🤖 AI-Powered LinkedIn Content Generator")

topic = st.text_input(
    "Enter your LinkedIn topic:",
    "How AI is helping students build real-world projects"
)

if st.button("Generate Post & Image"):
    st.session_state.generated = True
    st.session_state.linkedin_post = generate_linkedin_post(topic)
    prompt = generate_image_prompt(st.session_state.linkedin_post)
    path = generate_image(prompt)
    st.session_state.image = Image.open(path)
    st.session_state.image_path = path

# ------------------- Output -------------------
if st.session_state.generated:
    st.subheader("🔹 Generated LinkedIn Post")
    st.markdown(st.session_state.linkedin_post)

    st.subheader("🔹 Generated Image")
    if st.session_state.image:
        st.image(st.session_state.image, width=500)

    if st.session_state.linkedin_token is None:
        st.markdown("### 🔐 Connect to LinkedIn")
        st.markdown(f"[🔗 Login with LinkedIn]({get_linkedin_auth_url()})")
    else:
        if st.button("🚀 Post to LinkedIn"):
            with st.spinner("Posting to LinkedIn..."):
                post_to_linkedin(
                    st.session_state.linkedin_post,
                    st.session_state.image_path,
                    st.session_state.linkedin_token
                )
                st.success("✅ Posted successfully on LinkedIn!")

# ------------------- Download -------------------
if st.session_state.generated:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        zipf.writestr("linkedin_post.txt", st.session_state.linkedin_post)
        if st.session_state.image:
            img_bytes = io.BytesIO()
            st.session_state.image.save(img_bytes, format="PNG")
            zipf.writestr("linkedin_image.png", img_bytes.getvalue())

    st.download_button(
        "⬇️ Download Post & Image",
        zip_buffer.getvalue(),
        "linkedin_content.zip",
        "application/zip"
    )
