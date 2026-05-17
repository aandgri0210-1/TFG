from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from services.models import Service

from .forms import ServiceRequestCancelForm, ServiceRequestForm
from .models import ServiceRequest


@login_required
def request_create(request, pk):
	servicio = get_object_or_404(Service, pk=pk, is_active=True)

	if servicio.professional == request.user:
		messages.warning(request, 'No puedes solicitar tu propio servicio.')
		return redirect('services:service_detail', pk=servicio.pk)

	if ServiceRequest.objects.filter(customer=request.user, service=servicio).exclude(status=ServiceRequest.Status.CANCELLED).exists():
		messages.info(request, 'Ya tienes una solicitud activa para este servicio.')
		return redirect('requests_app:request_history')

	if request.method == 'POST':
		formulario = ServiceRequestForm(request.POST)
		if formulario.is_valid():
			solicitud = formulario.save(commit=False)
			solicitud.customer = request.user
			solicitud.service = servicio
			solicitud.save()
			messages.success(request, 'Solicitud creada correctamente.')
			return redirect('requests_app:request_history')
	else:
		formulario = ServiceRequestForm()

	return render(request, 'requests_app/request_create.html', {'form': formulario, 'service': servicio})


@login_required
def request_history(request):
	requests_list = ServiceRequest.objects.select_related('service', 'service__professional').filter(customer=request.user)
	return render(request, 'requests_app/request_history.html', {'requests_list': requests_list})


@login_required
def request_cancel(request, pk):
	service_request = get_object_or_404(ServiceRequest, pk=pk, customer=request.user)

	if not service_request.can_cancel:
		messages.error(request, 'Esta solicitud no se puede cancelar en su estado actual.')
		return redirect('requests_app:request_history')

	if request.method == 'POST':
		form = ServiceRequestCancelForm(request.POST)
		if form.is_valid():
			service_request.status = ServiceRequest.Status.CANCELLED
			service_request.cancellation_reason = form.cleaned_data.get('cancellation_reason', '')
			service_request.save(update_fields=['status', 'cancellation_reason', 'updated_at'])
			messages.success(request, 'Solicitud cancelada correctamente.')
			return redirect('requests_app:request_history')
	else:
		form = ServiceRequestCancelForm()

	return render(request, 'requests_app/request_cancel.html', {'form': form, 'service_request': service_request})


@login_required
def provider_requests(request):
	provider_requests_list = ServiceRequest.objects.select_related('service', 'customer').filter(service__professional=request.user)
	return render(request, 'requests_app/provider_requests.html', {'provider_requests_list': provider_requests_list})


@login_required
def provider_request_update(request, pk, action):
	service_request = get_object_or_404(ServiceRequest, pk=pk, service__professional=request.user)
	valid_actions = {
		'accept': ServiceRequest.Status.ACCEPTED,
		'complete': ServiceRequest.Status.COMPLETED,
	}

	if action not in valid_actions:
		messages.error(request, 'Acción no válida.')
		return redirect('requests_app:provider_requests')

	if request.method != 'POST':
		return redirect('requests_app:provider_requests')

	if action == 'accept' and service_request.status != ServiceRequest.Status.PENDING:
		messages.error(request, 'Solo puedes aceptar solicitudes pendientes.')
		return redirect('requests_app:provider_requests')

	if action == 'complete' and service_request.status != ServiceRequest.Status.ACCEPTED:
		messages.error(request, 'Solo puedes completar solicitudes aceptadas.')
		return redirect('requests_app:provider_requests')

	service_request.status = valid_actions[action]
	service_request.save(update_fields=['status', 'updated_at'])
	messages.success(request, 'Estado de la solicitud actualizado.')
	return redirect('requests_app:provider_requests')
