from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.http import HttpResponseRedirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.utils import timezone
import secrets
import string

from reviews.models import Review, ReviewReport
from services.models import Category, ListingType, Service
from services.models import ServiceReport

from .forms import AdminUserForm, ForcedPasswordChangeForm, ProfileForm, UserRegistrationForm, UserUpdateForm
from .models import Profile, User


def can_access_admin_panel(user):
    return user.is_authenticated and user.is_admin_account


def login_view(request):
    if request.user.is_authenticated:
        if request.user.must_change_password:
            return redirect('users:force_password_change')
        return redirect('services:service_list')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.must_change_password:
                messages.info(request, 'Se ha restablecido tu contraseña. Ahora debes crear una nueva.')
                return redirect('users:force_password_change')
            messages.success(request, 'Sesión iniciada correctamente.')
            return redirect('services:service_list')
    else:
        form = AuthenticationForm(request)

    return render(request, 'registration/login.html', {'form': form})


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Cuenta creada correctamente.')
            return redirect('users:profile')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def profile(request):
    perfil_usuario, _ = Profile.objects.get_or_create(user=request.user)
    return render(
        request,
        'users/profile.html',
        {
            'profile_object': perfil_usuario,
            'service_count': request.user.services.count(),
            'request_count': request.user.service_requests.count(),
            'review_count': request.user.reviews.count(),
        },
    )


@login_required
def profile_change_password(request):
    if request.method == 'POST':
        formulario = PasswordChangeForm(request.user, request.POST)
        if formulario.is_valid():
            usuario = formulario.save()
            update_session_auth_hash(request, usuario)
            messages.success(request, 'Tu contraseña se ha cambiado correctamente.')
            return redirect('users:profile')
    else:
        formulario = PasswordChangeForm(request.user)

    perfil_usuario, _ = Profile.objects.get_or_create(user=request.user)
    return render(
        request,
        'users/profile_password_change.html',
        {
            'form': formulario,
            'profile_object': perfil_usuario,
        },
    )


@login_required
def force_password_change(request):
    if not request.user.must_change_password:
        return redirect('services:service_list')

    if request.method == 'POST':
        form = ForcedPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            user.must_change_password = False
            user.save(update_fields=['must_change_password'])
            update_session_auth_hash(request, user)
            messages.success(request, 'Tu contraseña se ha actualizado correctamente.')
            return redirect('services:service_list')
    else:
        form = ForcedPasswordChangeForm(request.user)

    return render(
        request,
        'users/password_force_change.html',
        {
            'form': form,
        },
    )


@login_required
def profile_edit(request):
    perfil_usuario, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        formulario_usuario = UserUpdateForm(request.POST, instance=request.user)
        formulario_perfil = ProfileForm(request.POST, request.FILES, instance=perfil_usuario)
        if formulario_usuario.is_valid() and formulario_perfil.is_valid():
            formulario_usuario.save()
            formulario_perfil.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('users:profile')
    else:
        formulario_usuario = UserUpdateForm(instance=request.user)
        formulario_perfil = ProfileForm(instance=perfil_usuario)
    return render(
        request,
        'users/profile_form.html',
        {
            'user_form': formulario_usuario,
            'profile_form': formulario_perfil,
            'profile_object': perfil_usuario,
        },
    )


@login_required
def admin_dashboard(request):
    if not can_access_admin_panel(request.user):
        messages.error(request, 'No tienes permisos para acceder al panel de administración.')
        return redirect('services:service_list')

    ListingType.objects.get_or_create(name='Servicio', defaults={'slug': 'servicio'})
    ListingType.objects.get_or_create(name='Producto', defaults={'slug': 'producto'})

    usuarios = User.objects.select_related('profile').all().order_by('-date_joined')
    texto_busqueda = (request.GET.get('q') or '').strip()
    filtro_rol = (request.GET.get('role') or '').strip()
    filtro_estado = (request.GET.get('status') or '').strip()

    if texto_busqueda:
        usuarios = usuarios.filter(
            Q(username__icontains=texto_busqueda)
            | Q(first_name__icontains=texto_busqueda)
            | Q(last_name__icontains=texto_busqueda)
            | Q(email__icontains=texto_busqueda)
            | Q(profile__phone__icontains=texto_busqueda)
        )

    if filtro_rol:
        usuarios = usuarios.filter(role=filtro_rol)

    if filtro_estado == 'active':
        usuarios = usuarios.filter(is_active=True)
    elif filtro_estado == 'inactive':
        usuarios = usuarios.filter(is_active=False)

    context = {
        'users': usuarios,
        'search_query': texto_busqueda,
        'role_filter': filtro_rol,
        'status_filter': filtro_estado,
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'inactive_users': User.objects.filter(is_active=False).count(),
        'professional_users': User.objects.filter(role=User.Role.PROFESSIONAL).count(),
        'admin_users': User.objects.filter(role=User.Role.ADMIN).count(),
        'services': Service.objects.select_related('professional', 'professional__profile', 'category').all().order_by('-created_at')[:12],
        'categories': Category.objects.all(),
        'listing_types': ListingType.objects.all(),
        'total_reports': ReviewReport.objects.count(),
        'pending_reports': ReviewReport.objects.filter(is_resolved=False).count(),
        'total_service_reports': ServiceReport.objects.count(),
        'pending_service_reports': ServiceReport.objects.filter(is_resolved=False).count(),
    }
    return render(request, 'users/admin_dashboard.html', context)


