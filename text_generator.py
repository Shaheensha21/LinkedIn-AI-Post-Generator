from google import genai
import os

# -------------------------------
# Configure Gemini Client
# -------------------------------
client = genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY")
)

def generate_linkedin_post(topic, tone="professional"):
    prompt = f"""
You are a top 1% LinkedIn content creator.

Write a {tone} LinkedIn post on the topic:
"{topic}"

Rules:
- Strong hook in first 2 lines
- Short paragraphs
- Professional emojis (minimal)
- Clear value
- End with a call-to-action
- 3–5 hashtags at the end
- No markdown
- Sound human

Return ONLY the post text.
"""

    try:
        response = client.models.generate_content(
            model="models/gemini-1.5-flash-latest",
            contents=prompt
        )

        return response.text.strip()

    except Exception as e:
        return "⚠️ Failed to generate post. Please try again."
