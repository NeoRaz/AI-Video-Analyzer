# 🎬 AI Video Analyzer & Editor

An automated pipeline that takes a YouTube video, identifies funny moments using AI, cuts and edits those clips, adds subtitles, and exports short-form content for platforms like TikTok and Instagram Reels.

## ⚠️ Disclaimer:

This project is intended for educational and personal use only. Do not use it to download or republish copyrighted material without permission.
The author is not responsible for any misuse of this tool. Always comply with platform terms and local laws.


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
- **AI** – for humor/context analysis
- **MoviePy & FFmpeg** – for cutting, editing, and formatting video
- **yt-dlp** – to download YouTube videos

## 📂 Example Output

> Coming soon – will upload demo videos and screenshots.

### 🔐 API Keys

Create a `.env` file in the root directory with your credentials:

## 📦 Installation

To run the project locally, you'll need:

- Python 3.9+
- FFmpeg installed and available in PATH
- AI API key

```bash
git clone https://github.com/nimarazavi/funny-moment-extractor.git
cd funny-moment-extractor
pip install -r requirements.txt
