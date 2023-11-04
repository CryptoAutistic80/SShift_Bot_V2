from flask import Flask, render_template, send_from_directory
from threading import Thread
from datetime import datetime
import os  # Import os to access environment variables

app = Flask(__name__, static_folder='static')

@app.route('/keepalive', methods=['GET', 'HEAD'])
def keep_alive():
    return f"Keep alive check at {datetime.utcnow()} UTC", 200

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/members')
def members():
    return render_template('members.html')

@app.route('/charts/<path:filename>', methods=['GET'])
def charts(filename):
    return send_from_directory('static/charts', filename)

@app.route('/view_chart/<path:filename>', methods=['GET'])
def view_chart(filename):
    return render_template('chart.html', filename=filename)

@app.route('/robots.txt', methods=['GET'])
def robots():
    return send_from_directory('static', 'robots.txt')

def run():
    port = int(os.environ.get('PORT', 8080))  # Get the PORT environment variable, default to 8080 if not found
    app.run(host="0.0.0.0", port=port)

def start_server():
    t = Thread(target=run)
    t.start()

if __name__ == '__main__':
    start_server()