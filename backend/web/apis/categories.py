import os
import traceback
from flask_jwt_extended import jwt_required
from flask import request
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.utils import secure_filename
from web.apis.utils.decorators import access_required
from web.apis.utils.serializers import PageSerializer, error_response, success_response
from web.extensions import db, limiter
from web.apis.models.categories import Category
from web.apis.models.file_uploads import CategoryImage
from web.apis.utils.helpers import validate_file_upload
from web.apis import api_bp as categories_bp
from web.apis.utils.uploader import uploader
from web.apis.schemas.categories import category_schema

@categories_bp.route('/categories', methods=['POST'])
@jwt_required()
@access_required('admin', 'dev')
def create_category():
    try:
        if request.content_type == 'application/json':
            data = request.get_json()
        elif 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
        else:
            return error_response("Content-Type must be application/json or multipart/form-data")

        try:
            validate(instance=data, schema=category_schema)
        except ValidationError as e:
            return error_response(f"Validation error: {e.message}")

        # Create the category
        category = Category(
            name=data.get('name'),
            description=data.get('description', ''),
            parent_id=data.get('parent_id')  # Set parent_id for nested categories
        )

        # Handle images
        if 'images[]' in request.files:
            dir_path = os.getenv('IMAGES_LOCATION')
            dir_path = os.path.join(dir_path, 'categories')

            for image in request.files.getlist('images[]'):
                if image and validate_file_upload(image.filename):
                    file_name = secure_filename(image.filename)
                    file_path = uploader(image, upload_dir=dir_path)
                    file_size = image.content_length or os.stat(file_path).st_size

                    ci = CategoryImage(
                        file_path=file_path,
                        file_name=file_name,
                        original_name=image.filename,
                        file_size=file_size
                    )
                    category.images.append(ci)

        db.session.add(category)
        db.session.commit()
        return success_response("Category created successfully.", data=category.get_summary())

    except IntegrityError:
        db.session.rollback()
        return error_response(f"Integrity error. <{data.get('name')}> already exists.")

    except SQLAlchemyError as e:
        db.session.rollback()
        return error_response(f"Database error: {str(e)}")

    except Exception as e:
        return error_response(f"Unexpected error: {str(e)}")

@categories_bp.route('/categories', methods=['GET'])
@categories_bp.route('/categories/<int:category_id>', methods=['GET'])
def get_categories(category_id=None):
    try:
        if category_id:
            category = Category.query.get(category_id)
            if not category:
                return error_response("Category not found.")
            return success_response("Category fetched successfully.", data=category.get_summary(include_products=True))

        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        categories = Category.query.order_by(Category.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        data = PageSerializer(pagination_obj=categories, resource_name='categories').get_data()
        return success_response("Categories fetched successfully.", data=data)

    except Exception as e:
        return error_response(f"Error fetching categories: {str(e)}")

@categories_bp.route('/categories/<int:category_id>', methods=['PUT'])

@jwt_required()
@access_required('admin', 'dev')
def update_category(category_id):
    try:
        category = Category.query.get(category_id)
        if not category:
            return error_response("Category not found.")

        data = request.json
        category.name = data.get('name', category.name)
        category.description = data.get('description', category.description)

        db.session.commit()
        return success_response("Category updated successfully.")

    except SQLAlchemyError as e:
        db.session.rollback()
        return error_response(f"Database error: {str(e)}")

    except Exception as e:
        return error_response(f"Unexpected error: {str(e)}")

@categories_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@jwt_required()
@access_required('admin', 'dev')
def delete_category(category_id):
    try:
        category = Category.query.get(category_id)
        if not category:
            return error_response("Category not found.")

        db.session.delete(category)
        db.session.commit()
        return success_response("Category deleted successfully.")

    except SQLAlchemyError as e:
        db.session.rollback()
        return error_response(f"Database error: {str(e)}")

    except Exception as e:
        return error_response(f"Unexpected error: {str(e)}")
