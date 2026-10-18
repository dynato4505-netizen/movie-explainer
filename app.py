import streamlit as st
from google import genai
import asyncio
import edge_tts
import os
import tempfile
import re
import cv2  # សម្រាប់ទាញយករយៈពេលវីដេអូ

st.set_page_config(page_title="AI Full-Length Dialogue Dubbing", layout="centered")

st.title("🎬 AI Full-Length Dialogue Dubbing")
st.write("បកប្រែចំឃ្លាតួអង្គ **ពេញលេញពេញប្រវែងវីដេអូ មិនខ្លីពេក និងមិនវែងពេក**!")

api_key = st.text_input("បញ្ចូល Gemini API Key របស់អ្នក:", type="password")

# ជម្រើសសំឡេងប្រុស ឬស្រី
voice_choice = st.selectbox(
    "ជ្រើសរើសសំឡេង Dubbing:",
    ("ស្រី (Sreymom)", "ប្រុស (Piseth)")
)

voice_map = {
    "ស្រី (Sreymom)": "km-KH-SreymomNeural",
    "ប្រុស (Piseth)": "km-KH-PisethNeural"
}
selected_voice = voice_map[voice_choice]

uploaded_file = st.file_uploader("ជ្រើសរើសវីដេអូ (MP4, MOV - ក្រោម ១៥នាទី):", type=["mp4", "mov", "avi"])

# Function សម្រាប់ទាញយករយៈពេលវីដេអូជាវិនាទី
def get_video_duration(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    if fps > 0:
        return frame_count / fps
    return 0

# Function សម្រាប់លុប Timecode និងការពិពណ៌នាចេញទាំងស្រុង មុនយកទៅធ្វើ Audio
def clean_text_for_tts(text):
    cleaned = re.sub(r'\[\d{2}:\d{2}\s*-\s*\d{2}:\d{2}\]|\d{2}:\d{2}', '', text)
    cleaned = re.sub(r'\(.*?\)|\[.*?\]|\*.*?\*', '', cleaned)
    cleaned = cleaned.replace('—', ' ').replace('\n', ' ')
    return cleaned.strip()

# Function សម្រាប់ generate សំឡេងជាមួយ edge-tts
async def generate_edge_tts(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

if uploaded_file is not None:
    st.video(uploaded_file)

if st.button("ចាប់ផ្តើមបកប្រែចំឃ្លា (ពេញប្រវែងវីដេអូ) 🚀"):
    if not api_key:
        st.error("សូមបញ្ចូល Gemini API Key ជាមុនសិន!")
    elif uploaded_file is None:
        st.warning("សូម Upload វីដេអូជាមុនសិន!")
    else:
        with st.spinner("កំពុងវិភាគវីដេអូ និងរៀបចំអត្ថបទពេញលេញគ្រប់ឈុតឆាក..."):
            try:
                # បង្កើត Temp File សម្រាប់វីដេអូ
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tfile.write(uploaded_file.read())
                video_path = tfile.name

                # គណនារយៈពេលវីដេអូជាវិនាទី
                duration_sec = get_video_duration(video_path)
                
                if duration_sec > 900:
                    st.error("❌ វីដេអូរបស់អ្នកវែងពេក! សូមជ្រើសរើសវីដេអូដែលមានរយៈពេល ១៥នាទីចុះក្រោម។")
                else:
                    # កែសម្រួលកម្រិតពាក្យឱ្យសមស្របពេញលេញ (កុំឱ្យតិចពេក រួមទាំងដកឃ្លាឱ្យបានសមសួន)
                    max_words = int(duration_sec * 2.8)
                    
                    st.info(f"⏱️ រយៈពេលវីដេអូពិតប្រាកដ: {duration_sec/60:.2f} នាទី ({duration_sec:.1f} វិនាទី) | កំណត់ទំហំអត្ថបទ: ~{max_words} ពាក្យ")

                    client = genai.Client(api_key=api_key)
                    st.info("កំពុងបញ្ជូនវីដេអូទៅកាន់ Gemini AI...")
                    
                    video_file = client.files.upload(file=video_path)

                    # Prompt កែសម្រួលថ្មី៖ ពង្រីកអត្ថបទបកប្រែឱ្យមានប្រវែងពេញលេញពេញម៉ោងវីដេអូ មិនឱ្យខើចខ្លី
                    prompt = (
                        "អ្នកគឺជាអ្នកបកប្រែប្រយោគតួអង្គភាពយន្តអាជីព។ "
                        "សូមទស្សនាវីដេអូនេះដោយយកចិត្តទុកដាក់តាំងពីដើមរហូតដល់ចប់ រួចបកប្រែ **เฉพาะ ឃ្លាប្រយោគដែលតួអង្គនិយាយ** ជាភាសាខ្មែរឱ្យបាន **ពេញលេញគ្រប់ឈុតឆាកទាំងអស់**។ "
                        "**លក្ខខណ្ឌតឹងរឹង៖** "
                        "1. ហាមបន្សល់ទុកចន្លោះប្រហោង ឬកាត់បន្ថយឃ្លាតួអង្គសំខាន់ៗចេញឡើយ។ អត្ថបទសរុបត្រូវមានប្រវែងសមល្មមប្រហែល " + str(max_words) + " ពាក្យ ដើម្បីបំពេញគ្រប់រយៈពេល " + f"{duration_sec:.1f}" + " វិនាទីនៃវីដេអូដោយរលូនល្អ។ "
                        "2. ហាមសម្រាយរឿង និងហាមពិពណ៌នាឈុតឆាកក្នុងវង់ក្រចក (Pure Dialogue Only)។ "
                        "3. រក្សាកូដពេលវេលា [MM:SS - MM:SS] ទុកនៅខាងមុខប្រយោគនីមួយៗឱ្យបានគ្រប់គ្រាន់តាមលំដាប់វីដេអូ។"
                    )
                    
                    response = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=[video_file, prompt],
                    )
                    
                    raw_text = response.text
                    
                    # បង្ហាញអត្ថបទបកប្រែចំឃ្លា
                    st.subheader("📝 អត្ថបទបកប្រែចំប្រយោគតួអង្គ (ពេញប្រវែង):")
                    st.text_area("Copy Text ទីនេះ:", raw_text, height=250)
                    
                    # លុប Timecode និងការពិពណ៌នាចេញ មុនយកទៅធ្វើ Audio
                    clean_text = clean_text_for_tts(raw_text)
                    
                    st.info(f"កំពុងបង្កើតសំឡេងអានពេញប្រវែងសមាមាត្រនឹងវីដេអូ ({voice_choice})...")
                    
                    # បង្កើត Temp File សម្រាប់ Audio
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as audio_tf:
                        audio_path = audio_tf.name

                    # Run edge-tts ជាមួយអត្ថបទពេញលេញ
                    asyncio.run(generate_edge_tts(clean_text, selected_voice, audio_path))
                    
                    st.subheader("🔊 សំឡេងអានប្រយោគតួអង្គ (ពេញប្រវែងវីដេអូ):")
                    st.audio(audio_path)
                
                # លុប Video File ចោលវិញកុំឱ្យស្ទះម៉ាស៊ីន
                if os.path.exists(video_path):
                    os.remove(video_path)
                
            except Exception as e:
                st.error(f"មានបញ្ហាកើតឡើង: {e}")
                
