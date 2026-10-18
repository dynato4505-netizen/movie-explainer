import streamlit as st
from google import genai
import asyncio
import edge_tts
import os
import tempfile
import re
import cv2

st.set_page_config(page_title="AI Safe Dialogue Dubbing (MP3)", layout="centered")

st.title("🎬 AI Safe Dialogue Dubbing (MP3 Output)")
st.write("បកប្រែចំឃ្លាតួអង្គ **ត្រូវម៉ោងវីដេអូ និងထုတ်ជា File សំឡេង MP3** សម្រាប់យកទៅប្រើប្រាស់ដោយសុវត្ថិភាព (គ្មាន Error)!")

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

if uploaded_file is not None:
    st.video(uploaded_file)

if st.button("ចាប់ផ្តើមបកប្រែ និងទាញយកសំឡេង MP3 🚀"):
    if not api_key:
        st.error("សូមបញ្ចូល Gemini API Key ជាមុនសិន!")
    elif uploaded_file is None:
        st.warning("សូម Upload វីដេអូជាមុនសិន!")
    else:
        with st.spinner("កំពុងវិភាគវីដេអូ និងបង្កើតសំឡេង MP3..."):
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
                    
                    st.subheader("📝 អត្ថបទបកប្រែចំប្រយោគតួអង្គ (មាន Timecode):")
                    st.text_area("Copy Text ទីនេះ:", raw_text, height=200)
                    
                    # លុប Timecode និងការពិពណ៌នាចេញ មុនយកទៅធ្វើ Audio
                    clean_text = clean_text_for_tts(raw_text)
                    
                    st.info(f"កំពុងបង្កើតសំឡេងអាន MP3 ({voice_choice})...")
                    
                    # បង្កើត Temp File សម្រាប់ Audio
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as audio_tf:
                        audio_path = audio_tf.name

                    # 1. បង្កើតសំឡេង MP3 ជាមួយ edge-tts
                    asyncio.run(generate_edge_tts(clean_text, selected_voice, audio_path))
                    
                    st.success("🎉 ការបង្កើតសំឡេង MP3 បានសម្រេចជោគជ័យ!")
                    
                    # ຫຼິ້ນសំឡេងស្តាប់សាកល្បង
                    st.subheader("🔊 សំឡេងអាន MP3:")
                    st.audio(audio_path)
                    
                    # ប៊ូតុង Download File MP3
                    with open(audio_path, "rb") as file:
                        st.download_button(
                            label="📥 ទាញយកសំឡេង MP3 (Download Audio)",
                            data=file,
                            file_name="dubbed_audio.mp3",
                            mime="audio/mpeg"
                        )
                
                # លុប File Temp ចោលវិញ
                for p in [video_path, audio_path]:
                    if os.path.exists(p):
                        os.remove(p)
                
            except Exception as e:
                st.error(f"មានបញ្ហាកើតឡើង: {e}")
                
