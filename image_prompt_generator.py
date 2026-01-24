import streamlit as st
from google import genai

client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)

def generate_flux_image_prompt(topic: str):
    prompt = f"""
Generate a highly realistic, photorealistic image prompt for Black Forest Labs FLUX.

Topic:
{topic}

Prompt rules:
- Photorealistic
- Professional LinkedIn-friendly
- Natural lighting
- DSLR photo, 50mm lens
- Shallow depth of field
- Ultra high resolution
- Clean composition
- No text, no watermark, no logo

Return ONLY the final image prompt.
"""

    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print("GEMINI PROMPT ERROR:", e)
        return None
