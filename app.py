from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Google Gemini Pro
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-pro')

app = Flask(__name__)

def get_video_id(url):
    """Extract video ID from YouTube URL"""
    if 'v=' in url:
        return url.split('v=')[1].split('&')[0]
    elif 'youtu.be/' in url:
        return url.split('youtu.be/')[1].split('?')[0]
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_transcript', methods=['POST'])
def get_transcript():
    try:
        url = request.json['url']
        video_id = get_video_id(url)
        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL'})
        
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return jsonify({'transcript': transcript})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/translate_transcript', methods=['POST'])
def translate_transcript():
    try:
        transcript = request.json['transcript']
        target_lang = request.json['target_lang']
        
        # Use YouTube Transcript API's translate method
        translator = YouTubeTranscriptApi.translate(transcript, target_lang)
        return jsonify({'translated_transcript': translator})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/process_with_ai', methods=['POST'])
def process_with_ai():
    try:
        transcript = request.json['transcript']
        prompt = request.json['prompt']
        
        # Process with Gemini Pro
        response = model.generate_content(f"{prompt}\n\nTranscript:\n{transcript}")
        return jsonify({'result': response.text})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
