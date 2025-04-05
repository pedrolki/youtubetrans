from flask import Flask, render_template, request, jsonify, session
from youtube_transcript_api import YouTubeTranscriptApi
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from string import punctuation
from heapq import nlargest
from deep_translator import GoogleTranslator
from sentence_transformers import SentenceTransformer
import numpy as np
from collections import defaultdict
import re

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for session management

# Initialize the sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')  # Small, fast model

# Store video context
video_contexts = defaultdict(dict)

def get_video_id(url):
    """Extract video ID from YouTube URL"""
    if 'v=' in url:
        return url.split('v=')[1].split('&')[0]
    elif 'youtu.be/' in url:
        return url.split('youtu.be/')[1].split('?')[0]
    return None

def summarize_text(text, per=0.3):
    """Summarize text using NLTK"""
    sentences = sent_tokenize(text)
    words = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english') + list(punctuation))
    word_freq = {}
    
    for word in words:
        if word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    sent_scores = {}
    for sentence in sentences:
        for word in word_tokenize(sentence.lower()):
            if word in word_freq:
                sent_scores[sentence] = sent_scores.get(sentence, 0) + word_freq[word]
    
    select_length = max(int(len(sentences) * per), 1)
    summary = nlargest(select_length, sent_scores, key=sent_scores.get)
    
    return ' '.join(summary)

def prepare_context(transcript):
    """Prepare video context for Q&A"""
    # Combine transcript entries into context windows
    contexts = []
    current_context = []
    current_length = 0
    
    for entry in transcript:
        current_context.append(entry['text'])
        current_length += len(entry['text'].split())
        
        if current_length >= 100:  # Create context windows of ~100 words
            contexts.append({
                'text': ' '.join(current_context),
                'start_time': transcript[len(contexts)]['start']
            })
            current_context = []
            current_length = 0
    
    if current_context:
        contexts.append({
            'text': ' '.join(current_context),
            'start_time': transcript[-1]['start']
        })
    
    # Create embeddings for each context
    embeddings = model.encode([c['text'] for c in contexts])
    
    return contexts, embeddings

def find_best_context(query, contexts, embeddings):
    """Find most relevant context for a query"""
    query_embedding = model.encode([query])[0]
    similarities = np.dot(embeddings, query_embedding)
    best_idx = np.argmax(similarities)
    
    return contexts[best_idx], similarities[best_idx]

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
        
        # Prepare context for future Q&A
        contexts, embeddings = prepare_context(transcript)
        video_contexts[video_id] = {
            'contexts': contexts,
            'embeddings': embeddings,
            'transcript': transcript
        }
        
        return jsonify({'transcript': transcript})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/translate_transcript', methods=['POST'])
def translate_transcript():
    try:
        text = request.json['text']
        target_lang = request.json['target_lang']
        
        translator = GoogleTranslator(source='auto', target=target_lang)
        
        # Split text into smaller chunks to avoid length limits
        chunks = [text[i:i+500] for i in range(0, len(text), 500)]
        translated_chunks = [translator.translate(chunk) for chunk in chunks]
        
        translated_text = ' '.join(translated_chunks)
        return jsonify({'translated_text': translated_text})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        video_id = request.json['video_id']
        query = request.json['query']
        
        if video_id not in video_contexts:
            return jsonify({'error': 'Video context not found. Please load the transcript first.'})
        
        context = video_contexts[video_id]
        best_context, confidence = find_best_context(
            query, 
            context['contexts'],
            context['embeddings']
        )
        
        # Generate response based on context
        response = {
            'answer': f"Based on the video at {best_context['start_time']:.1f}s: {best_context['text']}",
            'timestamp': best_context['start_time'],
            'confidence': float(confidence)
        }
        
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/process_with_ai', methods=['POST'])
def process_with_ai():
    try:
        transcript = request.json['transcript']
        prompt_type = request.json['prompt']
        
        # Convert transcript to plain text
        text = ' '.join([entry['text'] for entry in transcript])
        
        if prompt_type == 'summarize':
            result = summarize_text(text)
        elif prompt_type == 'key-points':
            summary = summarize_text(text, 0.2)
            result = '\n• ' + '\n• '.join(sent_tokenize(summary))
        else:
            result = summarize_text(text, 0.5)
            
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
