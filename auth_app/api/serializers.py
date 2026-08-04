from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers

from auth_app.models import CustomUser

class RegistrationSerializer(serializers.ModelSerializer):
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'confirmed_password']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def validate(self, data):
        if data['password'] != data['confirmed_password']:
            raise serializers.ValidationError("Passwords do not match.")
        validate_password(data['password'])
        return data
    
    def validate_email(self, value):
        """Ensures the email is not already registered."""
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value

    def create(self, validated_data):
        validated_data.pop('confirmed_password')
        user = CustomUser.objects.create_user(**validated_data)
        return user