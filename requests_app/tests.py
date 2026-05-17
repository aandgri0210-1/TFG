from django.test import TestCase
from requests_app.models import ServiceRequest
from services.models import Service, Category
from django.contrib.auth import get_user_model

User = get_user_model()


class ServiceRequestModelTests(TestCase):
    """Test cases for ServiceRequest model"""

    def setUp(self):
        self.professional = User.objects.create_user(
            username='professional',
            email='prof@example.com',
            password='pass123',
            role=User.PROFESSIONAL
        )
        self.customer = User.objects.create_user(
            username='customer',
            email='cust@example.com',
            password='pass123',
            role=User.CUSTOMER
        )
        self.category = Category.objects.create(name='Mecánica')
        self.service = Service.objects.create(
            title='Reparación',
            description='Reparación de motor',
            professional=self.professional,
            category=self.category,
            price=100.00
        )

    def test_service_request_creation(self):
        """Test that service request is created correctly"""
        request = ServiceRequest.objects.create(
            service=self.service,
            requester=self.customer,
            message='Solicito este servicio'
        )
        self.assertEqual(request.status, ServiceRequest.PENDING)
        self.assertEqual(request.requester, self.customer)
