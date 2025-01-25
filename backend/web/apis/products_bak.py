import os, re
import traceback
from flask import current_app as app, request, jsonify
from flask_jwt_extended import jwt_required, current_user
from jsonschema import validate
from sqlalchemy import desc, exc
from werkzeug.utils import secure_filename

from web.apis.models.categories import Category
from web.apis.models.pages import Page
from web.apis.models.users import User
from web.extensions import db
from web.apis.models.file_uploads import ProductImage
from web.apis.models.products import Product
from web.apis.utils.get_or_create import get_or_create
from web.apis.utils.helpers import validate_file_upload
from web.apis.utils.serializers import PageSerializer, error_response, success_response
from web.apis.models.tags import Tag

from web.apis import api_bp as product_bp

# @product_bp.route('/products', methods=['GET'])
# @product_bp.route('/products/<int:product_slug>', methods=['GET'])
# @jwt_required()  # Uncomment this if you need JWT-based authentication
# def get_products(product_slug=None):
#     try:
#         # Fetch specific product record by ID/SLUG if product_id is provided
#         if product_slug is not None:
#             # product = Product.query.get(product_id)
#             product = Product.query.filter_by(slug=product_slug).first()
#             if not product:
#                 return error_response("Product not found.", status_code=404)
#             # Serialize and return the product data
#             data = PageSerializer(items=[product], resource_name="product").get_data()
#             return success_response("Product fetched successfully.", data=data)

#         # Pagination parameters: Default page = 1, page_size = 5
#         page = request.args.get('page', 1, type=int)  # Ensure 'page' is an integer
#         page_size = request.args.get('page_size', 5, type=int)  # Ensure 'page_size' is an integer

#         # Fetch products with pagination
#         products = Product.query.order_by(desc(Product.publish_on)).paginate(page=page, per_page=page_size)

#         # Serialize the paginated result using PageSerializer
#         response_data = PageSerializer(pagination_obj=products, resource_name="products")
#         data = response_data.get_data()
        
#         return success_response("Products fetched successfully.", data=data)

#     except Exception as e:
#         # Handle any unexpected errors
#         return error_response(f"An error occurred: {str(e)}", status_code=500)

@product_bp.route('/products', methods=['GET'])
@product_bp.route('/products/<product_id>', methods=['GET'])
@jwt_required()  # Uncomment this if you need JWT-based authentication
def get_products(product_id=None):
    try:
        """ 
        params: product_id
        This handles various tasks like:
        1. serving for both single(if product_id is provided) / list of products if product_id is not provided.
        2. If product_id is provided it work as ID if it's digit else SLUG
        """
        # If a specific product is requested by product_id (either id or slug)
        if product_id is not None:
            # Check if the product_id is an integer (assumed to be the product id)
            if product_id.isdigit():
                # Query by product ID
                product = Product.query.get(int(product_id))
            else:
                # Otherwise, treat it as a slug and query by slug
                product = Product.query.filter_by(slug=product_id).first()
            
            # If no product is found
            if not product:
                return error_response("Product not found.", status_code=404)
            
            # Serialize and return the product data
            # data = PageSerializer(items=[product], resource_name="product").get_data()
            data = product.get_summary()
            return success_response("Product fetched successfully.", data=data)

        # Pagination parameters: Default page = 1, page_size = 5
        page = request.args.get('page', 1, type=int)  # Ensure 'page' is an integer
        page_size = request.args.get('page_size', 5, type=int)  # Ensure 'page_size' is an integer

        # Fetch products with pagination
        paginated_products = Product.query.order_by(desc(Product.created_at)).paginate(page=page, per_page=page_size)

        # Serialize the paginated result using PageSerializer
        response_data = PageSerializer(pagination_obj=paginated_products, resource_name="products")
        data = response_data.get_data()
        
        return success_response("Products fetched successfully.", data=data)

    except Exception as e:
        # Handle any unexpected errors
        return error_response(f"An error occurred: {str(e)}", status_code=500)

