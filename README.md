# Flask-Builtin-WSGI-uWSGI-Ollama-RaspberryPi-API

This repo contains Ollama, Flask, Raspberry Pi 4B 8GB RAM based API server for all **builtin, WSGi and uWSGI** modes.

Flask server **builtin, WSGi and uWSGI** modes on Raspberry Pi and Ollama qwen:0.5b

The Flask builtin web server runs on **http://127.0.0.1:5000**. The port can be changed at the last line of the main application code.

**Apache benchmark** (ab) can be done on this code as mentioned later.

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
mkdir flask

cd flask
```

# Create a virtual environment:

Create a virtual environment named ‘flask’ or any other name 

```
python3 -m venv NAMEOFENVIRONMENT
```

# Activate the virtual environment:

```
source NAMEOFENVIRONMENT/bin/activate
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
sudo gedit flaskserver.py
```

The code is as below:

```python
# Flask web server and Ollama python code
# CSV file is used for metric logging asynchronously
# CSV file is logged into 'ollama_api_logs.csv'
# For logging CPU and Memory uage 'psutil' package is needed
"""
Separate Thread for CPU Usage: A separate thread measures CPU usage continuously during the request handling.
Stop Event: The stop event is used to stop the CPU measurement thread after the request is completed.
Average CPU Usage: The average CPU usage during the request is calculated and logged.
"""
# Common 'model_name' variable included for modular approach
# Handles exit to release all processes at port 5000
# Date: 22/5/2024





from flask import Flask, request, jsonify
import requests
import logging
from queue import Queue
import threading
import psutil
import time
import csv
import os
import signal
import sys
import subprocess

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

def release_port(port):
    try:
        output = subprocess.check_output(["sudo", "lsof", "-t", f"-i:{port}"])
        pids = output.strip().split()
        for pid in pids:
            subprocess.check_call(["sudo", "kill", "-9", pid.decode()])
    except subprocess.CalledProcessError:
        pass

def signal_handler(sig, frame):
    print('Stopping server...')
    release_port(5000)
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)  # Added to handle SIGTERM for Gunicorn/uWSGI
    release_port(5000)  # Ensure port 5000 is free before starting
    app.run(host='0.0.0.0', port=5000, debug=False)  # Disable debug mode for stability

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
source ~/FULL/PATH/bin/activate
```

# Run the application python file ‘flaskserver.py’ ‘’ created above”:

```
python3 flaskserver.py
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


# Data Collection

Collect the logged data into the csv file and also look into the Apache benchmark output from the terminal.


# Manual 



# Running with Builtin, WSGI and uWSGI on Flask

**Always work under the Virtual Environment**

## 1. Run Builtin Server

```bash
python3 flaskserver.py
```

Perform tests on Gunicorn Server by changing the parameters.

---

## 2. Create a `wsgi.py` file (Common for both WSGI and uWSGI Servers)

```python
# wsgi.py
# In this code, the filename must be flaskserver.py. The main application file must be in the same folder.
from flaskserver import app

if __name__ == "__main__":
    app.run()
```

## 3. Run Gunicorn Server (WSGI Server)

### 3.1. Run with Gunicorn

Run Gunicorn (wsgi is the name of the `wsgi.py` file where the Gunicorn server code is mentioned) with debug information:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

OR

```bash
gunicorn -w 4 -b 0.0.0.0:5000 --log-level debug --access-logfile - --error-logfile - wsgi:app
```

Perform tests (curl or ab from another terminal) on Gunicorn (WSGI) Server by changing the parameters. Press `CTRL+C` twice to close.

---

## 4. Running with uWSGI (uWSGI Server)

Use the same `wsgi.py` file for uWSGI as well.

### 4.1. Run below:

#### 4.1.1. Option 1

```bash
uwsgi --http :5000 --module wsgi:app --processes 4 --threads 2
```

Run the `stop_uwsgi.sh` script to stop the process at port 5000 from another terminal.

OR

#### 4.1.2. Option 2

Create a `uwsgi.ini` file in the same directory as below (change the processes and threads parameters for each test):

```ini
[uwsgi]
module = wsgi:app
master = true
processes = 4
threads = 2
http = :5000
die-on-term = true
logto = ./uwsgilog.log
```

Run with uWSGI:

```bash
uwsgi --ini uwsgi.ini
```

Run the `stop_uwsgi.sh` script to stop the process at port 5000 from another terminal.

Perform tests (curl or ab from another terminal) on uWSGI Server by changing the parameters.

---

## File Structure of the Project Directory for Flask

**Mandatory**

- `flaskserver.py` [for all servers]
- `requirements.txt` [for all servers to be installed initially, if not installed]
- `ollama_api_logs.csv` [generated from the flaskserver.py after API calls]
- `wsgi.py` [for WSGI server (Gunicorn) and uWSGI server (uWSGI)]

**Optional** [for uWSGI Server handling]

- `uwsgi.ini` [for uWSGI server Option 2]
- `uwsgilog.log` [Output of logs from uwsgi.ini]

**Mandatory to Stop uWSGI Server**

- `stop_uwsgi.sh` [Shell script to stop uWSGI server to release the processes from port 5000]

---

## Always Check Processes at Port 5000 and Process Killing [OPTIONAL]

**Check for any process running at port 5000**

```bash
sudo lsof -i :5000
```

**If processes are running at port 5000, then kill them**

```bash
sudo kill -9 <PID>
```

