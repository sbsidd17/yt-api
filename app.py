from flask import Flask, request, jsonify
import yt_dlp
import re
import os
import tempfile

app = Flask(__name__)

def extract_video_id(url):
    """Extract YouTube video ID from various URL formats"""
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

def get_cookies_file():
    """Create a temporary cookies file in Netscape format"""
    netscape_cookies = """# Netscape HTTP Cookie File
# http://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file!  Do not edit.

.youtube.com	TRUE	/	FALSE	1791783098	HSID	AFbXNnuoQ38m_Isbf
.youtube.com	TRUE	/	TRUE	1791783098	SSID	AFL2ZkJmyWfDHkaOZ
.youtube.com	TRUE	/	FALSE	1791783098	APISID	nCO_x36hbH_spNK-/A3b9x-CuwQ3QTOlve
.youtube.com	TRUE	/	TRUE	1791783098	SAPISID	zCtKazkWDBFVUx4C/A5msKbJka5fNRD3r0
.youtube.com	TRUE	/	TRUE	1791783098	__Secure-1PAPISID	zCtKazkWDBFVUx4C/A5msKbJka5fNRD3r0
.youtube.com	TRUE	/	TRUE	1791783098	__Secure-3PAPISID	zCtKazkWDBFVUx4C/A5msKbJka5fNRD3r0
.youtube.com	TRUE	/	TRUE	1779869218	LOGIN_INFO	AFmmF2swRQIhAKL2Z2ZAax5R3zDe9Lk_CqWggt8BHqllF1U4JV6xUx_FAiAFgtC0x7g9I6FabrjcI6OCoxE79H0WLtY8-INoS1luvg:QUQ3MjNmeEpHNmNXNmpUSzc5OTYxblVBQmt4ZGlpSzhSdzBKSXRXYjZWZm93MDd4d1hLYUhjQ25lWWNqVEhnVjNpSFJtWlplMWtuejFtNl9md0IxOGlxSU1weGhxLVBYMXIwMGFVSmZOSEx2eGdKQkNJSF9MWV81QmZHMXFvRE01REtRZFNrUkRtX05HY2RTQ1E4ckZ3NGxubjlkZEtPMnFB
.youtube.com	TRUE	/	TRUE	1792519215	PREF	f6=40000000&tz=Asia.Calcutta&f7=100&f4=4000000
.youtube.com	TRUE	/	FALSE	1791783098	SID	g.a0001Ajf9_sjTGl9s20zBSYrLp1NCEuoMyKesfzXCrzC6S3ldwBP5D_IRS3Ch3Lna9dX8YrMBAACgYKAccSARISFQHGX2Mil0mncc1gs6VWFsm1OiB-nhoVAUF8yKqApfPdXRnWUYUoHD9YRvtw0076
.youtube.com	TRUE	/	TRUE	1791783098	__Secure-1PSID	g.a0001Ajf9_sjTGl9s20zBSYrLp1NCEuoMyKesfzXCrzC6S3ldwBPA5iLiDjXgk_nMW4G9pUYQgACgYKAfsSARISFQHGX2Mi837Vtd11pI6pJk-yJyVFqxoVAUF8yKrU3_7LGxCQSJnQLXeHmN3I0076
.youtube.com	TRUE	/	TRUE	1791783098	__Secure-3PSID	g.a0001Ajf9_sjTGl9s20zBSYrLp1NCEuoMyKesfzXCrzC6S3ldwBPy21O0PkO_4ynQoX6L25caQACgYKATISARISFQHGX2MizUeedIFHFItzwAYbmHAjdBoVAUF8yKp0-EqNYqGw93ZpPnBzgOSo0076
.youtube.com	TRUE	/	TRUE	1789495218	__Secure-1PSIDTS	sidts-CjEBmkD5S3iRF_RG0xNhWX_CE4Zyj5PwCNFLXKGLVul6YceVTxpLlniU4Nsqw2Sm-hO5EAA
.youtube.com	TRUE	/	TRUE	1789495218	__Secure-3PSIDTS	sidts-CjEBmkD5S3iRF_RG0xNhWX_CE4Zyj5PwCNFLXKGLVul6YceVTxpLlniU4Nsqw2Sm-hO5EAA
.youtube.com	TRUE	/	FALSE	1789495218	SIDCC	AKEyXzWWvMoxS9JqSSSMLWDA9iNLw7CIk3F8IlFLtWZohhdCiJxmvC2mLlTtJwJQNW-wX_4V
.youtube.com	TRUE	/	TRUE	1789495218	__Secure-1PSIDCC	AKEyXzWcOpwCVp9AnHgvN0jmksoWUBxVrmGh1yUlKl-wBnNTMoRsIXQFCVT14M4WghRciOlcSg
.youtube.com	TRUE	/	TRUE	1789495218	__Secure-3PSIDCC	AKEyXzWOMKT3N1cKBCWdufvUB_0oSQltgemPPCuJR9G_BA-930INV_awZu5PEAZTonQRkyOM"""
    
    # Create a temporary cookie file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(netscape_cookies)
        return f.name

