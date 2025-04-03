import yt_dlp

def download_video(url):
    try:
        print(f"📥 Downloading video from: {url}")
        
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'temp/temp_video.mp4',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        print(f"✅ Video downloaded: temp_video.mp4")
        return "temp/temp_video.mp4"
    except Exception as e:
        print(f"❌ Error downloading video: {e}")
        return None
