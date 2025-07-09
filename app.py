from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# ✅ MongoDB Atlas Connection — update with your actual credentials
MONGO_URI = "mongodb+srv://gowthamreddy:Gowtham2004@cluster0.q5mzsyh.mongodb.net/github_events?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.github_events
collection = db.events

# ✅ GitHub Webhook Receiver
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    event_type = request.headers.get('X-GitHub-Event')

    payload = {}

    if event_type == "push":
        payload["author"] = data["pusher"]["name"]
        payload["to_branch"] = data["ref"].split("/")[-1]
        payload["timestamp"] = datetime.utcnow().strftime("%d %B %Y - %I:%M %p UTC")
        payload["type"] = "push"

    elif event_type == "pull_request":
        pr = data["pull_request"]
        payload["author"] = pr["user"]["login"]
        payload["from_branch"] = pr["head"]["ref"]
        payload["to_branch"] = pr["base"]["ref"]
        payload["timestamp"] = datetime.utcnow().strftime("%d %B %Y - %I:%M %p UTC")
        payload["type"] = "pull_request"

    elif event_type == "merge":  # Optional (brownie points)
        payload["author"] = data["sender"]["login"]
        payload["from_branch"] = data["pull_request"]["head"]["ref"]
        payload["to_branch"] = data["pull_request"]["base"]["ref"]
        payload["timestamp"] = datetime.utcnow().strftime("%d %B %Y - %I:%M %p UTC")
        payload["type"] = "merge"

    else:
        return jsonify({"msg": "Unhandled event type"}), 200

    collection.insert_one(payload)
    return jsonify({"msg": "Event stored"}), 200

# ✅ Serve events to frontend
@app.route('/events')
def get_events():
    data = list(collection.find({}, {"_id": 0}).sort("_id", -1))
    return jsonify(data)

# ✅ Serve frontend page
@app.route('/')
def index():
    return render_template('index.html')

# ✅ Start the Flask server
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
