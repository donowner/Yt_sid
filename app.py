import os
import yt_dlp
import tempfile
from flask import Flask, render_template_string, request, send_file
from youtubesearchpython import VideosSearch, Video, PlaylistsSearch

app = Flask(__name__)

# Ensure ffmpeg is installed
os.system('bash install_ffmpeg.sh')
from aiohttp import web
from flask import Flask, send_file, abort
import yt_dlp
import os

app = Flask(__name__)


from aiohttp import web
import re
import time
import math
import logging
import secrets
import mimetypes
from aiohttp import web


routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(_):
    return web.json_response(
        {
            "server_status": "running",
            "telegram_bot": "@musicbot",
        }
    )
    
async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app


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


async def web_server():
    app = web.Application()
    app.add_routes([web.get('/thumbnail/{video_id}', download_thumbnail)])
    app.add_routes([web.get('/video/{video_id}', download_video)])
    app.add_routes([web.get('/audio/{video_id}', download_audio)])
    return app

if __name__ == '__main__':
    if not os.path.exists('thumbnails'):
        os.makedirs('thumbnails')
    if not os.path.exists('videos'):
        os.makedirs('videos')
    if not os.path.exists('audios'):
        os.makedirs('audios')
    
    web.run_app(web_server(), host='0.0.0.0', port=8080)
