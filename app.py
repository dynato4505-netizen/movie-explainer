import streamlit as st
from google import genai
import asyncio
import edge_tts
import os
import tempfile
import cv2  # សម្រាប់ទាញយករយៈពេលវីដេអូ

st.set_page_config(page_title="AI Movie Explainer & Dubbing Pro")

st.title("🎬 AI Movie Explainer & Dubbing Pro")
st.write("បកប្រែសាច់រឿង និងបង្កើតសំឡេងអានឱ្យដើរស្មើគ្នាបេះបិទនឹងរយៈពេលវីដេអូដើម!")

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

uploaded_file = st.file_uploader("ជ្រើសរើសវីដេអូ (MP4, MOV):", type=["mp4", "mov", "avi"])

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

if st.button("ចាប់ផ្តើមបកប្រែ និងបង្កើតសំឡេងស្មើវីដេអូ 🚀"):
    if not api_key:
        st.error("សូមបញ្ចូល Gemini API Key ជាមុនសិន!")
    elif uploaded_file is None:
        st.warning("សូម Upload វីដេអូជាមុនសិន!")
    else:
        with st.spinner("កំពុងគណនារយៈពេលវីដេអូ និងបកប្រែសាច់រឿង..."):
            try:
                # បង្កើត Temp File សម្រាប់វីដេអូ
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tfile.write(uploaded_file.read())
                video_path = tfile.name

                # គណនារយៈពេលវីដេអូជាវិនាទី
                duration_sec = get_video_duration(video_path)
                st.info(f"⏱️ រយៈពេលវីដេអូដើម: {duration_sec:.1f} វិនាទី")

                # គណនាចំនួនពាក្យប៉ាន់ស្មայն (មនុស្សធម្មតាអានប្រហែល ២.៥ ទៅ ៣ពាក្យក្នុង១វិនាទី)
                target_words = int(duration_sec * 2.5)

                client = genai.Client(api_key=api_key)

                st.info("កំពុងបញ្ជូនវីដេអូទៅកាន់ Gemini AI...")
                video_file = client.files.upload(file=video_path)

                # Prompt បញ្ជា AI ឱ្យសរសេរអត្ថបទឱ្យត្រូវចំនួនពាក្យ និងសមាមាត្រនឹងវិនាទីវីដេអូ
                prompt = (
                    f"សូមទស្សនាវីដេអូនោះ រួចសរសេរបកប្រែសាច់រឿងជាភាសាខ្មែរក្នុងទម្រង់ជាស្គ្រីបអានរឿង (Voiceover)។ "
                    f"**លក្ខខណ្ឌតឹងរឹង៖** អត្ថបទសរុបត្រូវតែមានប្រវែងប្រហែល {target_words} ពាក្យប៉ុណ្ណោះ "
                    f"(ព្រោះវីដេអូមានរយៈពេលត្រឹមតែ {duration_sec:.1f} វិនាទី ដើម្បីពេលយកទៅអានទៅគឺដើរស្មើគ្នាច្បាស់លាស់ មិនខ្លីពេក មិនវែងពេក)។ "
                    "និយាយចំសាច់រឿងសំខាន់ៗ ពីរោះរលូន ធម្មជាតិ។ "
                    "**ហាមដាច់ខាត៖** ដាក់លេខកូដម៉ោង ពេលវេលា (00:00) ឬសញ្ញា Timecode ណាមួយឡើយ!"
                )
                
                response = client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=[video_file, prompt],
                )
                
                sub_text = response.text
                
                st.subheader("📝 សាច់រឿង (ស្គ្រីបត្រូវតាមរយៈពេលវីដេអូ):")
                st.text_area("Copy Text ទីនេះ:", sub_text, height=150)
                
                st.info(f"កំពុងបង្កើតសំឡេងអាន ({voice_choice})...")
                
                # បង្កើត Temp File សម្រាប់ Audio
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as audio_tf:
                    audio_path = audio_tf.name

                # Run edge-tts
                asyncio.run(generate_edge_tts(sub_text, selected_voice, audio_path))
                
                st.subheader("🔊 សំឡេងអានសាច់រឿង (Audio Dubbing):")
                st.audio(audio_path)
                
                # លុប Video File ចོលវិញកុំឱ្យស្ទះម៉ាស៊ីន
                if os.path.exists(video_path):
                    os.remove(video_path)
                
            except Exception as e:
                st.error(f"មានបញ្ហាកើតឡើង: {e}")
                
