from flask import Flask, send_from_directory
from threading import Thread

app = Flask(__name__, static_folder='static')

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/style.css')
def serve_style():
    return send_from_directory('static', 'style.css')

@app.route('/Page Media/bot_pfp.gif')
def serve_gif():
    return send_from_directory('static/Page Media', 'bot_pfp.gif')

def run():
    app.run(host="0.0.0.0", port=8080)

def start_server():
    t = Thread(target=run)
    t.start()
