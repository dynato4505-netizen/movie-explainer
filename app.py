import streamlit as st
from google import genai
import asyncio
import edge_tts
import os
import tempfile
import re
import cv2  # សម្រាប់ទាញយករយៈពេលវីដេអូ

st.set_page_config(page_title="AI Precise Time Dialogue Dubbing", layout="centered")

st.title("🎬 AI Precise Time Dialogue Dubbing")
st.write("បកប្រែចំឃ្លាតួអង្គសុទ្ធសាធ ដោយ **ទប់ទំហំអត្ថបទមិនឱ្យវែងលើសរយៈពេលវីដេអូដើម** (៣នាទីវីដេអូ = ៣នាទីសំឡេង)!")

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

if st.button("ចាប់ផ្តើមបកប្រែចំឃ្លា (រក្សាទំហំសមាមាត្រវីដេអូ) 🚀"):
    if not api_key:
        st.error("សូមបញ្ចូល Gemini API Key ជាមុនសិន!")
    elif uploaded_file is None:
        st.warning("សូម Upload វីដេអូជាមុនសិន!")
    else:
        with st.spinner("កំពុងវិភាគវីដេអូ និងកំណត់ប្រវែងពាក្យឱ្យត្រូវម៉ោង..."):
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
                    # មនុស្សធម្មតាអានប្រហែល ២.២ ទៅ ២.៥ ពាក្យក្នុង១វិនាទី
                    # ដូច្នេះចំនួនពាក្យអតិបរមាត្រូវស្មើនឹង duration_sec * 2.3
                    max_words = int(duration_sec * 2.3)
                    
                    st.info(f"⏱️ រយៈពេលវីដេអូពិតប្រាកដ: {duration_sec/60:.2f} នាទី ({duration_sec:.1f} វិនាទី) | កំណត់ពាក្យអតិបរមា: ~{max_words} ពាក្យ")

                    client = genai.Client(api_key=api_key)
                    st.info("កំពុងបញ្ជូនវីដេអូទៅកាន់ Gemini AI...")
                    
                    video_file = client.files.upload(file=video_path)

                    # Prompt កែសម្រួលថ្មី៖ បង្ខំទំហំអត្ថបទមិនឱ្យវែងលើសម៉ោងវីដេអូ និងយកតែប្រយោគតួអង្គនិយាយ
                    prompt = (
                        "អ្នកគឺជាអ្នកបកប្រែប្រយោគតួអង្គភាពយន្តអាជីព។ "
                        "សូមទស្សនាវីដេអូនេះ រួចបកប្រែ **เฉพาะ ឃ្លាប្រយោគដែលតួអង្គនិយាយផ្ទាល់** ជាភាសាខ្មែរ។ "
                        "**លក្ខខណ្ឌតឹងរឹងបំផុតដើម្បីការពារកុំឱ្យអត្ថបទវែងជ្រុល៖** "
                        "1. អត្ថបទសរុបត្រូវមានប្រវែងសមល្មម **មិនឱ្យលើសពីប្រហែល " + str(max_words) + " ពាក្យឡើយ** ដើម្បីឱ្យពេលយកទៅអាន គឺត្រូវគ្នាបេះបិទទៅនឹងរយៈពេលវីដេអូ " + f"{duration_sec:.1f}" + " វិនាទី (៣នាទីវីដេអូ ត្រូវតែចប់ក្នុង៣នាទី ហាមអូសបន្លាយវែងហួសហេតុ)។ "
                        "2. ហាមសរសេររបៀបសម្រាយរឿង និងហាមពិពណ៌នាឈុតឆាកក្នុងវង់ក្រចកណាមួយទាំងអស់ (Pure Dialogue Only)។ "
                        "3. រក្សាកូដពេលវេលា [MM:SS - MM:SS] ទុកនៅខាងមុខប្រយោគនីមួយៗ។"
                    )
                    
                    response = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=[video_file, prompt],
                    )
                    
                    raw_text = response.text
                    
                    # បង្ហាញអត្ថបទបកប្រែចំឃ្លា
                    st.subheader("📝 អត្ថបទបកប្រែចំប្រយោគតួអង្គ (គ្រប់គ្រងប្រវែងរួចរាល់):")
                    st.text_area("Copy Text ទីនេះ:", raw_text, height=250)
                    
                    # លុប Timecode និងការពិពណ៌នាចេញ មុនយកទៅធ្វើ Audio
                    clean_text = clean_text_for_tts(raw_text)
                    
                    st.info(f"កំពុងបង្កើតសំឡេងអានដែលមានប្រវែងត្រូវគ្នានឹងវីដេអូ ({voice_choice})...")
                    
                    # បង្កើត Temp File សម្រាប់ Audio
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as audio_tf:
                        audio_path = audio_tf.name

                    # Run edge-tts ជាមួយអត្ថបទដែលបានទប់ទំហំ
                    asyncio.run(generate_edge_tts(clean_text, selected_voice, audio_path))
                    
                    st.subheader("🔊 សំឡេងអានប្រយោគតួអង្គ (ត្រូវម៉ោងជាមួយវីដេអូ):")
                    st.audio(audio_path)
                
                # លុប Video File ចོលវិញកុំឱ្យស្ទះម៉ាស៊ីន
                if os.path.exists(video_path):
                    os.remove(video_path)
                
            except Exception as e:
                st.error(f"មានបញ្ហាកើតឡើង: {e}")
                