@login_required
def admin_user_edit(request, pk):
    if not can_access_admin_panel(request.user):
        messages.error(request, 'No tienes permisos para acceder al panel de administración.')
        return redirect('services:service_list')

    usuario_objetivo = get_object_or_404(User, pk=pk)
    perfil_objetivo, _ = Profile.objects.get_or_create(user=usuario_objetivo)

    if request.method == 'POST':
        formulario_usuario = AdminUserForm(request.POST, instance=usuario_objetivo)
        formulario_perfil = ProfileForm(request.POST, request.FILES, instance=perfil_objetivo)
        if formulario_usuario.is_valid() and formulario_perfil.is_valid():
            formulario_usuario.save()
            formulario_perfil.save()
            messages.success(request, 'Usuario actualizado correctamente.')
            return redirect('users:admin_dashboard')
    else:
        formulario_usuario = AdminUserForm(instance=usuario_objetivo)
        formulario_perfil = ProfileForm(instance=perfil_objetivo)

    return render(
        request,
        'users/admin_user_form.html',
        {
            'user_form': formulario_usuario,
            'profile_form': formulario_perfil,
            'target_user': usuario_objetivo,
        },
    )


@login_required
@require_POST
def admin_user_toggle(request, pk):
    if not can_access_admin_panel(request.user):
        messages.error(request, 'No tienes permisos para acceder al panel de administración.')
        return redirect('services:service_list')

    usuario_objetivo = get_object_or_404(User, pk=pk)
    if usuario_objetivo == request.user:
        messages.error(request, 'No puedes deshabilitarte a ti mismo desde el panel.')
        return redirect('users:admin_dashboard')

    usuario_objetivo.is_active = not usuario_objetivo.is_active
    usuario_objetivo.save(update_fields=['is_active'])
    messages.success(request, 'Estado del usuario actualizado.')
    return redirect('users:admin_dashboard')


@login_required
@require_POST
def admin_user_delete(request, pk):
    if not can_access_admin_panel(request.user):
        messages.error(request, 'No tienes permisos para acceder al panel de administración.')
        return redirect('services:service_list')

    usuario_objetivo = get_object_or_404(User, pk=pk)
    if usuario_objetivo == request.user:
        messages.error(request, 'No puedes borrarte a ti mismo desde el panel.')
        return redirect('users:admin_dashboard')

    usuario_objetivo.delete()
    messages.success(request, 'Usuario eliminado correctamente.')
    return redirect('users:admin_dashboard')


@login_required
@require_POST
def admin_service_delete(request, pk):
    if not can_access_admin_panel(request.user):
        messages.error(request, 'No tienes permisos para esta acción.')
        return redirect('services:service_list')

    service = get_object_or_404(Service, pk=pk)
    service.delete()
    messages.success(request, 'Anuncio eliminado correctamente.')
    return redirect('home')


@login_required
@require_POST
def admin_review_delete(request, pk):
    if not can_access_admin_panel(request.user):
        messages.error(request, 'No tienes permisos para esta acción.')
        return redirect('services:service_list')

    review = get_object_or_404(Review, pk=pk)
    service_pk = review.service.pk
    review.delete()
    messages.success(request, 'Reseña eliminada correctamente.')
    next_url = request.META.get('HTTP_REFERER')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return HttpResponseRedirect(next_url)
    return redirect('services:service_detail', pk=service_pk)


@login_required
@require_POST
def admin_review_comment_clear(request, pk):
    if not can_access_admin_panel(request.user):
        messages.error(request, 'No tienes permisos para esta acción.')
        return redirect('services:service_list')

    resena = get_object_or_404(Review, pk=pk)
    servicio_id = resena.service.pk
    resena.delete()
    messages.success(request, 'Reseña eliminada correctamente.')
    return redirect('services:service_detail', pk=servicio_id)


