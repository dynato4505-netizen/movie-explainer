import streamlit as st
from google import genai
from gtts import gTTS
import os

st.set_page_config(page_title="Movie Explainer AI", page_icon="🎬", layout="centered")

st.title("🎬 Movie Explainer & Recap Tool")
st.write("បញ្ចូលចំណងជើងរឿង ឬសាច់រឿង ដើម្បីឱ្យ AI សម្រាយ និងអានជាសំឡេង!")

api_key = st.text_input("បញ្ចូល Gemini API Key របស់អ្នក:", type="password")

movie_title = st.text_input("ឈ្មោះរឿង (Movie Title):")
prompt_details = st.text_area("ព័ត៌មានបន្ថែម ឬសាច់រឿងសង្ខេប (Optional):")

if st.button("សម្រាយរឿងឥឡូវនេះ 🚀"):
    if not api_key:
        st.error("សូមបញ្ចូល Gemini API Key ជាមុនសិន!")
    elif not movie_title:
        st.warning("សូមបញ្ចូលឈ្មោះរឿង!")
    else:
        with st.spinner("កំពុងសម្រាយរឿង និងបង្កើតសំឡេង..."):
            try:
                client = genai.Client(api_key=api_key)
                prompt = f"សូមសម្រាយរឿង '{movie_title}' ជាភាសាខ្មែរឱ្យបានលម្អិត គួរឱ្យចាប់អារម្មណ៍ និងយល់ងាយ។ {prompt_details}"
                
                response = client.models.generate_content(
                    model=',model='gemini-2.5-flash'

                    contents=prompt,
                )
                
                recap_text = response.text
                st.subheader("📝 អត្ថបទសម្រាយរឿង:")
                st.write(recap_text)
                
                # បង្កើត Audio ដោយ gTTS
                tts = gTTS(text=recap_text, lang='km')
                audio_file = "recap_audio.mp3"
                tts.save(audio_file)
                
                st.subheader("🔊 សំឡេងសម្រាយរឿង:")
                st.audio(audio_file)
                
            except Exception as e:
                st.error(f"មានបញ្ហាកើតឡើង: {e}")
              
