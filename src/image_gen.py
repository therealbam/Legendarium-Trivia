import streamlit as st
import openai
import base64
from PIL import Image
from io import BytesIO
import os

from dotenv import load_dotenv
load_dotenv()

# Set your OpenAI API key here (or load it from environment variables)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")
openai.api_key = OPENAI_API_KEY

# Function to generate an image using OpenAI
def generate_image_with_openai(prompt, output_path="test.webp"):
    try:
        print("Calling OpenAI API...")
        # Make the API call to generate the image
        response = openai.images.generate(
            model="dall-e-2",
            prompt=prompt,
            n=1,
            size="1024x1024",  # Adjust the size as per your requirement
            response_format="b64_json"
        )
        
        print("Decoding image data...")
        # Decode the Base64 string into binary data
        image_data = base64.b64decode(response.data[0].b64_json)
        
        print("Converting binary data to image...")
        # Convert the binary data into an image using PIL
        image = Image.open(BytesIO(image_data))
        
        print(f"Saving image as {output_path}...")
        # Save the image in WebP format
        image.save(output_path, format="WEBP")
        
        print("Image generation completed successfully.")
        return image
    except Exception as e:
        st.error(f"An error occurred: {e}")
        print(f"Error: {e}")
        return None

# Streamlit UI
st.title("AI Image Generator")

# Prompt input
prompt = st.text_area("Enter an image prompt:", value="Create a wide 8-bit pixel art style image of Aulë creating the Dwarves.")

# Generate image button
if st.button("Generate Image"):
    with st.spinner("Generating image..."):
        print("Button clicked, generating image...")
        # Generate image using OpenAI
        image = generate_image_with_openai(prompt)
        
        # Display the image if successful
        if image is not None:
            st.image(image, caption="Generated Image", use_column_width=True)
