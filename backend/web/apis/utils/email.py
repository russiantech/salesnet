from flask import current_app, render_template
from flask_mail import Message
from threading import Thread
import traceback
# from web.apis.utils.helpers import error_response, success_response
from web.extensions import mail

def send_email(subject, sender=None, recipients=None, text_body='', html_body=''):
    """
    Sends an email asynchronously using Flask-Mail.
    
    Args:
        subject (str): The subject of the email.
        sender (str, optional): The email sender. Defaults to `MAIL_DEFAULT_SENDER` if not provided.
        recipients (list, optional): List of recipient email addresses.
        text_body (str, optional): The plain-text content of the email.
        html_body (str, optional): The HTML content of the email.

    """
    def send_async_email(app, msg):
        try:
            with app.app_context():
                mail.send(msg)
                print("Success: Email sent successfully!")
        except Exception:
            traceback.print_exc()

    # Use default sender from app configuration if sender is not provided
    if sender is None:
        sender = current_app.config.get('MAIL_DEFAULT_SENDER')

     # Ensure the sender is in the format "Sender Name <email>"
    if isinstance(sender, str) and '@' in sender:
        sender = f"Techa <{sender}>"
        
    if not recipients:
        raise ValueError("Recipients list cannot be empty.")

    # Create the email message
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body

    # Use Flask's application context in a separate thread
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

def reset_email(user):
    token = user.make_token(token_type="reset_password")
    send_email(
        '[Techa] . Reset Your Password',
        # sender="no-reply@techa.tech",
        recipients=[user.email],
        text_body=render_template('email/forgot.txt', user=user, token=token),
        html_body=render_template('email/forgot.html', user=user, token=token)
    )

def verify_email(user):
    token = user.make_token(token_type="verify_email")
    # print("verification-token-email ->", token)
    send_email(
        '[Techa] . Verify Your Email Address.',
        # sender="no-reply@techa.tech",
        recipients=[user.email],
        text_body=render_template('email/verify.txt', user=user, token=token),
        html_body=render_template('email/verify.html', user=user, token=token)
    )

def confirm_email(user):
    token = user.make_token(token_type="confirm_email")
    send_email(
        '[Techa] . Confirmations',
        sender="no-reply@techa.tech",
        recipients=[user.email],
        text_body=render_template('email/verify.txt', user=user, token=token),
        html_body=render_template('email/verify.html', user=user, token=token)
    )



