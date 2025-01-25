from os import getenv, makedirs, path, listdir
import re, hashlib, cv2

import numpy as np
from werkzeug.utils import secure_filename
from flask import jsonify, current_app, request

from web.apis.utils.serializers import error_response

# Define a regular expression pattern for valid filenames (excluding illegal characters)
valid_filename_pattern = re.compile(r'^[a-zA-Z0-9_.]+$')

def clean_filename(filename):
    # Replace spaces with underscores and remove illegal characters
    cleaned_filename = re.sub(r'[^a-zA-Z0-9_.-]', '', filename)
    cleaned_filename = cleaned_filename.replace(' ', '_')
    cleaned_filename = cleaned_filename.replace('-', '_')
    return cleaned_filename

def uploader_BAK(file):
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
            file_name = secure_filename(filename + f_ext).lower()
            mpath = path.join(upload_folder, file_name)

            if file_name in existing_files:
                # File with the same name already exists, return the existing filename
                return file_name
            
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

            return file_name

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

def uploader_BAK2(file, upload_dir=None):
    try:
        """ 
        Uploads any kind of file/media/image/format ['.jpg', '.jpeg', '.png', '.webp', '.svg', '.gif', '.bmp'] 
        Parameters:
            file: The file to upload.
            upload_dir: Optional. Custom directory to upload the file to. Defaults to 'static/images/uploads'.
        Returns:
            The uploaded file-name.
        """
        
        if file and file.filename:
            file_content = file.read()
            file_hash = hashlib.md5(file_content).hexdigest()

            # Set default upload directory if not provided
            upload_folder = upload_dir or path.join(current_app.root_path, f"{getenv('IMAGES_LOCATION')}/uploads")
            
            if not path.exists(upload_folder):
                makedirs(upload_folder)  # Ensure the directory exists

            output_size = (200, 300)
            existing_files = listdir(upload_folder)
            
            # Extract the original filename (without extension)
            _, f_ext = path.splitext(file.filename)
            filename = clean_filename(_).lower()  # Clean the filename
            file_name = secure_filename(filename + f_ext).lower()
            mpath = path.join(upload_folder, file_name)

            if file_name in existing_files:
                return file_name
            
            for existing_file in existing_files:
                if path.isfile(path.join(upload_folder, existing_file)):
                    existing_file_content = open(path.join(upload_folder, existing_file), 'rb').read()
                    existing_file_hash = hashlib.md5(existing_file_content).hexdigest()
                    if existing_file_hash == file_hash:
                        return existing_file

            if f_ext.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.svg', '.gif', '.bmp']:
                img = cv2.imdecode(np.frombuffer(file_content, np.uint8), -1)
                if img is None:
                    raise ValueError("Invalid image format")
                img = cv2.resize(img, output_size, interpolation=cv2.INTER_AREA)
                cv2.imwrite(mpath, img)
            elif f_ext.lower() in ['.mp4', '.mov', '.webm', '.avi']:
                with open(mpath, 'wb') as video_file:
                    video_file.write(file_content)
            elif f_ext.lower() == '.svg':
                with open(mpath, 'wb') as svg_file:
                    svg_file.write(file_content)
            else:
                raise ValueError("Unsupported File(Image/Video) Format")

            return file_name

        return error_response('Please choose a file to upload')
    
    except (ValueError, Exception) as e:
        return error_response(f"Error processing the file: {str(e)}")

# from dotenv import getenv

def uploader(file, upload_dir=None):
    """ 
    Uploads any kind of file/media/image/format ['.jpg', '.jpeg', '.png', '.webp', '.svg', '.gif', '.bmp'].
    
    Parameters:
        file: The file to upload.
        upload_dir: Optional. Custom directory to upload the file to. Defaults to 'static/images/uploads'.
    
    Returns:
        str: The full path of the uploaded file if successful, error message otherwise.
    """
    try:
        if file and file.filename:
            file_content = file.read()
            file_hash = hashlib.md5(file_content).hexdigest()

            # Set default upload directory if not provided
            upload_folder = upload_dir or path.join(current_app.root_path, f"{getenv('IMAGES_LOCATION')}/uploads")
            
            if not path.exists(upload_folder):
                makedirs(upload_folder, exist_ok=True)  # Ensure the directory exists

            output_size = (200, 300)
            existing_files = listdir(upload_folder)
            
            # Extract the original filename (without extension)
            _, file_extension = path.splitext(file.filename)
            cleaned_filename = secure_filename(file.filename.rsplit('.', 1)[0]).lower()  # Clean the filename
            file_name = f"{cleaned_filename}{file_extension.lower()}"
            full_path = path.join(upload_folder, file_name)

            # Check for existing files
            if file_name in existing_files:
                return full_path  # Return the full path if the file already exists
            
            for existing_file in existing_files:
                existing_file_path = path.join(upload_folder, existing_file)
                if path.isfile(existing_file_path):
                    with open(existing_file_path, 'rb') as ef:
                        existing_file_content = ef.read()
                        existing_file_hash = hashlib.md5(existing_file_content).hexdigest()
                        if existing_file_hash == file_hash:
                            return existing_file_path  # Return the full path of the existing file

            # Handle different file types
            if file_extension.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp']:
                img = cv2.imdecode(np.frombuffer(file_content, np.uint8), -1)
                if img is None:
                    raise ValueError("Invalid image format")
                img = cv2.resize(img, output_size, interpolation=cv2.INTER_AREA)
                cv2.imwrite(full_path, img)
            elif file_extension.lower() in ['.mp4', '.mov', '.webm', '.avi']:
                with open(full_path, 'wb') as video_file:
                    video_file.write(file_content)
            elif file_extension.lower() == '.svg':
                with open(full_path, 'wb') as svg_file:
                    svg_file.write(file_content)
            else:
                raise ValueError("Unsupported file format")

            return full_path  # Return the full file path of the uploaded file

        return error_response('Please choose a file to upload')
    
    except (ValueError, Exception) as e:
        return error_response(f"Error processing the file: {str(e)}")
