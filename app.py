import streamlit as st
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

# ---------------- Session State Init ----------------
defaults = {
    "generated": False,
    "linkedin_post": "",
    "image": None,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------- UI ----------------
st.title("🤖 AI-Powered LinkedIn Content Generator")
st.markdown(
    "Generate **professional LinkedIn posts and images** using AI.\n\n"
    "✅ No OAuth\n"
    "✅ No API restrictions\n"
    "✅ LinkedIn-compliant sharing"
)

topic = st.text_input(
    "🔹 Enter your LinkedIn topic",
    placeholder="Completed AICTE internship on AI & Digital Literacy"
)

# ---------------- Generate Content ----------------
if st.button("🚀 Generate Post & Image"):
    if not topic.strip():
        st.warning("Please enter a topic")
    else:
        st.session_state.generated = True

        with st.spinner("Generating LinkedIn post..."):
            st.session_state.linkedin_post = generate_linkedin_post(topic)

        with st.spinner("Generating image prompt..."):
            img_prompt = generate_image_prompt(st.session_state.linkedin_post)

        with st.spinner("Generating image..."):
            img_bytes = generate_image(img_prompt)
            st.session_state.image = Image.open(io.BytesIO(img_bytes))

        st.success("✅ Content generated successfully!")

# ---------------- Output ----------------
if st.session_state.generated:

    st.subheader("📝 Generated LinkedIn Post")
    st.markdown(st.session_state.linkedin_post)

    st.subheader("🖼️ Generated Image")
    if st.session_state.image:
        st.image(st.session_state.image, width=500)

    col1, col2 = st.columns(2)

    # -------- Open LinkedIn Section --------
    with col1:
        st.subheader("🚀 Post on LinkedIn")

        encoded_text = urllib.parse.quote(st.session_state.linkedin_post)

        linkedin_share_url = (
            "https://www.linkedin.com/sharing/share-offsite/?url="
            + encoded_text
        )

        st.markdown(
            f"""
            <a href="{linkedin_share_url}" target="_blank">
                <button style="
                    background-color:#0A66C2;
                    color:white;
                    padding:12px 20px;
                    border:none;
                    border-radius:6px;
                    font-size:16px;
                    cursor:pointer;">
                    🔗 Open LinkedIn & Post
                </button>
            </a>
            """,
            unsafe_allow_html=True
        )

        st.info(
            "Steps:\n"
            "1️⃣ LinkedIn opens in new tab\n"
            "2️⃣ Login if required\n"
            "3️⃣ Post text is pre-filled\n"
            "4️⃣ Upload the generated image\n"
            "5️⃣ Click Post"
        )

    # -------- Download Section --------
    with col2:
        st.subheader("⬇️ Download Content")

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            zipf.writestr(
                "linkedin_post.txt",
                st.session_state.linkedin_post
            )

            if st.session_state.image:
                img_bytes = io.BytesIO()
                st.session_state.image.save(img_bytes, format="PNG")
                zipf.writestr(
                    "linkedin_image.png",
                    img_bytes.getvalue()
                )

        st.download_button(
            "📦 Download Post & Image (ZIP)",
            zip_buffer.getvalue(),
            "linkedin_content.zip",
            "application/zip"
        )
