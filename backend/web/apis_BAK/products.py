
""" 
==================================================================================================================
    FOR THE NEW DESIGN & PRODUCT MODEL
==================================================================================================================
"""

import traceback
from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from web.models import Extraction, db, Product
from web.apis.utils.helpers import success_response, error_response

product_bp = Blueprint('products', __name__)

# Create a new product record
@product_bp.route('/products', methods=['POST'])
def insert_product():
    try:
        data = request.json
        new_product = Product(
            product_title=data.get('product_title'),
            dept=data.get('product_dept', 'k'),
            main_qty=data.get('main_qty', 0),
            initial_producting=data.get('initial_producting', 0),
            apportioned_qty=data.get('apportioned_qty', data.get('initial_producting') ),
            extracted_qty=data.get('extracted_qty', 0),
            cost_price=data.get('cost_price', 0),
        )
        
        db.session.add(new_product)
        db.session.commit()
        return success_response("Product created successfully.", data=new_product)
    
    except IntegrityError:
        db.session.rollback()
        traceback.print_exc()
        return error_response("Failed to create product: Integrity error.")
    
    except SQLAlchemyError as e:
        db.session.rollback()
        return error_response(f"Database error: {str(e)}")
    
    except Exception as e:
        return error_response(f"Unexpected error: {str(e)}")
    
