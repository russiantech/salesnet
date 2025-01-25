
""" 
==================================================================================================================
    FOR THE NEW DESIGN & APPORTION MODEL
==================================================================================================================
"""

import traceback
from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from web.models import Extraction, db, Apportion
from web.apis.utils.helpers import success_response, error_response

# apportion_bp = Blueprint('apportion', __name__)
apportion_items_bp = Blueprint('apportion_items', __name__)

# Create a new apportion record
@apportion_items_bp.route('/apportions', methods=['POST'])
def insert_apportion():
    try:
        data = request.json
        new_apportion = Apportion(
            product_title=data.get('product_title'),
            dept=data.get('apportion_dept', 'k'),
            main_qty=data.get('main_qty', 0),
            initial_apportioning=data.get('initial_apportioning', 0),
            apportioned_qty=data.get('apportioned_qty', data.get('initial_apportioning') ),
            extracted_qty=data.get('extracted_qty', 0),
            cost_price=data.get('cost_price', 0),
        )
        
        db.session.add(new_apportion)
        db.session.commit()
        return success_response("Apportion created successfully.", data=new_apportion)
    
    except IntegrityError:
        db.session.rollback()
        traceback.print_exc()
        return error_response("Failed to create apportion: Integrity error.")
    
    except SQLAlchemyError as e:
        db.session.rollback()
        return error_response(f"Database error: {str(e)}")
    
    except Exception as e:
        return error_response(f"Unexpected error: {str(e)}")
    
