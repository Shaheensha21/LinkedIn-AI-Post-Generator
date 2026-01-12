from google import genai
import os

# -------------------------------
# Configure Gemini Client
# -------------------------------
client = genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY")  # Use environment variable instead of st.secrets
)

def generate_image_prompt(linkedin_post: str):
    prompt = f"""
You are a creative AI prompt generator.

Based on the following LinkedIn post, generate a visually appealing image prompt that can be used with AI image generation models:

LinkedIn post:
"{linkedin_post}"

Rules:
- Keep the description clear and concise
- Include key elements and context from the post
- Specify art style, composition, lighting, and color palette
- Output text should be ready for AI image generation models
"""

    try:
        response = client.models.generate_content(
            model="models/gemini-1.5-image",
            contents=prompt
        )

        return response.text.strip()

    except Exception as e:
        return "⚠️ Failed to generate image prompt. Please try again."
