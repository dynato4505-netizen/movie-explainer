import streamlit as st
import asyncio
import edge_tts
import os
import tempfile
import re
import io
from moviepy.editor import VideoFileClip, AudioFileClip

# 🌟 កំណត់ទម្រង់ទំព័រឱ្យធំទូលាយស្អាត (Wide Mode)
st.set_page_config(
    page_title="Khmer Video AI - កាត់វីដេអូ និងបញ្ចូលសំឡេង AI",
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
if "uploaded_video" not in st.session_state:
    st.session_state.uploaded_video = None
if "generated_clips" not in st.session_state:
    st.session_state.generated_clips = []
if "recap_history" not in st.session_state:
    st.session_state.recap_history = []

# -------------------------------------------------------------
# 1. ផ្ទាំងវីដេអូ (Video Input)
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
# 3. ផ្ទាំងសំឡេង និងកាត់វីដេអូ (Direct Video Output & Preview)
# -------------------------------------------------------------
with tab_audio:
    st.subheader("🎙️ កាត់វីដេអូ និងបញ្ចូលសំឡេង AI ជាមួយគ្នា")
    
    voice_type = st.radio("សំឡេងនិយាយ:", ("👩 ស្រី (Sreymom)", "👨 ប្រុស (Piseth)"))
    selected_voice = "km-KH-SreymomNeural" if "ស្រី" in voice_type else "km-KH-PisethNeural"

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
                    "end_sec": time_to_seconds(end_str),
                    "time_label": f"[{start_str}-{end_str}]".replace(":", "-"),
                    "text": content
                })
        return dialogues

    if st.button("🎬 ចាប់ផ្តើមកាត់ និងបញ្ចូលសំឡេងទៅវីដេអូ (.mp4)"):
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
                    
                    total_items = len(dialogues)
                    st.session_state.generated_clips = []
                    
                    for i, item in enumerate(dialogues):
                        status_text.info(f"🎬 កំពុងកាត់ និងបញ្ចូលសំឡេងវីដេអូឃ្លីបទី {i+1} នៃ {total_items}...")
                        
                        audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                        asyncio.run(generate_tts_safe(item["text"], selected_voice, audio_path))
                        
                        output_video_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                        try:
                            video_clip = VideoFileClip(tfile.name).subclip(item["start_sec"], item["end_sec"])
                            audio_clip = AudioFileClip(audio_path)
                            final_clip = video_clip.set_audio(audio_clip)
                            final_clip.write_videofile(output_video_path, codec="libx264", audio_codec="aac", logger=None)
                            
                            if os.path.exists(output_video_path) and os.path.getsize(output_video_path) > 0:
                                clip_name = f"video_clip_{i+1}_{item['time_label']}.mp4"
                                with open(output_video_path, "rb") as vf:
                                    clip_bytes = vf.read()
                                st.session_state.generated_clips.append({
                                    "name": clip_name,
                                    "bytes": clip_bytes,
                                    "time": item['time_label']
                                })
                                
                            video_clip.close()
                            audio_clip.close()
                            final_clip.close()
                        except Exception as sub_e:
                            st.warning(f"រំលងវីដេអូទី {i+1} ៖ {sub_e}")
                        
                        if os.path.exists(audio_path): os.remove(audio_path)
                        if os.path.exists(output_video_path): os.remove(output_video_path)
                        
                        progress_bar.progress(int((i + 1) / total_items * 100))
                    
                    if os.path.exists(tfile.name):
                        os.remove(tfile.name)

                    status_text.success("🎉 កាត់វីដេអូ និងបញ្ចូលសំឡេង AI រួចរាល់! លទ្ធផលបង្ហាញនៅខាងក្រោម៖")
            except Exception as e:
                st.error(f"មានបញ្ហាកើតឡើង: {e}")

    # 📺 បង្ហាញវីដេអូឃ្លីប និងប៊ូតុង Download ផ្ទាល់
    if st.session_state.get("generated_clips"):
        st.markdown("---")
        st.write("### 🎬 វីដេអូឃ្លីបដែលបានកាត់រួច (មើល និងទាញយកទីនេះ):")
        for idx, clip in enumerate(st.session_state.generated_clips):
            st.markdown(f"**ឃ្លីបទី {idx+1} — ម៉ោង: {clip['time']}**")
            st.video(clip["bytes"])
            st.download_button(
                label=f"📥 ទាញយកឃ្លីបទី {idx+1} (.mp4)",
                data=clip["bytes"],
                file_name=clip["name"],
                mime="video/mp4",
                key=f"audio_tab_dl_{idx}"
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
    st.subheader("📥 ទាញយកលទ្ធផលវីដេអូ")
    if st.session_state.get("generated_clips"):
        for idx, clip in enumerate(st.session_state.generated_clips):
            st.markdown(f"**ឃ្លីបទី {idx+1} — ម៉ោង: {clip['time']}**")
            st.download_button(
                label=f"📥 ទាញយកឃ្លីបទី {idx+1} (.mp4)",
                data=clip["bytes"],
                file_name=clip["name"],
                mime="video/mp4",
                key=f"download_tab_dl_{idx}"
            )
            st.markdown("---")
    else:
        st.info("មិនទាន់មានលទ្ធផលវីដេអូទេ! សូមបំពេញ Timestamps នៅផ្ទាំង «សំឡេង» ជាមុនសិន។")

# -------------------------------------------------------------
# 6. ផ្ទាំងរីដេអូម (Movie Recap History)
# -------------------------------------------------------------
with tab_recap:
    st.subheader("🎞️ ប្រវត្តិរីដេអូម")
    st.markdown("<p style='color: #94a3b8;'>វីដេអូដែលបានបង្កើតរួចនឹងត្រូវបានរក្សាទុកនៅទីនេះ។</p>", unsafe_allow_html=True)
