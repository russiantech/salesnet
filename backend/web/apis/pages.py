
# API Endpoints for Page Management

import os
import re
import traceback
from flask import request
from flask_jwt_extended import jwt_required, current_user
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc, exc
from werkzeug.utils import secure_filename
from web.apis.utils.uploader import uploader
from web.extensions import db
from web.apis.models.categories import Category
from web.apis.models.pages import Page
from web.apis.models.tags import Tag
from web.apis.models.file_uploads import ProductImage
from web.apis.schemas.pages import page_schema, page_update_schema
from web.apis.utils.get_or_create import get_or_create
from web.apis.utils.helpers import validate_file_upload
from web.apis.utils.serializers import PageSerializer, error_response, success_response
from web.apis import api_bp as pages_bp

@pages_bp.route('/pages', methods=['GET'])
@jwt_required()
def get_pages():
    """
    Retrieve a paginated list of pages.

    Returns a list of pages, paginated by the specified page and page size.
    If no pages are found, an empty list is returned.

    :return: JSON response with paginated page data.
    """
    try:
        page = request.args.get('page', 1, type=int)  # Ensure 'page' is an integer
        page_size = request.args.get('page_size', 5, type=int)  # Ensure 'page_size' is an integer

        # Fetch pages with pagination
        pages = Page.query.order_by(desc(Page.created_at)).paginate(page=page, per_page=page_size)
        if pages:
            # Serialize the paginated result using PageSerializer
            data = PageSerializer(pagination_obj=pages, resource_name="pages").get_data()
            return success_response("Pages fetched successfully.", data=data)
        
        return success_response('No pages found.', {'pages': []}, status_code=200)
    except Exception as e:
        return error_response(f"An error occurred: {str(e)}", status_code=500)

@pages_bp.route('/pages/<page_id>/page', methods=['GET'])
@jwt_required()
def get_page_by_id(page_id):
    """
    Retrieve a page by its ID.

    :param page_id: The ID of the page to retrieve.
    :return: JSON response with page data or error message.
    """
    try:
        page = Page.query.get_or_404(page_id)
        return success_response("Page fetched successfully", data=page.get_summary())
    except Exception as e:
        return error_response(f"An error occurred: {str(e)}", status_code=500)

@pages_bp.route('/pages/<page_slug>/slug', methods=['GET'])
@jwt_required()
def get_page_by_slug(page_slug):
    """
    Retrieve a page by its slug.

    :param page_slug: The slug of the page to retrieve.
    :return: JSON response with page data or error message.
    """
    try:
        page = Page.query.filter_by(slug=page_slug).first()
        if not page:
            return error_response(f"Page <{page_slug}> not found.", status_code=404)
        return success_response("Page fetched successfully.", data=page.get_summary())
    except Exception as e:
        traceback.print_exc()
        return error_response(f"An error occurred: {str(e)}", status_code=500)

@pages_bp.route('/pages/<int:user_id>/user', methods=['GET'])
@jwt_required()
def get_pages_by_user(user_id):
    """
    Fetch pages associated with a specific user.

    :param user_id: The ID of the user to filter pages.
    :return: JSON response with paginated page data for the user.
    """
    try:
        user = current_user
        
        if not user:
            return error_response("User not found.", status_code=404)

        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 5, type=int)

        # Fetch pages associated with the user
        pages = Page.query.filter(Page.users.any(id=user_id)).order_by(desc(Page.created_at)).paginate(page=page, per_page=page_size)

        # Serialize the paginated result using PageSerializer
        data = PageSerializer(pagination_obj=pages, resource_name="pages", context_id=user_id, include_user=True).get_data()

        return success_response("Pages fetched successfully.", data=data)

    except Exception as e:
        traceback.print_exc()
        return error_response(f"An error occurred: {str(e)}", status_code=500)

@pages_bp.route('/pages/<page_id>/page', methods=['GET'])
@jwt_required()
def get_associated_pages(page_id):
    """
    Fetch pages using a specific page.

    :param page_id: The ID of the page to filter pages.
    :return: JSON response with paginated page data for the page.
    """
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 5, type=int)

        # Fetch pages associated with the page
        pages = Page.query.filter(Page.pages.any(id=page_id)).order_by(desc(Page.created_at)).paginate(page=page, per_page=page_size)

        # Serialize the paginated result using PageSerializer
        data = PageSerializer(pagination_obj=pages, resource_name="pages", context_id=page_id, include_user=True, include_page=True).get_data()

        return success_response("Pages fetched successfully.", data=data)

    except Exception as e:
        traceback.print_exc()
        return error_response(f"An error occurred: {str(e)}", status_code=500)

