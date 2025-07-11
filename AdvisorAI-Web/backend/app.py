from flask import Flask, request, session, jsonify
from flask_session import Session
from flask_cors import CORS
import firebase_admin
from firebase_admin import auth, credentials
import os
from flask_jwt_extended import JWTManager

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "supersecretkey")
jwt = JWTManager(app)

# Enable CORS for all routes and allow credentials (cookies)
CORS(app, supports_credentials=True, origins=[
    "http://localhost:3000",  # React dev server
    # Add your production frontend URL here
])

# Initialize Firebase Admin SDK
cred = credentials.Certificate("path/to/your/firebase-service-account.json")
firebase_admin.initialize_app(cred)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    id_token = data.get('idToken')
    if not id_token:
        return jsonify({"error": "Missing idToken"}), 400
    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        session['user'] = uid
        return jsonify({"message": "Login successful", "uid": uid}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({"message": "Logged out"}), 200

@app.route('/me', methods=['GET'])
def me():
    uid = session.get('user')
    if not uid:
        return jsonify({"error": "Not authenticated"}), 401
    try:
        user = auth.get_user(uid)
        return jsonify({
            "uid": user.uid,
            "email": user.email,
            "display_name": user.display_name
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)