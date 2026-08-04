from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import CustomUser

class ActivationTestCase(APITestCase):
    def setUp(self):
        self.user_data = {
            'email': 'user@example.com',
            'password': 'securepassword',
            'confirmed_password': 'securepassword'
        }
        
        self.user = CustomUser.objects.create_user(email=self.user_data['email'], password=self.user_data['password'], is_active=False)
        
        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = PasswordResetTokenGenerator().make_token(self.user)
        self.url = reverse('activate', kwargs={'uidb64': self.uid, 'token': self.token})
    
    def test_activate_user_success(self):
        response = self.client.get(self.url)

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.is_active)
    
    def test_activate_user_invalid_token(self):
        token = 'invalid-token'
        url = reverse('activate', kwargs={'uidb64': self.uid, 'token': token})
        response = self.client.get(url)
    
        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.user.is_active)
        
    def test_activate_user_invalid_uid(self):
        uid = urlsafe_base64_encode(force_bytes(9999))
        url = reverse('activate', kwargs={'uidb64': uid, 'token': self.token})
        response = self.client.get(url)

        self.user.refresh_from_db()
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.user.is_active)
        
    def test_activate_user_already_active(self):
        self.user.is_active = True
        self.user.save()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)