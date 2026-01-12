import streamlit as st
from google import genai

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

def generate_linkedin_post(topic, tone="professional"):
    prompt = f"""
You are a top LinkedIn content creator.

Write a {tone} LinkedIn post about:
"{topic}"

Requirements:
- Strong hook
- Short paragraphs
- Clear value
- Call-to-action
- 3–5 hashtags
"""

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )

    return response.text.strip()
