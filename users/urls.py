from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    path('registro/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('perfil/', views.profile, name='profile'),
    path('perfil/editar/', views.profile_edit, name='profile_edit'),
    path('perfil/cambiar-contrasena/', views.profile_change_password, name='profile_change_password'),
    path('cambiar-contrasena/', views.force_password_change, name='force_password_change'),
    path('panel/', views.admin_dashboard, name='admin_dashboard'),
    path('panel/usuario/<int:pk>/editar/', views.admin_user_edit, name='admin_user_edit'),
    path('panel/usuario/<int:pk>/toggle/', views.admin_user_toggle, name='admin_user_toggle'),
    path('panel/usuario/<int:pk>/restablecer-contraseña/', views.admin_user_reset_password, name='admin_user_reset_password'),
    path('panel/usuario/<int:pk>/restablecer-contraseña/confirmación/', views.admin_user_reset_password_confirm, name='admin_user_reset_password_confirm'),
    path('panel/usuario/<int:pk>/borrar/', views.admin_user_delete, name='admin_user_delete'),
    path('panel/anuncio/<int:pk>/borrar/', views.admin_service_delete, name='admin_service_delete'),
    path('panel/resena/<int:pk>/borrar/', views.admin_review_delete, name='admin_review_delete'),
    path('panel/resena/<int:pk>/borrar-comentario/', views.admin_review_comment_clear, name='admin_review_comment_clear'),
    path('panel/categorias/crear/', views.admin_category_create, name='admin_category_create'),
    path('panel/categorias/<int:pk>/borrar/', views.admin_category_delete, name='admin_category_delete'),
    path('panel/tipos/crear/', views.admin_listing_type_create, name='admin_listing_type_create'),
    path('panel/tipos/<int:pk>/borrar/', views.admin_listing_type_delete, name='admin_listing_type_delete'),
    path('panel/incidencias/', views.admin_review_reports, name='admin_review_reports'),
    path('panel/incidencias/<int:pk>/resolver/', views.admin_report_resolve, name='admin_report_resolve'),
    path('panel/incidencias/<int:pk>/eliminar/', views.admin_report_delete_review, name='admin_report_delete_review'),
    path('panel/incidencias-anuncios/', views.admin_service_reports, name='admin_service_reports'),
    path('panel/incidencias-anuncios/<int:pk>/resolver/', views.admin_service_report_resolve, name='admin_service_report_resolve'),
    path('panel/incidencias-anuncios/<int:pk>/eliminar/', views.admin_service_report_delete_service, name='admin_service_report_delete_service'),
]
