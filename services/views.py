from functools import wraps
from urllib.error import URLError

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from users.models import User

from .forms import ServiceFilterForm, ServiceForm
from .models import Category, Service, ServiceImage
from .geoapify import (
    resolve_map_location,
    search_locations,
    search_municipalities,
    reverse_location,
)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from .forms import ServiceReportForm
from .models import Service, ServiceImage, ServiceReport
from django.utils import timezone


def professional_required(view_function):
    @wraps(view_function)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.role != User.Role.PROFESSIONAL:
            messages.error(request, 'Debes tener una cuenta profesional para crear o editar servicios.')
            return redirect('users:profile')
        return view_function(request, *args, **kwargs)

    return wrapper


def service_list(request):
    services = Service.objects.select_related('category', 'professional', 'professional__profile').filter(is_active=True)
    filter_form = ServiceFilterForm(request.GET or None)

    if filter_form.is_valid():
        category = filter_form.cleaned_data.get('category')
        city = filter_form.cleaned_data.get('city')

        if category:
            services = services.filter(category=category)
        if city:
            services = services.filter(city__icontains=city)

    categories = Category.objects.all()
    return render(
        request,
        'services/service_list.html',
        {
            'services': services,
            'filter_form': filter_form,
            'categories': categories,
        },
    )


@login_required
def my_services(request):
    if not request.user.es_profesional:
        messages.error(request, 'Debes tener una cuenta profesional para ver tus anuncios.')
        return redirect('services:service_list')
    
    services = Service.objects.select_related('category', 'professional', 'professional__profile').filter(professional=request.user)
    filter_form = ServiceFilterForm(request.GET or None)

    if filter_form.is_valid():
        category = filter_form.cleaned_data.get('category')
        city = filter_form.cleaned_data.get('city')

        if category:
            services = services.filter(category=category)
        if city:
            services = services.filter(city__icontains=city)

    categories = Category.objects.all()
    return render(
        request,
        'services/service_list_own.html',
        {
            'services': services,
            'filter_form': filter_form,
            'categories': categories,
        },
    )


def service_detail(request, pk):
    service = get_object_or_404(Service.objects.select_related('category', 'professional', 'professional__profile'), pk=pk, is_active=True)
    reviews = service.reviews.filter(is_deleted=False).select_related('reviewer')
    map_location = resolve_map_location(service)
    
    # Verificar si el usuario actual tiene una reseña de este servicio
    user_review = None
    if request.user.is_authenticated:
        from reviews.models import Review
        user_review = service.reviews.filter(reviewer=request.user).first()
    
    return render(
        request,
        'services/service_detail.html',
        {
            'service': service,
            'reviews': reviews,
            'map_location': map_location,
            'geoapify_api_key': settings.GEOAPIFY_API_KEY,
            'average_rating': service.average_rating,
            'review_count': service.review_count,
            'user_review': user_review,
        },
    )


@login_required
def report_service(request, pk):
    service = get_object_or_404(Service, pk=pk, is_active=True)

    if request.method == 'POST':
        form = ServiceReportForm(request.POST)
        if form.is_valid():
            reporte = form.save(commit=False)
            reporte.service = service
            reporte.reporter = request.user
            reporte.save()
            messages.success(request, 'Reporte del anuncio enviado correctamente. Gracias por ayudarnos.')
            return redirect('services:service_detail', pk=service.pk)
    else:
        form = ServiceReportForm()

    return render(request, 'services/report_form.html', {'form': form, 'service': service})


@require_GET
def location_search(request):
    query = (request.GET.get('q') or '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})

    try:
        results = search_municipalities(query, limit=7)
    except (URLError, ValueError, KeyError, TypeError):
        results = []

    return JsonResponse({'results': results})


@require_GET
def location_reverse(request):
    """Reverse geocode latitude/longitude to a municipality (Spain).

    Returns a single result or empty list.
    """
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (TypeError, ValueError):
        return JsonResponse({'result': None})

    try:
        res = reverse_location(lat_f, lon_f)
    except Exception:
        res = None

    return JsonResponse({'result': res})


@professional_required
def service_create(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES)
        if form.is_valid():
            service = form.save(commit=False)
            service.professional = request.user
            service.save()
            
            # Handle multiple images
            images = request.FILES.getlist('multiple_images')
            for idx, image_file in enumerate(images):
                ServiceImage.objects.create(
                    service=service,
                    image=image_file,
                    order=idx
                )
            
            messages.success(request, 'Servicio creado correctamente.')
            return redirect('services:service_detail', pk=service.pk)
    else:
        form = ServiceForm()
    return render(request, 'services/service_form.html', {'form': form, 'title': 'Crear anuncio'})


@login_required
def service_edit(request, pk):
    service = get_object_or_404(Service, pk=pk, professional=request.user)
    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES, instance=service)
        if form.is_valid():
            service = form.save()
            
            # Handle multiple images - add new ones
            images = request.FILES.getlist('multiple_images')
            if images:
                # Get the current max order
                max_order = service.service_images.aggregate(models.Max('order'))['order__max'] or -1
                for idx, image_file in enumerate(images):
                    ServiceImage.objects.create(
                        service=service,
                        image=image_file,
                        order=max_order + idx + 1
                    )
            
            messages.success(request, 'Servicio actualizado correctamente.')
            return redirect('services:service_detail', pk=service.pk)
    else:
        form = ServiceForm(instance=service)
    return render(request, 'services/service_form.html', {'form': form, 'title': 'Editar anuncio', 'service': service})


@login_required
@require_http_methods(["GET", "POST"])
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk, professional=request.user)
    if request.method == 'GET':
        return render(request, 'services/service_confirm_delete.html', {'service': service})

    service.delete()
    messages.success(request, 'Anuncio eliminado correctamente.')
    return redirect('services:service_list')
