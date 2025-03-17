import asyncio
import os
import ollama  # ✅ Import Ollama
import yt_dlp  # ✅ Use yt-dlp instead of pytube
from autogen_agentchat.agents import AssistantAgent
from dotenv import load_dotenv
from moviepy.editor import VideoFileClip

# Load environment variables
load_dotenv()

# ✅ Function to interact with Ollama
def ollama_chat(messages):
    response = ollama.chat(model="llama3", messages=messages)
    return response["message"]["content"]

# ✅ Function to download & trim video
def process_video(url):
    try:
        print(f"📥 Downloading video from: {url}")
        
        # ✅ Use yt-dlp to download video
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'temp_video.mp4',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        print(f"✂️ Trimming video: temp_video.mp4")
        clip = VideoFileClip("temp_video.mp4").subclip(5, 15)  # Trim first 5 seconds
        output_file = "short_video.mp4"
        clip.write_videofile(output_file, codec="libx264", audio_codec="aac")

        print(f"✅ Short video saved: {output_file}")
        return output_file
    except Exception as e:
        print(f"❌ Error processing video: {e}")
        return None

async def main():
    # ✅ Create AssistantAgent with Ollama function
    assistant = AssistantAgent(
        name="llama_assistant",
        model_client=lambda messages: ollama_chat(messages)  # ✅ Pass function directly
    )

    # ✅ No manual input; processing video directly
    video_url = "https://www.youtube.com/watch?v=ydRy-noAv1Y"  # Example URL

    print("🔄 Processing YouTube video...")
    short_video = process_video(video_url)

    # ✅ Send message to AI assistant & get a response
    if short_video:
        message = f"✅ Short video '{short_video}' has been successfully created!"
    else:
        message = "❌ Failed to process video."

    print(f"🤖 AI Input: {message}")
    
    # ✅ Fix: Use correct method `.generate_oai_reply()`
    ai_response = ollama_chat([{"role": "user", "content": message}])

    # ✅ Print AI's response
    print(f"🤖 AI Response: {ai_response}")

# Run the main function within an asyncio event loop
if __name__ == "__main__":
    asyncio.run(main())
