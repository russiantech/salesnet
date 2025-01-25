from flask import Blueprint, request, jsonify
from flask_login import current_user
from sqlalchemy.exc import SQLAlchemyError
from web.apis.utils.helpers import error_response, success_response, generator
from web.models import Expenses, StockHistory, db, Items, Extraction, Sales
from datetime import datetime
import traceback

sales_bp = Blueprint('sales', __name__)

# Helper: Fetch stock if from Item or Extraction
def fetch_stock(item_id, extracted_id):
    """ Returns a tuple-> stock_source(instance), available_stock """
    if item_id:
        item = Items.query.get(item_id)
        return item, item.in_stock if item else None
    elif extracted_id:
        extraction = Extraction.query.get(extracted_id)
        return extraction, extraction.apportion.apportioned_qty if extraction else None
    return None, None

def update_stock_history(item_id, quantity, description, user_id=0):
    stock_history = StockHistory(
        item_id=item_id,
        in_stock=quantity,
        desc=description,
        user_id=user_id,
        version=generator.next(),
        difference=quantity  # set this based on operation (increase or decrease)
    )
    db.session.add(stock_history)
    db.session.commit()

# Helper: Record Sales
def record_sales(data):
    try:
        # Extract and validate fields from input data
        item_id = int(data.get('item_id')) if data.get('item_id') and data.get('item_id').isdigit() else None
        extracted_id = int(data.get('extracted_id')) if data.get('extracted_id') and data.get('extracted_id').isdigit() else None
        title = data.get('title')
        dept = data.get('dept', None)
        price = int(data.get('price')) if data.get('price') and data.get('price').isdigit() else None
        qty = int(data.get('qty')) if data.get('qty') and data.get('qty').isdigit() else None # treated as closing stock for sales from Items()

        # Fetch stock based on item or extraction IDs
        stock_source, available_stock = fetch_stock(item_id, extracted_id)

        # Ensure valid dept is provided
        if dept is None or dept == '':
            return error_response(f"Pls select your department to record sales appropriately.")
        
        # Ensure valid stock source if item_id or extracted_id is provided
        if (item_id or extracted_id) and stock_source is None:
            return error_response("Item or Extracted source not found.")

        # qty provided cannot be greater than available_stock
        if (stock_source and available_stock and qty):
                title = stock_source.name if item_id else stock_source.extracted_title or title
                if (item_id and available_stock < qty):
                    
                    return error_response(
                        # f"Quantity sold [{qty}] exceeds available stock[{available_stock}] for\
                        f"Closing stock of [{qty}] you entered now exceeds available stock[{available_stock}] for\
                        [{title}].")
                    
                elif (item_id and available_stock == qty):
                    return error_response(
                        f"Closing Stock provided [{qty}] is same as available stock[{available_stock}] for\
                        [{title}]. This indicates No Sales For [{title}]")    
                
        # Validation: Require qty if only item_id is given (and not extracted_id)
        if item_id and not extracted_id:
            if qty is None or qty == '':
                title = title or (stock_source.name if stock_source else 'Unknown')
                return error_response(f"You must provide Quantity/Closing Stock to calculate sales for {title}.")
            elif qty <= 0:
                return error_response("Quantity must be greater than zero.")

        # Validation: Require price if extracted_id is provided
        if extracted_id and not (price or title):
            title = title or (stock_source.extracted_title if stock_source else 'Unknown')
            return error_response(f"You must provide price & name so we can evaluate sales from {title}.")

        # Validation: Require price and title if extracted_id is provided
        if extracted_id and not (price and title):
            # Fallback to a default title if not provided, based on the stock source if available
            title = title or (stock_source.extracted_title if stock_source else 'Unknown')
            return error_response(f"You must provide price & name so we can evaluate sales from {title}.")


        # Check required fields for "No stock" sales
        if not (item_id or extracted_id) and (not title or not price):
            return error_response("Title and price must be provided for sales without direct stock.")

        # Calculate qty_sold based on available stock and provided qty
        if stock_source and qty is not None and qty <= available_stock and item_id:
            qty_sold = available_stock - qty
        else:
            qty_sold = qty or 1

        # Calculate total sales amount based on available data
        if item_id and qty and price:
            total_price = price * qty_sold
        elif item_id and qty:
            total_price = (stock_source.s_price or 0) * qty_sold
        elif title and price and not stock_source:
            total_price = price * qty_sold if qty_sold else price
        elif extracted_id and price:
            total_price = price * qty_sold if qty_sold else price
        else:
            return error_response("Unable to calculate total. Please provide valid item or price details.")

        # Create new sale record
        sale = Sales(
            title=title or (stock_source.name if item_id else stock_source.extracted_title),
            qty=qty_sold,
            price=price,
            total=total_price,
            dept=dept,
            item_id=item_id,
            extracted_id=extracted_id,
            created=datetime.now(),
        )

        # Deduct stock quantity if item_id is provided
        if item_id:
            stock_source.in_stock -= qty_sold
            update_stock_history(item_id, -qty_sold, f"Sale recorded for {qty_sold} units.", user_id=current_user.id)

        # Commit the sale to the database
        db.session.add(sale)
        db.session.commit()
        
        return success_response(f"Sales recorded successfully.", sale.to_dict())

    except SQLAlchemyError as e:
        db.session.rollback()
        traceback.print_exc()
        return error_response(f"Database error: {str(e)}")
    except Exception as e:
        traceback.print_exc()
        return error_response(f"Unexpected error: {str(e)}")

