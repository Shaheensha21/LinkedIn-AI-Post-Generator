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

# ------------------- PAGE CONFIG -------------------
st.set_page_config(
    page_title="AI-Powered LinkedIn Post Generator",
    page_icon="🤖",
    layout="wide",
)

# ------------------- HARD SESSION STATE INIT (CRITICAL) -------------------
if "image" not in st.session_state:
    st.session_state["image"] = None

if "image_path" not in st.session_state:
    st.session_state["image_path"] = None

if "linkedin_post" not in st.session_state:
    st.session_state["linkedin_post"] = ""

if "generated" not in st.session_state:
    st.session_state["generated"] = False

if "linkedin_token" not in st.session_state:
    st.session_state["linkedin_token"] = None


# ------------------- LINKEDIN CONFIG -------------------
LINKEDIN_CLIENT_ID = st.secrets["LINKEDIN_CLIENT_ID"]
LINKEDIN_CLIENT_SECRET = st.secrets["LINKEDIN_CLIENT_SECRET"]
LINKEDIN_REDIRECT_URI = st.secrets["LINKEDIN_REDIRECT_URI"]

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
POST_URL = "https://api.linkedin.com/v2/ugcPosts"
UPLOAD_URL = "https://api.linkedin.com/v2/assets?action=registerUpload"
SCOPE = "openid profile email w_member_social"


# ------------------- OAUTH HELPERS -------------------
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


def upload_image_to_linkedin(image_path, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    register_payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": f"urn:li:person:{get_linkedin_urn(token)}",
            "serviceRelationships": [
                {"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}
            ],
        }
    }

    res = requests.post(UPLOAD_URL, headers=headers, json=register_payload)
    res.raise_for_status()
    upload_data = res.json()

    upload_url = upload_data["value"]["uploadMechanism"][
        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
    ]["uploadUrl"]

    asset_urn = upload_data["value"]["asset"]

    with open(image_path, "rb") as f:
        img_bytes = f.read()

    requests.put(upload_url, data=img_bytes, headers={"Authorization": f"Bearer {token}"})

    return asset_urn


def post_to_linkedin(text, image_path, token):
    author = f"urn:li:person:{get_linkedin_urn(token)}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    if image_path:
        asset_urn = upload_image_to_linkedin(image_path, token)
        payload = {
            "author": author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "IMAGE",
                    "media": [
                        {
                            "status": "READY",
                            "media": asset_urn,
                            "title": {"text": "AI Generated Image"},
                        }
                    ],
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }
    else:
        payload = {
            "author": author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

    res = requests.post(POST_URL, headers=headers, json=payload)
    res.raise_for_status()
    return res.json()


# ------------------- HANDLE OAUTH REDIRECT -------------------
query_params = st.query_params
if "code" in query_params and st.session_state["linkedin_token"] is None:
    with st.spinner("Connecting to LinkedIn..."):
        try:
            token = exchange_code_for_token(query_params["code"][0])
            st.session_state["linkedin_token"] = token
            st.success("✅ LinkedIn connected successfully!")
        except Exception as e:
            st.error(f"OAuth failed: {e}")


# ------------------- UI -------------------
st.title("🤖 AI-Powered LinkedIn Post Generator")

topic = st.text_input(
    "Enter your LinkedIn topic",
    "I successfully completed an AICTE internship on Employability Skills & AI",
)

if st.button("🚀 Generate Post & Image"):
    with st.spinner("Generating LinkedIn post..."):
        st.session_state["linkedin_post"] = generate_linkedin_post(topic)

    with st.spinner("Generating image..."):
        prompt = generate_image_prompt(st.session_state["linkedin_post"])
        path = generate_image(prompt)
        st.session_state["image_path"] = path
        st.session_state["image"] = Image.open(path)

    st.session_state["generated"] = True


# ------------------- OUTPUT -------------------
if st.session_state["generated"]:
    st.subheader("📄 LinkedIn Post")
    st.markdown(st.session_state["linkedin_post"])

    st.subheader("🖼 Generated Image")
    if st.session_state.get("image") is not None:
        st.image(st.session_state["image"], width=500)
    else:
        st.info("Image not generated yet.")

    col1, col2 = st.columns(2)

    with col1:
        if st.session_state["linkedin_token"] is None:
            st.markdown("### 🔐 Connect LinkedIn")
            st.markdown(f"[🔗 Login with LinkedIn]({get_linkedin_auth_url()})")
        else:
            st.success("✅ LinkedIn Connected")
            if st.button("📢 Post to LinkedIn"):
                with st.spinner("Posting..."):
                    try:
                        post_to_linkedin(
                            st.session_state["linkedin_post"],
                            st.session_state["image_path"],
                            st.session_state["linkedin_token"],
                        )
                        st.success("🎉 Posted successfully on LinkedIn!")
                    except Exception as e:
                        st.error(e)

    with col2:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            zipf.writestr("linkedin_post.txt", st.session_state["linkedin_post"])
            if st.session_state.get("image"):
                img_buf = io.BytesIO()
                st.session_state["image"].save(img_buf, format="PNG")
                zipf.writestr("linkedin_image.png", img_buf.getvalue())

        st.download_button(
            "⬇️ Download Post & Image",
            zip_buffer.getvalue(),
            "linkedin_content.zip",
            "application/zip",
        )
