import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_linkedin_post(topic, tone="professional"):
    """
    Generates a LinkedIn-style post based on a topic and tone
    """

    prompt = f"""
    You are a LinkedIn content expert.

    Write a {tone} LinkedIn post about the following topic:
    "{topic}"

    Requirements:
    - Professional and engaging tone
    - Short paragraphs
    - 3–5 relevant hashtags at the end
    - Include a call-to-action

    The post should feel natural and suitable for LinkedIn.
    """

    model = genai.GenerativeModel("models/gemini-2.5-flash")
    response = model.generate_content(prompt)

    return response.text
