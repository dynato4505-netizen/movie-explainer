import streamlit as st
import os
import tempfile
from gtts import gTTS
from google import genai

# 🌟 កំណត់ទម្រង់ទំព័រ
st.set_page_config(
    page_title="Khmer Video AI Pro (Simple)",
    page_icon="🎬",
    layout="wide"
)

# 📌 ចំណងជើងចម្បង
st.markdown("<h2 style='text-align: center; color: #a78bfa;'>🎬 Khmer Video AI Pro (Simple & Fast)</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94a3b8;'>ប្រព័ន្ធបង្កើតសំឡេងអត្ថបទ AI យ៉ាងងាយស្រួល និងរហ័ស</p>", unsafe_allow_html=True)

# 🔑 ប្រអប់សម្រាប់វាយបញ្ចូល API Key (AQ...) លើ Sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ ការកំណត់ API Key")
user_api_key = st.sidebar.text_input("🔑 បញ្ចូល Gemini API Key របស់អ្នក:", type="password", value="")

# 🗄️ Session State
if "script_input" not in st.session_state:
    st.session_state.script_input = ""
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None

# -------------------------------------------------------------
# 1. ផ្ទាំងបញ្ចូលអត្ថបទ និងបង្កើតសំឡេង
# -------------------------------------------------------------
st.subheader("📝 បញ្ចូលអត្ថបទ ឬស្គ្រីបសម្រាប់បម្លែងជាសំឡេង AI")

lang_choice = st.selectbox("ជ្រើសរើសភាសា:", ["ភាសាខ្មែរ (Khmer)", "ភាសាអង់គ្លេស (English)"])
lang_code = "km" if "ខ្មែរ" in lang_choice else "en"

st.session_state.script_input = st.text_area(
    "សរសេរ ឬបិទភ្ជាប់ (Paste) អត្ថបទនៅទីនេះ:",
    value=st.session_state.script_input,
    height=200
)

col1, col2 = st.columns(2)

with col1:
    if st.button("🚀 បង្កើតស្គ្រីបអូតូពី Gemini AI"):
        if not user_api_key.strip():
            st.warning("⚠️ សូមវាយបញ្ចូល Gemini API Key នៅ Sidebar ខាងឆ្វេងជាមុនសិន!")
        else:
            with st.spinner("⏳ Gemini AI កំពុងសរសេរស្គ្រីប..."):
                try:
                    client = genai.Client(api_key=user_api_key.strip())
                    response = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents="សូមសរសេរស្គ្រីបខ្លីមួយស្តីពីការអភិវឌ្ឍខ្លួនឯងជាភាសាខ្មែរ សម្រាប់ធ្វើជា Voiceover។"
                    )
                    st.session_state.script_input = response.text
                    st.success("🎉 បង្កើតស្គ្រីបបានជោគជ័យ!")
                    st.rerun()
                except Exception as e:
                    st.error(f"មានបញ្ហា: {e}")

with col2:
    if st.button("🎙️ បម្លែងអត្ថបទទៅเป็นសំឡេង AI"):
        text_to_speak = st.session_state.script_input
        if not text_to_speak.strip():
            st.warning("⚠️ សូមបញ្ចូលអត្ថបទជាមុនសិន!")
        else:
            with st.spinner("⏳ កំពុងបង្កើតសំឡេង AI..."):
                try:
                    tts = gTTS(text=text_to_speak, lang=lang_code, slow=False)
                    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                    tts.save(temp_audio.name)
                    temp_audio.close()
                    
                    with open(temp_audio.name, "rb") as f:
                        st.session_state.audio_bytes = f.read()
                        
                    if os.path.exists(temp_audio.name):
                        os.remove(temp_audio.name)
                        
                    st.success("🎉 បង្កើតសំឡេង AI បានជោគជ័យរួចរាល់!")
                except Exception as e:
                    st.error(f"មានបញ្ហាក្នុងការបង្កើតសំឡេង: {e}")

# -------------------------------------------------------------
# 2. ផ្ទាំងស្ដាប់ និងទាញយកសំឡេង
# -------------------------------------------------------------
if st.session_state.get("audio_bytes"):
    st.markdown("---")
    st.subheader("📥 ស្ដាប់ និងទាញយកឯកសារសំឡេង (.mp3)")
    st.audio(st.session_state.audio_bytes, format="audio/mp3")
    st.download_button(
        label="📥 ទាញយកឯកសារសំឡេង MP3",
        data=st.session_state.audio_bytes,
        file_name="ai_voiceover.mp3",
        mime="audio/mp3"
    )
    
