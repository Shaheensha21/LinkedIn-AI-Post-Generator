import streamlit as st
from text_generator import generate_linkedin_post
from image_prompt_generator import generate_image_prompt
from image_generator import generate_image

# -------------------------------
# Streamlit App UI
# -------------------------------
st.set_page_config(page_title="AI LinkedIn Post Generator", layout="wide")
st.title("🤖 AI-Powered LinkedIn Post Generator")

# Input: topic for LinkedIn post
topic = st.text_input(
    "Enter topic for LinkedIn post:",
    "How AI is helping students build real-world projects"
)

# Button to generate post and image
if st.button("Generate Post & Image"):
    with st.spinner("Generating content..."):
        try:
            # 1️⃣ Generate LinkedIn post
            linkedin_post = generate_linkedin_post(topic)
            st.subheader("🔹 LinkedIn Post:")
            st.write(linkedin_post)

            # 2️⃣ Generate image prompt from LinkedIn post
            image_prompt = generate_image_prompt(linkedin_post)
            st.subheader("🔹 Image Prompt:")
            st.write(image_prompt)

            # 3️⃣ Generate professional LinkedIn image
            image_path = generate_image(image_prompt)
            st.success(f"✅ Image generated successfully: {image_path}")

            # Display generated image
            from PIL import Image
            img = Image.open(image_path)
            st.image(img, caption="Generated LinkedIn Post Image", use_column_width=True)

        except Exception as e:
            st.error(f"❌ Error: {e}")

# -------------------------------
# Optional: Test run when script executed directly
# -------------------------------
if __name__ == "__main__":
    # This runs if someone executes python main.py locally
    topic = "How AI is helping students build real-world projects"
    linkedin_post = generate_linkedin_post(topic)
    print("\n🔹 LinkedIn Post:\n")
    print(linkedin_post)

    image_prompt = generate_image_prompt(linkedin_post)
    print("\n🔹 Image Prompt:\n")
    print(image_prompt)

    image_path = generate_image(image_prompt)
    print(f"\n✅ Image generated successfully: {image_path}")
