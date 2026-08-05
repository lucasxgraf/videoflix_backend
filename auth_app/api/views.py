from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import RegistrationSerializer
from .utils import build_login_response_data, set_auth_cookies

class RegistrationView(generics.GenericAPIView):
    permission_classes = []

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            user = serializer.instance
            token = PasswordResetTokenGenerator().make_token(user)

            return Response({"user": 
                { "id": user.id, "email": user.email },
                "token": token},
                status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ActivationView(generics.GenericAPIView):
    permission_classes = []
    
    def get(self, request, uidb64, token):
        CustomUser = get_user_model()
        
        try:
            uid = urlsafe_base64_decode(force_str(uidb64)).decode()
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            user = None    
        
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