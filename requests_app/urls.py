from django.urls import path

from . import views

app_name = 'requests_app'

urlpatterns = [
    path('', views.request_history, name='request_history'),
    path('crear/<int:pk>/', views.request_create, name='request_create'),
    path('<int:pk>/cancelar/', views.request_cancel, name='request_cancel'),
    path('profesional/', views.provider_requests, name='provider_requests'),
    path('profesional/<int:pk>/<str:action>/', views.provider_request_update, name='provider_request_update'),
]
