from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID")
INATURALIST_URL = "https://api.inaturalist.org/v1/observations"

def upload_to_imgur(image):
    headers = {"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"}
    files = {"image": image}
    response = requests.post("https://api.imgur.com/3/image", headers=headers, files=files)
    if response.status_code == 200:
        return response.json()['data']['link']
    else:
        return None

@app.route("/identify", methods=["POST"])
def identify_bird():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    imgur_link = upload_to_imgur(file)
    if not imgur_link:
        return jsonify({"error": "Failed to upload image to imgur"}), 500

    params = {
        "image_url": imgur_link,
        "per_page": 1,
        "order_by": "score"
    }
    response = requests.get(f"https://api.inaturalist.org/v1/computervision/score_image", params=params)

    if response.status_code == 200:
        data = response.json()
        if data["results"] and data["results"][0]["taxon"]:
            taxon = data["results"][0]["taxon"]
            result = {
                "common_name": taxon.get("preferred_common_name", "Unknown"),
                "scientific_name": taxon.get("name", "Unknown"),
                "confidence": data["results"][0]["score"]
            }
            return jsonify(result)
        else:
            return jsonify({"message": "No bird identified in the image."}), 200
    else:
        return jsonify({"error": "Failed to get identification from iNaturalist"}), 500

@app.route("/", methods=["GET"])
def home():
    return "Bird Identifier Action is running 🐦"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
