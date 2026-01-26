// Voice Recording Variables
let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let recognition;
let recognizedText = '';

// Initialize Speech Recognition
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
        console.warn('Speech recognition not supported in this browser');
        return null;
    }
    
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    
    recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript + ' ';
            } else {
                interimTranscript += transcript;
            }
        }
        
        if (finalTranscript) {
            recognizedText += finalTranscript;
        }
        
        // Update description field with transcribed text
        const descriptionField = document.getElementById('descriptionField');
        descriptionField.value = recognizedText + interimTranscript;
        
        // Auto-resize textarea
        descriptionField.style.height = 'auto';
        descriptionField.style.height = descriptionField.scrollHeight + 'px';
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        if (event.error === 'no-speech') {
            document.getElementById('recording-status').innerHTML = '<span class="text-warning"><i class="bi bi-exclamation-triangle-fill"></i> No speech detected</span>';
        }
    };
    
    return recognition;
}

// Start recording audio and speech recognition
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        // Start speech recognition
        if (!recognition) {
            initSpeechRecognition();
        }
        
        if (recognition) {
            recognizedText = document.getElementById('descriptionField').value || '';
            recognition.start();
        }
        
        // Start audio recording
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            const audioUrl = URL.createObjectURL(audioBlob);
            
            // Show preview
            const audioPreview = document.getElementById('voice-preview');
            audioPreview.src = audioUrl;
            audioPreview.classList.remove('d-none');
            
            // Convert to base64 for form submission
            const reader = new FileReader();
            reader.readAsDataURL(audioBlob);
            reader.onloadend = () => {
                document.getElementById('voiceRecording').value = reader.result;
            };
            
            // Show delete button
            document.getElementById('deleteBtn').classList.remove('d-none');
            
            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
        };
        
        mediaRecorder.start();
        isRecording = true;
        
        // Update UI
        document.getElementById('recording-status').innerHTML = '<span class="text-danger"><i class="bi bi-record-circle-fill"></i> Recording & transcribing...</span>';
        
    } catch (error) {
        console.error('Error accessing microphone:', error);
        alert('Unable to access microphone. Please check your browser permissions.');
    }
}

// Stop recording audio and speech recognition
function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        
        // Stop speech recognition
        if (recognition) {
            recognition.stop();
        }
        
        isRecording = false;
        document.getElementById('recording-status').innerHTML = '<span class="text-success"><i class="bi bi-check-circle-fill"></i> Recording saved & transcribed</span>';
    } else {
        alert('No recording in progress.');
    }
}

// Delete recording
function deleteRecording() {
    // Clear preview
    const audioPreview = document.getElementById('voice-preview');
    audioPreview.src = '';
    audioPreview.classList.add('d-none');
    
    // Clear hidden input
    document.getElementById('voiceRecording').value = '';
    
    // Hide delete button
    document.getElementById('deleteBtn').classList.add('d-none');
    
    // Clear status
    document.getElementById('recording-status').innerHTML = '';
    
    // Reset recording state
    audioChunks = [];
    
    alert('Recording deleted.');
}

// Form validation
function validateForm() {
    const tags = document.querySelectorAll('input[name="tags"]:checked');
    
    if (tags.length === 0) {
        alert('Please select at least one predefined tag.');
        return false;
    }
    
    return true;
}

// Remove media from story edit page
function removeMedia(button) {
    // Remove the entire card containing the media item
    const card = button.closest('.col-md-4');
    if (card) {
        // Find and remove the hidden input so it won't be submitted
        const hiddenInput = card.querySelector('input[name="existing_media"]');
        if (hiddenInput) {
            hiddenInput.remove();
        }
        // Remove the card from DOM with animation
        card.style.opacity = '0';
        card.style.transition = 'opacity 0.3s';
        setTimeout(() => {
            card.remove();
            // Check if there are any media left
            const mediaContainer = document.querySelector('.row.g-3');
            const remainingMedia = mediaContainer.querySelectorAll('.col-md-4').length;
            if (remainingMedia === 0) {
                mediaContainer.innerHTML = '<div class="col-12"><p class="text-muted">No media uploaded yet.</p></div>';
            }
        }, 300);
    }
}
