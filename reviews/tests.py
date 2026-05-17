from django.test import TestCase
from reviews.models import Review
from services.models import Service, Category
from django.contrib.auth import get_user_model

User = get_user_model()


class ReviewModelTests(TestCase):
    """Test cases for Review model"""

    def setUp(self):
        self.professional = User.objects.create_user(
            username='professional',
            email='prof@example.com',
            password='pass123',
            role=User.PROFESSIONAL
        )
        self.reviewer = User.objects.create_user(
            username='reviewer',
            email='rev@example.com',
            password='pass123',
            role=User.CUSTOMER
        )
        self.category = Category.objects.create(name='Mecánica')
        self.service = Service.objects.create(
            title='Servicio test',
            description='Test service',
            professional=self.professional,
            category=self.category,
            price=50.00
        )

    def test_review_creation(self):
        """Test that review is created correctly"""
        review = Review.objects.create(
            service=self.service,
            reviewer=self.reviewer,
            rating=4.5,
            title='Excelente servicio',
            comment='Muy satisfecho con el trabajo'
        )
        self.assertEqual(review.rating, 4.5)
        self.assertEqual(review.reviewer, self.reviewer)

    def test_review_unique_constraint(self):
        """Test that only one review per user per service is allowed"""
        Review.objects.create(
            service=self.service,
            reviewer=self.reviewer,
            rating=4.0,
            title='Bueno',
            comment='Muy bien'
        )
        # Attempting to create another review by same user should fail
        with self.assertRaises(Exception):
            Review.objects.create(
                service=self.service,
                reviewer=self.reviewer,
                rating=5.0,
                title='Excelente',
                comment='Perfecto'
            )
