import google.generativeai as genai
import asyncio
import os
import yt_dlp
from dotenv import load_dotenv
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip
import json
from faster_whisper import WhisperModel
import re
import moviepy.config as mpc
from datetime import datetime

# Load environment variables
load_dotenv()

mpc.change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})  # Update with correct path

# ✅ Configure Gemini API key using the environment variable
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def load_config(filename='config.json'):
    try:
        with open(filename, 'r') as config_file:
            config = json.load(config_file)
            return config
    except FileNotFoundError:
        print(f"File {filename} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Failed to parse {filename}.")
        return None

# ✅ Function to transcribe video using Whisper
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

# ✅ Function to find best moments (timestamps) using Gemini LLM
def fix_json_formatting(raw_text):
    """
    Attempt to fix common issues with malformed JSON responses, such as missing brackets or extra characters.
    
    Parameters:
    - raw_text (str): Raw AI response text.
    
    Returns:
    - str: Fixed JSON string.
    """
    # Remove any potential code block wrapping
    cleaned_text = re.sub(r"```json\n(.*?)\n```", r"\1", raw_text, flags=re.DOTALL).strip()
    
    # Attempt to fix any missing or extra characters that break the JSON format
    # For example, ensure there is a valid list at the top level
    if not cleaned_text.startswith('['):
        cleaned_text = f"[{cleaned_text}]"
    
    return cleaned_text

def find_best_moments(transcript_data):
    """
    Extracts viral moments from a video transcript.

    Parameters:
    - transcript_data (list): The video transcript as a structured JSON list.
    
    Returns:
    - list: Extracted moments with start/end times, captions, and hashtags.
    """
    
    # Convert transcript data to formatted JSON for AI prompt
    formatted_transcript = json.dumps(transcript_data, indent=2)

    prompt = f"""
    You will receive a JSON transcript of a video.

    ### Task:
    Extract 1 **viral moments** that are either **funny, shocking, or informative**.  
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
            "video_title": "celebrity_exposed",
        }} 
    ]
    ```

    ### Transcript JSON:  
    ```json
    {formatted_transcript}
    ```
    """

    # Generate AI response (assuming genai is your AI model interface)
    response = genai.GenerativeModel("gemini-1.5-pro").generate_content(prompt)
    raw_text = response.text.strip()

    # Fix any potential JSON formatting issues
    fixed_text = fix_json_formatting(raw_text)

    try:
        # Attempt to parse the fixed JSON response
        json_data = json.loads(fixed_text)

        # Validate if the response is a list of dictionaries with required keys
        if isinstance(json_data, list) and all(
            isinstance(item, dict) and 
            "start" in item and "end" in item and 
            "transcript" in item and "caption" in item
            for item in json_data
        ):
            print(f"✅ Successfully extracted viral moments: {json_data}")
            return json_data
        else:
            print(f"❌ AI response does not contain the expected structure.")
            return []
    
    except json.JSONDecodeError as e:
        print(f"❌ JSON Decode Error: {e}")
        print(f"🔍 Raw AI Response:\n{raw_text}")
        return []


# ✅ Function to trim video using best moments
def trim_video(video_path, moments):
    clips = []
    video = VideoFileClip(video_path)

    for i, moment in enumerate(moments[:5]):  # ✅ Max 5 clips
        start_time = float(moment["start"])
        end_time = float(moment["end"])

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_title = moment['video_title']
        output_file = f"{video_title}_{timestamp}.mp4"
        print(f"✂️ Cutting {output_file}: {moment['caption']} ({moment['start']} - {moment['end']})")
        
        clip = video.subclip(start_time, end_time)
        clip.write_videofile(output_file, codec="libx264", audio_codec="aac")
        clips.append(output_file)

        save_clip_metadata(moment, f"{video_title}_{timestamp}.json")

    video.close()
    return clips


def format_for_youtube_reels(input_video, output_video):
    """Create Short Video"""
    config = load_config()
    video_type = config["video_type"]
    if video_type == "1":
        reel_format_one(input_video=input_video, output_video=output_video)
    elif video_type == "2":
        reel_format_two(input_video=input_video, output_video=output_video)


