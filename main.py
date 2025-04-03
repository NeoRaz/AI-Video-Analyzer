import asyncio
import os
from utils import download_video, transcribe_audio, load_config, find_best_moments, trim_video, process_video, save_final_videos, cleanup_temp_files
import moviepy.config as mpc

mpc.change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})  # Update with correct path


async def main():
    config = load_config()
    video_url = config["video_url"]

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

    # Ensure closure and cleanup of temp files
    cleanup_temp_files()

    print(f"🎉 Final processed videos: {final_clips}")

# Run the main function within an asyncio event loop
if __name__ == "__main__":
    asyncio.run(main())
     