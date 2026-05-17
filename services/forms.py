from decimal import Decimal
from django import forms
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.forms.widgets import FileInput

from .models import Category, ListingType, Service, ServiceImage
from .geoapify import validate_location, search_municipalities
from .models import ServiceReport


class ServiceReportForm(forms.ModelForm):
    class Meta:
        model = ServiceReport
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


class MultipleFileInput(FileInput):
    """Custom widget for multiple file uploads"""
    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        # Don't pass 'multiple' to super().__init__() as Django validates against it
        # Instead, add it to the rendered widget attributes
        self.multiple = True
        super().__init__(attrs)
    
    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}
        attrs['multiple'] = True
        return super().render(name, value, attrs, renderer)


def _ensure_decimal_precision(value):
    """Convert a coordinate value to Decimal with 6 decimal places."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    # Convert float or string to Decimal, then quantize to 6 decimal places
    d = Decimal(str(value))
    return d.quantize(Decimal('0.000001'))


class ServiceForm(forms.ModelForm):
    listing_type = forms.ChoiceField(label='Tipo de anuncio', widget=forms.Select(attrs={'class': 'form-select'}))

    multiple_images = forms.FileField(
        label='Imágenes del anuncio',
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': '.png,.jpg,.jpeg,.webp',
        }),
        help_text='Puedes seleccionar una o varias imágenes. Formatos permitidos: PNG, JPG, JPEG y WEBP.'
    )

    cilindrada = forms.IntegerField(
        label='Cilindrada',
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 125'}),
    )
    kilometros = forms.IntegerField(
        label='Kilómetros',
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 35000'}),
    )
    year = forms.IntegerField(
        label='Año',
        required=False,
        min_value=1900,
        max_value=2100,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 2020'}),
    )

    city_query = forms.CharField(
        label='Localidad',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control location-input',
                'placeholder': 'Escribe una localidad de España',
                'autocomplete': 'off',
                'data-location-autocomplete': 'true',
                'data-location-url': '/servicios/localidades/',
            }
        ),
    )

    class Meta:
        model = Service
        fields = (
            'category',
            'listing_type',
            'title',
            'description',
            'cilindrada',
            'kilometros',
            'year',
            'city',
            'location_place_id',
            'price_from',
            'latitude',
            'longitude',
        )
        labels = {
            'category': 'Categoría',
            'title': 'Título',
            'description': 'Descripción',
            'cilindrada': 'Cilindrada',
            'kilometros': 'Kilómetros',
            'year': 'Año',
            'city': 'Localidad',
            'price_from': 'Precio desde',
            'latitude': 'Latitud',
            'longitude': 'Longitud',
        }
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'cilindrada': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 125'}),
            'kilometros': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 35000'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 2020'}),
            'city': forms.HiddenInput(),
            'location_place_id': forms.HiddenInput(),
            'price_from': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['city_query'].widget.attrs['data-location-url'] = reverse('services:location_search')
        listing_types = list(ListingType.objects.all())
        if not listing_types:
            ListingType.objects.get_or_create(name='Servicio', slug='servicio')
            ListingType.objects.get_or_create(name='Producto', slug='producto')
            listing_types = list(ListingType.objects.all())
        self.fields['listing_type'].choices = [(item.name, item.name) for item in listing_types]

        if self.instance and self.instance.pk:
            self.fields['listing_type'].initial = self.instance.listing_type
            self.fields['city_query'].initial = self.instance.city
            self.fields['city'].initial = self.instance.city
            self.fields['location_place_id'].initial = self.instance.location_place_id
            self.fields['latitude'].initial = self.instance.latitude
            self.fields['longitude'].initial = self.instance.longitude
            self.fields['cilindrada'].initial = self.instance.cilindrada
            self.fields['kilometros'].initial = self.instance.kilometros
            self.fields['year'].initial = self.instance.year

    def _is_vehicle_sale(self):
        selected_type = self.data.get('listing_type') if self.is_bound else self.initial.get('listing_type')
        if not selected_type and self.instance and self.instance.pk:
            selected_type = self.instance.listing_type
        # Normalize comparison: check if it matches "Vender vehiculo" (case-insensitive)
        return (selected_type or '').strip().lower() == 'vender vehiculo'

    def clean_cilindrada(self):
        value = self.cleaned_data.get('cilindrada')
        if self._is_vehicle_sale() and value in (None, ''):
            raise ValidationError('Este campo es obligatorio para vender-vehiculo.')
        return value

    def clean_kilometros(self):
        value = self.cleaned_data.get('kilometros')
        if self._is_vehicle_sale() and value in (None, ''):
            raise ValidationError('Este campo es obligatorio para vender-vehiculo.')
        return value

    def clean_year(self):
        value = self.cleaned_data.get('year')
        if self._is_vehicle_sale() and value in (None, ''):
            raise ValidationError('Este campo es obligatorio para vender-vehiculo.')
        return value

    def clean_multiple_images(self):
        images = self.files.getlist('multiple_images')
        if not images:
            return None

        allowed_extensions = ('.png', '.jpg', '.jpeg', '.webp')
        for image_file in images:
            filename = (image_file.name or '').lower()
            if not filename.endswith(allowed_extensions):
                raise ValidationError(f'La imagen {image_file.name} debe ser PNG, JPG, JPEG o WEBP.')
        return images

    def clean(self):
        cleaned_data = super().clean()
        city_query = (cleaned_data.get('city_query') or '').strip()
        city = (cleaned_data.get('city') or '').strip()
        place_id = (cleaned_data.get('location_place_id') or '').strip()
        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')

        if not city_query:
            raise ValidationError({'city_query': 'Debes indicar una localidad de España.'})

        selected_type = (cleaned_data.get('listing_type') or '').strip()
        if not ListingType.objects.filter(name=selected_type).exists():
            raise ValidationError({'listing_type': 'Selecciona un tipo de anuncio válido.'})

        # Normalize comparison: check if it matches "Vender vehiculo" (case-insensitive)
        if selected_type.lower() != 'vender vehiculo':
            cleaned_data['cilindrada'] = None
            cleaned_data['kilometros'] = None
            cleaned_data['year'] = None

        # Si es edición y la ciudad no cambió, mantén los datos
        if self.instance and self.instance.pk and self.instance.city == city_query and self.instance.latitude and self.instance.longitude:
            cleaned_data['city'] = self.instance.city
            cleaned_data['location_place_id'] = self.instance.location_place_id
            cleaned_data['latitude'] = self.instance.latitude
            cleaned_data['longitude'] = self.instance.longitude
            return cleaned_data

        # Si tiene place_id y coordenadas válidas, valida que sean correctos
        if place_id and latitude is not None and longitude is not None:
            match = validate_location(city_query, place_id)
            if not match:
                raise ValidationError({'city_query': 'La localidad seleccionada no existe o no es válida en España.'})
            cleaned_data['city'] = match['label']
            cleaned_data['location_place_id'] = match['place_id']
            cleaned_data['latitude'] = _ensure_decimal_precision(match['latitude'])
            cleaned_data['longitude'] = _ensure_decimal_precision(match['longitude'])
            return cleaned_data

        # Si no tiene place_id ni coordenadas válidas, intenta buscar automáticamente la localidad
        # Este es un fallback para compatibilidad; la forma correcta es seleccionar de la lista
        locations = search_municipalities(city_query, limit=1)
        if locations:
            location = locations[0]
            cleaned_data['city'] = location['label']
            cleaned_data['location_place_id'] = location['place_id']
            cleaned_data['latitude'] = _ensure_decimal_precision(location['latitude'])
            cleaned_data['longitude'] = _ensure_decimal_precision(location['longitude'])
            return cleaned_data

        # Si no encuentra nada, error claro pidiendo seleccionar de la lista
        raise ValidationError({'city_query': 'Por favor, selecciona una localidad de la lista de sugerencias. Debe ser una ciudad o pueblo válido de España.'})

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.city = self.cleaned_data['city']
        instance.listing_type = self.cleaned_data['listing_type']
        instance.cilindrada = self.cleaned_data.get('cilindrada')
        instance.kilometros = self.cleaned_data.get('kilometros')
        instance.year = self.cleaned_data.get('year')
        instance.location_place_id = self.cleaned_data['location_place_id']
        instance.latitude = self.cleaned_data['latitude']
        instance.longitude = self.cleaned_data['longitude']
        if commit:
            instance.save()
        return instance


class ServiceFilterForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label='Todas las categorías',
        widget=forms.Select(attrs={'class': 'form-select', 'data-autosubmit': 'true'}),
    )
    city = forms.CharField(required=False, label='Ciudad', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ciudad', 'data-autosubmit': 'true'}))
