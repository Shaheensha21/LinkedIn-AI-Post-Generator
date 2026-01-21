from google import genai
import os

# -------------------------------
# Configure Gemini Client
# -------------------------------
client = genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY")  # Use environment variable instead of st.secrets
)

def generate_image_prompt(linkedin_post: str):
template="""
        Write a professional and engaging LinkedIn post (100–120 words) about:
        "{topic}"

        Tone: professional, inspiring, positive.
        """

    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt
        )

        return response.text.strip()

    except Exception as e:
        return "⚠️ Failed to generate image prompt. Please try again."
