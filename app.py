import streamlit as st
from google import genai
import asyncio
import edge_tts
import os
import tempfile

st.set_page_config(page_title="Movie Subtitle & Dubbing App")

st.title("🎬 AI Movie Subtitle & Dubbing Pro")
st.write("Upload វីដេអូខ្លី ដើម្បីឱ្យ AI បកប្រែជា Subtitle ខ្មែរ និងបង្កើតសំឡេង Dubbing (ស្រី/ប្រុស)!")

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

# Function សម្រាប់ generate សំឡេងជាមួយ edge-tts asynchronously
async def generate_edge_tts(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

if st.button("ចាប់ផ្តើមបកប្រែ Subtitle និងសំឡេង 🚀"):
    if not api_key:
        st.error("សូមបញ្ចូល Gemini API Key ជាមុនសិន!")
    elif uploaded_file is None:
        st.warning("សូម Upload វីដេអូជាមុនសិន!")
    else:
        with st.spinner("កំពុងវិភាគវីដេអូ និងបង្កើត Subtitle ខ្មែរ..."):
            try:
                # បង្កើត Temp File សម្រាប់វីដេអូ
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tfile.write(uploaded_file.read())
                video_path = tfile.name

                client = genai.Client(api_key=api_key)

                st.info("កំពុងបញ្ជូនវីដេអូទៅកាន់ Gemini AI...")
                video_file = client.files.upload(file=video_path)

                prompt = "សូមទស្សនាវីដេអូនេះ ស្ដាប់សំឡេង និងសរសេរបកប្រែសាច់រឿងជាភាសាខ្មែរ ចែកចេញជាឃ្លាៗ (Subtitle) សម្រាប់យកទៅដាក់ក្នុង CapCut។"
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[video_file, prompt],
                )
                
                sub_text = response.text
                st.subheader("📝 អត្ថបទ Subtitle ភាសាខ្មែរ (សម្រាប់ Copy ដាក់ CapCut):")
                st.text_area("Copy Subtitle ទីនេះ:", sub_text, height=200)
                
                st.info(f"កំពុងបង្កើតសំឡេង Dubbing ({voice_choice})...")
                
                # បង្កើត Temp File សម្រាប់ Audio
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as audio_tf:
                    audio_path = audio_tf.name

                # Run edge-tts
                asyncio.run(generate_edge_tts(sub_text, selected_voice, audio_path))
                
                st.subheader("🔊 សំឡេងអានខ្មែរ (Audio Dubbing):")
                st.audio(audio_path)
                
                # លុប Video File ចោលវិញកុំឱ្យស្ទះម៉ាស៊ីន
                if os.path.exists(video_path):
                    os.remove(video_path)
                
            except Exception as e:
                st.error(f"មានបញ្ហាកើតឡើង: {e}")
                
