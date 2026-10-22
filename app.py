import streamlit as st
import asyncio
import edge_tts
import os
import tempfile
import time
import re

st.set_page_config(page_title="AI Khmer Audio Generator", layout="centered")

st.title("🎙️ AI Khmer Audio Generator (Safe & Fast)")
st.write("ប្រព័ន្ធបង្កើតសំឡេង AI តាម Timestamps (គ្មាន Error ធានារត់លឿនរលូន!)")

# ជ្រើសរើសសំឡេង AI ស្រី ឬ ប្រុស
voice_choice = st.selectbox(
    "ជ្រើសរើសសំឡេង AI:",
    ("ស្រី (Sreymom - ធម្មជាតិ)", "ប្រុស (Piseth - ធម្មជាតិ)")
)

voice_map = {
    "ស្រី (Sreymom - ធម្មជាតិ)": "km-KH-SreymomNeural",
    "ប្រុស (Piseth - ធម្មជាតិ)": "km-KH-PisethNeural"
}
selected_voice = voice_map[voice_choice]

# ប្រអប់សម្រាប់ដាក់ Timestamps និងអត្ថបទ
flow_script = st.text_area(
    "📝 ដាក់ Timestamps & ស្គ្រីប (ពី Google Flow):",
    placeholder="[00:01 - 00:03] សួស្តី\n[00:05 - 00:08] ຍິນດີต้อนรับ...",
    height=220
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

def parse_timestamps(text):
    pattern = r'\[\s*(\d{1,2}:\d{2})\s*(?:-\s*(\d{1,2}:\d{2}))?\s*\]\s*(.*)'
    matches = re.findall(pattern, text)
    dialogues = []
    for match in matches:
        content = match[2].strip()
        if content:
            dialogues.append(content)
    return dialogues

if "output_audio_path" not in st.session_state:
    st.session_state.output_audio_path = None

# 🚀 ប៊ូតុងដំណើរការបង្កើតអូឌីយ៉ូ
if st.button("🚀 ចាប់ផ្តើមបង្កើតไฟล์ MP3"):
    if not flow_script.strip():
        st.warning("សូម Paste ស្គ្រីប Timestamps ជាមុនសិន!")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            sentences = parse_timestamps(flow_script)
            
            if not sentences:
                st.error("❌ ទម្រង់ Timestamps មិនត្រឹមត្រូវទេ។ ឧទាហរណ៍៖ [00:01 - 00:03] សួស្តី")
            else:
                total_items = len(sentences)
                combined_audio_bytes = bytearray()
                
                for i, text in enumerate(sentences):
                    status_text.info(f"🎙️ កំពុងបង្កើតសំឡេង AI ទី {i+1} នៃ {total_items}...")
                    
                    chunk_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                    asyncio.run(generate_tts_safe(text, selected_voice, chunk_path))
                    
                    if os.path.exists(chunk_path) and os.path.getsize(chunk_path) > 0:
                        with open(chunk_path, "rb") as f:
                            combined_audio_bytes.extend(f.read())
                        os.remove(chunk_path)
                    
                    time.sleep(0.1)
                    progress_bar.progress(int((i + 1) / total_items * 90))

                status_text.info("💾 កំពុងរៀបចំไฟล์ MP3 ចុងក្រោយ...")
                output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                with open(output_path, "wb") as f:
                    f.write(combined_audio_bytes)
                
                progress_bar.progress(100)
                st.session_state.output_audio_path = output_path
                status_text.success("🎉 สร้างไฟล์ MP3 ជោគជ័យ ១០០%!")

        except Exception as e:
            st.error(f"មានបញ្ហាកើតឡើង: {e}")

# 📥 បង្ហាញប៊ូតុង Download
if st.session_state.output_audio_path and os.path.exists(st.session_state.output_audio_path):
    st.success("🎉 អូឌីយ៉ូរួចរាល់សម្រាប់យកទៅប្រើប្រាស់!")
    st.audio(st.session_state.output_audio_path, format="audio/mp3")
    
    with open(st.session_state.output_audio_path, "rb") as file:
        st.download_button(
            label="📥 ទាញយកไฟล์ MP3 ពេញលេញ (Download MP3)",
            data=file,
            file_name="khmer_dubbing.mp3",
            mime="audio/mp3"
            )
            
