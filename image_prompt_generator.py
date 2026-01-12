import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_image_prompt(linkedin_post: str):
    """
    Converts a LinkedIn post into a professional image-generation prompt
    """
    prompt = f"""
You are an expert visual designer for LinkedIn content.

Based on the LinkedIn post below, generate a single detailed image prompt
that can be used by an AI image generator.

LinkedIn post:
\"\"\"
{linkedin_post}
\"\"\"

Image prompt requirements:
- Professional LinkedIn style
- Clean, modern, minimal design
- Corporate / tech aesthetic
- No text inside the image
- High-quality, realistic or illustration-style visual
- Suitable for LinkedIn feed (business audience)

Output ONLY the image prompt text.
"""
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()
