from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from services.models import Service

from .forms import ReviewForm, ReviewReportForm
from .models import Review, ReviewReport


@login_required
def review_create(request, pk):
	servicio = get_object_or_404(Service, pk=pk, is_active=True)
	
	# Verificar que el usuario no intente valorar su propio servicio
	if servicio.professional == request.user:
		messages.warning(request, 'No puedes valorar tu propio servicio.')
		return redirect('services:service_detail', pk=servicio.pk)

	# Obtener reseña existente (para editar)
	resena = Review.objects.filter(service=servicio, reviewer=request.user).first()

	if request.method == 'POST':
		formulario = ReviewForm(request.POST, instance=resena)
		if formulario.is_valid():
			resena_guardada = formulario.save(commit=False)
			resena_guardada.service = servicio
			resena_guardada.reviewer = request.user
			resena_guardada.save()
			messages.success(request, 'Valoración guardada correctamente.')
			return redirect('services:service_detail', pk=servicio.pk)
		else:
			# Si el formulario no es válido, volver a renderizar con errores
			messages.error(request, 'Por favor corrige los errores del formulario.')
	else:
		formulario = ReviewForm(instance=resena) if resena else ReviewForm()

	context = {
		'form': formulario,
		'service': servicio,
		'review': resena,
	}
	return render(request, 'reviews/review_form.html', context)


@login_required
def report_review(request, review_id):
	resena = get_object_or_404(Review, pk=review_id)
	
	# Verificar que el usuario no sea el autor de la reseña
	if resena.reviewer == request.user:
		messages.error(request, 'No puedes reportar tu propia reseña.')
		return redirect('services:service_detail', pk=resena.service.pk)

	if request.method == 'POST':
		formulario = ReviewReportForm(request.POST)
		if formulario.is_valid():
			reporte = formulario.save(commit=False)
			reporte.review = resena
			reporte.reporter = request.user
			reporte.save()
			messages.success(request, 'Reporte enviado correctamente. Gracias por ayudarnos a mantener la comunidad segura.')
			return redirect('services:service_detail', pk=resena.service.pk)
	else:
		formulario = ReviewReportForm()

	context = {
		'form': formulario,
		'review': resena,
	}
	return render(request, 'reviews/report_form.html', context)
