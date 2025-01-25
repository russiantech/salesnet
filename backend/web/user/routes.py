from flask import Blueprint, render_template

showcase_bp = Blueprint('showcase', __name__)

@showcase_bp.route('/')
def showcase():
    return render_template('showcase/index.html')