@product_bp.route('/products/by_id/<product_id>', methods=['GET'])
@jwt_required()
def by_id(product_id):
    try:
        product = Product.query.get(product_id)
        # product = Product.query.filter_by(slug=product_slug).first_or_404()
        # return jsonify(PageSerializer(items=[product]).get_data()), 200
        return product.get_summary()
    
    except Exception as e:
            # Handle any unexpected errors
            return error_response(f"An error occurred: {str(e)}", status_code=500)

# @product_bp.route('/products', methods=['POST'])
# @jwt_required()
# def create():
#     try:
#         # print(request.form)  # Log the form data
#         # print(request.files)  # Log the files uploaded

#         if request.content_type == 'application/json':
#             data = request.get_json()
#         elif 'multipart/form-data' in request.content_type:
#             data = request.form.to_dict()
#         else:
#             return error_response("Content-Type must be application/json or multipart/form-data")
        
#         if not data:
#             return error_response("No data received to publish your product.")
        
#         # Validate the data against the schema
#         # try:
#         #     validate(instance=data, schema=pay_schema)
#         # except ValidationError as e:
#         #     return error_response(str(e.message))
        
#         print(data)

#         # Retrieve product details from the request
#         product_name = request.form.get('name')
#         description = request.form.get('description')
#         price = request.form.get('price')
#         stock = request.form.get('stock')
#         tags = []
#         categories = []

#         # Process tags and categories from the request
#         for header_key in list(request.form.keys()):
#             if 'tags[' in header_key:
#                 name = header_key[header_key.find("[") + 1:header_key.find("]")]
#                 tag_description = request.form[header_key]
#                 tags.append(get_or_create(db.session, Tag, {'description': tag_description}, name=name)[0])

#             if header_key.startswith('categories['):
#                 result = re.search(r"\[(.*?)\]", header_key)  # Use raw string for regex
#                 if result and len(result.groups()) == 1:
#                     name = result.group(1)
#                     category_description = request.form[header_key]
#                     categories.append(
#                         get_or_create(db.session, Category, {'description': category_description}, name=name)[0]
#                     )

#         # Create the product instance
#         product = Product(
#             name=product_name, 
#             description=description, 
#             price=price, 
#             stock=stock,
#             tags=tags, 
#             categories=categories
#             )

#         # Handle image uploads
#         if 'images[]' in request.files:
#             for image in request.files.getlist('images[]'):
#                 if image and validate_file_upload(image.filename):
#                     filename = secure_filename(image.filename)
#                     dir_path = os.path.join(app.config['IMAGES_LOCATION'], 'products')

#                     # Create directory if it doesn't exist
#                     os.makedirs(dir_path, exist_ok=True)

#                     file_path = os.path.join(dir_path, filename)
#                     image.save(file_path)

#                     # Adjust file path for storage
#                     relative_file_path = file_path.replace(app.config['IMAGES_LOCATION'].rsplit(os.sep, 2)[0], '')
#                     file_size = image.content_length if image.content_length > 0 else os.stat(file_path).st_size

#                     product_image = ProductImage(
#                         file_path=relative_file_path, 
#                         file_name=filename,
#                         original_name=image.filename, 
#                         file_size=file_size
#                         )
                    
#                     product.images.append(product_image)

#         # Save the product to the database
#         db.session.add(product)
#         db.session.commit()

#         # Prepare the success response
#         # response = {'full_messages': ['Product created successfully']}
#         # response.update(PageSerializer(product).data)
#         # return jsonify(response)
#         data = product.get_summary()
#         return success_response('Product created successfully', data=data)

#     except Exception as e:
#         # Log the exception for debugging
#         traceback.print_exc()
#         print(f"Error creating product: {e}")
#         return error_response(f'Error creating product: {e}', status_code=400)

# @product_bp.route('/products', methods=['POST'])
# @jwt_required()
# def create():
#     try:
#         if request.content_type == 'application/json':
#             data = request.get_json()
#         elif 'multipart/form-data' in request.content_type:
#             data = request.form.to_dict()
#         else:
#             return error_response("Content-Type must be application/json or multipart/form-data")
        
#         if not data:
#             return error_response("No data received to publish your product.")
        
#         print("files", request.files)  # Log the data for debugging
#         print("data", data)  # Log the data for debugging

