import streamlit as st
import google.generativeai as genai
import edge_tts
import asyncio
import os
import cv2
from PIL import Image
import yt_dlp

st.set_page_config(page_title="AI Movie Subtitle & Dubbing Pro", layout="wide")

st.title("🎬 AI Movie Subtitle & Dubbing Pro (Khmer)")
st.write("Tool សម្រាប់ទាញយកវីដេអូ កាត់យករូប Thumbnail បកប្រែសាច់រឿងដោយ Gemini និងបង្កើតសំឡេងនិយាយខ្មែរដោយ Edge-TTS")

# API Key Config
api_key = st.text_input("បញ្ចូល Google Gemini API Key:", type="password")

# Input source
source_type = st.radio("ជ្រើសរើសប្រភពវីដេអូ:", ["Upload វីដេអូផ្ទាល់", "ទាញយកតាម Link (YouTube/TikTok/...)"])

video_path = None

if source_type == "Upload វីដេអូផ្ទាល់":
    uploaded_file = st.file_uploader("ជ្រើសរើសဖိုင်វីដេអូ (MP4, MOV)", type=["mp4", "mov", "avi"])
    if uploaded_file is not None:
        video_path = "temp_video.mp4"
        with open(video_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("អាប់ឡូតវីដេអូរួចរាល់!")
else:
    video_url = st.text_input("បញ្ចូលលីងវីដេអូ (YouTube/TikTok/...):")
    if video_url:
        if st.button("ទាញយកវីដេអូ"):
            with st.spinner("កំពុងទាញយកវីដេអូ..."):
                ydl_opts = {
                    'format': 'best',
                    'outtmpl': 'temp_video.mp4',
                }
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([video_url])
                    video_path = "temp_video.mp4"
                    st.success("ទាញយកវីដេអូរួចរាល់!")
                except Exception as e:
                    st.error(f"មានបញ្ហាក្នុងការទាញយក: {e}")

if video_path and os.path.exists(video_path):
    st.subheader("📺 វីដេអូដើម និង Thumbnail")
    st.video(video_path)
    
    # Auto-Thumbnail extraction
    cap = cv2.VideoCapture(video_path)
    success, frame = cap.read()
    if success:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        thumb_img = Image.fromarray(frame_rgb)
        thumb_path = "thumbnail.jpg"
        thumb_img.save(thumb_path)
        st.image(thumb_img, caption="រូប Thumbnail ស្វ័យប្រវត្តិ", use_container_width=True)
        with open(thumb_path, "rb") as file:
            st.download_button("📥 ទាញយក Thumbnail", data=file, file_name="thumbnail.jpg", mime="image/jpeg")
    cap.release()

    st.subheader("🤖 បកប្រែសាច់រឿងពេញលេញដោយ Gemini AI")
    prompt = st.text_area("បញ្ជាបន្ថែមដល់ AI (ស្រេចចិត្ត):", "សូមបកប្រែនិងសរសេរសាច់រឿងរៀបរាប់ពីវីដេអូនេះជាភាសាខ្មែរពេញលេញធម្មជាតិសម្រាប់ทำ Movie Recap:")
    
    if st.button("ចាប់ផ្តើមបកប្រែសាច់រឿង"):
        if not api_key:
            st.warning("សូមបញ្ចូល Gemini API Key ជាមុនសិន!")
        else:
            with st.spinner("AI កំពុងវិភាគ និងបកប្រែសាច់រឿង..."):
                try:
                    genai.configure(api_key=api_key)
                    video_file = genai.upload_file(path=video_path)
                    while video_file.state.name == "PROCESSING":
                        import time
                        time.sleep(2)
                        video_file = genai.get_file(video_file.name)
                    
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    response = model.generate_content([video_file, prompt])
                    script_text = response.text
                    st.session_state['script_text'] = script_text
                    st.success("បកប្រែរួចរាល់!")
                except Exception as e:
                    st.error(f"កំហុសឆ្គង: {e}")

    if 'script_text' in st.session_state:
        st.text_area("អត្ថបទសាច់រឿង (Full Script):", st.session_state['script_text'], height=200)
        
        st.subheader("🎙️ បង្កើតសំឡេងនិយាយខ្មែរ (Edge-TTS)")
        voice_choice = st.selectbox("ជ្រើសរើសសំឡេង:", ["km-KH-SreymomNeural (ស្រី)", "km-KH-PisethNeural (ប្រុស)"])
        voice_name = "km-KH-SreymomNeural" if "ស្រី" in voice_choice else "km-KH-PisethNeural"
        
        if st.button("បង្កើតសំឡេង MP3"):
            with st.spinner("កំពុងបង្កើតសំឡេងនិយាយ..."):
                audio_output_path = "output_audio.mp3"
                
                async def generate_audio():
                    communicate = edge_tts.Communicate(st.session_state['script_text'], voice_name)
                    await communicate.save(audio_output_path)
                
                try:
                    # ជួសជុលកូដហៅ Async ឱ្យមានស្ថេរភាពលើ Streamlit Cloud
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    if loop.is_running():
                        import nest_asyncio
                        nest_asyncio.apply()
                    
                    loop.run_until_complete(generate_audio())
                    
                    if os.path.exists(audio_output_path):
                        st.session_state['audio_ready'] = True
                        st.success("បង្កើតសំឡេង MP3 រួចរាល់!")
                    else:
                        st.error("រកមិនឃើញហ្វាយសំឡេងដែលបានបង្កើតទេ។")
                except Exception as e:
                    st.error(f"មានបញ្ហាក្នុងការបង្កើតសំឡេង: {e}")

        # បង្ហាញប៊ូតុងស្តាប់ និងដោនឡុត ប្រសិនបើហ្វាយមានរួចរាល់
        if st.session_state.get('audio_ready', False) and os.path.exists("output_audio.mp3"):
            with open("output_audio.mp3", "rb") as audio_file:
                audio_bytes = audio_file.read()
                st.audio(audio_bytes, format='audio/mp3')
                st.download_button(
                    label="📥 ទាញយកហ្វាយ MP3 សំឡេង", 
                    data=audio_bytes, 
                    file_name="movie_voiceover.mp3", 
                    mime="audio/mp3"
    )
                        
