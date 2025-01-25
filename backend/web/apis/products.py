import os
import re
import traceback
from flask import current_app as app, request
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
from web.apis.models.products import Product
from web.apis.schemas.product import product_schema
from web.apis.utils.get_or_create import get_or_create
from web.apis.utils.helpers import validate_file_upload
from web.apis.utils.serializers import PageSerializer, error_response, success_response
from web.apis import api_bp as product_bp

@product_bp.route('/products', methods=['GET'])
@jwt_required()
def products():
    """
    Retrieve a paginated list of products.

    Returns a list of products, paginated by the specified page and page size.
    If no products are found, an empty list is returned.

    :return: JSON response with paginated product data.
    """
    try:
        # Pagination parameters: Default page = 1, page_size = 5
        page = request.args.get('page', 1, type=int)  # Ensure 'page' is an integer
        page_size = request.args.get('page_size', 5, type=int)  # Ensure 'page_size' is an integer

        # Fetch products with pagination
        products = Product.query.order_by(desc(Product.created_at)).paginate(page=page, per_page=page_size)

        # Serialize the paginated result using PageSerializer
        data = PageSerializer(pagination_obj=products, resource_name="products").get_data()
        
        return success_response("Products fetched successfully.", data=data)

    except Exception as e:
        
        # Handle any unexpected errors
        return error_response(f"An error occurred: {str(e)}", status_code=500)

@product_bp.route('/products/<product_id>/product', methods=['GET'])
@jwt_required()
def by_id(product_id):
    """
    Retrieve a product by its ID.

    :param product_id: The ID of the product to retrieve.
    :return: JSON response with product data or error message.
    """
    try:
        product = Product.query.get_or_404(product_id)
        return success_response("Product fetched successfully", data=product.get_summary())
    except Exception as e:
        return error_response(f"An error occurred: {str(e)}", status_code=500)

@product_bp.route('/products/<product_slug>/slug', methods=['GET'])
@jwt_required()
def by_slug(product_slug):
    """
    Retrieve a product by its slug.

    :param product_slug: The slug of the product to retrieve.
    :return: JSON response with product data or error message.
    """
    try:
        product = Product.query.filter_by(slug=product_slug).first()
        if not product:
            return error_response(f"Product <{product_slug}> not found.", status_code=404)
        return success_response("Product fetched successfully.", data=product.get_summary())
    except Exception as e:
        traceback.print_exc()
        return error_response(f"An error occurred: {str(e)}", status_code=500)

@product_bp.route('/products/<int:user_id>/user', methods=['GET'])
@jwt_required()
def by_user(user_id):
    """
    Fetch products associated with a specific user.

    :param user_id: The ID of the user to filter products.
    :return: JSON response with paginated product data for the user.
    """
    try:
        user = current_user
        
        if not user:
            return error_response("User not found.", status_code=404)

        # Pagination parameters: Default page = 1, page_size = 5
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 5, type=int)

        # Fetch products associated with the user
        products = Product.query.filter(Product.users.any(id=user_id)).order_by(desc(Product.created_at)).paginate(page=page, per_page=page_size)

        # Serialize the paginated result using PageSerializer
        data = PageSerializer(pagination_obj=products, resource_name="products", context_id=user_id, include_user=True).get_data()

        return success_response("Products fetched successfully.", data=data)

    except Exception as e:
        traceback.print_exc()
        return error_response(f"An error occurred: {str(e)}", status_code=500)
    
@product_bp.route('/products/<page_id>/page', methods=['GET'])
@jwt_required()
def by_page(page_id):
    """
    Fetch products associated with a specific page.

    :param page_id: The ID of the page to filter products.
    :return: JSON response with paginated product data for the page.
    """
    try:
        # Pagination parameters: Default page = 1, page_size = 5
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 5, type=int)

        # Fetch products associated with the page
        products = Product.query.filter(Product.pages.any(id=page_id)).order_by(desc(Product.created_at)).paginate(page=page, per_page=page_size)

        # Serialize the paginated result using PageSerializer
        data = PageSerializer(pagination_obj=products, resource_name="products", context_id=page_id, include_user=True, include_page=True).get_data()

        return success_response("Products fetched successfully.", data=data)

    except Exception as e:
        traceback.print_exc()
        return error_response(f"An error occurred: {str(e)}", status_code=500)

@product_bp.route('/products/<int:category_id>/category', methods=['GET'])
@jwt_required()
def by_category(category_id):
    """
    Fetch products associated with a specific category.

    :param category_id: The ID of the category to filter products.
    :return: JSON response with paginated product data for the category.
    """
    try:
        category = Category.query.get(category_id)
        if not category:
            return error_response("Category not found.", status_code=404)

        # Pagination parameters: Default page = 1, page_size = 5
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 5, type=int)

        # Fetch products associated with the category
        products = Product.query.filter(Product.categories.any(id=category_id)).order_by(desc(Product.created_at)).paginate(page=page, per_page=page_size)

        # Serialize the paginated result using PageSerializer
        data = PageSerializer(pagination_obj=products, resource_name="products", context_id=category_id).get_data()

        return success_response("Products fetched successfully.", data=data)

    except Exception as e:
        traceback.print_exc()
        return error_response(f"An error occurred: {str(e)}", status_code=500)

