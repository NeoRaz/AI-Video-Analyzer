from faster_whisper import WhisperModel
from utils.config_loader import load_config

def transcribe_audio(video_path):
    print(f"📝 Transcribing {video_path} using WhisperModel (CPU)...")

    config = load_config()
    max_words_per_segment = config["max_words_per_segment"]

    # Load the Whisper model
    model = WhisperModel("small", device="cpu", compute_type="int8")  # Optimized for CPU
    segments, word_timestamps = model.transcribe(video_path, word_timestamps=True)  # Request word-level timestamps

    # ✅ Store transcript with timestamps
    transcript_data = []
    transcript_text = ""

    for segment in segments:
        start = segment.start
        end = segment.end
        segment_words = segment.words  # Access words directly from the segment

        # Split words based on the max_words_per_segment
        current_words = []
        current_start = start
        for word_info in segment_words:
            word = word_info.word  # Access 'word' attribute directly
            word_start = word_info.start  # Access 'start' attribute directly
            word_end = word_info.end  # Access 'end' attribute directly
            
            current_words.append(word)

            # When we reach the max number of words, save the current chunk
            if len(current_words) >= max_words_per_segment:
                chunk_end = word_end
                transcript_data.append({"start": current_start, "end": chunk_end, "text": " ".join(current_words)})
                transcript_text += f"[{current_start:.2f} - {chunk_end:.2f}] {' '.join(current_words)}\n"
                
                # Reset for next chunk
                current_words = []
                current_start = word_end  # Next segment starts from the end of the current word
        
        # Add any remaining words as a final chunk
        if current_words:
            chunk_end = word_end
            transcript_data.append({"start": current_start, "end": chunk_end, "text": " ".join(current_words)})
            transcript_text += f"[{current_start:.2f} - {chunk_end:.2f}] {' '.join(current_words)}\n"

    # ✅ Save transcript with timestamps to a file
    transcript_file = "temp/transcript.txt"
    with open(transcript_file, "w", encoding="utf-8") as file:
        file.write(transcript_text)

    print(f"📄 Transcript saved to {transcript_file}")
    return transcript_data  # Returns list of timestamps + text
