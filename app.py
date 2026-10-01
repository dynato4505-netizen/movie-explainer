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

# --- INITIALIZE SESSION STATE ---
if "podcast_script" not in st.session_state:
    st.session_state.podcast_script = ""

if "movie_script" not in st.session_state:
    st.session_state.movie_script = ""

# --- SIDEBAR (ផ្នែកការកំណត់) ---
with st.sidebar:
    st.header("⚙ ការកំណត់ (Settings)")
    api_key = st.text_input("បញ្ចូល Google Gemini API Key (AQ. ឬ AIzaSy):", type="password")
    
    app_mode = st.radio(
        "ជ្រើសរើសរបៀបប្រើប្រាស់៖",
        ("🎬 សម្រាយរឿង (Khmer Dubbing)", "🎙 បកប្រែវីដេអូជា Podcast (English)")
    )
    
    model_option = st.selectbox(
        "ជ្រើសរើសម៉ូដែល AI (Gemini):",
        (
            "Gemini Flash (Standard)",
            "Gemini Pro"
        )
    )
    
    if "Pro" in model_option:
        selected_model = "gemini-pro"
    else:
        selected_model = "gemini-flash"

    st.markdown("---")
    
    if "Podcast" in app_mode:
        voice_option = st.selectbox(
            "ជ្រើសរើសសំឡេង Podcast (English):",
            ("Aria (ស្រី - អង់គ្លេសធម្មជាតិ)", "Christopher (ប្រុស - អង់គ្លេសធម្មជាតិ)")
        )
        if "Aria" in voice_option:
            selected_voice = "en-US-AriaNeural"
        else:
            selected_voice = "en-US-ChristopherNeural"
    else:
        voice_option = st.selectbox(
            "ជ្រើសរើសសំឡេង Dubbing (Khmer):",
            ("Sreymom (ស្រី - ធម្មជាតិ)", "Piseth (ប្រុស - ធម្មជាតិ)")
        )
        if "Sreymom" in voice_option:
            selected_voice = "km-KH-SreymomNeural"
        else:
            selected_voice = "km-KH-PisethNeural"

    st.markdown("---")
    st.subheader("🎛️ កែតម្រូវសំឡេងកុំឱ្យដូចរ៉ូបូត")
    rate_adjustment = st.slider("ល្បឿននិយាយ (Rate %):", min_value=-20, max_value=20, value=0, step=5)
    pitch_adjustment = st.slider("កម្រិតសំឡេង (Pitch Hz):", min_value=-10, max_value=10, value=0, step=1)
    
    st.info("💡 ដំណើរការដោយរលូនជាមួយ Edge-TTS, Gemini API និង MoviePy។")

# --- MAIN APP (អេក្រង់មេ) ---
st.title("🎬 Podcast & Movie Dubbing Pro")
if "Podcast" in app_mode:
    st.write("🎙️ មុខងារ Podcast: ដាក់វីដេអូ រួចបកប្រែ និងបង្កើតជាសំឡេង Podcast ភាសាអង់គ្លេស!")
else:
    st.write("🎬 មុខងារសម្រាយរឿង: ដាក់វីដេអូ និងបង្កើតសំឡេងនិយាយខ្មែរ ព្រមទាំងបញ្ចូលចូលវីដេអូស្វ័យប្រវត្តិ!")

input_method = st.radio("ជ្រើសរើសប្រភពវីដេអូ៖", ("📁 Upload វីដេអូពីកុំព្យូទ័រ", "🔗 បិទភ្ជាប់លីង (TikTok, YouTube, FB)"))

video_path = None

if input_method == "📁 Upload វីដេអូពីកុំព្យូទ័រ":
    uploaded_file = st.file_uploader("ជ្រើសរើសវីដេអូ (MP4, MOV, AVI):", type=["mp4", "mov", "avi"])
    if uploaded_file is not None:
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tfile.write(uploaded_file.read())
        video_path = tfile.name

