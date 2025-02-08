let currentUser = null;
let sequenceBuilder = [];
const SEQUENCE_LENGTH = 3;

// Login Form
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    
    // Wait for sequence input
    const sequence = await captureSequence();
    
    const response = await fetch('/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ username, gesture_sequence: sequence })
    });
    
    if (response.ok) {
        currentUser = await response.json();
        showAccountSection();
    }
});

// Sequence Update
document.getElementById('update-sequence').addEventListener('click', async () => {
    const newSequence = await captureSequence();
    
    const response = await fetch('/update-sequence', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': currentUser.session_token
        },
        body: JSON.stringify({ new_sequence: newSequence })
    });
    
    if (response.ok) {
        alert('Gesture sequence updated successfully!');
    }
});

// Sequence Capture Logic
async function captureSequence() {
    return new Promise((resolve) => {
        sequenceBuilder = [];
        const sequenceDisplay = document.getElementById('sequence-builder');
        
        socket.on('gesture_update', (data) => {
            if (sequenceBuilder.length < SEQUENCE_LENGTH) {
                sequenceBuilder.push(data.gesture);
                sequenceDisplay.textContent = sequenceBuilder.join(' → ');
                
                if (sequenceBuilder.length === SEQUENCE_LENGTH) {
                    resolve([...sequenceBuilder]);
                }
            }
        });
    });
}

function showAccountSection() {
    document.getElementById('login-section').style.display = 'none';
    document.getElementById('account-section').style.display = 'block';
    document.getElementById('current-sequence').textContent = 
        currentUser.gesture_sequence.join(' → ');
}