import streamlit as st
from google import genai

# -------------------------------
# Configure Gemini Client
# -------------------------------
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

def generate_linkedin_post(topic, tone="professional"):
    prompt = f"""
You are a LinkedIn content expert.

Write a {tone} LinkedIn post about the following topic:
"{topic}"

Requirements:
- Professional and engaging tone
- Short paragraphs
- 3–5 relevant hashtags at the end
- Include a call-to-action
"""

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )

    return response.text