@product_bp.route('/products', methods=['POST'])
@jwt_required()
def create():
    """
    Create a new product.

    Accepts product data in JSON or multipart/form-data format and saves it to the database.

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
            return error_response("No data received to publish your product.")

        # Validate product data
        try:
            data['price'] = int(data['price'])  # Convert to integer
            data['stock'] = int(data['stock'])  # Convert to integer
            validate(instance=data, schema=product_schema)
        except ValidationError as e:
            traceback.print_exc()
            return error_response(f"Validation error: {e.message}")

        # Retrieve product details from the request
        product_name = data.get('name')
        description = data.get('description')
        price = data.get('price')
        stock = data.get('stock')

        tags = []
        categories = []

        # Process tags and categories from the request
        for header_key in data.keys():
            if 'tags[' in header_key:
                index = re.search(r'\[(\d+)\]', header_key).group(1)
                if 'name' in header_key:
                    tag_name = data[header_key]
                    tag_description = data.get(f'tags[{index}][description]', tag_name)
                    tags.append(get_or_create(db.session, Tag, {'description': tag_description}, name=tag_name)[0])

            if 'categories[' in header_key:
                index = re.search(r'\[(\d+)\]', header_key).group(1)
                if 'name' in header_key:
                    category_name = data[header_key]
                    category_description = data.get(f'categories[{index}][description]', category_name)
                    categories.append(get_or_create(db.session, Category, {'description': category_description}, name=category_name)[0])

        # Create the product instance
        product = Product(
            name=product_name, 
            description=description, 
            price=price, 
            stock=stock,
            is_deleted=data.get('is_deleted', False),
            tags=tags, 
            categories=categories
        )

        # Assign product to the current user
        product.users.append(current_user)

        # Check if a page ID is provided in the request
        page_id = data.get('page_id')
        if page_id:
            page = Page.query.get(page_id)
            if page:
                product.pages.append(page)
            else:
                return error_response("The specified page does not exist.", status_code=404)
        else:
            # Use the first page associated with the current user if no page ID is provided
            if current_user.pages.count() > 0:
                page = current_user.pages[0]
                product.pages.append(page)

        # Handle image uploads
        if 'images[]' in request.files:
            dir_path = os.getenv('IMAGES_LOCATION')
            dir_path = os.path.join(dir_path, 'products')

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
                    
                    product.images.append(product_image)

        # Save the product to the database
        db.session.add(product)
        db.session.commit()

        data = product.get_summary()
        return success_response('Product created successfully', data=data)
    
    except IntegrityError as e:
        if 'Duplicate entry' in str(e.orig):
            return error_response("Duplicate entry for slug. Product already exists.", status_code=409)
        else:
            return error_response("Database error. Please try again.")
        
    except Exception as e:
        traceback.print_exc()
        return error_response(f'Error creating product: {e}', status_code=400)

@product_bp.route('/products/<product_slug>', methods=['PUT'])
@jwt_required()
def update(product_slug):
    """
    Update an existing product.

    Accepts product data in JSON or multipart/form-data format and updates the product in the database.

    :param product_slug: The slug of the product to update.
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
            return error_response("No data received to update your product.")

        # Validate product data
        try:
            validate(instance=data, schema=product_schema)
        except ValidationError as e:
            return error_response(f"Validation error: {e.message}")

        product = Product.query.filter_by(slug=product_slug).first()
        if product is None:
            return error_response(f'Product not found <{data.get("name", product_slug)}>', status_code=404)

        # Update product attributes
        product.name = data.get('name', product.name)
        product.description = data.get('description', product.description)
        product.price = data.get('price', product.price)
        product.stock = data.get('stock', product.stock)

        # Process tags and categories
        tags_input = data.get('tags')
        categories_input = data.get('categories')
        tags = []
        categories = []
        
        if categories_input:
            for category in categories_input:
                categories.append(
                    get_or_create( 
                        db.session, 
                        Category, 
                        {'description': category.get('description', None)},
                        name=category['name']
                    )[0]
                )

        if tags_input:
            for tag in tags_input:
                tags.append(
                    get_or_create(
                        db.session, Tag, 
                        {'description': tag.get('description')}, 
                        name=tag['name']
                    )[0]
                )

        product.tags = tags
        product.categories = categories
        db.session.commit()

        data = product.get_summary()
        return success_response("Product updated successfully", data=data)
    
    except exc.IntegrityError as e:
        db.session.rollback()  # Rollback the session to prevent further issues
        return error_response("A product with this slug already exists. Please choose a different name.", status_code=400)
    
    except Exception as e:
        traceback.print_exc()
        return error_response(f'Error updating product: {e}', status_code=400)

@product_bp.route('/products/<identifier>', methods=['DELETE'])
@jwt_required()
def destroy(identifier):
    """
    Delete a product by its slug or ID.

    :param identifier: The product slug or ID.
    :return: JSON response indicating success or failure.
    """
    try:
        # Attempt to find the product by ID first
        product = Product.query.get(identifier)
        
        # If no product is found by ID, try to find it by slug
        if product is None:
            product = Product.query.filter_by(slug=identifier).first()
        
        # If product is still None, return a 404 error
        if product is None:
            return error_response(f'Product not found <{identifier}>', status_code=404)

        # Delete the product and commit the transaction
        db.session.delete(product)
        db.session.commit()
        return success_response('Product deleted successfully')
    
    except Exception as e:
        traceback.print_exc()
        return error_response(f'Error deleting product: {e}', status_code=400)