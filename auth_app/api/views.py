from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
import django_rq

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import TokenError

from auth_app.tasks import send_activation_email, send_password_reset_email
from .serializers import RegistrationSerializer, PasswordResetSerializer, PasswordConfirmSerializer
from .utils import (
    build_login_response_data,
    set_auth_cookies,
    blacklist_refresh_token,
    clear_auth_cookies,
    generate_new_access_token,
    set_access_cookie,
    enqueue_token_email,
    get_user_from_uidb64,
    get_refresh_token_or_error,
)


class RegistrationView(generics.GenericAPIView):
    """Registers a new, inactive user and enqueues an activation email."""

    permission_classes = []

    def post(self, request, *args, **kwargs):
        """
        Validate and save the new user, then send the activation email
        in the background via RQ.
        """
        serializer = RegistrationSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            user = serializer.instance
            uidb64, token = enqueue_token_email(send_activation_email, user)

            return Response({"user": {"id": user.id, "email": user.email}, "token": token},
                             status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActivationView(generics.GenericAPIView):
    """Activates a user account via the link sent in the activation email."""

    permission_classes = []

    def get(self, request, uidb64, token):
        """
        Validate the uidb64/token pair and activate the account.
        Fails if the account is already active or the token is invalid/expired.
        """
        user = get_user_from_uidb64(uidb64)

        if user is not None and user.is_active:
            return Response({"error": "Account already activated."}, status=status.HTTP_400_BAD_REQUEST)

        if user is not None and PasswordResetTokenGenerator().check_token(user, token):
            user.is_active = True
            user.save()
            return Response({"message": "Account successfully activated."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Account activation failed."}, status=status.HTTP_400_BAD_REQUEST)


class CookieTokenObtainPairView(TokenObtainPairView):
    """Logs the user in and sets the JWT access/refresh tokens as HttpOnly cookies."""

    def post(self, request, *args, **kwargs):
        """Validate credentials and issue the auth cookies on success."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = build_login_response_data(serializer)
        response = Response(data, status=status.HTTP_200_OK)
        set_auth_cookies(
            response,
            serializer.validated_data['access'],
            serializer.validated_data['refresh'])

        return response


class LogoutView(generics.GenericAPIView):
    """Logs the user out by blacklisting the refresh token and clearing the auth cookies."""

    permission_classes = []

    def post(self, request, *args, **kwargs):
        """
        Blacklist the refresh token from the cookie and remove both auth cookies.
        Requires no valid access token, only a refresh token cookie.
        """
        refresh_token_string, error_response = get_refresh_token_or_error(request)
        if error_response:
            clear_auth_cookies(error_response)
            return error_response

        try:
            blacklist_refresh_token(refresh_token_string)
        except TokenError:
            response = Response({"detail": "Invalid refresh token."},
                                status=status.HTTP_400_BAD_REQUEST)
            clear_auth_cookies(response)
            return response

        detail = "Logout successful! All Tokens will be deleted. Refresh token is now invalid."
        response = Response({"detail": detail}, status=status.HTTP_200_OK)

        clear_auth_cookies(response)

        return response


class CookieTokenRefreshView(generics.GenericAPIView):
    """Issues a new access token cookie from a valid refresh token cookie."""

    permission_classes = []

    def post(self, request, *args, **kwargs):
        """Read the refresh token cookie and set a refreshed access token cookie."""
        refresh_token_string, error_response = get_refresh_token_or_error(request)
        if error_response:
            return error_response
        
        try:
            new_access_token = generate_new_access_token(refresh_token_string)
        except TokenError:
            return Response({"detail": "Invalid refresh token."},
                            status=status.HTTP_401_UNAUTHORIZED)

        response = Response({"detail": "Token refreshed",
                            "access": new_access_token}, status=status.HTTP_200_OK)
        set_access_cookie(response, new_access_token)
        return response


class PasswordResetView(generics.GenericAPIView):
    """Requests a password reset email for the given address, if an account exists."""

    permission_classes = []
    serializer_class = PasswordResetSerializer

    def post(self, request, *args, **kwargs):
        """
        Enqueue a reset email if a user with the given email exists.
        Always returns the same response, regardless of whether the account exists,
        to avoid leaking account existence.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        CustomUser = get_user_model()

        try:
            user = CustomUser.objects.get(email=email)
            enqueue_token_email(send_password_reset_email, user)
        except CustomUser.DoesNotExist:
            pass

        return Response({"detail": "An email has been sent to reset your password."}, status=status.HTTP_200_OK)


class PasswordConfirmView(generics.GenericAPIView):
    """Sets a new password via the link sent in the password reset email."""

    permission_classes = []

    def post(self, request, uidb64, token, *args, **kwargs):
        """
        Validate the uidb64/token pair and set the new password.
        The token becomes invalid afterwards since it is derived from the password hash.
        """
        user = get_user_from_uidb64(uidb64)

        if user is not None and PasswordResetTokenGenerator().check_token(user, token):
            serializer = PasswordConfirmSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"detail": "Your Password has been successfully reset."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Password reset failed."}, status=status.HTTP_400_BAD_REQUEST)
