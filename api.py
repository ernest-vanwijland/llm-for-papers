import requests
import json
import base64
import mimetypes
import os
import time
from pathlib import Path

API_KEY0 = "AIzaSyBR7Z3Qatx-S72g_OZXSfAOyl3IfagMXe4" # ernest 
API_KEY1 = "AIzaSyBNkra1dEv2nLtQWIcyoiUYSzOJhBCPjYY" # julien
API_KEY2 = "AIzaSyB2upUm17f7xuXKO4MamqVIyxKZ8glzUzc" # E
API_KEY3 = "AIzaSyBoJ__GLc7VDvQRV3OIYzzxJswVLZ3EXIs" # P
API_KEY4 = "AIzaSyBtTnn8z6QrVpwnJ0LinhB6YAU2rbWGSx0" # A
API_KEY5 = "AIzaSyAbVp0XrKFGaDcYKFkm-tubUh4y7rXNYaA" # max
API_KEY6 = "AIzaSyCKrge05eWudrw6R93osZaexqN4Eds_OwI" # julien 2
API_KEY_SET_ALL = [API_KEY0, API_KEY1, API_KEY2, API_KEY3, API_KEY4, API_KEY5, API_KEY6]
API_KEY_SET1 = [API_KEY5]
API_KEY_SET2 = [API_KEY2, API_KEY3]
API_KEY_SET3 = [API_KEY4, API_KEY5]
API_KEYS_SET_USED = API_KEY_SET1
API_KEYS_USED = API_KEYS_SET_USED[0] 
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
    global API_KEYS_USED
    headers = {
        'Content-Type': 'application/json',
        'x-goog-api-key': API_KEYS_USED  # You can implement a rotation mechanism if needed
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
    cnt = 1
    max_retries = 2
    while response == None and API_KEYS_USED != None :
        time.sleep(2.5)
        while response == None and cnt <= max_retries :
            time.sleep(1)
            print(f"Sending request to Gemini API... (attempt {cnt} of {max_retries})")
            cnt += 1
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
        API_KEYS_USED = API_KEYS_SET_USED[(API_KEYS_SET_USED.index(API_KEYS_USED) + 1) % len(API_KEYS_SET_USED)] if API_KEYS_USED in API_KEYS_SET_USED else None
        current_key = API_KEYS_USED
        print(f"Switching to the next API key: {current_key if current_key else 'No more keys available.'}")
        headers = {
            'Content-Type': 'application/json',
            'x-goog-api-key': API_KEYS_USED  # You can implement a rotation mechanism if needed
        }
        cnt = 1
    return extract_text_from_response(response)

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































































