import datetime
from hashlib import md5
from sqlite3 import OperationalError
import openai
import dotenv
import json
import requests
import sys

# curl https://api.openai.com/v1/completions \
#   -H 'Content-Type: application/json' \
#   -H 'Authorization: Bearer YOUR_API_KEY' \
#   -d '{
#   "model": "text-davinci-002",
#   "prompt": "Say this is a test",
#   "max_tokens": 6,
#   "temperature": 0
# }'

def curl_request(key,model, prompt, max_tokens, temperature):
    url = "https://api.openai.com/v1/completions"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(key)
    }
    data = {
        "model": model,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.json()

def write_response_to_log_file(response,prompt):
    with open('log.txt', 'a') as f:
        timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        f.write(timestamp+"|{}|".format(str(prompt))+str(response)+"\n")

def write_to_json_file(response):
    timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    timestamp = timestamp.replace(" ", "_").replace(":", "-").replace("-", "_")
    with open('{}_log.json'.format(timestamp), 'a') as f:
        json.dump(response, f)
    

def main():
    dotenv.load_dotenv()
    key = dotenv.get_key('openai-key.env', 'OPENAI_API_KEY')
    print("OPENAI_KEY: {}".format(str(hash(key))))
    print("Which model would you like to use?")
    print("1. davinci\n2. curie\n3. babbage\n4. ada")
    model = input("Enter the number of the model you would like to use: ")
    if model == "1":
        model = "text-davinci-002"
    elif model == "2":
        model = "text-curie-001"
    elif model == "3":
        model = "text-babbage-001"
    elif model == "4":
        model = "text-ada-001"
    else:
        print("Invalid model")
        sys.exit()
    print("Reading the prompt until EOF (Ctrl+D)")
    prompt = ""
    while True:
        try:
            line = input()
        except EOFError:
            break
        prompt += line + " "
    print("Prompt = {}".format(str(prompt)))
    max_tokens = input("Enter the max number of tokens: ")
    temperature = input("Enter the temperature: ")
    json_resp = curl_request(key, model, prompt, int(str(max_tokens).strip()), float(str(temperature).strip()))
    print(json_resp.get('choices')[0].get('text'))  
    write_response_to_log_file(json_resp,prompt)
    write_to_json_file(json_resp)

if __name__ == "__main__":
    main()