@pages_bp.route('/pages/<int:category_id>/category', methods=['GET'])
@jwt_required()
def get_pages_by_category(category_id):
    """
    Fetch pages associated with a specific category.

    :param category_id: The ID of the category to filter pages.
    :return: JSON response with paginated page data for the category.
    """
    try:
        category = Category.query.get(category_id)
        if not category:
            return error_response("Category not found.", status_code=404)

        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 5, type=int)

        # Fetch pages associated with the category
        pages = Page.query.filter(Page.categories.any(id=category_id)).order_by(desc(Page.created_at)).paginate(page=page, per_page=page_size)

        # Serialize the paginated result using PageSerializer
        data = PageSerializer(pagination_obj=pages, resource_name="pages", context_id=category_id).get_data()

        return success_response("Pages fetched successfully.", data=data)

    except Exception as e:
        traceback.print_exc()
        return error_response(f"An error occurred: {str(e)}", status_code=500)

@pages_bp.route('/pages', methods=['POST'])
@jwt_required()
def create_page():
    """
    Create a new page.

    Accepts page data in JSON or multipart/form-data format and saves it to the database.

    :return: JSON response indicating success or failure.
    """
    try:
        if request.content_type == 'application/json':
            data = request.get_json()
        elif 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
        else:
            return error_response("Content-Type must be application/json or multipart/form-data")
        
        if not data:
            return error_response("No data received to create your page.")

        # Validate page data
        try:
            validate(instance=data, schema=page_schema)
        except ValidationError as e:
            traceback.print_exc()
            return error_response(f"Validation error: {e.message}")

        # Retrieve page details from the request
        page_name = data.get('name')
        username = data.get('username')
        avatar = data.get('avatar')
        slug = data.get('slug')
        description = data.get('description')
        email = data.get('email')
        phone = data.get('phone')
        password = data.get('password')  # I'll Ensure to hash this before saving in production
        about_me = data.get('about_me')
        balance = data.get('balance', 0.0)  # Default to 0.0 if not provided
        withdrawal_password = data.get('withdrawal_password')
        valid_email = data.get('valid_email', False)  # Default to False if not provided
        socials = data.get('socials', {})  # Default to empty dict if not provided
        address = data.get('address', {})  # Default to empty dict if not provided
        whats_app = data.get('whats_app')
        bank = data.get('bank', {})  # Default to empty dict if not provided

        tags = []
        categories = []

        # Process tags from the request
        for header_key in data.keys():
            if 'tags[' in header_key:
                index = re.search(r'\[(\d+)\]', header_key).group(1)
                if 'name' in header_key:
                    tag_name = data[header_key]
                    tag_description = data.get(f'tags[{index}][description]', tag_name)
                    tags.append(get_or_create(db.session, Tag, {'description': tag_description}, name=tag_name)[0])

        # Process categories from the request
        for header_key in data.keys():
            if 'categories[' in header_key:
                index = re.search(r'\[(\d+)\]', header_key).group(1)
                if 'name' in header_key:
                    category_name = data[header_key]
                    category_description = data.get(f'categories[{index}][description]', category_name)
                    categories.append(get_or_create(db.session, Category, {'description': category_description}, name=category_name)[0])

        # Create the page instance with all relevant fields
        page = Page(
            name=page_name,
            username=username,
            avatar=avatar,
            # slug=slug, // comment to allow automatic slugging during insert
            description=description,
            email=email,
            phone=phone,
            password=password,  # Remember to hash this
            about_me=about_me,
            balance=balance,
            withdrawal_password=withdrawal_password,
            valid_email=valid_email,
            socials=socials,
            address=address,
            whats_app=whats_app,
            bank=bank,
            is_deleted=data.get('is_deleted', False),
            tags=tags,
            categories=categories
        )

        # Assign the page to the current user
        page.users.append(current_user)

        # Handle image uploads
        if 'images[]' in request.files:
            dir_path = os.getenv('IMAGES_LOCATION')
            dir_path = os.path.join(dir_path, 'pages')

            for image in request.files.getlist('images[]'):
                if image and validate_file_upload(image.filename):
                    file_name = secure_filename(image.filename)
                    file_path = uploader(image, upload_dir=dir_path)
                    file_size = image.content_length or os.stat(file_path).st_size

                    product_image = ProductImage(
                        file_path=file_path,
                        file_name=file_name,
                        original_name=image.filename,
                        file_size=file_size
                    )

                    page.images.append(product_image)

        # Trigger slug generation
        # receive_set(page, data['name'], None, None)
    
        # Save the page to the database
        db.session.add(page)
        db.session.commit()

        data = page.get_summary()
        return success_response('Page created successfully', data=data)
    
    except IntegrityError as e:
        print(f"Database duplicate entry detected-> {e}")
        if 'Duplicate entry' in str(e.orig):
            return error_response(f"Duplicate entry. Page already exists.", status_code=409)
        else:
            return error_response("Database error. Please try again.")
    
    except Exception as e:
        traceback.print_exc()
        return error_response(f'Error creating page: {e}', status_code=400)

