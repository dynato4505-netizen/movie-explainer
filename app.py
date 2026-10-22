import streamlit as st
import asyncio
import edge_tts
import os
import tempfile
import time
import re
from pydub import AudioSegment

st.set_page_config(page_title="AI Khmer Audio Generator Pro", layout="centered")

st.title("🎙️ AI Khmer Audio Generator Pro (Full Audio)")
st.write("ប្រព័ន្ធបង្កើតសំឡេង AI តាម Timestamps รวมជាไฟล์ MP3 ពេញលេញ!")

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

def time_to_milliseconds(time_str):
    parts = time_str.split(':')
    if len(parts) == 2:
        minutes = int(parts[0])
        seconds = float(parts[1])
        return int((minutes * 60 + seconds) * 1000)
    elif len(parts) == 3:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return int((hours * 3600 + minutes * 60 + seconds) * 1000)
    return 0

def parse_timestamps(text):
    pattern = r'\[\s*(\d{1,2}:\d{2})\s*(?:-\s*(\d{1,2}:\d{2}))?\s*\]\s*(.*)'
    matches = re.findall(pattern, text)
    dialogues = []
    for match in matches:
        start_str = match[0]
        end_str = match[1] if match[1] else match[0]
        content = match[2].strip()
        
        start_ms = time_to_milliseconds(start_str)
        end_ms = time_to_milliseconds(end_str)
        if end_ms <= start_ms:
            end_ms = start_ms + 3000
            
        if content:
            dialogues.append({
                "start": start_ms,
                "end": end_ms,
                "text": content
            })
    return dialogues

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

if "output_audio_path" not in st.session_state:
    st.session_state.output_audio_path = None

# 🚀 ប៊ូតុងដំណើរការបង្កើតអូឌីយ៉ូ
if st.button("🚀 ចាប់ផ្តើមបង្កើតไฟล์អូឌីយ៉ូពេញលេញ (Generate Full MP3)"):
    if not flow_script.strip():
        st.warning("សូម Paste ស្គ្រីប Timestamps ជាមុនសិន!")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            dialogues = parse_timestamps(flow_script)
            
            if not dialogues:
                st.error("❌ ទម្រង់ Timestamps មិនត្រឹមត្រូវទេ។ ឧទាហរណ៍៖ [00:01 - 00:03] សួស្តី")
            else:
                total_items = len(dialogues)
                final_audio = AudioSegment.silent(duration=0)
                temp_files = []
                
                # រត់បង្កើតសំឡេងម្ដង១ តាមប្រយោគ
                for i, item in enumerate(dialogues):
                    status_text.info(f"🎙️ កំពុងបង្កើតសំឡេង AI ទី {i+1} នៃ {total_items}...")
                    
                    chunk_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                    temp_files.append(chunk_path)
                    
                    asyncio.run(generate_tts_safe(item["text"], selected_voice, chunk_path))
                    
                    if os.path.exists(chunk_path) and os.path.getsize(chunk_path) > 0:
                        segment = AudioSegment.from_mp3(chunk_path)
                        
                        # គណនាទីតាំងម៉ោងឱ្យត្រូវចំ Timestamps ព្រមទាំងเว้นចន្លោះស្ងាត់
                        current_len = len(final_audio)
                        if item["start"] > current_len:
                            final_audio += AudioSegment.silent(duration=item["start"] - current_len)
                        
                        final_audio += segment
                    
                    time.sleep(0.2)
                    progress_bar.progress(int((i + 1) / total_items * 90))

                status_text.info("💾 កំពុង Export ជាไฟล์អូឌីយ៉ូចុងក្រោយ...")
                output_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                final_audio.export(output_audio_path, format="mp3")
                
                progress_bar.progress(100)
                st.session_state.output_audio_path = output_audio_path
                status_text.success("🎉 สร้างไฟล์អូឌីយ៉ូពេញលេញជោគជ័យ ១០០%!")
                
                for p in temp_files:
                    if os.path.exists(p): os.remove(p)

        except Exception as e:
            st.error(f"មានបញ្ហាកើតឡើង: {e}")

# 📥 បង្ហាញប៊ូតុង Download អូឌីយ៉ូពេញលេញ
if st.session_state.output_audio_path and os.path.exists(st.session_state.output_audio_path):
    st.success("🎉 អូឌីយ៉ូពេញលេញរួចរាល់សម្រាប់យកไปប្រើប្រាស់!")
    st.audio(st.session_state.output_audio_path, format="audio/mp3")
    
    with open(st.session_state.output_audio_path, "rb") as file:
        st.download_button(
            label="📥 ទាញយកไฟล์អូឌីយ៉ូពេញលេញ (Download Full MP3)",
            data=file,
            file_name="khmer_full_dubbed.mp3",
            mime="audio/mp3"
    )
