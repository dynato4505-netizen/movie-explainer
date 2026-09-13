import streamlit as st
from google import genai
import asyncio
import edge_tts
import os
import tempfile

st.set_page_config(page_title="Movie Subtitle & Dubbing Pro App", page_icon="🎬", layout="centered")

st.title("🎬 AI Movie Subtitle & Dubbing Pro")
st.write("បកប្រែវីដេអូជា Subtitle ខ្មែរ និងបង្កើតសំឡេង Dubbing ធម្មជាតិពិោះៗ (ប្រុស/ស្រី) ដូចមនុស្សពិត!")

# ផ្នែកកំណត់ការ Settings (Sidebar)
with st.sidebar:
    st.header("⚙️ ការកំណត់ (Settings)")
    api_key = st.text_input("បញ្ចូល Gemini API Key:", type="password")
    
    # ជ្រើសរើស Gemini Model
    model_choice = st.selectbox(
        "ជ្រើសរើស AI Model:",
        ["gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash"]
    )
    
    st.markdown("---")
    st.subheader("🎙️ ការកំណត់សំឡេង (Voice Settings)")
    # ជ្រើសរើសសំឡេងប្រុស ឬស្រី សម្រាប់ភាសាខ្មែរ (km-KH)
    voice_label = st.selectbox(
        "ជ្រើសរើសសំឡេងអាន (Voice):",
        ["ស្រី (Sreymom - Natural)", "ប្រុស (Piseth - Natural)"]
    )
    
    # Mapping ឈ្មោះទៅជា Voice ID ពិតប្រាកដរបស់ Edge-TTS
    if "ស្រី" in voice_label:
        selected_voice_id = "km-KH-SreymomNeural"
    else:
        selected_voice_id = "km-KH-PisethNeural"

uploaded_file = st.file_uploader("ជ្រើសរើសវីដេអូ (MP4, MOV, AVI):", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    st.video(uploaded_file)

async def generate_edge_audio(text, voice_name, output_file):
    communicate = edge_tts.Communicate(text, voice_name)
    await communicate.save(output_file)

if st.button("🚀 ចាប់ផ្តើមដំណើរការបកប្រែ និងបង្កើតសំឡេង"):
    if not api_key:
        st.error("សូមបញ្ចូល Gemini API Key នៅកន្លែង Sidebar ជាមុនសិន!")
    elif uploaded_file is None:
        st.warning("សូម Upload វីដេអូជាមុនសិន!")
    else:
        with st.spinner("កំពុងវិភាគវីដេអូ បង្កើត Subtitle និងសំឡេង Dubbing ធម្មជាតិ..."):
            try:
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tfile.write(uploaded_file.read())
                video_path = tfile.name

                # ភ្ជាប់ទៅ Gemini API
                client = genai.Client(api_key=api_key)

                st.info("កំពុងបញ្ជូនវីដេអូទៅកាន់ Gemini AI...")
                video_file = client.files.upload(file=video_path)

                # 1. បង្កើតអត្ថបទ Subtitle ធម្មតា ស្រួល Copy ដាក់ CapCut
                prompt_text = """សូមទស្សនាវីដេអូនេះ ស្ដាប់សំឡេង និងសរសេរបកប្រែសាច់រឿងជាភាសាខ្មែរ ចែកចេញជាឃ្លាៗដាច់ពីគ្នា (Paragraphs) ឱ្យបានច្បាស់លាស់ ដើម្បីងាយស្រួលយកទៅ Copy ដាក់ក្នុង CapCut លើទូរស័ព្ទ។"""
                response_text = client.models.generate_content(
                    model=model_choice,
                    contents=[video_file, prompt_text],
                )
                sub_plain_text = response_text.text

                st.subheader("📝 អត្ថបទ Subtitle ខ្មែរ (សម្រាប់ Copy ដាក់ CapCut):")
                st.text_area("Copy Subtext ទីនេះ:", sub_plain_text, height=180)

                # 2. បង្កើតទម្រង់ SRT (សម្រាប់ Download)
                prompt_srt = """សូមបង្កើតជាទម្រង់ Subtitle ស្តង់ដារ (SRT format) ជាភាសាខ្មែរ ដោយដាក់កំណត់ម៉ោង (Timecode ឧទាហរណ៍: 00:00:01,000 --> 00:00:04,000) ឱ្យបានត្រឹមត្រូវតាមសាច់រឿងក្នុងវីដេអូ។ ចេញលទ្ធផលជាទម្រង់ SRT សុទ្ធសាធ។"""
                response_srt = client.models.generate_content(
                    model=model_choice,
                    contents=[video_file, prompt_srt],
                )
                srt_text = response_srt.text
                
                st.download_button(
                    label="📥 Download SRT Subtitle ជា File (.srt)",
                    data=srt_text,
                    file_name="khmer_subtitle.srt",
                    mime="text/plain"
                )
                
                # 3. បង្កើតសំឡេងអាន Dubbing តាមរយៈ Edge-TTS (សំឡេងប្រុស/ស្រីធម្មជាតិ)
                output_audio = "khmer_dubbed_audio.mp3"
                
                # រត់ Async function ដើម្បីបង្កើតសំឡេង Edge-TTS
                asyncio.run(generate_edge_audio(sub_plain_text, selected_voice_id, output_audio))
                
                st.subheader("🔊 សំឡេងអានខ្មែរធម្មជាតិ (AI Audio Dubbing):")
                st.audio(output_audio)
                
                with open(output_audio, "rb") as audio_file:
                    audio_bytes = audio_file.read()
                    st.download_button(
                        label="📥 Download សំឡេង Dubbing ជា File (.mp3)",
                        data=audio_bytes,
                        file_name="khmer_dubbing.mp3",
                        mime="audio/mp3"
                    )
                
            except Exception as e:
                st.error(f"មានបញ្ហាកើតឡើង: {e}")
                                       
