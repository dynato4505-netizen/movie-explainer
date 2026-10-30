import streamlit as st
import asyncio
import edge_tts
import os
import tempfile
import time
import re
import cv2
from google import genai

# 🌟 កំណត់ទម្រង់ទំព័រឱ្យធំទូលាយស្អាត (Wide Mode)
st.set_page_config(
    page_title="Khmer Video AI - បកប្រែវីដេអូ និងបង្កើតអក្សរ/សំឡេងខ្មែរ",
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
st.markdown("<h2 style='text-align: center; color: #a78bfa;'>🎬 Khmer Video AI Pro</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94a3b8;'>បកប្រែវីដេអូ កាត់តកំណាត់ បង្កើតស្គ្រីប និងសំឡេងខ្មែរដោយ AI</p>", unsafe_allow_html=True)

# 🔑 Sidebar សម្រាប់ដាក់ Gemini API Key (AQ...)
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ ការកំណត់ Gemini API Key")
user_api_key = st.sidebar.text_input("🔑 បញ្ចូល API Key របស់អ្នក:", type="password", value="")

# 🗂️ បែងចែកផ្ទាំង (Tabs)
tab_video, tab_script, tab_split, tab_translate, tab_audio, tab_sub, tab_download, tab_recap = st.tabs([
    "🎬 វីដេអូ", 
    "📝 ស្គ្រីប AI",
    "✂️ កាត់វីដេអូ",
    "🌐 បកប្រែ", 
    "🎙️ សំឡេង", 
    "🔤 អក្សរ", 
    "📥 ទាញយក", 
    "🎞️ រីដេអូម"
])

# 🗄️ Session State Initialization
if "script_input" not in st.session_state:
    st.session_state.script_input = ""
if "uploaded_video_file" not in st.session_state:
    st.session_state.uploaded_video_file = None
if "single_audio_bytes" not in st.session_state:
    st.session_state.single_audio_bytes = None
if "split_zip_buffer" not in st.session_state:
    st.session_state.split_zip_buffer = None
if "recap_history" not in st.session_state:
    st.session_state.recap_history = []

# -------------------------------------------------------------
# 1. ផ្ទាំងវីដេអូ (Video Input)
# -------------------------------------------------------------
with tab_video:
    st.subheader("🎬 បញ្ចូលវីដេអូសម្រាប់កាត់ត និងសម្រាយ")
    
    uploaded_video = st.file_uploader("បន្ថែមវីដេអូ (MP4, MKV, MOV, AVI)", type=["mp4", "mov", "mkv", "avi", "webm"])
    if uploaded_video:
        st.session_state.uploaded_video_file = uploaded_video
        st.success("✅ បានផ្ទុកវីដេអូជោគជ័យ!")
        st.video(uploaded_video)

    st.markdown("---")
    st.subheader("📊 គុណភាពវីដេអូ (Resolution)")
    resolution = st.radio(
        "ជ្រើសរើសកម្រិតច្បាស់:",
        ("⚡ លឿន 480p", "✨ ល្អ 720p", "💎 ខ្ពស់ (ដើម)"),
        horizontal=True
    )

# -------------------------------------------------------------
# 2. ផ្ទាំងស្គ្រីប AI (Script Generator & Strict Khmer Format)
# -------------------------------------------------------------
with tab_script:
    st.subheader("📝 បង្កើតស្គ្រីបជាភាសាខ្មែរ និងកំណត់ពេលវេលាអូតូពី Gemini AI")
    st.markdown("<p style='color: #94a3b8;'>បញ្ចូលបញ្ជាដើម្បីឱ្យ AI ចងក្រងស្គ្រីបតាមទម្រង់ [00:01 - 00:04] អត្ថបទ ជាភាសាខ្មែរដាច់ខាត៖</p>", unsafe_allow_html=True)
    
    ai_prompt_input = st.text_area(
        "បញ្ជា AI (ឧទាហរណ៍: សូមសរសេរស្គ្រីបសង្ខេបសាច់រឿង):",
        height=100,
        key="ai_prompt_box"
    )

    if st.button("🚀 ឱ្យ Gemini AI សរសេរស្គ្រីបខ្មែរអូតូ"):
        if not user_api_key.strip():
            st.warning("⚠️ សូមវាយបញ្ចូល Gemini API Key នៅ Sidebar ខាងឆ្វេងជាមុនសិន!")
        elif not ai_prompt_input.strip():
            st.warning("⚠️ សូមសរសេរបញ្ជា (Prompt) ជាមុនសិន!")
        else:
            with st.spinner("⏳ Gemini AI កំពុងសរសេរស្គ្រីបជាភាសាខ្មែរ... (រង់ចាំបន្តិច)"):
                try:
                    client = genai.Client(api_key=user_api_key.strip())
                    strict_prompt = (
                        f"{ai_prompt_input}\n\n"
                        "សូមបកប្រែ ឬសរសេរជាភាសាខ្មែរដាច់ខាត ហាមមានអក្សរអង់គ្លេស ឬភាសាដទៃឡើយ។ "
                        "ទម្រង់នៃការសរសេរត្រូវតែមានកំណត់ពេលវេលាពិតប្រាកដតាមទម្រង់នេះប៉ុណ្ណោះ៖ "
                        "[00:01 - 00:04] អត្ថបទជាភាសាខ្មែរ..."
                    )
                    response = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=strict_prompt
                    )
                    st.session_state.script_input = response.text
                    st.success("🎉 បង្កើតស្គ្រីបភាសាខ្មែរបានជោគជ័យ!")
                except Exception as e:
                    st.error(f"មានបញ្ហាក្នុងការបង្កើតស្គ្រីប: {e}")

    st.markdown("---")
    st.subheader("📋 ស្គ្រីបចុងក្រោយ (ទ្រង់ទ្រាយ [00:01 - 00:04] ភាសាខ្មែរ):")
    st.session_state.script_input = st.text_area(
        "កែសម្រួលអត្ថបទ ឬ Timestamps នៅទីនេះ:",
        value=st.session_state.script_input,
        height=250,
        key="main_script_editor"
    )

