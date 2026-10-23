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
    page_title="Khmer Video AI - បកប្រែវីដេអូ និងបង្កើតអក្សរ/សំឡេងខ្មែរ",
    page_icon="🎬",
    layout="wide"
)

# 🎨 Custom CSS សម្រាប់ Dark Mode ដ៏ប្រណិត និងស៊ីគ្នាជាមួយ UI ក្នុងរូប
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

# 📌 ចំណងជើងหลักของแอป
st.markdown("<h2 style='text-align: center; color: #a78bfa;'>🎬 Khmer Video AI</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94a3b8;'>បកប្រែវីដេអូ និងបង្កើតអក្សរ/សំឡេងខ្មែរ ដោយ AI</p>", unsafe_allow_html=True)

# 🗂️ បែងចែកផ្ទាំង (Tabs) តាមស្តង់ដារកម្មវិធីថ្មី
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

# -------------------------------------------------------------
# 1. ផ្ទាំងវីដេអូ (Video Input & Resolution)
# -------------------------------------------------------------
with tab_video:
    st.subheader("🎬 បញ្ចូលវីដេអូ ឬតំណភ្ជាប់ (Link)")
    
    input_method = st.radio("ជ្រើសរើសវិធីសាស្ត្របញ្ចូល:", ["📤 Upload", "🔗 Link"], horizontal=True)
    
    if input_method == "📤 Upload":
        uploaded_video = st.file_uploader("បន្ថែមវីដេអូ (ជ្រើសរើសបានច្រើន)", type=["mp4", "mov", "mkv", "avi", "webm"])
        if uploaded_video:
            st.success("✅ បានផ្ទុកវីដេអូជោគជ័យ!")
            st.video(uploaded_video)
    else:
        video_url = st.text_input("🔗 ដាក់ Link វីដេអូ (YouTube, TikTok, ฯลฯ):")
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
    opt_sub = st.checkbox("បង្កើតអក្សររက်ខ្មែរ (Subtitle)", value=True)
    opt_dub = st.checkbox("បង្កើតសំឡេងអានខ្មែរ (Dubbing)", value=False)
    opt_srt = st.checkbox("ទាញយកអក្សรជាឯកសារ (SRT)", value=False)
    opt_book = st.checkbox("📖 ម៉ូដនិទានរឿង (កែអត្ថបទឱ្យល្វន់ដូចអ្នកនិទាន)", value=False)
    opt_check = st.checkbox("✏️ ពិនិត្យ និងកែអត្ថបទមុនបង្កើតសំឡេង", value=True)

# -------------------------------------------------------------
# 3. ផ្ទាំងសំឡេង AI (Voice & Audio Settings)
# -------------------------------------------------------------
with tab_audio:
    st.subheader("🎙️ ជ្រើសរើសសំឡេងនិយាយ (Voice Dubbing)")
    
    voice_type = st.radio(
        "សំឡេងនិយាយ:",
        ("👩 ស្រី (Sreymom)", "👨 ប្រុស (Piseth)")
    )
    
    selected_voice = "km-KH-SreymomNeural" if "ស្រី" in voice_type else "km-KH-PisethNeural"

    st.markdown("---")
    st.checkbox("🎭 ឱ្យ AI ប្ដូរសំឡេងប្រុស/ស្រី តាមអ្នកនិយាយក្នុងវីដេអូ", value=True)
    st.checkbox("🤪 ដាក់អារម្មណ៍ក្នុងសំឡេង (ខឹង ក្រៀមក្រំ សប្បាយ កี้យ)", value=True)
    st.checkbox("🔊 រ្សាវសំឡេងដើមក្នុងវីដេអូ (ពេលមាន Dubbing)", value=False)

    st.markdown("---")
    st.subheader("📝 ស្គ្រីប Timestamps សម្រាប់បំលែងជាអូឌីយ៉ូ")
    st.session_state.script_input = st.text_area(
        "បញ្ចូលអត្ថបទ ឬ Timestamps (ឧទាហរណ៍: [00:00 - 00:03] សួស្តី...):",
        value=st.session_state.script_input,
        height=140
    )

    # Edge-TTS Function
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
                dialogues.append({"time_label": filename_safe, "text": content})
        return dialogues

    if st.button("🎙️ ចាប់ផ្តើមបង្កើតកញ្ចប់អូឌីយ៉ូ ZIP"):
        script_text = st.session_state.script_input
        if not script_text.strip():
            st.warning("⚠️ សូមបញ្ចូលស្គ្រីប ឬ Timestamps ជាមុនសិន!")
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
                            status_text.info(f"🎙️ កំពុងបង្កើតសំឡេងទី {i+1} នៃ {total_items}...")
                            chunk_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                            asyncio.run(generate_tts_safe(item["text"], selected_voice, chunk_path))
                            
                            if os.path.exists(chunk_path) and os.path.getsize(chunk_path) > 0:
                                arcname = f"{item['time_label']}.mp3"
                                zipf.write(chunk_path, arcname=arcname)
                                os.remove(chunk_path)
                            
                            time.sleep(0.05)
                            progress_bar.progress(int((i + 1) / total_items * 100))

                    st.session_state.zip_buffer = zip_io.getvalue()
                    status_text.success("🎉 បង្កើតកញ្ចប់អូឌីយ៉ូ ZIP ជោគជ័យ ១០០%!")
            except Exception as e:
                st.error(f"មានបញ្ហាកើតឡើង: {e}")

