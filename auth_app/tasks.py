from django.contrib.auth import get_user_model
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

def send_activation_email(user_id, uidb64, token):
    CustomUser = get_user_model()
    user = CustomUser.objects.get(pk=user_id)
    
    username = user.email.split('@')[0]
    activation_link = f'{settings.FRONTEND_URL}/activate/{uidb64}/{token}/'
    backend_url = settings.BACKEND_URL
    html_message = render_to_string('email/activation_email.html', {
        'username': username,
        'activation_link': activation_link,
        'backend_url': backend_url,
    })
    
    subject = 'Videoflix - Activate Your Account'
    plain_text_message = f'Hey {user.email},\n\nPlease activate your account by clicking the link below:\n\n{activation_link}\n\nThank you!'
    from_email = settings.DEFAULT_FROM_EMAIL
    email_to = [user.email]
    
    email = EmailMultiAlternatives(subject, plain_text_message, from_email, email_to)
    email.attach_alternative(html_message, "text/html")
    email.send()

def send_password_reset_email(user_id, uidb64, token):
    CustomUser = get_user_model()
    user = CustomUser.objects.get(pk=user_id)
    
    username = user.email.split('@')[0]
    password_reset_link = f'{settings.FRONTEND_URL}/reset-password/{uidb64}/{token}/'
    backend_url = settings.BACKEND_URL
    password_reset_link_valid_hours = settings.PASSWORD_RESET_TIMEOUT
    html_message = render_to_string('email/password_reset_email.html', {
        'username': username,
        'password_reset_link': password_reset_link,
        'backend_url': backend_url,
        'password_reset_link_valid_hours': password_reset_link_valid_hours,
    })
    
    subject = 'Videoflix - Reset Your Password'
    plain_text_message = f'Hey {user.email},\n\nPlease reset your password by clicking the link below:\n\n{password_reset_link}\n\nThank you!'
    from_email = settings.DEFAULT_FROM_EMAIL
    email_to = [user.email]

    email = EmailMultiAlternatives(subject, plain_text_message, from_email, email_to)
    email.attach_alternative(html_message, "text/html")
    email.send()