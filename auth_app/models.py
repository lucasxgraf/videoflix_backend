from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager


class CustomUserManager(UserManager):
    """
    Manager for CustomUser.
    Authenticates via email instead of username.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a new user with a hashed password.
        The account stays inactive until it is confirmed via the activation email.
        """
        if email is None:
            raise ValueError("User must have an email address.")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a new superuser.
        Sets is_staff, is_superuser and is_active to True.
        """
        if email is None:
            raise ValueError("Superuser must have an email address.")

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    User model authenticated by email instead of username.
    Inactive by default until account activation.
    """

    username = None
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()
