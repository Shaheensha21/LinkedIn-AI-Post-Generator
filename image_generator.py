import requests
import base64
import uuid
import os
import streamlit as st

CLOUDFLARE_API_TOKEN = st.secrets["CLOUDFLARE_API_TOKEN"]
CLOUDFLARE_ACCOUNT_ID = st.secrets["CLOUDFLARE_ACCOUNT_ID"]

MODEL = "@cf/black-forest-labs/flux-1-schnell"

def generate_image(prompt: str):
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/{MODEL}"

    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "prompt": prompt
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        raise RuntimeError(f"Cloudflare API error: {response.text}")

    data = response.json()

    if "result" not in data or "image" not in data["result"]:
        raise RuntimeError(f"No image returned: {data}")

    image_base64 = data["result"]["image"]
    image_bytes = base64.b64decode(image_base64)

    os.makedirs("generated_images", exist_ok=True)
    image_path = f"generated_images/{uuid.uuid4().hex}.png"

    with open(image_path, "wb") as f:
        f.write(image_bytes)

    return image_path
