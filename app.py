import streamlit as st
import asyncio
import edge_tts
import tempfile
import os
import yt_dlp
import re
import google.generativeai as genai
from moviepy.editor import VideoFileClip, AudioFileClip

st.set_page_config(page_title="Podcast & Movie Pro", page_icon="🎬", layout="wide")

if "podcast_script" not in st.session_state:
    st.session_state.podcast_script = ""
if "movie_script" not in st.session_state:
    st.session_state.movie_script = ""

with st.sidebar:
    st.header("⚙ ការកំណត់ (Settings)")
    api_key = st.text_input("បញ្ចូល Google Gemini API Key:", type="password")
    app_mode = st.radio("ជ្រើសរើសរបៀបប្រើប្រាស់៖", ("🎬 សម្រាយរឿង (Khmer Dubbing)", "🎙 បកប្រែវីដេអូជា Podcast (English)"))
    
    # ប្រើម៉ូដែលស្តង់ដារប្រាកដប្រជា មិនបាច់ខ្លាច Error
    selected_model = "gemini-pro"
    st.info("🤖 កំពុងប្រើប្រាស់ម៉ូដែល៖ Gemini Pro")
    st.markdown("---")
    
    if "Podcast" in app_mode:
        voice_option = st.selectbox("ជ្រើសរើសសំឡេង Podcast (English):", ("Aria (ស្រី)", "Christopher (ប្រុស)"))
        selected_voice = "en-US-AriaNeural" if "Aria" in voice_option else "en-US-ChristopherNeural"
    else:
        voice_option = st.selectbox("ជ្រើសរើសសំឡេង Dubbing (Khmer):", ("Sreymom (ស្រី)", "Piseth (ប្រុស)"))
        selected_voice = "km-KH-SreymomNeural" if "Sreymom" in voice_option else "km-KH-PisethNeural"

    st.markdown("---")
    rate_adjustment = st.slider("ល្បឿននិយាយ (Rate %):", -20, 20, 0, 5)
    pitch_adjustment = st.slider("កម្រិតសំឡេង (Pitch Hz):", -10, 10, 0, 1)

st.title("🎬 Podcast & Movie Dubbing Pro")
input_method = st.radio("ជ្រើសរើសប្រភពវីដេអូ៖", ("📁 Upload វីដេអូ", "🔗 បិទភ្ជាប់លីង (YouTube, TikTok, FB)"))
video_path = None

if input_method == "📁 Upload វីដេអូ":
    uploaded_file = st.file_uploader("ជ្រើសរើសវីដេអូ (MP4):", type=["mp4", "mov", "avi"])
    if uploaded_file:
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tfile.write(uploaded_file.read())
        video_path = tfile.name
else:
    raw_video_url = st.text_input("សូមបិទភ្ជាប់ (Paste) លីងវីដេអូ៖")
    if raw_video_url and st.button("⬇️ ទាញយកវីដេអូ"):
        with st.spinner("កំពុងទាញយក..."):
            try:
                downloaded_file_path = "downloaded_video.mp4"
                if os.path.exists(downloaded_file_path): os.remove(downloaded_file_path)
                ydl_opts = {'format': 'best', 'outtmpl': downloaded_file_path, 'noplaylist': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([raw_video_url.strip()])
                if os.path.exists(downloaded_file_path):
                    video_path = downloaded_file_path
                    st.success("ទាញយកវីដេអូបានជោគជ័យ!")
            except Exception as e:
                st.error(f"មិនអាចទាញយកបានទេ៖ {e}")

if video_path and os.path.exists(video_path):
    st.video(video_path)
    
    if "Podcast" in app_mode:
        st.session_state.podcast_script = st.text_area("អត្ថបទ Podcast:", value=st.session_state.podcast_script, height=150)
        if st.button("✨ បកប្រែជាអង់គ្លេស"):
            if api_key:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(selected_model)
                resp = model.generate_content(f"Translate into natural English podcast script:\n\n{st.session_state.podcast_script}")
                st.session_state.podcast_script = resp.text
                st.rerun()
            else:
                st.warning("សូមបញ្ចូល API Key ជាមុនសិន!")
    else:
        st.session_state.movie_script = st.text_area("សាច់រឿងសម្រាយ:", value=st.session_state.movie_script, height=150)
        if st.button("✨ ឱ្យ AI សរសេរសាច់រឿង"):
            if api_key:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(selected_model)
                resp = model.generate_content("សូមសរសេរអត្ថបទសម្រាយរឿងជាភាសាខ្មែរសម្រាប់ធ្វើ Voiceover សុទ្ធសាធ គ្មានដាក់ពេលវេលាឡើយ។")
                st.session_state.movie_script = resp.text
                st.rerun()
            else:
                st.warning("សូមបញ្ចូល API Key ជាមុនសិន!")

def clean_script(text):
    text = re.sub(r'\[\d+:\d+.*?\]', '', text)
    return text.strip()

async def gen_audio(text, voice, out_path, rate, pitch):
    cleaned = clean_script(text)
    rate_str = f"{rate:+d}%" if rate != 0 else "+0%"
    pitch_str = f"{pitch:+d}Hz" if pitch != 0 else "+0Hz"
    comm = edge_tts.Communicate(cleaned, voice, rate=rate_str, pitch=pitch_str)
    await comm.save(out_path)

if st.button("🚀 បង្កើតវីដេអូ និងបញ្ចូលសំឡេងស្វ័យប្រវត្តិ"):
    if not video_path:
        st.warning("សូមដាក់វីដេអូជាមុនសិន!")
    else:
        cur_script = st.session_state.podcast_script if "Podcast" in app_mode else st.session_state.movie_script
        if not cur_script.strip():
            st.warning("សូមបញ្ចូលអត្ថបទសិន!")
        else:
            with st.spinner("កំពុងដំណើរការបង្កើតសំឡេងនិងវីដេអូ..."):
                audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                asyncio.run(gen_audio(cur_script, selected_voice, audio_path, rate_adjustment, pitch_adjustment))
                
                v_clip = VideoFileClip(video_path)
                a_clip = AudioFileClip(audio_path)
                final_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                final_clip = v_clip.set_audio(a_clip)
                final_clip.write_videofile(final_path, codec='libx264', audio_codec='aac', fps=v_clip.fps or 24, preset='ultrafast')
                
            st.success("ជោគជ័យរលូនល្អ!")
            st.video(final_path)
            with open(final_path, "rb") as f:
                st.download_button("📥 ទាញយកវីដេអូ", f.read(), file_name="final_video.mp4", mime="video/mp4")
