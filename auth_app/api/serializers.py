from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers

from auth_app.models import CustomUser


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Validates and creates a new, inactive user.
    Requires a matching password confirmation and a strong password.
    """

    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'confirmed_password']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def validate(self, data):
        """
        Ensure password and confirmed_password match and satisfy
        Django's configured password strength rules.
        """
        if data['password'] != data['confirmed_password']:
            raise serializers.ValidationError("Passwords do not match.")
        validate_password(data['password'])
        return data

    def validate_email(self, value):
        """Reject the email if it is already registered."""
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value

    def create(self, validated_data):
        """Create the user via CustomUserManager, discarding the confirmation field."""
        validated_data.pop('confirmed_password')
        user = CustomUser.objects.create_user(**validated_data)
        return user


class PasswordResetSerializer(serializers.Serializer):
    """Validates the email address for a password reset request."""

    email = serializers.EmailField()


class PasswordConfirmSerializer(serializers.Serializer):
    """
    Validates a new password submitted to confirm a password reset.
    Requires a matching confirmation and a strong password.
    """

    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        """
        Ensure new_password and confirm_password match and satisfy
        Django's configured password strength rules.
        """
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        validate_password(data['new_password'])
        return data
