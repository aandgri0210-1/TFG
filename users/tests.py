from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelTests(TestCase):
    """Test cases for User model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_user_creation(self):
        """Test that user is created correctly"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')


class UserAuthenticationTests(TestCase):
    """Test cases for user authentication"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='authtest',
            email='auth@example.com',
            password='securepass123'
        )

    def test_user_login(self):
        """Test user login"""
        self.assertTrue(
            self.client.login(
                username='authtest',
                password='securepass123'
            )
        )
