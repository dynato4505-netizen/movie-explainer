import streamlit as st
import asyncio
import edge_tts
import os
import tempfile
import time
import re

# Import moviepy ដោយសុវត្ថិភាព
try:
    from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
except ImportError:
    from moviepy.video.io.VideoFileClip import VideoFileClip
    from moviepy.audio.io.AudioFileClip import AudioFileClip
    from moviepy.audio.CompositeAudioClip import CompositeAudioClip

st.set_page_config(page_title="AI Khmer Video Dubbing Pro", layout="centered")

st.title("🎬 AI Khmer Video Dubbing Pro (Safe Mode)")
st.write("ប្រព័ន្ធដាប់ប៊ីងវីដេអូ៖ មានប្រព័ន្ធសម្រាកសុវត្ថិភាព មិនឱ្យដាច់តំណ Server ពេលវីដេអូវែង!")

# ជ្រើសរើសសំឡេង AI ស្រី ឬ ប្រុស
voice_choice = st.selectbox(
    "ជ្រើសរើសសំឡេង Dubbing:",
    ("ស្រី (Sreymom - ធម្មជាតិ)", "ប្រុស (Piseth - ធម្មជាតិ)")
)

voice_map = {
    "ស្រី (Sreymom - ធម្មជាតិ)": "km-KH-SreymomNeural",
    "ប្រុស (Piseth - ធម្មជាតិ)": "km-KH-PisethNeural"
}
selected_voice = voice_map[voice_choice]

# 🎛️ ការកំណត់កម្រិតសំឡេង AI ក្នុង Sidebar
st.sidebar.header("🎛️ ការសារ៉េកម្រិតសំឡេង (Audio Settings)")
ai_volume = st.sidebar.slider("កម្រិតសំឡេង AI (Voice Volume):", 0.5, 2.0, 1.5, 0.1)

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

async def generate_tts_with_retry(text, voice, output_path):
    # ព្យាយាមទាញយក រួមទាំងមានប្រព័ន្ធ Retry ៣ ដងការពារការដាច់តំណ
    for attempt in range(3):
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True
        except Exception:
            if attempt == 2:
                return False
            await asyncio.sleep(1)
    return False

if uploaded_file is not None:
    st.video(uploaded_file)

if "output_video_path" not in st.session_state:
    st.session_state.output_video_path = None

if st.button("🚀 ចាប់ផ្តើមបញ្ចូលសំឡេង AI (Safe Mode)"):
    if uploaded_file is None:
        st.warning("សូម Upload វីដេអូជាមុនសិន!")
    elif not flow_script.strip():
        st.warning("សូម Paste ស្គ្រីប Timestamps ពី Google Flow ជាមុនសិន!")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.info("🔄 កំពុងរៀបចំទិន្នន័យវីដេអូ...")
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
                
                total_items = len(dialogues)
                
                # 🔄 រត់បង្កើតសំឡេងម្ដង១ យ៉ាងស្រទន់ និងមានការសម្រាក (Delay) ដើម្បីការពារ Error
                for i, item in enumerate(dialogues):
                    status_text.info(f"🎙️ កំពុងបង្កើតសំឡេង AI ទី {i+1} នៃ {total_items}...")
                    chunk_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                    temp_audio_files.append(chunk_audio_path)
                    
                    # ហៅ asyncio រត់បង្កើតអូឌីយ៉ូ
                    asyncio.run(generate_tts_with_retry(item["text"], selected_voice, chunk_audio_path))
                    
                    if os.path.exists(chunk_audio_path) and os.path.getsize(chunk_audio_path) > 0:
                        audio_clip = AudioFileClip(chunk_audio_path)
                        audio_clip = audio_clip.volumex(ai_volume).set_start(item["start"])
                        audio_clips_to_composite.append(audio_clip)
                    
                    # 🛑 សម្រាក 0.4 វិនាទីរវាងប្រយោគនីមួយៗ ដើម្បីកុំឱ្យ Server បិទខ្ទប់ IP (Rate Limit)
                    time.sleep(0.4)
                    
                    progress_bar.progress(int((i + 1) / total_items * 70))

                status_text.info("🎬 កំពុងចាក់បញ្ចូលសំឡេង និង Render វីដេអូចុងក្រោយ...")
                progress_bar.progress(80)
                
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
                
                progress_bar.progress(100)
                st.session_state.output_video_path = output_video_path
                status_text.success("🎉 បង្កើតវីដេអូជោគជ័យរលូនល្អ ១០០%!")
                
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
            file_name="khmer_dubbed_safemode.mp4",
            mime="video/mp4"
                )
        