# -------------------------------------------------------------
# 3. ផ្ទាំងកាត់វីដេអូជាកំណាត់ៗតាម Timestamps (Video Splitter)
# -------------------------------------------------------------
with tab_split:
    st.subheader("✂️ កាត់វីដេអូជាបំណែកៗតាម Timestamps")
    st.markdown("<p style='color: #94a3b8;'>ប្រព័ន្ធនឹងយករស្គ្រីបខាងលើមកកាត់វីដេអូចេញជាកំណាត់ៗស្វ័យប្រវត្តក្នុងកញ្ចប់ ZIP៖</p>", unsafe_allow_html=True)
    
    def time_to_seconds(time_str):
        parts = list(map(int, time_str.split(':')))
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        return parts[0]

    def parse_time_intervals(text):
        pattern = r'\[\s*(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\s*\]'
        matches = re.findall(pattern, text)
        intervals = []
        for match in matches:
            start_sec = time_to_seconds(match[0])
            end_sec = time_to_seconds(match[1])
            if end_sec > start_sec:
                filename_safe = f"[{match[0]} - {match[1]}]".replace(":", "-")
                intervals.append({"name": filename_safe, "start": start_sec, "end": end_sec})
        return intervals

    import zipfile
    import io

    if st.button("✂️ ចាប់ផ្តើមកាត់វីដេអូជាបំណែកៗ (.ZIP)"):
        if not st.session_state.get("uploaded_video_file"):
            st.warning("⚠️ សូម Upload វីដេអូនៅផ្ទាំង «វីដេអូ» ជាមុនសិន!")
        elif not st.session_state.script_input.strip():
            st.warning("⚠️ សូមបញ្ចូលស្គ្រីបដែលមាន Timestamps នៅផ្ទាំង «ស្គ្រីប AI» ជាមុនសិន!")
        else:
            intervals = parse_time_intervals(st.session_state.script_input)
            if not intervals:
                st.error("❌ រកមិនឃើញទម្រង់ Timestamps ក្នុងស្គ្រីបទេ។ (ឧទាហរណ៍: [00:00 - 00:05])")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                    st.session_state.uploaded_video_file.seek(0)
                    tfile.write(st.session_state.uploaded_video_file.read())
                    tfile.close()

                    cap = cv2.VideoCapture(tfile.name)
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    if fps == 0 or fps is None:
                        fps = 25.0
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

                    zip_io = io.BytesIO()
                    total_clips = len(intervals)

                    with zipfile.ZipFile(zip_io, mode='w', compression=zipfile.ZIP_DEFLATED) as zipf:
                        for i, interval in enumerate(intervals):
                            status_text.info(f"✂️ កំពុងកាត់កំណាត់ទី {i+1} នៃ {total_clips} ({interval['name']})...")
                            
                            output_clip_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                            out = cv2.VideoWriter(output_clip_path, fourcc, fps, (width, height))

                            start_frame = int(interval['start'] * fps)
                            end_frame = int(interval['end'] * fps)

                            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
                            current_frame = start_frame

                            while current_frame <= end_frame:
                                ret, frame = cap.read()
                                if not ret:
                                    break
                                out.write(frame)
                                current_frame += 1

                            out.release()

                            if os.path.exists(output_clip_path) and os.path.getsize(output_clip_path) > 0:
                                zipf.write(output_clip_path, arcname=f"clip_{interval['name']}.mp4")
                                os.remove(output_clip_path)

                            progress_bar.progress(int((i + 1) / total_clips * 100))

                    cap.release()
                    if os.path.exists(tfile.name):
                        os.remove(tfile.name)

                    st.session_state.split_zip_buffer = zip_io.getvalue()
                    status_text.success("🎉 កាត់វីដេអូជាបំណែកៗ និងវេចខ្ចប់ក្នុង ZIP រួចរាល់ជាស្រេច!")
                except Exception as e:
                    st.error(f"មានបញ្ហាក្នុងការកាត់វីដេអូ: {e}")

    if st.session_state.get("split_zip_buffer"):
        st.markdown("---")
        st.download_button(
            label="📥 ទាញយកកញ្ចប់វីដេអូជាបំណែកៗ (.ZIP)",
            data=st.session_state.split_zip_buffer,
            file_name="khmer_video_clips.zip",
            mime="application/zip",
            key="download_split_zip"
        )

