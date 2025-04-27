from django import forms

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
        # self.fields["latitude"].label = "Latitud"
        # self.fields["longitude"].label = "Longitud"
        self.fields["incident_date"].label = "Fecha del incidente"
        self.fields["incident_time"].label = "Hora del incidente"
        self.fields["description"].label = "Descripción"
        # self.fields["report_date"].label = "Fecha del reporte"
        # self.fields["report_time"].label = "Hora del reporte"
