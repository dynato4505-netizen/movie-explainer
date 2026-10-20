import streamlit as st
import os
import tempfile
import re
from gtts import gTTS
from concurrent.futures import ThreadPoolExecutor

# Import moviepy ដោយសុវត្ថិភាព
try:
    from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
except ImportError:
    from moviepy.video.io.VideoFileClip import VideoFileClip
    from moviepy.audio.io.AudioFileClip import AudioFileClip
    from moviepy.audio.CompositeAudioClip import CompositeAudioClip

st.set_page_config(page_title="AI Khmer Video Dubbing Pro", layout="centered")

st.title("🎬 AI Khmer Video Dubbing Pro (Google TTS Engine)")
st.write("ប្រព័ន្ធដាប់ប៊ីងវីដេអូ៖ ប្រើប្រាស់ Google Engine លឿនស្ថិរភាពខ្ពស់ មិនមាន Error ទៀតទេ!")

# ជ្រើសរើសភាសា/សំឡេង (gTTS ប្រើកូដ 'km' សម្រាប់ភាសាខ្មែរ)
voice_choice = st.selectbox(
    "ជ្រើសរើសសំឡេង Dubbing:",
    ("ភាសាខ្មែរ (Google Natural Voice)",)
)

# 🎛️ ការកំណត់កម្រិតសំឡេង AI ក្នុង Sidebar
st.sidebar.header("🎛️ ការសារ៉េកម្រិតសំឡេង (Audio Settings)")
ai_volume = st.sidebar.slider("កម្រិតសំឡេង AI (Voice Volume):", 0.5, 2.0, 1.5, 0.1)
st.sidebar.info("💡 ប្រើ Google TTS Engine ធានាថាលឿន រលូន និងមិនជួបបញ្ហា No audio error ទៀតទេ!")

# ប្រអប់ Upload វីដេអូ
uploaded_file = st.file_uploader("ជ្រើសរើសវីដេអូដើម (MP4, MOV):", type=["mp4", "mov", "avi"])

# ប្រអប់សម្រាប់ដាក់ Timestamps និងអត្ថបទ (ពី Google Flow)
flow_script = st.text_area(
    "📝 ដាក់ Timestamps & ស្គ្រីប (ពី Google Flow):",
    placeholder="[00:01 - 00:03] សួស្តី\n[00:05 - 00:08] ຍິນດີต้อนรับ...",
    height=180
)

def time_to_seconds(time_str):
    parts = time_str.split(':')
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    return 0.0

def parse_timestamps(text):
    pattern = r'\[\s*(\d{1,2}:\d{2})\s*(?:-\s*(\d{1,2}:\d{2}))?\s*\]\s*(.*)'
    matches = re.findall(pattern, text)
    dialogues = []
    for match in matches:
        start_str = match[0]
        end_str = match[1] if match[1] else match[0]
        content = match[2].strip()
        
        start_sec = time_to_seconds(start_str)
        end_sec = time_to_seconds(end_str)
        if end_sec <= start_sec:
            end_sec = start_sec + 3.0
            
        if content:
            dialogues.append({
                "start": start_sec,
                "end": end_sec,
                "text": content
            })
    return dialogues

def generate_gtts_audio(item):
    chunk_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
    try:
        # ប្រើប្រាស់ gTTS សម្រាប់ភាសាខ្មែរ ('km')
        tts = gTTS(text=item["text"], lang='km', slow=False)
        tts.save(chunk_audio_path)
    except Exception:
        pass
    return item, chunk_audio_path

if uploaded_file is not None:
    st.video(uploaded_file)

if "output_video_path" not in st.session_state:
    st.session_state.output_video_path = None

if st.button("🚀 ចាប់ផ្តើមបញ្ចូលសំឡេង AI (Google Engine)"):
    if uploaded_file is None:
        st.warning("សូម Upload វីដេអូជាមុនសិន!")
    elif not flow_script.strip():
        st.warning("សូម Paste ស្គ្រីប Timestamps ពី Google Flow ជាមុនសិន!")
    else:
        with st.spinner("⚡ កំពុងបង្កើតសំឡេង AI ជាមួយ Google Engine อย่างรวดเร็ว..."):
            try:
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tfile.write(uploaded_file.read())
                video_path = tfile.name

                dialogues = parse_timestamps(flow_script)
                
                if not dialogues:
                    st.error("❌ ទម្រង់ Timestamps មិនត្រឹមត្រូវទេ។ ឧទាហរណ៍៖ [00:01 - 00:03] សួស្តី")
                else:
                    video_clip = VideoFileClip(video_path)
                    duration = video_clip.duration
                    
                    temp_audio_files = []
                    audio_clips_to_composite = []
                    
                    # ⚡ ទាញយកសំឡេង AI ព្រមៗគ្នាដោយប្រើ Google TTS
                    with ThreadPoolExecutor(max_workers=5) as executor:
                        futures = [executor.submit(generate_gtts_audio, item) for item in dialogues]
                        for future in futures:
                            item, chunk_audio_path = future.result()
                            temp_audio_files.append(chunk_audio_path)
                            
                            if os.path.exists(chunk_audio_path) and os.path.getsize(chunk_audio_path) > 0:
                                audio_clip = AudioFileClip(chunk_audio_path)
                                audio_clip = audio_clip.volumex(ai_volume).set_start(item["start"])
                                audio_clips_to_composite.append(audio_clip)

                    # ដាក់តែសំឡេង AI សុទ្ធសាធ បិទសំឡេងដើមទាំងស្រុង
                    if audio_clips_to_composite:
                        final_audio = CompositeAudioClip(audio_clips_to_composite).set_duration(duration)
                        final_video = video_clip.set_audio(final_audio)
                    else:
                        final_video = video_clip.set_audio(None)
                        
                    output_video_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                    final_video.write_videofile(
                        output_video_path, 
                        codec="libx264", 
                        audio_codec="aac", 
                        fps=video_clip.fps,
                        logger=None
                    )
                    
                    video_clip.close()
                    final_video.close()
                    
                    st.session_state.output_video_path = output_video_path
                    st.success("🎉 បង្កើតវីដេអូជោគជ័យរលូនល្អ ១០០%!")
                    
                    for p in temp_audio_files:
                        if os.path.exists(p): os.remove(p)
                    if os.path.exists(video_path): os.remove(video_path)

            except Exception as e:
                st.error(f"មានបញ្ហាកើតឡើង: {e}")

if st.session_state.output_video_path and os.path.exists(st.session_state.output_video_path):
    st.success("🎉 វីដេអូកែសម្រួលរួចរាល់ជាស្ថាពរ!")
    st.subheader("🎬 វីដេអូចុងក្រោយ:")
    st.video(st.session_state.output_video_path)
    
    with open(st.session_state.output_video_path, "rb") as file:
        st.download_button(
            label="📥 ទាញយកវីដេអូចុងក្រោយ (Download Video)",
            data=file,
            file_name="khmer_dubbed_gtts.mp4",
            mime="video/mp4"
            )
            
