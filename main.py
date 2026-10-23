# 🗄️ Session State Initialization
if "script_input" not in st.session_state:
    st.session_state.script_input = ""
if "zip_buffer" not in st.session_state:
    st.session_state.zip_buffer = None
if "uploaded_video" not in st.session_state:
    st.session_state.uploaded_video = None
if "generated_clips" not in st.session_state:
    st.session_state.generated_clips = [] # រក្សាទុកវីដេអូឃ្លីបសម្រាប់មើលនិងទាញយក

# -------------------------------------------------------------
# 3. ផ្ទាំងសំឡេង និងកាត់វីដេអូ (Video Dubbing & Audio Cutting)
# -------------------------------------------------------------
with tab_audio:
    st.subheader("🎙️ កាត់វីដេអូ និងបញ្ចូលសំឡេង AI (Dubbing Video)")
    
    voice_type = st.radio(
        "សំឡេងនិយាយ:",
        ("👩 ស្រី (Sreymom)", "👨 ប្រុស (Piseth)")
    )
    selected_voice = "km-KH-SreymomNeural" if "ស្រី" in voice_type else "km-KH-PisethNeural"

    st.markdown("---")
    st.session_state.script_input = st.text_area(
        "បញ្ចូល Timestamps និងអត្ថបទ (ឧទាហរណ៍: [00:00 - 00:05] សួស្តី...):",
        value=st.session_state.script_input,
        height=140
    )

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

    if st.button("🎬 ចាប់ផ្តើមកាត់វីដេអូ និងបញ្ចូលសំឡេង AI"):
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
                    zip_io = io.BytesIO()
                    st.session_state.generated_clips = [] # សម្អាតទិន្នន័យចាស់
                    
                    with zipfile.ZipFile(zip_io, mode='w', compression=zipfile.ZIP_DEFLATED) as zipf:
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
                                    zipf.write(output_video_path, arcname=clip_name)
                                    
                                    # អានទិន្នន័យវីដេអូទុកសម្រាប់បង្ហាញនិងទាញយកដាច់ដោយឡែក
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

                    st.session_state.zip_buffer = zip_io.getvalue()
                    status_text.success("🎉 កាត់វីដេអូ និងបញ្ចូលសំឡេង AI រួចរាល់! អាចចូលទៅផ្ទាំង «ទាញយក» ដើម្បីមើលនិងទាញយកបាន។")
            except Exception as e:
                st.error(f"មានបញ្ហាកើតឡើង: {e}")

# -------------------------------------------------------------
# 5. ផ្ទាំងទាញយក (Download & Preview Section)
# -------------------------------------------------------------
with tab_download:
    st.subheader("📥 មើល និងទាញយកវីដេអូឃ្លីប")
    
    if st.session_state.get("zip_buffer"):
        st.success("🎉 កញ្ចប់វីដេអូទាំងអស់ត្រូវបានរៀបចំរួចរាល់ហើយ!")
        st.download_button(
            label="📥 ទាញយកកញ្ចប់វីដេអូទាំងអស់ (.ZIP)",
            data=st.session_state.zip_buffer,
            file_name="khmer_dubbed_video_clips.zip",
            mime="application/zip",
            key="download_video_zip_main"
        )
        st.markdown("---")

    if st.session_state.get("generated_clips"):
        st.write("### 🎬 វីដេអូឃ្លីបនីមួយៗ (អាចមើល និងទាញយកទីនេះ):")
        for idx, clip in enumerate(st.session_state.generated_clips):
            st.markdown(f"**ឃ្លីបទី {idx+1} — ម៉ោង: {clip['time']}**")
            st.video(clip["bytes"]) # 📺 បង្ហាញវីដេអូសម្រាប់មើលផ្ទាល់
            st.download_button(
                label=f"📥 ទាញយកឃ្លីបទី {idx+1} (.mp4)",
                data=clip["bytes"],
                file_name=clip["name"],
                mime="video/mp4",
                key=f"dl_clip_{idx}"
            )
            st.markdown("---")
    else:
        st.info("មិនទាន់មានលទ្ធផលវីដេអូទេ! សូមដាក់ Timestamps និងចុចចាប់ផ្តើមដំណើរការនៅផ្ទាំង «សំឡេង» ជាមុនសិន។")
                    
