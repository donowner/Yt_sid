import os
import yt_dlp
import tempfile
from flask import Flask, render_template_string, request, send_file
from youtubesearchpython import VideosSearch, Video, PlaylistsSearch

app = Flask(__name__)

# Ensure ffmpeg is installed
os.system('bash install_ffmpeg.sh')

from flask import Flask, send_file, abort
import yt_dlp
import os

app = Flask(__name__)

# Function to download the video thumbnail
def download_thumbnail(video_id):
    ydl_opts = {
        'skip_download': True,
        'writethumbnail': True,
        'outtmpl': f'thumbnails/{video_id}.%(ext)s',
        'cookiefile': 'cookies.txt',  # Specify the path to the cookies file
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f'https://www.youtube.com/watch?v={video_id}'])
    
    for ext in ['jpg', 'webp', 'png']:
        thumbnail_path = f'thumbnails/{video_id}.{ext}'
        if os.path.exists(thumbnail_path):
            return thumbnail_path
    return None

# Function to download the video
def download_video(video_id):
    ydl_opts = {
        'format': 'best',
        'outtmpl': f'videos/{video_id}.%(ext)s',
        'cookiefile': 'cookies.txt',  # Specify the path to the cookies file
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f'https://www.youtube.com/watch?v={video_id}'])
    
    for ext in ['mp4', 'webm']:
        video_path = f'videos/{video_id}.{ext}'
        if os.path.exists(video_path):
            return video_path
    return None

# Function to download the audio
def download_audio(video_id):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'audios/{video_id}.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'cookiefile': 'cookies.txt',  # Specify the path to the cookies file
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f'https://www.youtube.com/watch?v={video_id}'])
    except yt_dlp.utils.DownloadError:
        # Fallback to medium quality if original quality is not available
        ydl_opts['format'] = 'bestaudio[abr<=128]/best[abr<=128]'
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f'https://www.youtube.com/watch?v={video_id}'])
    
    for ext in ['mp3']:
        audio_path = f'audios/{video_id}.{ext}'
        if os.path.exists(audio_path):
            return audio_path
    return None

@app.route('/thumbnail/<video_id>', methods=['GET'])
def get_thumbnail(video_id):
    thumbnail_path = download_thumbnail(video_id)
    if thumbnail_path:
        return send_file(thumbnail_path, as_attachment=True)
    else:
        abort(404, description="Thumbnail not found")

@app.route('/video/<video_id>', methods=['GET'])
def get_video(video_id):
    video_path = download_video(video_id)
    if video_path:
        return send_file(video_path, as_attachment=True)
    else:
        abort(404, description="Video not found")

@app.route('/audio/<video_id>', methods=['GET'])
def get_audio(video_id):
    audio_path = download_audio(video_id)
    if audio_path:
        return send_file(audio_path, as_attachment=True)
    else:
        abort(404, description="Audio not found")

if __name__ == '__main__':
    if not os.path.exists('thumbnails'):
        os.makedirs('thumbnails')
    if not os.path.exists('videos'):
        os.makedirs('videos')
    if not os.path.exists('audios'):
        os.makedirs('audios')
    app.run(debug=True, host='0.0.0.0', port=5000)


@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    format_id = request.form['format_id']
    file_path, filename = download_with_ytdlp(url, format_id)
    return send_file(file_path, as_attachment=True, download_name=filename)

@app.route('/download_song', methods=['POST'])
def download_song():
    song_url = request.form['song_url']
    # Logic to download song by URL or video ID
    # Example: Assuming you have a function to handle song downloads
    file_path, filename = download_song_by_url(song_url)
    return send_file(file_path, as_attachment=True, download_name=filename)

def search_youtube(query):
    videos_search = VideosSearch(query, limit=10)
    videos = []
    for video in videos_search.result()['result']:
        videos.append({
            'id': video['id'],
            'url': video['link'],
            'thumbnail': video['thumbnails'][0]['url'],
            'title': video['title'],
            'duration': video.get('duration', 'N/A'),
            'type': 'video'
        })
    # Example: Also search for songs using another library like Spotify API
    return videos

def download_song_by_url(song_url):
    # Logic to download song by URL or video ID using yt_dlp or other methods
    temp_dir = tempfile.gettempdir()
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(song_url, download=True)
        file_path = ydl.prepare_filename(info_dict)
        file_extension = info_dict.get('ext', 'mp3')
        file_title = info_dict.get('title', 'downloaded_song')
        filename = f"{file_title}.{file_extension}"
    return file_path, filename

def get_available_formats(url):
    ydl_opts = {'listformats': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        formats = info_dict['formats']
        available_formats = []

        for fmt in formats:
            if fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none':
                if 'height' in fmt:
                    label = f"{fmt['height']}p ({fmt['format_note']})"
                else:
                    label = fmt['format_note']
                available_formats.append({'format_id': fmt['format_id'], 'label': label})

        return available_formats

def download_with_ytdlp(url, format_id):
    temp_dir = tempfile.gettempdir()
    ydl_opts = {
        'format': format_id,
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info_dict)
        file_extension = info_dict.get('ext', 'mp4')
        file_title = info_dict.get('title', 'downloaded_video')
        filename = f"{file_title}.{file_extension}"
        return file_path, filename

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
