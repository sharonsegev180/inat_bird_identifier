from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Bird identifier API is running. Use /identify_bird to POST an image."

@app.route('/identify_bird', methods=['POST'])
def identify_bird():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    # העלאת התמונה ל-Imgur לקבלת URL ציבורי
    imgur_client_id = os.environ.get('IMGUR_CLIENT_ID')
    if not imgur_client_id:
        return jsonify({'error': 'IMGUR_CLIENT_ID not set'}), 500

    headers = {'Authorization': f'Client-ID {imgur_client_id}'}
    files = {'image': file.read()}
    response = requests.post('https://api.imgur.com/3/image', headers=headers, files=files)

    if response.status_code != 200:
        return jsonify({'error': 'Failed to upload image to Imgur'}), 500

    image_url = response.json()['data']['link']

    # שליחת התמונה ל-iNaturalist לזיהוי
    payload = {
        'image_url': image_url,
        'lat': 32.0,
        'lng': 35.0,
        'locale': 'he'
    }
    inat_response = requests.post('https://api.inaturalist.org/v1/computervision/identify', json=payload)

    if inat_response.status_code != 200:
        return jsonify({'error': 'Failed to identify bird using iNaturalist'}), 500

    data = inat_response.json()
    if not data.get('results'):
        return jsonify({'message': 'No bird identified'}), 200

    result = data['results'][0]['taxon']

    return jsonify({
        'common_name': result.get('preferred_common_name', 'Unknown'),
        'scientific_name': result.get('name', 'Unknown'),
        'url': f"https://www.inaturalist.org/taxa/{result.get('id')}"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)

