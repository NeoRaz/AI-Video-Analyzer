from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip, ColorClip
import os
from utils.transcriber import transcribe_audio
from utils.config_loader import load_config
from datetime import datetime
from constants import FORMAT_ONE, FORMAT_TWO
from utils.file_utils import save_clip_metadata

def trim_video(video_path, moments):
    clips = []
    video = VideoFileClip(video_path)

    for i, moment in enumerate(moments[:5]):  # ✅ Max 5 clips
        start_time = float(moment["start"])
        end_time = float(moment["end"])

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_title = moment['video_title']
        output_file = f"temp/{video_title}_{timestamp}.mp4"
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
    if video_type == FORMAT_ONE:
        reel_format_one(input_video=input_video, output_video=output_video)
    elif video_type == FORMAT_TWO:
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

    temp1 = "temp/temp_resized.mp4"
    temp2 = "temp/temp_subtitled.mp4"
    
    # Format video to vertical
    format_for_youtube_reels(input_video, temp1)
    
    # Final video with subs
    if subtitles:
        add_subtitles(temp1, temp2)
        final_clip = VideoFileClip(temp2)
        final_clip.write_videofile(output_video, codec='libx264', audio_codec='aac', fps=30)

    # Final video without subs
    else:
        final_clip = VideoFileClip(temp1)
        final_clip.write_videofile(output_video, codec='libx264', audio_codec='aac', fps=30)


    final_clip.close()
    print(f"✅ Final processed video saved as {output_video}")
