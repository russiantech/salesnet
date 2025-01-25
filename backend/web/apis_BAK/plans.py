from flask import request, Blueprint
from web.models import db
from web.apis.utils.helpers import success_response, error_response
from web.apis.utils.valid_schemas import plan_schema
from web.models import Plan
from jsonschema import validate, ValidationError
from sqlalchemy import func

plan_bp = Blueprint('plans', __name__)

@plan_bp.route('/plans', methods=['GET'])
@plan_bp.route('/plans/<int:plan_id>', methods=['GET'])
def get_plans(plan_id=None):
    try:
        # Fetch specific plan record by ID
        if plan_id:
            plan = Plan.query.get(plan_id)
            if not plan or plan.deleted:
                return error_response("Plan not found.")
            return success_response("Plan fetched successfully.", data=plan.to_dict())
        
        plans = Plan.query.filter_by(deleted=False).all()
        data = [plan.to_dict() for plan in plans]
        return success_response("Plans fetched successfully", data=data)
    except Exception as e:
        return error_response(f"An error occurred: {str(e)}")

@plan_bp.route('/plans', methods=['POST'])
def create_plan():
    try:
        
        data = request.json
        
        # Validate the incoming data against the JSON schema
        try:
            validate(instance=data, schema=plan_schema)
        except ValidationError as e:
            return error_response(f"Validation error: {e.message}")
        
        new_plan = Plan(
            plan_title=data['plan_title'],
            plan_amount=data['plan_amount'],
            plan_currency=data['plan_currency'],
            plan_descr=data.get('plan_descr', ''),
            plan_type=data['plan_type'],
            plan_duration=data['plan_duration'],
            plan_features=data['plan_features'],
            plan_avatar=data.get('plan_avatar')
        )
        
        db.session.add(new_plan)
        db.session.commit()
        return success_response("Plan created successfully.", data=new_plan.to_dict(), status_code=201)
    except Exception as e:
        return error_response(f"An error occurred: {str(e)}")

@plan_bp.route('/plans/<int:id>', methods=['PUT'])
def update_plan(id):
    try:
        
        plan = Plan.query.get_or_404(id)

        data = request.json
        
        # Validate the incoming data against the JSON schema
        try:
            validate(instance=data, schema=plan_schema)
        except ValidationError as e:
            return error_response(f"Validation error: {e.message}")
        
        plan.plan_title = data.get('plan_title', plan.plan_title)
        plan.plan_amount = data.get('plan_amount', plan.plan_amount)
        plan.plan_currency = data.get('plan_currency', plan.plan_currency)
        plan.plan_descr = data.get('plan_descr', plan.plan_descr)
        plan.plan_type = data.get('plan_type', plan.plan_type)
        plan.plan_duration = data.get('plan_duration', plan.plan_duration)
        plan.plan_features = data.get('plan_features', plan.plan_features)
        plan.plan_avatar = data.get('plan_avatar', plan.plan_avatar)
        plan.updated_at = func.now()
        
        db.session.commit()
        return success_response("Plan updated successfully.", data=plan.to_dict())
    except Exception as e:
        return error_response(f"An error occurred: {str(e)}")

@plan_bp.route('/plans/<int:id>', methods=['DELETE'])
def delete_plan(id):
    try:
        plan = Plan.query.get_or_404(id)
        # plan.deleted = True
        db.session.delete(plan)
        db.session.commit()
        return success_response("Plan deleted successfully.", status_code=204)
    except Exception as e:
        return error_response(f"An error occurred: {str(e)}")




""" =============== """

@plan_bp.route('/insert-plans', methods=['GET'])
def insert():
    try:
        # Plans to be added
        weekly_plan = Plan(
            plan_title="Weekly",
            plan_amount=1500,
            plan_currency="NGN",
            plan_descr="For businesses needing quick insights to stay on top of daily activities and receive instant alerts for effective decision-making. Essential features for immediate impact.",
            plan_type="weekly",
            plan_duration=7,
            plan_features=[
                "Start scaling!",
                "Watch and analyze your business growth without a data analyst.",
                "Track inventory and measure sales.",
                "Manage your users/workers in one place.",
                "Receive timely alerts on low stock to prevent any interruptions in business operations.",
                "Stay informed about stock status changes in real-time to address shortages or excess inventory."
            ]
        )

        monthly_plan = Plan(
            plan_title="Monthly",
            plan_amount=5000,
            plan_currency="NGN",
            plan_descr="For businesses looking to manage and measure their performance comprehensively. Monthly plans offer enhanced reporting and tracking capabilities.",
            plan_type="monthly",
            plan_duration=30,
            plan_features=[
                "Get started now!",
                "Track monthly profits or losses to assess business health and profitability.",
                "Get detailed sales reports every month to understand sales trends and plan inventory accordingly.",
                "Manage multiple businesses simultaneously, simplifying multi-business operations.",
                "Organize inventory, sales, and personnel based on departmental structures for more granular management.",
                "Access reports for various date ranges to analyze performance metrics and support month-to-month planning."
            ]
        )

        yearly_plan = Plan(
            plan_title="Yearly",
            plan_amount=50000,
            plan_currency="NGN",
            plan_descr="Ideal for large-scale businesses requiring continuous, unrestricted access. Yearly plans unlock all features and support strategic growth and long-term analysis.",
            plan_type="yearly",
            plan_duration=365,
            plan_features=[
                "Get inventory-pro!",
                "Regular updates with new features, custom domain, and priority email/WhatsApp support.",
                "Apportioning: Allocate resources precisely across departments, locations, or time periods to improve efficiency and budget management.",
                "Register as many products as needed without restrictions, accommodating business growth and expanded offerings.",
                "Storage unlimited: Enjoy unlimited storage, ideal for businesses with extensive product ranges and historical data.",
                "Export data to other platforms or software, streamlining inventory management and allowing for easier data transfer."
            ]
        )

        # Commit the plans to the database
        db.session.add_all([weekly_plan, monthly_plan, yearly_plan])
        db.session.commit()
        
        data = {
                "weekly_plan": weekly_plan.to_dict(),
                "monthly_plan": monthly_plan.to_dict(),
                "yearly_plan": yearly_plan.to_dict()
            }
        
        return success_response("Plans inserted successfully.", data=data)

    except Exception as e:
        return error_response(f"An error occurred: {str(e)}")