# CREATE: Record a new sale
@sales_bp.route('/sales', methods=['POST'])
def create_sale():
    data = request.json
    return record_sales(data)

@sales_bp.route('/sales', methods=['GET'])
def fetch_sales():
    try:
        
        dept = request.args.get('dept')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = Sales.query.filter_by(deleted=False)
        
        # Apply department filter if specified
        if dept:
            query = query.filter(Sales.dept == dept)

        # Apply date range filter if specified
        if start_date and end_date:
            # Swap dates if end_date is less than start
            if end_date < start_date:
                start_date, end_date = end_date, start_date
                
            query = query.filter(Sales.created >= start_date, Sales.created <= end_date)

        sales = query.order_by(Sales.created.desc()).all()
        
        report_data = {
            "main_stock": [],
            "extraction": {},
            "others": []
        }

        total_sales, total_profit, total_expense = 0, 0, 0

        for sale in sales:
            sale_data = sale.to_dict()

            # Total and profit calculations
            if sale.total:
                total_sales += sale.total

            item_cost_price = sale.item.c_price if sale.item else 0
            item_selling_price = sale.item.s_price if sale.item else sale.price or 0
            item_profit = 0
            
            if item_selling_price and item_cost_price and sale.qty:
                item_profit = (item_selling_price - item_cost_price) * sale.qty
                # item_profit = (item_selling_price - item_cost_price)
                total_profit += item_profit

            # Add individual item profit to the sale data
            sale_data["item_profit"] = item_profit
            
            # Organize sale entries by department and type
            if sale.item_id:
                report_data["main_stock"].append(sale_data)
            elif sale.extracted_id:
                extraction_id = sale.extracted_id
                extraction = Extraction.query.get(extraction_id)
                extracted_title = extraction.extracted_title if extraction else 'not known'

                if extraction_id not in report_data["extraction"]:
                    report_data["extraction"][extraction_id] = {
                        "extraction": {"extracted_title": extracted_title},
                        "sales": [],
                        "total_sales": 0
                    }
                
                report_data["extraction"][extraction_id]["sales"].append(sale_data)
                report_data["extraction"][extraction_id]["total_sales"] += sale.total or 0
            else:
                report_data["others"].append(sale_data)

        # Fetch and sum up expenses for the specified department and date range
        expenses = Expenses.query.filter_by(deleted=False)
        if start_date and end_date:
            expenses = expenses.filter(Expenses.created >= start_date, Expenses.created <= end_date)
        
        # Apply date range filter if specified
        if dept:
            expenses = expenses.filter(Expenses.dept==dept)
        
        expenses = expenses.order_by(Expenses.created.desc()).all()
            
        total_expense = sum(expense.cost for expense in expenses)
        
        summary = {
            "total_sales": total_sales,
            "profit_minus_expense": total_profit - total_expense,
            "total_profit": total_profit,
            "total_expense": total_expense
        }
        report_data["summary"] = summary

        return success_response("Sales Fetched Successfully", data=report_data)

    except Exception as e:
        traceback.print_exc()
        return error_response(f"Error fetching sales: {str(e)}")
 
# UPDATE: Modify an existing sale record
@sales_bp.route('/sales-0/<int:sale_id>', methods=['PUT'])
def update_sale_0(sale_id):
    try:
        data = request.json
        sale = Sales.query.get(sale_id)

        if not sale:
            return error_response("Sale record not found.")

        if "qty" in data and sale.item_id:
            stock_source, available_stock = fetch_stock(sale.item_id, sale.extracted_id)
            former_price = stock_source.s_price or sale.price  # Use stock price if available

            # Maintain original qty if no new value is provided or it is invalid
            new_qty = data.get("qty")
            if new_qty is None or not str(new_qty).strip():
                new_qty = sale.qty
            else:
                try:
                    new_qty = int(new_qty)
                except ValueError:
                    return error_response("Invalid quantity: must be a valid number/integer.")

            # Check if the updated quantity exceeds available stock
            if stock_source and new_qty > available_stock + sale.qty:
                return error_response(f"Updated quantity [{new_qty}] exceeds available stock [{available_stock}].")

            # Adjust stock quantities
            if sale.item_id:
                stock_source.in_stock += sale.qty  # restore old qty
                stock_source.in_stock -= new_qty  # reduce to new qty
                update_stock_history(sale.item_id, new_qty - sale.qty, f"Sale updated from {sale.qty} to {new_qty}.", user_id=current_user.id)

        # Update sale attributes with validation, using original values if new data is missing
        for key, value in data.items():
            # Maintain original price if no new value is provided or it is invalid
            if key == "price":
                if value is None or not str(value).strip():
                    value = sale.price
                else:
                    try:
                        value = float(value) if '.' in str(value) else int(value)
                    except ValueError:
                        return error_response("Invalid price: must be a valid number.")
            
            # Maintain original qty if new value is not provided or empty
            elif key == "qty":
                value = new_qty  # already validated

            setattr(sale, key, value)

        # Set default price from stock source if no new or original price exists
        if sale.item_id and not sale.price:
            stock_source, _ = fetch_stock(sale.item_id, sale.extracted_id)
            sale.price = former_price

        # Calculate total if qty and price are available
        if sale.qty and sale.price:
            sale.total = float(sale.qty) * float(sale.price)
        else:
            return error_response("Quantity and price must be valid numbers for total calculation.")

        db.session.commit()
        return success_response(f"Sale updated successfully.", sale.to_dict())

    except SQLAlchemyError as e:
        db.session.rollback()
        traceback.print_exc()
        return error_response(f"Database error: {str(e)}")
    except Exception as e:
        traceback.print_exc()
        return error_response(f"Unexpected error: {str(e)}")

