import asyncio
import os
import ollama  # ✅ Import Ollama for LLM & Whisper
import yt_dlp  # ✅ Use yt-dlp instead of pytube
from autogen_agentchat.agents import AssistantAgent
from dotenv import load_dotenv
from moviepy.editor import VideoFileClip
import json  # ✅ To parse timestamps from AI
from faster_whisper import WhisperModel
import json
import re
import time

# Load environment variables
load_dotenv()

# ✅ Function to interact with Ollama LLM
def ollama_chat(messages):
    response = ollama.chat(model="llama3", messages=messages, format="json")
    return response["message"]["content"]

# ✅ Function to transcribe video using Whisper
from faster_whisper import WhisperModel

def transcribe_audio(video_path):
    
    print(f"📝 Transcribing {video_path} using Faster Whisper (CPU)...")

    model = WhisperModel("small", device="cpu", compute_type="int8")  # Optimized for CPU
    segments, _ = model.transcribe(video_path)  # ✅ Faster processing

    # ✅ Store transcript with timestamps
    transcript_data = []
    transcript_text = ""

    for segment in segments:
        start = segment.start  # Start timestamp
        end = segment.end      # End timestamp
        text = segment.text    # Text content

        transcript_data.append({"start": start, "end": end, "text": text})
        transcript_text += f"[{start:.2f} - {end:.2f}] {text}\n"  # Save formatted text

    # ✅ Save transcript with timestamps to a file
    transcript_file = "transcript.txt"
    with open(transcript_file, "w", encoding="utf-8") as file:
        file.write(transcript_text)

    print(f"📄 Transcript saved to {transcript_file}")
    return transcript_data  # Returns list of timestamps + text


# ✅ Function to download video from YouTube
def download_video(url):
    try:
        print(f"📥 Downloading video from: {url}")
        
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'temp_video.mp4',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        print(f"✅ Video downloaded: temp_video.mp4")
        return "temp_video.mp4"
    except Exception as e:
        print(f"❌ Error downloading video: {e}")
        return None

# ✅ Function to find best moments (timestamps) using LLM
def find_best_moments(transcript_data):
    """
    Extracts viral moments from a video transcript.

    Parameters:
    - transcript_data (list): The video transcript as a structured JSON list.
    - max_retries (int): Number of retry attempts if AI response is invalid.

    Returns:
    - list: Extracted moments with start/end times, captions, and hashtags.
    """

    formatted_transcript = json.dumps(transcript_data, indent=2)

    prompt = f"""
        You will receive a JSON transcript of a video.

        ### Task:
        Extract up to 5 **viral moments** that are either **funny, shocking, or informative**.  
        Each selected moment **must be between 30 to 60 seconds long** and should be a meaningful combination of transcript entries.

        ### Strict Rules:
        - ✅ **Use only the provided timestamps** (Do NOT invent new timestamps).  
        - ✅ **Each extracted moment must consist of multiple transcript entries** to form a coherent 30-60 second segment.
        - ✅ **Ensure logical continuity**—the moment must make sense when viewed as a clip.
        - ✅ **Include the transcript excerpt** from the selected segment for reference.
        - ✅ **Return only valid JSON**, formatted like this:

        ```json
        [
            {{
                "start": 0.00,
                "end": 30.00,
                "transcript": "I'm gonna give my honest humble opinion... Another celebrity has just been accused of serious acts of violence.",
                "caption": "This celebrity just exposed the truth! 👀",
                "hashtags": ["#celebrity", "#drama", "#mustwatch"]
            }},
            {{
                "start": 45.00,
                "end": 75.00,
                "transcript": "Now, I'm not gonna pretend nothing's happened overnight... I'm gonna be open and honest as I always am.",
                "caption": "Wait… did they just say that?! 😱",
                "hashtags": ["#shocking", "#trending", "#viralclip"]
            }}
        ]
        ```

        ### Transcript JSON:  
        ```json
        {formatted_transcript}
        ```
    """

   
    response = ollama_chat([{"role": "user", "content": prompt}]).strip()
    print(response)
    try:
        json_data = json.loads(response)
        if isinstance(json_data, list) and all(isinstance(item, dict) and "start" in item and "end" in item for item in json_data):
            print(f"✅ Best moments identified: {json_data}")
            return json_data
        else:
            print(f"❌ AI response missing timestamps.")
    except json.JSONDecodeError as e:
        print(f"🔍 Raw AI Response: {response}")
        return []


# ✅ Function to trim video using best moments
def trim_video(video_path, moments):
    clips = []
    video = VideoFileClip(video_path)

    for i, moment in enumerate(moments[:5]):  # ✅ Max 5 clips
        start_time = float(moment["start"])
        end_time = float(moment["end"])

        output_file = f"short_clip_{i+1}.mp4"
        print(f"✂️ Cutting {output_file}: {moment['reason']} ({moment['start']} - {moment['end']})")
        
        clip = video.subclip(start_time, end_time)
        clip.write_videofile(output_file, codec="libx264", audio_codec="aac")
        clips.append(output_file)

    video.close()
    return clips

async def main():
    video_url = "https://www.youtube.com/watch?v=ydRy-noAv1Y"  # Example URL

    print("🔄 Processing YouTube video...")
    video_path = download_video(video_url)

    if not video_path:
        print("❌ Failed to download video.")
        return

    # ✅ Step 1: Transcribe the Video
    transcript = transcribe_audio(video_path)

    # ✅ Step 2: Ask AI for best timestamps
    best_moments = find_best_moments(transcript)

    if not best_moments:
        print("❌ No viral moments found.")
        return

    # ✅ Step 3: Cut those parts
    short_clips = trim_video(video_path, best_moments)

    if short_clips:
        print(f"✅ Generated {len(short_clips)} short clips: {short_clips}")
    else:
        print("❌ Failed to generate short clips.")

    os.remove(video_path)
    print("🗑️ Deleted temp video file.")


# Run the main function within an asyncio event loop
if __name__ == "__main__":
    asyncio.run(main())
