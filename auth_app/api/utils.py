from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
import django_rq

from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken


def build_login_response_data(serializer):
    """
    Build the login response body.
    Contains only basic user info since the actual tokens live in HttpOnly cookies.
    """
    data = {
        "detail": "Login successful",
        "user": {
            "id": serializer.user.id,
            "email": serializer.user.email,
        }
    }

    return data


def set_auth_cookies(response, access, refresh):
    """Set the access_token and refresh_token as HttpOnly cookies on the response."""
    _set_cookie(response, 'access_token', access)
    _set_cookie(response, 'refresh_token', refresh)
    return response


def _set_cookie(response, key, value):
    """
    Set a single HttpOnly cookie with SameSite=Lax.
    Marked Secure outside of DEBUG only - browsers refuse to store Secure
    cookies over plain HTTP, which is how the app runs locally in DEBUG mode.
    """
    response.set_cookie(key=key, value=value, httponly=True, secure=not settings.DEBUG, samesite='Lax')


def set_access_cookie(response, new_access_token):
    """Set only the access_token cookie, used after a token refresh."""
    _set_cookie(response, 'access_token', new_access_token)


def get_refresh_token_or_error(request):
    """
    Read the refresh_token cookie from the request.
    Returns (token, None) on success, or (None, error_response) if the cookie is missing.
    """
    token = request.COOKIES.get('refresh_token')
    if token:
        return token, None
    return None, Response({"detail": "Refresh token not provided."}, status=status.HTTP_400_BAD_REQUEST)


def blacklist_refresh_token(refresh_token_string):
    """Invalidate a refresh token by adding it to the blacklist."""
    refresh_token = RefreshToken(refresh_token_string)
    refresh_token.blacklist()


def clear_auth_cookies(response):
    """Remove the access_token and refresh_token cookies from the response."""
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')


def generate_new_access_token(refresh_token_string):
    """Create a new access token from a valid, non-blacklisted refresh token."""
    refresh_token = RefreshToken(refresh_token_string)
    new_access_token = str(refresh_token.access_token)
    return new_access_token


def get_user_from_uidb64(uidb64):
    """
    Decode a base64-encoded user id and look up the matching user.
    Returns None if the id is malformed or no matching user exists.
    """
    User = get_user_model()
    try:
        uid = urlsafe_base64_decode(force_str(uidb64)).decode()
        return User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None


def enqueue_token_email(task_fn, user):
    """
    Generate a uidb64/token pair for the given user and enqueue the given
    email task (RQ) with it. Returns the pair so callers can reuse it, e.g. in a response body.
    """
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = PasswordResetTokenGenerator().make_token(user)
    queue = django_rq.get_queue('default')
    queue.enqueue(task_fn, user.id, uidb64, token)
    return uidb64, token