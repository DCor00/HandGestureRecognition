const video = document.getElementById('video');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
let streamController = null;
let isStreamActive = false;

// Add this helper function at the top
function setModelButtonsState(disabled, loadingButton = null) {
    document.querySelectorAll('.model-select').forEach(btn => {
        btn.disabled = disabled;
        if (loadingButton && btn === loadingButton) {
            btn.innerHTML = disabled 
                ? `<span class="btn-loading">🔄 Switching...</span>`
                : btn.dataset.originalText;
        } else if (!disabled) {
            btn.innerHTML = btn.dataset.originalText;
        }
    });
}


async function startStream() {
    try {
        // Immediately update UI states
        startBtn.disabled = true;
        stopBtn.disabled = true;
        startBtn.innerHTML = '⌛ Starting...';
        
        // Add cache-busting parameter
        const timestamp = Date.now();
        video.src = `/video_feed?t=${timestamp}`;
        
        // Initialize stream controller
        streamController = new AbortController();
        
        // Start stream control
        await fetch(`/control_stream/start`, {
            signal: streamController.signal
        });
        
        // Update UI states after successful start
        isStreamActive = true;
        startBtn.innerHTML = '▶ Stream Running';
        stopBtn.disabled = false;
        
        // Handle video metadata load
        video.onloadedmetadata = () => {
            video.play().catch(error => {
                console.error('Video play failed:', error);
                stopStream();
            });
        };

        // Handle video errors
        video.onerror = () => {
            console.error('Video stream error');
            stopStream();
        };
        
    } catch (error) {
        console.error('Stream start failed:', error);
        stopStream();
    }
}

async function stopStream() {
    try {
        if (streamController) {
            // Update UI states immediately
            isStreamActive = false;
            startBtn.disabled = true;
            stopBtn.disabled = true;
            stopBtn.innerHTML = '⌛ Stopping...';
            
            await fetch(`/control_stream/stop`);
            streamController.abort();
        }
    } catch (error) {
        console.error('Stream stop error:', error);
    } finally {
        // Reset UI states
        video.src = '';
        streamController = null;
        startBtn.disabled = false;
        stopBtn.disabled = true;
        startBtn.innerHTML = '▶ Start Stream';
        stopBtn.innerHTML = '⏹ Stop Stream';
    }
}


// Modified model selection handler
// Updated model switching with proper error handling
document.querySelectorAll('.model-select').forEach(button => {
    button.addEventListener('click', async (e) => {
        const targetButton = e.target.closest('.model-select');
        if (!targetButton) return;

        const modelType = targetButton.dataset.modelType;
        console.log('Attempting to switch to:', modelType);

        try {
            // Show loading state
            targetButton.innerHTML = '🔄 Switching...';
            targetButton.disabled = true;

            const response = await fetch(`/switch_model/${modelType}`);
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.message || 'Failed to switch model');
            }

            // Update UI only after successful switch
            document.querySelectorAll('.model-select').forEach(btn => {
                btn.classList.remove('active');
                btn.disabled = false;
                btn.innerHTML = btn.dataset.originalText;
            });
            
            targetButton.classList.add('active');
            console.log('Model switched successfully:', modelType);
            
            // Restart stream if it was active
            if (isStreamActive) {
                await stopStream();
                await startStream();
            }
            
        } catch (error) {
            console.error('Model switch failed:', error);
            alert(`Model switch failed: ${error.message}`);
            // Reset button state
            targetButton.disabled = false;
            targetButton.innerHTML = targetButton.dataset.originalText;
        }
    });
});

// Event listeners
startBtn.addEventListener('click', startStream);
stopBtn.addEventListener('click', stopStream);

// Cleanup on page unload
window.addEventListener('beforeunload', async () => {
    if (isStreamActive) {
        await stopStream();
    }
});