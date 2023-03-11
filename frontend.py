from importlib.abc import TraversableResources
from time import time
import flask
import json
import requests
import datetime
import os
from flask import Flask, request, redirect, url_for, render_template

app = flask.Flask(__name__)
app.config["DEBUG"] = True

data_dir_name = "data"
data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), data_dir_name)
    

@app.route('/', methods = ['GET'])
def home():
    if not os.path.exists("openai-key.env"):
        #create a file
        with open("openai-key.env", "w") as f:
            f.write("OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>")
            return "Please add your OpenAI API key to the openai-key.env file"
    return render_template('index.html')
    
def openai_api_call(model, prompt, max_tokens, temperature):
    #create the request body
    request_body = {
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "stop": []
    }
    #call the openai api
    response = requests.post(
        "https://api.openai.com/v1/engines/" + model + "/completions",
        headers = {"Authorization": "Bearer " + os.environ['OPENAI_API_KEY']},
        data = json.dumps(request_body)
    )
    #return the response
    return response.json()['choices'][0]['text']

def write_response_to_log_file(response,prompt):
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    if not os.path.exists(data_dir+'/log.txt'):
        with open(data_dir+'/log.txt', 'w') as f:
            f.write("timestamp|prompt|response")
    with open(data_dir+'/log.txt', 'a') as f:
        timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        f.write(timestamp+"|{}|".format(str(prompt))+str(response)+"\n")

def write_to_json_file(response):
    timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    timestamp = timestamp.replace(" ", "_").replace(":", "-").replace("-", "_")
    with open(data_dir+'/{}_log.json'.format(timestamp), 'a') as f:
        json.dump(response, f)

@app.route('/log')
def log():
    #create a flask table with all json files
    table = ""
    with open('templates/head.txt', 'r') as f:
        for line in f:
            table += line
    with open('templates/menu.txt', 'r') as f:
        for line in f:
            table += line
    table += "<style>table, th, td {border: 1px solid black;}</style>"
    table += "<table><thead><tr><th>File</th><th>Created</th><th>Model</th><th>Prompt</th><th>Response</th></tr></thead><tbody>"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        return table + "</tbody></table>"
    #get a list of files in the data directory
    files = os.listdir(data_dir)
    #sort the files in descending order
    files.sort(reverse=True)
    #loop through the files
    data = ""
    for file in files:
        try:
                
            if file.endswith(".json"):
                #get data from file
                #create a table row
                #get the model name , prompt and response from the json file
                with open(data_dir+'/'+file, 'r') as f:
                    table += "<tr>"
                    data = json.load(f)
                    model = data['model']
                    response = data['choices'][0]['text']
                    created = data['created']
                    table += "<td>{}</td>".format(file)
                    table += "<td>{}</td>".format(created)
                    table += "<td>{}</td>".format(model)
                    table += "<td>{}</td>".format(find_prompt_from_created(created))
                    table += "<td>{}</td>".format(response)
                    table += "</tr>"
        except:
            table += "<td>{}</td><td></td><td></td><td></td><td>{}</td>".format(file,data)
    table += "</tbody></table>"
    return table

def find_prompt_from_created(created):
    created = str(created)
    with open(data_dir+'/log.txt', 'r') as f:
        for line in f:
            if created in line:
                return line.split("|")[1]
    return "Prompt not found"

@app.route('/api', methods=['POST'])
def api():
    #get the form data
    #call the openai api
    #write the response to a log file
    #write the response to a json file
    #return the response to the frontend
    key = open("openai-key.env", "r").read().split("=")[1].strip()
    model = str(request.form.get('model')).strip()
    prompt = str(request.form.get('prompt')).strip()
    max_tokens = int(str(request.form.get('max_tokens')))
    temperature = float(str(request.form.get('temperature')))
    model = model.lower()
    if model == "davinci":
        model = "text-davinci-002"
    elif model == "curie":
        model = "text-curie-001"
    elif model == "babbage":
        model = "text-babbage-001"
    elif model == "ada":
        model = "text-ada-001"
    else:
        return "Invalid model[{}]".format(model)
    response = curl_request(key,model, prompt, max_tokens, temperature)
    write_response_to_log_file(response,prompt)
    write_to_json_file(response)
    return redirect(url_for('log'))

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

@app.route('/test', methods=['GET'])
def test():
    return data_dir

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

app.run()

