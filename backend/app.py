from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sqlite3
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: opencv-python not installed. Video frame extraction will not work.")
    print("Install it with: pip install opencv-python")

# Audio conversion uses ffmpeg directly via subprocess
# No Python library dependencies needed, just ffmpeg must be installed

app = Flask(__name__)
# Enable CORS for frontend - allow requests from any origin (for development)
# In production, restrict this to your actual frontend domain
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configuration
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'm4a', 'aac'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Create main upload directory
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database setup
def init_db():
    conn = sqlite3.connect('animations.db')
    c = conn.cursor()
    
    # Create tables if they don't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS animations (
            id TEXT PRIMARY KEY,
            video_path TEXT NOT NULL,
            audio_path TEXT NOT NULL,
            face_reference_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'processing'
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS frames (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            animation_id TEXT NOT NULL,
            frame_path TEXT NOT NULL,
            frame_order INTEGER NOT NULL,
            FOREIGN KEY (animation_id) REFERENCES animations (id)
        )
    ''')
    
    # Migrate existing database: add face_reference_path column if it doesn't exist
    try:
        # Check if column exists by trying to select it
        c.execute('SELECT face_reference_path FROM animations LIMIT 1')
    except sqlite3.OperationalError:
        # Column doesn't exist, add it
        print("Migrating database: adding face_reference_path column...")
        c.execute('ALTER TABLE animations ADD COLUMN face_reference_path TEXT')
        print("Migration complete!")
    
    conn.commit()
    conn.close()

def allowed_file(filename, file_type):
    """Check if file extension is allowed"""
    if file_type == 'video':
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS
    elif file_type == 'audio':
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS
    elif file_type == 'image':
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS
    return False

def save_file(file, file_type, animation_id, animation_folder, frame_index=None):
    """Save file to disk and return the path"""
    if file and file.filename:
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower()
        
        # Create subfolder based on file type
        if file_type == 'video':
            subfolder = 'video'
            save_filename = f"video.{file_ext}"
        elif file_type == 'audio':
            subfolder = 'audio'
            save_filename = f"audio.{file_ext}"
        elif file_type == 'face_reference':
            subfolder = 'face_reference'
            save_filename = f"face_reference.{file_ext}"
        elif file_type == 'frame':
            subfolder = 'frames'
            # For frames, use numbered filenames: frame_001.png, frame_002.png, etc.
            if frame_index is not None:
                save_filename = f"frame_{frame_index:03d}.{file_ext}"
            else:
                save_filename = filename  # Fallback to original name
        else:
            subfolder = file_type
            save_filename = f"{file_type}.{file_ext}"
        
        # Create subfolder if it doesn't exist
        type_folder = os.path.join(animation_folder, subfolder)
        os.makedirs(type_folder, exist_ok=True)
        
        file_path = os.path.join(type_folder, save_filename)
        file.save(file_path)
        return file_path
    return None

def extract_video_frames(video_path, output_folder, fps=24):
    """
    Extract all frames from a video and save them as PNG files.
    
    Args:
        video_path: Path to the video file
        output_folder: Folder to save extracted frames
        fps: Frames per second of the video (default 24)
    
    Returns:
        List of paths to extracted frame files
    """
    frame_paths = []
    
    if not CV2_AVAILABLE:
        print("Error: opencv-python is not installed. Cannot extract frames.")
        return frame_paths
    
    try:
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Open video file
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"Error: Could not open video file {video_path}")
            return frame_paths
        
        # Get video properties for verification
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration_seconds = total_frames / video_fps if video_fps > 0 else 0
        
        print(f"Extracting frames from video: {video_path}")
        print(f"Video properties:")
        print(f"  - Resolution: {video_width}x{video_height}")
        print(f"  - Actual FPS: {video_fps:.2f}")
        print(f"  - Expected FPS: {fps}")
        print(f"  - Total frames in video: {total_frames}")
        print(f"  - Duration: {duration_seconds:.2f} seconds")
        
        frame_count = 0
        frame_number = 0
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # Save frame as PNG
            frame_filename = f"frame_{frame_number+1:06d}.png"
            frame_path = os.path.join(output_folder, frame_filename)
            success = cv2.imwrite(frame_path, frame)
            
            if success and os.path.exists(frame_path):
                frame_paths.append(frame_path)
                frame_number += 1
                # Print progress every 30 frames
                if frame_number % 30 == 0:
                    print(f"  Extracted {frame_number} frames...")
            else:
                print(f"Warning: Failed to save frame {frame_number+1}")
            
            frame_count += 1
        
        cap.release()
        
        print(f"✓ Successfully extracted {len(frame_paths)} frames from video")
        print(f"  - Saved to: {output_folder}")
        if total_frames > 0:
            extraction_rate = (len(frame_paths) / total_frames) * 100
            print(f"  - Extraction rate: {extraction_rate:.1f}% ({len(frame_paths)}/{total_frames} frames)")
        
        return frame_paths
        
    except Exception as e:
        print(f"Error extracting frames from video: {e}")
        import traceback
        traceback.print_exc()
        return frame_paths

def convert_audio_to_wav(input_audio_path, output_wav_path, sample_rate=44100, channels=2):
    """
    Convert audio file to WAV format using ffmpeg.
    
    Args:
        input_audio_path: Path to input audio file
        output_wav_path: Path to save output WAV file
        sample_rate: Sample rate for output WAV (default 44100 Hz)
        channels: Number of channels (1=mono, 2=stereo, default 2)
    
    Returns:
        True if conversion successful, False otherwise
    """
    import subprocess
    
    try:
        print(f"Converting audio to WAV: {input_audio_path}")
        print(f"  Output: {output_wav_path}")
        print(f"  Sample rate: {sample_rate} Hz")
        print(f"  Channels: {channels}")
        
        # Build ffmpeg command
        # -i: input file
        # -ar: audio sample rate
        # -ac: audio channels
        # -y: overwrite output file if it exists
        # -f wav: output format
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', input_audio_path,
            '-ar', str(sample_rate),
            '-ac', str(channels),
            '-f', 'wav',
            '-y',  # Overwrite output file
            output_wav_path
        ]
        
        print(f"  Running: {' '.join(ffmpeg_cmd)}")
        
        # Run ffmpeg
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0 and os.path.exists(output_wav_path):
            file_size = os.path.getsize(output_wav_path) / (1024 * 1024)  # Size in MB
            print(f"✓ Successfully converted audio to WAV")
            print(f"  - Output file size: {file_size:.2f} MB")
            return True
        else:
            print(f"Error: ffmpeg conversion failed")
            if result.stderr:
                print(f"  Error output: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("Error: ffmpeg not found. Please install ffmpeg:")
        print("  macOS: brew install ffmpeg")
        print("  Linux: sudo apt-get install ffmpeg")
        print("  Windows: Download from https://ffmpeg.org/download.html")
        return False
    except subprocess.TimeoutExpired:
        print("Error: Audio conversion timed out (exceeded 5 minutes)")
        return False
    except Exception as e:
        print(f"Error converting audio to WAV: {e}")
        import traceback
        traceback.print_exc()
        return False

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 500MB'}), 413

@app.route('/api/submit', methods=['POST'])
def submit_files():
    try:
        print("Received submit request")
        print(f"Content-Type: {request.content_type}")
        print(f"Files in request: {list(request.files.keys())}")
        
        # Generate unique animation ID
        animation_id = str(uuid.uuid4())
        
        # Create folder for this animation - directly under uploads/, no "animations" prefix
        animation_folder = os.path.join(UPLOAD_FOLDER, animation_id)
        os.makedirs(animation_folder, exist_ok=True)
        print(f"Created animation folder: {animation_folder}")
        
        # Get files from request
        video_file = request.files.get('video')
        audio_file = request.files.get('audio')
        face_reference_file = request.files.get('face_reference')
        frame_files = request.files.getlist('frames')
        
        # Store original audio filename for later use
        original_audio_filename = audio_file.filename if audio_file and audio_file.filename else None
        
        print(f"Video file: {video_file.filename if video_file else 'None'}")
        print(f"Audio file: {audio_file.filename if audio_file else 'None'}")
        print(f"Face reference file: {face_reference_file.filename if face_reference_file else 'None'}")
        print(f"Frame files: {len(frame_files)}")
        
        # Validate files
        if not video_file:
            return jsonify({'error': 'No video file provided'}), 400
        if not video_file.filename:
            return jsonify({'error': 'Video file has no filename'}), 400
        if not allowed_file(video_file.filename, 'video'):
            return jsonify({'error': f'Invalid video file type. Allowed: {ALLOWED_VIDEO_EXTENSIONS}'}), 400
        
        if not audio_file:
            return jsonify({'error': 'No audio file provided'}), 400
        if not audio_file.filename:
            return jsonify({'error': 'Audio file has no filename'}), 400
        if not allowed_file(audio_file.filename, 'audio'):
            return jsonify({'error': f'Invalid audio file type. Allowed: {ALLOWED_AUDIO_EXTENSIONS}'}), 400
        
        if not frame_files or len(frame_files) == 0:
            return jsonify({'error': 'No frame files provided'}), 400
        
        if not face_reference_file:
            return jsonify({'error': 'No face reference file provided'}), 400
        if not face_reference_file.filename:
            return jsonify({'error': 'Face reference file has no filename'}), 400
        if not allowed_file(face_reference_file.filename, 'image'):
            return jsonify({'error': f'Invalid face reference file type. Allowed: {ALLOWED_IMAGE_EXTENSIONS}'}), 400
        
        # Save files to disk in the animation folder
        print("Saving video file...")
        video_path = save_file(video_file, 'video', animation_id, animation_folder)
        print(f"Video saved to: {video_path}")
        
        if not video_path:
            return jsonify({'error': 'Failed to save video file'}), 500
        
        # Extract frames from video (24 fps)
        print("Extracting frames from video...")
        video_frames_folder = os.path.join(animation_folder, 'video_frames')
        extracted_frame_paths = extract_video_frames(video_path, video_frames_folder, fps=24)
        
        if len(extracted_frame_paths) == 0:
            print("Warning: No frames extracted from video")
        else:
            print(f"Successfully extracted {len(extracted_frame_paths)} frames from video")
        
        print("Saving audio file...")
        audio_path = save_file(audio_file, 'audio', animation_id, animation_folder)
        print(f"Audio saved to: {audio_path}")
        
        if not audio_path:
            return jsonify({'error': 'Failed to save audio file'}), 500
        
        # Convert audio to WAV format
        print("Converting audio to WAV format...")
        audio_folder = os.path.join(animation_folder, 'audio')
        wav_path = os.path.join(audio_folder, 'audio.wav')
        
        conversion_success = convert_audio_to_wav(audio_path, wav_path)
        
        if conversion_success:
            # Use the WAV file path instead of original
            audio_path = wav_path
            print(f"Using converted WAV file: {audio_path}")
            
            # Copy WAV file to aligner/data directory
            import shutil
            
            # Get the project root directory (one level up from backend/)
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(backend_dir)
            aligner_data_dir = os.path.join(project_root, 'aligner', 'data')
            
            # Create aligner/data directory if it doesn't exist
            os.makedirs(aligner_data_dir, exist_ok=True)
            
            # Copy WAV file to aligner/data with animation_id as filename
            aligner_wav_filename = f"{animation_id}.wav"
            aligner_wav_path = os.path.join(aligner_data_dir, aligner_wav_filename)
            shutil.copy2(wav_path, aligner_wav_path)
            print(f"✓ Copied WAV file to aligner/data: {aligner_wav_path}")
            
            # Create a text file with the audio file name
            audio_txt_filename = f"{animation_id}.txt"
            audio_txt_path = os.path.join(aligner_data_dir, audio_txt_filename)
            with open(audio_txt_path, 'w') as f:
                f.write(f"{aligner_wav_filename}\n")
            print(f"✓ Created text file: {audio_txt_path}")
            
            # Write original audio file name to audionames.txt (overwrite with single line)
            audionames_file = os.path.join(project_root, 'audionames.txt')
            if original_audio_filename:
                with open(audionames_file, 'w') as f:
                    f.write(f"{original_audio_filename}\n")
                print(f"✓ Updated audionames.txt with: {original_audio_filename}")
            else:
                print("Warning: Could not get original audio filename")
        else:
            print("Warning: Audio conversion to WAV failed. Using original audio file.")
            # Continue with original file if conversion fails
        
        print("Saving face reference file...")
        face_reference_path = save_file(face_reference_file, 'face_reference', animation_id, animation_folder)
        print(f"Face reference saved to: {face_reference_path}")
        
        if not face_reference_path:
            return jsonify({'error': 'Failed to save face reference file'}), 500
        
        # Save frame files
        print("Saving frame files...")
        frame_paths = []
        for idx, frame_file in enumerate(frame_files):
            if frame_file and frame_file.filename:
                if allowed_file(frame_file.filename, 'image'):
                    # Use idx+1 for frame numbering (frame_001, frame_002, etc.)
                    frame_path = save_file(frame_file, 'frame', animation_id, animation_folder, frame_index=idx+1)
                    if frame_path:
                        frame_paths.append((frame_path, idx))
                        print(f"Frame {idx+1} saved to: {frame_path}")
                else:
                    print(f"Frame {idx} has invalid extension: {frame_file.filename}")
        
        if len(frame_paths) == 0:
            return jsonify({'error': 'No valid frame files. Allowed extensions: ' + ', '.join(ALLOWED_IMAGE_EXTENSIONS)}), 400
        
        # Store metadata in database
        print("Storing metadata in database...")
        conn = sqlite3.connect('animations.db')
        c = conn.cursor()
        
        try:
            # Insert animation record
            c.execute('''
                INSERT INTO animations (id, video_path, audio_path, face_reference_path, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (animation_id, video_path, audio_path, face_reference_path, 'uploaded'))
            
            # Insert frame records (user-uploaded frames)
            for frame_path, frame_order in frame_paths:
                c.execute('''
                    INSERT INTO frames (animation_id, frame_path, frame_order)
                    VALUES (?, ?, ?)
                ''', (animation_id, frame_path, frame_order))
            
            # Insert extracted video frame records
            for idx, extracted_frame_path in enumerate(extracted_frame_paths):
                c.execute('''
                    INSERT INTO frames (animation_id, frame_path, frame_order)
                    VALUES (?, ?, ?)
                ''', (animation_id, extracted_frame_path, idx + 10000))  # Use high order number to distinguish from user frames
            
            conn.commit()
            print(f"Database updated successfully. Animation ID: {animation_id}")
        except Exception as db_error:
            conn.rollback()
            print(f"Database error: {db_error}")
            return jsonify({'error': f'Database error: {str(db_error)}'}), 500
        finally:
            conn.close()
        
        print("Request completed successfully")
        return jsonify({
            'success': True,
            'animation_id': animation_id,
            'message': 'Files uploaded and stored successfully'
        }), 200
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in submit_files: {e}")
        print(f"Traceback: {error_trace}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify server is running"""
    return jsonify({'status': 'ok', 'message': 'Server is running', 'port': 5001}), 200

@app.route('/api/animations/<animation_id>/frames', methods=['GET'])
def get_video_frames(animation_id):
    """Get information about extracted video frames for an animation"""
    animation_folder = os.path.join(UPLOAD_FOLDER, animation_id)
    video_frames_folder = os.path.join(animation_folder, 'video_frames')
    
    if not os.path.exists(video_frames_folder):
        return jsonify({'error': 'Video frames folder not found'}), 404
    
    # Get all frame files
    frame_files = sorted([f for f in os.listdir(video_frames_folder) if f.endswith('.png')])
    frame_count = len(frame_files)
    
    # Get video file info
    video_folder = os.path.join(animation_folder, 'video')
    video_files = [f for f in os.listdir(video_folder) if f.startswith('video.')] if os.path.exists(video_folder) else []
    video_path = os.path.join(video_folder, video_files[0]) if video_files else None
    
    video_info = {}
    if video_path and CV2_AVAILABLE and os.path.exists(video_path):
        try:
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                video_info = {
                    'fps': float(cap.get(cv2.CAP_PROP_FPS)),
                    'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                    'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                    'duration_seconds': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / cap.get(cv2.CAP_PROP_FPS) if cap.get(cv2.CAP_PROP_FPS) > 0 else 0
                }
                cap.release()
        except Exception as e:
            print(f"Error getting video info: {e}")
    
    return jsonify({
        'animation_id': animation_id,
        'extracted_frame_count': frame_count,
        'frame_files': frame_files[:10],  # First 10 frame filenames
        'video_info': video_info,
        'frames_folder': video_frames_folder
    }), 200

@app.route('/api/animations/<animation_id>', methods=['GET'])
def get_animation(animation_id):
    """Get animation details from database"""
    conn = sqlite3.connect('animations.db')
    c = conn.cursor()
    
    c.execute('SELECT * FROM animations WHERE id = ?', (animation_id,))
    animation = c.fetchone()
    
    if not animation:
        conn.close()
        return jsonify({'error': 'Animation not found'}), 404
    
    c.execute('SELECT frame_path, frame_order FROM frames WHERE animation_id = ? ORDER BY frame_order', (animation_id,))
    frames = c.fetchall()
    
    conn.close()
    
    # Handle both old and new database schemas
    if len(animation) >= 6:
        # New schema with face_reference_path
        return jsonify({
            'id': animation[0],
            'video_path': animation[1],
            'audio_path': animation[2],
            'face_reference_path': animation[3],
            'created_at': animation[4],
            'status': animation[5],
            'frames': [{'path': f[0], 'order': f[1]} for f in frames]
        }), 200
    else:
        # Old schema without face_reference_path
        return jsonify({
            'id': animation[0],
            'video_path': animation[1],
            'audio_path': animation[2],
            'face_reference_path': None,
            'created_at': animation[3],
            'status': animation[4],
            'frames': [{'path': f[0], 'order': f[1]} for f in frames]
        }), 200

if __name__ == '__main__':
    # Change this port if needed
    PORT = 5001
    
    print("Initializing database...")
    init_db()
    print("Database initialized!")
    print(f"Starting Flask server on http://localhost:{PORT}")
    print("Make sure your frontend is running on http://localhost:8000")
    try:
        app.run(debug=True, port=PORT, host='0.0.0.0')
    except Exception as e:
        print(f"Error starting server: {e}")
        print(f"Make sure port {PORT} is not already in use")
