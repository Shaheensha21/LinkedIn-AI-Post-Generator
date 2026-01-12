import streamlit as st
from huggingface_hub import InferenceClient

client = InferenceClient(
    model="black-forest-labs/FLUX.1-schnell",
    token=st.secrets["HUGGINGFACE_API_KEY"]
)

def generate_image(image_prompt, output_path="linkedin_post_image.webp"):
    image = client.text_to_image(image_prompt)
    image.save(output_path)
    return output_path
