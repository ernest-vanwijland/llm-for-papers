import os
import google.generativeai as genai

API_KEY = "AIzaSyBR7Z3Qatx-S72g_OZXSfAOyl3IfagMXe4"

def error_status(contents):
    try:
        model.generate_content(contents=contents)
    except Exception as e:
        print(f"An error occurred while making the API request: {e}")
        print("----------------------------------------\n")

def configure_gemini():
    if API_KEY == "YOUR_API_KEY_HERE":
        print("="*50)
        print("!!! IMPORTANT !!!")
        print("Please replace 'YOUR_API_KEY_HERE' with your actual Gemini API key.")
        print("="*50)
        return

    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
    except Exception as e:
        print(f"Error configuring the API: {e}")
        return

def run_gemini_examples():
    print("\n--- Running Multimodal (Text + Image) Example ---")
    try:
        image_path = "example_image.png"
        multimodal_prompt = "Describe what you see in this image in one sentence."

        if True:
            print(f"Opening image: {image_path}")
            print(f"Sending prompt: \"{multimodal_prompt}\"")
            img = Image.open(image_path)
            response = model.generate_content([multimodal_prompt, img])
            print("\n--- Gemini's Response (Image) ---")
            print(response.text)
            print("-----------------------------------\n")
    except Exception as e:
        print(f"\n--- An Error Occurred (Image Example) ---")
        print(f"An error occurred while making the API request: {e}")
        print("-----------------------------------------\n")

if __name__ == "__main__":
    configure_gemini()
    run_gemini_examples()




























































