import streamlit as st
import asyncio
import edge_tts
import os
import tempfile
import re
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

# 🌟 កំណត់ទម្រង់ទំព័រឱ្យធំទូលាយស្អាត (Wide Mode)
st.set_page_config(
    page_title="Khmer Video AI - បញ្ចូលសំឡេង AI លើវីដេអូពេញ",
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
st.markdown("<p style='text-align: center; color: #94a3b8;'>រក្សាទុកវីដេអូដើមពេញលេញ និងបញ្ចូលសំឡេង AI តាម Timestamps</p>", unsafe_allow_html=True)

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
if "uploaded_video" not in st.session_state:
    st.session_state.uploaded_video = None
if "final_video_bytes" not in st.session_state:
    st.session_state.final_video_bytes = None

# -------------------------------------------------------------
# 1. ផ្ទាំងវីដេអូ (Video Input)
# -------------------------------------------------------------
with tab_video:
    st.subheader("🎬 បញ្ចូលវីដេអូ ឬតំណភ្ជាប់ (Link)")
    input_method = st.radio("ជ្រើសរើសវិធីសាស្ត្របញ្ចូល:", ["📤 Upload", "🔗 Link"], horizontal=True)
    
    if input_method == "📤 Upload":
        uploaded_file = st.file_uploader("បន្ថែមវីដេអូពេញ", type=["mp4", "mov", "mkv", "avi", "webm"])
        if uploaded_file:
            st.session_state.uploaded_video = uploaded_file
            st.success("✅ បានផ្ទុកវីដេអូជោគជ័យ!")
            st.video(uploaded_file)
    else:
        st.text_input("🔗 ដាក់ Link វីដេអូ (YouTube, TikTok, ฯលฯ):")

    st.markdown("---")
    st.subheader("📊 គុណភាពវីដេអូ (Resolution)")
    st.radio("ជ្រើសរើសកម្រិតច្បាស់:", ("⚡ លឿន 480p", "✨ ល្អ 720p", "💎 ខ្ពស់ (ដើម)"), horizontal=True)

# -------------------------------------------------------------
# 2. ផ្ទាំងបកប្រែ (Translation)
# -------------------------------------------------------------
with tab_translate:
    st.subheader("🌐 ការកំណត់ម៉ាស៊ីនបកប្រែ")
    st.selectbox("ម៉ាស៊ីនបកប្រែ:", ("✨ Gemini (ធម្មជាតិ)", "Google Translate Pro", "OpenAI GPT-4o"))
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        st.selectbox("ភាសាដើម", ["អង់គ្លេស (En)", "ថៃ (Th)", "ចិន (Zh)"])
    with col_l2:
        st.selectbox("បកប្រែទៅ", ["🇰🇭 ខ្មែរ (Khmer)"])

# -------------------------------------------------------------
# 3. ផ្ទាំងសំឡេង និងបញ្ចូលសំឡេងលើវីដេអូពេញ (Full Video Dubbing)
# -------------------------------------------------------------
with tab_audio:
    st.subheader("🎙️ បញ្ចូលសំឡេង AI លើវីដេអូពេញ (មិនកាត់ផ្ដាច់សាច់រឿង)")
    
    voice_type = st.radio("សំឡេងនិយាយ:", ("👩 ស្រី (Sreymom)", "👨 ប្រុស (Piseth)"))
    selected_voice = "km-KH-SreymomNeural" if "ស្រី" in voice_type else "km-KH-PisethNeural"
    
    keep_orig_audio = st.checkbox("🔊 រក្សាសំឡេងដើមក្នុងវីដេអូខ្លះ (Background Audio - 10%)", value=False)

    st.markdown("---")
    st.session_state.script_input = st.text_area(
        "បញ្ចូល Timestamps និងអត្ថបទ (ឧទាហរណ៍: [00:00 - 00:05] សួស្តី...):",
        value=st.session_state.script_input,
        height=140
    )

    async def generate_tts_safe(text, voice, output_path):
        for attempt in range(3):
            try:
                communicate = edge_tts.Communicate(text, voice)
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
                    "text": content
                })
        return dialogues

    if st.button("🎬 ចាប់ផ្តើមបញ្ចូលសំឡេង AI លើវីដេអូពេញ (.mp4)"):
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
                    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                    tfile.write(uploaded_video_file.read())
                    tfile.close()
                    
                    status_text.info("🎬 กำลังโหลดវីដេអូ និងបង្កើតសំឡេង AI...")
                    video_clip = VideoFileClip(tfile.name)
                    
                    audio_clips = []
                    if video_clip.audio is not None and keep_orig_audio:
                        audio_clips.append(video_clip.audio.volumized(0.1))
                    
                    total_items = len(dialogues)
                    temp_audio_files = []
                    
                    for i, item in enumerate(dialogues):
                        status_text.info(f"🎙️ កំពុងបង្កើតសំឡេងទី {i+1} នៃ {total_items}...")
                        audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                        temp_audio_files.append(audio_path)
                        
                        success = asyncio.run(generate_tts_safe(item["text"], selected_voice, audio_path))
                        if success:
                            ai_audio = AudioFileClip(audio_path).set_start(item["start_sec"])
                            audio_clips.append(ai_audio)
                            
                        progress_bar.progress(int((i + 1) / total_items * 100))
                    
                    status_text.info("🔄 កំពុងចងក្រងសំឡេង AI ចូលគ្នាជាមួយវីដេអូពេញ...")
                    final_audio = CompositeAudioClip(audio_clips)
                    final_video = video_clip.set_audio(final_audio)
                    
                    output_video_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                    final_video.write_videofile(output_video_path, codec="libx264", audio_codec="aac", logger=None)
                    
                    with open(output_video_path, "rb") as f:
                        st.session_state.final_video_bytes = f.read()
                    
                    video_clip.close()
                    final_video.close()
                    if os.path.exists(tfile.name): os.remove(tfile.name)
                    if os.path.exists(output_video_path): os.remove(output_video_path)
                    for p in temp_audio_files:
                        if os.path.exists(p): os.remove(p)
                        
                    status_text.success("🎉 បញ្ចូលសំឡេង AI លើវីដេអូពេញបានរួចរាល់ជាស្រេច!")
            except Exception as e:
                st.error(f"មានបញ្ហាកើតឡើង: {e}")

    # 📺 បង្ហាញវីដេអូពេញ និងប៊ូតុង Download (ដាក់ key ដាច់ដោយឡែក)
    if st.session_state.get("final_video_bytes"):
        st.markdown("---")
        st.write("### 🎬 លទ្ធផលវីដេអូពេញ (Full Video ជាមួយសំឡេង AI):")
        st.video(st.session_state.final_video_bytes)
        st.download_button(
            label="📥 ទាញយកវីដេអូពេញ (.mp4)",
            data=st.session_state.final_video_bytes,
            file_name="khmer_ai_full_dubbed_video.mp4",
            mime="video/mp4",
            key="audio_tab_download_btn"
        )
        st.markdown("---")