#         # Retrieve product details from the request
#         product_name = data.get('name')
#         description = data.get('description')
#         price = data.get('price')
#         stock = data.get('stock')
#         page_id = data.get('page_id')  # Get the page/store ID from the request
#         # current_user_id = current_user.id
#         tags = []
#         categories = []
        
#         # Process tags and categories from the request
#         for header_key in data.keys():
#             if 'tags[' in header_key:
#                 # Extract the index and name
#                 index = re.search(r'\[(\d+)\]', header_key).group(1)
#                 if 'name' in header_key:
#                     tag_name = data[header_key]
#                     tag_description = data.get(f'tags[{index}][description]', tag_name)
#                     tags.append(get_or_create(db.session, Tag, {'description': tag_description}, name=tag_name)[0])

#             if 'categories[' in header_key:
#                 # Extract the index and name
#                 index = re.search(r'\[(\d+)\]', header_key).group(1)
#                 if 'name' in header_key:
#                     category_name = data[header_key]
#                     category_description = data.get(f'categories[{index}][description]', category_name)
#                     categories.append(get_or_create(db.session, Category, {'description': category_description}, name=category_name)[0])

#         # Create the product instance
#         product = Product(
#             name=product_name, 
#             description=description, 
#             price=price, 
#             stock=stock,
#             tags=tags, 
#             categories=categories
#         )

#         # assign product to a user
#         product.users.append(current_user)
        
#         # assign product to a page if applicable
#         # Check if a page ID is provided in the request
#         page_id = data.get('page_id')
#         if page_id:
#             page = Page.query.get(page_id)  # Attempt to retrieve the specified page
#             if page:
#                 product.pages.append(page)  # Associate the product with the specified page
#             else:
#                 return error_response("The specified page does not exist.", status_code=404)
#         else:
#             # Use the first page associated with the current user if no page ID is provided
#             if current_user.pages:
#                 page = current_user.pages[0]  # Get the first page | a user can have multiple page(s)
#                 product.pages.append(page)  # Associate the product with the page
                
#         # Handle image uploads
#         if 'images[]' in request.files:
#             for image in request.files.getlist('images[]'):
#                 if image and validate_file_upload(image.filename):
#                     filename = secure_filename(image.filename)
#                     dir_path = os.path.join(app.config['IMAGES_LOCATION'], 'products')

#                     # Create directory if it doesn't exist
#                     os.makedirs(dir_path, exist_ok=True)

#                     file_path = os.path.join(dir_path, filename)
#                     image.save(file_path)
                    
#                     file_size = image.content_length if image.content_length > 0 else os.stat(file_path).st_size
#                     # print("file_path", file_path)
#                     product_image = ProductImage(
#                         file_path=file_path, 
#                         file_name=filename,
#                         original_name=image.filename, 
#                         file_size=file_size
#                     )
                    
#                     product.images.append(product_image)

#         # Save the product to the database
#         db.session.add(product)
#         db.session.commit()

#         data = product.get_summary()
#         return success_response('Product created successfully', data=data)

#     except Exception as e:
#         traceback.print_exc()
#         print(f"Error creating product: {e}")
#         return error_response(f'Error creating product: {current_user.pages, e}', status_code=400)

