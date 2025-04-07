from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip, concatenate_audioclips, AudioFileClip, CompositeAudioClip
import os
from utils.transcriber import transcribe_audio
from utils.config_loader import load_config
from datetime import datetime
from constants import FORMAT_ONE, FORMAT_TWO
from utils.file_utils import save_clip_metadata
import random

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
    """Convert video to vertical (1080x1920) format for YouTube Reels without stretching the video.
       Optionally plays a short audio caption at the start along with the original audio.
    """
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
    """Formats the video for YouTube Reels with the top half as the main video and the bottom half as a game filler,
       ensuring correct aspect ratio without stretching or black bars. Optionally overlays a short caption audio at start.
    """

    # Load main video
    main_clip = VideoFileClip(input_video)
    original_width, original_height = main_clip.size

    # Resize and center-crop main video to fit exactly in the top half (1080x960)
    main_clip_resized = main_clip.crop(
        x_center=original_width / 2,
        y_center=original_height / 2,
        width=min(original_width, 1080),
        height=min(original_height, 960)
    ).resize((1080, 960))

    # Locate filler video
    filler_folder = "video_fillers"
    filler_videos = [f for f in os.listdir(filler_folder) if f.endswith(('.mp4', '.mov', '.avi'))]

    if not filler_videos:
        raise FileNotFoundError("No filler video found in the 'video_fillers' directory.")

    filler_path = os.path.join(filler_folder, random.choice(filler_videos))
    filler_clip = VideoFileClip(filler_path).subclip(0, min(main_clip.duration, VideoFileClip(filler_path).duration))

    # Resize filler only if it's narrower than 1080px
    filler_width, filler_height = filler_clip.size
    if filler_width < 1080:
        scale_factor = 1080 / filler_width
        filler_clip = filler_clip.resize(width=1080, height=int(filler_height * scale_factor))

    # Crop starting from 5% above the bottom
    filler_width, filler_height = filler_clip.size
    y1 = max(0, filler_height - 960 - int(filler_height * 0.15))
    y2 = y1 + 960
    filler_clip_cropped = filler_clip.crop(x1=0, x2=1080, y1=y1, y2=y2)

    # Position the clips
    main_clip_positioned = main_clip_resized.set_position((0, 0))
    filler_clip_positioned = filler_clip_cropped.set_position((0, 960))

    # Combine into a single vertical video
    final_clip = CompositeVideoClip(
        [main_clip_positioned, filler_clip_positioned],
        size=(1080, 1920),
        bg_color=(0, 0, 0)
    )

    # Save final output
    final_clip.write_videofile(output_video, codec='libx264', audio_codec='aac', fps=main_clip.fps)


def add_subtitles(input_video, output_video):
    """Overlay subtitles from relevant transcript onto video, centered on screen with custom font."""
    print(f"🎬 Loading video: {input_video}")
    clip = VideoFileClip(input_video)
    print(f"✅ Video loaded. Duration: {clip.duration}s, Resolution: {clip.w}x{clip.h}, FPS: {clip.fps}")

    print("🧠 Transcribing audio...")
    relevant_transcript = transcribe_audio(input_video)  # Replace with your actual transcription function
    print(f"📝 Transcription complete. Found {len(relevant_transcript)} lines.")

    fps = clip.fps
    subtitle_clips = []

    # Subtitle settings
    print("⚙️ Loading subtitle configuration...")
    config = load_config()
    font_path = config["font_path"]
    text_color = config["subtitle_color"]
    font_size = 60
    subtitle_margin = 40
    shadow_color = 'black'
    shadow_offset = (2, 2)
    position = ('center', 'center')
    print(f"🎨 Font loaded: {font_path}")

    subtitle_height = 100
    vertical_position = clip.h - subtitle_height - subtitle_margin

    horizontal_position = position[0]
    vertical_position_offset = position[1]

    if vertical_position_offset == 'bottom':
        vertical_position = clip.h - subtitle_height - subtitle_margin
    elif vertical_position_offset == 'top':
        vertical_position = subtitle_margin
    else:
        vertical_position = clip.h // 2

    print("🧱 Building subtitle clips...")

    for idx, line in enumerate(relevant_transcript):
        start_time = line["start"]
        end_time = line["end"]
        duration = end_time - start_time
        text = line["text"]

        print(f"🕒 Subtitle {idx+1}/{len(relevant_transcript)}: {start_time}s to {end_time}s — '{text}'")

        # Create subtitle text clip
        subtitle = TextClip(
            text,
            fontsize=font_size,
            color=text_color,
            font=font_path,
            size=(clip.w - 2 * subtitle_margin, None),
            method="caption"
        )

        # Create shadow text clip
        shadow = TextClip(
            text,
            fontsize=font_size,
            color=shadow_color,
            font=font_path,
            size=(clip.w - 2 * subtitle_margin, None),
            method="caption"
        )

        # Apply positions and durations
        shadow = shadow.set_position((horizontal_position, vertical_position + shadow_offset[1])) \
                       .set_duration(duration).set_start(start_time)

        subtitle = subtitle.set_position((horizontal_position, vertical_position)) \
                           .set_duration(duration).set_start(start_time)

        subtitle_clips.append(shadow)
        subtitle_clips.append(subtitle)

    print("🧩 Combining video and subtitles...")
    final = CompositeVideoClip([clip] + subtitle_clips)

    print(f"💾 Exporting final video to {output_video}...")
    final.write_videofile(output_video, codec='libx264', audio_codec='aac', fps=fps)

    print(f"✅ Done! Final video saved to {output_video}")

def process_video(input_video, output_video, voice_caption):
    config = load_config()
    subtitles = config["add_subtitles"]

    temp1 = "temp/temp_resized.mp4"
    temp2 = "temp/temp_subtitled.mp4"
    
    # Format video to vertical
    format_for_youtube_reels(input_video, temp1)

    # Decide which video to load based on subtitle flag
    if subtitles:
        add_subtitles(temp1, temp2)
        video_path = temp2
    else:
        video_path = temp1

    final_clip = VideoFileClip(video_path)

    # Handle optional caption audio
    if voice_caption is not None:
        caption_audio = AudioFileClip(voice_caption)

        # Mute original audio during caption if needed
        caption_duration = caption_audio.duration
        original_audio = final_clip.audio

        muted_part = original_audio.subclip(0, caption_duration).volumex(0)
        rest_part = original_audio.subclip(caption_duration)
        adjusted_original = concatenate_audioclips([muted_part, rest_part])

        # Combine caption voice and adjusted original audio
        final_audio = CompositeAudioClip([adjusted_original, caption_audio.set_start(0)])
        final_clip = final_clip.set_audio(final_audio)

    # Export final video
    final_clip.write_videofile(output_video, codec='libx264', audio_codec='aac', fps=30)
    final_clip.close()
    print(f"✅ Final processed video saved as {output_video}")