from django.test import TestCase
from services.models import Service, Category
from django.contrib.auth import get_user_model

User = get_user_model()


class ServiceModelTests(TestCase):
    """Test cases for Service model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='provider',
            email='provider@example.com',
            password='pass123',
            role=User.PROFESSIONAL
        )
        self.category = Category.objects.create(name='Mecánica')
        self.service = Service.objects.create(
            title='Cambio de aceite',
            description='Servicio de cambio de aceite',
            professional=self.user,
            category=self.category,
            price=50.00
        )

    def test_service_creation(self):
        """Test that service is created correctly"""
        self.assertEqual(self.service.title, 'Cambio de aceite')
        self.assertEqual(self.service.professional, self.user)
        self.assertTrue(self.service.is_active)


class ServiceQueryTests(TestCase):
    """Test cases for Service queries"""

    def test_service_list(self):
        """Test service listing"""
        services = Service.objects.all()
        self.assertEqual(services.count(), 0)