@login_required
@require_POST
def admin_category_create(request):
    if not can_access_admin_panel(request.user):
        messages.error(request, 'No tienes permisos para esta acción.')
        return redirect('services:service_list')

    name = (request.POST.get('name') or '').strip()
    description = (request.POST.get('description') or '').strip()
    if not name:
        messages.error(request, 'Debes indicar un nombre para la categoría.')
        return redirect('users:admin_dashboard')

    slug = slugify(name)
    base_slug = slug or 'categoria'
    counter = 1
    while Category.objects.filter(slug=slug).exists() or not slug:
        slug = f'{base_slug}-{counter}'
        counter += 1

    Category.objects.create(name=name, slug=slug, description=description)
    messages.success(request, 'Categoría creada correctamente.')
    return redirect('users:admin_dashboard')


@login_required
@require_POST
def admin_category_delete(request, pk):
    if not can_access_admin_panel(request.user):
        messages.error(request, 'No tienes permisos para esta acción.')
        return redirect('services:service_list')

    category = get_object_or_404(Category, pk=pk)
    try:
        category.delete()
        messages.success(request, 'Categoría eliminada correctamente.')
    except ProtectedError:
        messages.error(request, 'No se puede eliminar la categoría porque tiene anuncios asociados.')
    return redirect('users:admin_dashboard')


@login_required
@require_POST
def admin_listing_type_create(request):
    if not can_access_admin_panel(request.user):
        messages.error(request, 'No tienes permisos para esta acción.')
        return redirect('services:service_list')

    name = (request.POST.get('name') or '').strip()
    if not name:
        messages.error(request, 'Debes indicar un nombre para el tipo de anuncio.')
        return redirect('users:admin_dashboard')

    slug = slugify(name)
    base_slug = slug or 'tipo'
    counter = 1
    while ListingType.objects.filter(slug=slug).exists() or not slug:
        slug = f'{base_slug}-{counter}'
        counter += 1

    ListingType.objects.create(name=name, slug=slug)
    messages.success(request, 'Tipo de anuncio creado correctamente.')
    return redirect('users:admin_dashboard')


@login_required
@require_POST
def admin_listing_type_delete(request, pk):
    if not can_access_admin_panel(request.user):
        messages.error(request, 'No tienes permisos para esta acción.')
        return redirect('services:service_list')

    listing_type = get_object_or_404(ListingType, pk=pk)
    if Service.objects.filter(listing_type=listing_type.name).exists():
        messages.error(request, 'No se puede eliminar el tipo porque hay anuncios usándolo.')
        return redirect('users:admin_dashboard')

    listing_type.delete()
    messages.success(request, 'Tipo de anuncio eliminado correctamente.')
    return redirect('users:admin_dashboard')


