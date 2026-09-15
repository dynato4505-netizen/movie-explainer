import streamlit as st
from google import genai
import asyncio
import edge_tts
import tempfile
import os
import yt_dlp
import re
import cv2
from pydub import AudioSegment  # បន្ថែមសម្រាប់កែច្នៃល្បឿនសំឡេង

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

# --- ជ្រើសរើសវិធីសាស្ត្របញ្ចូលវីដេអូ ---
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
    st.info("💡 **ចំណាំ៖** សម្រាប់ RedNote សូម Download វីដេអូទុកក្នុងទូរសព្ទ/កុំព្យូទ័រ រួចជ្រើសរើស Upload ផ្ទាល់ គឺធានាថាលឿន និងមិន Error ទេ។")
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

# ប្រសិនបើមានវីដេអូរួចរាល់ ដំណើរការកាត់យក Thumbnail
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

# មុខងារជំនួយ៖ គណនារយៈពេលវីដេអូ និងកែសម្រួលល្បឿនសំឡេងឱ្យដើរស្មើគ្នា
def match_audio_to_video(video_file_path, audio_file_path):
    try:
        # 1. យករយៈពេលវីដេអូជាវិនាទី (ដោយប្រើ OpenCV)
        cap = cv2.VideoCapture(video_file_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        cap.release()
        
        if fps <= 0 or frame_count <= 0:
            return audio_file_path  # បើទាញយកមិនបាន រក្សាទុកសំឡេងដើម
            
        video_duration_sec = frame_count / fps
        
        # 2. យករយៈពេលសំឡេងដើម (ដោយប្រើ Pydub)
        sound = AudioSegment.from_file(audio_file_path, format="mp3")
        audio_duration_sec = len(sound) / 1000.0  # បំប្លែងពី milliseconds ទៅ seconds
        
        # 3. គណនារកកម្រិតល្បឿនដែលត្រូវប្តូរ (Speed Ratio)
        speed_ratio = audio_duration_sec / video_duration_sec
        
        # កំណត់ទំហំកំណត់ (guardrails) ដើម្បីកុំឱ្យសំឡេងលឿន ឬយឺតហួសហេតុពេក (ត្រឹម 0.7x ដល់ 1.8x)
        if speed_ratio < 0.7:
            speed_ratio = 0.7
        elif speed_ratio > 1.8:
            speed_ratio = 1.8
            
        # ប្រសិនបើល្បឿនខុសគ្នាឆ្ងាយ ទើបធ្វើការ Sync
        if abs(audio_duration_sec - video_duration_sec) > 3.0:
            # ប្តូរល្បឿនសំឡេងដោយរក្សាកម្រិតសំឡេងដើម (Pitch)
            altered_sound = sound.speedup(playback_speed=speed_ratio)
            synced_output_path = tempfile.NamedTemporaryFile(delete=False, suffix='_synced.mp3').name
            altered_sound.export(synced_output_path, format="mp3")
            return synced_output_path
            
    except Exception as e:
        print(f"Sync error: {e}")
        
    return audio_file_path

if st.button("🚀 ចាប់ផ្តើមដំណើរការបកប្រែ និងបង្កើតសំឡេង MP3 (Auto-Sync)"):
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

            with st.spinner("កំពុងបង្កើតសំឡេង Dubbing និងធ្វើការ Sync ឱ្យស្មើនឹងរយៈពេលវីដេអូ..."):
                raw_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                asyncio.run(generate_long_audio(translated_text, selected_voice, raw_audio_path))
                
                # ហៅមុខងារធ្វើឱ្យសំឡេងដើរស្មើជាមួយវីដេអូ
                audio_path = match_audio_to_video(video_path, raw_audio_path)

            st.subheader("🔊 សំឡេង Dubbing ខ្មែរដែលបាន Sync ត្រូវជាមួយវីដេអូ (MP3):")
            st.audio(audio_path)
            
            with open(audio_path, "rb") as f:
                st.download_button(
                    label="📥 ទាញយកសំឡេង MP3 នេះ",
                    data=f,
                    file_name="khmer_dubbing_synced.mp3",
                    mime="audio/mp3"
                )

        except Exception as e:
            st.error(f"មានបញ្ហាកើតឡើង: {e}")
        
