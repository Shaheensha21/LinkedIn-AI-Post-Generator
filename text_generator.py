import streamlit as st
from google import genai

# ----------------------------------
# Initialize Gemini client (SAFE)
# ----------------------------------
def get_gemini_client():
    if "GEMINI_API_KEY" not in st.secrets:
        raise RuntimeError("GEMINI_API_KEY not found in Streamlit secrets")

    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])


def generate_linkedin_post(topic: str, tone: str = "professional") -> str:
    """
    Generate a LinkedIn post using Gemini
    """

    client = get_gemini_client()

    prompt = f"""
You are a LinkedIn content expert.

Write a {tone} LinkedIn post about the following topic:
"{topic}"

Requirements:
- Professional and engaging tone
- Short paragraphs
- 3–5 relevant hashtags at the end
- Include a clear call-to-action
"""

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )

    return response.text.strip()
