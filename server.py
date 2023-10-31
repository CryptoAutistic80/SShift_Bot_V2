from flask import Flask, render_template, send_from_directory
from threading import Thread

app = Flask(__name__, static_folder='static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/members')
def members():
    return render_template('members.html')

@app.route('/charts/<path:filename>', methods=['GET'])
def charts(filename):
    return send_from_directory('static/charts', filename)

def run():
    app.run(host="0.0.0.0", port=8080)

def start_server():
    t = Thread(target=run)
    t.start()

if __name__ == '__main__':
    start_server()