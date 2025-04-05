import json
import google.generativeai as genai
import os
import re
from dotenv import load_dotenv
from utils.config_loader import load_config

# Load environment variables
load_dotenv()

# Configure Gemini API Key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def find_best_moments(transcript_data):
    """
    Extracts viral moments from a video transcript.

    Parameters:
    - transcript_data (list): The video transcript as a structured JSON list.
    
    Returns:
    - list: Extracted moments with start/end times, captions, and hashtags.
    """
    
    config = load_config()
    number_of_viral_moments = config["number_of_viral_moments"]
    minimum_moment_time = config["minimum_moment_time"]
    maximum_moment_time = config["maximum_moment_time"]

    # Convert transcript data to formatted JSON for AI prompt
    formatted_transcript = json.dumps(transcript_data, indent=2)

    prompt = f"""
    You will receive a JSON transcript of a video.

    ### Task:
    Extract {number_of_viral_moments} **viral moments** that are either **funny, shocking, or informative**.  
    Each selected moment **must be between {minimum_moment_time} to {maximum_moment_time} seconds long** and should be a meaningful combination of transcript entries.

    ### Strict Rules:
    - ✅ **Use only the provided timestamps** (Do NOT invent new timestamps).  
    - ✅ **Each extracted moment must consist of multiple transcript entries** to form a coherent {minimum_moment_time}-{maximum_moment_time} second segment.
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
