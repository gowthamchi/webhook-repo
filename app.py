from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client.webhookDB
collection = db.events

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    event_type = request.headers.get('X-GitHub-Event')
    author = data.get('pusher', {}).get('name') or data.get('sender', {}).get('login')
    timestamp = datetime.utcnow().isoformat()

    if event_type == 'push':
        ref = data.get('ref', '')
        to_branch = ref.split('/')[-1]
        event = {
            "author": author,
            "type": "push",
            "to_branch": to_branch,
            "timestamp": timestamp
        }
        collection.insert_one(event)

    elif event_type == 'pull_request':
        action = data['action']
        if action == 'opened' or action == 'closed':
            from_branch = data['pull_request']['head']['ref']
            to_branch = data['pull_request']['base']['ref']
            merged = data['pull_request'].get('merged', False)
            event_type_label = "merge" if merged else "pull_request"
            event = {
                "author": author,
                "type": event_type_label,
                "from_branch": from_branch,
                "to_branch": to_branch,
                "timestamp": timestamp
            }
            collection.insert_one(event)

    return "OK", 200

@app.route('/events')
def events():
    results = collection.find().sort("timestamp", -1)
    formatted = []
    for r in results:
        if r['type'] == 'push':
            msg = f"{r['author']} pushed to {r['to_branch']} on {format_time(r['timestamp'])}"
        elif r['type'] == 'pull_request':
            msg = f"{r['author']} submitted a pull request from {r['from_branch']} to {r['to_branch']} on {format_time(r['timestamp'])}"
        elif r['type'] == 'merge':
            msg = f"{r['author']} merged branch {r['from_branch']} to {r['to_branch']} on {format_time(r['timestamp'])}"
        formatted.append(msg)
    return jsonify(formatted)

@app.route('/')
def index():
    return render_template('index.html')

def format_time(timestamp):
    dt = datetime.fromisoformat(timestamp)
    return dt.strftime('%d %B %Y - %I:%M %p UTC')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
