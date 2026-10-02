from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import asyncio
import edge_tts
import yt_dlp
import os
import tempfile

app = FastAPI(title="AI Movie Dubbing API", version="1.0")

class DubRequest(BaseModel):
    url: str
    script: str
    voice: str = "km-KH-PisethNeural"

@app.get("/")
def home():
    return {"message": "AI Dubbing API is running successfully!"}

@app.post("/generate-dub/")
async def generate_dub(req: DubRequest):
    try:
        downloaded_file_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
        ydl_opts = {'format': 'best', 'outtmpl': downloaded_file_path, 'noplaylist': True}
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([req.url.strip()])
            
        if not os.path.exists(downloaded_file_path):
            raise HTTPException(status_code=400, detail="មិនអាចទាញយកវីដេអូបានទេ")

        audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
        communicate = edge_tts.Communicate(req.script, req.voice)
        await communicate.save(audio_path)

        from moviepy.editor import VideoFileClip, AudioFileClip
        v_clip = VideoFileClip(downloaded_file_path)
        a_clip = AudioFileClip(audio_path)
        
        final_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
        final_clip = v_clip.set_audio(a_clip)
        final_clip.write_videofile(final_path, codec='libx264', audio_codec='aac', fps=v_clip.fps or 24, preset='ultrafast')

        return FileResponse(final_path, media_type="video/mp4", filename="dubbed_video.mp4")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
            
