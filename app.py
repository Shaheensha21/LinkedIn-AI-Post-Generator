import streamlit as st
from PIL import Image
import requests

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

# -------------------------------
# SECRETS
# -------------------------------
CLIENT_ID = st.secrets["LINKEDIN_CLIENT_ID"]
CLIENT_SECRET = st.secrets["LINKEDIN_CLIENT_SECRET"]
REDIRECT_URI = st.secrets["LINKEDIN_REDIRECT_URI"]  # MUST be oauth success page
AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"

# -------------------------------
# SESSION STATE INIT
# -------------------------------
defaults = {
    "linkedin_token": None,
    "linkedin_logged_in": False,
    "generated_text": "",
    "image_path": None,
    "has_content": False,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -------------------------------
# STEP 1: AUTH STATUS
# -------------------------------
if st.session_state.linkedin_logged_in:
    st.success("🔐 Authentication successful! You can now generate & post.")
else:
    login_url = (
        f"{AUTH_URL}"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=openid%20profile%20w_member_social"
    )

    st.warning("⚠️ You must login to LinkedIn first.")
    st.markdown(f"👉 [Login with LinkedIn]({login_url})")
    st.stop()  # ⛔ STOP here until login is done

# -------------------------------
# STEP 2: GENERATE POST & IMAGE
# -------------------------------
st.divider()
st.subheader("📝 Step 2: Generate LinkedIn Post & Image")

topic = st.text_input(
    "Enter LinkedIn post topic",
    "How AI is helping students build real-world projects"
)

if st.button("✨ Generate Post & Image"):
    if topic.strip() == "":
        st.warning("⚠️ Please enter a topic")
    else:
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
# STEP 3: POST TO LINKEDIN
# -------------------------------
if st.session_state.has_content:
    st.divider()
    st.subheader("🚀 Step 3: Post to LinkedIn")

    def get_user_urn(token):
        r = requests.get(
            "https://api.linkedin.com/v2/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        r.raise_for_status()
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

    if st.button("📤 Post on LinkedIn"):
        with st.spinner("Posting to LinkedIn..."):
            try:
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
                    st.success("🎉 Successfully posted on LinkedIn!")
                else:
                    st.error(f"❌ Failed to post ({res.status_code})")

            except Exception as e:
                st.error(f"❌ Error: {e}")
