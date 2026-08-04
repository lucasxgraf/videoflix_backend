from django.contrib.auth.tokens import PasswordResetTokenGenerator

from rest_framework import generics, status
from rest_framework.response import Response

from .serializers import RegistrationSerializer

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