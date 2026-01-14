import streamlit as st
import requests
import urllib.parse
from PIL import Image
import io
import zipfile

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="AI-Powered LinkedIn Post Generator",
    page_icon="🤖",
    layout="wide"
)

# ---------------- Imports (your existing files) ----------------
from text_generator import generate_linkedin_post
from image_prompt_generator import generate_image_prompt
from image_generator import generate_image

# ---------------- Secrets ----------------
CLIENT_ID = st.secrets["LINKEDIN_CLIENT_ID"]
CLIENT_SECRET = st.secrets["LINKEDIN_CLIENT_SECRET"]
REDIRECT_URI = st.secrets["LINKEDIN_REDIRECT_URI"]

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

# ✅ CORRECT LinkedIn scopes
SCOPE = "r_liteprofile r_emailaddress w_member_social"

# ---------------- Session State Init ----------------
defaults = {
    "linkedin_token": None,
    "generated": False,
    "linkedin_post": "",
    "image": None,
    "image_path": None,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------- OAuth URL ----------------
def linkedin_auth_url():
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

# ---------------- Token Exchange ----------------
def exchange_token(code):
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    res = requests.post(TOKEN_URL, data=data, headers=headers)
    res.raise_for_status()
    return res.json()["access_token"]

# ---------------- Handle OAuth Redirect ----------------
params = st.query_params
if "code" in params and st.session_state.linkedin_token is None:
    try:
        token = exchange_token(params["code"])
        st.session_state.linkedin_token = token
        st.query_params.clear()
        st.success("✅ LinkedIn connected successfully!")
    except Exception as e:
        st.error(f"OAuth failed: {e}")

# ---------------- UI ----------------
st.title("🤖 AI-Powered LinkedIn Content Generator")
st.markdown("Generate **professional LinkedIn posts and images** using AI.")

topic = st.text_input(
    "Enter your LinkedIn topic:",
    "How AI is helping students build real-world projects"
)

# ---------------- Generate Content ----------------
if st.button("🚀 Generate Post & Image"):
    st.session_state.generated = True

    with st.spinner("Generating LinkedIn post..."):
        st.session_state.linkedin_post = generate_linkedin_post(topic)

    with st.spinner("Generating image prompt..."):
        img_prompt = generate_image_prompt(st.session_state.linkedin_post)

    with st.spinner("Generating image..."):
        path = generate_image(img_prompt)
        st.session_state.image_path = path
        st.session_state.image = Image.open(path)

    st.success("Content generated successfully!")

# ---------------- Output ----------------
if st.session_state.generated:
    st.subheader("🔹 Generated LinkedIn Post")
    st.markdown(st.session_state.linkedin_post)

    st.subheader("🔹 Generated Image")
    if st.session_state.image is not None:
        st.image(st.session_state.image, width=500)

    col1, col2 = st.columns(2)

    # -------- OAuth Section --------
    with col1:
        if st.session_state.linkedin_token is None:
            st.markdown("### 🔐 Connect LinkedIn")
            st.markdown(f"[🔗 Connect to LinkedIn]({linkedin_auth_url()})")
        else:
            st.success("✅ LinkedIn Connected")
            st.info("You are ready to post on LinkedIn 🚀")

    # -------- Download Section --------
    with col2:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            zipf.writestr("linkedin_post.txt", st.session_state.linkedin_post)

            if st.session_state.image is not None:
                img_bytes = io.BytesIO()
                st.session_state.image.save(img_bytes, format="PNG")
                zipf.writestr("linkedin_image.png", img_bytes.getvalue())

        st.download_button(
            "⬇️ Download Post & Image",
            zip_buffer.getvalue(),
            "linkedin_content.zip",
            "application/zip"
        )
