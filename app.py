import streamlit as st
from google import genai
import asyncio
import edge_tts
import tempfile
import os

st.set_page_config(page_title="AI Movie Subtitle & Dubbing Pro", page_icon="🎬")

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

st.title("🎬 AI Movie Subtitle & Dubbing Pro")
st.write("បកប្រែវីដេអូពេញលេញជា Subtitle ខ្មែរ និងបង្កើតសំឡេង Dubbing ត្រូវសាច់រឿងពីដើមដល់ចប់ដោយរលូន!")

uploaded_file = st.file_uploader("ជ្រើសរើសវីដេអូ (MP4, MOV, AVI):", type=["mp4", "mov", "avi"])

async def generate_long_audio(text, voice, output_path):
    max_chars = 3000
    text_chunks = [text[i:i+max_chars] for i in range(0, len(text), max_chars)]
    
    temp_files = []
    for idx, chunk in enumerate(text_chunks):
        chunk_path = tempfile.NamedTemporaryFile(delete=False, suffix=f'_part{idx}.mp3').name
        communicate = edge_tts.Communicate(chunk, voice)
        await communicate.save(chunk_path)
        temp_files.append(chunk_path)
    
    with open(output_path, 'wb') as outfile:
        for f_path in temp_files:
            with open(f_path, 'rb') as infile:
                outfile.write(infile.read())
            os.remove(f_path)

if st.button("🚀 ចាប់ផ្តើមដំណើរការបកប្រែ និងបង្កើតសំឡេង"):
    if not api_key:
        st.error("សូមបញ្ចូល Google Gemini API Key នៅកន្លែង Settings ខាងឆ្វេងជាមុនសិន!")
    elif uploaded_file is not None:
        try:
            client = genai.Client(api_key=api_key)
            
            with st.spinner("កំពុងបកប្រែសាច់រឿងពេញលេញគ្រប់វិនាទីពីវីដេអូ... (សូមរង់ចាំបន្តិច)"):
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tfile.write(uploaded_file.read())
                video_path = tfile.name

                video_file = client.files.upload(file=video_path)
                
                # Prompt នេះបង្គាប់ឱ្យបកប្រែពេញលេញគ្រប់សកម្មភាព និងសន្ទនា មិនមែនជាការសម្រាយរឿងខ្លីទេ
                prompt = (
                    "Listen and translate the full video from start to finish into natural Khmer. "
                    "Do NOT summarize, do NOT recap, and do NOT cut short. Translate every conversation, event, and detail thoroughly "
                    "so that the narrative covers the entire 14-minute runtime sequence naturally. "
                    "CRITICAL INSTRUCTIONS: "
                    "1. Present it as a smooth, continuous script covering all events from beginning to the end. "
                    "2. Do NOT include any timestamps, time markers, brackets, or code symbols."
                )
                
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=[video_file, prompt]
                )
                
                translated_text = response.text

            st.success("បកប្រែសាច់រឿងពេញលេញបានជោគជ័យ!")
            
            st.subheader("📝 អត្ថបទសាច់រឿងពេញលេញ (សម្រាប់ Copy ដាក់ CapCut):")
            st.info(translated_text)

            with st.spinner("កំពុងបង្កើតសំឡេង Dubbing ខ្មែរពេញលេញ..."):
                audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                asyncio.run(generate_long_audio(translated_text, selected_voice, audio_path))

            st.subheader("🔊 សំឡេង Dubbing ខ្មែរពេញលេញ (AI Voice):")
            st.audio(audio_path)

        except Exception as e:
            st.error(f"មានបញ្ហាកើតឡើង: {e}")
    else:
        st.warning("សូម Upload វីដេអូមុននឹងចាប់ផ្តើម!")
                                                    
