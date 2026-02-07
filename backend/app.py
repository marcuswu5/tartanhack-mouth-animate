from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sqlite3
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename

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
        
        print("Saving audio file...")
        audio_path = save_file(audio_file, 'audio', animation_id, animation_folder)
        print(f"Audio saved to: {audio_path}")
        
        print("Saving face reference file...")
        face_reference_path = save_file(face_reference_file, 'face_reference', animation_id, animation_folder)
        print(f"Face reference saved to: {face_reference_path}")
        
        if not video_path:
            return jsonify({'error': 'Failed to save video file'}), 500
        if not audio_path:
            return jsonify({'error': 'Failed to save audio file'}), 500
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
            
            # Insert frame records
            for frame_path, frame_order in frame_paths:
                c.execute('''
                    INSERT INTO frames (animation_id, frame_path, frame_order)
                    VALUES (?, ?, ?)
                ''', (animation_id, frame_path, frame_order))
            
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
