import requests
import json
import base64
import mimetypes
import os
from pathlib import Path

# API_KEY = "AIzaSyBR7Z3Qatx-S72g_OZXSfAOyl3IfagMXe4"#ernest 
API_KEY ="AIzaSyBNkra1dEv2nLtQWIcyoiUYSzOJhBCPjYY" #julien
MODEL_NAME = "gemini-1.5-flash-latest"
MODEL_NAME = "gemini-2.5-pro"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent"

def extract_text_from_response(api_response):
    if not api_response:
        return None
    try:
        candidates = api_response.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text")
        return "No text content found in the response."
    except (IndexError, KeyError, AttributeError):
        print("Error: Could not parse the expected text from the API response.")
        return None

def request(prompts, system_prompt = "", model = "", contents=[]):
    headers = {
        'Content-Type': 'application/json',
        'x-goog-api-key': API_KEY
    }
    #parts = []
    parts = [{"text": prompt} for prompt in prompts]
    for file_path in contents:
        if file_path and os.path.exists(file_path):
            try:
                print(f"Processing file: {file_path}")
                
                mime_type, _ = mimetypes.guess_type(file_path)
                
                if mime_type is None:
                    print(f"Warning: Could not determine a supported MIME type for '{file_path}'. Skipping this file.")
                    continue
                
                with open(file_path, "rb") as f:
                    file_content = f.read()
                
                encoded_content = base64.b64encode(file_content).decode('utf-8')
                
                parts.append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": encoded_content
                    }
                })
            except Exception as e:
                print(f"Error processing file '{file_path}': {e}")
                continue

    payload = {
        "systemInstruction": {
            "role": "system",
            "parts": [
            {
                "text": system_prompt
            }
            ]
        },
        "contents": [
        {
            "role": "user",
            "parts": parts
        },
        {
            "role": "model",
            "parts": [{"text": model}]
        }
        ]
    }
    #for prompt in prompts:
    #    payload["contents"].append({"role": "user", "parts": [{"text": prompt}]})

    response = None
    cnt = 5
    while response == None and cnt > 0:
        cnt -= 1
        print("Sending request to Gemini API...")
        try:
            response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
            
            response.raise_for_status() 
            
            print("Successfully received response.")
            response = response.json()

        except requests.exceptions.HTTPError as e:
            print("\n--- A Bad Request Error Occurred ---")
            response = e.response
            print(f"Error Status Code: {response.status_code}")
            print(f"Error Reason: {response.reason}")
            print("--- Full Error Details ---")
            try:
                print(json.dumps(response.json(), indent=2))
            except json.JSONDecodeError:
                print(response.text)
            print("--------------------------\n")
            response = None
        except requests.exceptions.RequestException as e:
            print(f"\n--- A Network Error Occurred ---")
            print(f"An error occurred while making the request: {e}")
            print("--------------------------------\n")
            response = None
    return extract_text_from_response(response)

def run_examples():
    if API_KEY == "YOUR_API_KEY_HERE":
        print("="*50)
        print("!!! IMPORTANT !!!")
        print("Please replace 'YOUR_API_KEY_HERE' with your actual Gemini API key.")
        print("="*50)
        return
    
    image_path = "example_image.png"
    image_prompt = "Describe this image."

    if os.path.exists(image_path):
        image_text_response = request([image_prompt], contents=[image_path])
        if image_text_response:
            print("\n--- Gemini's Response (Single Image) ---")
            print(image_text_response)
            print("------------------------------------------\n")
    else:
        print(f"Skipping single image example because the file was not found or created.")

def get_file_paths(folder_path):
    file_paths = []
    
    # Check if the provided path exists and is a directory
    if not os.path.isdir(folder_path):
        print(f"Error: Folder not found at '{folder_path}'")
        return file_paths

    # Iterate over all the entries in the folder
    for entry_name in os.listdir(folder_path):
        # Create the full path to the entry
        full_path = os.path.join(folder_path, entry_name)
        
        # Check if the entry is a file (and not a directory)
        if os.path.isfile(full_path):
            file_paths.append(full_path)
            
    return file_paths


def list_papers(folder_path: str):
    try:
        p = Path(folder_path)
        return [item.name for item in p.iterdir() if item.is_dir()]
    except FileNotFoundError:
        print(f"Error: Directory not found at '{folder_path}'")
        return None

if __name__ == "__main__":
    run_examples()
    prompt = "You are a university professor and an expert mathematician and algorithmician. Your job is to write the proof where TOPROVE 1 is written. Do not read the article after that point. You need to understand the article until TOPROVE 1 to understand what the claim to prove is. Make sure your proof is rigorous and correctly proves the desired claim. Your proof cannot use the statement of the claim it needs to prove to prove itself, and it cannot use any element that is not yet proved. Provide your answer as a Latex code snippet that I can copy paste into an overleaf document, make sure it compiles correctly. Just provide the proof of TOPROVE 1 and nothing else."
    
    prompt = "You are a university professor and an expert mathematician and algorithmician. Your job is to understand the article until TOPROVE 1, do not read anything that comes after. Then, you need to output a latex code snippet that compiles correctly that contains just the statement of the result of which TOPROVE 1 replaces the proof, and nothing else."
    
    
    files=["data/2407.02412/noproof/paper.pdf"]
    
    if os.path.exists(files[0]):
        text_response = request([prompt], contents = files)
        print(text_response)
    else:
        print(f"File not found")































