def reel_format_one(input_video, output_video):
    """Convert video to vertical (1080x1920) format for YouTube Reels without stretching the video."""
    clip = VideoFileClip(input_video)
    original_width, original_height = clip.size

    # Resize the video to fit within a square (1080x1080) while maintaining aspect ratio
    new_width = 1080
    new_height = int(new_width * original_height / original_width) if original_width > original_height else 1080

    # Resize video to fit within the square
    clip_resized = clip.resize(newsize=(new_width, new_height))

    # Set the final video size to 1080x1920 and center the video with black bars
    final_clip = clip_resized.on_color(size=(1080, 1920), color=(0, 0, 0), pos='center')

    # Save final output
    final_clip.write_videofile(output_video, codec='libx264', audio_codec='aac', fps=clip.fps)


def reel_format_two(input_video, output_video):
    """Formats the video for YouTube Reels with the top half as the main video and the bottom half as a game filler, ensuring correct aspect ratio without stretching or black bars."""
    
    # Load main video
    main_clip = VideoFileClip(input_video)
    original_width, original_height = main_clip.size
    
    # Resize and center-crop main video to fit exactly in the top half (1080x960)
    main_clip_resized = main_clip.crop(x_center=original_width / 2, y_center=original_height / 2, width=min(original_width, 1080), height=min(original_height, 960))
    main_clip_resized = main_clip_resized.resize((1080, 960))
    
    # Locate filler video
    filler_folder = "video_fillers"
    filler_videos = [f for f in os.listdir(filler_folder) if f.endswith(('.mp4', '.mov', '.avi'))]
    
    if not filler_videos:
        raise FileNotFoundError("No filler video found in the 'video_fillers' directory.")
    
    filler_path = os.path.join(filler_folder, filler_videos[0])
    filler_clip = VideoFileClip(filler_path)
    
    # Trim filler video to match main video duration
    filler_clip = filler_clip.subclip(0, min(main_clip.duration, filler_clip.duration))
    
    # Resize filler only if it's narrower than 1080px (preserving height)
    filler_width, filler_height = filler_clip.size
    if filler_width < 1080:
        scale_factor = 1080 / filler_width
        filler_clip = filler_clip.resize(width=1080, height=int(filler_height * scale_factor))  # Maintain aspect ratio
    
    # New size after potential resize
    filler_width, filler_height = filler_clip.size

    # Crop starting from 5% above the bottom
    y1 = max(0, filler_height - 960 - int(filler_height * 0.15))
    y2 = y1 + 960

    filler_clip_cropped = filler_clip.crop(
        x1=0, x2=1080, 
        y1=y1, y2=y2
    )
    
    # Position the clips correctly
    main_clip_positioned = main_clip_resized.set_position((0, 0))
    filler_clip_positioned = filler_clip_cropped.set_position((0, 960))
    
    # Create final composite video of size 1080x1920
    final_clip = CompositeVideoClip([main_clip_positioned, filler_clip_positioned], size=(1080, 1920), bg_color=(0, 0, 0))
    
    # Save final output
    final_clip.write_videofile(output_video, codec='libx264', audio_codec='aac', fps=main_clip.fps)

def add_subtitles(input_video, output_video):
    """Overlay subtitles from relevant transcript onto video with a margin around the text."""
    clip = VideoFileClip(input_video)
    
    relevant_transcript = transcribe_audio(input_video)  # Get the transcript
    
    # Get the FPS of the input video
    fps = clip.fps
    
    subtitle_clips = []
    
    # Subtitle settings
    font_size = 50
    subtitle_margin = 20  # Margin around subtitles
    box_height = 100  # Height of the black box background
    box_color = (0, 0, 0)  # Black color for the box
    text_color = 'white'
    
    # Adjust the subtitle position dynamically
    vertical_position = clip.h - box_height - 50  # Push the subtitle higher (avoid bottom edge)
    
    for line in relevant_transcript:
        start_time = line["start"]
        end_time = line["end"]
        duration = end_time - start_time

        # Create subtitle text with background
        subtitle = TextClip(line["text"], fontsize=font_size, color=text_color, size=(clip.w - 2*subtitle_margin, None), method="caption")
        subtitle = subtitle.set_position(('center', vertical_position)).set_duration(duration).set_start(start_time)

        subtitle_clips.append(subtitle)
    
    # Create a black rectangle for the subtitle background
    black_box = ColorClip(size=(clip.w, box_height), color=box_color).set_position(('center', clip.h - box_height)).set_duration(clip.duration)

    # Composite the video with subtitles
    final = CompositeVideoClip([clip, black_box] + subtitle_clips)

    # Save the final video
    final.write_videofile(output_video, codec='libx264', audio_codec='aac', fps=fps)


