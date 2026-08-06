from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from rest_framework import status
from rest_framework.test import APITestCase

from unittest.mock import patch

from auth_app.models import CustomUser
from auth_app.tasks import send_activation_email, send_password_reset_email

class RegistrationTestCase(APITestCase):
    def setUp(self):
        self.user_data = {
            'email': 'user@example.com',
            'password': 'securepassword',
            'confirmed_password': 'securepassword'
        }
        
        self.url = reverse('register')
        
    def test_registration_success(self):
        response = self.client.post(self.url, self.user_data, format='json')
        user = CustomUser.objects.get()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CustomUser.objects.count(), 1)
        self.assertEqual(user.email, self.user_data['email'])
        self.assertFalse(user.is_active)
        self.assertTrue(user.check_password(self.user_data['password']))
        
        self.assertIn("token", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], self.user_data["email"])
    
    def test_register_password_mismatch(self):
        user_data = self.user_data.copy()
        user_data['confirmed_password'] = 'invalid_password'
        response = self.client.post(self.url, user_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CustomUser.objects.count(), 0)
        
    def test_register_email_already_exists(self):
        CustomUser.objects.create_user(email='user@example.com', password='securepassword')

        user_data = self.user_data.copy()
        response = self.client.post(self.url, user_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CustomUser.objects.count(), 1)
        
    def test_register_weak_password(self):
        user_data = self.user_data.copy()
        user_data['password'] = '123'
        user_data['confirmed_password'] = '123'
        response = self.client.post(self.url, user_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CustomUser.objects.count(), 0)
        
    @patch('auth_app.api.views.django_rq.get_queue')
    def test_registration_enqueues_activation_email(self, mock_get_queue):
        mock_queue = mock_get_queue.return_value
        response = self.client.post(self.url, self.user_data, format='json')

        user = CustomUser.objects.get()
        expected_uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        expected_token = PasswordResetTokenGenerator().make_token(user)

        mock_queue.enqueue.assert_called_once()
        args = mock_queue.enqueue.call_args[0]

        self.assertEqual(args[0], send_activation_email)
        self.assertEqual(args[1], user.id)
        self.assertEqual(args[2], expected_uidb64)
        self.assertEqual(args[3], expected_token)