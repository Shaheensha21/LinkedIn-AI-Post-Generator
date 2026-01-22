import streamlit as st
from text_generator import generate_linkedin_post
from image_prompt_generator import generate_flux_image_prompt
from image_generator import generate_image
from PIL import Image

# -------------------------------
# SESSION STATE INIT
# -------------------------------
if "linkedin_logged_in" not in st.session_state:
    st.session_state.linkedin_logged_in = False

if "linkedin_token" not in st.session_state:
    st.session_state.linkedin_token = None

if "generated_text" not in st.session_state:
    st.session_state.generated_text = ""

if "image_path" not in st.session_state:
    st.session_state.image_path = None

if "has_content" not in st.session_state:
    st.session_state.has_content = False

# -------------------------------
# STEP 0: LINKEDIN LOGIN PROMPT
# -------------------------------
st.title("🤖 AI LinkedIn Post Generator")
st.subheader("Step 1: Login with LinkedIn")

if not st.session_state.linkedin_logged_in:
    st.info("You must login first to post on LinkedIn.")
    st.markdown("[🔑 Login with LinkedIn](./1_oauth_success)")

else:
    st.success("✅ Logged in with LinkedIn!")

    # -------------------------------
    # STEP 2: GENERATE CONTENT
    # -------------------------------
    st.subheader("Step 2: Generate Post & Image")
    topic = st.text_input("Enter LinkedIn post topic:")

    if st.button("Generate Post & Image"):
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
        st.markdown("### ✍️ Generated Post")
        st.write(st.session_state.generated_text)
        st.download_button("⬇️ Download Post Text", st.session_state.generated_text, file_name="linkedin_post.txt")

        st.markdown("### 🖼️ Generated Image")
        img = Image.open(st.session_state.image_path)
        st.image(img, use_column_width=True)
        with open(st.session_state.image_path, "rb") as f:
            st.download_button("⬇️ Download Image", f, file_name="linkedin_post_image.webp")

        # -------------------------------
        # STEP 3: POST TO LINKEDIN
        # -------------------------------
        st.subheader("Step 3: Post to LinkedIn")
        if st.button("📤 Post on LinkedIn"):
            # call your LinkedIn post function here using st.session_state.linkedin_token
            st.success("🎉 Successfully posted on LinkedIn!")
