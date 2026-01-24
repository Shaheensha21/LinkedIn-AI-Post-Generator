import streamlit as st
from huggingface_hub import InferenceClient
import uuid
import os

client = InferenceClient(
    model="stabilityai/stable-diffusion-xl-base-1.0",
    token=st.secrets["HUGGINGFACE_API_KEY"]
)

def generate_image(image_prompt):
    try:
        os.makedirs("generated_images", exist_ok=True)
        image_path = f"generated_images/{uuid.uuid4()}.png"

        image = client.text_to_image(
            image_prompt,
            guidance_scale=7.5,
            num_inference_steps=30
        )
        image.save(image_path)
        return image_path

    except Exception as e:
        print("SDXL image generation failed:", e)
        return None
