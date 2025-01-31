import os
from werkzeug.utils import secure_filename
import traceback
from flask import app, request
from flask_jwt_extended import jwt_required
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from web.apis.utils.helpers import validate_file_upload
from web.apis.models.tags import Tag
from web.apis.models.file_uploads import TagImage
from web.apis.utils.decorators import access_required
from web.apis.utils.serializers import PageSerializer, error_response, success_response
from web.extensions import db
from web.apis import api_bp as tag_bp

@tag_bp.route('/tags', methods=['POST'])
@jwt_required()
@access_required('admin', 'dev')
def create_tag():
    try:
        # data = request.json
        
        if request.content_type == 'application/json':
            data = request.get_json()
        elif 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
        else:
            return error_response("Content-Type must be application/json or multipart/form-data")
        
        tag = Tag(
            name=data.get('name'),
            description=data.get('description', '')
        )

        if 'images[]' in request.files:
            for image in request.files.getlist('images[]'):
                if image and validate_file_upload(image.filename):
                    filename = secure_filename(image.filename)
                    dir_path = app.config['IMAGES_LOCATION']
                    dir_path = os.path.join((os.path.join(dir_path, 'tags')))

                    if not os.path.exists(dir_path):
                        os.makedirs(dir_path)

                    file_path = os.path.join(dir_path, filename)
                    image.save(file_path)

                    file_path = file_path.replace(app.config['IMAGES_LOCATION'].rsplit(os.sep, 2)[0], '')
                    if image.content_length == 0:
                        file_size = image.content_length
                    else:
                        file_size = os.stat(file_path).st_size

                    ti = TagImage(
                        file_path=file_path, 
                        file_name=filename, 
                        original_name=image.filename,
                        file_size=file_size
                        )
                    tag.images.append(ti)

        db.session.add(tag)
        db.session.commit()

        return success_response("Tag created successfully.", data=tag.get_summary())
    
    except IntegrityError:
        db.session.rollback()
        return error_response("Failed to create tag: Integrity error.")
    
    except SQLAlchemyError as e:
        db.session.rollback()
        return error_response(f"Database error: {str(e)}")
    
    except Exception as e:
        traceback.print_exc()
        return error_response(f"Unexpected error: {str(e)}")

@tag_bp.route('/tags', methods=['GET'])
@tag_bp.route('/tags/<int:tag_id>', methods=['GET'])
@jwt_required()
@access_required('admin', 'dev')
def get_tags(tag_id=None):
    try:
        if tag_id:
            tag = Tag.query.get(tag_id)
            if not tag:
                return error_response("Tag not found.")
            return success_response(f"Tag <{tag.name}> fetched successfully.", data=tag.get_summary())

        # Pagination parameters: Default page = 1, page_size = 5
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 5, type=int)

        # Fetch tags ordered by creation date
        tags = Tag.query.order_by(desc(Tag.created_at)).paginate(page=page, per_page=page_size)

        # Serialize the paginated result using PageSerializer
        data = PageSerializer(pagination_obj=tags, resource_name="tags", include_products=True).get_data()

        # Check if data is iterable
        if isinstance(data, dict):  # Assuming get_data() returns a dict
            return success_response("Tags fetched successfully.", data=data)
        else:
            return error_response("Unexpected data format returned.")

    except Exception as e:
        traceback.print_exc()
        return error_response(f"Error fetching tags: {str(e)}")

@tag_bp.route('/tags/<int:tag_id>', methods=['PUT'])
@jwt_required()
@access_required('admin', 'dev')
def update_tag(tag_id):
    try:
        tag = Tag.query.get(tag_id)
        if not tag:
            return error_response("Tag not found.")

        data = request.json
        tag.name = data.get('name', tag.name)
        tag.description = data.get('description', tag.description)

        db.session.commit()
        return success_response("Tag updated successfully.", data=tag.get_summary())

    except SQLAlchemyError as e:
        db.session.rollback()
        return error_response(f"Database error: {str(e)}")
    except Exception as e:
        return error_response(f"Unexpected error: {str(e)}")

@tag_bp.route('/tags/<int:tag_id>', methods=['DELETE'])
@jwt_required()
@access_required('admin', 'dev')
def delete_tag(tag_id):
    try:
        tag = Tag.query.get(tag_id)
        if not tag:
            return error_response("Tag not found.")

        db.session.delete(tag)
        db.session.commit()
        return success_response("Tag deleted successfully.")

    except SQLAlchemyError as e:
        db.session.rollback()
        return error_response(f"Database error: {str(e)}")
    except Exception as e:
        return error_response(f"Unexpected error: {str(e)}")
