import streamlit as st
from huggingface_hub import InferenceClient
import os

client = InferenceClient(
    model="black-forest-labs/FLUX.1-schnell",
    token=st.secrets["HF_API_KEY"]
)

def generate_image(image_prompt, output_path="linkedin_post_image.webp"):
    try:
        image = client.text_to_image(image_prompt)
        image.save(output_path)
        return output_path
    except Exception as e:
        print("HF IMAGE ERROR:", e)
        raise RuntimeError(str(e))