# UPDATE: Modify an existing sale record
@sales_bp.route('/sales/<int:sale_id>', methods=['PUT'])
def update_sale(sale_id):
    try:
        data = request.json
        sale = Sales.query.get(sale_id)

        if not sale:
            return error_response("Sale record not found.")

        # Default new_qty to the existing quantity if not provided
        new_qty = data.get("qty", sale.qty)
        if new_qty is None or not str(new_qty).strip():
            new_qty = sale.qty
        else:
            try:
                new_qty = int(new_qty)
            except ValueError:
                return error_response("Invalid quantity: must be a valid integer.")

        if sale.item_id:
            stock_source, available_stock = fetch_stock(sale.item_id, sale.extracted_id)
            former_price = stock_source.s_price or sale.price  # Use stock price if available

            # Check if updated quantity exceeds available stock
            if stock_source and new_qty > available_stock + sale.qty:
                return error_response(f"Updated quantity [{new_qty}] exceeds available stock [{available_stock}].")

            # Adjust stock quantities
            stock_source.in_stock += sale.qty  # restore old qty
            stock_source.in_stock -= new_qty  # reduce to new qty
            update_stock_history(sale.item_id, new_qty - sale.qty, f"Sale updated from {sale.qty} to {new_qty}.", user_id=current_user.id)

        # Update sale attributes with validation
        for key, value in data.items():
            if key == "price":
                if value is None or not str(value).strip():
                    value = sale.price  # Maintain original price if no new value
                else:
                    try:
                        value = float(value) if '.' in str(value) else int(value)
                    except ValueError:
                        return error_response("Invalid price: must be a valid number.")
            elif key == "qty":
                value = new_qty  # Use validated `new_qty`

            setattr(sale, key, value)

        # Set default price from stock source if no new or original price exists
        if sale.item_id and not sale.price:
            sale.price = former_price

        # Calculate total if qty and price are available
        if sale.qty and sale.price:
            sale.total = float(sale.qty) * float(sale.price)
        else:
            return error_response("Quantity and price must be valid numbers for total calculation.")

        db.session.commit()
        return success_response("Sale updated successfully.", sale.to_dict())

    except SQLAlchemyError as e:
        db.session.rollback()
        traceback.print_exc()
        return error_response(f"Database error: {str(e)}")
    except Exception as e:
        traceback.print_exc()
        return error_response(f"Unexpected error: {str(e)}")

from sqlalchemy.orm import joinedload
# DELETE: Remove a sale record
@sales_bp.route('/sales/<int:sale_id>', methods=['DELETE'])
def delete_sale(sale_id):
    try:
        # Use eager loading to load related data at the time of querying to curb below errors.
        """ 
        File "C:\_\pythonic\flask\africana\env\Lib\site-packages\sqlalchemy\orm\strategies.py", line 918, in _load_for_state
        raise orm_exc.DetachedInstanceError(
        sqlalchemy.orm.exc.DetachedInstanceError: Parent instance <Sales at 0x226c46caf30> is not bound to a Session; 
        lazy load operation of attribute 'item' cannot proceed (Background on this error at: https://sqlalche.me/e/20/bhk3)
        """
        # sale = Sales.query.get(sale_id)
        # sale = db.session.query(Sales).options(db.joinedload(Sales.extraction)).get(sale_id)
        sale = Sales.query.options(joinedload(Sales.item)).get(sale_id)
        
        if not sale:
            return error_response("Sale record not found.")

        # Perform any necessary operations with `sale.item` here
        # Example: Adjust stock if necessary based on `sale.item` properties

        db.session.delete(sale)
        db.session.commit()

        return success_response("Sale record deleted successfully.")
    
    except SQLAlchemyError as e:
        db.session.rollback()
        traceback.print_exc()
        return error_response(f"Database error: {str(e)}")
    except Exception as e:
        traceback.print_exc()
        return error_response(f"Unexpected error: {str(e)}")
