# Flask-Builtin-Ollama-RaspberryPi-API

This repo contains Ollama, Flask, Raspberry Pi 4B 8GB RAM based API server for **builtin** mode.

Flask server **builtin mode** on Raspberry Pi and Ollama qwen:0.5b

The Flask builtin web server runs on http://127.0.0.1:5000

Apache benchmark can be done on this code as mentioned later

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
mkdir flask-builtin

cd flask-builtin
```

# Create a virtual environment:

Create a virtual environment named ‘flask_builtin’ or any other name 

```
python3 -m venv flask_builtin
```

# Activate the virtual environment:

```
source flask_builtin/bin/activate
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
sudo gedit flask_builtin.py
```

The code is as below:

```python
from flask import Flask, request, jsonify
import requests
import logging
from logging.handlers import QueueHandler, QueueListener
from queue import Queue
import threading
import psutil
import time
import csv
import os

app = Flask(__name__)

# Define the model name as a variable
model_name = "qwen:0.5b"
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# CSV file setup
csv_file = 'ollama_api_logs.csv'
csv_headers = [
    'timestamp', 'model_name', 'prompt', 'response', 'eval_count', 'eval_duration',
    'load_duration', 'prompt_eval_duration', 'total_duration', 'tokens_per_second',
    'avg_cpu_usage_during', 'memory_usage_before', 'memory_usage_after',
    'memory_allocated_for_model', 'network_latency', 'total_response_time'
]

csv_queue = Queue()

