from flask import Flask, request, jsonify, Response, send_from_directory, Blueprint, render_template
from flask_socketio import SocketIO
import cv2
import numpy as np
from ultralytics import YOLO
from collections import deque
import json
import os 
import threading
from accounts.routes import account_bp
from accounts.models import get_users, get_user, update_user, add_user


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Enable CORS for SocketIO

app.register_blueprint(account_bp)

# Gesture sequences to detect
GESTURE_SEQUENCES = {
    "unlock": ["like", "peace", "peace_inverted"],  # Example sequence
    "confetti": ["dislike", "like", "like"],  # Example sequence
    "alert": ["peace", "peace", "thumbs_down"]  # Another example
}

# Global variables for video processing
camera = None
processing = False
current_model = 'YOLOv10n_gestures.pt'
models = {
    'YOLOv10n_gestures.pt': YOLO('models/YOLOv10n_gestures.pt'),
    'YOLOv10x_gestures.pt': YOLO('models/YOLOv10x_gestures.pt')
}

# Global variables for sequence tracking
gesture_history = deque(maxlen=20)  
# sequence_triggers = {key: False for key in GESTURE_SEQUENCES.keys()}  # Tracks triggered sequences

def generate_frames():
    global camera, processing, current_model, gesture_history, sequence_triggers
    camera = cv2.VideoCapture(0)
    processing = True
    
    while processing:
        success, frame = camera.read()
        if not success:
            break
            
        # Perform detection with current model
        results = models[current_model](frame, verbose=False)
        annotated_frame = results[0].plot()
        
        # Get current gesture
        current_gesture = None
        for result in results:
            for box in result.boxes:
                current_gesture = models[current_model].names[int(box.cls)]
                break  # Only use the first detected gesture per frame
        
        # Update gesture history
        if current_gesture:
            gesture_history.append(current_gesture)
        
        # Check for gesture sequences
        for sequence_name, sequence in GESTURE_SEQUENCES.items():
            if all(gesture in list(gesture_history)[-20:] for gesture in sequence):  #and not sequence_triggers[sequence_name]:
                print(f"Sequence detected: {sequence_name}")
                # sequence_triggers[sequence_name] = True
                gesture_history = deque(maxlen=20)
                trigger_event(sequence_name)  # Trigger event via SocketIO
        
        # Encode frame and predictions
        ret, buffer = cv2.imencode('.webp', annotated_frame, [cv2.IMWRITE_WEBP_QUALITY, 50])
        frame = buffer.tobytes()
        
        # Yield frame and predictions
        yield (b'--frame\r\n'
               b'Content-Type: image/webp\r\n\r\n' + frame + b'\r\n'
               b'X-Predictions: ' + json.dumps({"gesture": current_gesture}).encode() + b'\r\n')
    
    if camera:
        camera.release()
    processing = False

def reset_sequence_trigger(sequence_name):
    """Reset the sequence trigger after a short delay."""
    import time
    time.sleep(1)  # Wait for 5 seconds before resetting
    # sequence_triggers[sequence_name] = False
    print(f"Sequence trigger reset: {sequence_name}")

# Real-time Detection Configuration
camera = None
processing = False
current_model = 'nano'
models = {
    'nano': YOLO('models/YOLOv10n_gestures.pt'),
    'x': YOLO('models/YOLOv10x_gestures.pt')
}

def trigger_event(sequence_name):
    """Handle events when a sequence is detected."""
    socketio.emit('sequence_detected', {'sequence': sequence_name})
    if sequence_name == "unlock":
        print("Unlock event triggered!")
    elif sequence_name == "alert":
        print("Alert event triggered!")
    elif sequence_name == "confetti":
        print("confetti event triggered!")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/realtime')
def realtime():
    return send_from_directory('static', 'realtime.html')




@app.route('/reset_sequence/<sequence_name>', methods=['POST'])
def reset_sequence(sequence_name):
    global sequence_triggers
    if sequence_name in sequence_triggers:
        sequence_triggers[sequence_name] = False
        return jsonify({"status": "success", "message": f"Reset {sequence_name}"}), 200
    return jsonify({"status": "error", "message": "Invalid sequence"}), 400


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stop_feed', methods=['POST'])
def stop_feed():
    global processing
    processing = False
    return jsonify({'status': 'stopped'})

@app.route('/switch_model/<model_type>')
def switch_model(model_type):
    global current_model
    if model_type in models:
        current_model = model_type
        return jsonify({"status": "success", "model": model_type})
    return jsonify({"status": "error", "message": "Invalid model"}), 400

# Image Upload Routes
@app.route('/upload')
def upload():
    return send_from_directory('static', 'upload.html')




@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    img = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(img, cv2.IMREAD_COLOR)

    if img is None:
        return jsonify({"error": "Image cannot be processed"}), 400

    results = models[current_model].predict(img)
    
    detections = []
    for result in results:
        for box in result.boxes:
            detections.append({
                "class": models[current_model].names[int(box.cls)],
                "confidence": float(box.conf),
                "bbox": box.xyxy.tolist()[0]
            })
    
    return jsonify(detections)

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    if not os.path.exists('static'):
        os.makedirs('static')
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)


