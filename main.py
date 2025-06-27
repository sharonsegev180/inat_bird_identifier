# bird_identifier_api/main.py

from flask import Flask, request, jsonify
import requests
import tempfile
import os

app = Flask(__name__)

INATURALIST_API_URL = "https://api.inaturalist.org/v1/identifications"

@app.route("/")
def home():
    return "Bird Identifier API is running 🐦"

@app.route("/identify_bird", methods=["POST"])
def identify_bird():
    try:
        data = request.get_json()

        if not data or "image_url" not in data:
            return jsonify({"error": "Missing 'image_url' in request."}), 400

        image_url = data["image_url"]

        # הורדת התמונה לקובץ זמני
        response = requests.get(image_url)
        if response.status_code != 200:
            return jsonify({"error": "Failed to download image from provided URL."}), 400

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(response.content)
            tmp.flush()

            # שליחת הבקשה לזיהוי ל-Inaturalist
            files = {"file": open(tmp.name, "rb")}
            api_response = requests.post("https://api.inaturalist.org/v1/identifications/project", files=files)

            if api_response.ok:
                result = api_response.json()
                # בדיקה אם נמצאו תוצאות
                if result.get('results'):
                    top_result = result['results'][0]
                    species_guess = top_result.get('taxon', {}).get('preferred_common_name', 'Unknown')
                    scientific_name = top_result.get('taxon', {}).get('name', 'Unknown')
                    confidence = top_result.get('score', 'N/A')

                    return jsonify({
                        "species_guess": species_guess,
                        "scientific_name": scientific_name,
                        "confidence": confidence
                    }), 200
                else:
                    return jsonify({"message": "No bird identified in the image."}), 200
            else:
                return jsonify({"error": "iNaturalist API returned an error."}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
