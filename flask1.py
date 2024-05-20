from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

OLLAMA_API_URL = "http://localhost:11434/api/generate"

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    if not data or 'prompt' not in data:
        return jsonify({'error': 'No prompt provided'}), 400

    payload = {
        "model": "qwen:0.5b",
        "prompt": data['prompt'],
        "stream": False  # Set to True if you want streaming responses
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response_data = response.json()
        return jsonify(response_data), 200
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

