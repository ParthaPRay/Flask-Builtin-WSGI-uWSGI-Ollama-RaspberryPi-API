# Calls to API End Point of Flask, FastAPI and Sanic web server where Ollama is running with a given LLM
# Date: 24/5/2024


import subprocess
import json

# List of prompts
prompts = [
    "What is the capital of France?",
    "Who wrote 'To Kill a Mockingbird'?",
    "What is the largest ocean on Earth?",
    "What is 2+2?",
    "What is 5*3?",
    "What is 10/2?",
    "Why is the sky blue?",
    "What is photosynthesis?",
    "How do magnets work?",
    "Tell me a short story about a brave knight.",
    "Write a short story about a trip to the moon.",
    "Tell a short story about a lost treasure.",
    "How are you today?",
    "What is your favorite color?",
    "What do you like to do in your free time?",
    "How to make a cup of tea?",
    "How to tie a tie?",
    "How to change a tire?"
]

# API endpoint
api_url = "http://127.0.0.1:5000/generate"

# Function to run curl command
def run_curl(prompt):
    curl_command = [
        "curl", "-X", "POST", api_url,
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"prompt": prompt})
    ]
    result = subprocess.run(curl_command, capture_output=True, text=True)
    return result.stdout

# Iterate over prompts and call the API
for prompt in prompts:
    response = run_curl(prompt)
    print(f"Prompt: {prompt}")
    print(f"Response: {response}\n")
