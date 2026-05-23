import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY", "").strip()
print(f"Loaded GEMINI_API_KEY: '{api_key}'")

genai.configure(api_key=api_key)

print("\n--- Listing Models ---")
try:
    models = genai.list_models()
    for m in models:
        print(f"Name: {m.name}, Supported Methods: {m.supported_generation_methods}")
except Exception as e:
    print(f"Error listing models: {e}")

print("\n--- Testing simple generate_content with gemini-1.5-flash ---")
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hello! What is your name?")
    print("Success with gemini-1.5-flash!")
    print(response.text)
except Exception as e:
    print(f"Error with gemini-1.5-flash: {e}")

print("\n--- Testing simple generate_content with gemini-2.5-flash ---")
try:
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content("Hello! What is your name?")
    print("Success with gemini-2.5-flash!")
    print(response.text)
except Exception as e:
    print(f"Error with gemini-2.5-flash: {e}")

print("\n--- Testing simple generate_content with gemini-2.0-flash ---")
try:
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content("Hello! What is your name?")
    print("Success with gemini-2.0-flash!")
    print(response.text)
except Exception as e:
    print(f"Error with gemini-2.0-flash: {e}")
