import streamlit as st

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(page_title="AI Post & Image Generator", layout="centered")

# -------------------------------
# Initialize Session State
# -------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "generated_post" not in st.session_state:
    st.session_state.generated_post = ""
if "generated_image_prompt" not in st.session_state:
    st.session_state.generated_image_prompt = ""
if "posted" not in st.session_state:
    st.session_state.posted = False

# -------------------------------
# LOGIN SECTION
# -------------------------------
def login_section():
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username and password:
            st.session_state.logged_in = True
            st.success(f"Login successful ✅ Welcome {username}")
        else:
            st.error("Please enter username and password")

# -------------------------------
# POST GENERATION SECTION
# -------------------------------
def generate_post(topic: str):
    # Dummy AI-generated content
    return (
        f"🚀 Excited to share insights on **{topic}**!\n\n"
        f"This topic is crucial in today’s tech world. "
        f"Continuous learning and innovation help us stay ahead.\n\n"
        f"#Learning #Growth #Technology"
    )

def generate_image_prompt(topic: str):
    # Dummy AI image prompt
    return f"A professional, creative, realistic image representing: {topic}"

def generation_section():
    st.title("✍️ Generate LinkedIn Post & Image Prompt")
    topic = st.text_input("Enter topic for post and image")

    if st.button("Generate Post & Image Prompt"):
        if topic:
            st.session_state.generated_post = generate_post(topic)
            st.session_state.generated_image_prompt = generate_image_prompt(topic)
            st.success("Post and Image Prompt generated successfully ✅")
        else:
            st.warning("Please enter a topic")

    if st.session_state.generated_post:
        st.subheader("📝 Generated Post")
        st.text_area("Post", st.session_state.generated_post, height=200)

    if st.session_state.generated_image_prompt:
        st.subheader("🖼️ Generated Image Prompt")
        st.text_area("Image Prompt", st.session_state.generated_image_prompt, height=100)

# -------------------------------
# POSTING SECTION
# -------------------------------
def posting_section():
    st.title("📤 Post / Share Section")
    if st.button("Post Now"):
        # Simulated posting
        st.session_state.posted = True
        st.success("Post published successfully 🎉")

    if st.session_state.posted:
        st.info("✅ Your post has been shared!")

# -------------------------------
# MAIN FLOW
# -------------------------------
if not st.session_state.logged_in:
    login_section()
else:
    generation_section()
    if st.session_state.generated_post:
        posting_section()
