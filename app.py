import streamlit as st
from google import genai
import asyncio
import edge_tts
import os
import tempfile

st.set_page_config(page_title="AI Movie Subtitle & Dubbing Pro", page_icon="🎬")

# ផ្នែកកំណត់ការ Settings (Sidebar ធម្មតា)
with st.sidebar:
    st.header("⚙️ ការកំណត់ (Settings)")
    api_key = st.text_input("បញ្ចូល Google Gemini API Key:", type="password")
    
    voice_option = st.selectbox(
        "ជ្រើសរើសសំឡេង Dubbing:",
        ("Sreymom (ស្រី - ធម្មជាតិ)", "Piseth (ប្រុស - ធម្មជាតិ)")
    )
    
    if "Sreymom" in voice_option:
        selected_voice = "km-KH-SreymomNeural"
    else:
        selected_voice = "km-KH-PisethNeural"

# បង្ហាញរូបថតផ្ទាល់ខ្លួនរបស់បងចំកណ្តាលអេក្រង់តែម្តង
if os.path.exists("profile.jpg"):
    st.image("profile.jpg", caption="Admin App Profile", use_container_width=True)

st.title("🎬 AI Movie Subtitle & Dubbing Pro")
st.write("បកប្រែវីដេអូជា Subtitle ខ្មែរ និងបង្កើតសំឡេង Dubbing ធម្មជាតិពិោះៗ (ប្រុស/ស្រី) ដូចមនុស្សពិត!")

uploaded_file = st.file_uploader("ជ្រើសរើសវីដេអូ (MP4, MOV, AVI):", type=["mp4", "mov", "avi"])

async def generate_audio(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

if st.button("🚀 ចាប់ផ្តើមដំណើរការបកប្រែ និងបង្កើតសំឡេង"):
    if not api_key:
        st.error("សូមបញ្ចូល Google Gemini API Key នៅកន្លែង Settings ខាងឆ្វេងជាមុនសិន!")
    elif uploaded_file is not None:
        try:
            client = genai.Client(api_key=api_key)
            
            with st.spinner("កំពុងដំណើរការវីដេអូ និងបកប្រែជាសាច់រឿងសន្ទនាបន្តគ្នា..."):
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tfile.write(uploaded_file.read())
                video_path = tfile.name

                video_file = client.files.upload(file=video_path)
                
                prompt = (
                    "Listen closely to the video and write out the full dialogue and conversation story in natural Khmer. "
                    "CRITICAL INSTRUCTIONS: "
                    "1. Present it as a smooth, continuous dialogue script where characters speak back and forth naturally. "
                    "2. Do NOT include any timestamps, time markers, brackets, or code symbols. "
                    "3. Make sure the narrative flows seamlessly from one character's speech to the next in proper story sequence."
                )
                
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=[video_file, prompt]
                )
                
                translated_text = response.text

            st.success("បកប្រែសាច់រឿងសន្ទនាបានជោគជ័យ!")
            
            st.subheader("📝 អត្ថបទសាច់រឿងសន្ទនា (សម្រាប់ Copy ដាក់ CapCut):")
            st.info(translated_text)

            with st.spinner("កំពុងបង្កើតសំឡេង Dubbing តាមសាច់រឿង..."):
                audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                asyncio.run(generate_audio(translated_text, selected_voice, audio_path))

            st.subheader("🔊 សំឡេង Dubbing ខ្មែរ (AI Voice):")
            st.audio(audio_path)

        except Exception as e:
            st.error(f"មានបញ្ហាកើតឡើង: {e}")
    else:
        st.warning("សូម Upload វីដេអូមុននឹងចាប់ផ្តើម!")
    
