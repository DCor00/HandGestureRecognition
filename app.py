from flask import Flask, request, jsonify, Response, send_from_directory, render_template
import cv2
import numpy as np
from ultralytics import YOLO
import threading
import os

app = Flask(__name__)

# Real-time Detection Configuration
camera = None
processing = False
current_model = 'nano'
models = {
    'nano': YOLO('models/YOLOv10n_gestures.pt'),
    'x': YOLO('models/YOLOv10x_gestures.pt')
}

# Image Upload Detection Model
upload_model = models['nano']

def generate_frames():
    global camera, processing, current_model
    camera = cv2.VideoCapture(0)
    processing = True
    
    while processing:
        success, frame = camera.read()
        if not success:
            break
            
        results = models[current_model](frame, verbose=False)
        annotated_frame = results[0].plot()
        
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    if camera:
        camera.release()
    processing = False

# Main Index Route
@app.route('/')
def index():
    return render_template('index.html')

# Real-time Detection Routes
@app.route('/realtime')
def realtime():
    return send_from_directory('static', 'realtime.html')

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

    results = upload_model.predict(img)
    
    detections = []
    for result in results:
        for box in result.boxes:
            detections.append({
                "class": upload_model.names[int(box.cls)],
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
    app.run(host='0.0.0.0', port=8000, threaded=True)