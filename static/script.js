const video = document.getElementById('video');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const modelButtons = document.querySelectorAll('.model-select');
let streamActive = false;

// Initialize video stream
function initVideoStream() {
    video.src = '/video_feed';
    video.onloadedmetadata = () => {
        video.play();
        streamActive = true;
        startBtn.disabled = true;
        stopBtn.disabled = false;
    };
}

// Start detection
startBtn.addEventListener('click', () => {
    if (!streamActive) {
        initVideoStream();
    }
});

// Stop detection
stopBtn.addEventListener('click', async () => {
    if (streamActive) {
        try {
            const response = await fetch('/stop_feed', {
                method: 'POST'
            });
            
            if (response.ok) {
                video.src = '';
                streamActive = false;
                startBtn.disabled = false;
                stopBtn.disabled = true;
            }
        } catch (error) {
            console.error('Error stopping stream:', error);
        }
    }
});

// Model switching
modelButtons.forEach(button => {
    button.addEventListener('click', async (e) => {
        if (!streamActive) return;
        
        const model = e.target.dataset.model;
        try {
            const response = await fetch('/switch_model', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ model: model })
            });
            
            if (response.ok) {
                modelButtons.forEach(btn => btn.classList.remove('active'));
                e.target.classList.add('active');
            }
        } catch (error) {
            console.error('Error switching model:', error);
        }
    });
});

// Initialize with start button enabled
window.addEventListener('load', () => {
    stopBtn.disabled = true;
});