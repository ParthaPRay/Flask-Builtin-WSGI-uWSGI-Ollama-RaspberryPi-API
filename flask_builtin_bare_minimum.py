# Bare minimum flask code that only accpet the requestes and responds back

# This code should be for Apache benchmark 'ab' testing ONLY



from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Define the model name as a variable
model_name = "qwen:0.5b"
OLLAMA_API_URL = "http://localhost:11434/api/generate"

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    if not data or 'prompt' not in data:
        return jsonify({'error': 'No prompt provided'}), 400

    payload = {
        "model": model_name,
        "prompt": data['prompt'],
        "stream": False  # Set to True if you want streaming responses
    }

    try:
        # Send the API request
        response = requests.post(OLLAMA_API_URL, json=payload)
        response_data = response.json()
        return jsonify(response_data), 200
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
