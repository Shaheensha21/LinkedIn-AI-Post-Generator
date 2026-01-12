import streamlit as st
import google.generativeai as genai

# ------------------- Configure Gemini API -------------------
# Use Streamlit Secrets for secure API keys
# Add in your Streamlit Cloud: GEMINI_API_KEY
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# ------------------- Image Prompt Generator -------------------
def generate_image_prompt(linkedin_post: str) -> str:
    """
    Converts a LinkedIn post into a professional image-generation prompt
    suitable for AI image generators.

    Args:
        linkedin_post (str): The LinkedIn post text.

    Returns:
        str: A detailed image prompt text.
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
    # Use Gemini 2.5 Flash model
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()
