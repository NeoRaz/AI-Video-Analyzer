import os
import json

def cleanup_temp_files():
    temp_folder = "temp"
    if os.path.exists(temp_folder):
        for file in os.listdir(temp_folder):
            os.remove(os.path.join(temp_folder, file))

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

