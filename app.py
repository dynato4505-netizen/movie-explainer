import streamlit as st
from google import genai
import asyncio
import edge_tts
import os
import tempfile
import re
import cv2  # សម្រាប់ទាញយករយៈពេលវីដេអូ

st.set_page_config(page_title="AI Human-like Dubbing Pro", layout="centered")

st.title("🎬 AI Human-like Voice Dubbing Pro")
st.write("ប្រព័ន្ធបកប្រែ සහ បង្កើតសំឡេងអាន **ដូចមនុស្សពិត ពីរោះ មានទឹកដម និងចង្វាក់ធម្មជាតិ!**")

api_key = st.text_input("បញ្ចូល Gemini API Key របស់អ្នក:", type="password")

# ជម្រើសសំឡេងប្រុស ឬស្រី (បន្ថែមការណែនាំពីភាពធម្មជាតិ)
voice_choice = st.selectbox(
    "ជ្រើសរើសសំឡេង Dubbing:",
    ("ស្រី (Sreymom - ស្រទន់ពីរោះ)", "ប្រុស (Piseth - ច្បាស់អ៊ុតធម្មជាតិ)")
)

voice_map = {
    "ស្រី (Sreymom - ស្រទន់ពីរោះ)": "km-KH-SreymomNeural",
    "ប្រុស (Piseth - ច្បាស់អ៊ុតធម្មជាតិ)": "km-KH-PisethNeural"
}
selected_voice = voice_map[voice_choice]

uploaded_file = st.file_uploader("ជ្រើសរើសវីដេអូខ្លី (MP4, MOV - ក្រោម ១៥នាទី):", type=["mp4", "mov", "avi"])

# Function សម្រាប់ទាញយករយៈពេលវីដេអូជាវិនាទី
def get_video_duration(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    if fps > 0:
        return frame_count / fps
    return 0

# Function សម្រាប់លុប Timecode ចេញពីអត្ថបទមុននឹងយកទៅបង្កើត Audio
def clean_text_for_tts(text):
    # លុបគំរូ [00:00 - 00:05] ឬ 00:00 ออกจากអត្ថបទ
    cleaned = re.sub(r'\[\d{2}:\d{2}\s*-\s*\d{2}:\d{2}\]|\d{2}:\d{2}', '', text)
    # បន្ថែមការរៀបចំសញ្ញាក្បៀស ដើម្បីឱ្យ TTS ចេះដកចង្អោរ
    cleaned = cleaned.replace('\n', ' ')
    return cleaned.strip()

# Function សម្រាប់ generate សំឡេងជាមួយ edge-tts
async def generate_edge_tts(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

if uploaded_file is not None:
    st.video(uploaded_file)

if st.button("ចាប់ផ្តើមបង្កើតសំឡេងមនុស្សពិត 🚀"):
    if not api_key:
        st.error("សូមបញ្ចូល Gemini API Key ជាមុនសិន!")
    elif uploaded_file is None:
        st.warning("សូម Upload វីដេអូជាមុនសិន!")
    else:
        with st.spinner("កំពុងរៀបចំស្គ្រីប និងកែច្នៃសំឡេងឱ្យដូចមនុស្សពិត..."):
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
                    client = genai.Client(api_key=api_key)

                    st.info("កំពុងបញ្ជូនវីដេអូទៅកាន់ Gemini AI...")
                    video_file = client.files.upload(file=video_path)

                    # Prompt កម្រិតខ្ពស់បំផុត៖ បង្ខំឱ្យ AI សរសេរអត្ថបទបែប Voiceover ដាក់អារម្មណ៍ ចង្វាក់ដកដង្ហើម
                    prompt = (
                        "អ្នកគឺជាអ្នកអានសាច់រឿង និងជា Voiceover Talent អាជីព។ "
                        "សូមទស្សនាវីដេអូនេះ ហើយបកប្រែចំឃ្លា ឬអត្ថន័យសាច់រឿងជាភាសាខ្មែរ ដោយ **សរសេរក្នុងទម្រង់ជាសំឡេងនិយាយផ្ទាល់ (Spoken Style) ដែលមានជីវិតរស់រវើក ដាក់អារម្មណ៍រំភើប ស្រទន់ ឬអន្លង់អន្លោចតាមឈុតឆាក**។ "
                        "**លក្ខខណ្ឌសំខាន់ខ្លាំង៖** "
                        "1. ត្រូវចេះដាក់សញ្ញាក្បៀស (,) សញ្ញាអន្តរាគមន៍ (!) ឬដកឃ្លាឱ្យបានញឹកញាប់ ដើម្បីពេលយកទៅអាន សំឡេងនឹងចេះដកចង្អោរ និងមានចង្វាក់ចុះឡើង (Intonation) ដូចមនុស្សពិតនិយាយគ្នា មិនមែនអានស្រុញៗរ៉ូប៊តទេ។ "
                        "2. ដាក់កូដពេលវេលា [MM:SS - MM:SS] ទុកនៅខាងមុខសម្រាប់ងាយស្រួលផ្ទៀងផ្ទាត់។ "
                        "3. ហាមប្រើពាក្យសរសេរបែបសៀវភៅ ឬវេយ្យាករណ៍រឹងៗ។"
                    )
                    
                    response = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=[video_file, prompt],
                    )
                    
                    raw_text = response.text
                    
                    # បង្ហាញអត្ថបទដែលមានម៉ោងសម្រាប់មើលផ្ទៀងផ្ទាត់
                    st.subheader("📝 ស្គ្រីបសម្រាប់អាន (មានដាក់ចង្វាក់អារម្មណ៍):")
                    st.text_area("Copy Text ទីនេះ:", raw_text, height=200)
                    
                    # លុបលេខកូដម៉ោងចេញ ដើម្បីយកទៅធ្វើ Audio ឱ្យស្អាត
                    clean_text = clean_text_for_tts(raw_text)
                    
                    st.info(f"កំពុងបង្កើតសំឡេងអានទឹកដមដូចមនុស្សពិត ({voice_choice})...")
                    
                    # បង្កើត Temp File សម្រាប់ Audio
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as audio_tf:
                        audio_path = audio_tf.name

                    # Run edge-tts ជាមួយអត្ថបទស្គ្រីបធម្មជាតិ
                    asyncio.run(generate_edge_tts(clean_text, selected_voice, audio_path))
                    
                    st.subheader("🔊 សំឡេងអានធម្មជាតិ (ដូចមនុស្សពិត):")
                    st.audio(audio_path)
                
                # លុប Video File ចོលវិញកុំឱ្យស្ទះម៉ាស៊ីន
                if os.path.exists(video_path):
                    os.remove(video_path)
                
            except Exception as e:
                st.error(f"មានបញ្ហាកើតឡើង: {e}")
                    