def get_video_info(video_url, cookie_file):
    """Get video information using yt-dlp with cookies"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'cookiefile': cookie_file,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.youtube.com/',
        'geo_bypass': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'youtube_include_dash_manifest': False,
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
                "resource_url": video_info.get('webpage_url', ''),
                "preview_url": video_info.get('thumbnail', ''),
                "formats": organized_formats
            }
        ],
        "overseas": 1
    }
    
    return response

@app.route('/')
def home():
    return {"message": "Welcome to YouTube Video Link Extractor API"}

@app.route('/extract')
def extract_youtube_links():
    """Main endpoint for extracting YouTube video links"""
    yt_link = request.args.get('ytlink')
    
    if not yt_link:
        return jsonify({"error": "No YouTube link provided"}), 400
    
    try:
        video_id = extract_video_id(yt_link)
        if not video_id:
            return jsonify({"error": "Invalid YouTube URL"}), 400
        
        standard_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Create cookies file
        cookie_file = get_cookies_file()
        
        video_info = get_video_info(standard_url, cookie_file)
        
        # Clean up cookie file
        try:
            os.unlink(cookie_file)
        except:
            pass
        
        if not video_info:
            return jsonify({
                "error": "Could not extract video information",
                "solution": "YouTube cookies may have expired or are invalid. Please provide fresh YouTube cookies."
            }), 500
        
        formatted_response = format_response(video_info)
        if not formatted_response:
            return jsonify({"error": "Could not format response"}), 500
        
        return jsonify(formatted_response)
    except Exception as e:
        return jsonify({
            "error": f"Failed to process request: {str(e)}",
            "solution": "Check if your cookies are valid and not expired."
        }), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "youtube-extractor-api"})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)                quality_map[fmt['quality']]['audio_url'] = fmt['audio_url']
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
                "resource_url": video_info.get('webpage_url', ''),
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
    
    try:
        video_id = extract_video_id(yt_link)
        if not video_id:
            return jsonify({"error": "Invalid YouTube URL"}), 400
        
        standard_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Create cookies file
        cookie_file = get_cookies_file()
        
        video_info = get_video_info(standard_url, cookie_file)
        
        # Clean up cookie file
        try:
            os.unlink(cookie_file)
        except:
            pass
        
        if not video_info:
            return jsonify({
                "error": "Could not extract video information",
                "solution": "YouTube cookies may have expired or are invalid. Please provide fresh YouTube cookies."
            }), 500
        
        formatted_response = format_response(video_info)
        if not formatted_response:
            return jsonify({"error": "Could not format response"}), 500
        
        return jsonify(formatted_response)
    except Exception as e:
        return jsonify({
            "error": f"Failed to process request: {str(e)}",
            "solution": "Check if your cookies are valid and not expired."
        }), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "youtube-extractor-api"})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)        else:
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
                "resource_url": video_info.get('webpage_url', ''),
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
    
    try:
        video_id = extract_video_id(yt_link)
        if not video_id:
            return jsonify({"error": "Invalid YouTube URL"}), 400
        
        standard_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Create cookies file
        cookie_file = get_cookies_file()
        
        video_info = get_video_info(standard_url, cookie_file)
        
        # Clean up cookie file
        try:
            os.unlink(cookie_file)
        except:
            pass
        
        if not video_info:
            return jsonify({
                "error": "Could not extract video information",
                "solution": "YouTube cookies may have expired or are invalid. Please provide fresh YouTube cookies."
            }), 500
        
        formatted_response = format_response(video_info)
        if not formatted_response:
            return jsonify({"error": "Could not format response"}), 500
        
        return jsonify(formatted_response)
    except Exception as e:
        return jsonify({
            "error": f"Failed to process request: {str(e)}",
            "solution": "Check if your cookies are valid and not expired."
        }), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "youtube-extractor-api"})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)        else:
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
                "resource_url": video_info.get('webpage_url', ''),
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
    
    try:
        video_id = extract_video_id(yt_link)
        if not video_id:
            return jsonify({"error": "Invalid YouTube URL"}), 400
        
        standard_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Create cookies file
        cookie_file = get_cookies_file()
        
        video_info = get_video_info(standard_url, cookie_file)
        
        # Clean up cookie file
        try:
            os.unlink(cookie_file)
        except:
            pass
        
        if not video_info:
            return jsonify({
                "error": "Could not extract video information",
                "solution": "YouTube cookies may have expired or are invalid. Please provide fresh YouTube cookies."
            }), 500
        
        formatted_response = format_response(video_info)
        if not formatted_response:
            return jsonify({"error": "Could not format response"}), 500
        
        return jsonify(formatted_response)
    except Exception as e:
        return jsonify({
            "error": f"Failed to process request: {str(e)}",
            "solution": "Check if your cookies are valid and not expired."
        }), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "youtube-extractor-api"})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)            if format_data['separate'] == 0 and fmt.get('acodec') != 'none':
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
    
    try:
        video_id = extract_video_id(yt_link)
        if not video_id:
            return jsonify({"error": "Invalid YouTube URL"}), 400
        
        standard_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Get cookies from environment variable
        cookies = get_cookies()
        print(f"Using cookies: {list(cookies.keys())}")
        
        video_info = get_video_info(standard_url, cookies)
        if not video_info:
            return jsonify({
                "error": "Could not extract video information",
                "solution": "Cookies may have expired. Please provide fresh YouTube cookies."
            }), 500
        
        formatted_response = format_response(video_info)
        if not formatted_response:
            return jsonify({"error": "Could not format response"}), 500
        
        return jsonify(formatted_response)
    except Exception as e:
        return jsonify({
            "error": f"Failed to process request: {str(e)}",
            "solution": "Check if your cookies are valid and not expired."
        }), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "youtube-extractor-api"})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
