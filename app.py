import streamlit as st
import asyncio
import edge_tts
import os
import tempfile
import re
import cv2
import numpy as np

# Import moviepy ដោយសុវត្ថិភាព ដើម្បីការពារបញ្ហា ImportError
try:
    from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
except ImportError:
    from moviepy.video.io.VideoFileClip import VideoFileClip
    from moviepy.audio.io.AudioFileClip import AudioFileClip
    from moviepy.audio.CompositeAudioClip import CompositeAudioClip

st.set_page_config(page_title="AI Khmer Video Dubbing Pro", layout="centered")

st.title("🎬 AI Khmer Video Dubbing Pro (Smart Background Audio)")
st.write("ប្រព័ន្ធដាប់ប៊ីង៖ រក្សាសំឡេងតន្ត្រី/បរិយាកាសដើមនៅកន្លែងតួអង្គអត់និយាយ និងដាក់សំឡេង AI ពេលតួអង្គនិយាយ!")

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

# 🎛️ ការកំណត់កម្រិតសំឡេង
st.sidebar.header("🎛️ កម្រិតសំឡេង (Smart Audio Mixer)")
ai_volume = st.sidebar.slider("កម្រិតសំឡេង AI (Voice Volume):", 0.5, 2.0, 1.4, 0.1)
bg_volume_during_speech = st.sidebar.slider("កម្រិតសំឡេងដើមពេលតួអង្គនិយាយ (Duck Volume):", 0.0, 0.5, 0.1, 0.05)
bg_volume_normal = st.sidebar.slider("កម្រិតសំឡេងដើមពេលអត់មានអ្នកនិយាយ (Normal BG Volume):", 0.1, 1.0, 0.8, 0.05)

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

async def generate_edge_tts(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

if uploaded_file is not None:
    st.video(uploaded_file)

if "output_video_path" not in st.session_state:
    st.session_state.output_video_path = None

if st.button("🚀 ចាប់ផ្តើមបង្កើតវីដេអូ (Smart Audio Mixing)"):
    if uploaded_file is None:
        st.warning("សូម Upload វីដេអូជាមុនសិន!")
    elif not flow_script.strip():
        st.warning("សូម Paste ស្គ្រីប Timestamps ពី Google Flow ជាមុនសិន!")
    else:
        status_text = st.empty()
        status_text.info("🔄 កំពុងបង្កើតសំឡេង AI និងកែច្នៃសំឡេងផ្ទៃខាងក្រោយ (Smart Ducking)...")
        
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
                ai_audio_clips = []
                
                # បង្កើតសំឡេង AI តាម Timestamps
                for item in dialogues:
                    chunk_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                    temp_audio_files.append(chunk_audio_path)
                    
                    asyncio.run(generate_edge_tts(item["text"], selected_voice, chunk_audio_path))
                    
                    if os.path.exists(chunk_audio_path) and os.path.getsize(chunk_audio_path) > 0:
                        audio_clip = AudioFileClip(chunk_audio_path)
                        audio_clip = audio_clip.volumex(ai_volume).set_start(item["start"])
                        ai_audio_clips.append(audio_clip)

                status_text.info("🎬 កំពុងលាយបញ្ចូលគ្នារវាងសំឡេង AI និងសំឡេងបរិយាកាសដើម...")
                
                audio_mix_list = []
                
                # បើវីដេអូដើមមានសំឡេង យើងបង្កើត Custom Volume តាមពេលវេលា
                if video_clip.audio is not None:
                    original_audio = video_clip.audio
                    
                    # បង្កើត Function កំណត់សំឡេងដើមឱ្យខ្លាំងពេលអត់និយាយ និងខ្សោយពេលមាន AI និយាយ (Audio Ducking)
                    def dynamic_volume(get_frame, t):
                        # t គឺពេលវេលាបច្ចុប្បន្នជាវិនាទី
                        is_speaking = False
                        for d in dialogues:
                            if d["start"] <= t <= d["end"]:
                                is_speaking = True
                                break
                        
                        vol = bg_volume_during_speech if is_speaking else bg_volume_normal
                        frame = get_frame(t)
                        return frame * vol

                    # អនុវត្ត Dynamic Volume លើសំឡេងដើម
                    processed_original_audio = original_audio.fl(dynamic_volume, keep_duration=True)
                    audio_mix_list.append(processed_original_audio)
                
                # បន្ថែមសំឡេង AI ចូល
                if ai_audio_clips:
                    ai_composite = CompositeAudioClip(ai_audio_clips).set_duration(duration)
                    audio_mix_list.append(ai_composite)
                
                # ផ្គុំសំឡេងទាំងអស់ចូលគ្នា
                if audio_mix_list:
                    final_audio = CompositeAudioClip(audio_mix_list).set_duration(duration)
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
                status_text.success("🎉 បង្កើតវីដេអូលាយសំឡេងឆ្លាតវៃជោគជ័យ ១០០%!")
                
                for p in temp_audio_files:
                    if os.path.exists(p): os.remove(p)
                if os.path.exists(video_path): os.remove(video_path)

        except Exception as e:
            st.error(f"មានបញ្ហាកើតឡើង: {e}")

if st.session_state.output_video_path and os.path.exists(st.session_state.output_video_path):
    st.success("🎉 វីដេអូរួចរាល់ជាស្ថាពរ!")
    st.subheader("🎬 វីដេអូចុងក្រោយ:")
    st.video(st.session_state.output_video_path)
    
    with open(st.session_state.output_video_path, "rb") as file:
        st.download_button(
            label="📥 ទាញយកវីដេអូចុងក្រោយ (Download Video)",
            data=file,
            file_name="khmer_smart_dubbed.mp4",
            mime="video/mp4"
        )
        
