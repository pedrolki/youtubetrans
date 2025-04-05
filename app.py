import streamlit as st
import nltk
from nltk.tokenize import sent_tokenize
from youtube_transcript_api import YouTubeTranscriptApi
from deep_translator import GoogleTranslator

# Initialize NLTK
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def get_video_id(url):
    """Extract video ID from YouTube URL"""
    if 'v=' in url:
        return url.split('v=')[1].split('&')[0]
    elif 'youtu.be/' in url:
        return url.split('youtu.be/')[1].split('?')[0]
    return None

def format_time(seconds):
    """Format seconds to MM:SS"""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

def summarize_text(text, per=0.3):
    """Simple summarization by selecting first few sentences"""
    sentences = sent_tokenize(text)
    n_sentences = max(int(len(sentences) * per), 1)
    return ' '.join(sentences[:n_sentences])

# Streamlit UI
st.set_page_config(page_title="YouTube Transcript Assistant", page_icon="🎥", layout="wide")

st.title("YouTube Transcript Assistant 🎥")

# Sidebar
st.sidebar.header("Options")
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
            # Display YouTube video using HTML iframe
            video_html = f'''
                <iframe
                    width="100%"
                    height="400"
                    src="[https://www.youtube.com/embed/{video_id}"](https://www.youtube.com/embed/{video_id}")
                    frameborder="0"
                    allow="autoplay; encrypted-media"
                    allowfullscreen
                ></iframe>
            '''
            st.markdown(video_html, unsafe_allow_html=True)
            
            try:
                # Get transcript
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                
                # Show transcript
                st.subheader("Transcript")
                transcript_text = "\n".join([f"{format_time(t['start'])}: {t['text']}" for t in transcript])
                st.text_area("", transcript_text, height=300)
                
                # Translation
                if st.button("Translate"):
                    try:
                        translator = GoogleTranslator(source='auto', target=target_lang)
                        chunks = [transcript_text[i:i+500] for i in range(0, len(transcript_text), 500)]
                        translated_chunks = [translator.translate(chunk) for chunk in chunks]
                        translated_text = ' '.join(translated_chunks)
                        st.text_area("Translated Transcript", translated_text, height=300)
                    except Exception as e:
                        st.error(f"Translation error: {str(e)}")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

with col2:
    if url and video_id:
        st.subheader("Summary")
        try:
            # Get full text for summary
            full_text = ' '.join([t['text'] for t in transcript])
            summary = summarize_text(full_text)
            st.write(summary)
        except Exception as e:
            st.error(f"Error generating summary: {str(e)}")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit")
