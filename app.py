# Import necessary libraries
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

# Initialize the Flask app and SocketIO for real-time communication
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  

# Register the account-related routes
app.register_blueprint(account_bp)

# Define gesture sequences for specific actions (e.g., unlocking, confetti)
GESTURE_SEQUENCES = {
    "unlock": ["like", "peace", "peace_inverted"],
    "confetti": ["dislike", "like", "like"],
    "alert": ["peace", "peace", "thumbs_down"]
}

# Global variables for video processing and model configuration
camera = None
processing = False
current_model = 'YOLOv10n_gestures.pt'  # Default model
models = {
    'YOLOv10n_gestures.pt': YOLO('models/YOLOv10n_gestures.pt'),
    'YOLOv10x_gestures.pt': YOLO('models/YOLOv10x_gestures.pt')
}

# A deque to store the gesture history (used to detect sequences)
gesture_history = deque(maxlen=20)  # Limit to last 20 gestures

# Function to generate video frames for real-time processing
def generate_frames():
    global camera, processing, current_model, gesture_history
    camera = cv2.VideoCapture(0)  # Start camera capture
    processing = True
    
    while processing:
        success, frame = camera.read()  # Read frame from camera
        if not success:
            break
            
        # Run gesture detection on the frame using the current model
        results = models[current_model](frame, verbose=False)
        annotated_frame = results[0].plot()  # Annotate frame with detection results
        
        current_gesture = None
        # Identify the detected gesture from the results
        for result in results:
            for box in result.boxes:
                current_gesture = models[current_model].names[int(box.cls)]
                break  # Only use the first detected gesture
        
        # Update gesture history with the detected gesture
        if current_gesture:
            gesture_history.append(current_gesture)
        
        # Check if any gesture sequence is detected
        for sequence_name, sequence in GESTURE_SEQUENCES.items():
            if all(gesture in list(gesture_history)[-20:] for gesture in sequence):
                print(f"Sequence detected: {sequence_name}")
                gesture_history = deque(maxlen=20)  # Reset history
                trigger_event(sequence_name)  # Trigger event via SocketIO
        
        # Encode the annotated frame as a webp image
        ret, buffer = cv2.imencode('.webp', annotated_frame, [cv2.IMWRITE_WEBP_QUALITY, 50]) # to change the quality for performance
        frame = buffer.tobytes()
        
        # Frame and predictions to be sent to client
        yield (b'--frame\r\n'
               b'Content-Type: image/webp\r\n\r\n' + frame + b'\r\n'
               b'X-Predictions: ' + json.dumps({"gesture": current_gesture}).encode() + b'\r\n')
    
    if camera:
        camera.release()  # Release the camera when done
    processing = False

# Reset the sequence trigger
def reset_sequence_trigger(sequence_name):
    import time
    time.sleep(1)  # Delay 
    print(f"Sequence trigger reset: {sequence_name}")

# Trigger event when a gesture sequence is detected
def trigger_event(sequence_name):
    """Handle events when a sequence is detected."""
    socketio.emit('sequence_detected', {'sequence': sequence_name})
    if sequence_name == "unlock":
        print("Unlock event triggered!")
    elif sequence_name == "alert":
        print("Alert event triggered!")
    elif sequence_name == "confetti":
        print("Confetti event triggered!")

# Basic route to render the main index page
@app.route('/')
def index():
    return render_template('index.html')

# Route for the real-time detection page
@app.route('/realtime')
def realtime():
    return send_from_directory('static', 'realtime.html')

# Route to reset a sequence's state (stopping gesture recognition for a given sequence)
@app.route('/reset_sequence/<sequence_name>', methods=['POST'])
def reset_sequence(sequence_name):
    global sequence_triggers
    if sequence_name in sequence_triggers:
        sequence_triggers[sequence_name] = False
        return jsonify({"status": "success", "message": f"Reset {sequence_name}"}), 200
    return jsonify({"status": "error", "message": "Invalid sequence"}), 400

# Route to video feed for real-time processing
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Route to stop video feed 
@app.route('/stop_feed', methods=['POST'])
def stop_feed():
    global processing
    processing = False
    return jsonify({'status': 'stopped'})

# Route to switch between different detection models
@app.route('/switch_model/<model_type>')
def switch_model(model_type):
    global current_model
    if model_type in models:
        current_model = model_type
        return jsonify({"status": "success", "model": model_type})
    return jsonify({"status": "error", "message": "Invalid model"}), 400

# Route to upload an image for gesture prediction
@app.route('/upload')
def upload():
    return send_from_directory('static', 'upload.html')

# Route to handle image prediction
@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    img = np.frombuffer(file.read(), np.uint8)  # Convert file to image array
    img = cv2.imdecode(img, cv2.IMREAD_COLOR)  # Decode image
    
    if img is None:
        return jsonify({"error": "Image cannot be processed"}), 400

    # Run detection on the uploaded image
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

# Route to serve static files from the 'static' folder
@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

# Main entry point of the application
if __name__ == '__main__':
    if not os.path.exists('static'):
        os.makedirs('static')  # Ensure the static folder exists
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)
