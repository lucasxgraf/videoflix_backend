from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings


def send_activation_email(user_id, uidb64, token):
    CustomUser = get_user_model()
    user = CustomUser.objects.get(pk=user_id)
    
    subject = 'Videoflix - Activate Your Account'
    message = f'Hey {user.email},\n\nPlease activate your account by clicking the link below:\n\nhttp://example.com/activate/{uidb64}/{token}/\n\nThank you!'
    from_email = settings.DEFAULT_FROM_EMAIL
    email_to = [user.email]

    send_mail(subject, message, from_email, email_to)

def send_password_reset_email(user_id, uidb64, token):
    CustomUser = get_user_model()
    user = CustomUser.objects.get(pk=user_id)
    
    subject = 'Videoflix - Reset Your Password'
    message = f'Hey {user.email},\n\nYou can reset your password by clicking the link below:\n\nhttp://example.com/reset-password/{uidb64}/{token}/\n\nThank you!'
    from_email = settings.DEFAULT_FROM_EMAIL
    email_to = [user.email]

    send_mail(subject, message, from_email, email_to)