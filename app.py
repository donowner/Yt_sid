import os
import yt_dlp
import tempfile
from flask import Flask, render_template_string, request, send_file
from youtubesearchpython import VideosSearch, Video, PlaylistsSearch

app = Flask(__name__)

# Ensure ffmpeg is installed
os.system('bash install_ffmpeg.sh')

@app.route('/')
def index():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>YouTube Downloader</title>
        <style>
            /* Your CSS styles */
        </style>
        <script>
            /* Your JavaScript functions */
        </script>
    </head>
    <body onload="showTab('downloader')">
        <div class="tab-container">
            <div id="downloader" class="tab active" onclick="showTab('downloader')">YouTube Downloader</div>
            <div id="search" class="tab" onclick="showTab('search')">YouTube Search</div>
            <div id="song-downloader" class="tab" onclick="showTab('song-downloader')">Song Downloader</div>
        </div>

        <div id="downloader-content" class="content active">
            <div class="form-container">
                <form method="POST" action="/get_formats">
                    <input type="text" id="url" name="url" class="input-box" placeholder="Paste YouTube URL here" required>
                    <button type="submit" class="submit-button">Check and Download</button>
                </form>
            </div>
        </div>

        <div id="search-content" class="content">
            <div class="form-container">
                <form method="POST" action="/search">
                    <input type="text" id="query" name="query" class="input-box" placeholder="Search for videos or songs" required>
                    <button type="submit" class="submit-button">Search</button>
                </form>
            </div>
            <div id="search-results" class="form-container"></div>
        </div>

        <div id="song-downloader-content" class="content">
            <div class="form-container">
                <form method="POST" action="/download_song">
                    <input type="text" id="song_url" name="song_url" class="input-box" placeholder="Paste song URL or video ID" required>
                    <button type="submit" class="submit-button">Download Song</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_content)

@app.route('/get_formats', methods=['POST'])
def get_formats():
    url = request.form['url']
    formats = get_available_formats(url)

    html_content = """
    <div class="form-container">
        <h2>Select Quality</h2>
        <form method="POST" action="/download">
            <input type="hidden" name="url" value="{{ url }}">
            {% for fmt in formats %}
            <div>
                <input type="radio" id="{{ fmt['format_id'] }}" name="format_id" value="{{ fmt['format_id'] }}" required>
                <label for="{{ fmt['format_id'] }}">{{ fmt['label'] }}</label>
            </div>
            {% endfor %}
            <button type="submit" class="submit-button">Download</button>
        </form>
    </div>
    """
    return render_template_string(html_content, url=url, formats=formats)

@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    results = search_youtube(query)
    html_content = """
    <div class="form-container">
        <h2>Search Results</h2>
        <form method="POST" action="/get_formats">
            {% for result in results %}
            <div class="result-item">
                <input type="radio" id="{{ result['id'] }}" name="url" value="{{ result['url'] }}" required>
                <label for="{{ result['id'] }}">
                    {% if result['type'] == 'video' %}
                        <img src="{{ result['thumbnail'] }}" alt="Thumbnail" class="video-thumbnail">
                        <div class="video-details">
                            <div class="video-title">{{ result['title'] }}</div>
                            <div class="video-duration">{{ result['duration'] }}</div>
                        </div>
                    {% elif result['type'] == 'song' %}
                        <img src="{{ result['thumbnail'] }}" alt="Thumbnail" class="song-thumbnail">
                        <div class="song-details">
                            <div class="song-title">{{ result['title'] }}</div>
                            <div class="song-artist">{{ result['artist'] }}</div>
                        </div>
                    {% endif %}
                </label>
            </div>
            {% endfor %}
            <button type="submit" class="submit-button">Download Selected</button>
        </form>
    </div>
    """
    return render_template_string(html_content, results=results)

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
