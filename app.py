from flask import Flask, request, jsonify
import yt_dlp
import re

app = Flask(__name__)

def extract_video_id(url):
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:shorts\/)([0-9A-Za-z_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_video_info(video_url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return info
    except Exception as e:
        print(f"Error extracting video info: {e}")
        return None

def format_response(video_info):
    if not video_info:
        return None
    
    formats = []
    for fmt in video_info.get('formats', []):
        if fmt.get('url'):
            quality = fmt.get('height', 0)
            quality_note = f"{quality}p" if quality else "audio"
            
            format_data = {
                "quality": quality,
                "quality_note": quality_note,
                "video_url": fmt.get('url', ''),
                "video_ext": fmt.get('ext', ''),
                "video_size": fmt.get('filesize', 0),
                "separate": 1 if fmt.get('acodec') != 'none' and fmt.get('vcodec') != 'none' else 0
            }
            
            if format_data['separate'] == 0 and fmt.get('acodec') != 'none':
                format_data['audio_url'] = fmt.get('url', '')
                format_data['audio_ext'] = fmt.get('ext', '')
                format_data['audio_size'] = fmt.get('filesize', 0)
            
            formats.append(format_data)
    
    # Group by quality and ensure proper formatting
    organized_formats = []
    quality_map = {}
    
    for fmt in formats:
        if fmt['quality'] not in quality_map:
            quality_map[fmt['quality']] = fmt
        else:
            if fmt.get('video_url') and quality_map[fmt['quality']].get('audio_url'):
                quality_map[fmt['quality']] = fmt
            elif fmt.get('audio_url') and quality_map[fmt['quality']].get('video_url'):
                quality_map[fmt['quality']]['audio_url'] = fmt['audio_url']
                quality_map[fmt['quality']]['audio_ext'] = fmt['audio_ext']
                quality_map[fmt['quality']]['audio_size'] = fmt['audio_size']
    
    for quality in sorted(quality_map.keys(), reverse=True):
        if quality > 0:
            organized_formats.append(quality_map[quality])
    
    audio_format = next((fmt for fmt in formats if fmt['quality'] == 0), None)
    if audio_format:
        organized_formats.append({
            "media_type": "audio",
            "resource_url": audio_format.get('url', ''),
            "preview_url": video_info.get('thumbnail', '')
        })
    
    response = {
        "text": video_info.get('title', ''),
        "medias": [
            {
                "media_type": "video",
                "resource_url": video_info.get('url', ''),
                "preview_url": video_info.get('thumbnail', ''),
                "formats": organized_formats
            }
        ],
        "overseas": 1
    }
    
    return response

@app.route('/')
def extract_youtube_links():
    yt_link = request.args.get('ytlink')
    
    if not yt_link:
        return jsonify({"error": "No YouTube link provided"}), 400
    
    video_id = extract_video_id(yt_link)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400
    
    standard_url = f"https://www.youtube.com/watch?v={video_id}"
    
    video_info = get_video_info(standard_url)
    if not video_info:
        return jsonify({"error": "Could not extract video information"}), 500
    
    formatted_response = format_response(video_info)
    if not formatted_response:
        return jsonify({"error": "Could not format response"}), 500
    
    return jsonify(formatted_response)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
