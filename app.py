import streamlit as st
import asyncio
import edge_tts
import tempfile
import os
import yt_dlp
import re
import cv2
import google.generativeai as genai

st.set_page_config(page_title="AI Movie & Podcast Pro", page_icon="🎬", layout="wide")

# --- SIDEBAR (ផ្នែកការកំណត់) ---
with st.sidebar:
    st.header("⚙️ ការកំណត់ (Settings)")
    api_key = st.text_input("បញ្ចូល Google Gemini API Key:", type="password")
    
    # ជ្រើសរើសមុខងារ Tool
    app_mode = st.radio(
        "ជ្រើសរើសរបៀបប្រើប្រាស់៖",
        ("🎬 សម្រាយរឿង (Khmer Dubbing)", "🎙️ បកប្រែវីដេអូជា Podcast (English)")
    )
    
    model_option = st.selectbox(
        "ជ្រើសរើសម៉ូដែល AI (Gemini):",
        (
            "Gemini 3.7 Flash (Fastest/New)",
            "Gemini 3 Flash",
            "Gemini 3.1 Pro",
            "Gemini 2.5 Flash (Stable)",
            "Gemini 2.5 Pro"
        )
    )
    
    if "3.7" in model_option:
        selected_model = "gemini-3.7-flash"
    elif "3 Flash" in model_option:
        selected_model = "gemini-3-flash"
    elif "3.1 Pro" in model_option:
        selected_model = "gemini-3.1-pro"
    elif "2.5 Pro" in model_option:
        selected_model = "gemini-2.5-pro"
    else:
        selected_model = "gemini-2.5-flash"

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
    
    st.info("💡 ប្រើប្រាស់ Edge-TTS ប្រកបដោយសុវត្ថិភាពខ្ពស់ គ្មាន Error 401 ។")

# --- MAIN APP (អេក្រង់មេ) ---
st.title("🎬 AI Movie & Podcast Pro")
if "Podcast" in app_mode:
    st.write("🎙️ មុខងារ Podcast: ដាក់វីដេអូ ឬអត្ថបទខ្មែរ រួចបកប្រែ និងបង្កើតជាសំឡេង Podcast ភាសាអង់គ្លេស!")
else:
    st.write("🎬 មុខងារសម្រាយរឿង: ដាក់វីដេអូ និងបង្កើតសំឡេងនិយាយខ្មែរពីដើមដល់ចប់ដោយរលូន!")

input_method = st.radio("ជ្រើសរើសប្រភពវីដេអូ៖", ("📁 Upload វីដេអូពីកុំព្យូទ័រ", "🔗 បិទភ្ជាប់លីង (TikTok, YouTube, FB)"))

video_path = None
thumbnail_path = None

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
                    'outtmpl': downloaded_file_path,
                    'format': 'best',
                    'socket_timeout': 30,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([clean_url])
                
                if os.path.exists(downloaded_file_path):
                    video_path = downloaded_file_path
                    st.success("ទាញយកវីដេអូได้ជោគជ័យ!")
            except Exception as e:
                st.error(f"មិនអាចទាញយកលីងនេះបានទេ៖ {e}")