# Fetch all product records or a specific record by ID, with latest records coming first
@product_bp.route('/products', methods=['GET'])
@product_bp.route('/products/<int:product_id>', methods=['GET'])
def fetch_products(product_id=None):
    try:
        # Fetch specific product record by ID
        if product_id:
            product = Product.query.get(product_id)
            if not product:
                return error_response("Product not found.")
            return success_response("Product fetched successfully.", data=product.to_dict())

        # Pagination settings
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # Fetch paginated apportions, ordered by latest
        product_pagination = Product.query.order_by(Product.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        apportions = [item.to_dict() for item in product_pagination.items]

        # Prepare paginated response data
        data = {
            "current_page": product_pagination.page,
            "items": apportions,
            "total_items": product_pagination.total,
            "total_pages": product_pagination.pages
        }
        return success_response("Product items fetched successfully.", data=data)

    except Exception as e:
        traceback.print_exc()
        return error_response(f"Error fetching product records: {str(e)}")


# Update an product record
@product_bp.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    try:
        product = Product.query.get(product_id)
        if product is None:
            return error_response("Product not found.")
        
        data = request.json
        product.product_title = data.get('product_title', product.product_title)
        product.dept = data.get('dept', product.dept)
        product.main_qty = data.get('main_qty', product.main_qty)
        product.initial_producting = data.get('initial_producting', product.initial_producting)
        product.apportioned_qty = data.get('apportioned_qty', product.apportioned_qty)
        product.extracted_qty = data.get('extracted_qty', product.extracted_qty)
        product.cost_price = data.get('cost_price', product.cost_price)
        
        db.session.commit()
        return success_response("Product updated successfully.")
    
    except SQLAlchemyError as e:
        db.session.rollback()
        return error_response(f"Database error: {str(e)}")
    except Exception as e:
        return error_response(f"Unexpected error: {str(e)}")

# Delete an product record
@product_bp.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        product = Product.query.get(product_id)
        if product is None:
            return error_response("Product Product Not Found.")

        db.session.delete(product)
        db.session.commit()
        return success_response("Product Item deleted successfully.")
    
    except SQLAlchemyError as e:
        db.session.rollback()
        return error_response(f"Database error: {str(e)}")
    except Exception as e:
        return error_response(f"Unexpected error: {str(e)}")

# Adjust quantities
def adjust_quantity(product_id, quantity_change, action):
    product = Product.query.get(product_id)
    if product:
        if action == "takeout":
            if product.apportioned_qty < quantity_change:
                print("Not enough stock to take out.")
                return
            product.apportioned_qty -= quantity_change
        elif action == "return":
            product.apportioned_qty += quantity_change
        db.session.commit()
        print(f"{quantity_change} quantity {action}d.")
    else:
        print("Product record not found.")

@product_bp.route('/product/<int:product_id>/takeout', methods=['POST'])
def api_take_out_bags(product_id):
    try:
        data = request.json
        quantity_to_take = data.get('quantity')
        
        if quantity_to_take is None or quantity_to_take <= 0:
            return error_response("Invalid quantity specified.")
        
        product = Product.query.get(product_id)
        if product is None:
            return error_response("Product record not found.")
        
        if product.apportioned_qty < quantity_to_take:
            return error_response(f"Not enough stock to take out {quantity_to_take} from {product.product_title}.")
        
        adjust_quantity(product_id, quantity_to_take, action="takeout")
        return success_response(f"Successfully took out {quantity_to_take} from {product.product_title}.")
    
    except Exception as e:
        return error_response(f"Error: {str(e)}")

@product_bp.route('/product/<int:product_id>/return', methods=['POST'])
def api_return_bags(product_id):
    try:
        data = request.json
        quantity_to_return = data.get('quantity')
        
        if quantity_to_return is None or quantity_to_return <= 0:
            return error_response("Invalid quantity specified.")
        
        product = Product.query.get(product_id)
        if product is None:
            return error_response("Product record not found.")
        
        adjust_quantity(product_id, quantity_to_return, action="return")
        return success_response(f"Successfully returned {quantity_to_return} to {product.product_title}.")
    
    except Exception as e:
        return error_response(f"Error: {str(e)}")


""" 
==================================================================================================================
    FOR THE EXTRACTION MODEL
==================================================================================================================
"""

# Create a new extraction record
@product_bp.route('/extractions', methods=['POST'])
def insert_extraction():
    try:
        data = request.json
        product_id = int(data.get('product_id', 0))
        extracted_qty = int(data.get('extracted_qty', None))

        # Fetch the Product item based on provided ID
        if product_id:
            product = Product.query.filter(
                (Product.id == product_id) & (Product.deleted.is_(False))
            ).first()
        
        if product is None:
            return error_response(f"Product not found for the provided ID.{product_id}")

        # Ensure extracted_qty is provided and valid
        if extracted_qty is None or extracted_qty <= 0:
            return error_response("Invalid extracted quantity provided.")

        # Check if there is enough quantity in the product to extract
        if product.apportioned_qty < int(extracted_qty):
            return error_response(f"Not enough quantity available in product. You have {product.apportioned_qty } left to extract.")

        # Create a new extraction record
        extraction = Extraction(
            extracted_title=data['extracted_title'],
            product_id=product_id,
            extracted_qty=extracted_qty,
            remaining_stock=product.apportioned_qty - extracted_qty,
            descr=data.get('descr', None)
        )

        # Deduct the extracted quantity from the main product quantity
        product.apportioned_qty -= extracted_qty

        # Save the extraction and update the product quantity in the database
        db.session.add(extraction)
        db.session.commit()

        return success_response("Extraction created successfully.", data=extraction.to_dict())
    
    except SQLAlchemyError as e:
        db.session.rollback()
        traceback.print_exc()
        return error_response(f"Database error: {str(e)}")
    
    except Exception as e:
        traceback.print_exc()
        return error_response(f"Unexpected error: {str(e)}")

@product_bp.route('/extractions/<int:extraction_id>', methods=['PUT'])
def update_extraction(extraction_id):
    try:
        
        """ 
            This part of the update function is specifically for cases where we are modifying the `extracted_qty` for an existing 
            `Extraction` record without changing its associated `product_id`. Here’s what’s happening and why each step is necessary:

            Explanation of Each Step

            1.Identify Quantity Difference:**
            
            qty_difference = new_extracted_qty - extraction.extracted_qty
            
            We calculate `qty_difference`, which is the difference between the new extraction quantity (`new_extracted_qty`) provided in the update request and the current `extracted_qty` stored in the database. 
            This tells us if:
            - We’re increasing the extraction quantity (i.e., `qty_difference > 0`)
            - We’re decreasing it (i.e., `qty_difference < 0`)
            - Or if it remains the same (i.e., `qty_difference = 0`)

            2.Check Available Product Quantity if Extracted Quantity Increases:**
            
            if qty_difference > 0 and product.apportioned_qty < qty_difference:
                return error_response(f"Not enough quantity in product. Available: {product.apportioned_qty}.")
            
            If `qty_difference` is positive, it means we’re attempting to increase the amount extracted. Therefore, we need to check if the associated `Product` has enough remaining quantity (`apportioned_qty`) to support this increase:
            - If `product.apportioned_qty < qty_difference`, the update fails, and an error is returned to inform the user there isn’t enough stock available to meet this requested increase.

            3.Adjust Apportioned Quantity Based on Difference:**
            
            product.apportioned_qty -= qty_difference
            
            After ensuring there’s sufficient quantity available, we update the `apportioned_qty` in the `Product` model by deducting `qty_difference`. 
            This updates the `apportioned_qty` in `Product` to accurately reflect the remaining stock after the extraction change.

            Why This Approach?

            When modifying `extracted_qty`, the apportion’s `apportioned_qty` needs to reflect this change to maintain data consistency and prevent over-extraction. For instance:
            -If we increase `extracted_qty`,** we reduce `apportioned_qty` accordingly to show the reduction in stock.
            -If we decrease `extracted_qty`,** `qty_difference` becomes negative, so adding it back to `apportioned_qty` accurately reflects the returned stock.

            This logic preserves data integrity by ensuring `apportioned_qty` accurately tracks remaining stock after each extraction modification.

        """
        # extraction = Extraction.query.get(extraction_id)
        if extraction_id:
            extraction = Extraction.query.filter(
                (Extraction.id == extraction_id) & (Extraction.deleted.is_(False))
            ).first()
            
        if extraction is None:
            return error_response("Extraction not found.")
        
        data = request.json
        new_product_id = data.get('product_id', extraction.product_id)
        new_extracted_qty = int(data.get('extracted_qty', extraction.extracted_qty))

        # Check if the product_id is changing and fetch the new product item
        if new_product_id != extraction.product_id:
            new_product = Product.query.get(new_product_id)
            if new_product is None:
                return error_response("Product not found for the provided ID.")
            
            # Add back the previous extracted_qty to the old product
            old_product = Product.query.get(extraction.product_id)
            old_product.apportioned_qty += extraction.extracted_qty

            # Deduct the new extracted_qty from the new product
            if new_product.apportioned_qty < new_extracted_qty:
                return error_response(f"Not enough quantity in the new product. Available: {new_product.apportioned_qty}.")
            new_product.apportioned_qty -= new_extracted_qty
            extraction.product_id = new_product_id

        else:
            # Adjust the quantity in the same product if extracted_qty is changed
            product = Product.query.get(extraction.product_id)
            qty_difference = int(new_extracted_qty - extraction.extracted_qty)
            if qty_difference > 0 and product.apportioned_qty < qty_difference:
                return error_response(f"Not enough quantity in product. Available: {product.apportioned_qty}.")
            
            product.apportioned_qty -= qty_difference

        # Update the extraction record fields
        extraction.extracted_title = data.get('extracted_title', extraction.extracted_title)
        extraction.extracted_qty = new_extracted_qty
        extraction.remaining_stock = data.get('remaining_stock', extraction.remaining_stock)
        extraction.descr = data.get('descr', extraction.descr)
        
        db.session.commit()
        return success_response("Extraction updated successfully.", data=extraction.to_dict())
    
    except SQLAlchemyError as e:
        db.session.rollback()
        traceback.print_exc()
        return error_response(f"Database error: {str(e)}")
    except Exception as e:
        traceback.print_exc()
        return error_response(f"Unexpected error: {str(e)}")


# Fetch all extractions or a specific extraction by ID
@product_bp.route('/extractions', methods=['GET'])
@product_bp.route('/extractions/<int:extraction_id>', methods=['GET'])
def fetch_extractions(extraction_id=None):
    try:
        # Fetch specific extraction record by ID
        # if extraction_id:
        #     extraction = Extraction.query.get(extraction_id)
        #     if not extraction:
        #         return error_response("Extraction not found.")
        #     return success_response("Extraction fetched successfully.", data=extraction.to_dict())
        
        if extraction_id:
            extraction = Extraction.query.filter(
                (Extraction.id == extraction_id) & (Extraction.deleted.is_(False))
            ).first()
            
            if not extraction:
                return error_response("Extraction not found.")
            return success_response("Extraction fetched successfully.", data=extraction.to_dict())
        
            
        # Pagination settings
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Get department from query parameters
        dept = request.args.get('dept', None, type=str)
        query = Extraction.query
        
        # Filter by department if provided
        if dept and dept is not None:
            # query = query.filter(Extraction.product.dept == dept)  # Corrected the equality comparison
            query = query.join(Product).filter(Product.dept == dept)
            
        # Paginate the query results
        extraction_pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        extractions = [item.to_dict() for item in extraction_pagination.items]

        # Prepare paginated response data
        data = {
            "current_page": extraction_pagination.page,
            "items": extractions,
            "total_items": extraction_pagination.total,
            "total_pages": extraction_pagination.pages
        }
        return success_response("Extractions fetched successfully.", data=data)
    
    except Exception as e:
        return error_response(f"Error fetching extraction records: {str(e)}")

# Delete an extraction record
@product_bp.route('/extractions/<int:extraction_id>', methods=['DELETE'])
def delete_extraction(extraction_id):
    try:
        extraction = Extraction.query.get(extraction_id)
        if extraction is None:
            return error_response("Extraction not found.")

        db.session.delete(extraction)
        db.session.commit()
        return success_response("Extraction deleted successfully.")
    
    except SQLAlchemyError as e:
        db.session.rollback()
        return error_response(f"Database error: {str(e)}")
    except Exception as e:
        return error_response(f"Unexpected error: {str(e)}")
