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
        request_id = data.get('head_commit', {}).get('id', 'unknown')  # ✅ Git commit hash
        event = {
            "request_id": request_id,
            "author": author,
            "action": "PUSH",
            "from_branch": None,
            "to_branch": to_branch,
            "timestamp": timestamp
        }
        collection.insert_one(event)

    elif event_type == 'pull_request':
        action = data['action']
        from_branch = data['pull_request']['head']['ref']
        to_branch = data['pull_request']['base']['ref']
        request_id = str(data['pull_request']['id'])  # ✅ PR ID
        merged = data['pull_request'].get('merged', False)

        if action == 'opened':
            event = {
                "request_id": request_id,
                "author": author,
                "action": "PULL_REQUEST",
                "from_branch": from_branch,
                "to_branch": to_branch,
                "timestamp": timestamp
            }
            collection.insert_one(event)

        elif action == 'closed' and merged:
            event = {
                "request_id": request_id,
                "author": author,
                "action": "MERGE",
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
        if r['action'] == 'PUSH':
            msg = f"{r['author']} pushed to {r['to_branch']} on {format_time(r['timestamp'])}"
        elif r['action'] == 'PULL_REQUEST':
            msg = f"{r['author']} submitted a pull request from {r['from_branch']} to {r['to_branch']} on {format_time(r['timestamp'])}"
        elif r['action'] == 'MERGE':
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
