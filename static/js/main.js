// YouTube Player API
let player;
function onYouTubeIframeAPIReady() {
    player = new YT.Player('video-player', {
        height: '360',
        width: '640',
        videoId: '',
        playerVars: {
            'playsinline': 1
        }
    });
}

// Load YouTube IFrame API
const tag = document.createElement('script');
tag.src = "[https://www.youtube.com/iframe_api";](https://www.youtube.com/iframe_api";)
const firstScriptTag = document.getElementsByTagName('script')[0];
firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

// Get video ID from URL
function getVideoId(url) {
    const urlParams = new URLSearchParams(new URL(url).search);
    return urlParams.get('v');
}

// Main functions
async function getTranscript() {
    const urlInput = document.getElementById('youtube-url');
    const transcriptContent = document.getElementById('transcript-content');
    
    try {
        const response = await fetch('/get_transcript', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: urlInput.value })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Update video player
        const videoId = getVideoId(urlInput.value);
        player.loadVideoById(videoId);
        
        // Display transcript
        displayTranscript(data.transcript);
        
    } catch (error) {
        transcriptContent.innerHTML = `Error: ${error.message}`;
    }
}

function displayTranscript(transcript) {
    const transcriptContent = document.getElementById('transcript-content');
    transcriptContent.innerHTML = transcript.map(entry => `
        <div class="transcript-entry" data-start="${entry.start}">
            <span class="timestamp">${formatTime(entry.start)}</span>
            <span class="text">${entry.text}</span>
        </div>
    `).join('');
    
    // Add click handlers for timestamps
    document.querySelectorAll('.transcript-entry').forEach(entry => {
        entry.addEventListener('click', () => {
            player.seekTo(parseFloat(entry.dataset.start));
        });
    });
}

async function translateTranscript() {
    const langSelect = document.getElementById('language-select');
    const transcriptContent = document.getElementById('transcript-content');
    
    try {
        const response = await fetch('/translate_transcript', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                transcript: transcriptContent.innerHTML,
                target_lang: langSelect.value
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        displayTranscript(data.translated_transcript);
        
    } catch (error) {
        alert(`Translation error: ${error.message}`);
    }
}

async function processWithAI() {
    const promptSelect = document.getElementById('ai-prompt-select');
    const transcriptContent = document.getElementById('transcript-content');
    const aiOutput = document.getElementById('ai-output');
    
    try {
        const response = await fetch('/process_with_ai', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                transcript: transcriptContent.innerHTML,
                prompt: promptSelect.value
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        aiOutput.innerHTML = data.result;
        
    } catch (error) {
        aiOutput.innerHTML = `Error: ${error.message}`;
    }
}

function copyTranscript() {
    const transcriptContent = document.getElementById('transcript-content');
    navigator.clipboard.writeText(transcriptContent.innerText)
        .then(() => alert('Transcript copied to clipboard!'))
        .catch(err => alert('Failed to copy transcript: ' + err));
}

function downloadTranscript() {
    const transcriptContent = document.getElementById('transcript-content');
    const blob = new Blob([transcriptContent.innerText], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'transcript.txt';
    a.click();
    window.URL.revokeObjectURL(url);
}

function formatTime(seconds) {
    const date = new Date(seconds * 1000);
    const mm = date.getUTCMinutes();
    const ss = date.getUTCSeconds();
    return `${mm.toString().padStart(2, '0')}:${ss.toString().padStart(2, '0')}`;
}
// Add these functions at the end of the file

let currentVideoId = null;

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const messages = document.getElementById('chat-messages');
    const query = input.value.trim();
    
    if (!query) return;
    if (!currentVideoId) {
        alert('Please load a video transcript first!');
        return;
    }
    
    // Add user message
    messages.innerHTML += `
        <div class="message user-message">
            ${query}
        </div>
    `;
    
    input.value = '';
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                video_id: currentVideoId,
                query: query
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Add bot message with clickable timestamp
        messages.innerHTML += `
            <div class="message bot-message">
                ${data.answer}
                <br>
                <span class="timestamp-link" onclick="player.seekTo(${data.timestamp})">
                    Jump to ${formatTime(data.timestamp)}
                </span>
            </div>
        `;
        
    } catch (error) {
        messages.innerHTML += `
            <div class="message bot-message error">
                Error: ${error.message}
            </div>
        `;
    }
    
    // Scroll to bottom
    messages.scrollTop = messages.scrollHeight;
}

// Update getTranscript function to store video ID
async function getTranscript() {
    const urlInput = document.getElementById('youtube-url');
    const transcriptContent = document.getElementById('transcript-content');
    
    try {
        currentVideoId = getVideoId(urlInput.value);
        if (!currentVideoId) {
            throw new Error('Invalid YouTube URL');
        }
        
        const response = await fetch('/get_transcript', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: urlInput.value })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Update video player
        player.loadVideoById(currentVideoId);
        
        // Display transcript
        displayTranscript(data.transcript);
        
        // Clear chat messages
        document.getElementById('chat-messages').innerHTML = '';
        
    } catch (error) {
        transcriptContent.innerHTML = `Error: ${error.message}`;
        currentVideoId = null;
    }
}

// Add event listener for Enter key in chat input
document.getElementById('chat-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});
