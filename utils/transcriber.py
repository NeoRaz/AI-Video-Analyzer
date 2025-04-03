from faster_whisper import WhisperModel

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
    transcript_file = "temp/transcript.txt"
    with open(transcript_file, "w", encoding="utf-8") as file:
        file.write(transcript_text)

    print(f"📄 Transcript saved to {transcript_file}")
    return transcript_data  # Returns list of timestamps + text
