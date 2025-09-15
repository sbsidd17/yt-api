from flask import Flask, request, jsonify
import yt_dlp
import re
import os
import json
from urllib.parse import unquote

app = Flask(__name__)

# Default cookies for YouTube access
DEFAULT_COOKIES = {
    'CONSENT': 'YES+cb.20210328-17-p0.en-GB+FX+{}'.format(100),
    'SOCS': 'CAISNQgEEitib3FfaWRlbnRpdHlmcm9udGVuZHVpc2VydmVyXzIwMjMwNzI1LjA2X3AwGgJlbiACGgYIgL6ElgU'
}

def extract_video_id(url):
    """Extract video ID from various YouTube URL formats"""
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

def get_cookies_from_request():
    """Extract cookies from request or use defaults"""
    cookies_str = request.args.get('cookies', '')
    if cookies_str:
        try:
            # Try to parse as JSON
            return json.loads(unquote(cookies_str))
        except:
            # Fallback to string parsing
            cookies = {}
            for pair in unquote(cookies_str).split(';'):
                if '=' in pair:
                    key, value = pair.strip().split('=', 1)
                    cookies[key] = value
            return cookies
    return DEFAULT_COOKIES

def get_video_info(video_url, cookies):
    """Get video information using yt-dlp with cookies"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'cookies': cookies,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'referer': 'https://www.youtube.com/',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return info
    except Exception as e:
        print(f"Error extracting video info: {str(e)}")
        return None

def format_response(video_info):
    """Format the response according to the required structure"""
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
    
    # Add audio-only entry
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
    """Main endpoint for extracting YouTube video links"""
    yt_link = request.args.get('ytlink')
    
    if not yt_link:
        return jsonify({"error": "No YouTube link provided"}), 400
    
    # Extract cookies from request or use defaults
    cookies = get_cookies_from_request()
    
    try:
        video_id = extract_video_id(yt_link)
        if not video_id:
            return jsonify({"error": "Invalid YouTube URL"}), 400
        
        standard_url = f"https://www.youtube.com/watch?v={video_id}"
        
        video_info = get_video_info(standard_url, cookies)
        if not video_info:
            return jsonify({
                "error": "Could not extract video information",
                "solution": "Try providing fresh YouTube cookies using the 'cookies' parameter"
            }), 500
        
        formatted_response = format_response(video_info)
        if not formatted_response:
            return jsonify({"error": "Could not format response"}), 500
        
        return jsonify(formatted_response)
    except Exception as e:
        return jsonify({
            "error": f"Failed to process request: {str(e)}",
            "solution": "Ensure you're providing valid YouTube cookies if required"
        }), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "youtube-extractor-api"})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