@product_bp.route('/products', methods=['POST'])
@jwt_required()
def create():
    try:
        # current_user_id = jwt_claims()['id']  # Get the current user's ID
        # current_user = User.query.get(current_user_id)  # Fetch the current user object

        if request.content_type == 'application/json':
            data = request.get_json()
        elif 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
        else:
            return error_response("Content-Type must be application/json or multipart/form-data")
        
        if not data:
            return error_response("No data received to publish your product.")

        print("files", request.files)  # Log the data for debugging
        print("data", data)  # Log the data for debugging

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
            tags=tags, 
            categories=categories
        )

        # Assign product to the current user
        product.users.append(current_user)

        # Check if a page ID is provided in the request
        page_id = data.get('page_id')
        if page_id:
            page = Page.query.get(page_id)  # Attempt to retrieve the specified page
            if page:
                product.pages.append(page)  # Associate the product with the specified page
            else:
                return error_response("The specified page does not exist.", status_code=404)
        else:
            # Use the first page associated with the current user if no page ID is provided
            if current_user.pages.count() > 0:  # Check if the user has any pages
                page = current_user.pages[0]  # Get the first page
                product.pages.append(page)  # Associate the product with the page
            # else:
            #     return error_response("No pages available for the current user.", status_code=400)

        # Handle image uploads
        if 'images[]' in request.files:
            for image in request.files.getlist('images[]'):
                if image and validate_file_upload(image.filename):
                    
                    filename = secure_filename(image.filename)
                    dir_path = os.path.join(app.config['IMAGES_LOCATION'], 'products')
                    os.makedirs(dir_path, exist_ok=True)

                    file_path = os.path.join(dir_path, filename)
                    image.save(file_path)
                    
                    file_size = image.content_length if image.content_length > 0 else os.stat(file_path).st_size
                    product_image = ProductImage(
                        file_path=file_path, 
                        file_name=filename,
                        original_name=image.filename, 
                        file_size=file_size
                    )
                    
                    product.images.append(product_image)

        # Save the product to the database
        db.session.add(product)
        db.session.commit()

        data = product.get_summary()
        return success_response('Product created successfully', data=data)

    except Exception as e:
        traceback.print_exc()
        print(f"Error creating product: {e}")
        return error_response(f'Error creating product: {e}', status_code=400)

@product_bp.route('/products/<product_slug>', methods=['PUT'])
@jwt_required()
def update(product_slug):
    try:
        
        if request.content_type == 'application/json':
            data = request.get_json()
        elif 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
        else:
            return error_response("Content-Type must be application/json or multipart/form-data")
        
        if not data:
            return error_response("No data received to publish your product.")

        # name = request.json.get('name')
        # description = request.json.get('description')
        # stock = request.json.get('stock')
        # price = request.json.get('price')

        # if not (name and description and price and stock and price):
        #     return error_response('You must provide a name, description, stock and price')

        product = Product.query.filter_by(slug=product_slug).first()
        if product is None:
            return error_response(f'Product not found <{data.get('name', product_slug)}>', status_code=404)

        product.name = data.get('name', product.name)
        product.description = data.get('description', product.description)
        product.price = data.get('price', product.price)
        product.name = data.get('stock', product.stock)

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
                        )[0])

        product.tags = tags
        product.categories = categories
        db.session.commit()
        data = product.get_summary()
        return success_response("Product updated successfully", data=data)
    
    except exc.IntegrityError as e:
        db.session.rollback()  # Rollback the session to prevent further issues
        error_message = str(e.orig)  # Get the original error message
        print(f"Database Integrity Error: {error_message}")  # Log the error for debugging
        return error_response("A product with this slug already exists. Please choose a different name.", status_code=400)
    
    except Exception as e:
        traceback.print_exc()
        print(f"Error updating product in: {e}")
        return error_response(f'Error updating product in: {e}', status_code=400)
    
@product_bp.route('/products/<product_slug>', methods=['DELETE'])
@jwt_required()
def destroy(product_slug):
    try:
        product = Product.query.filter_by(slug=product_slug).first()
        if product is None:
            return error_response(f'Product not found <{product_slug}>', status_code=404)
        
        db.session.delete(product)
        db.session.commit()
        return success_response('Product deleted successfully')
    except Exception as e:
            traceback.print_exc()
            print(f"Error deleting product in: {e}")
            return error_response(f'Error deleting product in: {e}', status_code=400)
    
@product_bp.route('/products/by_id/<product_id>', methods=['DELETE'])
@jwt_required()
def destroy_by_id(product_id):
    try:
        # product = Product.query.get(product_id).first()
        product = Product.query.get_or_404(product_id)
        if product is None:
            return error_response(f'Product not found <{product_id}>', status_code=404)
        db.session.delete(product)
        db.session.commit()
        return success_response('Product deleted successfully')
    except Exception as e:
                traceback.print_exc()
                print(f"Error deleting product in: {e}")
                return error_response(f'Error deleting product in: {e}', status_code=400)
