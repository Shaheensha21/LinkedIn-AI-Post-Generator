import streamlit as st
from google import genai

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

def generate_image_prompt(linkedin_post: str):
    prompt = f"""
You are an expert LinkedIn visual designer.

Convert the LinkedIn post below into ONE professional image prompt.

Post:
\"\"\"
{linkedin_post}
\"\"\"

Rules:
- Clean, modern, corporate
- No text inside image
- LinkedIn business style
- High-quality visual
- Output ONLY the prompt
"""

    response = client.models.generate_content(
        model="models/gemini-1.5-flash",
        contents=prompt
    )

    return response.text.strip()
