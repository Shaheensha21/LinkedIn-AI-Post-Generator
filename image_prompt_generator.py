import streamlit as st
from google import genai

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

def generate_image_prompt(linkedin_post: str):
    prompt = f"""
Create a professional LinkedIn-style image prompt based on this post:

{linkedin_post}

Requirements:
- Corporate, modern
- Clean background
- No text in image
"""

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )

    return response.text.strip()
