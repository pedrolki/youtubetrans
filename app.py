import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="YouTube Summarizer", layout="centered")

st.title("🎬 YouTube Video Summarizer")
st.write("Paste a YouTube video link to generate a summary using GPT.")

url = st.text_input("📎 YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
if st.button("Summarize") and url:
    try:
        with st.spinner("Fetching transcript..."):
            video_id = url.split("v=")[-1].split("&")[0]
            transcript = YoutubeTranscriptApi.get_transcript(video_id)
            full_text = " ".join([entry['text'] for entry in transcript])

        with st.spinner("Summarizing with GPT..."):
            prompt = f"Summarize this YouTube video transcript:\n\n{full_text}"
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=1000
            )
            summary = response['choices'][0]['message']['content']
            st.success("✅ Summary Generated!")
            st.markdown("### 📝 Summary:")
            st.write(summary)

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
