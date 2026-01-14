import streamlit as st
from text_generator import generate_linkedin_post
from image_prompt_generator import generate_image_prompt
from image_generator import generate_image
from PIL import Image
import io
import zipfile
import requests
import secrets
import urllib.parse
import json

# ------------------- Streamlit Page Config -------------------
st.set_page_config(
    page_title="AI-Powered LinkedIn Post Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------- LinkedIn OAuth Config -------------------
LINKEDIN_CLIENT_ID = st.secrets["LINKEDIN_CLIENT_ID"]
LINKEDIN_CLIENT_SECRET = st.secrets["LINKEDIN_CLIENT_SECRET"]
LINKEDIN_REDIRECT_URI = st.secrets["LINKEDIN_REDIRECT_URI"]  # Must exactly match LinkedIn Authorized Redirect URL

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
POST_URL = "https://api.linkedin.com/v2/ugcPosts"
UPLOAD_URL = "https://api.linkedin.com/v2/assets?action=registerUpload"
SCOPE = "openid profile email w_member_social"

# ------------------- Session State Init -------------------
if "generated" not in st.session_state:
    st.session_state.generated = False
if "linkedin_token" not in st.session_state:
    st.session_state.linkedin_token = None
# --- Persistent OAuth state to fix security check ---
if "oauth_state" not in st.session_state:
    st.session_state.oauth_state = secrets.token_urlsafe(16)

# ------------------- OAuth Helpers -------------------
def get_linkedin_auth_url():
    state = st.session_state.oauth_state
    params = {
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,
        "redirect_uri": LINKEDIN_REDIRECT_URI,
        "scope": SCOPE,
        "state": state,
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
    response = requests.post(TOKEN_URL, data=data, headers=headers)
    response.raise_for_status()
    return response.json()["access_token"]

def get_linkedin_urn(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    res = requests.get("https://api.linkedin.com/v2/me", headers=headers)
    res.raise_for_status()
    return res.json()["id"]

def upload_image_to_linkedin(image_path, access_token):
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    # Step 1: Register upload
    register_payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": f"urn:li:person:{get_linkedin_urn(access_token)}",
            "serviceRelationships": [
                {"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}
            ]
        }
    }
    res = requests.post(UPLOAD_URL, headers=headers, data=json.dumps(register_payload))
    res.raise_for_status()
    upload_info = res.json()
    upload_url = upload_info["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    asset_urn = upload_info["value"]["asset"]

    # Step 2: Upload image bytes
    with open(image_path, "rb") as f:
        img_data = f.read()
    res2 = requests.put(upload_url, data=img_data, headers={"Authorization": f"Bearer {access_token}"})
    res2.raise_for_status()

    return asset_urn

def post_to_linkedin(content, image_path, access_token):
    author_urn = f"urn:li:person:{get_linkedin_urn(access_token)}"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    if image_path:
        asset_urn = upload_image_to_linkedin(image_path, access_token)
        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": content},
                    "shareMediaCategory": "IMAGE",
                    "media": [
                        {"status": "READY", "description": {"text": content}, "media": asset_urn, "title": {"text": "AI-Generated Image"}}
                    ]
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }
    else:
        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": content},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

    res = requests.post(POST_URL, headers=headers, data=json.dumps(payload))
    res.raise_for_status()
    return res.json()

# ------------------- Handle Redirect from LinkedIn -------------------
query_params = st.query_params
if "code" in query_params and st.session_state.linkedin_token is None:
    if query_params.get("state") != st.session_state.oauth_state:
        st.error("⚠️ OAuth security check failed. Please reconnect.")
    else:
        with st.spinner("Connecting to LinkedIn..."):
            token = exchange_code_for_token(query_params["code"])
            st.session_state.linkedin_token = token
            st.success("✅ LinkedIn connected successfully!")

# ------------------- UI -------------------
st.title("🤖 AI-Powered LinkedIn Content Generator")
st.markdown("Generate professional LinkedIn posts and images instantly!")

topic = st.text_input("Enter your LinkedIn topic:", "How AI is helping students build real-world projects")

# ------------------- Generate Content -------------------
if st.button("Generate Post & Image"):
    st.session_state.generated = True
    with st.spinner("Generating LinkedIn post..."):
        st.session_state.linkedin_post = generate_linkedin_post(topic)
    with st.spinner("Generating image prompt..."):
        prompt = generate_image_prompt(st.session_state.linkedin_post)
    with st.spinner("Generating image..."):
        path = generate_image(prompt)
        st.session_state.image = Image.open(path)
        st.session_state.image_path = path  # save path for LinkedIn upload

# ------------------- Output -------------------
if st.session_state.generated:
    st.subheader("🔹 Generated LinkedIn Post")
    st.markdown(st.session_state.linkedin_post)

    st.subheader("🔹 Generated Image")
    st.image(st.session_state.image, width=500)

    col1, col2 = st.columns(2)

    # ------------------- LinkedIn OAuth -------------------
    with col1:
        if st.session_state.linkedin_token is None:
            auth_url = get_linkedin_auth_url()
            st.markdown("### 🔐 Step 1: Connect to LinkedIn")
            st.markdown(f"[🔗 Connect to LinkedIn]({auth_url})")
        else:
            st.success("✅ LinkedIn Connected")
            st.info("Ready to post directly to LinkedIn 🚀")
            if st.button("Post to LinkedIn"):
                with st.spinner("Posting to LinkedIn..."):
                    try:
                        res = post_to_linkedin(st.session_state.linkedin_post, st.session_state.image_path, st.session_state.linkedin_token)
                        st.success("✅ Post published on LinkedIn!")
                        st.json(res)
                    except Exception as e:
                        st.error(f"❌ Failed to post: {e}")

    # ------------------- Download -------------------
    with col2:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            zipf.writestr("linkedin_post.txt", st.session_state.linkedin_post)
            img_bytes = io.BytesIO()
            st.session_state.image.save(img_bytes, format="WEBP")
            zipf.writestr("linkedin_image.webp", img_bytes.getvalue())
        st.download_button("⬇️ Download Post & Image", zip_buffer.getvalue(), "linkedin_content.zip", "application/zip")
