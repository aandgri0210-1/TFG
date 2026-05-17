from decimal import Decimal
from django import forms

from .models import Review, ReviewReport


class ReviewForm(forms.ModelForm):
    RATING_CHOICES = [
        (Decimal('1.0'), '1'),
        (Decimal('1.5'), '1.5'),
        (Decimal('2.0'), '2'),
        (Decimal('2.5'), '2.5'),
        (Decimal('3.0'), '3'),
        (Decimal('3.5'), '3.5'),
        (Decimal('4.0'), '4'),
        (Decimal('4.5'), '4.5'),
        (Decimal('5.0'), '5'),
    ]

    rating = forms.TypedChoiceField(
        coerce=Decimal,
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'rating-input'}),
        label='Puntuación',
        required=True,
        error_messages={'required': 'Debes seleccionar una puntuación.'}
    )

    class Meta:
        model = Review
        fields = ('title', 'rating', 'comment')
        labels = {
            'title': 'Título de la reseña',
            'rating': 'Puntuación',
            'comment': 'Texto de la reseña',
        }
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Resume tu experiencia en una frase',
                'maxlength': 120,
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Cuéntanos tu experiencia con este servicio...',
            }),
        }
        help_texts = {
            'comment': 'Escribe un texto con tu experiencia para que la reseña tenga contexto.',
        }


class ReviewReportForm(forms.ModelForm):
    class Meta:
        model = ReviewReport
        fields = ('reason', 'description')
        labels = {
            'reason': 'Motivo del reporte',
            'description': 'Descripción adicional (opcional)',
        }
        widgets = {
            'reason': forms.Select(attrs={
                'class': 'form-select',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Proporciona más detalles sobre tu reporte (opcional)...',
            }),
        }
        help_texts = {
            'reason': 'Selecciona el motivo principal de tu reporte.',
        }
