import streamlit as st
from google import genai
from gtts import gTTS
import os
import tempfile
import subprocess

st.set_page_config(page_title="Movie Dubbing & Explainer App")

st.title("🎬 AI Movie Dubbing & Explainer App")
st.write("Upload វីដេអូរបស់អ្នក (រហូតដល់ ៣នាទី) ដើម្បីឱ្យ AI ជួយបកប្រែ និងធ្វើជាសំឡេងខ្មែរជូន!")

api_key = st.text_input("បញ្ចូល Gemini API Key របស់អ្នក:", type="password")

uploaded_file = st.file_uploader("ជ្រើសរើសវីដេអូ (MP4, MOV):", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    st.video(uploaded_file)
    
if st.button("ចាប់ផ្តើមបកប្រែ និង Dubbing 🚀"):
    if not api_key:
        st.error("សូមបញ្ចូល Gemini API Key ជាមុនសិន!")
    elif uploaded_file is None:
        st.warning("សូម Upload វីដេអូជាមុនសិន!")
    else:
        with st.spinner("កំពុងទាញយកសំឡេង និងបកប្រែជាភាសាខ្មែរ..."):
            try:
                # ទុកវីដេអូក្នុង Temporary file
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tfile.write(uploaded_file.read())
                video_path = tfile.name

                # កាត់យកតែសំឡេង (Audio) ចេញពីវីដេអូ ដើម្បីកុំឱ្យធ្ងន់ និងមិន Error
                audio_path = video_path.replace('.mp4', '.mp3')
                subprocess.run(['ffmpeg', '-i', video_path, '-q:a', '0', '-map', 'a', audio_path], check=True)

                client = genai.Client(api_key=api_key)

                st.info("កំពុងបញ្ជូនសំឡេងទៅកាន់ Gemini AI...")
                audio_file_ref = client.files.upload(file=audio_path)

                prompt = "សូមស្ដាប់សំឡេងក្នុងឯកសារនេះ ហើយសរសេរបកប្រែសាច់រឿងជាភាសាខ្មែរឱ្យបានក្បោះក្បាយ និងទាក់ទាញ។"
                
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=[audio_file_ref, prompt],
                )
                
                recap_text = response.text
                st.subheader("📝 អត្ថបទបកប្រែជាភាសាខ្មែរ:")
                st.write(recap_text)
                
                # បង្កើតជាសំឡេងអានខ្មែរ
                tts = gTTS(text=recap_text, lang='km')
                output_audio = "dubbed_audio.mp3"
                tts.save(output_audio)
                
                st.subheader("🔊 សំឡេងបកប្រែភាសាខ្មែរ (Dubbing):")
                st.audio(output_audio)
                
            except Exception as e:
                st.error(f"មានបញ្ហាកើតឡើង: {e}")
                
