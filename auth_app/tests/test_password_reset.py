from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from rest_framework import status
from rest_framework.test import APITestCase

from unittest.mock import patch

from auth_app.models import CustomUser
from auth_app.tasks import send_password_reset_email

class PasswordResetTestCase(APITestCase):
    def setUp(self):
        self.user_data = {
            'email': 'user@example.com',
            'password': 'securepassword',
        }
                
        self.user = CustomUser.objects.create_user(email=self.user_data['email'], password=self.user_data['password'])
        
        self.url = reverse('password_reset')
        
    @patch('auth_app.api.views.django_rq.get_queue')
    def test_password_reset_enqueues_reset_email(self, mock_get_queue):
        mock_queue = mock_get_queue.return_value
        response = self.client.post(self.url, {'email': self.user_data['email']}, format='json')

        user = CustomUser.objects.get()
        expected_uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        expected_token = PasswordResetTokenGenerator().make_token(user)

        mock_queue.enqueue.assert_called_once()
        args = mock_queue.enqueue.call_args[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(args[0], send_password_reset_email)
        self.assertEqual(args[1], user.id)
        self.assertEqual(args[2], expected_uidb64)
        self.assertEqual(args[3], expected_token)
    
    @patch('auth_app.api.views.django_rq.get_queue')
    def test_password_reset_nonexistent_email_no_enqueue(self, mock_get_queue): 
        mock_queue = mock_get_queue.return_value
        response = self.client.post(self.url, {'email': 'nobody@example.com'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'An email has been sent to reset your password.')
        mock_queue.enqueue.assert_not_called()
        
    def test_password_reset_missing_email(self):
        response = self.client.post(self.url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        
        
        
        