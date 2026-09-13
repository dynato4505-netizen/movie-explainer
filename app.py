import streamlit as st
from google import genai
from gtts import gTTS
import os
import tempfile

st.set_page_config(page_title="Movie Subtitle & Dubbing Pro App")

st.title("🎬 AI Movie Subtitle & Dubbing Pro")
st.write("Upload វីដេអូខ្លី ដើម្បីឱ្យ AI បកប្រែជា Subtitle ខ្មែរ (សម្រាប់ Copy ឬ Download SRT) និងបង្កើតសំឡេង Dubbing ព្រមទាំងអាច Download បានភ្លាមៗ!")

api_key = st.text_input("បញ្ចូល Gemini API Key របស់អ្នក:", type="password")

uploaded_file = st.file_uploader("ជ្រើសរើសវីដេអូ (MP4, MOV):", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    st.video(uploaded_file)
    
if st.button("ចាប់ផ្តើមបង្កើត Subtitle និងសំឡេង 🚀"):
    if not api_key:
        st.error("សូមបញ្ចូល Gemini API Key ជាមុនសិន!")
    elif uploaded_file is None:
        st.warning("សូម Upload វីដេអូជាមុនសិន!")
    else:
        with st.spinner("កំពុងវិភាគវីដេអូ បង្កើត Subtitle ខ្មែរ និងសំឡេង..."):
            try:
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tfile.write(uploaded_file.read())
                video_path = tfile.name

                client = genai.Client(api_key=api_key)

                st.info("កំពុងបញ្ជូនវីដេអូទៅកាន់ Gemini AI...")
                video_file = client.files.upload(file=video_path)

                # 1. បង្កើតអត្ថបទ Subtitle ធម្មតា ស្រួល Copy ដាក់ទូរស័ព្ទ
                prompt_text = """សូមទស្សនាវីដេអូនេះ ស្ដាប់សំឡេង និងសរសេរបកប្រែសាច់រឿងជាភាសាខ្មែរ ចែកចេញជាឃ្លាៗដាច់ពីគ្នា (Paragraphs) ឱ្យបានច្បាស់លាស់ ដើម្បីងាយស្រួលយកទៅ Copy ដាក់ក្នុង CapCut លើទូរស័ព្ទ។"""
                response_text = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=[video_file, prompt_text],
                )
                sub_plain_text = response_text.text

                st.subheader("📝 អត្ថបទ Subtitle ខ្មែរ (សម្រាប់ Copy ដាក់ CapCut):")
                st.text_area("Copy Subtext ទីនេះ:", sub_plain_text, height=180)

                # 2. បង្កើតទម្រង់ SRT (សម្រាប់ Download)
                prompt_srt = """សូមបង្កើតជាទម្រង់ Subtitle ស្តង់ដារ (SRT format) ជាភាសាខ្មែរ ដោយដាក់កំណត់ម៉ោង (Timecode ឧទាហរណ៍: 00:00:01,000 --> 00:00:04,000) ឱ្យបានត្រឹមត្រូវតាមសាច់រឿងក្នុងវីដេអូ។ ចេញលទ្ធផលជាទម្រង់ SRT សុទ្ធសាធ។"""
                response_srt = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=[video_file, prompt_srt],
                )
                srt_text = response_srt.text
                
                # ប៊ូតុងសម្រាប់ Download SRT Subtitle ជា File .srt
                st.download_button(
                    label="📥 Download SRT Subtitle ជា File (.srt)",
                    data=srt_text,
                    file_name="khmer_subtitle.srt",
                    mime="text/plain"
                )
                
                # 3. បង្កើតសំឡេងអាន Dubbing
                tts = gTTS(text=sub_plain_text, lang='km')
                output_audio = "khmer_dubbed_audio.mp3"
                tts.save(output_audio)
                
                st.subheader("🔊 សំឡេងអានខ្មែរ (Audio Dubbing):")
                st.audio(output_audio)
                
                # ប៊ូតុងសម្រាប់ Download សំឡេងជា File .mp3
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
                
