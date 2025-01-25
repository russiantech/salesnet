from os import path, listdir
import secrets, re, hashlib, cv2
import numpy as np
from werkzeug.utils import secure_filename
from flask import jsonify, current_app, flash, request

# Define a regular expression pattern for valid filenames (excluding illegal characters)
valid_filename_pattern = re.compile(r'^[a-zA-Z0-9_.]+$')

def clean_filename(filename):
    # Replace spaces with underscores and remove illegal characters
    cleaned_filename = re.sub(r'[^a-zA-Z0-9_.-]', '', filename)
    cleaned_filename = cleaned_filename.replace(' ', '_')
    cleaned_filename = cleaned_filename.replace('-', '_')
    return cleaned_filename

def uploader(file):
    try:
        """ 
        uploads any kind of file/media/image/format ['.jpg', '.jpeg', '.png', '.webp', '.svg' '.gif', '.bmp'] 
        Returns: the uploaded file-name
        """
        
        if file and file.filename:

            file_content = file.read()
            file_hash = hashlib.md5(file_content).hexdigest()
            upload_folder = path.join(current_app.root_path, 'static/images/uploads')
            output_size = (200, 300)
            existing_files = listdir(upload_folder)
            
            # Extract the original filename (without extension)
            _, f_ext = path.splitext(file.filename)
            filename = clean_filename(_).lower()  # Clean the filename
            # Create the final filename by preserving the original file extension
            fname = secure_filename(filename + f_ext).lower()
            mpath = path.join(upload_folder, fname)

            if fname in existing_files:
                # File with the same name already exists, return the existing filename
                return fname
            
            for filename in existing_files:
                if path.isfile(path.join(upload_folder, filename)):
                    existing_file_content = open(path.join(upload_folder, filename), 'rb').read()
                    existing_file_hash = hashlib.md5(existing_file_content).hexdigest()
                    if existing_file_hash == file_hash:
                        return filename

            if f_ext.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.svg' '.gif', '.bmp']:
                img = cv2.imdecode(np.frombuffer(file_content, np.uint8), -1)
                if img is None:
                    raise ValueError("Invalid image format")
                img = cv2.resize(img, output_size, interpolation=cv2.INTER_AREA)
                cv2.imwrite(mpath, img)
            elif f_ext.lower() in ['.mp4', '.mov', '.webm', '.avi']:
                with open(mpath, 'wb') as video_file:
                    video_file.write(file_content)
            elif f_ext.lower() == '.svg':
                # Save SVG files as-is
                with open(mpath, 'wb') as svg_file:
                    svg_file.write(file_content)
            else:
                raise ValueError("Unsupported File(Image/Video) Format")

            return fname

        return jsonify({
            'success': True,
            'error': f'Please choose a file to upload',
            'link': f"{request.refferer}"  # Assuming referring_url is a valid URL
        })
    
    except (ValueError, Exception) as e:
        flash(f'Error processing the file: {str(e)}', 'alert-danger')
        return jsonify({
            'error': f'Error processing the file: {e}',
            'flash': 'alert-danger'
        })

