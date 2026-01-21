import streamlit as st
from PIL import Image
import requests
from text_generator import generate_linkedin_post
from image_prompt_generator import generate_image_prompt
from image_generator import generate_image
import io

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="AI-Powered LinkedIn Post Generator",
    page_icon="🤖",
    layout="wide"
)

# ---------------- Load Secrets ----------------
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
HUGGINGFACE_API_KEY = st.secrets["HUGGINGFACE_API_KEY"]
CLIENT_ID = st.secrets["LINKEDIN_CLIENT_ID"]
CLIENT_SECRET = st.secrets["LINKEDIN_CLIENT_SECRET"]
REDIRECT_URI = st.secrets["LINKEDIN_REDIRECT_URI"]

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

# ---------------- Session State ----------------
defaults = {
    "generated": False,
    "linkedin_post": "",
    "image_path": None,
    "linkedin_logged_in": False,
    "linkedin_token": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------- OAuth Helpers ----------------
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
    r = requests.get("https://api.linkedin.com/v2/me", headers=headers)
    return f"urn:li:person:{r.json()['id']}"

def upload_image(token, image_path, owner_urn):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    register = {
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
        json=register
    )
    upload_url = r.json()["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    asset = r.json()["value"]["asset"]

    with open(image_path, "rb") as f:
        requests.put(upload_url, data=f.read())

    return asset

def create_post(token, owner_urn, text, asset):
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
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    return requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers=headers,
        json=payload
    ).status_code

# ---------------- UI ----------------
st.title("🤖 AI-Powered LinkedIn Content Generator")

topic = st.text_input("🔹 Enter LinkedIn topic", placeholder="Completed AICTE internship on AI & Digital Literacy")

# Generate Post & Image
if st.button("🚀 Generate Post & Image"):
    if topic.strip() == "":
        st.warning("Please enter a topic to generate content.")
    else:
        # Generate text
        st.session_state.linkedin_post = generate_linkedin_post(topic)
        # Generate image prompt
        img_prompt = generate_image_prompt(st.session_state.linkedin_post + " | professional, realistic, LinkedIn style")
        # Generate image
        st.session_state.image_path = generate_image(img_prompt)
        st.session_state.generated = True
        st.success("✅ Content generated successfully!")

# Display Generated Content
if st.session_state.generated:
    st.subheader("📝 Generated LinkedIn Post")
    st.text_area("LinkedIn Script", value=st.session_state.linkedin_post, height=180)
    st.subheader("🖼️ Generated Image")
    st.image(Image.open(st.session_state.image_path), width=520)

# ---------------- LinkedIn Login ----------------
st.divider()
st.subheader("🔐 LinkedIn Authorization")
login_url = (
    f"{AUTH_URL}?response_type=code"
    f"&client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&scope=w_member_social%20r_liteprofile"
)
st.markdown(f"[Login with LinkedIn]({login_url})")

params = st.experimental_get_query_params()
if "code" in params and not st.session_state.linkedin_logged_in:
    token = get_access_token(params["code"][0])
    if token:
        st.session_state.linkedin_token = token
        st.session_state.linkedin_logged_in = True
        st.success("LinkedIn Authorized")

# ---------------- Upload to LinkedIn ----------------
upload_disabled = not (st.session_state.generated and st.session_state.linkedin_logged_in)
if st.button("Upload to LinkedIn", disabled=upload_disabled):
    owner_urn = get_user_urn(st.session_state.linkedin_token)
    asset = upload_image(st.session_state.linkedin_token, st.session_state.image_path, owner_urn)
    status = create_post(st.session_state.linkedin_token, owner_urn, st.session_state.linkedin_post, asset)

    if status == 201:
        st.success("🎉 Posted successfully on LinkedIn!")
    else:
        st.error("❌ Failed to post on LinkedIn")
