from calendar import month_abbr
from datetime import datetime
from flask import Blueprint, jsonify
from flask_login import login_required
from sqlalchemy import extract, func
from web.models import Expenses, Items, Sales, db

# apportion_bp = Blueprint('apportion', __name__)
stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/<string:data>/stats') 
@login_required
def api(data):
    
    current_year = datetime.now().year

    if data == 'monthly_sales':

        monthly_sales = db.session.query(
            extract('month', Sales.updated).label('month'),
            func.sum(Sales.qty * Items.s_price).label('total_sales')
        ).join(Items, Items.id == Sales.item_id).filter(
            extract('year', Sales.updated) == current_year,
            Sales.deleted == False
        ).group_by(extract('month', Sales.updated)).all()

        monthly_sales = [{'monthabr': month_abbr[x.month], 'sales': x.total_sales} for x in monthly_sales]

        return jsonify(monthly_sales)

    if data == 'monthly_xp':
        monthly_xp = db.session.query(
            extract('month', Expenses.updated).label('month'),
            func.sum(Expenses.cost).label('total_xp')
        ).filter(
            extract('year', Expenses.updated) == current_year,
            Expenses.deleted == False
        ).group_by(extract('month', Expenses.updated)).all()

        #month_short = month_abbr[1:]

        monthly_xp = [{'monthabr': month_abbr[x.month], 'xps': x.total_xp} for x in monthly_xp]

        return jsonify(monthly_xp)
    
    from decimal import Decimal
    if data == 'monthly_income':
        monthly_income = []
        for year, month in db.session.query(func.extract('year', Sales.updated), func.extract('month', Sales.updated)).distinct():
            sales_amount = db.session.query(func.sum(Sales.qty * Items.s_price)).join(Items, Items.id == Sales.item_id).filter(
                func.extract('year', Sales.updated) == year,
                func.extract('month', Sales.updated) == month,
                Sales.deleted == False
            ).scalar() or 0.0
            expenses_amount = db.session.query(func.sum(Expenses.cost)).filter(
                func.extract('year', Expenses.updated) == year,
                func.extract('month', Expenses.updated) == month,
                Expenses.deleted == False
            ).scalar() or 0.0

            # Convert sales_amount and expenses_amount to Decimal before subtraction
            sales_amount = Decimal(sales_amount)
            expenses_amount = Decimal(expenses_amount)
            income = sales_amount - expenses_amount if (sales_amount is not None and expenses_amount is not None) else Decimal(0)

            monthly_income.append({'monthabr': month_abbr[int(month)], 'income': income})

        return jsonify(monthly_income)