def csv_writer():
    while True:
        log_message_csv = csv_queue.get()
        if log_message_csv is None:  # Exit signal
            break
        file_exists = os.path.isfile(csv_file)
        with open(csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(csv_headers)
            writer.writerow(log_message_csv)

# Start the CSV writer thread
csv_thread = threading.Thread(target=csv_writer)
csv_thread.start()

# Function to measure CPU usage during the API call
def measure_cpu_usage(interval, stop_event, result):
    while not stop_event.is_set():
        result.append(psutil.cpu_percent(interval=interval))

# Function to load the model and measure memory usage
def load_model_and_measure_memory(model_name):
    # Measure baseline memory usage
    process = psutil.Process()
    baseline_memory = process.memory_info().rss

    # Load the model
    payload = {
        "model": model_name,
        "prompt": "",
        "stream": False  # Just load the model without generating a response
    }
    response = requests.post(OLLAMA_API_URL, json=payload)

    if response.status_code == 200:
        print("Model loaded successfully")
    else:
        print("Failed to load model")

    # Measure memory usage after loading the model
    time.sleep(5)  # Wait for a few seconds to ensure the model is fully loaded
    memory_after_loading = process.memory_info().rss
    memory_allocated_for_model = memory_after_loading - baseline_memory
    return memory_allocated_for_model

# Measure memory usage for the model
memory_allocated_for_model = load_model_and_measure_memory(model_name)
print(f"Memory Allocated for Model: {memory_allocated_for_model} bytes")

@app.route('/generate', methods=['POST'])
def generate():
    start_time = time.time()
    data = request.json
    if not data or 'prompt' not in data:
        return jsonify({'error': 'No prompt provided'}), 400

    payload = {
        "model": model_name,
        "prompt": data['prompt'],
        "stream": False  # Set to True if you want streaming responses
    }

    try:
        # Measure memory usage before the request
        process = psutil.Process()
        memory_usage_before = process.memory_info().rss

        # Start measuring CPU usage in a separate thread
        cpu_usage_result = []
        stop_event = threading.Event()
        cpu_thread = threading.Thread(target=measure_cpu_usage, args=(0.1, stop_event, cpu_usage_result))
        cpu_thread.start()

        # Measure network latency
        network_start_time = time.time()
        # Send the API request
        response = requests.post(OLLAMA_API_URL, json=payload)
        network_latency = (time.time() - network_start_time) * 1e9  # Convert to nanoseconds

        # Stop measuring CPU usage
        stop_event.set()
        cpu_thread.join()

        response_data = response.json()

        # Measure memory usage after the request
        memory_usage_after = process.memory_info().rss

        # Calculate average CPU usage during the request
        avg_cpu_usage_during = sum(cpu_usage_result) / len(cpu_usage_result) if cpu_usage_result else 0.0
        avg_cpu_usage_during = round(avg_cpu_usage_during, 2)  # Round to 2 decimal points

        # Extract the required values
        eval_count = response_data.get('eval_count', 0)
        eval_duration = response_data.get('eval_duration', 1)  # avoid division by zero
        load_duration = response_data.get('load_duration', 0)
        prompt_eval_duration = response_data.get('prompt_eval_duration', 0)
        total_duration = response_data.get('total_duration', 0)

        # Calculate tokens per second
        tokens_per_second = eval_count / eval_duration * 1e9 if eval_duration > 0 else 0

        # Calculate total response time
        end_time = time.time()
        total_response_time = (end_time - start_time) * 1e9  # Convert to nanoseconds

        # Prepare log message for CSV
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_message_csv = [
            timestamp, model_name, data['prompt'], response_data.get('response', 'N/A'), eval_count,
            eval_duration, load_duration, prompt_eval_duration, total_duration,
            tokens_per_second, avg_cpu_usage_during, memory_usage_before,
            memory_usage_after, memory_allocated_for_model, network_latency, total_response_time
        ]

        # Put the log message into the CSV queue
        csv_queue.put(log_message_csv)

        return jsonify(response_data), 200
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

# Ensure the CSV writer thread exits cleanly
import atexit
@atexit.register
def shutdown():
    csv_queue.put(None)
    csv_thread.join()

```


# Activate the virtual environment:

 Give full path

```
source ~/Desktop/flask-builtin/flask_builtin/bin/activate
```

# Run the application python file ‘flask1.py’ ‘’ created above”:

```
python3 flask_builtin_v1.py
```

The server must be running and should show below (if model changes then model size can be changed):

```
Model loaded successfully
Memory Allocated for Model: 262144 bytes
 * Serving Flask app 'flask_builtin_v1'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://172.16.12.28:5000
Press CTRL+C to quit
 * Restarting with stat
Model loaded successfully
Memory Allocated for Model: 262144 bytes
 * Debugger is active!
 * Debugger PIN: 139-424-820

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

# It creats a CSV file in local directory that saves the test metrics

The name of file is **ollama_api_logs.csv**

# (If needed) Deactivate the virtual environment:

Press ‘Ctrl + C’ in the terminal where the server was running

Then 

```
deactivate
```

# Apache Benchmark Technqiue


* Apache benchmark tools must be installed first (if not installed already)

    ```
    sudo apt-get install apache2-utils
    ```


* Create a **post_data.json** file in a **sepearte location** than the above virtual environment that should contain the load as below (or put other prompt as per requirement):

  ```
  {
    "prompt": "What is 2+2?"
   }
  ```


* In command line from the location where the above json file is located, run below (change the value after -n and -c accordingly):

    ```
    ab -n 10 -c 5  -p post_data.json -T application/json -l http://127.0.0.1:5000/generate
    ```

      * -n:  Total number of requests to perform.

             For example, **-n 10** represents 10 requests to perform.
   
      * -c: Number of multiple requests to perform at a time (concurrency level).

             For example, **-c 5** represents 5 concurency level.

      * -p: File containing the data to POST

             For example, **-p post_data.json** represents post_data.json is the data to POST

      * -T: Content-Type header to send with the requests.

             For example, **-T application/json** represents Content-Type header to send with the requests.

      * http://127.0.0.1:5000/generate: The URL of your API endpoint.


     The **output** will vary, you may something similar to below:


  ![Untitled](https://github.com/ParthaPRay/Flask-Builtin-Ollama-RaspberryPi-API/assets/1689639/06443b38-9328-4181-941f-8af002b4a4e8)