@login_required
def admin_review_reports(request):
    if not can_access_admin_panel(request.user):
        messages.error(request, 'No tienes permisos para acceder al panel de administración.')
        return redirect('services:service_list')

    reports = ReviewReport.objects.select_related('review', 'reporter', 'review__reviewer', 'review__service').order_by('-created_at')
    search_query = (request.GET.get('q') or '').strip()
    status_filter = (request.GET.get('status') or '').strip()
    reason_filter = (request.GET.get('reason') or '').strip()

    if search_query:
        reports = reports.filter(
            Q(review__title__icontains=search_query)
            | Q(review__comment__icontains=search_query)
            | Q(reporter__username__icontains=search_query)
            | Q(reviewer__username__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    if status_filter == 'resolved':
        reports = reports.filter(is_resolved=True)
    elif status_filter == 'pending':
        reports = reports.filter(is_resolved=False)

    if reason_filter:
        reports = reports.filter(reason=reason_filter)

    context = {
        'reports': reports,
        'search_query': search_query,
        'status_filter': status_filter,
        'reason_filter': reason_filter,
        'pending_reports': ReviewReport.objects.filter(is_resolved=False).count(),
        'resolved_reports': ReviewReport.objects.filter(is_resolved=True).count(),
        'total_reports': ReviewReport.objects.count(),
        'reason_choices': ReviewReport.REASON_CHOICES,
    }
    return render(request, 'users/admin_review_reports.html', context)


@login_required
def admin_service_reports(request):
    if not can_access_admin_panel(request.user):
        messages.error(request, 'No tienes permisos para acceder al panel de administración.')
        return redirect('services:service_list')

    reports = ServiceReport.objects.select_related('service', 'reporter', 'service__professional').order_by('-created_at')
    search_query = (request.GET.get('q') or '').strip()
    status_filter = (request.GET.get('status') or '').strip()
    reason_filter = (request.GET.get('reason') or '').strip()

    if search_query:
        reports = reports.filter(
            Q(service__title__icontains=search_query)
            | Q(service__description__icontains=search_query)
            | Q(reporter__username__icontains=search_query)
            | Q(service__professional__username__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    if status_filter == 'resolved':
        reports = reports.filter(is_resolved=True)
    elif status_filter == 'pending':
        reports = reports.filter(is_resolved=False)

    if reason_filter:
        reports = reports.filter(reason=reason_filter)

    context = {
        'reports': reports,
        'search_query': search_query,
        'status_filter': status_filter,
        'reason_filter': reason_filter,
        'pending_reports': ServiceReport.objects.filter(is_resolved=False).count(),
        'resolved_reports': ServiceReport.objects.filter(is_resolved=True).count(),
        'total_reports': ServiceReport.objects.count(),
        'reason_choices': ServiceReport.REASON_CHOICES,
    }
    return render(request, 'users/admin_service_reports.html', context)


@login_required
@require_POST
def admin_service_report_resolve(request, pk):
    if not can_access_admin_panel(request.user):
        messages.error(request, 'No tienes permisos para esta acción.')
        return redirect('services:service_list')

    report = get_object_or_404(ServiceReport, pk=pk)
    report.is_resolved = True
    report.resolved_at = timezone.now()
    report.save()
    messages.success(request, 'Reporte marcado como resuelto.')
    return redirect('users:admin_service_reports')


@login_required
@require_POST
def admin_service_report_delete_service(request, pk):
    if not can_access_admin_panel(request.user):
        messages.error(request, 'No tienes permisos para esta acción.')
        return redirect('services:service_list')

    report = get_object_or_404(ServiceReport, pk=pk)
    service = report.service
    service.is_active = False
    service.save()
    report.is_resolved = True
    report.resolved_at = timezone.now()
    report.save()
    messages.success(request, 'Anuncio eliminado y reporte marcado como resuelto.')
    return redirect('users:admin_service_reports')


@login_required
@require_POST
def admin_report_resolve(request, pk):
    if not can_access_admin_panel(request.user):
        messages.error(request, 'No tienes permisos para esta acción.')
        return redirect('services:service_list')

    report = get_object_or_404(ReviewReport, pk=pk)
    report.is_resolved = True
    report.resolved_at = timezone.now()
    report.save()
    messages.success(request, 'Reporte marcado como resuelto.')
    return redirect('users:admin_review_reports')


@login_required
@require_POST
def admin_report_delete_review(request, pk):
    if not can_access_admin_panel(request.user):
        messages.error(request, 'No tienes permisos para esta acción.')
        return redirect('services:service_list')

    report = get_object_or_404(ReviewReport, pk=pk)
    review = report.review
    review.is_deleted = True
    review.save()
    report.is_resolved = True
    report.resolved_at = timezone.now()
    report.save()
    messages.success(request, 'Reseña eliminada y reporte marcado como resuelto.')
    return redirect('users:admin_review_reports')


def generate_temporary_password(length=12):
    """Generate a secure temporary password."""
    characters = string.ascii_letters + string.digits + '!@#$%'
    return ''.join(secrets.choice(characters) for _ in range(length))


@login_required
@require_POST
def admin_user_reset_password(request, pk):
    if not can_access_admin_panel(request.user):
        messages.error(request, 'No tienes permisos para esta acción.')
        return redirect('services:service_list')

    usuario_objetivo = get_object_or_404(User, pk=pk)
    if usuario_objetivo == request.user:
        messages.error(request, 'No puedes restablecer tu propia contraseña desde aquí.')
        return redirect('users:admin_dashboard')

    # Generate temporary password
    contrasena_temporal = generate_temporary_password()
    usuario_objetivo.set_password(contrasena_temporal)
    usuario_objetivo.must_change_password = True
    usuario_objetivo.save(update_fields=['password', 'must_change_password'])

    # Store in session for display on confirmation page
    request.session[f'reset_password_{pk}'] = contrasena_temporal
    return redirect('users:admin_user_reset_password_confirm', pk=pk)


@login_required
def admin_user_reset_password_confirm(request, pk):
    if not can_access_admin_panel(request.user):
        messages.error(request, 'No tienes permisos para esta acción.')
        return redirect('services:service_list')

    usuario_objetivo = get_object_or_404(User, pk=pk)
    contrasena_temporal = request.session.pop(f'reset_password_{pk}', None)

    if not contrasena_temporal:
        messages.error(request, 'No se encontró una contraseña temporal. Intenta nuevamente.')
        return redirect('users:admin_dashboard')

    return render(
        request,
        'users/admin_reset_password_confirm.html',
        {
            'target_user': usuario_objetivo,
            'temp_password': contrasena_temporal,
        },
    )

