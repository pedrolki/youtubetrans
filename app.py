import streamlit as st
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from string import punctuation
from heapq import nlargest
from youtube_transcript_api import YouTubeTranscriptApi
from deep_translator import GoogleTranslator
from sentence_transformers import SentenceTransformer
import numpy as np
from collections import defaultdict

# Download required NLTK data
@st.cache_resource
def download_nltk_data():
    nltk.download('punkt')
    nltk.download('stopwords')

download_nltk_data()

# Initialize the sentence transformer model
@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = load_model()

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
    contexts = []
    current_context = []
    current_length = 0
    
    for entry in transcript:
        current_context.append(entry['text'])
        current_length += len(entry['text'].split())
        
        if current_length >= 100:
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
    
    embeddings = model.encode([c['text'] for c in contexts])
    
    return contexts, embeddings

def find_best_context(query, contexts, embeddings):
    """Find most relevant context for a query"""
    query_embedding = model.encode([query])[0]
    similarities = np.dot(embeddings, query_embedding)
    best_idx = np.argmax(similarities)
    
    return contexts[best_idx], similarities[best_idx]

def format_time(seconds):
    """Format seconds to MM:SS"""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

# Streamlit UI
st.set_page_config(page_title="YouTube Transcript Assistant", page_icon="🎥", layout="wide")

st.title("YouTube Transcript Assistant 🎥")

# Sidebar
st.sidebar.header("Options")
ai_option = st.sidebar.selectbox(
    "AI Processing",
    ["Summarize", "Key Points", "Study Notes"]
)

target_lang = st.sidebar.selectbox(
    "Translation Language",
    ["en", "es", "fr", "de", "it", "pt", "nl", "ru", "ja", "ko", "zh"]
)

# Main content
col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("Video Input")
    url = st.text_input("Enter YouTube URL")
    
    if url:
        video_id = get_video_id(url)
        if video_id:
            st.video(f"[https://www.youtube.com/watch?v={video_id}")](https://www.youtube.com/watch?v={video_id}"))
            
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                
                # Prepare context for Q&A
                contexts, embeddings = prepare_context(transcript)
                video_contexts[video_id] = {
                    'contexts': contexts,
                    'embeddings': embeddings,
                    'transcript': transcript
                }
                
                # Show transcript
                st.subheader("Transcript")
                transcript_text = "\n".join([f"{format_time(t['start'])}: {t['text']}" for t in transcript])
                st.text_area("", transcript_text, height=300)
                
                # Translation
                if st.button("Translate"):
                    translator = GoogleTranslator(source='auto', target=target_lang)
                    chunks = [transcript_text[i:i+500] for i in range(0, len(transcript_text), 500)]
                    translated_chunks = [translator.translate(chunk) for chunk in chunks]
                    translated_text = ' '.join(translated_chunks)
                    st.text_area("Translated Transcript", translated_text, height=300)
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

with col2:
    st.subheader("AI Analysis")
    
    if url and video_id in video_contexts:
        # Process transcript with AI
        text = ' '.join([t['text'] for t in video_contexts[video_id]['transcript']])
        
        if ai_option == "Summarize":
            st.write("Summary:")
            summary = summarize_text(text)
            st.write(summary)
        
        elif ai_option == "Key Points":
            st.write("Key Points:")
            summary = summarize_text(text, 0.2)
            for point in sent_tokenize(summary):
                st.markdown(f"• {point}")
        
        else:  # Study Notes
            st.write("Study Notes:")
            notes = summarize_text(text, 0.5)
            st.write(notes)
        
        # Chat interface
        st.subheader("Chat with Video")
        query = st.text_input("Ask a question about the video")
        
        if query:
            context = video_contexts[video_id]
            best_context, confidence = find_best_context(
                query,
                context['contexts'],
                context['embeddings']
            )
            
            st.write("Answer:")
            st.info(f"{best_context['text']}")
            st.caption(f"Timestamp: {format_time(best_context['start_time'])}")
            
            # Store chat history in session state
            if 'chat_history' not in st.session_state:
                st.session_state.chat_history = []
            
            st.session_state.chat_history.append({
                'query': query,
                'response': best_context['text'],
                'timestamp': best_context['start_time']
            })
        
        # Display chat history
        if 'chat_history' in st.session_state and st.session_state.chat_history:
            st.subheader("Chat History")
            for item in st.session_state.chat_history:
                st.markdown(f"**Q:** {item['query']}")
                st.markdown(f"**A:** {item['response']}")
                st.caption(f"Timestamp: {format_time(item['timestamp'])}")
                st.divider()

# Footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit")
