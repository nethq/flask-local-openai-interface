from cgitb import text
from cmd import PROMPT
from distutils.command.build_scripts import first_line_re
from nis import cat
from operator import indexOf
from re import L
import flask
import json
import requests
import datetime
import os
from flask import Flask, request, redirect, url_for
from werkzeug.utils import secure_filename
import flask_table

class ItemTable(flask_table.Table):
    classes = ['table', 'table-striped', 'table-hover']
    prompt = flask_table.Col('Prompt')
    response = flask_table.Col('Response')
    text_response = flask_table.Col('Text Response')
    timestamp = flask_table.Col('Timestamp')
class Item(object):
    def __init__(self, prompt, response, timestamp, text_response):
        self.prompt = prompt
        self.response = response
        self.text_response = text_response
        self.timestamp = timestamp
app = Flask(__name__)
data_dir = "data/"


app = flask.Flask(__name__)
app.config["DEBUG"] = True

@app.route('/', methods=['GET'])
def home():
    #check if a req-responses folder exists, if not create it
    #create a table with the following columns:
    #model, prompt, max_tokens, temperature, response
    #prompt is a text field
    #response is a text field
    #model is a dropdown with the following options:
    #davinci, curie, babbage, ada
    #max_tokens is a number field
    #temperature is a number field
    #submit button
    #when the submit button is clicked, the form data is sent to the backend
    #the backend calls the openai api and returns the response
    #the backend then writes the response to a log file
    #the backend then writes the response to a json file
    #the backend then returns the response to the frontend
    #the frontend then displays the response in a text field
    #the frontend then displays the response in a json field
    html = "<html>"
    html += "<head>"
    html += "<title>OpenAI API</title>"
    html += "</head>"
    html += "<body>"
    html += "<h1>OpenAI API</h1>"
    html += "<a href='/log'>Log</a>"
    html += "<form action='/api' method='post'>"
    html += "<label for='model'>Model:</label>"
    html += "<select name='model' id='model'>"
    html += "<option value='davinci'>Davinci</option>"
    html += "<option value='curie'>Curie</option>"
    html += "<option value='babbage'>Babbage</option>"
    html += "<option value='ada'>Ada</option>"
    html += "</select>"
    html += "<br>"
    html += "<label for='prompt'>Prompt:</label>"
    html += "<input type='text' id='prompt' name='prompt'>"
    html += "<br>"
    html += "<label for='max_tokens'>Max Tokens:</label>"
    html += "<input type='number' id='max_tokens' name='max_tokens'>"
    html += "<br>"
    html += "<label for='temperature'>Temperature:</label>"
    #temperature should be a float from 0 to 1
    html += "<input type='number' id='temperature' name='temperature' step='0.01' min='0' max='1'>"
    html += "<br>"
    html += "<input type='submit' value='Submit'>"
    html += "</form>"
    html += "</body>"
    html += "</html>"
    return html

#list all json files and the log file 
@app.route('/log', methods=['GET'])
def log_page():
    #use the flask table to display the log file
    #use the flask table to display the json files
    table = create_flask_table_with_json_files()
    #add css to the table
    html = "<html>"
    html += "<head>"
    html += "<title>OpenAI API</title>"
    html += "<style>"
    html += "table, th, td {"
    html += "border: 1px solid black;"
    html += "border-collapse: collapse;"
    html += "}"
    html += "th, td {"
    html += "padding: 5px;"
    html += "text-align: left;"
    html += "}"
    html += "</style>"
    html += "</head>"
    html += "<body>"
    html += "<h1>OpenAI API</h1>"
    html += "<a href='/'>Home</a>"
    html += table
    html += "</body>"
    html += "</html>"
    return html

def extract_text_from_json_file(file):
    try:
        with open(file, 'r') as f:
            data = json.load(f)
            return data['choices'][0]['text']
    except:
        return 
def extract_keyvalue_from_json_file(file, key):
    try:
        with open(file, 'r') as f:
            data = json.load(f)
            return data[key]
    except:
        return
def get_prompt_from_log_file(created_at):
    with open(data_dir+'log.txt', 'r') as f:
        for line in f:
            if created_at in line:
                return line.split("|")[1].split("|")[0]
    #2022_09_16_13_47_00|test|{'id': 'cmpl-5r45tDiXUNNwfFxzMF71rbI8xYjgU', 'object': 'text_completion', 'created': 1663328805, 'model': 'text-ada-001', 'choices': [{'text': '\n\nHello World!', 'index': 0, 'logprobs': None, 'finish_reason': 'length'}], 'usage': {'prompt_tokens': 5, 'completion_tokens': 5, 'total_tokens': 10}}


def create_flask_table_with_json_files():
    table = "<table>"
    table += "<tr>"
    table += "<th>File</th>"
    table += "<th>Text</th>"
    table += "</tr>"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    #for each file in subdir tmp
    for file in os.listdir(data_dir):
        if file.endswith(".json"):
            table += "<tr>"
            table += "<td>" + file + "</td>"
            #get created from json file
            created_at = extract_keyvalue_from_json_file(data_dir + file, 'created')
            #get prompt from log file
            prompt = get_prompt_from_log_file(str(created_at))
            #get text from json file
            table += "<td>{}</td>".format(created_at)
            table += "<td>" + prompt + "</td>"
            table += "<td>" + str(extract_text_from_json_file(data_dir + file)) + "</td>"
            table += "</tr>"
    table += "</table>"


    return table

#depreceated function to create a flask table with the log file        
def create_flask_table():
    items = []
    
    #auto refresh the page every 5 seconds
    html = "<meta http-equiv='refresh' content='5'>"
    openai_log = open(data_dir+"log.txt", "r")
    for line in openai_log:
        if "error" in line:
            continue
        line = line.strip()
        line = line.split("|")
        timestamp = line[0]
        prompt = line[1]
        response = line[2]
        text_response = response.split("'text': '")
        item = Item(prompt, response, timestamp,text_response)
        items.append(item)
    openai_log.close()
    table = ItemTable(items)
    html += table.__html__()
    return html


#answer the api call
@app.route('/api', methods=['POST'])
def api():
    import pyoai
    import dotenv
    #get the form data
    #call the openai api
    #write the response to a log file
    #write the response to a json file
    #return the response to the frontend
    key = dotenv.get_key("openai-key.env","OPENAI_API_KEY")
    model = request.form.get('model').strip()
    prompt = request.form.get('prompt').strip()
    max_tokens = int(request.form.get('max_tokens'))
    temperature = float(request.form.get('temperature'))
    #check the data
    if model == None or prompt == None or max_tokens == None or temperature == None:
        return "Invalid data"
    #call the openai api
    response = curl_request(key,model, prompt, max_tokens, temperature)
    #write the response to a log file
    try:
        write_to_json_file(response)
        #write the response to a json file
    except:
        print("Error writing to json file")

    write_response_to_log_file(response,prompt)

    return response

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
    with open(data_dir+'log.txt', 'a') as f:
        timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        f.write(timestamp+"|{}|".format(str(prompt))+str(response)+"\n")

def write_to_json_file(response):
    timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    timestamp = timestamp.replace(" ", "_").replace(":", "-").replace("-", "_")
    with open(data_dir+'{}_log.json'.format(timestamp), 'a') as f:
        json.dump(response, f)

app.run()


