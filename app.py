from flask import request, jsonify
import json
import os

NOTIF_FILE = 'notifications.json'

def load_notifications():
    if not os.path.exists(NOTIF_FILE):
        return []
    with open(NOTIF_FILE, 'r') as f:
        return json.load(f)

def save_notifications(notifs):
    with open(NOTIF_FILE, 'w') as f:
        json.dump(notifs, f, indent=2)

# Admin: Send notification
@app.route('/api/notifications', methods=['POST'])
def send_notification():
    data = request.json
    message = data.get('message')
    users = data.get('users', [])  # Empty = all
    notif = {
        "message": message,
        "users": users,
        "timestamp": datetime.utcnow().isoformat(),
        "id": str(uuid.uuid4()),
        "read_by": []
    }
    notifs = load_notifications()
    notifs.append(notif)
    save_notifications(notifs)
    return jsonify({"success": True})

# Client: Fetch notifications
@app.route('/api/fetch_notifications', methods=['POST'])
def fetch_notifications():
    data = request.json
    username = data.get('username')
    notifs = load_notifications()
    result = []
    for n in notifs:
        if (not n['users'] or username in n['users']) and username not in n.get("read_by", []):
            result.append({"id": n["id"], "message": n["message"]})
    return jsonify({"notifications": result})

# Client: Mark as read
@app.route('/api/mark_notification', methods=['POST'])
def mark_notification():
    data = request.json
    notif_id = data.get('id')
    username = data.get('username')
    notifs = load_notifications()
    for n in notifs:
        if n['id'] == notif_id:
            if "read_by" not in n:
                n["read_by"] = []
            if username not in n["read_by"]:
                n["read_by"].append(username)
            break
    save_notifications(notifs)
    return jsonify({"success": True})