# -------------------------------------------------------------
# 4. ផ្ទាំងអក្សរ (Subtitle Styling & Font)
# -------------------------------------------------------------
with tab_sub:
    st.subheader("🔤 ការកំណត់រចនាប័ទ្មអក្សរ Subtitle")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        font_choice = st.selectbox("Font អក្សរ:", ("Battambang", "Siemreap", "Moul", "Bayon"))
    with col_s2:
        color_choice = st.selectbox("ពណ៌អក្សរ:", ("ស (White)", "លឿង (Yellow)", "ខៀវ (Blue)"))

    col_s3, col_s4 = st.columns(2)
    with col_s3:
        bg_choice = st.selectbox("ផ្ទៃខាងក្រោយអក្សរ (Background):", ("គ្មាន", "ខ្មៅស្រទន់", "ពាក់កណ្តាលតម្លាភាព"))
    with col_s4:
        style_choice = st.selectbox("របៀបបង្ហាញអក្សរ:", ("ធម្មតា", "ដិត (Bold)", "មានគែមអក្សរ (Outline)"))

    font_size = st.slider("ទំហំអក្សរ (Font Size)", 14, 40, 22, 1)
    sub_count_line = st.slider("ចំនួនបន្ទាត់ក្នុងមួយផ្ទាំងអក្សរ", 1, 3, 2, 1)

    st.markdown("📍 **ទីតាំងអក្សរនៅលើវីដេអូ:**")
    st.markdown("""
        <div style='text-align: center; color: #a78bfa;'>
            [ ↖️ លើឆ្វេង ] &nbsp; [ ⬆️ កណ្តាលលើ ] &nbsp; [ ↗️ លើស្តាំ ]<br>
            [ ⬅️ កណ្តាលឆ្វេង ] &nbsp; [ 🔘 កណ្តាលចំ ] &nbsp; [ ➡️ កណ្តាលស្តាំ ]<br>
            [ ↙️ ក្រោមឆ្វេង ] &nbsp; [ ⬇️ ក្រោមចំ (ពេញនិយម) ] &nbsp; [ ↘️ ក្រោមស្តាំ ]
        </div>
    """, unsafe_allow_html=True)

# -------------------------------------------------------------
# 5. ផ្ទាំងទាញយក (Download Section)
# -------------------------------------------------------------
with tab_download:
    st.subheader("📥 ទាញយកលទ្ធផលវីដេអូ ឬអូឌីយ៉ូ")
    
    if st.session_state.zip_buffer:
        st.success("🎉 កញ្ចប់អូឌីយ៉ូតាម Timestamps រួចរាល់សម្រាប់ទាញយកហើយ!")
        st.download_button(
            label="📥 ទាញយកកញ្ចប់អូឌីយ៉ូទាំងអស់ (.ZIP)",
            data=st.session_state.zip_buffer,
            file_name="khmer_movie_audio_chunks.zip",
            mime="application/zip"
        )
    else:
        st.markdown("""
            <div style='padding: 40px 20px; background-color: #1e293b; border-radius: 12px; text-align: center; border: 1px dashed #475569; margin-top: 20px;'>
                <p style='color: #cbd5e1; font-size: 16px; margin-bottom: 10px;'>មិនទាន់មានលទ្ធផលទេ!</p>
                <p style='color: #94a3b8; font-size: 14px;'>សូមបំពេញស្គ្រីប និងចុចបង្កើតអូឌីយ៉ូនៅផ្ទាំង <b>«សំឡេង»</b> ជាមុនសិន។</p>
            </div>
        """, unsafe_allow_html=True)

# -------------------------------------------------------------
# 6. ផ្ទាំងរីដេអូម (Movie Recap History)
# -------------------------------------------------------------
with tab_recap:
    st.subheader("🎞️ ប្រវត្តិរីដេអូម (Movie Recap History)")
    st.markdown("<p style='color: #94a3b8;'>វីដេអូដែលបានបង្កើតរួចនឹងត្រូវបានរក្សាទុកដោយស្វ័យប្រវត្ត ហើយអ្នកប្រើប្រាស់អាចមើល/ទាញយកបាន។</p>", unsafe_allow_html=True)
    
    if not st.session_state.recap_history:
        st.markdown("""
            <div style='padding: 40px 20px; background-color: #1e293b; border-radius: 12px; text-align: center; border: 1px dashed #475569; margin-top: 20px;'>
                <p style='color: #cbd5e1; font-size: 16px;'>មិនទាន់មានវីដេអូក្នុងរីដេអូមទេ។ បង្កើតវីដេអូថ្មី វានឹងបង្ហាញនៅទីនេះដោយស្វ័យប្រវត្តិ។</p>
            </div>
        """, unsafe_allow_html=True)
    ue
