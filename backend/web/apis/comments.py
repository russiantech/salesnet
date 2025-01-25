import traceback
from flask import request
from flask_jwt_extended import jwt_required, get_jwt, current_user
from jsonschema import ValidationError, validate
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from web.apis.utils.decorators import access_required
from web.apis.utils.serializers import PageSerializer, error_response, success_response
from web.apis.models.products import Product
from web.apis.models.comments import Comment
from web.apis.schemas.comment import comment_schema
from web.extensions import db
from web.apis import api_bp as comment_bp

# List comments for a specific product or all products
@comment_bp.route('/comments/products/<product_slug>', methods=['GET'])
@comment_bp.route('/comments/products', methods=['GET'])
def list_comments(product_slug=None):
    try:
        # If product_slug is provided, fetch its comments
        page_size = request.args.get('page_size', 5, type=int)
        page = request.args.get('page', 1, type=int)
            
        if product_slug:
            product = Product.query.filter_by(slug=product_slug).first()
            if not product:
                return error_response("Product not found.", status_code=404)
            
            product_id = product.id

            comments = Comment.query.filter_by(product_id=product_id).order_by(
                desc(Comment.created_at) ).paginate(page=page, per_page=page_size)

            data = PageSerializer(pagination_obj=comments, resource_name="comments", include_user=True).get_data()
            return success_response("Comments fetched successfully.", data=data)
        
        # fetch - return all comments if slug is not provided
        comments = Comment.query.order_by(desc(Comment.created_at) ).paginate(page=page, per_page=page_size)
        data = PageSerializer(pagination_obj=comments, resource_name="comments", include_user=True).get_data()
        return success_response("Comments fetched successfully.", data=data)
    
    except SQLAlchemyError as e:
        db.session.rollback()
        traceback.print_exc()
        return error_response(f"Database error: {str(e)}", status_code=500)
    except Exception as e:
        traceback.print_exc()
        return error_response(f"Unexpected error: {str(e)}", status_code=500)

# Get details of a specific comment by id
@comment_bp.route('/comments/<int:comment_id>', methods=['GET'])
def show_comment(comment_id):
    try:
        comment = Comment.query.get_or_404(comment_id)
        # data = PageSerializer(items=[comment], resource_name="comment").get_data()
        data = comment.get_summary(include_user=True)
        return success_response("Comment fetched successfully.", data=data)
    except Exception as e:
        return error_response(f"Unexpected error: {str(e)}", status_code=500)

# Create a new comment
# @comment_bp.route('/products/<product_slug>/comments', methods=['POST'])
@comment_bp.route('/comments/<product_slug>/products', methods=['POST'])
@jwt_required()
def create_comment(product_slug):
    try:
        data = request.json
        
        # Validate incoming data against JSON schema
        try:
            validate(instance=data, schema=comment_schema)
        except ValidationError as e:
            return error_response(f"Validation error: {e.message}", status_code=400)
        
        claims = get_jwt()
        user_id = claims.get('id')

        # Fetch the product by slug
        product = Product.query.filter_by(slug=product_slug).first()
        if not product:
            return error_response("Product not found.", status_code=404)

        # Create the new comment
        comment = Comment(content=data['content'], user_id=user_id, rating=data.get('rating'), product_id=product.id)
        db.session.add(comment)
        db.session.commit()

        # Serialize and return the response
        # data = PageSerializer(items=[comment], resource_name="comment").get_data()
        data = comment.get_summary()
        return success_response("Comment created successfully.", data=data)

    except SQLAlchemyError as e:
        db.session.rollback()
        return error_response(f"Database error: {str(e)}", status_code=500)
    except Exception as e:
        return error_response(f"Unexpected error: {str(e)}", status_code=500)


# Update an existing comment
@comment_bp.route('/comments/<int:comment_id>', methods=['PUT'])
@jwt_required()
def update_comment(comment_id):
    try:
        
        comment = Comment.query.get_or_404(comment_id)

        # Check permissions - only the comment owner or an admin can update
        if not current_user.is_admin() and comment.user_id != current_user.id:
            return error_response("Permission denied.", status_code=403)

        # Validate incoming data
        data = request.json
        
        try:
            validate(instance=data, schema=comment_schema)
        except ValidationError as e:
            return error_response(f"Validation error: {e.message}", status_code=400)

        content = data.get('content')
        rating = data.get('rating')

        # Update the comment content or rating if provided
        if content:
            comment.content = content
        if rating is not None:  # Ensure rating is updated even if it's 0
            comment.rating = rating

        db.session.commit()
        # data = PageSerializer(items=[comment], resource_name="comment").get_data()
        data = comment.get_summary()
        return success_response("Comment updated successfully.", data=data)

    except SQLAlchemyError as e:
        db.session.rollback()
        return error_response(f"Database error: {str(e)}", status_code=500)
    except Exception as e:
        return error_response(f"Unexpected error: {str(e)}", status_code=500)


# Delete an existing comment
@comment_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
@access_required('admin')
def destroy_comment(comment_id):
    try:
        comment = Comment.query.get_or_404(comment_id)

        # if not comment:
        #     return error_response("Comment not found.", status_code=404)
        
        # Check permissions
        if not current_user.is_admin() and comment.user_id != current_user.id:
            return error_response("Permission denied.", status_code=403)

        db.session.delete(comment)
        db.session.commit()
        return success_response("Comment deleted successfully.")

    except SQLAlchemyError as e:
        db.session.rollback()
        return error_response(f"Database error: {str(e)}", status_code=500)
    except Exception as e:
        return error_response(f"Unexpected error: {str(e)}", status_code=500)