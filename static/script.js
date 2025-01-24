const fileInput = document.getElementById('fileInput');
const captureButton = document.getElementById('captureButton');
const submitButton = document.getElementById('submitButton');
const webcam = document.getElementById('webcam');
const webcamCanvas = document.getElementById('webcamCanvas');
const resultsDiv = document.getElementById('results');
const context = webcamCanvas.getContext('2d');
let currentImage = null;
let stream;

// Add this at the top with other DOM element references
const loadingElement = document.querySelector('.loading');

submitButton.addEventListener('click', async () => {
    if (!currentImage) {
        alert('Please upload or capture an image first.');
        return;
    }

    // Show loading spinner
    loadingElement.style.display = 'block';
    resultsDiv.innerHTML = '';

    try {
        const formData = new FormData();
        const blob = dataURItoBlob(currentImage);
        formData.append('file', blob, 'image.jpg');

        const response = await fetch('/predict', {
            method: 'POST',
            body: formData
        });

        const detections = await response.json();
        displayResults(detections);

        const img = new Image();
        img.onload = () => {
            drawDetections('webcamCanvas', img, detections);
        };
        img.src = currentImage;
    } catch (error) {
        console.error('Error:', error);
        resultsDiv.innerHTML = '<p class="text-danger">An error occurred while processing the image.</p>';
    } finally {
        // Hide loading spinner whether successful or not
        loadingElement.style.display = 'none';
    }
});

// Set up webcam capture
captureButton.addEventListener('click', async () => {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        webcam.style.display = 'block';
        webcam.srcObject = stream;

        webcam.addEventListener('loadeddata', () => {
            context.drawImage(webcam, 0, 0, webcamCanvas.width, webcamCanvas.height);
            webcam.style.display = 'none';
            currentImage = webcamCanvas.toDataURL('image/jpeg');
        });
    } else {
        alert('Camera not supported on this device.');
    }
});

// Handle file input change (image upload)
fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    const reader = new FileReader();
    reader.onload = () => {
        const img = new Image();
        img.onload = () => {
            context.clearRect(0, 0, webcamCanvas.width, webcamCanvas.height);
            context.drawImage(img, 0, 0, webcamCanvas.width, webcamCanvas.height);
            currentImage = webcamCanvas.toDataURL('image/jpeg');
        };
        img.src = reader.result;
    };
    if (file) {
        reader.readAsDataURL(file);
    }
});



function dataURItoBlob(dataURI) {
    const byteString = atob(dataURI.split(',')[1]);
    const mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];
    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    for (let i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ab], { type: mimeString });
}

function drawDetections(canvasId, imageElement, detections) {
    const canvas = document.getElementById(canvasId);
    const ctx = canvas.getContext('2d');

    canvas.width = imageElement.width;
    canvas.height = imageElement.height;
    ctx.drawImage(imageElement, 0, 0, canvas.width, canvas.height);

    detections.forEach(detection => {
        const [x1, y1, x2, y2] = detection.bbox;
        // ctx.strokeStyle = 'red';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.rect(x1, y1, x2 - x1, y2 - y1);
        ctx.stroke();
        ctx.font = '16px Arial';
        ctx.fillStyle = 'red';
        ctx.fillText(`${detection.class}: ${Math.round(detection.confidence * 100)}%`, x1, y1 - 10);
    });
}

function displayResults(detections) {
    resultsDiv.innerHTML = '';
    detections.forEach((detection) => {
        const { class: gestureClass, confidence, bbox } = detection;
        const result = document.createElement('div');
        result.classList.add('detection-card');
        result.innerHTML = `
            <div class="detection-item">
                <span>Gesture:</span>
                <span>${gestureClass}</span>
            </div>
            <div class="detection-item">
                <span>Confidence:</span>
                <span>${(confidence * 100).toFixed(2)}%</span>
            </div>
            <div class="confidence-bar">
                <div class="confidence-fill" style="width: ${confidence * 100}%"></div>
            </div>
            <div class="detection-item">
                <span>Bounding Box:</span>
                <span>${bbox.map(coord => Math.round(coord)).join(', ')}</span>
            </div>
        `;
        resultsDiv.appendChild(result);
    });
}