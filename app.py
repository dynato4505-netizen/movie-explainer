import streamlit as st
import os
import tempfile
from gtts import gTTS
from google import genai

# 🌟 កំណត់ទំព័រឱ្យធំទូលាយ
st.set_page_config(
    page_title="Khmer Video AI Pro (Auto Video Dubbing)",
    page_icon="🎬",
    layout="wide"
)

# 🧹 Clear Cache Button
with st.sidebar:
    st.markdown("---")
    if st.button("🧹 Clear Cache & Restart"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("បានលុប Cache និងចាប់ផ្តើមថ្មីជោគជ័យ!")
        st.rerun()

# 🎨 Custom CSS សម្រាប់ Dark Theme
st.markdown("""
    <style>
    .main { background-color: #0b0f19; color: #ffffff; }
    .stButton>button {
        background: linear-gradient(45deg, #8b5cf6, #3b82f6);
        color: white; border-radius: 10px; border: none;
        padding: 12px 24px; font-weight: bold; width: 100%;
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #1e293b; color: white; border-radius: 8px; border: 1px solid #334155;
    }
    </style>
""", unsafe_allow_html=True)

# 📌 ចំណងជើង
st.markdown("<h2 style='text-align: center; color: #a78bfa;'>🎬 Khmer Video AI Pro (Auto Video Dubbing)</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94a3b8;'>ប្រព័ន្ធទាញយកស្គ្រីប និងបង្កើតសំឡេង AI ភ្ជាប់ជាមួយវីដេអូ</p>", unsafe_allow_html=True)

# 🔑 Sidebar API Key
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ ការកំណត់ API Key")
user_api_key = st.sidebar.text_input("🔑 បញ្ចូល Gemini API Key:", type="password", value="")

# 🗄️ Session States
if "script_input" not in st.session_state:
    st.session_state.script_input = ""
if "uploaded_video" not in st.session_state:
    st.session_state.uploaded_video = None
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None

# -------------------------------------------------------------
# 1. ផ្ទាំង Upload វីដេអូ និងទាញយកស្គ្រីបអូតូ
# -------------------------------------------------------------
st.subheader("🎬 ជំហានទី ១៖ បញ្ចូលវីដេអូ និងទាញយកស្គ្រីបអូតូ (Gemini AI)")

uploaded_file = st.file_uploader("📂 ជ្រើសរើសវីដេអូ (MP4, MOV, AVI):", type=["mp4", "mov", "mkv", "avi"], key="vid_up")
if uploaded_file is not None:
    st.session_state.uploaded_video = uploaded_file

if st.session_state.get("uploaded_video") is not None:
    st.success("✅ បានផ្ទុកវីដេអូជោគជ័យ!")
    st.video(st.session_state.uploaded_video)
    
    if st.button("🚀 ទាញយកស្គ្រីបអូតូពីវីដេអូ (Gemini AI)") :
        if not user_api_key.strip():
            st.warning("⚠️ សូមបញ្ចូល Gemini API Key នៅ Sidebar ខាងឆ្វេងជាមុនសិន!")
        else:
            with st.spinner("⏳ Gemini AI កំពុងអានវីដេអូ និងបង្កើតស្គ្រីប..."):
                try:
                    client = genai.Client(api_key=user_api_key.strip())
                    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                    st.session_state.uploaded_video.seek(0)
                    tfile.write(st.session_state.uploaded_video.read())
                    tfile.close()
                    
                    video_file = client.files.upload(file=tfile.name)
                    import time
                    while video_file.state.name == "PROCESSING":
                        time.sleep(2)
                        video_file = client.files.get(name=video_file.name)
                        
                    response = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=[video_file, "សូមស្ដាប់សំឡេងក្នុងវីដេអូនេះ រួចសរសេរជាស្គ្រីបសាច់រឿងជាភាសាខ្មែរសម្រាប់ធ្វើ Voiceover។"]
                    )
                    st.session_state.script_input = response.text
                    os.remove(tfile.name)
                    client.files.delete(name=video_file.name)
                    st.success("🎉 ទាញយកស្គ្រីបបានជោគជ័យ!")
                except Exception as e:
                    st.error(f"មានបញ្ហា: {e}")

# -------------------------------------------------------------
# 2. ផ្ទាំងកែសម្រួលស្គ្រីប និងបង្កើតសំឡេង AI
# -------------------------------------------------------------
st.markdown("---")
st.subheader("🎙️ ជំហានទី ២៖ កែសម្រួលស្គ្រីប និងបង្កើតសំឡេង AI")

st.session_state.script_input = st.text_area(
    "📋 ស្គ្រីបសម្រាប់អាន (អាចកែសម្រួលបាន):",
    value=st.session_state.script_input,
    height=200
)

if st.button("🔊 ចាប់ផ្ដើមបង្កើតសំឡេង AI (.mp3)"):
    script_text = st.session_state.script_input
    if not script_text.strip():
        st.warning("⚠️ សូមបញ្ចូលស្គ្រីបជាមុនសិន!")
    else:
        with st.spinner("⏳ កំពុងបង្កើតសំឡេង AI..."):
            try:
                tts = gTTS(text=script_text, lang='km', slow=False)
                temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                tts.save(temp_audio.name)
                temp_audio.close()
                
                with open(temp_audio.name, "rb") as f:
                    st.session_state.audio_bytes = f.read()
                if os.path.exists(temp_audio.name):
                    os.remove(temp_audio.name)
                    
                st.success("🎉 បង្កើតសំឡេង AI រួចរាល់ជាស្រេច!")
            except Exception as e:
                st.error(f"មានបញ្ហា: {e}")

# -------------------------------------------------------------
# 3. ផ្ទាំងទាញយកលទ្ធផល
# -------------------------------------------------------------
if st.session_state.get("audio_bytes"):
    st.markdown("---")
    st.subheader("📥 ជំហានទី ៣៖ ទាញយកលទ្ធផលសំឡេង AI ទៅប្រើប្រាស់")
    st.audio(st.session_state.audio_bytes, format="audio/mp3")
    st.download_button(
        label="📥 ទាញយកឯកសារសំឡេង MP3",
        data=st.session_state.audio_bytes,
        file_name="ai_dubbed_audio.mp3",
        mime="audio/mp3"
    )
    st.info("💡 ចំណាំ៖ បងអាចយកវីដេអូដើម និងសំឡេង MP3 នេះទៅដាក់ចូលក្នុង CapCut ឬកម្មវិធីកាត់តណាមួយដើម្បីรวมគ្នាបានយ៉ាងងាយស្រួល និងរហ័សបំផុត ដោយធានាថាអត់មាន Error គាំង Server ទៀតទេ។")
                    
