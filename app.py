from flask import Flask, request, jsonify, send_from_directory
from ultralytics import YOLO
import cv2
import numpy as np
import os

app = Flask(__name__)
model = YOLO("YOLOv10x_gestures.pt")


# Serve frontend files
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)


@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    # Read the file in memory (it's sent as binary data)
    img = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(img, cv2.IMREAD_COLOR)

    if img is None:
        return jsonify({"error": "Image cannot be processed"}), 400

    results = model.predict(img)

    # Process results
    detections = []
    for result in results:
        for box in result.boxes:
            detections.append({
                "class": model.names[int(box.cls)],
                "confidence": float(box.conf),
                "bbox": box.xyxy.tolist()[0]
            })
    
    return jsonify(detections)


if __name__ == '__main__':
    # Create static folder if not exists
    if not os.path.exists('static'):
        os.makedirs('static')
        
    app.run(host='0.0.0.0', port=5000)
