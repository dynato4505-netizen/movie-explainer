Jo Jox:
import streamlit as st
from google import genai
import asyncio
import edge_tts
import tempfile
import os
import yt_dlp
import re
import cv2

st.set_page_config(page_title="AI Movie Subtitle & Dubbing Pro", page_icon="🎬")

with st.sidebar:
    st.header("⚙️ ការកំណត់ (Settings)")
    api_key = st.text_input("បញ្ចូល Google Gemini API Key:", type="password")
    
    voice_option = st.selectbox(
        "ជ្រើសរើសសំឡេង Dubbing:",
        ("Sreymom (ស្រី - ធម្មជាតិ)", "Piseth (ប្រុស - ធម្មជាតិ)")
    )
    
    if "Sreymom" in voice_option:
        selected_voice = "km-KH-SreymomNeural"
    else:
        selected_voice = "km-KH-PisethNeural"

st.title("🎬 AI Movie Subtitle & Dubbing Pro")
st.write("បកប្រែវីដេអូពេញលេញជា Subtitle ខ្មែរ និងបង្កើតសំឡេង Dubbing ត្រូវសាច់រឿងពីដើមដល់ចប់ដោយរលូន!")

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
    st.info("💡 ចំណាំ៖ សម្រាប់ RedNote សូម Download វីដេអូទុកក្នុងទូរសព្ទ/កុំព្យូទ័រ រួចជ្រើសរើស Upload ផ្ទាល់ គឺធានាថាលឿន និងមិន Error ទេ។")
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
                    st.success("ទាញយកវីដេអូបានជោគជ័យ!")
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
        st.subheader("🖼️ រូប Thumbnail ដែល Tool កាត់បានពីវីដេអូ៖")
        st.image(thumbnail_path, use_container_width=True)
        
        with open(thumbnail_path, "rb") as img_file:
            st.download_button(
                label="📥 ទាញយក Thumbnail នេះ",
                data=img_file,
                file_name="video_thumbnail.jpg",
                mime="image/jpeg"
            )

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

if st.button("🚀 ចាប់ផ្តើមដំណើរការបកប្រែ និងបង្កើតសំឡេង MP3"):
    if not api_key:
        st.error("សូមបញ្ចូល Google Gemini API Key នៅកន្លែង Settings ខាងឆ្វេងជាមុនសិន!")
    elif not video_path:
        st.warning("សូម Upload វីដេអូ ឬទាញយកវីដេអូតាមលីងជាមុនសិន!")
    else:
        try:
            client = genai.Client(api_key=api_key)
            
            with st.spinner("កំពុងបកប្រែសាច់រឿងពេញលេញគ្រប់វិនាទីពីវីដេអូ... (សូមរង់ចាំបន្តិច)"):
                video_file = client.files.upload(file=video_path)
                
                prompt = (
                    "Listen and translate the full video from start to finish into natural Khmer. "
                    "Do NOT summarize, do NOT recap, and do NOT cut short. Translate every conversation, event, and detail thoroughly "
                    "so that the narrative covers the entire runtime sequence naturally. "
                    "CRITICAL INSTRUCTIONS: "
                    "1. Present it as a smooth, continuous script covering all events from beginning to the end. "
                    "2. Do NOT include any timestamps, time markers, brackets, or code symbols."
                )
                
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=[video_file, prompt]
                )
                
                translated_text = response.text

            st.success("បកប្រែសាច់រឿងពេញលេញបានជោគជ័យ!")
            
            st.subheader("📝 អត្ថបទសាច់រឿងពេញលេញ (សម្រាប់ Copy ដាក់ CapCut):")
            st.info(translated_text)

            with st.spinner("កំពុងបង្កើតសំឡេង Dubbing ខ្មែរពេញលេញ (MP3)..."):
                audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                asyncio.run(generate_long_audio(translated_text, selected_voice, audio_path))

            st.subheader("🔊 សំឡេង Dubbing ខ្មែរពេញលេញ (AI Voice MP3):")
            st.audio(audio_path)
            
            with open(audio_path, "rb") as f:
                st.download_button(
                    label="📥 ទាញយកសំឡេង MP3 នេះ",
                    data=f,
                    file_name="khmer_dubbing_audio.mp3",
                    mime="audio/mp3"
                )

        except Exception as e:
            st.error(f"មានបញ្ហាកើតឡើង: {e}")
