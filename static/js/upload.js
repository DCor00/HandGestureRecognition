// Get references to DOM elements
const fileInput = document.getElementById('fileInput');
const captureButton = document.getElementById('captureButton');
const submitButton = document.getElementById('submitButton');
const webcam = document.getElementById('webcam');
const webcamCanvas = document.getElementById('webcamCanvas');
const resultsDiv = document.getElementById('results');
const context = webcamCanvas.getContext('2d');
let currentImage = null; // Holds the current image (either captured or uploaded)
let stream; // Holds webcam stream
const loadingElement = document.querySelector('.loading');

// Event listener for the submit button (for sending the image to the server)
submitButton.addEventListener('click', async () => {
    if (!currentImage) { // Check if there is an image to process
        alert('Please upload or capture an image first.');
        return;
    }

    // Show loading spinner while processing
    loadingElement.style.display = 'block';
    resultsDiv.innerHTML = '';

    try {
        const formData = new FormData();
        const blob = dataURItoBlob(currentImage); // Convert image data URI to Blob
        formData.append('file', blob, 'image.jpg');

        // Send the image to the server for predictions
        const response = await fetch('/predict', {
            method: 'POST',
            body: formData
        });

        const detections = await response.json(); // Get the prediction results
        displayResults(detections); // Display results

        // Display the image with detections on a canvas
        const img = new Image();
        img.onload = () => {
            drawDetections('webcamCanvas', img, detections);
        };
        img.src = currentImage;
    } catch (error) {
        console.error('Error:', error);
        resultsDiv.innerHTML = '<p class="text-danger">An error occurred while processing the image.</p>';
    } finally {
        // Hide loading spinner
        loadingElement.style.display = 'none';
    }
});

// Set up webcam capture when capture button is clicked
captureButton.addEventListener('click', async () => {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        // Access webcam stream
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        webcam.style.display = 'block';
        webcam.srcObject = stream;

        webcam.addEventListener('loadeddata', () => {
            // Draw webcam image to canvas once it's loaded
            context.drawImage(webcam, 0, 0, webcamCanvas.width, webcamCanvas.height);
            webcam.style.display = 'none';
            currentImage = webcamCanvas.toDataURL('image/jpeg'); // Save the image as Data URI
        });
    } else {
        alert('Camera not supported on this device.');
    }
});

// Handle file input change for image upload
fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    const reader = new FileReader();
    reader.onload = () => {
        const img = new Image();
        img.onload = () => {
            // Draw uploaded image on canvas
            context.clearRect(0, 0, webcamCanvas.width, webcamCanvas.height);
            context.drawImage(img, 0, 0, webcamCanvas.width, webcamCanvas.height);
            currentImage = webcamCanvas.toDataURL('image/jpeg'); // Save the image as Data URI
        };
        img.src = reader.result;
    };
    if (file) {
        reader.readAsDataURL(file); // Read the file as Data URI
    }
});

// Helper function to convert data URI to Blob
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

// Draw bounding boxes and labels on the canvas based on detection results
function drawDetections(canvasId, imageElement, detections) {
    const canvas = document.getElementById(canvasId);
    const ctx = canvas.getContext('2d');

    canvas.width = imageElement.width;
    canvas.height = imageElement.height;
    ctx.drawImage(imageElement, 0, 0, canvas.width, canvas.height);

    detections.forEach(detection => {
        const [x1, y1, x2, y2] = detection.bbox;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.rect(x1, y1, x2 - x1, y2 - y1); // Draw bounding box
        ctx.stroke();
        ctx.font = '16px Arial';
        ctx.fillStyle = 'red';
        ctx.fillText(`${detection.class}: ${Math.round(detection.confidence * 100)}%`, x1, y1 - 10); // Display label and confidence
    });
}

// Display detection results in the results section
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
        resultsDiv.appendChild(result); // Append results to the DOM
    });
}
