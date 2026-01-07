import os
from google import genai
from google.genai import types

# Initialize Gemini client with your API key
os.environ["API_KEY"] = "YOUR_GOOGLE_GEMINI_API_KEY"
client = genai.Client(api_key=os.environ["API_KEY"])

def extract_phone_names_with_gemini(text):
    """
    Uses Gemini API to extract mobile phone names from given text via prompt.
    Returns list of product names extracted.
    """
    prompt = f"""Extract all mobile phone product names (brand + model) from the following text, return as a JSON list of strings:

    Text: \"\"\"{text}\"\"\"
    
    JSON List of product names:"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",  # Or your preferred Gemini model
        contents=prompt
    )

    # Gemini returns raw text response, parse it as JSON
    import json
    try:
        extracted = json.loads(response.text)
        return extracted
    except Exception as e:
        print(f"Failed to parse Gemini response: {e}")
        return []

# Example of integrating with existing Reddit post processing code:

# During iteration over each post (inside your existing loop in collect_data.py)

# Sample:
# phone_names = extract_phone_names_with_gemini(post.title)
# For each extracted phone name:
#   Store it in a new database table or existing related table linking with post.id

