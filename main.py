# Updated main.py for your bird identification GPT bot
# Displays species name, scientific name, confidence, species ID, and uploaded image link

from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

IMGUR_CLIENT_ID = os.environ.get("IMGUR_CLIENT_ID")
INATURALIST_API_URL = "https://api.inaturalist.org/v1/"

@app.route("/")
def home():
    return "iNaturalist Bird Identifier API is running 🐦"

@app.route("/identify", methods=["POST"])
def identify():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files['file']
    
    # Upload to Imgur
    headers = {'Authorization': f'Client-ID {IMGUR_CLIENT_ID}'}
    img = {'image': file.read()}
    imgur_response = requests.post("https://api.imgur.com/3/image", headers=headers, files=img)
    if imgur_response.status_code != 200:
        return jsonify({"error": "Failed to upload image to Imgur."}), 500

    image_url = imgur_response.json()['data']['link']

    # Identify with iNaturalist
    data = {
        'image_url': image_url,
        'lat': 32.0853,  # Example: Tel Aviv latitude
        'lng': 34.7818,  # Example: Tel Aviv longitude
        'locale': 'he'
    }
    inat_response = requests.post(f"{INATURALIST_API_URL}computervision/identify", data=data)

    if inat_response.status_code != 200:
        return jsonify({"error": "Failed to identify image with iNaturalist."}), 500

    results = inat_response.json()['results']
    if not results:
        return jsonify({"message": "No species identified."}), 200

    top_result = results[0]
    species_guess = top_result.get('taxon', {}).get('preferred_common_name', 'Unknown')
    scientific_name = top_result.get('taxon', {}).get('name', 'Unknown')
    confidence = top_result.get('score', 0)
    species_id = top_result.get('taxon', {}).get('id', 'Unknown')

    # Structured, clean response
    response = {
        "species_name": species_guess,
        "scientific_name": scientific_name,
        "confidence": round(confidence, 2),
        "species_id": species_id,
        "image_url": image_url
    }

    print(f"[LOG] Identification: {response}")
    return jsonify(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)

