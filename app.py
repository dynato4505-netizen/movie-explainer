import streamlit as st
from google import genai
import asyncio
import edge_tts
import os
import tempfile
import cv2  # សម្រាប់គណនារយៈពេលវីដេអូ

st.set_page_config(page_title="AI Movie Explainer & Dubbing Pro", layout="centered")

st.title("🎬 AI Movie Explainer & Dubbing Pro")
st.write("ប្រព័ន្ធបកប្រែ និងបង្កើតសំឡេងអានរឿងកម្រិតខ្ពស់ ស្ដាប់ទៅដូចមនុស្សពិត ដើរស្មើនឹងវីដេអូដើម!")

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

uploaded_file = st.file_uploader("ជ្រើសរើសវីដេអូខ្លី (MP4, MOV):", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    st.video(uploaded_file)

# Function សម្រាប់ទាញយករយៈពេលវីដេអូជាវិនាទី
def get_video_duration(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    if fps > 0:
        return frame_count / fps
    return 0

# Function សម្រាប់ generate សំឡេងជាមួយ edge-tts
async def generate_edge_tts(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

if st.button("ចាប់ផ្តើមបកប្រែ និងបង្កើតសំឡេងគុណភាពខ្ពស់ 🚀"):
    if not api_key:
        st.error("សូមបញ្ចូល Gemini API Key ជាមុនសិន!")
    elif uploaded_file is None:
        st.warning("សូម Upload វីដេអូជាមុនសិន!")
    else:
        with st.spinner("កំពុងវិភាគសាច់រឿង និងបកប្រែដោយយកចិត្តទុកដាក់លើគុណភាព..."):
            try:
                # បង្កើត Temp File សម្រាប់វីដេអូ
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tfile.write(uploaded_file.read())
                video_path = tfile.name

                # គណនារយៈពេលវីដេអូជាវិនាទី
                duration_sec = get_video_duration(video_path)
                st.info(f"⏱️ រយៈពេលវីដេអូដើម: {duration_sec:.1f} វិនាទី")

                # ល្បឿនអានស្តង់ដាររបស់មនុស្សប្រហែល ២.៣ ដល់ ២.៥ ពាក្យក្នុង១វិនាទី เพื่อให้ស្មើវីដេអូ និងមិនប្រញាប់ពេក
                target_words = int(duration_sec * 2.3)

                client = genai.Client(api_key=api_key)

                st.info("កំពុងបញ្ជូនវីដេអូទៅកាន់ Gemini AI...")
                video_file = client.files.upload(file=video_path)

                # Prompt កម្រិត Pro ដើម្បីរក្សាគុណភាពខ្ពស់ មិនរ៉ូប៊ត មិនខ្លីហួសហេតុ និងត្រូវរយៈពេលវីដេអូ
                prompt = (
                    "អ្នកគឺជាអ្នកនិពន្ធ និងអ្នកបកប្រែស្គ្រីបភាពយន្តអាជីព។ "
                    f"សូមទស្សនារូបភាព និងស្ដាប់សំឡេងក្នុងវីដេអូនេះ រួចបកប្រែ និងច្នៃសាច់រឿងជាភាសាខ្មែរក្នុងទម្រង់ជាស្គ្រីបអានរឿង (Voiceover) "
                    "ដែលមានអត្ថន័យស៊ីជម្រៅ ពីរោះរលូន ស្ដាប់ទៅធម្មជាតិដូចមនុស្សពិតเล่าរឿង មិនមែនបកប្រែចំៗបែបមនុស្សយន្តទេ។ "
                    f"**លក្ខខណ្ឌកំណត់ប្រវែង៖** អត្ថបទសរុបត្រូវមានចំនួនប្រហែល {target_words} ពាក្យ (ដើម្បីឱ្យសមាមាត្រស្របគ្នាបេះបិទទៅនឹងរយៈពេលវីដេអូ {duration_sec:.1f} វិនាទី មិនខ្លីពេក និងមិនវែងពេក)។ "
                    "**ចំណាំដាច់ខាត៖** ហាមដាក់លេខកូដម៉ោង ពេលវេលា (00:00) ឬសញ្ញា Timecode ណាមួយឡើយ! "
                    "សូមផ្ដល់ត្រឹមតែអត្ថបទសាច់រឿងសុទ្ធសាធដែលមានការដកឃ្លា ឬដាក់សញ្ញាក្បៀស (,) ត្រឹមត្រូវដើម្បីឱ្យចង្វាក់អានមានដង្ហើមធម្មជាតិ។"
                )
                
                response = client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=[video_file, prompt],
                )
                
                sub_text = response.text
                
                st.subheader("📝 សាច់រឿង (ស្គ្រីបគុណភាពខ្ពស់):")
                st.text_area("Copy Text ទីនេះ:", sub_text, height=200)
                
                st.info(f"កំពុងបង្កើតសំឡេងអានកម្រិតធម្មជាតិ ({voice_choice})...")
                
                # បង្កើត Temp File សម្រាប់ Audio
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as audio_tf:
                    audio_path = audio_tf.name

                # Run edge-tts
                asyncio.run(generate_edge_tts(sub_text, selected_voice, audio_path))
                
                st.subheader("🔊 សំឡេងអានសាច់រឿង (Audio Dubbing):")
                st.audio(audio_path)
                
                # លុប Video File ចោលវិញកុំឱ្យស្ទះម៉ាស៊ីន
                if os.path.exists(video_path):
                    os.remove(video_path)
                
            except Exception as e:
                st.error(f"មានបញ្ហាកើតឡើង: {e}")
