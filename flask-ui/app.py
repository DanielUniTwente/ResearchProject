# app.py

from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    user_message = request.json.get('message')
    response = requests.post('http://localhost:5005/webhooks/rest/webhook', json={"message": user_message})
    # print(response.json())
    return jsonify(response.json())

if __name__ == '__main__':
    app.run(debug=True)
