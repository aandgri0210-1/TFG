from django.shortcuts import redirect


class ForcePasswordChangeMiddleware:
    rutas_permitidas = (
        '/usuarios/cambiar-contrasena/',
        '/usuarios/login/',
        '/accounts/login/',
        '/accounts/logout/',
        '/admin/login/',
        '/admin/logout/',
        '/static/',
        '/media/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario = getattr(request, 'user', None)
        if usuario and usuario.is_authenticated and getattr(usuario, 'must_change_password', False):
            if not request.path.startswith(self.rutas_permitidas):
                return redirect('users:force_password_change')

        return self.get_response(request)