def process_video(input_video, output_video):

    config = load_config()
    subtitles = config["add_subtitles"]

    temp1 = "temp_resized.mp4"
    temp2 = "temp_subtitled.mp4"
    
    # Format video to vertical
    format_for_youtube_reels(input_video, temp1)
    
    # Final video with no subs
    if subtitles:
        add_subtitles(temp1, temp2)
        final_clip = VideoFileClip(temp2)
        final_clip.write_videofile(output_video, codec='libx264', audio_codec='aac', fps=30)

    # Final video with subs
    else:
        final_clip = VideoFileClip(temp1)
        final_clip.write_videofile(output_video, codec='libx264', audio_codec='aac', fps=30)

    # Ensure closure and cleanup of temp files
    if temp1 and os.path.exists(temp1):
        os.remove(temp1)

    if temp2 and os.path.exists(temp2):
        os.remove(temp2)

    final_clip.close()
    print(f"✅ Final processed video saved as {output_video}")


def save_clip_metadata(moments, output_file, output_folder="metadata"):
    """
    Saves the metadata (captions, timestamps) for each generated clip in a JSON file.

    Parameters:
    - moments (list): List of extracted moments containing start, end, transcript, and caption.
    - output_folder (str): Folder to save the metadata files.
    """
    os.makedirs(output_folder, exist_ok=True)  # Ensure the folder exists
    
    metadata_file = os.path.join(output_folder, output_file)
    
    with open(metadata_file, "w", encoding="utf-8") as file:
        json.dump(moments, file, indent=4, ensure_ascii=False)
    
    print(f"📄 Clip metadata saved to {metadata_file}")


def save_final_videos(final_clips, output_folder="videos"):
    """
    Moves final processed videos to the 'videos/' folder.
    
    Parameters:
    - final_clips (list): List of filenames for final processed videos.
    - output_folder (str): Folder to store the final videos.
    """
    os.makedirs(output_folder, exist_ok=True)  # Ensure the folder exists
    
    for clip in final_clips:
        destination = os.path.join(output_folder, os.path.basename(clip))
        os.rename(clip, destination)
        print(f"📂 Moved {clip} to {destination}")
    
    print(f"✅ All final videos saved in '{output_folder}/' folder.")



async def main():
    video_url = "https://www.youtube.com/watch?v=R_ICzXotoQY"  # Example URL

    print("🔄 Processing YouTube video...")
    video_path = download_video(video_url)

    if not video_path:
        print("❌ Failed to download video.")
        return

    # ✅ Step 1: Transcribe the Video
    transcript = transcribe_audio(video_path)
    if not transcript:
        print("❌ Failed to transcribe video.")
        os.remove(video_path)  # Clean up
        return

    # ✅ Step 2: Find the best timestamps using Gemini
    best_moments = find_best_moments(transcript)
    if not best_moments:
        print("❌ No viral moments found.")
        os.remove(video_path)  # Clean up
        return

    # ✅ Step 3: Trim the best moments into short clips
    short_clips = trim_video(video_path, best_moments)
    os.remove(video_path)  # Remove the original video after trimming

    if not short_clips:
        print("❌ Failed to generate short clips.")
        return

    print(f"✅ Generated {len(short_clips)} short clips: {short_clips}")

    # ✅ Step 4: Format and Enhance Each Clip
    final_clips = []
    for clip in short_clips:
        output_video = f"{clip}"
        process_video(clip, output_video)  # Apply formatting and effects
        final_clips.append(output_video)

    save_final_videos(final_clips)

    # ✅ Cleanup transcript file after everything is done
    os.remove("transcript.txt")

    print(f"🎉 Final processed videos: {final_clips}")

# Run the main function within an asyncio event loop
if __name__ == "__main__":
    asyncio.run(main())
     