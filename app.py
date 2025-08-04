from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# one admin user (change password before production)
USERS = {"admin":"supersecret"}

@app.route("/admin/login", methods=["POST"])
def login():
    data = request.json or {}
    u,p = data.get("username"), data.get("password")
    if USERS.get(u)==p:
        return jsonify({"status":"success","token":"faketoken123"})
    return jsonify({"status":"error","message":"Invalid credentials"}), 401

if __name__=="__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
