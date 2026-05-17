from django import forms

from .models import ServiceRequest


class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = ('desired_date', 'message')
        labels = {
            'desired_date': 'Fecha deseada',
            'message': 'Mensaje para el profesional',
        }
        widgets = {
            'desired_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class ServiceRequestCancelForm(forms.Form):
    cancellation_reason = forms.CharField(
        required=False,
        label='Motivo de cancelación',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
    )
