import streamlit as st
from google import genai
from gtts import gTTS
import os
import tempfile

st.set_page_config(page_title="Movie Dubbing & Explainer App")

st.title("🎬 AI Movie Dubbing & Explainer App")
st.write("Upload វីដេអូបរទេសរបស់អ្នក ដើម្បីឱ្យ AI ជួយបកប្រែ និងបង្កើតជាសំឡេងខ្មែរជូន!")

api_key = st.text_input("បញ្ចូល Gemini API Key របស់អ្នក:", type="password")

# មុខងារ Upload វីដេអូ
uploaded_file = st.file_uploader("ជ្រើសរើសវីដេអូបរទេស (MP4, MOV):", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    st.video(uploaded_file)
    
if st.button("ចាប់ផ្តើមបកប្រែ និង Dubbing 🚀"):
    if not api_key:
        st.error("សូមបញ្ចូល Gemini API Key ជាមុនសិន!")
    elif uploaded_file is None:
        st.warning("សូម Upload វីដេអូជាមុនសិន!")
    else:
        with st.spinner("កំពុងអានវីដេអូ និងបកប្រែជាភាសាខ្មែរ..."):
            try:
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tfile.write(uploaded_file.read())
                video_path = tfile.name

                client = genai.Client(api_key=api_key)

                st.info("កំពុងបញ្ជូនវីដេអូទៅកាន់ Gemini AI...")
                video_file = client.files.upload(file=video_path)

                prompt = "សូមទស្សនាវីដេអូនេះ ស្ដាប់សំឡេង និងសរសេរបកប្រែសាច់រឿងជាភាសាខ្មែរឱ្យបានក្បោះក្បាយ និងទាក់ទាញ ដើម្បីធ្វើការ Dubbing សំឡេង។"
                
                # ដូរមកប្រើម៉ូដែលថ្មីតាមការណែនាំរបស់ Error
                response = client.models.generate_content(
                    model='gemini-3.1-pro-preview',
                    contents=[video_file, prompt],
                )
                
                recap_text = response.text
                st.subheader("📝 អត្ថបទបកប្រែជាភាសាខ្មែរ:")
                st.write(recap_text)
                
                tts = gTTS(text=recap_text, lang='km')
                audio_file = "dubbed_audio.mp3"
                tts.save(audio_file)
                
                st.subheader("🔊 សំឡេងបកប្រែភាសាខ្មែរ (Dubbing):")
                st.audio(audio_file)
                
            except Exception as e:
                st.error(f"មានបញ្ហាកើតឡើង: {e}")
                
