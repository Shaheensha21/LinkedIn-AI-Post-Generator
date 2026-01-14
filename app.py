import streamlit as st
import urllib.parse
from PIL import Image
import io

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="AI-Powered LinkedIn Post Generator",
    page_icon="🤖",
    layout="wide"
)

# ---------------- Your existing modules ----------------
from text_generator import generate_linkedin_post
from image_prompt_generator import generate_image_prompt
from image_generator import generate_image

# ---------------- Session State Init ----------------
defaults = {
    "generated": False,
    "linkedin_post": "",
    "image": None,
    "image_path": None,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------- UI ----------------
st.title("🤖 AI-Powered LinkedIn Content Generator")
st.markdown(
    "Create **professional LinkedIn posts and visuals** using AI. "
    "Designed with real-world platform constraints in mind."
)

topic = st.text_input(
    "🔹 Enter your LinkedIn topic",
    placeholder="Completed AICTE internship on AI & Digital Literacy"
)

# ---------------- Info / Explanation Section ----------------
with st.expander("ℹ️ Project Notes – OAuth & Real-World API Challenges"):
    st.markdown(
        """
        **Why direct LinkedIn posting is not enabled in this app**

        - LinkedIn provides OAuth and REST APIs for posting on behalf of users.
        - However, **direct posting (`w_member_social`) is restricted to approved & verified applications**.
        - Unverified third-party apps face errors such as:
          - OAuth security check failed  
          - 401 Unauthorized  
          - Redirect validation issues
        - These are **policy-level restrictions**, not coding mistakes.

        **How this project solves the real-world problem**

        - AI generates professional post content and images.
        - Users manually post using LinkedIn’s official UI.
        - This approach is:
          - Platform-compliant
          - Secure
          - Reliable
          - Interview-ready (real-world engineering decision)

        This demonstrates **practical API awareness and system design**, not just automation.
        """
    )

# ---------------- Generate Content ----------------
if st.button("🚀 Generate Post & Image"):
    if not topic.strip():
        st.warning("Please enter a topic to generate content.")
    else:
        st.session_state.generated = True

        with st.spinner("Generating LinkedIn post..."):
            st.session_state.linkedin_post = generate_linkedin_post(topic)

        with st.spinner("Generating image prompt..."):
            img_prompt = generate_image_prompt(
                st.session_state.linkedin_post
                + " | professional, realistic, high-quality, modern office, AI theme, LinkedIn style"
            )

        with st.spinner("Generating image..."):
            path = generate_image(img_prompt)
            st.session_state.image_path = path
            st.session_state.image = Image.open(path)

        st.success("✅ Content generated successfully!")

# ---------------- Output ----------------
if st.session_state.generated:

    st.divider()

    # -------- Post Section --------
    st.subheader("📝 Generated LinkedIn Post")
    st.text_area(
        label="LinkedIn Script (copy & edit if needed)",
        value=st.session_state.linkedin_post,
        height=180
    )

    # -------- Image Section --------
    st.subheader("🖼️ Generated Image")
    if st.session_state.image is not None:
        st.image(st.session_state.image, width=520)

    st.divider()

    # -------- Actions --------
    st.subheader("🚀 How to Post on LinkedIn")

    col1, col2, col3 = st.columns(3)

    # Step 1: Download Script
    with col1:
        st.markdown("**Step 1: Download Script**")
        st.download_button(
            label="📄 Download Post Text",
            data=st.session_state.linkedin_post,
            file_name="linkedin_post.txt",
            mime="text/plain"
        )

    # Step 2: Download Image
    with col2:
        st.markdown("**Step 2: Download Image**")
        if st.session_state.image is not None:
            img_bytes = io.BytesIO()
            st.session_state.image.save(img_bytes, format="PNG")
            st.download_button(
                label="🖼️ Download Image",
                data=img_bytes.getvalue(),
                file_name="linkedin_image.png",
                mime="image/png"
            )

    # Step 3: Open LinkedIn
    with col3:
        st.markdown("**Step 3: Open LinkedIn**")
        encoded_text = urllib.parse.quote(st.session_state.linkedin_post)
        linkedin_share_url = (
            "https://www.linkedin.com/sharing/share-offsite/?url=" + encoded_text
        )

        st.markdown(
            f"""
            <a href="{linkedin_share_url}" target="_blank">
                <button style="
                    background-color:#0A66C2;
                    color:white;
                    padding:12px 22px;
                    border:none;
                    border-radius:6px;
                    font-size:16px;
                    cursor:pointer;
                    width:100%;">
                    🔗 Open LinkedIn
                </button>
            </a>
            """,
            unsafe_allow_html=True
        )

    # -------- Final Note --------
    st.divider()
    st.markdown(
        """
        **Important Note**

        - Automated posting requires LinkedIn REST API approval and strict OAuth verification.
        - These permissions are **not granted to personal or demo applications**.
        - This project intentionally follows a **LinkedIn-compliant workflow**.
        - Focus is on **AI content generation, UX, and real-world API constraints**.
        """
    )
