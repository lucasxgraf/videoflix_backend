from django.contrib.auth import get_user_model
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives


def send_activation_email(user_id, uidb64, token):
    """
    Send the account activation email to the given user.
    Runs as an RQ background job, contains both an HTML and a plain-text version.
    """
    user = get_user_model().objects.get(pk=user_id)

    username = user.email.split('@')[0]
    activation_link = f'{settings.FRONTEND_URL}/activate/{uidb64}/{token}/'
    backend_url = settings.BACKEND_URL

    subject = 'Videoflix - Activate Your Account'
    plain_text_message = (
        f'Hey {user.email},\n\n'
        f'Please activate your account by clicking the link below:\n\n'
        f'{activation_link}\n\nThank you!'
    )
    
    _send_html_email(user, subject, plain_text_message, 'email/activation_email.html', context={
        'username': username,
        'activation_link': activation_link,
        'backend_url': backend_url,
    })


def send_password_reset_email(user_id, uidb64, token):
    """
    Send the password reset email to the given user.
    Runs as an RQ background job, contains both an HTML and a plain-text version.
    """
    user = get_user_model().objects.get(pk=user_id)

    username = user.email.split('@')[0]
    password_reset_link = f'{settings.FRONTEND_URL}/reset-password/{uidb64}/{token}/'
    backend_url = settings.BACKEND_URL
    password_reset_link_valid_hours = settings.PASSWORD_RESET_TIMEOUT

    subject = 'Videoflix - Reset Your Password'
    plain_text_message = (
        f'Hey {user.email},\n\n'
        f'Please reset your password by clicking the link below:\n\n'
        f'{password_reset_link}\n\nThank you!'
    )
    
    _send_html_email(user, subject, plain_text_message, 'email/password_reset_email.html', context={
        'username': username,
        'password_reset_link': password_reset_link,
        'backend_url': backend_url,
        'password_reset_link_valid_hours': password_reset_link_valid_hours,
    })


def _send_html_email(user, subject, plain_text_message, template_name, context):
    """
    Render the given template as HTML and send it as an alternative
    alongside the provided plain-text body.
    """
    html_message = render_to_string(template_name, context)
    email = EmailMultiAlternatives(subject, plain_text_message, settings.DEFAULT_FROM_EMAIL, [user.email])
    email.attach_alternative(html_message, "text/html")
    email.send()
