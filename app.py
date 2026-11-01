import streamlit as st
import asyncio
import edge_tts
import os
import tempfile
import re
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip

# 🌟 កំណត់ទម្រង់ទំព័រឱ្យធំទូលាយ (Wide Mode)
st.set_page_config(
    page_title="Khmer Video AI - Auto Merge Video & Audio",
    page_icon="🎬",
    layout="wide"
)

# 🎨 Custom CSS សម្រាប់ Dark Mode ស្អាត
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
    </style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center; color: #a78bfa;'>🎬 Khmer Video AI Pro (Auto Merge)</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94a3b8;'>ប្រព័ន្ធកាត់តវីដេអូ និងបញ្ចូលសំឡេង AI ឱ្យត្រូវនឹងសាច់រឿងស្វ័យប្រវត្តិ</p>", unsafe_allow_html=True)

# 🗂️ Tabs
tab_upload, tab_script, tab_merge = st.tabs([
    "🎬 ជំហានទី ១៖ បញ្ចូលវីដេអូ", 
    "📝 ជំហានទី ២៖ បញ្ចូលស្គ្រីប និង Timestamps",
    "🎥 ជំហានទី ៣៖ កាត់ និងបញ្ចូលសំឡេង (Merge)"
])

# Session States
if "uploaded_video" not in st.session_state:
    st.session_state.uploaded_video = None
if "script_text" not in st.session_state:
    st.session_state.script_text = ""
if "final_video_bytes" not in st.session_state:
    st.session_state.final_video_bytes = None

# -------------------------------------------------------------
# 1. ផ្ទាំងវីដេអូដើម
# -------------------------------------------------------------
with tab_upload:
    st.subheader("🎬 ដាក់បញ្ចូលវីដេអូសម្រាប់ធ្វើសម្រាយរឿង")
    vid_file = st.file_uploader("ជ្រើសរើសវីដេអូ (MP4, MKV, MOV):", type=["mp4", "mkv", "mov"], key="vid_upload_unique_key")
    if vid_file:
        st.session_state.uploaded_video = vid_file
        st.success("✅ បានផ្ទុកវីដេអូជោគជ័យ!")
        st.video(vid_file)

# -------------------------------------------------------------
# 2. ផ្ទាំងស្គ្រីប
# -------------------------------------------------------------
with tab_script:
    st.subheader("📝 បញ្ចូលស្គ្រីប ឬយកពីកន្លែងផ្សេងមក pasting ទុកទីនេះ")
    st.markdown("<p style='color: #94a3b8;'>ទម្រង់តម្រូវឱ្យមាន Timestamps ដូចជា: [00:00 - 00:05] អត្ថបទនិយាយ...</p>", unsafe_allow_html=True)
    
    st.session_state.script_text = st.text_area(
        "បិទភ្ជាប់ (Paste) ស្គ្រីបរបស់អ្នកនៅទីនេះ:",
        value=st.session_state.script_text,
        height=250,
        key="script_text_area_unique_key"
    )

# -------------------------------------------------------------
# 3. ផ្ទាំងកាត់ និងបញ្ចូលសំឡេង (Merge Video & Audio)
# -------------------------------------------------------------
with tab_merge:
    st.subheader("🎥 បង្កើតសំឡេង AI និងច្របាច់បញ្ចូលគ្នាជាវីដេអូចុងក្រោយ")
    
    col_v1, col_v2, col_v3 = st.columns(3)
    with col_v1:
        voice_choice = st.radio("ជ្រើសរើសសំឡេងនិយាយ:", ("👩 ស្រី (Sreymom)", "👨 ប្រុស (Piseth)"), key="voice_radio_unique_key")
        selected_voice = "km-KH-SreymomNeural" if "ស្រី" in voice_choice else "km-KH-PisethNeural"
    with col_v2:
        # 🎚️ សារ៉េកម្រិតសំឡេង AI
        ai_volume = st.slider("🎚️ កម្រិតសំឡេង AI", min_value=0.1, max_value=2.0, value=1.0, step=0.1)
    with col_v3:
        # 🎚️ សារ៉េកម្រិតសំឡេងដើមឱ្យខ្សាវៗ (កុំឱ្យបាំងសំឡេង AI)
        orig_volume = st.slider("🎚️ កម្រិតសំឡេងដើម (ខ្សាវៗ)", min_value=0.0, max_value=0.5, value=0.1, step=0.05, help="0.0 គឺបិទសំឡេងដើមផ្ដាច់, 0.1 ដល់ 0.2 គឺលឺខ្សាវៗស្រទន់")

    async def generate_tts(text, voice, path):
        comm = edge_tts.Communicate(text, voice)
        await comm.save(path)

    if st.button("🚀 ចាប់ផ្ដើមបង្កើតសំឡេង និងបញ្ចូលចូលវីដេអូ", key="btn_merge_unique_key"):
        if not st.session_state.get("uploaded_video"):
            st.warning("⚠️ សូម Upload វីដេអូនៅផ្ទាំងទី ១ ជាមុនសិន!")
        elif not st.session_state.script_text.strip():
            st.warning("⚠️ សូមបញ្ចូលស្គ្រីបនៅផ្ទាំងទី ២ ជាមុនសិន!")
        else:
            with st.spinner("⏳ កំពុងបង្កើតសំឡេង និងច្របាច់បញ្ចូលវីដេអូ... (សូមរង់ចាំបន្តិច)"):
                try:
                    script = st.session_state.script_text
                    clean_text = re.sub(r'\[\s*\d{1,2}:\d{2}\s*(?:-\s*\d{1,2}:\d{2})?\s*\]', '', script)
                    clean_text = re.sub(r'\n\s*\n', '\n', clean_text).strip()

                    audio_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                    audio_path = audio_temp.name
                    audio_temp.close()

                    asyncio.run(generate_tts(clean_text, selected_voice, audio_path))

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

                    # 🎚️ စစ်ဆေးថាតើវីដេអូដើមមានសំឡេងឬអត់ រួចកែតម្រូវកម្រិតខ្សាវ
                    if video_clip.audio is not None:
                        orig_audio = video_clip.audio.with_volume_scaled(orig_volume)
                        # បញ្ចូលសំឡេងទាំងពីរ (AI + សំឡេងដើមខ្សាវៗ) ចូលគ្នា
                        final_audio = CompositeAudioClip([orig_audio, ai_audio])
                    else:
                        final_audio = ai_audio

                    final_clip = video_clip.with_audio(final_audio)
                    final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=24, logger=None)

                    with open(output_path, "rb") as f:
                        st.session_state.final_video_bytes = f.read()

                    video_clip.close()
                    ai_audio.close()
                    final_clip.close()
                    os.remove(audio_path)
                    os.remove(vid_temp_path)
                    os.remove(output_path)

                    st.success("🎉 បញ្ចូលវីដេអូ និងសំឡេងជោគជ័យ ១០០%!")
                except Exception as e:
                    st.error(f"មានបញ្ហាក្នុងการ Merge: {e}")

    if st.session_state.get("final_video_bytes"):
        st.markdown("---")
        st.subheader("📥 ទាញយកវីដេអូចុងក្រោយរបស់អ្នក")
        st.video(st.session_state.final_video_bytes)
        st.download_button(
            label="📥 ទាញយកវីដេអូសម្រាយរឿង (.MP4)",
            data=st.session_state.final_video_bytes,
            file_name="final_recap_video.mp4",
            mime="video/mp4",
            key="download_final_video_unique_key"
    )
            
