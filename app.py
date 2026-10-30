import streamlit as st
import asyncio
import edge_tts
import os
import tempfile
import re
from google import genai
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip

# 🌟 កំណត់ទម្រង់ទំព័រឱ្យធំទូលាយស្អាត (Wide Mode)
st.set_page_config(
    page_title="Khmer Video AI Pro - Auto Script & Dubbing",
    page_icon="🎬",
    layout="wide"
)

# 🧹 ប៊ូតុង Clear Cache & Restart
with st.sidebar:
    st.markdown("---")
    if st.button("🧹 Clear Cache & Restart"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("បានលុប Cache និងចាប់ផ្តើមថ្មីជោគជ័យ!")
        st.rerun()

# 🎨 Custom CSS សម្រាប់ Dark Mode
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
    </style>
""", unsafe_allow_html=True)

# 📌 ចំណងជើងចម្បង
st.markdown("<h2 style='text-align: center; color: #a78bfa;'>🎬 Khmer Video AI Pro (Auto-Script & Dubbing)</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94a3b8;'>ប្រព័ន្ធទាញយកស្គ្រីប និងបកប្រែអូតូដោយ Gemini AI ពេញលេញ</p>", unsafe_allow_html=True)

# 🔑 ប្រអប់សម្រាប់វាយបញ្ចូល API Key (AQ...) លើ Sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ ការកំណត់ API Key")
user_api_key = st.sidebar.text_input("🔑 បញ្ចូល Gemini API Key របស់អ្នក:", type="password", value="")

# 🗂️ ផ្ទាំង Tabs
tab_video, tab_audio, tab_download = st.tabs(["🎬 វីដេអូ & ទាញយកស្គ្រីបអូតូ", "🎙️ បញ្ចូលសំឡេង AI", "📥 ទាញយកលទ្ធផល"])

# 🗄️ Session State
if "script_input" not in st.session_state:
    st.session_state.script_input = ""
if "uploaded_video" not in st.session_state:
    st.session_state.uploaded_video = None
if "final_video_bytes" not in st.session_state:
    st.session_state.final_video_bytes = None

# -------------------------------------------------------------
# 1. ផ្ទាំងវីដេអូ និង Gemini Auto-Script
# -------------------------------------------------------------
with tab_video:
    st.subheader("🎬 បញ្ចូលវីដេអូសម្រាប់ទាញយកស្គ្រីបអូតូ")
    
    uploaded_file = st.file_uploader("បន្ថែមវីដេអូ (ទំហំក្រោម 200MB)", type=["mp4", "mov", "mkv", "avi"], key="vid_uploader")
    
    if uploaded_file is not None:
        st.session_state.uploaded_video = uploaded_file
        
    if st.session_state.get("uploaded_video") is not None:
        current_video = st.session_state.uploaded_video
        st.success("✅ បានផ្ទុកវីដេអូជោគជ័យ!")
        st.video(current_video)
        
        st.markdown("---")
        st.markdown("### ✨ ទាញយកស្គ្រីប និងបកប្រែជាភាសាខ្មែរអូតូ (Gemini AI)")
        
        if st.button("🚀 ចាប់ផ្ដើមទាញយក និងបកប្រែស្គ្រីបអូតូ", key="start_gemini_transcribe"):
            if not user_api_key.strip():
                st.warning("⚠️ សូមវាយបញ្ចូល Gemini API Key នៅកន្លែង Sidebar ខាងឆ្វេងជាមុនសិន!")
            else:
                with st.spinner("⏳ Gemini AI កំពុងអានវីដេអូ និងបង្កើតស្គ្រីបព្រមទាំង Timestamps... (រង់ចាំបន្តិច)"):
                    try:
                        client = genai.Client(api_key=user_api_key.strip())
                        
                        tfile_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                        current_video.seek(0)
                        tfile_temp.write(current_video.read())
                        tfile_temp.close()
                        
                        video_file = client.files.upload(file=tfile_temp.name)
                        
                        import time
                        while video_file.state.name == "PROCESSING":
                            time.sleep(2)
                            video_file = client.files.get(name=video_file.name)
                            
                        prompt = """
                        សូមស្ដាប់សំឡេងក្នុងវីដេអូនោះ រួចសរសេរជាស្គ្រីបសាច់រឿងជាភាសាខ្មែរដែលមានដាក់កាលកំណត់ពេល (Timestamps) ក្នុងទម្រង់បែបនេះឱ្យបានត្រឹមត្រូវ:
                        [00:00 - 00:05] អត្ថបទនិយាយ...
                        [00:05 - 00:10] អត្ថបទនិយាយ...
                        សូមចេញលទ្ធផលជា Timestamps និងអត្ថបទសុទ្ធសាធសម្រាប់យកទៅធ្វើ Voiceover។
                        """
                        
                        response = client.models.generate_content(
                            model='gemini-3.8-flash',
                            contents=[video_file, prompt]
                        )
                        st.session_state.script_input = response.text
                        
                        os.remove(tfile_temp.name)
                        client.files.delete(name=video_file.name)
                        
                        st.success("🎉 ទាញយក និងបកប្រែស្គ្រីបអូតូបានជោគជ័យ!")
                    except Exception as e:
                        st.error(f"មានបញ្ហាក្នុងការទាញយកស្គ្រីបពី Gemini: {e}")

        if st.session_state.get("script_input"):
            st.text_area(
                "📋 ស្គ្រីបដែលបានបង្កើត (អាចកែសម្រួលបានបើចង់):",
                value=st.session_state.script_input,
                height=250,
                key="script_textarea_main"
            )

# -------------------------------------------------------------
# 2. ផ្ទាំងសំឡេង និងបញ្ចូលសំឡេងលើវីដេអូ (Full Dubbing)
# -------------------------------------------------------------
with tab_audio:
    st.subheader("🎙️ បញ្ចូលសំឡេង AI លើវីដេអូពេញ")
    
    voice_type = st.radio("សំឡេងនិយាយ:", ("👩 ស្រី (Sreymom)", "👨 ប្រុស (Piseth)"), key="voice_type_radio")
    selected_voice = "km-KH-SreymomNeural" if "ស្រី" in voice_type else "km-KH-PisethNeural"
    
    st.markdown("---")
    st.session_state.script_input = st.text_area(
        "បញ្ចូល Timestamps និងអត្ថបទ (ទម្រង់: [00:00 - 00:05] សួស្តី...):",
        value=st.session_state.script_input,
        height=180,
        key="audio_tab_script_textarea"
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

    if st.button("🎬 ចាប់ផ្តើមបញ្ចូលសំឡេង AI ចូលវីដេអូ", key="start_dubbing_btn"):
        script_text = st.session_state.script_input
        uploaded_video_file = st.session_state.get("uploaded_video", None)
        
        if not script_text.strip():
            st.warning("⚠️ សូមបង្កើត ឬបញ្ចូលស្គ្រីបជាមុនសិន!")
        elif not uploaded_video_file:
            st.warning("⚠️ សូម Upload វីដេអូនៅផ្ទាំងទី ១ ជាមុនសិន!")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                dialogues = parse_timestamps_video(script_text)
                if not dialogues:
                    st.error("❌ ទម្រង់ Timestamps មិនត្រឹមត្រូវទេ។ (ឧទាហរណ៍: [00:00 - 00:05] អត្ថបទ)")
                else:
                    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                    uploaded_video_file.seek(0)
                    tfile.write(uploaded_video_file.read())
                    tfile.close()
                    
                    status_text.info("🎬 កំពុងបង្កើតសំឡេង AI...")
                    video_clip = VideoFileClip(tfile.name)
                    audio_clips = []
                    
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
                    
                    status_text.info("🔄 កំពុងចងក្រងវីដេអូចុងក្រោយ...")
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
                        
                    status_text.success("🎉 បញ្ចូលសំឡេង AI រួចរាល់ជាស្រេច!")
            except Exception as e:
                st.error(f"មានបញ្ហាកើតឡើង: {e}")

# -------------------------------------------------------------
# 3. ផ្ទាំងទាញយកលទ្ធផល
# -------------------------------------------------------------
with tab_download:
    st.subheader("📥 ទាញយកវីដេអូចុងក្រោយ")
    if st.session_state.get("final_video_bytes"):
        st.video(st.session_state.final_video_bytes)
        st.download_button(
            label="📥 ទាញយកវីដេអូពេញ (.mp4)",
            data=st.session_state.final_video_bytes,
            file_name="khmer_ai_dubbed_video.mp4",
            mime="video/mp4",
            key="download_btn_final"
        )
    else:
        st.info("មិនទាន់មានវីដេអូទេ! សូមបំពេញដំណើរការនៅផ្ទាំងមុនៗសិន។")
                                
