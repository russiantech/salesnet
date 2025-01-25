
from flask import render_template, stream_template, Blueprint
from flask_login import login_required
from web.apis.utils.decorators import role_required

main = Blueprint('main', __name__)

@main.route("/users", methods=['GET', 'POST'])
@login_required
@role_required('*')
def users():
    context = {
    'pname' : 'Users : [staffs . customers . suppliers]',
    'users': "users"
    }
    
    return stream_template('users/index.html', **context)

@main.route('/us')
@login_required
def us():
    return render_template("us.html", pname='About Us')

@main.route('/terms')
@login_required
def terms():
    return render_template("terms.html", pname='Terms Of Use')

@main.route('/privacy')
def privacy():
    return render_template("privacy.html", pname='Privacy Policy')

@main.route('/faqs')
def faqs():
    return render_template("faqs.html", pname='Frequently Asked Questions')