else:
    raw_video_url = st.text_input("សូមបិទភ្ជាប់ (Paste) លីងវីដេអូ (YouTube, TikTok, FB):")
    if raw_video_url and st.button("⬇️ ទាញយកវីដេអូចូល Tool"):
        with st.spinner("កំពុងទាញយកវីដេអូ សូមរង់ចាំបន្តិច..."):
            try:
                url_match = re.search(r'https?://[^\s]+', raw_video_url)
                clean_url = url_match.group(0) if url_match else raw_video_url
                clean_url = clean_url.strip(')"]}')

                downloaded_file_path = "downloaded_video.mp4"
                if os.path.exists(downloaded_file_path):
                    os.remove(downloaded_file_path)
                
                ydl_opts = {
                    'format': 'best',
                    'outtmpl': downloaded_file_path,
                    'socket_timeout': 30,
                    'noplaylist': True,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([clean_url])
                
                if os.path.exists(downloaded_file_path):
                    video_path = downloaded_file_path
                    st.success("ទាញយកវីដេអូបានជោគជ័យ!")
            except Exception as e:
                st.error(f"មិនអាចទាញយកលីងនេះបានទេ៖ {e}")

if video_path and os.path.exists(video_path):
    st.video(video_path)

    st.subheader("📌 បង្កើតចំណងជើងវីដេអូ (Titles) សម្រាប់ Facebook:")
    if st.button("🔥 ឱ្យ AI ជួយបង្កើតចំណងជើងទាក់ទាញ"):
        if not api_key:
            st.warning("សូមបញ្ចូល Google Gemini API Key នៅកន្លែង Settings ខាងឆ្វេងជាមុនសិន!")
        else:
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(selected_model)
                with st.spinner("កំពុងបង្កើតចំណងជើងទាក់ទាញ..."):
                    title_prompt = "សូមបង្កើតចំណងជើងវីដេអូសង្ខេបភាពយន្ត ឬវីដេអូខ្លីចំនួន ៥ ដែលទាក់ទាញខ្លាំង ជាភាសាខ្មែរ សម្រាប់យកទៅផុសលើ Facebook Page។"
                    t_response = model.generate_content(title_prompt)
                    if t_response and t_response.text:
                        st.markdown(t_response.text)
            except Exception as e:
                st.error(f"មានបញ្ហាក្នុងការបង្កើតចំណងជើង: {e}")

    if "Podcast" in app_mode:
        st.subheader("📝 អត្ថបទសម្រាប់ทำ Podcast:")
        script_text = st.text_area("បញ្ចូលអត្ថបទរបស់អ្នកទីនេះ៖", value=st.session_state.podcast_script, height=200)
        st.session_state.podcast_script = script_text

        if st.button("✨ ឱ្យ AI បកប្រែអត្ថបទទៅជា English Podcast"):
            if not api_key:
                st.warning("សូមបញ្ចូល Google Gemini API Key នៅកន្លែង Settings ខាងឆ្វេងជាមុនសិន!")
            else:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(selected_model)
                    with st.spinner(f"កំពុងប្រើប្រាស់ {selected_model} ដើម្បីបកប្រែជាអង់គ្លេស..."):
                        prompt = f"Translate and refine the following Khmer script into a natural, engaging English podcast script suitable for voiceover:\n\n{st.session_state.podcast_script}"
                        response = model.generate_content(prompt)
                        if response and response.text:
                            st.session_state.podcast_script = response.text
                            st.success("បកប្រែជាអង់គ្លេសបានជោគជ័យ!")
                            st.rerun()
                except Exception as e:
                    st.error(f"មានបញ្ហាក្នុងការទាក់ទងទៅ AI Model: {e}")
    else:
        st.subheader("📝 អត្ថបទសាច់រឿង (Script) សម្រាប់បង្កើតសំឡេងខ្មែរ៖")
        script_text = st.text_area("បញ្ចូលអត្ថបទសម្រាយរឿងរបស់អ្នកនៅទីនេះ៖", value=st.session_state.movie_script, height=200)
        st.session_state.movie_script = script_text

        if st.button("✨ ឱ្យ AI ជួយសរសេរសាច់រឿងសម្រាយ"):
            if not api_key:
                st.warning("សូមបញ្ចូល Google Gemini API Key នៅកន្លែង Settings ខាងឆ្វេងជាមុនសិន!")
            else:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(selected_model)
                    with st.spinner(f"កំពុងប្រើប្រាស់ {selected_model} ដើម្បីបង្កើតសាច់រឿង..."):
                        prompt = (
                            "សូមសរសេរអត្ថបទសង្ខេបសាច់រឿង ឬសម្រាយរឿងជាភាសាខ្មែរសម្រាប់យកទៅអានធ្វើ Voiceover សុទ្ធសាធ។ "
                            "ហាមដាក់សញ្ញាសម្គាល់ឈុតឆាក ពេលវេលា (ឧ. [0:00 - 0:15]) ឬសញ្ញាណែនាំតន្រ្តីផ្សេងៗឡើយ។"
                        )
                        response = model.generate_content(prompt)
                        if response and response.text:
                            st.session_state.movie_script = response.text
                            st.success("បង្កើតសាច់រឿងដោយ AI បានជោគជ័យ!")
                            st.rerun()
                except Exception as e:
                    st.error(f"មានបញ្ហាក្នុងការទាក់ទងទៅ AI Model: {e}")

# មុខងារសម្អាតអត្ថបទ
def clean_script_for_tts(text):
    text = re.sub(r'\[\d+:\d+.*?\]', '', text)
    text = re.sub(r'\(\d+:\d+.*?\)', '', text)
    text = re.sub(r'\*\*.*?\*\*', '', text)
    text = re.sub(r'\*.*?\*', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    return text.strip()

async def generate_long_audio(text, voice, output_path, rate, pitch):
    cleaned_text = clean_script_for_tts(text)
    
    rate_str = f"{rate:+d}%" if rate != 0 else "+0%"
    pitch_str = f"{pitch:+d}Hz" if pitch != 0 else "+0Hz"

    max_chars = 3000
    text_chunks = [cleaned_text[i:i+max_chars] for i in range(0, len(cleaned_text), max_chars)]
    
    temp_files = []
    for idx, chunk in enumerate(text_chunks):
        if not chunk.strip():
            continue
        chunk_path = tempfile.NamedTemporaryFile(delete=False, suffix=f'_part{idx}.mp3').name
        communicate = edge_tts.Communicate(chunk, voice, rate=rate_str, pitch=pitch_str)
        await communicate.save(chunk_path)
        temp_files.append(chunk_path)
    
    with open(output_path, 'wb') as outfile:
        for f_path in temp_files:
            with open(f_path, 'rb') as infile:
                outfile.write(infile.read())
            os.remove(f_path)

if st.button("🚀 បង្កើតវីដេអូ និងច្របាច់បញ្ចូលសំឡេងស្វ័យប្រវត្តិ (បែបលឿនរហ័ស)"):
    if not video_path:
        st.warning("សូម Upload វីដេអូ ឬទាញយកវីដេអូតាមលីងជាមុនសិន!")
    else:
        current_script = st.session_state.podcast_script if "Podcast" in app_mode else st.session_state.movie_script
        
        if not current_script.strip():
            st.warning("សូមបញ្ចូលអត្ថបទសាច់រឿងជាមុនសិន!")
        else:
            try:
                with st.spinner("កំពុងបង្កើតសំឡេង និង Render វីដេអូក្នុងល្បឿនលឿន..."):
                    audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                    asyncio.run(generate_long_audio(current_script, selected_voice, audio_path, rate_adjustment, pitch_adjustment))

                    video_clip = VideoFileClip(video_path)
                    audio_clip = AudioFileClip(audio_path)

                    final_video_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                    final_clip = video_clip.set_audio(audio_clip)
                    
                    final_clip.write_videofile(
                        final_video_path, 
                        codec='libx264', 
                        audio_codec='aac', 
                        fps=video_clip.fps if video_clip.fps else 24,
                        preset='ultrafast',
                        threads=4
                    )

                st.success("បង្កើតវីដេអូបានលឿនរហ័ស និងជោគជ័យរលូនល្អ!")
                
                st.subheader("🎬 វីដេអូចុងក្រោយ (Final Video with Dubbed Audio):")
                st.video(final_video_path)
                
                with open(final_video_path, "rb") as f:
                    video_bytes = f.read()
                    st.download_button(
                        label="📥 ទាញយកវីដេអូពេញលេញ (មានសំឡេងស្រេច)",
                        data=video_bytes,
                        file_name="final_dubbed_video.mp4",
                        mime="video/mp4"
                    )

            except Exception as e:
                st.error(f"មានបញ្ហាក្នុងការកែច្នៃវីដេអូ (MoviePy): {e}")
        
