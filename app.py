import streamlit as st

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(page_title="AI Post Generator", layout="centered")

# -------------------------------
# Session State Initialization
# -------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "generated_post" not in st.session_state:
    st.session_state.generated_post = ""

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
        # Simple demo validation (you can replace this)
        if username and password:
            st.session_state.logged_in = True
            st.success("Login successful ✅")
        else:
            st.error("Please enter username and password")


# -------------------------------
# POST GENERATION SECTION
# -------------------------------
def generation_section():
    st.title("✍️ Generate LinkedIn Post")

    topic = st.text_input("Enter post topic")

    if st.button("Generate Post"):
        if topic:
            # Dummy AI-generated content (replace with Gemini/OpenAI later)
            st.session_state.generated_post = (
                f"🚀 Excited to share insights on **{topic}**!\n\n"
                f"This topic plays a crucial role in today’s tech-driven world. "
                f"Continuous learning and innovation help us stay ahead.\n\n"
                f"#Learning #Growth #Technology"
            )
            st.success("Post generated successfully ✅")
        else:
            st.warning("Please enter a topic")

    if st.session_state.generated_post:
        st.text_area(
            "Generated Post",
            st.session_state.generated_post,
            height=200
        )


# -------------------------------
# POSTING SECTION
# -------------------------------
def posting_section():
    st.title("📤 Post to Platform")

    if st.button("Post Now"):
        # Simulated posting logic
        st.session_state.posted = True
        st.success("Post published successfully 🎉")

    if st.session_state.posted:
        st.info("✅ Your post has been shared!")


# -------------------------------
# MAIN FLOW (NO REFRESH)
# -------------------------------
if not st.session_state.logged_in:
    login_section()
else:
    generation_section()
    if st.session_state.generated_post:
        posting_section()
