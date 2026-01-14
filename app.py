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
st.markdown("Create professional LinkedIn posts and visuals using AI.")

topic = st.text_input(
    "🔹 Enter your LinkedIn topic",
    placeholder="Completed AICTE internship on AI & Digital Literacy"
)
with st.expander("ℹ️ Project Notes & OAuth Issues"):
    st.markdown(
        """
        **LinkedIn OAuth & API Real-World Problem**  

        - LinkedIn OAuth is a protocol for letting apps post on behalf of a user.  
        - Our project aimed to post directly via Streamlit using LinkedIn API.  
        - However, LinkedIn **restricts direct posting for unverified apps** due to security and policy reasons.  
        - The `w_member_social` scope requires **OAuth tokens with proper REST API approval**.  
        - Our attempts returned errors like:  
          `OAuth security check failed` or `401 Unauthorized`.  
        - **Solution:** Instead of direct posting, we now:  
          1️⃣ Generate AI-based post & image in Streamlit.  
          2️⃣ Provide a copy script and download image.  
          3️⃣ Open LinkedIn share page where the user can manually post.  
        
        This demonstrates understanding of real-world API restrictions and designing a compliant workflow.
        """
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
            # Professional realistic image prompt
            img_prompt = generate_image_prompt(
                st.session_state.linkedin_post + 
                " --style professional, realistic, high-quality, modern office, AI theme"
            )

        with st.spinner("Generating image..."):
            path = generate_image(img_prompt)  # returns file path
            st.session_state.image_path = path
            st.session_state.image = Image.open(path)

        st.success("Content generated successfully!")

# ---------------- Output ----------------
if st.session_state.generated:

    st.subheader("📝 Generated LinkedIn Post")
    st.text_area(
        "Copy your LinkedIn script here",
        st.session_state.linkedin_post,
        height=150
    )

    st.subheader("🖼️ Generated Image")
    if st.session_state.image is not None:
        st.image(st.session_state.image, width=500)

    col1, col2, col3 = st.columns([1, 1, 1])

    # -------- Copy Post Button --------
    with col1:
        st.download_button(
            label="📋 Copy Script",
            data=st.session_state.linkedin_post,
            file_name="linkedin_post.txt",
            mime="text/plain"
        )

    # -------- Download Image Button --------
    with col2:
        if st.session_state.image is not None:
            img_bytes = io.BytesIO()
            st.session_state.image.save(img_bytes, format="PNG")
            st.download_button(
                label="🖼️ Download Image",
                data=img_bytes.getvalue(),
                file_name="linkedin_image.png",
                mime="image/png"
            )

    # -------- Open LinkedIn Section --------
    with col3:
        st.subheader("🚀 Post to LinkedIn")
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
                    padding:12px 20px;
                    border:none;
                    border-radius:6px;
                    font-size:16px;
                    cursor:pointer;">
                    🔗 Open LinkedIn
                </button>
            </a>
            """,
            unsafe_allow_html=True
        )

        st.info(
            "Steps:\n"
            "1️⃣ LinkedIn opens in a new tab\n"
            "2️⃣ Copy the script and download the image\n"
            "3️⃣ Upload script & image on LinkedIn and click Post"
        )

    # -------- Final Note --------
    st.markdown(
        """
        **Note:**  
        - Direct posting via OAuth requires LinkedIn REST API access.  
        - LinkedIn policies are strict; third-party apps cannot post automatically without approval.  
        - This workflow ensures compliance while allowing professional AI-generated content.
        """
    )
