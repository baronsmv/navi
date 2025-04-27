from django import forms

from .models import Incident


class IncidenteForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = [
            "type",
            "severity",
            "latitude",
            "longitude",
            "incident_datetime",
            "incident_time",
            "description",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4, "cols": 50}),
            "latitude": forms.HiddenInput(),
            "longitude": forms.HiddenInput(),
            "incident_datetime": forms.DateInput(attrs={"type": "date"}),
            "incident_time": forms.TimeInput(attrs={"type": "time"}),
            "report_datetime": forms.HiddenInput(),
            "report_time": forms.HiddenInput(),
        }

    def clean_latitude(self):
        latitude = self.cleaned_data.get("latitude")
        if not latitude:
            raise forms.ValidationError("La latitud es obligatoria.")
        return latitude

    def clean_longitude(self):
        longitude = self.cleaned_data.get("longitude")
        if not longitude:
            raise forms.ValidationError("La longitud es obligatoria.")
        return longitude
