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
    permission_classes = []

    def post(self, request, *args, **kwargs):
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
    permission_classes = []

    def get(self, request, uidb64, token):
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
    def post(self, request, *args, **kwargs):
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
    permission_classes = []

    def post(self, request, *args, **kwargs):
        refresh_token_string, error_response = get_refresh_token_or_error(request)
        if error_response:
            return error_response

        try:
            blacklist_refresh_token(refresh_token_string)
        except TokenError:
            return Response({"detail": "Invalid refresh token."},
                            status=status.HTTP_400_BAD_REQUEST)

        detail = "Logout successful! All Tokens will be deleted. Refresh token is now invalid."
        response = Response({"detail": detail}, status=status.HTTP_200_OK)

        clear_auth_cookies(response)

        return response


class CookieTokenRefreshView(generics.GenericAPIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
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
    permission_classes = []
    serializer_class = PasswordResetSerializer

    def post(self, request, *args, **kwargs):
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
    permission_classes = []

    def post(self, request, uidb64, token, *args, **kwargs):
        user = get_user_from_uidb64(uidb64)

        if user is not None and PasswordResetTokenGenerator().check_token(user, token):
            serializer = PasswordConfirmSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"detail": "Your Password has been successfully reset."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Password reset failed."}, status=status.HTTP_400_BAD_REQUEST)
