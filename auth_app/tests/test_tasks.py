from django.core import mail
from django.test import TestCase, override_settings

from auth_app.models import CustomUser
from auth_app.tasks import send_activation_email, send_password_reset_email

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class SendActivationEmailTest(TestCase):
    def setUp(self):
        self.user_data = {
            'email': 'user@example.com',
            'password': 'securepassword',
        }
                
        self.user = CustomUser.objects.create_user(email=self.user_data['email'], password=self.user_data['password'])

    def test_sends_email_to_user(self):
        send_activation_email(self.user.id, 'some-uid', 'some-token')
        
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        
    def test_email_contains_activation_link_parts(self):
        send_activation_email(self.user.id, 'some-uid', 'some-token')
        
        self.assertIn('some-uid', mail.outbox[0].body)
        self.assertIn('some-token', mail.outbox[0].body)
        
@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class SendPasswordResetEmailTest(TestCase):
    def setUp(self):
        self.user_data = {
            'email': 'user@example.com',
            'password': 'securepassword',
        }
                
        self.user = CustomUser.objects.create_user(email=self.user_data['email'], password=self.user_data['password'])

    def test_sends_reset_email_to_user(self):
        send_password_reset_email(self.user.id, 'some-uid', 'some-token')
        
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        
    def test_email_contains_reset_link_parts(self):
        send_password_reset_email(self.user.id, 'some-uid', 'some-token')
        
        self.assertIn('some-uid', mail.outbox[0].body)
        self.assertIn('some-token', mail.outbox[0].body)
        