# Fetch all apportion records or a specific record by ID, with latest records coming first
@apportion_items_bp.route('/apportions', methods=['GET'])
@apportion_items_bp.route('/apportions/<int:apportion_id>', methods=['GET'])
def fetch_apportions(apportion_id=None):
    try:
        # Fetch specific apportion record by ID
        if apportion_id:
            apportion = Apportion.query.get(apportion_id)
            if not apportion:
                return error_response("Apportion not found.")
            return success_response("Apportion fetched successfully.", data=apportion.to_dict())

        # Pagination settings
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # Fetch paginated apportions, ordered by latest
        apportion_pagination = Apportion.query.order_by(Apportion.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        apportions = [item.to_dict() for item in apportion_pagination.items]

        # Prepare paginated response data
        data = {
            "current_page": apportion_pagination.page,
            "items": apportions,
            "total_items": apportion_pagination.total,
            "total_pages": apportion_pagination.pages
        }
        return success_response("Apportion items fetched successfully.", data=data)

    except Exception as e:
        traceback.print_exc()
        return error_response(f"Error fetching apportion records: {str(e)}")


# Update an apportion record
@apportion_items_bp.route('/apportions/<int:apportion_id>', methods=['PUT'])
def update_apportion(apportion_id):
    try:
        apportion = Apportion.query.get(apportion_id)
        if apportion is None:
            return error_response("Apportion not found.")
        
        data = request.json
        apportion.product_title = data.get('product_title', apportion.product_title)
        apportion.dept = data.get('dept', apportion.dept)
        apportion.main_qty = data.get('main_qty', apportion.main_qty)
        apportion.initial_apportioning = data.get('initial_apportioning', apportion.initial_apportioning)
        apportion.apportioned_qty = data.get('apportioned_qty', apportion.apportioned_qty)
        apportion.extracted_qty = data.get('extracted_qty', apportion.extracted_qty)
        apportion.cost_price = data.get('cost_price', apportion.cost_price)
        
        db.session.commit()
        return success_response("Apportion updated successfully.")
    
    except SQLAlchemyError as e:
        db.session.rollback()
        return error_response(f"Database error: {str(e)}")
    except Exception as e:
        return error_response(f"Unexpected error: {str(e)}")

# Delete an apportion record
@apportion_items_bp.route('/apportions/<int:apportion_id>', methods=['DELETE'])
def delete_apportion(apportion_id):
    try:
        apportion = Apportion.query.get(apportion_id)
        if apportion is None:
            return error_response("Apportion Product Not Found.")

        db.session.delete(apportion)
        db.session.commit()
        return success_response("Apportion Item deleted successfully.")
    
    except SQLAlchemyError as e:
        db.session.rollback()
        return error_response(f"Database error: {str(e)}")
    except Exception as e:
        return error_response(f"Unexpected error: {str(e)}")

# Adjust quantities
def adjust_quantity(apportion_id, quantity_change, action):
    apportion = Apportion.query.get(apportion_id)
    if apportion:
        if action == "takeout":
            if apportion.apportioned_qty < quantity_change:
                print("Not enough stock to take out.")
                return
            apportion.apportioned_qty -= quantity_change
        elif action == "return":
            apportion.apportioned_qty += quantity_change
        db.session.commit()
        print(f"{quantity_change} quantity {action}d.")
    else:
        print("Apportion record not found.")

@apportion_items_bp.route('/apportion/<int:apportion_id>/takeout', methods=['POST'])
def api_take_out_bags(apportion_id):
    try:
        data = request.json
        quantity_to_take = data.get('quantity')
        
        if quantity_to_take is None or quantity_to_take <= 0:
            return error_response("Invalid quantity specified.")
        
        apportion = Apportion.query.get(apportion_id)
        if apportion is None:
            return error_response("Apportion record not found.")
        
        if apportion.apportioned_qty < quantity_to_take:
            return error_response(f"Not enough stock to take out {quantity_to_take} from {apportion.product_title}.")
        
        adjust_quantity(apportion_id, quantity_to_take, action="takeout")
        return success_response(f"Successfully took out {quantity_to_take} from {apportion.product_title}.")
    
    except Exception as e:
        return error_response(f"Error: {str(e)}")

@apportion_items_bp.route('/apportion/<int:apportion_id>/return', methods=['POST'])
def api_return_bags(apportion_id):
    try:
        data = request.json
        quantity_to_return = data.get('quantity')
        
        if quantity_to_return is None or quantity_to_return <= 0:
            return error_response("Invalid quantity specified.")
        
        apportion = Apportion.query.get(apportion_id)
        if apportion is None:
            return error_response("Apportion record not found.")
        
        adjust_quantity(apportion_id, quantity_to_return, action="return")
        return success_response(f"Successfully returned {quantity_to_return} to {apportion.product_title}.")
    
    except Exception as e:
        return error_response(f"Error: {str(e)}")


""" 
==================================================================================================================
    FOR THE EXTRACTION MODEL
==================================================================================================================
"""

# Create a new extraction record
@apportion_items_bp.route('/extractions', methods=['POST'])
def insert_extraction():
    try:
        data = request.json
        apportion_id = int(data.get('apportion_id', 0))
        extracted_qty = int(data.get('extracted_qty', None))

        # Fetch the Apportion item based on provided ID
        if apportion_id:
            apportion = Apportion.query.filter(
                (Apportion.id == apportion_id) & (Apportion.deleted.is_(False))
            ).first()
        
        if apportion is None:
            return error_response(f"Apportion not found for the provided ID.{apportion_id}")

        # Ensure extracted_qty is provided and valid
        if extracted_qty is None or extracted_qty <= 0:
            return error_response("Invalid extracted quantity provided.")

        # Check if there is enough quantity in the apportion to extract
        if apportion.apportioned_qty < int(extracted_qty):
            return error_response(f"Not enough quantity available in apportion. You have {apportion.apportioned_qty } left to extract.")

        # Create a new extraction record
        extraction = Extraction(
            extracted_title=data['extracted_title'],
            apportion_id=apportion_id,
            extracted_qty=extracted_qty,
            remaining_stock=apportion.apportioned_qty - extracted_qty,
            descr=data.get('descr', None)
        )

        # Deduct the extracted quantity from the main apportion quantity
        apportion.apportioned_qty -= extracted_qty

        # Save the extraction and update the apportion quantity in the database
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

@apportion_items_bp.route('/extractions/<int:extraction_id>', methods=['PUT'])
def update_extraction(extraction_id):
    try:
        
        """ 
            This part of the update function is specifically for cases where we are modifying the `extracted_qty` for an existing 
            `Extraction` record without changing its associated `apportion_id`. Here’s what’s happening and why each step is necessary:

            Explanation of Each Step

            1.Identify Quantity Difference:**
            
            qty_difference = new_extracted_qty - extraction.extracted_qty
            
            We calculate `qty_difference`, which is the difference between the new extraction quantity (`new_extracted_qty`) provided in the update request and the current `extracted_qty` stored in the database. 
            This tells us if:
            - We’re increasing the extraction quantity (i.e., `qty_difference > 0`)
            - We’re decreasing it (i.e., `qty_difference < 0`)
            - Or if it remains the same (i.e., `qty_difference = 0`)

            2.Check Available Apportion Quantity if Extracted Quantity Increases:**
            
            if qty_difference > 0 and apportion.apportioned_qty < qty_difference:
                return error_response(f"Not enough quantity in apportion. Available: {apportion.apportioned_qty}.")
            
            If `qty_difference` is positive, it means we’re attempting to increase the amount extracted. Therefore, we need to check if the associated `Apportion` has enough remaining quantity (`apportioned_qty`) to support this increase:
            - If `apportion.apportioned_qty < qty_difference`, the update fails, and an error is returned to inform the user there isn’t enough stock available to meet this requested increase.

            3.Adjust Apportioned Quantity Based on Difference:**
            
            apportion.apportioned_qty -= qty_difference
            
            After ensuring there’s sufficient quantity available, we update the `apportioned_qty` in the `Apportion` model by deducting `qty_difference`. 
            This updates the `apportioned_qty` in `Apportion` to accurately reflect the remaining stock after the extraction change.

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
        new_apportion_id = data.get('apportion_id', extraction.apportion_id)
        new_extracted_qty = int(data.get('extracted_qty', extraction.extracted_qty))

        # Check if the apportion_id is changing and fetch the new apportion item
        if new_apportion_id != extraction.apportion_id:
            new_apportion = Apportion.query.get(new_apportion_id)
            if new_apportion is None:
                return error_response("Apportion not found for the provided ID.")
            
            # Add back the previous extracted_qty to the old apportion
            old_apportion = Apportion.query.get(extraction.apportion_id)
            old_apportion.apportioned_qty += extraction.extracted_qty

            # Deduct the new extracted_qty from the new apportion
            if new_apportion.apportioned_qty < new_extracted_qty:
                return error_response(f"Not enough quantity in the new apportion. Available: {new_apportion.apportioned_qty}.")
            new_apportion.apportioned_qty -= new_extracted_qty
            extraction.apportion_id = new_apportion_id

        else:
            # Adjust the quantity in the same apportion if extracted_qty is changed
            apportion = Apportion.query.get(extraction.apportion_id)
            qty_difference = int(new_extracted_qty - extraction.extracted_qty)
            if qty_difference > 0 and apportion.apportioned_qty < qty_difference:
                return error_response(f"Not enough quantity in apportion. Available: {apportion.apportioned_qty}.")
            
            apportion.apportioned_qty -= qty_difference

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
@apportion_items_bp.route('/extractions', methods=['GET'])
@apportion_items_bp.route('/extractions/<int:extraction_id>', methods=['GET'])
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
            # query = query.filter(Extraction.apportion.dept == dept)  # Corrected the equality comparison
            query = query.join(Apportion).filter(Apportion.dept == dept)
            
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
@apportion_items_bp.route('/extractions/<int:extraction_id>', methods=['DELETE'])
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
