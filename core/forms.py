from django import forms

from .models import Incidente


class IncidenteForm(forms.ModelForm):
    class Meta:
        model = Incidente
        fields = [
            "tipo",
            "gravedad",
            "latitud",
            "longitud",
            "fecha_incidente",
            "hora_incidente",
            "descripcion",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4, "cols": 50}),
            "latitud": forms.HiddenInput(),
            "longitud": forms.HiddenInput(),
            "fecha_incidente": forms.DateInput(attrs={"type": "date"}),
            "hora_incidente": forms.TimeInput(attrs={"type": "time"}),
            "fecha_registro": forms.HiddenInput(),
            "hora_registro": forms.HiddenInput(),
        }

    # Validación adicional si lo necesitas
    def clean_latitud(self):
        latitud = self.cleaned_data.get("latitud")
        if not latitud:
            raise forms.ValidationError("La latitud es obligatoria.")
        return latitud

    def clean_longitud(self):
        longitud = self.cleaned_data.get("longitud")
        if not longitud:
            raise forms.ValidationError("La longitud es obligatoria.")
        return longitud
