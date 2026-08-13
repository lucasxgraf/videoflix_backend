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
        Ensure password and confirmed_password match, satisfy Django's
        configured password strength rules, and that the email isn't
        already registered. The email check is raised as a non-field
        error so the response shape doesn't reveal which check failed,
        preventing account enumeration via the given email address.
        """
        if data['password'] != data['confirmed_password']:
            raise serializers.ValidationError("Passwords do not match.")
        validate_password(data['password'])
        
        if CustomUser.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError(
                'Please check your input and try again.')
        return data

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
