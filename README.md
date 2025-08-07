# 🎬 AI Video Analyzer & Editor

An automated pipeline that takes a YouTube video, identifies funny moments using AI, cuts and edits those clips, adds subtitles, and exports short-form content for platforms like TikTok and Instagram Reels.

## ⚠️ Disclaimer

This project is for educational and experimental purposes only. Respect copyright laws when downloading and using third-party videos.

## ✨ Features

- 🧠 **AI-Powered Humor Detection**: Uses OpenAI to analyze video transcripts and detect funny moments.
- 🎥 **Video Processing**: Automatically cuts relevant clips based on timestamps and context.
- 💬 **Subtitles**: Generates accurate subtitles using Whisper and burns them into the video.
- 📱 **Short-Form Format**: Resizes output to mobile-friendly ratios (9:16) for TikTok, Reels, and YouTube Shorts.
- 🔁 **End-to-End Automation**: From download to export, no manual intervention needed.

## 🚀 How It Works

1. **Download** a YouTube video using `yt-dlp`.
2. **Transcribe** the audio using OpenAI’s Whisper model.
3. **Analyze** the transcript with GPT to find funny or interesting moments.
4. **Cut** the video using MoviePy and FFmpeg based on those timestamps.
5. **Add Subtitles** with styling and synchronization.
6. **Export** final videos in vertical short format.

## 🛠️ Tech Stack

- **Python** – core scripting and orchestration
- **OpenAI GPT-4** – for humor/context analysis
- **Whisper API** – for speech-to-text transcription
- **MoviePy & FFmpeg** – for cutting, editing, and formatting video
- **yt-dlp** – to download YouTube videos

## 📂 Example Output

> Coming soon – will upload demo videos and screenshots.

## 📦 Installation

To run the project locally, you'll need:

- Python 3.9+
- FFmpeg installed and available in PATH
- AI API key

```bash
git clone https://github.com/nimarazavi/funny-moment-extractor.git
cd funny-moment-extractor
pip install -r requirements.txt
