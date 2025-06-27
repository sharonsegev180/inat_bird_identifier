from flask import Flask, request, jsonify
import requests
import os
import tempfile

app = Flask(__name__)

IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID")

@app.route("/")
def home():
    return "Bird Identifier API is running 🐦 - Upload an image via POST to /identify_bird"

@app.route("/identify_bird", methods=["POST"])
def identify_bird():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded.'}), 400

    file = request.files['file']

    # העלאה ל-Imgur לקבלת URL ציבורי
    headers = {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}
    files = {"image": file.read()}
    imgur_response = requests.post("https://api.imgur.com/3/image", headers=headers, files=files)

    if imgur_response.status_code != 200:
        return jsonify({"error": "Failed to upload image to Imgur."}), 500

    image_url = imgur_response.json()['data']['link']

    # שליחת URL ל-iNaturalist לזיהוי
    data = {
        "image_url": image_url,
        "lat": 32.0853,  # ת"א לדוגמה
        "lng": 34.7818,
        "locale": "he"
    }

    inat_response = requests.post("https://api.inaturalist.org/v1/computervision/identify", json=data)

    if inat_response.status_code != 200:
        return jsonify({"error": "Failed to identify image using iNaturalist."}), 500

    results = inat_response.json().get("results")
    if not results:
        return jsonify({"message": "No bird identified in the image."}), 200

    top_result = results[0]
    taxon = top_result.get("taxon", {})

    return jsonify({
        "species_guess": taxon.get("preferred_common_name", "Unknown"),
        "scientific_name": taxon.get("name", "Unknown"),
        "confidence": round(top_result.get("score", 0), 2),
        "image_url": image_url,
        "inat_url": f"https://www.inaturalist.org/taxa/{taxon.get('id', '')}"
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
