from flask import Flask, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import cv2
from ultralytics import YOLO
import secrets
import json
from collections import deque
from models import User

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")
# Python shell
with app.app_context():
    new_user = User(username="john", gesture_sequence=["thumbs_up", "peace", "fist"])
    db.session.add(new_user)
    db.session.commit()

# Import User model from models.py
from models import User

# Gesture detection setup
camera = None
processing = False
current_model = YOLO('models/YOLOv10n_gestures.pt')
gesture_history = deque(maxlen=30)

# Authentication middleware
def authenticate_user(func):
    def wrapper(*args, **kwargs):
        session_token = request.headers.get('Authorization')
        if not session_token or not User.query.filter_by(session_token=session_token).first():
            return jsonify({"error": "Unauthorized"}), 401
        return func(*args, **kwargs)
    return wrapper

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    # Compare received gesture sequence with stored sequence
    received_sequence = data.get('gesture_sequence')
    if received_sequence != user.gesture_sequence:
        return jsonify({"error": "Invalid gesture sequence"}), 401
        
    # Generate session token
    session_token = secrets.token_hex(16)
    user.session_token = session_token
    db.session.commit()
    
    return jsonify({"session_token": session_token})

@app.route('/update-sequence', methods=['POST'])
@authenticate_user
def update_sequence():
    user = User.query.filter_by(session_token=request.headers.get('Authorization')).first()
    new_sequence = request.json.get('new_sequence')
    
    # Validate sequence length
    if len(new_sequence) < 3:
        return jsonify({"error": "Sequence too short"}), 400
        
    user.gesture_sequence = new_sequence
    db.session.commit()
    
    return jsonify({"message": "Sequence updated successfully"})

def generate_frames():
    global camera, processing, gesture_history
    camera = cv2.VideoCapture(0)
    processing = True
    
    while processing:
        success, frame = camera.read()
        if not success:
            break
            
        results = current_model(frame, verbose=False)
        annotated_frame = results[0].plot()
        
        current_gesture = None
        for result in results:
            for box in result.boxes:
                current_gesture = current_model.names[int(box.cls)]
                break

        if current_gesture:
            gesture_history.append(current_gesture)
            socketio.emit('gesture_update', {'gesture': current_gesture})
        
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, host='0.0.0.0', port=8000)