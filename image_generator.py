import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# Load environment variables
load_dotenv()

HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
if HF_API_KEY is None:
    raise ValueError("HUGGINGFACE_API_KEY not found in .env")

# Initialize Hugging Face client with FLUX model
client = InferenceClient(
    model="black-forest-labs/FLUX.1-schnell",
    token=HF_API_KEY
)

def generate_image(image_prompt, output_path="linkedin_post_image.webp"):
    """
    Generates a professional LinkedIn-style image from a prompt
    """

    image = client.text_to_image(image_prompt)
    image.save(output_path)

    return output_path
if __name__ == "__main__":
    # Sample prompt for testing
    test_prompt = (
        "Professional LinkedIn-style image of an AI workspace, modern desk, "
        "laptop with analytics dashboard, clean corporate look, minimal style"
    )

    image_file = generate_image(test_prompt)
    print(f"✅ Test image generated successfully: {image_file}")
