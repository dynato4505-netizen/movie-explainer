import streamlit as st
import requests
import json
import edge_tts
import asyncio
import os
import yt_dlp

st.set_page_config(page_title="AI Movie Subtitle & Dubbing Pro", layout="wide")

# --- SIDEBAR (ផ្នែកខាងឆ្វេង) ---
with st.sidebar:
    st.header("⚙️ ការកំណត់ (Settings)")
    api_key = st.text_input("បញ្ចូល Google Gemini API Key:", type="password")
    st.divider()
    st.subheader("🎙️ ការកំណត់សំឡេង (Edge-TTS)")
    voice_choice = st.selectbox("ជ្រើសរើសសំឡេង:", ["km-KH-SreymomNeural (ស្រី)", "km-KH-PisethNeural (ប្រុស)"])
    voice_name = "km-KH-SreymomNeural" if "ស្រី" in voice_choice else "km-KH-PisethNeural"

# --- MAIN CONTENT (ផ្នែកខាងស្តាំ / អេក្រង់មេ) ---
st.title("🎬 HD-AI សម្រាយរឿង Pro")
st.write("Tool សម្រាប់ទាញយកវីដេអូ បកប្រែសាច់រឿងដោយ Gemini និងបង្កើតសំឡេងនិយាយខ្មែរ")

source_type = st.radio("ជ្រើសរើសប្រភពវីដេអូ:", ["Upload វីដេអូផ្ទាល់", "ទាញយកតាម Link (YouTube/TikTok/...)"])

video_path = None

if source_type == "Upload វីដេអូផ្ទាល់":
    uploaded_file = st.file_uploader("ជ្រើសរើសဖိုင်វីដេអូ (MP4, MOV)", type=["mp4", "mov", "avi"])
    if uploaded_file is not None:
        with st.spinner("កំពុងផ្ទុកវីដេអូចូលប្រព័ន្ធ សូមរង់ចាំបន្តិច..."):
            video_path = "temp_video.mp4"
            with open(video_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        st.success("អាប់ឡូតវីដេអូរួចរាល់!")
else:
    video_url = st.text_input("បញ្ចូលលីងវីដេអូ (YouTube/TikTok/...):")
    if video_url:
        if st.button("ទាញយកវីដេអូ"):
            with st.spinner("កំពុងទាញយកវីដេអូពីលីង..."):
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
    st.subheader("📺 វីដេអូដើម")
    st.video(video_path)

    st.subheader("🤖 បកប្រែសាច់រឿងដោយ Gemini AI")
    prompt = st.text_area("បញ្ចូលអត្ថបទ ឬបញ្ជាដល់ AI:", "សូមសរសេរសាច់រឿងរៀបរាប់ពីវីដេអូនេះជាភាសាខ្មែរពេញលេញធម្មជាតិសម្រាប់ทำ Movie Recap:")
    
    if st.button("ចាប់ផ្តើមបង្កើតសាច់រឿង"):
        if not api_key:
            st.warning("សូមបញ្ចូល Google Gemini API Key នៅផ្នែកខាងឆ្វេង (Sidebar) ជាមុនសិន!")
        else:
            with st.spinner("AI កំពុងវិភាគ និងបង្កើតសាច់រឿង..."):
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                    headers = {'Content-Type': 'application/json'}
                    payload = {
                        "contents": [{
                            "parts": [{"text": prompt}]
                        }]
                    }
                    
                    response = requests.post(url, headers=headers, data=json.dumps(payload))
                    res_json = response.json()
                    
                    if "candidates" in res_json:
                        script_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                        st.session_state['script_text'] = script_text
                        st.success("បង្កើតសាច់រឿងរួចរាល់!")
                    else:
                        st.error(f"កំហុសពី API: {res_json}")
                except Exception as e:
                    st.error(f"កំហុសឆ្គង: {e}")

    if 'script_text' in st.session_state:
        st.text_area("អត្ថបទសាច់រឿង (Full Script):", st.session_state['script_text'], height=200)
        
        if st.button("បង្កើតសំឡេង MP3"):
            with st.spinner("កំពុងបង្កើតសំឡេងនិយាយ..."):
                audio_output_path = "output_audio.mp3"
                
                async def generate_audio():
                    communicate = edge_tts.Communicate(st.session_state['script_text'], voice_name)
                    await communicate.save(audio_output_path)
                
                try:
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
                    
