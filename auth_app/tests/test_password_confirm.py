from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from rest_framework import status
from rest_framework.test import APITestCase

from auth_app.models import CustomUser


class PasswordConfirmTest(APITestCase):
    def setUp(self):
        self.user_data = {
            'email': 'user@example.com',
            'password': 'securepassword',
        }

        self.reset_password_payload = {
            'new_password': 'newsecurepassword',
            'confirm_password': 'newsecurepassword',
        }

        self.user = CustomUser.objects.create_user(email=self.user_data['email'], password=self.user_data['password'])

        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = PasswordResetTokenGenerator().make_token(self.user)
        self.url = reverse('password_confirm', kwargs={'uidb64': self.uid, 'token': self.token})

    def test_password_confirm_success(self):
        response = self.client.post(self.url, self.reset_password_payload, format='json')

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.check_password(self.reset_password_payload['new_password']))

    def test_password_confirm_missmatched_passwords(self):
        self.reset_password_payload['confirm_password'] = 'differentpassword'
        response = self.client.post(self.url, self.reset_password_payload, format='json')

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.user.check_password(self.reset_password_payload['new_password']))

    def test_password_confirm_weak_password(self):
        self.reset_password_payload['new_password'] = '123'
        self.reset_password_payload['confirm_password'] = '123'
        response = self.client.post(self.url, self.reset_password_payload, format='json')

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.user.check_password(self.reset_password_payload['new_password']))

    def test_password_confirm_invalid_token(self):
        token = 'invalid-token'
        url = reverse('password_confirm', kwargs={'uidb64': self.uid, 'token': token})
        response = self.client.post(url, self.reset_password_payload, format='json')

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.user.check_password(self.reset_password_payload['new_password']))

    def test_password_confirm_invalid_uid(self):
        uid = urlsafe_base64_encode(force_bytes(9999))
        url = reverse('password_confirm', kwargs={'uidb64': uid, 'token': self.token})
        response = self.client.post(url, self.reset_password_payload, format='json')

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.user.check_password(self.reset_password_payload['new_password']))

    def test_password_confirm_already_confirmed(self):
        response = self.client.post(self.url, self.reset_password_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(self.url, self.reset_password_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
