import time
import json
import os
import re
import google.generativeai as genai
from dotenv import load_dotenv
from utils.config_loader import load_config

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Constants
RPM_LIMIT = 2
SECONDS_BETWEEN_CALLS = 60 / RPM_LIMIT  # 30 seconds for 2 RPM

def chunk_transcript(transcript_data, max_chunk_duration=600):
    chunks = []
    current_chunk = []
    current_duration = 0.0

    for entry in transcript_data:
        start = entry.get("start", 0.0)
        end = entry.get("end", 0.0)
        duration = end - start

        if current_duration + duration <= max_chunk_duration:
            current_chunk.append(entry)
            current_duration += duration
        else:
            chunks.append(current_chunk)
            current_chunk = [entry]
            current_duration = duration

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def distribute_moments(num_moments, num_chunks):
    base = num_moments // num_chunks
    remainder = num_moments % num_chunks
    return [base + 1 if i < remainder else base for i in range(num_chunks)]

def fix_json_formatting(raw_text):
    cleaned_text = re.sub(r"```json\n(.*?)\n```", r"\1", raw_text, flags=re.DOTALL).strip()
    if not cleaned_text.startswith('['):
        cleaned_text = f"[{cleaned_text}]"
    return cleaned_text

def extract_viral_moments_from_chunk(chunk, num_moments, min_time, max_time):
    formatted_transcript = json.dumps(chunk, indent=2)

    prompt = f"""
    You will receive a JSON transcript of a video.

    ### Task:
    Extract {num_moments} **viral moments** that are either **funny, shocking, or informative**.  
    Each selected moment **must be between {min_time} to {max_time} seconds long** and should be a meaningful combination of transcript entries.

    ### Strict Rules:
    - ✅ **Use only the provided timestamps** (Do NOT invent new timestamps).  
    - ✅ **Each extracted moment must consist of multiple transcript entries** to form a coherent {min_time}-{max_time} second segment.
    - ✅ **Ensure logical continuity**—the moment must make sense when viewed as a clip.
    - ✅ **Include the transcript excerpt** from the selected segment for reference.
    - ✅ **Ensure all video titles generated are unique.
    - ✅ **Return only valid JSON**, formatted like this:

    ```json
    [
        {{
            "start": 0.00,
            "end": 30.00,
            "transcript": "I'm gonna give my honest humble opinion... Another celebrity has just been accused of serious acts of violence.",
            "caption": "This celebrity just exposed the truth! 👀",
            "video_title": "celebrity_exposed"
        }} 
    ]
    ```

    ### Transcript JSON:  
    ```json
    {formatted_transcript}
    ```
    """

    try:
        response = genai.GenerativeModel("gemini-1.5-pro").generate_content(prompt)
        raw_text = response.text.strip()
        fixed_text = fix_json_formatting(raw_text)
        json_data = json.loads(fixed_text)

        if isinstance(json_data, list) and all(
            isinstance(item, dict) and 
            "start" in item and "end" in item and 
            "transcript" in item and "caption" in item and "video_title" in item
            for item in json_data
        ):
            return json_data
        else:
            print("❌ Skipping: Invalid structure returned.")
            return []

    except Exception as e:
        print(f"❌ Error processing chunk: {e}")
        return []

def find_best_moments(transcript_data):
    config = load_config()
    number_of_viral_moments = config["number_of_viral_moments"]
    minimum_moment_time = config["minimum_moment_time"]
    maximum_moment_time = config["maximum_moment_time"]

    chunks = chunk_transcript(transcript_data)
    print(f"🔹 Transcript split into {len(chunks)} chunks.")

    distribution = distribute_moments(number_of_viral_moments, len(chunks))

    all_moments = []
    for idx, (chunk, num_moments) in enumerate(zip(chunks, distribution)):
        print(f"🔸 Processing chunk {idx+1}/{len(chunks)} with {num_moments} moments...")

        moments = extract_viral_moments_from_chunk(chunk, num_moments, minimum_moment_time, maximum_moment_time)
        all_moments.extend(moments)

        if idx < len(chunks) - 1:
            print(f"⏳ Sleeping {SECONDS_BETWEEN_CALLS} seconds to respect RPM...")
            time.sleep(SECONDS_BETWEEN_CALLS)

    print(f"✅ Final viral moments count: {len(all_moments)}")
    return all_moments
