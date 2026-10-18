import streamlit as st
from google import genai
import asyncio
import edge_tts
import os
import tempfile
import re
import cv2
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

st.set_page_config(page_title="AI Cinematic Dubbing & Audio Mixing Pro", layout="centered")

st.title("🎬 AI Cinematic Dubbing & Audio Mixing Pro")
st.write("បកប្រែចំឃ្លាតួអង្គ **លាយសំឡេងភ្លេង/សំឡេងវ៉ៃគ្នាដើមជាមួយសំឡេងអាន AI** មិនបាំងគ្នា! រក្សាសំឡេងសកម្មភាពដើមល្វើយៗអមជាមួយសំឡេងអានខ្មែរ។")

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

# Function សម្រាប់លាយសំឡេងដើម (BGM/Fighting sounds) និងសំឡេងអាន AI ចូលគ្នា (Audio Mixing)
def mix_audio_and_video(video_path, tts_audio_path, output_path):
    video_clip = VideoFileClip(video_path)
    duration = video_clip.duration
    tts_audio = AudioFileClip(tts_audio_path)
    
    if video_clip.audio is not None:
        # ទាញយកសំឡេងដើមពីវីដេអូ ហើយបន្ថយសំឡេងវាឱ្យនៅត្រឹម 25% (0.25) ដើម្បីកុំឱ្យបាំងសំឡេងអានខ្មែរ
        original_audio = video_clip.audio.volumex(0.25)
        # កែសម្រួលសំឡេងអាន AI ឱ្យខ្លាំងច្បាស់នៅកម្រិត 100% (1.0)
        tts_audio_vol = tts_audio.volumex(1.0)
        # លាយសំឡេងទាំងពីរចូលគ្នា (CompositeAudioClip)
        final_audio = CompositeAudioClip([original_audio, tts_audio_vol]).set_duration(duration)
    else:
        final_audio = tts_audio.set_duration(duration)
        
    final_video = video_clip.set_audio(final_audio)
    final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=video_clip.fps)
    
    video_clip.close()
    tts_audio.close()
    final_video.close()

if uploaded_file is not None:
    st.video(uploaded_file)

if st.button("ចាប់ផ្តើមបកប្រែ លាយសំឡេង និងបង្កើតវីដេអូ 🚀"):
    if not api_key:
        st.error("សូមបញ្ចូល Gemini API Key ជាមុនសិន!")
    elif uploaded_file is None:
        st.warning("សូម Upload វីដេអូជាមុនសិន!")
    else:
        with st.spinner("កំពុងវិភាគ បកប្រែ និងធ្វើការលាយសំឡេងវីដេអូ (Audio Mixing)..."):
            try:
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tfile.write(uploaded_file.read())
                video_path = tfile.name

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
                    
                    clean_text = clean_text_for_tts(raw_text)
                    
                    st.info(f"កំពុងបង្កើតសំឡេងអាន និងលាយបញ្ចូលគ្នាជាមួយសំឡេងសកម្មភាពក្នុងរឿង ({voice_choice})...")
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as audio_tf:
                        audio_path = audio_tf.name

                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as output_tf:
                        output_video_path = output_tf.name

                    # 1. បង្កើតសំឡេង MP3 ជាមួយ edge-tts
                    asyncio.run(generate_edge_tts(clean_text, selected_voice, audio_path))
                    
                    # 2. លាយសំឡេងដើម (BGM/Fighting sounds) និងសំឡេងអាន AI ចូលគ្នាជាមួយវីដេអូ
                    mix_audio_and_video(video_path, audio_path, output_video_path)
                    
                    st.success("🎉 ការលាយសំឡេង និងបង្កើតវីដេអូបានសម្រេចជោគជ័យ!")
                    
                    st.subheader("🎬 វីដេអូចុងក្រោយ (ມີសំឡេងវ៉ៃគ្នា/ភ្លេងដើមល្វើយៗ + សំឡេងអានខ្មែរ):")
                    st.video(output_video_path)
                    
                    with open(output_video_path, "rb") as file:
                        st.download_button(
                            label="📥 ទាញយកវីដេអូ (Download Mixed Video)",
                            data=file,
                            file_name="mixed_dubbed_video.mp4",
                            mime="video/mp4"
                        )
                
                for p in [video_path, audio_path]:
                    if os.path.exists(p):
                        os.remove(p)
                
            except Exception as e:
                st.error(f"មានបញ្ហាកើតឡើង: {e}")
    
