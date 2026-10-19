import streamlit as st
from google import genai
import asyncio
import edge_tts
import os
import tempfile
import re
import cv2
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

st.set_page_config(page_title="AI Smart Cinematic Dubbing Pro", layout="centered")

st.title("🎬 AI Smart Cinematic Dubbing Pro")
st.write("ប្រព័ន្ធដាប់ប៊ីងវីដេអូកម្រិតខ្ពស់៖ បន្ថយសំឡេងចិនឱ្យស្ងាត់ល្វើយៗ (BGM 10%) និង **បង្កើនសំឡេង AI ខ្មែរឱ្យខ្លាំងច្បាស់ល្អ**!")

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

if "output_video_path" not in st.session_state:
    st.session_state.output_video_path = None
if "raw_text_result" not in st.session_state:
    st.session_state.raw_text_result = ""

if st.button("ចាប់ផ្តើមដាប់ប៊ីងកម្រិតខ្ពស់ (Volume Balanced) 🚀"):
    if not api_key:
        st.error("សូមបញ្ចូល Gemini API Key ជាមុនសិន!")
    elif uploaded_file is None:
        st.warning("សូម Upload វីដេអូជាមុនសិន!")
    else:
        with st.spinner("កំពុងវិភាគវីដេអូ ទាញយកកូដពេលវេលា និងកែតម្រូវកម្រិតសំឡេង..."):
            try:
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tfile.write(uploaded_file.read())
                video_path = tfile.name

                duration_sec = get_video_duration(video_path)
                
                if duration_sec > 900:
                    st.error("❌ វីដេអូរបស់អ្នកវែងពេក! សូមជ្រើសរើសវីដេអូដែលមានរយៈពេល ១៥នាទីចុះក្រោម。")
                else:
                    client = genai.Client(api_key=api_key)
                    video_file = client.files.upload(file=video_path)

                    prompt = (
                        "អ្នកគឺជាអ្នកបកប្រែប្រយោគតួអង្គភាពយន្តអាជីព។ "
                        "សូមទស្សនាវីដេអូនេះដោយផ្ចង់ស្មារតីលើបបូរមាត់តួអង្គ រួចកំណត់ពេលវេលា [MM:SS - MM:SS] ឱ្យបានត្រឹមត្រូវបំផុត "
                        "សម្រាប់រាល់ឃ្លាប្រយោគដែលតួអង្គនិយាយ ហើយបកប្រែជាភាសាខ្មែរតាមទម្រង់នេះដាច់ខាត៖\n"
                        "[00:05 - 00:08] សួស្ដី\n"
                        "[00:12 - 00:15] ប្រយោគបន្ទាប់...\n"
                        "ហាមសរសេរខុសពីទម្រង់កូដពេលវេលានេះ និងហាមពន្យល់រឿងក្រៅពីប្រយោគតួអង្គនិយាយ。"
                    )
                    
                    response = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=[video_file, prompt],
                    )
                    
                    st.session_state.raw_text_result = response.text
                    dialogues = parse_timestamps(st.session_state.raw_text_result)
                    
                    if not dialogues:
                        st.error("❌ រកមិនឃើញកូដពេលវេលាត្រឹមត្រូវទេ។ សូមព្យាយាមម្ដងទៀត។")
                    else:
                        st.info(f"រកឃើញប្រយោគចំនួន {len(dialogues)} កំពុងបង្កើតសំឡេង AI និងកែច្នៃកម្រិតសំឡេង...")
                        
                        video_clip = VideoFileClip(video_path)
                        temp_audio_files = []
                        audio_clips_to_composite = []
                        
                        for item in dialogues:
                            chunk_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                            temp_audio_files.append(chunk_audio_path)
                            
                            asyncio.run(generate_edge_tts(item["text"], selected_voice, chunk_audio_path))
                            
                            if os.path.exists(chunk_audio_path) and os.path.getsize(chunk_audio_path) > 0:
                                audio_clip = AudioFileClip(chunk_audio_path)
                                # 🔊 បង្កើនសំឡេង AI ខ្មែរឱ្យខ្លាំងជាងមុន ១.5 ដង (volumex 1.5) ដើម្បីឱ្យលឺច្បាស់ល្អ
                                audio_clip = audio_clip.volumex(1.5).set_start(item["start"])
                                audio_clips_to_composite.append(audio_clip)

                        if video_clip.audio is not None:
                            subclips_audio = []
                            last_end = 0.0
                            # 🔊 បន្ថយសំឡេងដើមឱ្យនៅសល់ត្រឹម ១០% (volumex 0.1) ដើម្បីកុំឱ្យសំឡេងចិនលឺខ្លាំងបាំងសំឡេងខ្មែរ
                            orig_audio = video_clip.audio.volumex(0.1)
                            
                            for d in dialogues:
                                if d["start"] > last_end:
                                    subclips_audio.append(orig_audio.subclip(last_end, d["start"]))
                                last_end = max(last_end, d["end"])
                                
                            if last_end < video_clip.duration:
                                subclips_audio.append(orig_audio.subclip(last_end, video_clip.duration))
                                
                            if subclips_audio:
                                from moviepy.editor import concatenate_audioclips
                                clean_bgm = concatenate_audioclips(subclips_audio)
                                all_audios = [clean_bgm] + audio_clips_to_composite
                            else:
                                all_audios = audio_clips_to_composite
                        else:
                            all_audios = audio_clips_to_composite

                        final_audio = CompositeAudioClip(all_audios).set_duration(video_clip.duration)
                        final_video = video_clip.set_audio(final_audio)
                        
                        output_video_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                        final_video.write_videofile(output_video_path, codec="libx264", audio_codec="aac", fps=video_clip.fps)
                        
                        video_clip.close()
                        final_video.close()
                        
                        st.session_state.output_video_path = output_video_path
                        
                        for p in temp_audio_files:
                            if os.path.exists(p):
                                os.remove(p)
                        if os.path.exists(video_path):
                            os.remove(video_path)

            except Exception as e:
                st.error(f"មានបញ្ហាកើតឡើង: {e}")

if st.session_state.raw_text_result:
    st.subheader("📝 កូដពេលវេលា និងអត្ថបទបកប្រែ:")
    st.text_area("Timestamps & Text:", st.session_state.raw_text_result, height=200)

if st.session_state.output_video_path and os.path.exists(st.session_state.output_video_path):
    st.success("🎉 ការកែតម្រូវកម្រិតសំឡេងបានសម្រេចជោគជ័យ ១០០%!")
    st.subheader("🎬 វីដេអូចុងក្រោយ:")
    st.video(st.session_state.output_video_path)
    
    with open(st.session_state.output_video_path, "rb") as file:
        st.download_button(
            label="📥 ទាញយកវីដេអូ (Balanced Dubbed Video)",
            data=file,
            file_name="balanced_dubbed_video.mp4",
            mime="video/mp4"
                    )
            
