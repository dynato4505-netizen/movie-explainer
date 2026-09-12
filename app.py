import streamlit as st
from google import genai
from gtts import gTTS
import os
import tempfile

st.set_page_config(page_title="Movie Subtitle & Dubbing App")

st.title("🎬 AI Movie Subtitle & Dubbing App")
st.write("Upload វីដេអូខ្លី ដើម្បីឱ្យ AI បកប្រែជា Subtitle ខ្មែរ និងសំឡេង Dubbing!")

api_key = st.text_input("បញ្ចូល Gemini API Key របស់អ្នក:", type="password")

uploaded_file = st.file_uploader("ជ្រើសរើសវីដេអូ (MP4, MOV):", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    st.video(uploaded_file)
    
if st.button("ចាប់ផ្តើមបកប្រែ Subtitle និងសំឡេង 🚀"):
    if not api_key:
        st.error("សូមបញ្ចូល Gemini API Key ជាមុនសិន!")
    elif uploaded_file is None:
        st.warning("សូម Upload វីដេអូជាមុនសិន!")
    else:
        with st.spinner("កំពុងវិភាគវីដេអូ និងបង្កើត Subtitle ខ្មែរ..."):
            try:
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tfile.write(uploaded_file.read())
                video_path = tfile.name

                client = genai.Client(api_key=api_key)

                st.info("កំពុងបញ្ជូនវីដេអូទៅកាន់ Gemini AI...")
                video_file = client.files.upload(file=video_path)

                prompt = "សូមទស្សនាវីដេអូនេះ ស្ដាប់សំឡេង និងសរសេរបកប្រែសាច់រឿងជាភាសាខ្មែរ ចែកចេញជាឃ្លាៗ (Subtitle) សម្រាប់យកទៅដាក់ក្នុង CapCut។"
                
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=[video_file, prompt],
                )
                
                sub_text = response.text
                st.subheader("📝 អត្ថបទ Subtitle ភាសាខ្មែរ (សម្រាប់ Copy ដាក់ CapCut):")
                st.text_area("Copy Subtitle ទីនេះ:", sub_text, height=200)
                
                tts = gTTS(text=sub_text, lang='km')
                output_audio = "dubbed_audio.mp3"
                tts.save(output_audio)
                
                st.subheader("🔊 សំឡេងអានខ្មែរ (Audio):")
                st.audio(output_audio)
                
            except Exception as e:
                st.error(f"មានបញ្ហាកើតឡើង: {e}")
             