# -------------------------------------------------------------
# 4. ផ្ទាំងបកប្រែ (Translation & Settings)
# -------------------------------------------------------------
with tab_translate:
    st.subheader("🌐 ការកំណត់ម៉ាស៊ីនបកប្រែ")
    trans_engine = st.selectbox("ម៉ាស៊ីនបកប្រែ:", ("✨ Gemini", "Google Translate Pro"))
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        source_lang = st.selectbox("ភាសាដើម", ["អង់គ្លេស (En)", "ថៃ (Th)", "ចិន (Zh)"])
    with col_l2:
        target_lang = st.selectbox("បកប្រែទៅ", ["🇰🇭 ខ្មែរ (Khmer)"])

# -------------------------------------------------------------
# 5. ផ្ទាំងសំឡេង AI (Voice Dubbing & Edge-TTS - Single MP3 Audio)
# -------------------------------------------------------------
with tab_audio:
    st.subheader("🎙️ បម្លែងស្គ្រីបទៅជាសំឡេង MP3 តែមួយ (Voiceover)")
    voice_type = st.radio("សំឡេងនិយាយ:", ("👩 ស្រី (Sreymom)", "👨 ប្រុស (Piseth)"))
    selected_voice = "km-KH-SreymomNeural" if "ស្រី" in voice_type else "km-KH-PisethNeural"

    st.markdown("---")
    st.info("ប្រព័ន្ធនឹងទាញយកអត្ថបទទាំងអស់ពីផ្ទាំង «ស្គ្រីប AI» មកបម្លែងជាសំឡេង MP3 តែមួយដោយរលូនសម្រាប់យកទៅកាត់ត។")

    async def generate_single_tts(text, voice, output_path):
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True
        except Exception:
            pass
        return False

    if st.button("🎙️ ចាប់ផ្ដើមបង្កើតសំឡេង MP3 តែមួយ"):
        script_text = st.session_state.script_input
        if not script_text.strip():
            st.warning("⚠️ សូមបញ្ចូលស្គ្រីបនៅផ្ទាំង «ស្គ្រីប AI» ជាមុនសិន!")
        else:
            with st.spinner("⏳ កំពុងបង្កើតសំឡេង MP3 តែមួយ... (រង់ចាំបន្តិច)"):
                try:
                    # Clean timestamps to generate clean narration audio
                    clean_text = re.sub(r'\[\s*\d{1,2}:\d{2}\s*(?:-\s*\d{1,2}:\d{2})?\s*\]', '', script_text)
                    clean_text = re.sub(r'\n\s*\n', '\n', clean_text).strip()
                    
                    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                    temp_audio.close()
                    
                    success = asyncio.run(generate_single_tts(clean_text, selected_voice, temp_audio.name))
                    
                    if success:
                        with open(temp_audio.name, "rb") as f:
                            st.session_state.single_audio_bytes = f.read()
                        if os.path.exists(temp_audio.name):
                            os.remove(temp_audio.name)
                        st.success("🎉 បង្កើតសំឡេង MP3 បានជោគជ័យរួចរាល់!")
                    else:
                        st.error("❌ មានបញ្ហាក្នុងการបង្កើតសំឡេង!")
                except Exception as e:
                    st.error(f"មានបញ្ហា: {e}")

    if st.session_state.get("single_audio_bytes"):
        st.markdown("---")
        st.subheader("🎧 ស្ដាប់ និងទាញយកសំឡេង MP3")
        st.audio(st.session_state.single_audio_bytes, format="audio/mp3")
        st.download_button(
            label="📥 ទាញយកឯកសារសំឡេង MP3",
            data=st.session_state.single_audio_bytes,
            file_name="khmer_voiceover_recap.mp3",
            mime="audio/mp3"
        )

