import streamlit as st
from google import genai
import asyncio
import edge_tts
import os
import tempfile

st.set_page_config(page_title="AI Movie Explainer & Dubbing Pro")

st.title("🎬 AI Movie Explainer & Dubbing Pro")
st.write("បកប្រែសាច់រឿងវីដេអូជាសំឡេងរៀបរាប់ធម្មជាតិ (Voiceover) ជាមួយសំឡេងស្រី/ប្រុស និង Subtitle ស្អាតៗ!")

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

# Function សម្រាប់ generate សំឡេងជាមួយ edge-tts
async def generate_edge_tts(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

if st.button("ចាប់ផ្តើមបកប្រែ និងបង្កើតសំឡេងរឿង 🚀"):
    if not api_key:
        st.error("សូមបញ្ចូល Gemini API Key ជាមុនសិន!")
    elif uploaded_file is None:
        st.warning("សូម Upload វីដេអូជាមុនសិន!")
    else:
        with st.spinner("កំពុងវិភាគវីដេអូ និងច្នៃសាច់រឿងឱ្យដូចមនុស្សនិយាយធម្មជាតិ..."):
            try:
                # បង្កើត Temp File សម្រាប់វីដេអូ
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tfile.write(uploaded_file.read())
                video_path = tfile.name

                client = genai.Client(api_key=api_key)

                st.info("កំពុងបញ្ជូនវីដេអូទៅកាន់ Gemini AI...")
                video_file = client.files.upload(file=video_path)

                # Prompt កែច្នៃថ្មី ដើម្បីឱ្យអត្ថបទអានស្ដាប់ទៅដូចមនុស្សពិត និងលុបលេខ 00:00 ចោលដាច់ខាត
                prompt = (
                    "សូមទស្សនាវីដេអូនេះ រួចសរសេរបកប្រែ និងច្នៃសាច់រឿងជាភាសាខ្មែរក្នុងទម្រង់ជាស្គ្រីបសម្រាប់អានរឿង (Voiceover script) "
                    "ដែលមានលក្ខណៈរលូន ទន់ភ្លន់ ដូចមនុស្សពិតកំពុងនិយាយเล่าរឿងប្រាប់គេ មិនមែនបកប្រែចំៗបែបមនុស្សយន្តទេ។ "
                    "**ចំណាំសំខាន់៖** ហាមដាក់ដាច់ខាតនូវលេខកូដម៉ោង ពេលវេលា (ឧទាហរណ៍ 00:00) ឬសញ្ញាចែក Timecode ណាមួយឡើយ! "
                    "សូមផ្ដល់តែអត្ថបទសាច់រឿងសុទ្ធសាធ តភ្ជាប់គ្នាពីរោះៗ ងាយស្រួលយកទៅប្រើជាមួយកម្មវិធីអានសំឡេង។"
                )
                
                response = client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=[video_file, prompt],
                )
                
                sub_text = response.text
                
                st.subheader("📝 សាច់រឿង (ស្គ្រីបសម្រាប់អាន):")
                st.text_area("Copy Text ទីនេះ:", sub_text, height=200)
                
                st.info(f"កំពុងបង្កើតសំឡេងអានរឿងធម្មជាតិ ({voice_choice})...")
                
                # បង្កើត Temp File សម្រាប់ Audio
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as audio_tf:
                    audio_path = audio_tf.name

                # Run edge-tts
                asyncio.run(generate_edge_tts(sub_text, selected_voice, audio_path))
                
                st.subheader("🔊 សំឡេងអានសាច់រឿងធម្មជាតិ (Audio Dubbing):")
                st.audio(audio_path)
                
                # លុប Video File ចោលវិញកុំឱ្យស្ទះម៉ាស៊ីន
                if os.path.exists(video_path):
                    os.remove(video_path)
                
            except Exception as e:
                st.error(f"មានបញ្ហាកើតឡើង: {e}")
    
