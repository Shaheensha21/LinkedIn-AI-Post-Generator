from google import genai
import os

client = genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY")
)

def generate_flux_image_prompt(topic: str):
    prompt = f"""
Generate a highly realistic, photorealistic image prompt for Black Forest Labs FLUX.

Topic:
{topic}

Prompt rules:
- Photorealistic, real-world photography
- Professional LinkedIn-friendly style
- Natural lighting, realistic skin texture
- Modern environment
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

    except Exception:
        return "⚠️ Failed to generate FLUX image prompt."
