# Flask-Ollama-RaspberryPi-API
This repo contains Ollama, Flask, Raspberry Pi 4B 8GB RAM based API server.

Flask server on Raspberry Pi and Ollama qwen:0.5b



*********************************************************************************************** 

# Ollama Setup

1.	Install Ollama: curl -fsSL https://ollama.com/install.sh | sh

2.	Start Ollama Server: ollama serv

3.	Run a local LLM Model: ollama run qwen:0.5b

4.	Test whether Ollama is running:

Open http://127.0.0.1:11434/  on the browser

It should show

Ollama is running

***********************************************************************************************

# The whole process is conducted in the ‘Desktop’ directory, Change the directory if needed.

/home/pi/Desktop


(Optional but Important)

sudo apt-get update
sudo apt-get upgrade

sudo apt-get install python3-venv


# Create a new project directory and go inside the project directory:

```
mkdir flask-server-1

cd flask-server-1
```

# Create a virtual environment:

Create a virtual environment named ‘flask1’ or any other name 

```
python3 -m venv flask1
```

# Activate the virtual environment:

```
source flask1/bin/activate
```

# Update / create a ‘requirements.txt’ file to update with necessary python package names:

```
sudo gedit requirements.txt
```

Then place the packages (e.g., flask, requests etc. into it) that are needed to install and run the application

Save it

Then 

```
pip3 install -r requirements.txt
```


# Write the application code: 

```
sudo gedit flask1.py
```

```python

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
```


# Activate the virtual environment:

 Give full path

```
source ~/Desktop/flask-server-1/flask1/bin/activate
```

# Run the application python file ‘flask1.py’ ‘’ created above”:

```
python3 flask1.py
```

The server must be running and should show below:

```
* Serving Flask app 'flask1'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://172.16.12.28:5000
```







# Testing of API Call

Open a New Terminal

Send a POST request using curl:

```
curl -X POST http://127.0.0.1:5000/generate -H "Content-Type: application/json" -d '{"prompt": "Why is the sky blue?"}'
```

or

```
curl -X POST http://127.0.0.1:5000/generate -H "Content-Type: application/json" -d '{
  "prompt": "Why is the sky blue?",
  "options": {
    "temperature": 0.7
  }
}'
```

or

etc.


# (If needed) Deactivate the virtual environment:

Press ‘Ctrl + C’ in the terminal where the server was running

Then 

```
deactivate
```

# After activation of the virtual environment the process can be restarted as per above
