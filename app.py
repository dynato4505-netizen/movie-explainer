import streamlit as st
import asyncio
import edge_tts
import os
import tempfile
import time
import re
import zipfile
import io

# 🌟 កំណត់ទម្រង់ទំព័រឱ្យធំទូលាយស្អាត (Wide Mode)
st.set_page_config(
    page_title="Khmer Auto Caption & Dubbing Pro",
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
    </style>
""", unsafe_allow_html=True)

# 📌 ចំណងជើងหลัก
st.markdown("<h2 style='text-align: center; color: #a78bfa;'>🎬 Khmer Auto Caption & Dubbing Pro</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94a3b8;'>ប្រព័ន្ធបង្កើតសំឡេង AI ខ្មែរតាម Timestamps សម្រាប់ Movie Recap</p>", unsafe_allow_html=True)

# 🗂️ បែងចែកផ្ទាំង (Tabs)
tab_video, tab_audio, tab_download = st.tabs([
    "📁 ១. វីដេអូ & ស្គ្រីប", 
    "🎙️ ២. សំឡេង AI", 
    "📥 ៣. ទាញយកលទ្ធផល"
])

if "script_input" not in st.session_state:
    st.session_state.script_input = ""
if "zip_buffer" not in st.session_state:
    st.session_state.zip_buffer = None

# -------------------------------------------------------------
# 1. ផ្ទាំងវីដេអូ & ស្គ្រីប
# -------------------------------------------------------------
with tab_video:
    st.subheader("📁 ផ្ទុកវីដេអូ និងបញ្ចូលស្គ្រីប Timestamps")
    
    col1, col2 = st.columns(2)
    with col1:
        uploaded_video = st.file_uploader("📤 Upload វីដេអូ (MP4, MKV, MOV)", type=["mp4", "mkv", "mov"])
        if uploaded_video:
            st.success("✅ បានផ្ទុកវីដេអូជោគជ័យ!")
            st.video(uploaded_video)
                
    with col2:
        video_url = st.text_input("🔗 ឬដាក់ Link វីដេអូ:")
        if video_url:
            st.info("បានទទួលតំណភ្ជាប់វីដេអូរួចរាល់។")

    st.markdown("---")
    st.subheader("📝 ស្គ្រីប Timestamps")
    st.session_state.script_input = st.text_area(
        "បញ្ចូលស្គ្រីប Timestamps នៅទីនេះ (ឧទាហរណ៍: [00:00 - 00:03] សួស្តី...):",
        value=st.session_state.script_input,
        height=160
    )

# -------------------------------------------------------------
# 2. ផ្ទាំងសំឡេង AI
# -------------------------------------------------------------
with tab_audio:
    st.subheader("🎙️ ការកំណត់សំឡេង AI ខ្មែរ")
    
    voice_choice = st.selectbox(
        "ជ្រើសរើសសំឡេង AI:",
        ("ស្រី (Sreymom - ធម្មជាតិ)", "ប្រុស (Piseth - ធម្មជាតិ)")
    )
    
    voice_map = {
        "ស្រី (Sreymom - ធម្មជាតិ)": "km-KH-SreymomNeural",
        "ប្រុស (Piseth - ធម្មជាតិ)": "km-KH-PisethNeural"
    }
    selected_voice = voice_map[voice_choice]

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        speed_val = st.slider("ល្បឿនអាន (Speed Rate)", -30, 30, 0, 5)
        rate_str = f"{speed_val:+d}%"
    with col_v2:
        pitch_val = st.slider("កម្រិតសੁਰសៀង (Pitch Hz)", -10, 10, 0, 1)
        pitch_str = f"{pitch_val:+d}Hz"

    st.markdown("---")

    async def generate_tts_safe(text, voice, output_path, rate, pitch):
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

    def parse_timestamps(text):
        pattern = r'\[\s*(\d{1,2}:\d{2})\s*(?:-\s*(\d{1,2}:\d{2}))?\s*\]\s*(.*)'
        matches = re.findall(pattern, text)
        dialogues = []
        for match in matches:
            start_str = match[0]
            end_str = match[1] if match[1] else match[0]
            content = match[2].strip()
            if content:
                filename_safe = f"[{start_str} - {end_str}]".replace(":", "-")
                dialogues.append({
                    "time_label": filename_safe,
                    "text": content
                })
        return dialogues

    if st.button("🎙️ ចាប់ផ្តើមបង្កើតកញ្ចប់អូឌីយ៉ូ ZIP តាម Timestamps"):
        script_text = st.session_state.script_input
        if not script_text.strip():
            st.warning("⚠️ សូមបញ្ចូលស្គ្រីប Timestamps នៅផ្ទាំងទី ១ ជាមុនសិន!")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                dialogues = parse_timestamps(script_text)
                if not dialogues:
                    st.error("❌ ទម្រង់ Timestamps មិនត្រឹមត្រូវទេ។ (ឧទាហរណ៍: [00:00 - 00:03] អត្ថបទ)")
                else:
                    total_items = len(dialogues)
                    zip_io = io.BytesIO()
                    
                    with zipfile.ZipFile(zip_io, mode='w', compression=zipfile.ZIP_DEFLATED) as zipf:
                        for i, item in enumerate(dialogues):
                            status_text.info(f"🎙️ កំពុងបង្កើតសំឡេងទី {i+1} នៃ {total_items} ({item['time_label']})...")
                            
                            chunk_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                            asyncio.run(generate_tts_safe(item["text"], selected_voice, chunk_path, rate_str, pitch_str))
                            
                            if os.path.exists(chunk_path) and os.path.getsize(chunk_path) > 0:
                                arcname = f"{item['time_label']}.mp3"
                                zipf.write(chunk_path, arcname=arcname)
                                os.remove(chunk_path)
                            
                            time.sleep(0.05)
                            progress_bar.progress(int((i + 1) / total_items * 90))

                    progress_bar.progress(100)
                    st.session_state.zip_buffer = zip_io.getvalue()
                    status_text.success("🎉 បង្កើតកញ្ចប់អូឌីយ៉ូ ZIP ជោគជ័យ ១០០%!")

            except Exception as e:
                st.error(f"មានបញ្ហាកើតឡើង: {e}")

# -------------------------------------------------------------
# 3. ផ្ទាំងទាញយក
# -------------------------------------------------------------
with tab_download:
    st.subheader("📥 ទាញយកកញ្ចប់អូឌីយ៉ូចុងក្រោយ")
    
    if st.session_state.zip_buffer:
        st.success("🎉 កញ្ចប់អូឌីយ៉ូតាម Timestamps រួចរាល់សម្រាប់ទាញយកហើយ!")
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="📥 ទាញយកកញ្ចប់អូឌីយ៉ូទាំងអស់ (Download Audio ZIP)",
            data=st.session_state.zip_buffer,
            file_name="khmer_movie_audio_chunks.zip",
            mime="application/zip"
        )
    else:
        st.markdown("""
            <div style='padding: 40px 20px; background-color: #1e293b; border-radius: 12px; text-align: center; border: 1px dashed #475569; margin-top: 20px;'>
                <p style='color: #cbd5e1; font-size: 16px; margin-bottom: 10px;'>មិនទាន់មានលទ្ធផលទេ!</p>
                <p style='color: #94a3b8; font-size: 14px;'>សូមបំពេញស្គ្រីប និងចុចបង្កើតអូឌីយ៉ូនៅផ្ទាំង <b>«សំឡេង AI»</b> ជាមុនសិន។</p>
            </div>
        """, unsafe_allow_html=True)