if video_path and os.path.exists(video_path):
    st.video(video_path)
    
    try:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if fps > 0 and total_frames > 0:
            target_frame = int(fps * 2) if total_frames > int(fps * 2) else total_frames // 2
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            success, frame = cap.read()
            
            if success:
                thumb_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                cv2.imwrite(thumb_temp.name, frame)
                thumbnail_path = thumb_temp.name
        cap.release()
    except Exception as ex:
        print(f"Error generating thumbnail: {ex}")

    if thumbnail_path and os.path.exists(thumbnail_path):
        st.subheader("🖼️ រូប Thumbnail ពីវីដេអូ៖")
        st.image(thumbnail_path, use_container_width=True)
        with open(thumbnail_path, "rb") as img_file:
            st.download_button(
                label="📥 ទាញយក Thumbnail នេះ",
                data=img_file,
                file_name="video_thumbnail.jpg",
                mime="image/jpeg"
            )

    if "Podcast" in app_mode:
        st.subheader("📝 អត្ថបទសម្រាប់ทำ Podcast (បកប្រែពីខ្មែរទៅអង់គ្លេស):")
        script_text = st.text_area("បញ្ចូលអត្ថបទខ្មែរ ឬសាច់រឿងរបស់អ្នកទីនេះ៖", "សួស្តីស្វាគមន៍មកកាន់ឆានែលរបស់យើង ថ្ងៃនេះយើងនឹងនិយាយពី...", height=200)

        if st.button("✨ ឱ្យ AI បកប្រែអត្ថបទខ្មែរទៅជា English Podcast"):
            if not api_key:
                st.warning("សូមបញ្ចូល Google Gemini API Key នៅកន្លែង Settings ខាងឆ្វេងជាមុនសិន!")
            else:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(selected_model)
                    with st.spinner(f"កំពុងប្រើប្រាស់ {selected_model} ដើម្បីបកប្រែជាអង់គ្លេស..."):
                        prompt = f"Translate and refine the following Khmer script into a natural, engaging English podcast script suitable for voiceover:\n\n{script_text}"
                        response = model.generate_content(prompt)
                        if response and response.text:
                            script_text = response.text
                            st.success("បកប្រែជាអង់គ្លេសបានជោគជ័យ! សូមពិនិត្យមើលក្នុងប្រអប់ខាងលើ។")
                except Exception as e:
                    st.error(f"មានបញ្ហាក្នុងការទាក់ទងទៅ AI Model: {e}")
    else:
        st.subheader("📝 អត្ថបទសាច់រឿង (Script) សម្រាប់បង្កើតសំឡេងខ្មែរ៖")
        script_text = st.text_area("បញ្ចូលអត្ថបទសម្រាយរឿងរបស់អ្នកនៅទីនេះ៖", "សួស្តី! ថ្ងៃនេះយើងនាំអារម្មណ៍មកទស្សនាការសម្រាយរឿង...", height=200)

        if st.button("✨ ឱ្យ AI ជួយសរសេរសាច់រឿងសម្រាយ"):
            if not api_key:
                st.warning("សូមបញ្ចូល Google Gemini API Key នៅកន្លែង Settings ខាងឆ្វេងជាមុនសិន!")
            else:
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(selected_model)
                    with st.spinner(f"កំពុងប្រើប្រាស់ {selected_model} ដើម្បីបង្កើតសាច់រឿង..."):
                        prompt = "បង្កើតអត្ថបទសម្រាយរឿងជាភាសាខ្មែរប្រកបដោយភាពទាក់ទាញ និងរលូន សម្រាប់យកទៅអានធ្វើសំឡេង Voiceover៖"
                        response = model.generate_content(prompt)
                        if response and response.text:
                            script_text = response.text
                            st.success("បង្កើតសាច់រឿងដោយ AI បានជោគជ័យ!")
                except Exception as e:
                    st.error(f"មានបញ្ហាក្នុងការទាក់ទងទៅ AI Model: {e}")

async def generate_long_audio(text, voice, output_path):
    max_chars = 3000
    text_chunks = [text[i:i+max_chars] for i in range(0, len(text), max_chars)]
    
    temp_files = []
    for idx, chunk in enumerate(text_chunks):
        chunk_path = tempfile.NamedTemporaryFile(delete=False, suffix=f'_part{idx}.mp3').name
        communicate = edge_tts.Communicate(chunk, voice)
        await communicate.save(chunk_path)
        temp_files.append(chunk_path)
    
    with open(output_path, 'wb') as outfile:
        for f_path in temp_files:
            with open(f_path, 'rb') as infile:
                outfile.write(infile.read())
            os.remove(f_path)

if st.button("🚀 ចាប់ផ្តើមបង្កើតសំឡេង MP3"):
    if not video_path:
        st.warning("សូម Upload វីដេអូ ឬទាញយកវីដេអូតាមលីងជាមុនសិន!")
    elif 'script_text' in locals() and not script_text.strip():
        st.warning("សូមបញ្ចូលអត្ថបទជាមុនសិន!")
    else:
        try:
            with st.spinner("កំពុងបង្កើតហ្វាយសំឡេង MP3..."):
                audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                asyncio.run(generate_long_audio(script_text, selected_voice, audio_path))

            st.success("បង្កើតសំឡេង MP3 បានជោគជ័យរលូនល្អ!")
            
            if "Podcast" in app_mode:
                st.subheader("🔊 សំឡេង English Podcast (MP3):")
                file_name = "english_podcast_audio.mp3"
            else:
                st.subheader("🔊 សំឡេង Khmer Dubbing (MP3):")
                file_name = "khmer_dubbing_audio.mp3"

            st.audio(audio_path)
            
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
                st.download_button(
                    label="📥 ទាញយកហ្វាយ MP3 នេះចូលទូរស័ព្ទ",
                    data=audio_bytes,
                    file_name=file_name,
                    mime="audio/mp3"
                )

        except Exception as e:
            st.error(f"មានបញ្ហាកើតឡើង: {e}")
            
