from django.urls import path

from . import views

app_name = 'reviews'

urlpatterns = [
    path('crear/<int:pk>/', views.review_create, name='review_create'),
    path('<int:review_id>/reportar/', views.report_review, name='report_review'),
]
