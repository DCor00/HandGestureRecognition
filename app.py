from flask import Flask, request, jsonify, Response, send_from_directory
from flask_socketio import SocketIO
import cv2
import numpy as np
from ultralytics import YOLO
from collections import deque
import json
import threading

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Enable CORS for SocketIO

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
gesture_history = deque(maxlen=100)  # Stores last 10 detected gestures
sequence_triggers = {key: False for key in GESTURE_SEQUENCES.keys()}  # Tracks triggered sequences

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
            if list(gesture_history)[-len(sequence):] == sequence and not sequence_triggers[sequence_name]:
                print(f"Sequence detected: {sequence_name}")
                sequence_triggers[sequence_name] = True
                trigger_event(sequence_name)  # Trigger event via SocketIO
        
        # Encode frame and predictions
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame = buffer.tobytes()
        
        # Yield frame and predictions
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
               b'X-Predictions: ' + json.dumps({"gesture": current_gesture}).encode() + b'\r\n')
    
    if camera:
        camera.release()
    processing = False

def reset_sequence_trigger(sequence_name):
    """Reset the sequence trigger after a short delay."""
    import time
    time.sleep(5)  # Wait for 5 seconds before resetting
    sequence_triggers[sequence_name] = False
    print(f"Sequence trigger reset: {sequence_name}")


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
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stop_feed', methods=['POST'])
def stop_feed():
    global processing
    processing = False
    return jsonify({'status': 'stopped'})

@app.route('/switch_model/<model_type>')
def switch_model(model_type):
    global current_model
    valid_models = {
        'nano': 'YOLOv10n_gestures.pt',
        'x': 'YOLOv10x_gestures.pt'
    }
    
    if model_type in valid_models:
        model_path = f"models/{valid_models[model_type]}"
        
        try:
            # Load the new model
            models[model_type] = YOLO(model_path)
            current_model = model_type
            return jsonify({
                "status": "success",
                "model": model_type,
                "message": f"Switched to {model_type} model"
            }), 200
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Failed to load model: {str(e)}"
            }), 500
    
    return jsonify({
        "status": "error",
        "message": "Invalid model specified"
    }), 400

@app.route('/reset_sequence/<sequence_name>', methods=['POST'])
def reset_sequence(sequence_name):
    global sequence_triggers
    if sequence_name in sequence_triggers:
        sequence_triggers[sequence_name] = False
        return jsonify({"status": "success", "message": f"Reset {sequence_name}"}), 200
    return jsonify({"status": "error", "message": "Invalid sequence"}), 400

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)