import streamlit as st
from google import genai
import asyncio
import edge_tts
import os
import tempfile

st.set_page_config(page_title="AI Movie Subtitle & Dubbing Pro", page_icon="🎬")

st.title("🎬 AI Movie Subtitle & Dubbing Pro")
st.write("បកប្រែវីដេអូជា Subtitle ខ្មែរ និងបង្កើតសំឡេង Dubbing ធម្មជាតិពិោះៗ (ប្រុស/ស្រី) ដូចមនុស្សពិត!")

# ផ្នែកកំណត់ការ Settings (Sidebar)
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
            
            with st.spinner("កំពុងដំណើរការវីដេអូ និងទាញយកសាច់រឿងសុទ្ធ..."):
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tfile.write(uploaded_file.read())
                video_path = tfile.name

                video_file = client.files.upload(file=video_path)
                
                # Prompt ថ្មីដែលហាមដាច់ខាតមិនឱ្យដាក់ Timestamp, ឈ្មោះតួអង្គ ឬសញ្ញាខ្វែង គឺយកតែអត្ថបទសាច់រឿងរលូនៗសុទ្ធសាធ
                prompt = (
                    "Listen to the dialogue and narration in this video and write down a smooth, continuous story in natural Khmer. "
                    "CRITICAL INSTRUCTIONS: "
                    "1. Do NOT include any timestamps (like [01:31 - 01:40] or similar time markers). "
                    "2. Do NOT include character names, tags, bullet points, or brackets. "
                    "3. Provide ONLY the pure narrative text or storyline prose in fluent Khmer sentences so it reads like a continuous story script."
                )
                
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=[video_file, prompt]
                )
                
                translated_text = response.text

            st.success("បកប្រែសាច់រឿងបានជោគជ័យ!")
            
            st.subheader("📝 អត្ថបទសាច់រឿងសុទ្ធសាធ (សម្រាប់ Copy ដាក់ CapCut):")
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
            
