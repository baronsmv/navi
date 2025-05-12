from django import forms
from django.contrib.gis.geos import Point

from core.models import Incident


class IncidentForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = [
            "type",
            "severity",
            "latitude",
            "longitude",
            "incident_date",
            "incident_time",
            "description",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4, "cols": 50}),
            "latitude": forms.HiddenInput(),
            "longitude": forms.HiddenInput(),
            "incident_date": forms.DateInput(attrs={"type": "date"}),
            "incident_time": forms.TimeInput(attrs={"type": "time"}),
            "report_date": forms.HiddenInput(),
            "report_time": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["type"].label = "Tipo de incidente"
        self.fields["severity"].label = "Gravedad"
        self.fields["incident_date"].label = "Fecha del incidente"
        self.fields["incident_time"].label = "Hora del incidente"
        self.fields["description"].label = "Descripción"

    def save(self, commit=True):
        latitude = self.cleaned_data.get("latitude")
        longitude = self.cleaned_data.get("longitude")

        if latitude is not None and longitude is not None:
            self.instance.location = Point(longitude, latitude, srid=4326)

        return super().save(commit)