# -------------------------------------------------------------
# 6. ផ្ទាំងអក្សរ (Subtitle Styling)
# -------------------------------------------------------------
with tab_sub:
    st.subheader("🔤 ការកំណត់រចនាប័ទ្មអក្សរ Subtitle")
    font_choice = st.selectbox("Font អក្សរ:", ("Battambang", "Siemreap", "Moul", "Bayon"))
    color_choice = st.selectbox("ពណ៌អក្សរ:", ("ស (White)", "លឿង (Yellow)"))

# -------------------------------------------------------------
# 7. ផ្ទាំងទាញយក (Download Section)
# -------------------------------------------------------------
with tab_download:
    st.subheader("📥 ទាញយកលទ្ធផលអូឌីយ៉ូ MP3")
    if st.session_state.get("single_audio_bytes"):
        st.success("🎉 សំឡេង MP3 រួចរាល់សម្រាប់ទាញយកហើយ!")
        st.download_button(
            label="📥 ទាញយកឯកសារសំឡេង MP3",
            data=st.session_state.single_audio_bytes,
            file_name="khmer_voiceover_recap.mp3",
            mime="audio/mp3"
        )
    else:
        st.info("មិនទាន់មានលទ្ធផលអូឌីយ៉ូទេ!")

# -------------------------------------------------------------
# 8. ផ្ទាំងរីដេអូម (Movie Recap History)
# -------------------------------------------------------------
with tab_recap:
    st.subheader("🎞️ ប្រវត្តិរីដេអូម (Movie Recap History)")
    st.info("ប្រវត្តិវីដេអូសម្រាយរឿងដែលបានបង្កើតនឹងបង្ហាញនៅទីនេះ។")