# -------------------------------------------------------------
# 4. ផ្ទាំងអក្សរ (Subtitle)
# -------------------------------------------------------------
with tab_sub:
    st.subheader("🔤 ការកំណត់រចនាប័ទ្មអក្សរ Subtitle")
    st.selectbox("Font អក្សរ:", ("Battambang", "Siemreap", "Moul"))
    st.slider("ទំហំអក្សរ", 14, 40, 22, 1)

# -------------------------------------------------------------
# 5. ផ្ទាំងទាញយក (Download Section)
# -------------------------------------------------------------
with tab_download:
    st.subheader("📥 ទាញយកលទ្ធផលវីដេអូពេញ")
    if st.session_state.get("final_video_bytes"):
        st.video(st.session_state.final_video_bytes)
        st.download_button(
            label="📥 ទាញយកវីដេអូពេញ (.mp4)",
            data=st.session_state.final_video_bytes,
            file_name="khmer_ai_full_dubbed_video.mp4",
            mime="video/mp4",
            key="download_tab_download_btn"
        )
    else:
        st.info("មិនទាន់មានវីដេអូទេ! សូមបំពេញ Timestamps នៅផ្ទាំង «សំឡេង» ជាមុនសិន។")

# -------------------------------------------------------------
# 6. ផ្ទាំងរីដេអូម (Movie Recap History)
# -------------------------------------------------------------
with tab_recap:
    st.subheader("🎞️ ប្រវត្តិរីដេអូម")
    st.markdown("<p style='color: #94a3b8;'>វីដេអូដែលបានបង្កើតរួចនឹងត្រូវបានរក្សាទុកនៅទីនេះ។</p>", unsafe_allow_html=True)
