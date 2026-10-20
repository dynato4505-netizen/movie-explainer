import streamlit as st
import asyncio
import edge_tts
import os
import tempfile
import re
import cv2
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, Silence

st.set_page_config(page_title="AI Pure Khmer Dubbing Pro", layout="centered")

st.title("🎬 AI Pure Khmer Dubbing Pro (Auto-Sync)")
st.write("ប្រព័ន្ធដាប់ប៊ីងវីដេអូ៖ ສំឡេង AI ខ្មែរនិយាយចំម៉ោងតួអង្គ និងស្ងាត់ពេលអត់មានអ្នកនិយាយ (លែងបាច់កាត់តច្រើន)!")

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

uploaded_file = st.file_uploader("ជ្រើសរើសវីដេអូដើម (MP4, MOV):", type=["mp4", "mov", "avi"])

# ប្រអប់សម្រាប់ដាក់ Timestamps និងអត្ថបទ (ពី Google Flow)
flow_script = st.text_area(
    "📝 ដាក់ Timestamps & ស្គ្រីប (ពី Google Flow):",
    placeholder="[00:01 - 00:03] សួស្តី\n[00:05 - 00:08] ยินดีต้อนรับ...",
    height=180
)

def get_video_duration(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    if fps > 0:
        return frame_count / fps
    return 0

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

async def generate_edge_tts(text, voice, output_path):
    # បន្ថែម Rate/Pitch បន្តិចបើចាំបាច់ ដើម្បីឱ្យសំឡេងស្តាប់ទៅធម្មជាតិមិនលឿនពេក
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

if uploaded_file is not None:
    st.video(uploaded_file)

if "output_video_path" not in st.session_state:
    st.session_state.output_video_path = None

if st.button("🚀 ចាប់ផ្តើមបង្កើតវីដេអូដាក់សំឡេងចំម៉ោង (Auto-Sync Dub)"):
    if uploaded_file is None:
        st.warning("សូម Upload វីដេអូជាមុនសិន!")
    elif not flow_script.strip():
        st.warning("សូម Paste ស្គ្រីប Timestamps ពី Google Flow ជាមុនសិន!")
    else:
        status_text = st.empty()
        status_text.info("🔄 កំពុងបង្កើតសំឡេង AI និងតម្រៀបម៉ោងស្វ័យប្រវត្តិ...")
        
        try:
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            tfile.write(uploaded_file.read())
            video_path = tfile.name
            video_duration = get_video_duration(video_path)

            dialogues = parse_timestamps(flow_script)
            
            if not dialogues:
                st.error("❌ ទម្រង់ Timestamps មិនត្រឹមត្រូវទេ។ ឧទាហរណ៍៖ [00:01 - 00:03] សួស្តី")
            else:
                video_clip = VideoFileClip(video_path)
                temp_audio_files = []
                audio_clips_to_composite = []
                
                for item in dialogues:
                    chunk_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                    temp_audio_files.append(chunk_audio_path)
                    
                    # បង្កើតសំឡេងតាម Edge-TTS
                    asyncio.run(generate_edge_tts(item["text"], selected_voice, chunk_audio_path))
                    
                    if os.path.exists(chunk_audio_path) and os.path.getsize(chunk_audio_path) > 0:
                        audio_clip = AudioFileClip(chunk_audio_path)
                        
                        # ការពារកុំឱ្យសំឡេងវែងពេកលើសម៉ោងកំណត់ (Stretch/Speed adjustment បើចាំបាច់ ឬកំណត់ Start ឱ្យចំម៉ោង)
                        audio_clip = audio_clip.volumex(1.4).set_start(item["start"])
                        audio_clips_to_composite.append(audio_clip)

                status_text.info("🎬 កំពុងផ្គុំសំឡេងចូលវីដេអូ និងបិទសំឡេងដើម...")
                
                if audio_clips_to_composite:
                    # បង្កើត Composite Audio ឱ្យស្មើនឹងរយៈពេលវីដេអូ ធ្វើឱ្យកន្លែងអត់មាននិយាយស្ងាត់ល្អ
                    final_audio = CompositeAudioClip(audio_clips_to_composite).set_duration(video_clip.duration)
                    final_video = video_clip.set_audio(final_audio)
                else:
                    final_video = video_clip
                    
                output_video_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                final_video.write_videofile(
                    output_video_path, 
                    codec="libx264", 
                    audio_codec="aac", 
                    fps=video_clip.fps
                )
                
                video_clip.close()
                final_video.close()
                
                st.session_state.output_video_path = output_video_path
                status_text.success("🎉 បង្កើតវីដេអូដាប់ប៊ីងចំម៉ោងជោគជ័យ ១០០%!")
                
                # លុបហ្វាល Temp ទុកកន្លែងទំនេរ
                for p in temp_audio_files:
                    if os.path.exists(p): os.remove(p)
                if os.path.exists(video_path): os.remove(video_path)

        except Exception as e:
            st.error(f"មានបញ្ហាកើតឡើង: {e}")

if st.session_state.output_video_path and os.path.exists(st.session_state.output_video_path):
    st.success("🎉 វីដេអូបកប្រែរួចរាល់ជាស្ថាពរ!")
    st.subheader("🎬 វីដេអូចុងក្រោយ (លឺសំឡេង AI ខ្មែរចំម៉ោង និងស្ងាត់ពេលអត់មាននិយាយ):")
    st.video(st.session_state.output_video_path)
    
    with open(st.session_state.output_video_path, "rb") as file:
        st.download_button(
            label="📥 ទាញយកវីដេអូចុងក្រោយ (Download Video)",
            data=file,
            file_name="khmer_dubbed_synced.mp4",
            mime="video/mp4"
                )
        
