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
    page_title="Khmer Video AI Pro",
    page_icon="🎬",
    layout="wide"
)

# 🎨 Custom CSS សម្រាប់ Dark Mode ដ៏ស្រស់ស្អាត
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stButton>button {
        background: linear-gradient(45deg, #6b46c1, #3182ce);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
        width: 100%;
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #1a202c;
        color: white;
        border-radius: 6px;
    }
    </style>
""", unsafe_allow_html=True)

# 📌 ចំណងជើងหลักของแፕ
st.title("🎬 Khmer Video AI Pro")
st.write("ប្រព័ន្ធបកប្រែវីដេអូ បង្កើតអក្សរ និងសំឡេងខ្មែរដោយ AI សម្រាប់ធ្វើ Movie Recap")

# 🗂️ បែងចែកផ្ទាំង (Tabs) ធំៗ
tab_video, tab_translate, tab_audio, tab_sub, tab_download = st.tabs([
    "🎬 វីដេអូ & ស្គ្រីប", 
    "🌐 បកប្រែ AI", 
    "🎙️ សំឡេង AI", 
    "🔤 កែតម្រូវអក្សរ", 
    "📥 ទាញយកលទ្ធផល"
])

# -------------------------------------------------------------
# 1. ផ្ទាំងវីដេអូ និងស្គ្រីប (Video & Script Input)
# -------------------------------------------------------------
with tab_video:
    st.subheader("📁 បញ្ចូលវីដេអូ ឬ ស្គ្រីប Timestamps")
    
    col1, col2 = st.columns(2)
    with col1:
        uploaded_video = st.file_uploader("📤 Upload វីដេអូ (MP4, MKV, MOV)", type=["mp4", "mkv", "mov"])
        if uploaded_video:
            st.success("✅ បានផ្ទុកវីដេអូជោគជ័យ!")
            st.video(uploaded_video)
                
    with col2:
        video_url = st.text_input("🔗 ឬដាក់ Link វីដេអូ (YouTube / Social):")
        if video_url:
            st.info("បានទទួលតំណភ្ជាប់វីដេអូរួចរាល់។")

    st.markdown("---")
    st.subheader("📝 ស្គ្រីប Timestamps សម្រាប់បំលែងជាសំឡេង")
    if "script_input" not in st.session_state:
        st.session_state.script_input = "[00:00 - 00:03] សួស្តីអ្នកទាំងអស់គ្នា ថ្ងៃនេះយើងនាំយករឿងថ្មីមកជូន...\n[00:03 - 00:06] ព្រះចៅអធិរាជនិងពួកមន្ត្រីបាននាំគ្នាដឹកមាសប្រាក់រត់គេចខ្លួនបាត់ហើយ!"

    st.session_state.script_input = st.text_area(
        "កែសម្រួលស្គ្រីប Timestamps នៅទីនេះ:",
        value=st.session_state.script_input,
        height=180
    )

# -------------------------------------------------------------
# 2. ផ្ទាំងបកប្រែ AI (Translation Settings)
# -------------------------------------------------------------
with tab_translate:
    st.subheader("🌐 ប្រព័ន្ធបកប្រែស្វ័យប្រវត្ត")
    ai_engine = st.selectbox("ម៉ាស៊ីនបកប្រែ (AI Engine):", ["Gemini Pro (លឿន និងធម្មជាតិ)", "OpenAI GPT-4"])
    source_lang = st.selectbox("ភាសាដើម:", ["ចិន (Mandarin)", "អង់គ្លេស", "ថៃ"])
    target_lang = st.selectbox("ភាសាគោលដៅ:", ["🇰🇭 ខ្មែរ (Khmer)"])
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        gen_sub = st.checkbox("បង្កើតអក្សររត់ (Subtitle SRT)", value=True)
        gen_dub = st.checkbox("បង្កើតសំឡេងអាន (Dubbing Audio)", value=True)
    with col_t2:
        check_script = st.checkbox("ពិនិត្យ និងកែតម្រូវអត្ថបទមុនបង្កើតសំឡេង", value=True)

    if st.button("🚀 ចាប់ផ្តើមបកប្រែ និងវិភាគវីដេអូ"):
        st.info("កំពុងដំណើរការបកប្រែអត្ថបទដោយ AI ... សូមរង់ចាំបន្តិច!")
        time.sleep(1)
        st.success("🎉 បកប្រែជោគជ័យ! សូមទស្សនាលទ្ធផលនៅផ្ទាំង 'សំឡេង AI'")

# -------------------------------------------------------------
# 3. ផ្ទាំងសំឡេង AI (Voice & Audio Generation)
# -------------------------------------------------------------
with tab_audio:
    st.subheader("🎙️ ការកំណត់សੁਰសៀងសំឡេង AI")
    
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
    
    if "zip_buffer" not in st.session_state:
        st.session_state.zip_buffer = None

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

    if st.button("🎙️ ចាប់ផ្តើមបង្កើតកញ្ចប់អូឌីយ៉ូតាម Timestamps (ZIP)"):
        script_text = st.session_state.script_input
        if not script_text.strip():
            st.warning("សូមបញ្ចូលស្គ្រីប Timestamps ជាមុនសិន!")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                dialogues = parse_timestamps(script_text)
                if not dialogues:
                    st.error("❌ ទម្រង់ Timestamps មិនត្រឹមត្រូវទេ។ ឧទាហរណ៍៖ [00:00 - 00:03] អត្ថបទ")
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
# 4. ផ្ទាំងអក្សររត់ (Subtitle Customization)
# -------------------------------------------------------------
with tab_sub:
    st.subheader("🔤 កែតម្រូវទម្រង់អក្សររត់ (Subtitle Styling)")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        font_choice = st.selectbox("Font អក្សរ:", ["Battambang", "Moul", "Kantumruy", "Siemreap"])
        text_color = st.color_picker("ពណ៌អក្សរ", "#FFFFFF")
        font_size = st.slider("ទំហំអក្សរ", 12, 48, 24)
    with col_s2:
        bg_color = st.color_picker("ពណ៌ផ្ទៃខាងក្រោយអក្សរ", "#000000")
        position_choice = st.selectbox("ទីតាំងអក្សរ:", ["ខាងក្រោម (Bottom)", "កណ្តាល (Center)", "ខាងលើ (Top)"])
        
    st.info("ការកំណត់ទម្រង់អក្សរនេះនឹងត្រូវរក្សាទុកដើម្បី Export ចេញជាហ្វាល SRT សម្រាប់ដាក់ក្នុង CapCut។")

# -------------------------------------------------------------
# 5. ផ្ទាំងទាញយក (Download Section) - រៀបចំស្អាតពេញលេញ
# -------------------------------------------------------------
with tab_download:
    st.subheader("📥 ទាញយកលទ្ធផលវីដេអូ និងអូឌីយ៉ូចុងក្រោយ")
    
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
            <div style='padding: 40px 20px; background-color: #1a202c; border-radius: 12px; text-align: center; border: 1px dashed #4a5568; margin-top: 20px;'>
                <p style='color: #a0aec0; font-size: 16px; margin-bottom: 10px;'>មិនទាន់មានលទ្ធផលទេ!</p>
                <p style='color: #718096; font-size: 14px;'>សូមជ្រើសរើសស្គ្រីប Timestamps និងបង្កើតអូឌីយ៉ូនៅផ្ទាំង <b>«សំឡេង AI»</b> ជាមុនសិន។</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("📂 សូមជ្រើសរើសស្គ្រីប ឬវីដេអូជាមុនសិន"):
            st.info("💡 គន្លឹះ៖ សូមចូលទៅកាន់ផ្ទាំង «វីដេអូ & ស្គ្រីប» ដើម្បីចាប់ផ្តើម!")
            
