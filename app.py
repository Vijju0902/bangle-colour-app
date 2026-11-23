import io
import zipfile
import streamlit as st
from PIL import Image
from google import genai
from google.genai import types

st.set_page_config(page_title="Product Colour Generator", layout="wide")
st.title("One-Click Product Colour Variation Generator")

with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Gemini API Key", type="password", help="Get a key from Google AI Studio")
    product_name = st.text_input("Design Name (for filenames)", value="Design 1")

uploaded_file = st.file_uploader("Upload your phone photo", type=["jpg", "jpeg", "png", "webp"])

default_colours = "Ruby Red, Emerald Green, Royal Blue, Rani Pink"
colours_input = st.text_input("Enter colours (comma-separated)", value=default_colours)

if uploaded_file and st.button("Generate Variations", type="primary"):
    if not api_key:
        st.error("Please enter a Gemini API key in the sidebar.")
        st.stop()

    client = genai.Client(api_key=api_key)
    original_img = Image.open(uploaded_file)
    colours = [c.strip() for c in colours_input.split(",") if c.strip()]

    st.image(original_img, caption="Original Photo", width=250)
    st.divider()

    zip_buffer = io.BytesIO()
    cols = st.columns(min(len(colours), 4))

    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for idx, colour in enumerate(colours):
            with st.spinner(f"Generating {colour}..."):
                prompt = (
                    f"Change only the main colour of this product to {colour}. "
                    "Keep the exact same design, pattern, metallic accents, stones, "
                    "camera angle, lighting, and background completely unchanged."
                )
                try:
                    response = client.models.generate_content(
                        model="gemini-3.1-flash-image",
                        contents=[original_img, prompt],
                        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
                    )

                    generated_img = None
                    for part in response.candidates[0].content.parts:
                        if part.inline_data is not None:
                            generated_img = Image.open(io.BytesIO(part.inline_data.data))
                            break

                    if generated_img:
                        filename = f"{product_name} - {colour}.png"
                        img_bytes = io.BytesIO()
                        generated_img.save(img_bytes, format="PNG")
                        zf.writestr(filename, img_bytes.getvalue())

                        with cols[idx % len(cols)]:
                            st.image(generated_img, caption=filename, use_container_width=True)
                    else:
                        st.warning(f"No image returned for {colour}.")
                except Exception as e:
                    st.error(f"Failed for {colour}: {e}")

    st.download_button(
        label="Download All Variations (ZIP)",
        data=zip_buffer.getvalue(),
        file_name=f"{product_name}_variations.zip",
        mime="application/zip",
    )
