import streamlit as st
from huggingface_hub import InferenceClient
from PIL import Image

# -------------------------------
# Load API key from Streamlit secrets
# -------------------------------
HUGGINGFACE_API_KEY = st.secrets["HUGGINGFACE_API_KEY"]

# -------------------------------
# Initialize Hugging Face client with FLUX model
# -------------------------------
client = InferenceClient(
    model="black-forest-labs/FLUX.1-schnell",
    token=HUGGINGFACE_API_KEY
)

# -------------------------------
# Function to generate image
# -------------------------------
def generate_image(image_prompt, output_path="linkedin_post_image.webp"):
    """
    Generates a professional LinkedIn-style image from a prompt
    """
    image = client.text_to_image(image_prompt)
    image.save(output_path)
    return output_path

# -------------------------------
# Streamlit App UI
# -------------------------------
st.set_page_config(page_title="AI LinkedIn Post Generator", layout="wide")
st.title("🤖 AI-Powered LinkedIn Post Generator")

# Input prompt from user
image_prompt = st.text_area(
    "Enter image description for LinkedIn post:",
    "Professional LinkedIn-style image of an AI workspace, modern desk, laptop with analytics dashboard, clean corporate look, minimal style"
)

# Button to generate image
if st.button("Generate Image"):
    with st.spinner("Generating image..."):
        try:
            image_file = generate_image(image_prompt)
            st.success("✅ Image generated successfully!")
            img = Image.open(image_file)
            st.image(img, caption="Generated LinkedIn Post Image", use_column_width=True)
        except Exception as e:
            st.error(f"❌ Error generating image: {e}")

# -------------------------------
# Optional: Test run when script executed directly
# -------------------------------
if __name__ == "__main__":
    test_prompt = (
        "Professional LinkedIn-style image of an AI workspace, modern desk, "
        "laptop with analytics dashboard, clean corporate look, minimal style"
    )
    image_file = generate_image(test_prompt)
    print(f"✅ Test image generated successfully: {image_file}")
