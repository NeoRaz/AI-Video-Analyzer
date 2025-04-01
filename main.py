import google.generativeai as genai
import asyncio
import os
import yt_dlp
from dotenv import load_dotenv
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import json
from faster_whisper import WhisperModel
import re
import moviepy.config as mpc

# Load environment variables
load_dotenv()

mpc.change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})  # Update with correct path

# ✅ Configure Gemini API key using the environment variable
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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

        output_file = f"short_clip_{i+1}.mp4"
        print(f"✂️ Cutting {output_file}: {moment['caption']} ({moment['start']} - {moment['end']})")
        
        clip = video.subclip(start_time, end_time)
        clip.write_videofile(output_file, codec="libx264", audio_codec="aac")
        clips.append(output_file)

    video.close()
    return clips


def format_for_youtube_reels(input_video, output_video):
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


def add_subtitles(input_video, relevant_transcript, output_video):
    """Overlay subtitles from relevant transcript onto video with margin around the text."""
    clip = VideoFileClip(input_video)
    
    # Get the FPS of the input video
    fps = clip.fps
    
    subtitle_clips = []
    start_time = 0
    duration_per_line = clip.duration / len(relevant_transcript)
    
    # Adjust font size and margin to add space around subtitles
    font_size = 50
    subtitle_margin = 20  # Margin around subtitle text
    
    # Set up the height for the subtitle box (black background)
    box_height = 100  # You can adjust this depending on how tall you want the black box to be
    box_color = (0, 0, 0)  # Black color for the box
    
    # Adjust the position to move subtitles higher
    vertical_position = clip.h - box_height - 150  # This will push the subtitles 150px higher from the bottom
    
    for line in relevant_transcript:
        # Create subtitle clip with black background for better readability
        subtitle = TextClip(line["text"], fontsize=font_size, color='white', bg_color='black', size=(clip.w - 2*subtitle_margin, None))
        
        # Position the subtitle clip at the new vertical position
        subtitle = subtitle.set_position(('center', vertical_position)).set_duration(duration_per_line)
        subtitle = subtitle.set_start(start_time)
        start_time += duration_per_line
        subtitle_clips.append(subtitle)
    
    # Create the final video with subtitles over a black bar
    final = CompositeVideoClip([clip] + subtitle_clips)

    # Add the black box background at the bottom for the subtitles
    final = final.on_color(size=(clip.w, clip.h + box_height), color=box_color, pos=('center', 'bottom'))
    
    # Save final video with subtitles
    final.write_videofile(output_video, codec='libx264', audio_codec='aac', fps=fps)  # Use the input video's FPS




def process_video(input_video, transcript_data, output_video):
    temp1 = "temp_resized.mp4"
    temp2 = "temp_subtitled.mp4"
    
    # Format video to vertical
    format_for_youtube_reels(input_video, temp1)
    
    # Add subtitles
    add_subtitles(temp1, transcript_data, temp2)
    
    # Final processed video is saved as the output video
    final_clip = VideoFileClip(temp2)
    final_clip.write_videofile(output_video, codec='libx264', audio_codec='aac', fps=30)

    # Ensure closure and cleanup of temp files
    os.remove(temp1)
    os.remove(temp2)
    final_clip.close()
    print(f"✅ Final processed video saved as {output_video}")


def get_relevant_transcript(transcript_data, start_time, end_time):
    """Filter the transcript to get the relevant portion for the current clip."""
    relevant_lines = []
    for segment in transcript_data:
        if (segment["start"] >= start_time and segment["end"] <= end_time):
            relevant_lines.append(segment)
    return relevant_lines


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
        start_time = best_moments[short_clips.index(clip)]["start"]
        end_time = best_moments[short_clips.index(clip)]["end"]
        
        # Get the relevant transcript for the current clip
        relevant_transcript = get_relevant_transcript(transcript, start_time, end_time)
        
        output_video = f"final_{clip}"
        process_video(clip, relevant_transcript, output_video)  # Apply formatting and effects
        final_clips.append(output_video)
        os.remove(clip)  # Clean up temp clips

    print(f"🎉 Final processed videos: {final_clips}")



# Run the main function within an asyncio event loop
if __name__ == "__main__":
    asyncio.run(main())
