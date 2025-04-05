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

def get_available_transcripts(video_id):
    """Get list of available transcript languages"""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        return transcript_list
    except Exception as e:
        st.error(f"Error getting transcript list: {str(e)}")
        return None

def get_transcript(video_id, target_lang='en'):
    """Get transcript in target language, translating if necessary"""
    transcript_list = get_available_transcripts(video_id)
    if not transcript_list:
        return None

    try:
        # Try to get transcript in target language
        transcript = transcript_list.find_transcript([target_lang])
    except:
        try:
            # If target language not available, get any transcript and translate
            transcript = transcript_list.find_transcript([next(iter(transcript_list._manually_created_transcripts))])
        except:
            # If no manual transcripts, try auto-generated ones
            try:
                transcript = transcript_list.find_transcript([next(iter(transcript_list._generated_transcripts))])
            except:
                return None

    # Translate if not in target language
    if transcript.language_code != target_lang:
        try:
            transcript = transcript.translate(target_lang)
        except Exception as e:
            st.warning(f"Could not translate to {target_lang}. Using original language.")

    return transcript.fetch()

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
    "Transcript Language",
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
                # Get transcript in desired language
                transcript = get_transcript(video_id, target_lang)
                
                if transcript:
                    # Show transcript
                    st.subheader(f"Transcript ({target_lang})")
                    transcript_text = "\n".join([f"{format_time(t['start'])}: {t['text']}" for t in transcript])
                    st.text_area("", transcript_text, height=300)
                    
                    # Show available languages
                    transcript_list = get_available_transcripts(video_id)
                    if transcript_list:
                        st.subheader("Available Languages")
                        st.write("Manual transcripts:", ", ".join(transcript_list._manually_created_transcripts.keys()))
                        st.write("Auto-generated:", ", ".join(transcript_list._generated_transcripts.keys()))
                    
                    # Summary in col2
                    with col2:
                        st.subheader("Summary")
                        try:
                            full_text = ' '.join([t['text'] for t in transcript])
                            summary = summarize_text(full_text)
                            st.write(summary)
                        except Exception as e:
                            st.error(f"Error generating summary: {str(e)}")
                else:
                    st.error("No transcript available for this video.")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit")
