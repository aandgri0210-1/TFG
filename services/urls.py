from django.urls import path

from . import views

app_name = 'services'

urlpatterns = [
    path('', views.service_list, name='service_list'),
    path('mis-anuncios/', views.my_services, name='my_services'),
    path('localidades/reverse/', views.location_reverse, name='location_reverse'),
    path('localidades/', views.location_search, name='location_search'),
    path('crear/', views.service_create, name='service_create'),
    path('<int:pk>/report/', views.report_service, name='service_report'),
    path('<int:pk>/editar/', views.service_edit, name='service_edit'),
    path('<int:pk>/borrar/', views.service_delete, name='service_delete'),
    path('<int:pk>/', views.service_detail, name='service_detail'),
]
