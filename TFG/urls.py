from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

from services import views as service_views
from users import views as user_views

urlpatterns = [
    path('', service_views.service_list, name='home'),
    path('accounts/login/', user_views.login_view, name='login'),
    path('usuarios/', include('users.urls')),
    path('servicios/', include('services.urls')),
    path('solicitudes/', include('requests_app.urls')),
    path('valoraciones/', include('reviews.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Serve static files collected in STATICFILES_DIRS during development
    urlpatterns += staticfiles_urlpatterns()
