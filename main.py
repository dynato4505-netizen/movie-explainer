import streamlit as st
import asyncio
import edge_tts
import os
import tempfile
import time
import re
import zipfile
import io
from moviepy.editor import VideoFileClip, AudioFileClip

# 🌟 កំណត់ទម្រង់ទំព័រឱ្យធំទូលាយស្អាត (Wide Mode)
st.set_page_config(
    page_title="Khmer Video AI - បកប្រែវីដេអូ និងបង្កើតសំឡេង/វីដេអូខ្មែរ",
    page_icon="🎬",
    layout="wide"
)

# 🎨 Custom CSS សម្រាប់ Dark Mode ដ៏ប្រណិត
st.markdown("""
    <style>
    .main {
        background-color: #0b0f19;
        color: #ffffff;
    }
    .stButton>button {
        background: linear-gradient(45deg, #8b5cf6, #3b82f6);
        color: white;
        border-radius: 10px;
        border: none;
        padding: 12px 24px;
        font-weight: bold;
        width: 100%;
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #1e293b;
        color: white;
        border-radius: 8px;
        border: 1px solid #334155;
    }
    .stSelectbox>div>div>select {
        background-color: #1e293b;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# 📌 ចំណងជើងចម្បងរបស់แอป
st.markdown("<h2 style='text-align: center; color: #a78bfa;'>🎬 Khmer Video AI</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94a3b8;'>កាត់វីដេអូ និងបញ្ចូលសំឡេង AI ខ្មែរ ដោយស្វ័យប្រវត្តិ</p>", unsafe_allow_html=True)

# 🗂️ បែងចែកផ្ទាំង (Tabs)
tab_video, tab_translate, tab_audio, tab_sub, tab_download, tab_recap = st.tabs([
    "🎬 វីដេអូ", 
    "🌐 បកប្រែ", 
    "🎙️ សំឡេង", 
    "🔤 អក្សរ", 
    "📥 ទាញយក", 
    "🎞️ រីដេអូម"
])

# 🗄️ Session State Initialization
if "script_input" not in st.session_state:
    st.session_state.script_input = ""
if "zip_buffer" not in st.session_state:
    st.session_state.zip_buffer = None
if "recap_history" not in st.session_state:
    st.session_state.recap_history = []
if "uploaded_video" not in st.session_state:
    st.session_state.uploaded_video = None

# -------------------------------------------------------------
# 1. ផ្ទាំងវីដេអូ (Video Input & Resolution)
# -------------------------------------------------------------
with tab_video:
    st.subheader("🎬 បញ្ចូលវីដេអូ ឬតំណភ្ជាប់ (Link)")
    
    input_method = st.radio("ជ្រើសរើសវិធីសាស្ត្របញ្ចូល:", ["📤 Upload", "🔗 Link"], horizontal=True)
    
    if input_method == "📤 Upload":
        uploaded_file = st.file_uploader("បន្ថែមវីដេអូ", type=["mp4", "mov", "mkv", "avi", "webm"])
        if uploaded_file:
            st.session_state.uploaded_video = uploaded_file
            st.success("✅ បានផ្ទុកវីដេអូជោគជ័យ!")
            st.video(uploaded_file)
    else:
        video_url = st.text_input("🔗 ដាក់ Link វីដេអូ (YouTube, TikTok, ฯលฯ):")
        if video_url:
            st.info("បានទទួលតំណភ្ជាប់វីដេអូរួចរាល់។")

    st.markdown("---")
    st.subheader("📊 គុណភាពវីដេអូ (Resolution)")
    resolution = st.radio(
        "ជ្រើសរើសកម្រិតច្បាស់:",
        ("⚡ លឿន 480p", "✨ ល្អ 720p", "💎 ខ្ពស់ (ដើម)"),
        horizontal=True
    )

# -------------------------------------------------------------
# 2. ផ្ទាំងបកប្រែ (Translation & Gemini Settings)
# -------------------------------------------------------------
with tab_translate:
    st.subheader("🌐 ការកំណត់ម៉ាស៊ីនបកប្រែ (Translation Engine)")
    
    trans_engine = st.selectbox(
        "ម៉ាស៊ីនបកប្រែ:",
        ("✨ Gemini (ធម្មជាតិ តែមានកូតា)", "Google Translate Pro", "OpenAI GPT-4o")
    )
    
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        source_lang = st.selectbox("ភាសាដើម (Source Language)", ["ស៊ុយអែត (Sv)", "អង់គ្លេស (En)", "ថៃ (Th)", "ចិន (Zh)"])
    with col_l2:
        target_lang = st.selectbox("បកប្រែទៅ (Target Language)", ["🇰🇭 ខ្មែរ (Khmer)"])

    st.markdown("---")
    st.subheader("⚙️ មុខងារបន្ថែមពេលបកប្រែ:")
    opt_sub = st.checkbox("បង្កើតអក្សររត់ខ្មែរ (Subtitle)", value=True)
    opt_dub = st.checkbox("បង្កើតសំឡេងអានខ្មែរ (Dubbing)", value=False)
    opt_srt = st.checkbox("ទាញយកអក្សរជាឯកសារ (SRT)", value=False)
    opt_book = st.checkbox("📖 ម៉ូដនិទានរឿង (កែអត្ថបទឱ្យល្វន់ដូចអ្នកនិទាន)", value=False)
    opt_check = st.checkbox("✏️ ពិនិត្យ និងកែអត្ថបទមុនបង្កើតសំឡេង", value=True)

# -------------------------------------------------------------
# 3. ផ្ទាំងសំឡេង និងកាត់វីដេអូ (Video Dubbing & Audio Cutting)
# -------------------------------------------------------------
with tab_audio:
    st.subheader("🎙️ កាត់វីដេអូ និងបញ្ចូលសំឡេង AI (Dubbing Video)")
    
    voice_type = st.radio(
        "សំឡេងនិយាយ:",
        ("👩 ស្រី (Sreymom)", "👨 ប្រុស (Piseth)")
    )
    selected_voice = "km-KH-SreymomNeural" if "ស្រី" in voice_type else "km-KH-PisethNeural"

    st.markdown("---")
    st.session_state.script_input = st.text_area(
        "បញ្ចូល Timestamps និងអត្ថបទ (ឧទាហរណ៍: [00:00 - 00:05] សួស្តី...):",
        value=st.session_state.script_input,
        height=140
    )

    async def generate_tts_safe(text, voice, output_path, rate="+0%", pitch="+0Hz"):
        for attempt in range(3):
            try:
                communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
                await communicate.save(output_path)
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    return True
            except Exception:
                if attempt == 2:
                    return False
                await asyncio.sleep(1)
        return False

    def time_to_seconds(time_str):
        parts = list(map(int, time_str.split(':')))
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        return parts[0]

    def parse_timestamps_video(text):
        pattern = r'\[\s*(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\s*\]\s*(.*)'
        matches = re.findall(pattern, text)
        dialogues = []
        for match in matches:
            start_str, end_str, content = match[0], match[1], match[2].strip()
            if content:
                dialogues.append({
                    "start_sec": time_to_seconds(start_str),
                    "end_sec": time_to_seconds(end_str),
                    "time_label": f"[{start_str}-{end_str}]".replace(":", "-"),
                    "text": content
                })
        return dialogues

    if st.button("🎬 ចាប់ផ្តើមកាត់វីដេអូ និងបញ្ចូលសំឡេង AI"):
        script_text = st.session_state.script_input
        uploaded_video_file = st.session_state.get("uploaded_video", None)
        
        if not script_text.strip():
            st.warning("⚠️ សូមបញ្ចូលស្គ្រីប ឬ Timestamps ជាមុនសិន!")
        elif not uploaded_video_file:
            st.warning("⚠️ សូម Upload វីដេអូនៅផ្ទាំង «វីដេអូ» ជាមុនសិន!")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                dialogues = parse_timestamps_video(script_text)
                if not dialogues:
                    st.error("❌ ទម្រង់ Timestamps មិនត្រឹមត្រូវទេ។ (ឧទាហរណ៍: [00:00 - 00:05] អត្ថបទ)")
                else:
                    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4
    
