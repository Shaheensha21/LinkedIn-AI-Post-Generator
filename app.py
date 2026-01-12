import streamlit as st

# MUST be first Streamlit command
st.set_page_config(
    page_title="AI-Powered LinkedIn Post Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

from text_generator import generate_linkedin_post
from image_prompt_generator import generate_image_prompt
from image_generator import generate_image
from PIL import Image
import io
import zipfile
import time

# ------------------- Session State Init -------------------
if "generated" not in st.session_state:
    st.session_state.generated = False

if "linkedin_stage" not in st.session_state:
    st.session_state.linkedin_stage = "disconnected"

# ------------------- UI -------------------
st.title("🤖 AI-Powered LinkedIn Content Generator")
st.markdown("Generate professional LinkedIn posts and images instantly!")

topic = st.text_input(
    "Enter your LinkedIn topic here:",
    "How AI is helping students build real-world projects"
)

# ------------------- Generate -------------------
if st.button("Generate Post & Image"):
    st.session_state.generated = True

    with st.spinner("Generating LinkedIn post..."):
        st.session_state.linkedin_post = generate_linkedin_post(topic)

    with st.spinner("Generating image prompt..."):
        prompt = generate_image_prompt(st.session_state.linkedin_post)

    with st.spinner("Generating image..."):
        path = generate_image(prompt)
        st.session_state.image = Image.open(path)

# ------------------- Output -------------------
if st.session_state.generated:

    st.subheader("🔹 Generated LinkedIn Post")
    st.markdown(st.session_state.linkedin_post)

    st.subheader("🔹 Generated Image")
    st.image(st.session_state.image, width=500)

    col1, col2 = st.columns(2)

    # LinkedIn OAuth Demo
    with col1:
        if st.session_state.linkedin_stage == "disconnected":
            if st.button("Connect to LinkedIn (Demo)"):
                st.session_state.linkedin_stage = "redirect"
                st.rerun()

        elif st.session_state.linkedin_stage == "redirect":
            time.sleep(1)
            st.session_state.linkedin_stage = "permission"
            st.rerun()

        elif st.session_state.linkedin_stage == "permission":
            if st.button("Allow Permissions (Demo)"):
                st.session_state.linkedin_stage = "connected"
                st.rerun()

        elif st.session_state.linkedin_stage == "connected":
            st.success("✅ LinkedIn Connected (Demo Mode)")

    # Download
    with col2:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            zipf.writestr("linkedin_post.txt", st.session_state.linkedin_post)

            img_bytes = io.BytesIO()
            st.session_state.image.save(img_bytes, format="WEBP")
            zipf.writestr("linkedin_image.webp", img_bytes.getvalue())

        st.download_button(
            "⬇️ Download Post & Image",
            zip_buffer.getvalue(),
            "linkedin_content.zip",
            "application/zip"
        )
