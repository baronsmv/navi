# core/models.py

from django.contrib.gis.db import models
from django.contrib.gis.geos import Point


class Incident(models.Model):
    INCIDENT_TYPE = [
        ("assault", "Asalto"),
        ("crash", "Choque"),
        ("homicide", "Homicidio"),
        ("robbery", "Robo"),
        ("other", "Otro"),
    ]

    INCIDENT_STATUS = [
        ("in_progress", "En Proceso"),
        ("resolved", "Resuelto"),
        ("unresolved", "No Resuelto"),
    ]

    type = models.CharField(max_length=20, choices=INCIDENT_TYPE)
    description = models.TextField(null=True, blank=True)

    report_datetime = models.DateTimeField(auto_now_add=True)
    report_time = models.TimeField(auto_now_add=True)

    incident_datetime = models.DateTimeField()
    incident_time = models.TimeField()

    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)

    location = models.PointField(geography=True, srid=4326, default=Point(0.0, 0.0))

    severity = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])  # 1 to 5

    status = models.CharField(
        max_length=20, choices=INCIDENT_STATUS, default="unresolved"
    )

    def __str__(self):
        return f"{self.type} - {self.incident_datetime}"

    class Meta:
        db_table = "incident"
        indexes = [
            models.Index(fields=["latitude", "longitude"]),
            models.Index(fields=["incident_datetime"]),
            models.Index(fields=["severity"]),
        ]
