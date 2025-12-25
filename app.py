from flask import Flask, request, send_file, jsonify
import yt_dlp
import os
import tempfile
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        video_url = data.get('url')
        
        if not video_url:
            return jsonify({'error': 'No URL provided'}), 400
        
        logger.info(f"Downloading: {video_url}")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_template = os.path.join(tmpdir, 'video')
            
            ydl_opts = {
                'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
                'outtmpl': output_template,
                'quiet': False,
                'no_warnings': False,
                'socket_timeout': 60,
                'noplaylist': True,
                'ignoreerrors': False,
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4'
                }],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                logger.info(f"Downloaded: {info.get('title', 'Unknown')}")
            
            output_path = None
            for f in os.listdir(tmpdir):
                if f.startswith('video'):
                    output_path = os.path.join(tmpdir, f)
                    break
            
            if not output_path or not os.path.exists(output_path):
                return jsonify({'error': 'Download failed: No file created'}), 400
            
            file_size = os.path.getsize(output_path)
            logger.info(f"File size: {file_size} bytes")
            
            return send_file(
                output_path,
                mimetype='video/mp4',
                as_attachment=True,
                download_name='video.mp4'
            )
    
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'message': 'pong'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
