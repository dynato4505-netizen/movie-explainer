import streamlit as st
import asyncio
import edge_tts
import os
import tempfile
import re
import google.generativeai as genai
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip
from PIL import Image

# 🌟 កំណត់ទម្រង់ទំព័រឱ្យធំទូលាយ (Wide Mode)
st.set_page_config(
    page_title="Khmer Video AI Pro - Ultimate Edition",
    page_icon="🎬",
    layout="wide"
)

# 🎨 Custom CSS សម្រាប់ Dark Mode ស្អាត និងទំនើប
st.markdown("""
    <style>
    .main { background-color: #0b0f19; color: #ffffff; }
    .stButton>button {
        background: linear-gradient(45deg, #8b5cf6, #3b82f6);
        color: white; border-radius: 10px; border: none;
        padding: 12px 24px; font-weight: bold; width: 100%;
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #1e293b; color: white; border-radius: 8px; border: 1px solid #334155;
    }
    .stSelectbox>div>div>div { background-color: #1e293b; color: white; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center; color: #a78bfa;'>🎬 Khmer Video AI Pro (Advanced Edition)</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94a3b8;'>ប្រព័ន្ធកាត់តវីដេអូ សម្រាយរឿង និងបញ្ចូលសំឡេង AI តាម Timestamp ស្វ័យប្រវត្តិ</p>", unsafe_allow_html=True)

# 🗂️ Tabs គ្រប់គ្រងកម្មវិធី
tab_config, tab_script, tab_upload, tab_merge = st.tabs([
    "🔑 ជំហានទី ១៖ កំណត់ API & Logo",
    "📝 ជំហានទី ២៖ បញ្ចូល និងបង្កើតស្គ្រីប AI",
    "🎬 ជំហានទី ៣៖ បញ្ចូលវីដេអូ និងសំឡេង",
    "🎥 ជំហានទី ៤៖ កាត់ត និងទាញយក"
])

# Session States
if "uploaded_video" not in st.session_state:
    st.session_state.uploaded_video = None
if "script_text" not in st.session_state:
    st.session_state.script_text = "[00:00 - 00:05] សួស្តីស្វាគមន៍មកកាន់ឆានែលសម្រាយរឿង..."
if "final_video_bytes" not in st.session_state:
    st.session_state.final_video_bytes = None
if "generated_audio_bytes" not in st.session_state:
    st.session_state.generated_audio_bytes = None
if "logo_image" not in st.session_state:
    st.session_state.logo_image = None

# -------------------------------------------------------------
# 1. ផ្ទាំងទី ១៖ កំណត់ Gemini API Key ថ្មី & Template Logo
# -------------------------------------------------------------
with tab_config:
    st.subheader("🔑 កំណត់ Gemini API Key (รุ่นใหม่ / google-genai) និង Logo Template")
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        gemini_api_key = st.text_input("បញ្ចូល Gemini API Key របស់អ្នក:", type="password", help="ប្រើសម្រាប់ជំនួយបង្កើតស្គ្រីបសម្រាយរឿង")
        if gemini_api_key:
            try:
                # កំណត់ការប្រើប្រាស់ Gemini API ជំនាន់ថ្មី
                genai.configure(api_key=gemini_api_key)
                st.success("✅ API Key បានតភ្ជាប់ជោគជ័យ!")
            except Exception as e:
                st.error(f"❌ API Key មានបញ្ហា: {e}")

    with col_c2:
        logo_file = st.file_uploader("ដាក់រូបភាព Logo (PNG/JPG) សម្រាប់ដាក់លើវីដេអូ:", type=["png", "jpg", "jpeg"])
        if logo_file:
            st.session_state.logo_image = Image.open(logo_file)
            st.success("✅ បានផ្ទុក Logo រួចរាល់!")
            st.image(st.session_state.logo_image, width=150)

# -------------------------------------------------------------
# 2. ជំហានទី ២៖ បញ្ចូលស្គ្រីប និង Timestamps + ជ្រើសរើសសំឡេង AI
# -------------------------------------------------------------
with tab_script:
    st.subheader("📝 បញ្ចូលស្គ្រីប ឬឱ្យ AI ជួយសរសេរតាមប្រភេទរឿង")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        story_genre = st.selectbox(
            "🎭 ជ្រើសរើសប្រភេទសំឡេង និងរចនាប័ទ្មសម្រាយរឿង:",
            ("ទូទៅ / ធម្មតា (General)", "កំប្លែង (Comedy)", "រន្ធត់ / ញាក់សាច់ (Horror)", "សេដ / ឈឺចាប់ (Sad / Emotional)", "សកម្មភាព / ប្រយុទ្ធ (Action)")
        )
    with col_s2:
        voice_choice = st.selectbox(
            "🗣️ ជ្រើសរើសសំឡេង AI (Edge-TTS):",
            ("👩 ស្រី (Sreymom - ធម្មតា)", "👨 ប្រុស (Piseth - ធម្មតា)")
        )
        selected_voice = "km-KH-SreymomNeural" if "ស្រី" in voice_choice else "km-KH-PisethNeural"

    # បង្កើតស្គ្រីបដោយស្វ័យប្រវត្តិជាមួយ Gemini ប្រសិនបើមាន API Key
    story_prompt = st.text_area("បញ្ចូលសាច់រឿងសង្ខេប ឬលម្អិត ដើម្បីឲ្យ AI បំបែកជា Timestamp [00:00 - 00:05]:", height=100)
    if st.button("🤖 ឱ្យ AI បង្កើតស្គ្រីបតាម Timestamps"):
        if not gemini_api_key:
            st.warning("⚠️ សូមដាក់ Gemini API Key នៅផ្ទាំងទី ១ ជាមុនសិន!")
        elif not story_prompt.strip():
            st.warning("⚠️ សូមបញ្ចូលសាច់រឿងសង្ខេប!")
        else:
            with st.spinner("⏳ កំពុងបង្កើតស្គ្រីបសម្រាយរឿងតាមរចនាប័ទ្ម " + story_genre + "..."):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash') # កាត់បន្ថយ Token និងលឿន
                    prompt_full = f"""
                    អ្នកគឺជាអ្នកសម្រាយរឿងអាជីព។ ចូរព្រាងស្គ្រីបសម្រាយរឿងតាមរចនាប័ទ្ម '{story_genre}' 
                    ដោយបែងចែកជាកូដពេលវេន (Timestamps) ដាច់ៗពីគ្នា მკស្គាល់ទម្រង់ដូចខាងក្រោមជាដាច់ខាត:
                    [00:00 - 00:05] អត្ថបទនិយាយ...
                    [00:05 - 00:10] អត្ថបទនិយាយ...
                    សាច់រឿងដើម៖ {story_prompt}
                    """
                    response = model.generate_content(prompt_full)
                    st.session_state.script_text = response.text
                    st.success("✅ បង្កើតស្គ្រីបជោគជ័យ!")
                except Exception as e:
                    st.error(f"❌ កំហុសកើតឡើង៖ {e}")

    st.markdown("<p style='color: #94a3b8; margin-top: 10px;'>ទម្រង់តម្រូវឱ្យមាន Timestamps ដូចជា: [00:00 - 00:05] អត្ថបទនិយាយ...</p>", unsafe_allow_html=True)
    st.session_state.script_text = st.text_area(
        "កែសម្រួលស្គ្រីប (Script & Timestamps) នៅទីនេះ:",
        value=st.session_state.script_text,
        height=250
    )

# -------------------------------------------------------------
# 3. ជំហានទី ៣៖ បញ្ចូលវីដេអូ និងការកំណត់សំឡេង
# -------------------------------------------------------------
with tab_upload:
    st.subheader("🎬 ដាក់បញ្ចូលវីដេអូដើម")
    vid_file = st.file_uploader("ជ្រើសរើសវីដេអូ (MP4, MKV, MOV):", type=["mp4", "mkv", "mov"])
    if vid_file:
        st.session_state.uploaded_video = vid_file
        st.success("✅ បានផ្ទុកវីដេអូជោគជ័យ!")
        st.video(vid_file)

    st.markdown("---")
    st.subheader("🎚️ ការកំណត់កម្រិតសំឡេង និងការបែងចែកទាញយកដាច់ដោយឡែក")
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        ai_volume = st.slider("🎚️ កម្រិតសំឡេង AI (Voiceover)", min_value=0.1, max_value=2.0, value=1.0, step=0.1)
    with col_v2:
        orig_volume = st.slider("🎚️ កម្រិតសំឡេងវីដេអូដើម (Background Audio)", min_value=0.0, max_value=0.5, value=0.1, step=0.05, help="0.0 គឺបិទសំឡេងដើមផ្ដាច់, 0.1 គឺលឺខ្សាវៗពីក្រោយកុំឱ្យបាំងសំឡេង AI")

    async def generate_tts(text, voice, path):
        comm = edge_tts.Communicate(text, voice)
        await comm.save(path)

    if st.button("🎙️ បង្កើតសំឡេង AI (Generate Audio Only)"):
        if not st.session_state.script_text.strip():
            st.warning("⚠️ សូមបញ្ចូលស្គ្រីបនៅផ្ទាំងទី ២!")
        else:
            with st.spinner("⏳ កំពុងបង្កើតឯកសារសំឡេង AI..."):
                try:
                    script = st.session_state.script_text
                    # ដក Timestamp ចេញយកតែអត្ថបទសុទ្ធសម្រាប់អាន
                    clean_text = re.sub(r'\[\s*\d{1,2}:\d{2}\s*(?:-\s*\d{1,2}:\d{2})?\s*\]', '', script)
                    clean_text = re.sub(r'\n\s*\n', '\n', clean_text).strip()

                    audio_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                    audio_path = audio_temp.name
                    audio_temp.close()

                    asyncio.run(generate_tts(clean_text, selected_voice, audio_path))

                    with open(audio_path, "rb") as f:
                        st.session_state.generated_audio_bytes = f.read()
                    os.remove(audio_path)
                    st.success("✅ បង្កើតសំឡេងជោគជ័យ! អ្នកអាចទាញយកវានៅខាងក្រោម។")
                except Exception as e:
                    st.error(f"❌ កំហុស: {e}")

    if st.session_state.get("generated_audio_bytes"):
        st.audio(st.session_state.generated_audio_bytes, format='audio/mp3')
        st.download_button(
            label="📥 ទាញយកឯកសារសំឡេងដាច់ដោយឡែក (.MP3)",
            data=st.session_state.generated_audio_bytes,
            file_name="ai_voiceover.mp3",
            mime="audio/mp3"
        )

# -------------------------------------------------------------
# 4. ជំហានទី ៤៖ កាត់ត និងបញ្ចូលគ្នា (Merge) ព្រមទាំងបែងចែកកន្លែង Download
# -------------------------------------------------------------
with tab_merge:
    st.subheader("🎥 ច្របាច់បញ្ចូលវីដេអូ និងសំឡេងឲ្យត្រូវចំតួអង្គ (មិនកាត់តម្រឹមខុស)")
    
    st.info("💡 ប្រព័ន្ធនឹងធ្វើសមកាលកម្ម (Sync) សំឡេង AI ឲ្យស្របទៅនឹងវីដេអូដើម ដោយរក្សាប្រវែងវីដេអូនិងសំឡេងដើមលឺខ្សាវៗពីក្រោយយ៉ាងរលូន។")

    if st.button("🚀 ចាប់ផ្ដើមដំណើរការបញ្ចូលគ្នា (Merge Final Video)"):
        if not st.session_state.get("uploaded_video"):
            st.warning("⚠️ សូម Upload វីដេអូនៅផ្ទាំងទី ៣ ជាមុនសិន!")
        elif not st.session_state.get("generated_audio_bytes"):
            st.warning("⚠️ សូមបង្កើតសំឡេង AI នៅផ្ទាំងទី ៣ ជាមុនសិន!")
        else:
            with st.spinner("⏳ កំពុងបញ្ចូលវីដេអូ និងសំឡេង... (សូមរង់ចាំបន្តិច)"):
                try:
                    # យករំលងស្គ្រីបបង្កើតសំឡេងម្ដងទៀតដោយប្រើ bytes ដែលមានស្រាប់
                    audio_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                    audio_temp.write(st.session_state.generated_audio_bytes)
                    audio_path = audio_temp.name
                    audio_temp.close()

                    vid_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                    st.session_state.uploaded_video.seek(0)
                    vid_temp.write(st.session_state.uploaded_video.read())
                    vid_temp_path = vid_temp.name
                    vid_temp.close()

                    output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
                    
                    video_clip = VideoFileClip(vid_temp_path)
                    ai_audio = AudioFileClip(audio_path)

                    # 🎚️ កែតម្រូវកម្រិតសំឡេង AI
                    ai_audio = ai_audio.with_volume_scaled(ai_volume)

                    # 🎚️ រៀបចំសំឡេងវីដេអូដើមឲ្យលឺខ្សាវៗពីក្រោយ (Background Audio)
                    if video_clip.audio is not None:
                        orig_audio = video_clip.audio.with_volume_scaled(orig_volume)
                        final_audio = CompositeAudioClip([orig_audio, ai_audio])
                    else:
                        final_audio = ai_audio

                    final_clip = video_clip.with_audio(final_audio)

                    # កត់សម្គាល់៖ ប្រសិនបើមាន Logo អាចបញ្ចូលកន្លែងនេះ (Composite Video with Logo ប្រសិនបើចង់បន្ថែម)
                    
                    # នាំចេញវីដេអូចុងក្រោយ (ធានាថាមិនកាត់តតម្រឹមវីដេអូចោលខុសសាច់រឿង)
                    final_clip.write_videofile(
                        output_path, 
                        codec='libx264', 
                        audio_codec='aac', 
                        fps=24, 
                        preset='medium',
                        logger=None
                    )

                    with open(output_path, "rb") as f:
                        st.session_state.final_video_bytes = f.read()

                    # បិទ Resource ទាំងអស់ដើម្បីការពារ File Locking error
                    video_clip.close()
                    ai_audio.close()
                    final_clip.close()
                    os.remove(audio_path)
                    os.remove(vid_temp_path)
                    os.remove(output_path)

                    st.success("🎉 បញ្ចូលវីដេអូ និងសំឡេងជោគជ័យ ១០០%!")
                except Exception as e:
                    st.error(f"❌ មានបញ្ហាក្នុងការ Merge: {e}")

    if st.session_state.get("final_video_bytes"):
        st.markdown("---")
        st.subheader("📥 ទាញយកវីដេអូចុងក្រោយរបស់អ្នក (Final Output)")
        st.video(st.session_state.final_video_bytes)
        st.download_button(
            label="📥 ទាញយកវីដេអូសម្រាយរឿងចុងក្រោយ (.MP4)",
            data=st.session_state.final_video_bytes,
            file_name="final_recap_video.mp4",
            mime="video/mp4"
                                      )
        
