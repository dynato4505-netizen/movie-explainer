import streamlit as st
from google import genai
import asyncio
import edge_tts
import os
import tempfile
import re
import cv2
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, AudioClip
import numpy as np

st.set_page_config(page_title="AI Smart Cinematic Dubbing Pro", layout="centered")

st.title("🎬 AI Smart Cinematic Dubbing Pro")
st.write("ប្រព័ន្ធដាប់ប៊ីងវីដេអូកម្រិតខ្ពស់៖ រក្សាសំឡេងភ្លេង BGM ធម្មតា និង **ដកសំឡេងចិនเฉพาะពេលតួអង្គនិយាយ** ដាក់ជំនួសដោយសំឡេង AI ខ្មែរចំម៉ោង ១០០%!")

api_key = st.text_input("បញ្ចូល Gemini API Key របស់អ្នក:", type="password")

voice_choice = st.selectbox(
    "ជ្រើសរើសសំឡេង Dubbing:",
    ("ស្រី (Sreymom)", "ប្រុស (Piseth)")
)

voice_map = {
    "ស្រី (Sreymom)": "km-KH-SreymomNeural",
    "ប្រុស (Piseth)": "km-KH-PisethNeural"
}
selected_voice = voice_map[voice_choice]

uploaded_file = st.file_uploader("ជ្រើសរើសវីដេអូ (MP4, MOV - ក្រោម ១៥នាទី):", type=["mp4", "mov", "avi"])

def get_video_duration(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    if fps > 0:
        return frame_count / fps
    return 0

async def generate_edge_tts(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

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

if uploaded_file is not None:
    st.video(uploaded_file)

if st.button("ចាប់ផ្តើមដាប់ប៊ីងឆ្លាតវៃ (Smart Ducking) 🚀"):
    if not api_key:
        st.error("សូមបញ្ចូល Gemini API Key ជាមុនសិន!")
    elif uploaded_file is None:
        st.warning("សូម Upload វីដេអូជាមុនសិន!")
    else:
        with st.spinner("កំពុងវិភាគវីដេអូ ទាញយកកូដពេលវេលា និងដំណើរការ Smart Audio Ducking..."):
            try:
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tfile.write(uploaded_file.read())
                video_path = tfile.name

                duration_sec = get_video_duration(video_path)
                
                if duration_sec > 900:
                    st.error("❌ វីដេអូរបស់អ្នកវែងពេក! សូមជ្រើសរើសវីដេអូដែលមានរយៈពេល ១៥នាទីចុះក្រោម។")
                else:
                    client = genai.Client(api_key=api_key)
                    video_file = client.files.upload(file=video_path)

                    prompt = (
                        "អ្នកគឺជាអ្នកបកប្រែប្រយោគតួអង្គភាពយន្តអាជីព។ "
                        "សូមទស្សនាវីដេអូនេះដោយផ្ចង់ស្មារតីលើបបូរមាត់តួអង្គ រួចកំណត់ពេលវេលា [MM:SS - MM:SS] ឱ្យបានត្រឹមត្រូវបំផុត "
                        "សម្រាប់រាល់ឃ្លាប្រយោគដែលតួអង្គនិយាយ ហើយបកប្រែជាភាសាខ្មែរតាមទម្រង់នេះដាច់ខាត៖\n"
                        "[00:05 - 00:08] សួស្ដី\n"
                        "[00:12 - 00:15] ប្រយោគបន្ទាប់...\n"
                        "ហាមសរសេរខុសពីទម្រង់កូដពេលវេលានេះ និងហាមពន្យល់រឿងក្រៅពីប្រយោគតួអង្គនិយាយ។"
                    )
                    
                    response = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=[video_file, prompt],
                    )
                    
                    raw_text = response.text
                    st.subheader("📝 កូដពេលវេលា និងអត្ថបទបកប្រែ:")
                    st.text_area("Timestamps & Text:", raw_text, height=200)
                    
                    dialogues = parse_timestamps(raw_text)
                    
                    if not dialogues:
                        st.error("❌ រកមិនឃើញកូដពេលវេលាត្រឹមត្រូវទេ។ សូមព្យាយាមម្ដងទៀត។")
                    else:
                        st.info(f"រកឃើញប្រយោគចំនួន {len(dialogues)} កំពុងបង្កើតសំឡេង AI និងកែច្នៃសំឡេងវីដេអូ...")
                        
                        video_clip = VideoFileClip(video_path)
                        temp_audio_files = []
                        audio_clips_to_composite = []
                        
                        # 1. បង្កើតសំឡេង AI តាមម៉ោងនីមួយៗ
                        for item in dialogues:
                            chunk_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                            temp_audio_files.append(chunk_audio_path)
                            
                            asyncio.run(generate_edge_tts(item["text"], selected_voice, chunk_audio_path))
                            
                            if os.path.exists(chunk_audio_path) and os.path.getsize(chunk_audio_path) > 0:
                                audio_clip = AudioFileClip(chunk_audio_path)
                                audio_clip = audio_clip.set_start(item["start"])
                                audio_clips_to_composite.append(audio_clip)

                        # 2. បច្ចេកទេស Smart Ducking៖ កាត់បន្ថយសំឡេងដើម (Mute/Ducking) ចំពេលតួអង្គនិយាយ
                        if video_clip.audio is not None:
                            original_audio = video_clip.audio
                            
                            # បង្កើត Function សម្រាប់បញ្ចុះសំឡេងដើមឱ្យនៅ 0 (ស្ងាត់) ត្រង់ចំណុចដែលមានតួអង្គនិយាយ
                            def duck_audio(get_frame, t):
                                frame = get_frame(t)
                                # ពិនិត្យមើលថាតើពេលវេលាបច្ចុប្បន្ន (t) ស្ថិតក្នុងចន្លោះពេលតួអង្គនិយាយដែរឬទេ
                                for d in dialogues:
                                    if d["start"] <= t <= d["end"]:
                                        return np.array([0.0, 0.0]) # ផ្ដាច់សំឡេងដើមចោលទាំងស្រុងត្រង់កន្លែងនិយាយ
                                return frame # រក្សាសំឡេងភ្លេងដើមធម្មតាពេលអត់មានអ្នកនិយាយ
                                
                            smart_bgm = original_audio.fl(duck_audio)
                            all_audios = [smart_bgm] + audio_clips_to_composite
                        else:
                            all_audios = audio_clips_to_composite

                        final_audio = CompositeAudioClip(all_audios).set_duration(video_clip.duration)
                        final_video = video_clip.set_audio(final_audio)
                        
                        output_video_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                        final_video.write_videofile(output_video_path, codec="libx264", audio_codec="aac", fps=video_clip.fps)
                        
                        video_clip.close()
                        final_video.close()
                        
                        st.success("🎉 ការដាប់ប៊ីងឆ្លាតវៃ (Smart Ducking) បានសម្រេចជោគជ័យ ១០០%!")
                        st.subheader("🎬 វីដេអូចុងក្រោយ:")
                        st.video(output_video_path)
                        
                        with open(output_video_path, "rb") as file:
                            st.download_button(
                                label="📥 ទាញយកវីដេអូ (Smart Dubbed Video)",
                                data=file,
                                file_name="smart_dubbed_video.mp4",
                                mime="video/mp4"
                            )
                            
                        for p in temp_audio_files:
                            if os.path.exists(p):
                                os.remove(p)
                        if os.path.exists(video_path):
                            os.remove(video_path)

            except Exception as e:
                st.error(f"មានបញ្ហាកើតឡើង: {e}")
