import streamlit as st
from google import genai
import asyncio
import edge_tts
import os
import tempfile
import re
import cv2
from moviepy.editor import VideoFileClip, AudioFileClip

st.set_page_config(page_title="AI Auto-Dubbing & Video Merger Pro", layout="centered")

st.title("🎬 AI Auto-Dubbing & Video Merger Pro")
st.write("បកប្រែចំឃ្លាតួអង្គ **បញ្ចូលសំឡេងថ្មីចូលវីដេអូដោយស្វ័យប្រវត្តិ** (ខុសម៉ោងក្រោម ១០វិនាទី)!")

api_key = st.text_input("បញ្ចូល Gemini API Key របស់អ្នក:", type="password")

# ជម្រើសសំឡេងប្រុស ឬស្រី
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

# Function សម្រាប់ទាញយករយៈពេលវីដេអូជាវិនាទី
def get_video_duration(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    if fps > 0:
        return frame_count / fps
    return 0

# Function សម្រាប់លុប Timecode និងការពិពណ៌នាចេញទាំងស្រុង មុនយកទៅធ្វើ Audio
def clean_text_for_tts(text):
    cleaned = re.sub(r'\[\d{2}:\d{2}\s*-\s*\d{2}:\d{2}\]|\d{2}:\d{2}', '', text)
    cleaned = re.sub(r'\(.*?\)|\[.*?\]|\*.*?\*', '', cleaned)
    cleaned = cleaned.replace('—', ' ').replace('\n', ' ')
    return cleaned.strip()

# Function សម្រាប់ generate សំឡេងជាមួយ edge-tts
async def generate_edge_tts(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

# Function សម្រាប់បញ្ចូលសំឡេងថ្មីចូលទៅក្នុងវីដេអូដើម
def merge_audio_video(video_path, audio_path, output_path):
    video_clip = VideoFileClip(video_path)
    audio_clip = AudioFileClip(audio_path)
    
    # កំណត់សំឡេងថ្មីចូលវីដេអូ (ប្រសិនបើវីដេអូដើមมีសំឡេង អាចជំនួស ឬលុបសំឡេងចាស់ចេញ)
    final_clip = video_clip.set_audio(audio_clip)
    
    # Export ចេញជាវីដេអូថ្មី
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=video_clip.fps)
    
    video_clip.close()
    audio_clip.close()
    final_clip.close()

if uploaded_file is not None:
    st.video(uploaded_file)

if st.button("ចាប់ផ្តើមបកប្រែ និងបញ្ចូលសំឡេងចូលវីដេអូ 🚀"):
    if not api_key:
        st.error("សូមបញ្ចូល Gemini API Key ជាមុនសិន!")
    elif uploaded_file is None:
        st.warning("សូម Upload វីដេអូជាមុនសិន!")
    else:
        with st.spinner("កំពុងវិភាគ បកប្រែ និងបញ្ចូលសំឡេងចូលវីដេអូ..."):
            try:
                # បង្កើត Temp File សម្រាប់វីដេអូ
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tfile.write(uploaded_file.read())
                video_path = tfile.name

                # គណនារយៈពេលវីដេអូជាវិនាទី
                duration_sec = get_video_duration(video_path)
                
                if duration_sec > 900:
                    st.error("❌ វីដេអូរបស់អ្នកវែងពេក! សូមជ្រើសរើសវីដេអូដែលមានរយៈពេល ១៥នាទីចុះក្រោម។")
                else:
                    target_words = int(duration_sec * 2.5)
                    st.info(f"⏱️ រយៈពេលវីដេអូពិតប្រាកដ: {duration_sec/60:.2f} នាទី ({duration_sec:.1f} វិនាទី)")

                    client = genai.Client(api_key=api_key)
                    st.info("កំពុងបញ្ជូនវីដេអូទៅកាន់ Gemini AI...")
                    
                    video_file = client.files.upload(file=video_path)

                    prompt = (
                        "អ្នកគឺជាអ្នកបកប្រែប្រយោគតួអង្គភាពយន្តអាជីព។ "
                        "សូមទស្សនាវីដេអូនេះតាំងពីដើមរហូតដល់ចប់ រួចបកប្រែ **เฉพาะ ឃ្លាប្រយោគដែលតួអង្គនិយាយ** ជាភាសាខ្មែរ "
                        "ឱ្យមានប្រវែងគ្រប់គ្រាន់ប្រហែល " + str(target_words) + " ពាក្យ ដើម្បីឱ្យស្មើម៉ោងជាមួយវីដេអូ។ "
                        "ហាមសម្រាយរឿង និងហាមពិពណ៌នាឈុតឆាកក្នុងវង់ក្រចក (Pure Dialogue Only)។ "
                        "រក្សាកូដពេលវេលា [MM:SS - MM:SS] ទុកនៅខាងមុខប្រយោគនីមួយៗ។"
                    )
                    
                    response = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=[video_file, prompt],
                    )
                    
                    raw_text = response.text
                    
                    st.subheader("📝 អត្ថបទបកប្រែចំប្រយោគតួអង្គ:")
                    st.text_area("Copy Text ទីនេះ:", raw_text, height=200)
                    
                    # លុប Timecode និងការពិពណ៌នាចេញ មុនយកទៅធ្វើ Audio
                    clean_text = clean_text_for_tts(raw_text)
                    
                    st.info(f"កំពុងបង្កើតសំឡេងអាន និងបញ្ចូលចូលវីដេអូ ({voice_choice})...")
                    
                    # បង្កើត Temp File សម្រាប់ Audio និង Output Video
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as audio_tf:
                        audio_path = audio_tf.name

                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as output_tf:
                        output_video_path = output_tf.name

                    # 1. បង្កើតសំឡេង MP3
                    asyncio.run(generate_edge_tts(clean_text, selected_voice, audio_path))
                    
                    # 2. បញ្ចូលសំឡេងថ្មីចូលទៅក្នុងវីដេអូដើម
                    merge_audio_video(video_path, audio_path, output_video_path)
                    
                    st.success("🎉 ការបញ្ចូលសំឡេងទៅក្នុងវីដេអូបានសម្រេចជោគជ័យ!")
                    
                    # បង្ហាញវីដេអូចុងក្រោយដែលបាន Dubbing រួច
                    st.subheader("🎬 វីដេអូថ្មីដែលបានដាក់សំឡេងបកប្រែរួច:")
                    st.video(output_video_path)
                    
                    # ប៊ូតុង Download វីដេអូ
                    with open(output_video_path, "rb") as file:
                        st.download_button(
                            label="📥 ទាញយកវីដេអូនោះ (Download Dubbed Video)",
                            data=file,
                            file_name="dubbed_video_output.mp4",
                            mime="video/mp4"
                        )
                
                # លុប File Temp ចោលវិញ
                for p in [video_path, audio_path]:
                    if os.path.exists(p):
                        os.remove(p)
                
            except Exception as e:
                st.error(f"មានបញ្ហាកើតឡើង: {e}")
                        