@pages_bp.route('/pages/<page_slug>', methods=['PUT'])
@jwt_required()
def update_page(page_slug):
    """
    Update an existing page.

    Accepts page data in JSON or multipart/form-data format and updates the page in the database.

    :param page_slug: The slug of the page to update.
    :return: JSON response indicating success or failure.
    """
    try:
        # Determine the content type and retrieve data accordingly
        if request.content_type == 'application/json':
            data = request.get_json()
        elif 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
        else:
            return error_response("Content-Type must be application/json or multipart/form-data")

        if not data:
            return error_response("No data received to update your page.")

        # Validate page data
        try:
            validate(instance=data, schema=page_update_schema)
        except ValidationError as e:
            return error_response(f"Validation error: {e.message}")

        # Fetch the page to update
        page = Page.get_page(page_slug)
        
        if page is None:
            return error_response(f'Page not found <{data.get("name", page_slug)}>', status_code=404)

        # Update page attributes with provided data
        page.name = data.get('name', page.name)
        page.username = data.get('username', page.username)
        page.avatar = data.get('avatar', page.avatar)
        page.slug = data.get('slug', page.slug)
        page.description = data.get('description', page.description)
        page.email = data.get('email', page.email)
        page.phone = data.get('phone', page.phone)
        page.about_me = data.get('about_me', page.about_me)
        page.balance = data.get('balance', page.balance)
        page.withdrawal_password = data.get('withdrawal_password', page.withdrawal_password)
        page.valid_email = data.get('valid_email', page.valid_email)
        page.whats_app = data.get('whats_app', page.whats_app)
        page.bank = data.get('bank', page.bank)

        # Process tags and categories
        tags_input = data.get('tags', [])
        categories_input = data.get('categories', [])
        tags = []
        categories = []

        # Update categories
        for category in categories_input:
            category_obj = get_or_create(
                db.session,
                Category,
                {'description': category.get('description', None)},
                name=category['name']
            )[0]
            categories.append(category_obj)

        # Update tags
        for tag in tags_input:
            tag_obj = get_or_create(
                db.session,
                Tag,
                {'description': tag.get('description')},
                name=tag['name']
            )[0]
            tags.append(tag_obj)

        # Update relationships
        page.tags = tags
        page.categories = categories

        # Handle image uploads
        if 'images[]' in request.files:
            dir_path = os.getenv('IMAGES_LOCATION')
            dir_path = os.path.join(dir_path, 'pages')

            # Clear existing images if needed (optional)
            page.images.clear()

            for image in request.files.getlist('images[]'):
                if image and validate_file_upload(image.filename):
                    file_name = secure_filename(image.filename)
                    file_path = uploader(image, upload_dir=dir_path)
                    file_size = image.content_length or os.stat(file_path).st_size

                    page_image = ProductImage(
                        file_path=file_path,
                        file_name=file_name,
                        original_name=image.filename,
                        file_size=file_size
                    )

                    page.images.append(page_image)

        # Commit the changes to the database
        db.session.commit()

        # Prepare and return the response
        data = page.get_summary()
        return success_response("Page updated successfully", data=data)

    except exc.IntegrityError:
        db.session.rollback()  # Rollback the session to prevent further issues
        return error_response("A page with this slug already exists. Please choose a different name.", status_code=400)

    except Exception as e:
        db.session.rollback()  # Ensure rollback on any other exception
        traceback.print_exc()
        return error_response(f'Error updating page: {e}', status_code=400)

@pages_bp.route('/pages/<identifier>', methods=['DELETE'])
@jwt_required()
def delete_page(identifier):
    """
    Delete a page by its slug or ID.

    :param identifier: The page slug or ID.
    :return: JSON response indicating success or failure.
    """
    try:
        # Attempt to find the page by ID first
        page = Page.query.get(identifier)
        
        # If no page is found by ID, try to find it by slug
        if page is None:
            page = Page.query.filter_by(slug=identifier).first()
        
        # If page is still None, return a 404 error
        if page is None:
            return error_response(f'Page not found <{identifier}>', status_code=404)

        # Delete the page and commit the transaction
        db.session.delete(page)
        db.session.commit()
        return success_response('Page deleted successfully')
    
    except Exception as e:
        traceback.print_exc()
        return error_response(f'Error deleting page: {e}', status_code=400)
