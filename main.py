from text_generator import generate_linkedin_post
from image_prompt_generator import generate_image_prompt
from image_generator import generate_image

if __name__ == "__main__":

    # 🔹 Single input (this is all the user provides)
    topic = "How AI is helping students build real-world projects"

    # 1️⃣ Generate LinkedIn post
    linkedin_post = generate_linkedin_post(topic)
    print("\n🔹 LinkedIn Post:\n")
    print(linkedin_post)

    # 2️⃣ Generate image prompt from LinkedIn post
    image_prompt = generate_image_prompt(linkedin_post)
    print("\n🔹 Image Prompt:\n")
    print(image_prompt)

    # 3️⃣ Generate professional LinkedIn image
    image_path = generate_image(image_prompt)
    print(f"\n✅ Image generated successfully: {image_path}")
