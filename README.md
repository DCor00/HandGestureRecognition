# Hand Gesture Recognition

A Flask-based hand gesture recognition system that uses YOLO models to detect and process hand gestures in real-time. The application supports both live webcam streams and image uploads for gesture prediction and includes basic account management functionality.

## Features

- **Real-time Gesture Detection:** 
  - Stream video from a webcam and perform live gesture recognition.
- **Image-Based Prediction:** 
  - Upload images to obtain gesture predictions.
- **Gesture Sequence Detection:** 
  - Detect specific sequences of gestures to trigger events.
- **Model Switching:** 
  - Dynamically switch between different pre-trained YOLO models.
- **Web Interface:** 
  - Simple web pages for real-time view, image uploads, and account management.
- **User Account Management (dev):** 
  - Basic account routes and models for managing users.

## Main scripts 

There is `app.py` that orchestrate the different scripts, then there are 3 mains html, css and js files linked :
- `templates/index.html`, `static/main.css`
- `static/realtime.html`, `static/css/realtime.css`, `static/js/realtime.js`
- `static/upload.html`, `static/css/upload.css`, `static/js/upload.js`

### Android app
Since there is also an Android app (developed by [surendramran](https://github.com/surendraman) and available at [YOLO Android](https://github.com/surendramaran/YOLO)) related to the project, a small Jupyter notebook called `TFLite_conversion.ipynb` is included in the repo for converting the YOLO model to TFLite.

## Directory Structure
```
.
.
├── Info.plist
├── LICENSE
├── README.md
├── TFLite_conversion.ipynb
├── __pycache__
│   └── app.cpython-312.pyc
├── accounts
│   ├── __pycache__
│   │   ├── models.cpython-312.pyc
│   │   └── routes.cpython-312.pyc
│   ├── models.py
│   └── routes.py
├── app.py
├── models
│   ├── SSDLiteMobileNetV3Large.pth
│   ├── YOLOv10n_gestures.pt
│   └── YOLOv10x_gestures.pt
├── requirements.txt
├── static
│   ├── accounts.html
│   ├── css
│   │   ├── main.css
│   │   ├── realtime.css
│   │   └── upload.css
│   ├── js
│   │   ├── realtime.js
│   │   └── upload.js
│   ├── realtime.html
│   └── upload.html
└── templates
    └── index.html
```

## Installation

### Prerequisites

- **Python 3.8+**

### Setup

1. **Clone the repository:**

    ```bash
    git clone https://github.com/DCor00/HandGestureRecognition.git
    cd HandGestureRecognition
    ```

2. **Create and activate a Python virtual environment (recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. **Install the required Python packages:**

    If a `requirements.txt` file is available:
    ```bash
    pip install -r requirements.txt
    ```
    Otherwise, install dependencies manually:
    ```bash
    pip install Flask Flask-SocketIO opencv-python numpy ultralytics
    ```

## Usage

1. **Run the application:**

    ```bash
    python app.py
    ```

    The Flask server with SocketIO support should now be running at [http://0.0.0.0:8000](http://0.0.0.0:8000).

2. **Access the Web Interface:**

    - **Home:** [http://localhost:8000](http://localhost:8000)
    - **Real-Time Video Feed:** [http://localhost:8000/realtime](http://localhost:8000/realtime)
    - **Image Upload:** [http://localhost:8000/upload](http://localhost:8000/upload)

3. **Switching Between Models with the API (example):**

    Use the `/switch_model/<model_type>` endpoint to switch between the YOLO models:
    - `nano` → Uses the `YOLOv10n_gestures.pt` model.
    - `x` → Uses the `YOLOv10x_gestures.pt` model.

    For example, to switch to the nano model, you can run:
    ```bash
    curl http://localhost:8000/switch_model/nano
    ```



## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Acknowledgments

- [Flask](https://flask.palletsprojects.com/)
- [Flask-SocketIO](https://flask-socketio.readthedocs.io/)
- [OpenCV](https://opencv.org/)
- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics)
- Thanks to all the contributors and open source projects that made this work possible.
