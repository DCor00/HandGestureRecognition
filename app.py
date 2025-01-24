from flask import Flask, request, jsonify, Response, send_from_directory
import cv2
import numpy as np
from ultralytics import YOLO
import threading

app = Flask(__name__)

# Global variables for video processing
camera = None
processing = False
current_model = 'YOLOv10n_gestures.pt'
models = {
    'YOLOv10n_gestures.pt': YOLO('models/YOLOv10n_gestures.pt'),
    'YOLOv10x_gestures.pt': YOLO('models/YOLOv10x_gestures.pt')
}

def generate_frames():
    global camera, processing, current_model
    camera = cv2.VideoCapture(0)
    processing = True
    
    while processing:
        success, frame = camera.read()
        if not success:
            break
            
        # Perform detection with current model
        results = models[current_model](frame, verbose=False)
        annotated_frame = results[0].plot()
        
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    if camera:
        camera.release()
    processing = False

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

@app.route('/switch_model', methods=['POST'])
def switch_model():
    global current_model
    data = request.json
    new_model = data.get('model')
    
    if new_model in models:
        current_model = new_model
        return jsonify({'status': 'success', 'model': current_model})
    
    return jsonify({'status': 'error', 'message': 'Invalid model'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, threaded=True)