# core/models.py

from django.contrib.gis.db import models
from django.contrib.gis.geos import Point


class Incidente(models.Model):
    TIPO_INCIDENTE = [
        ("asalto", "Asalto"),
        ("choque", "Choque"),
        ("homicidio", "Homicidio"),
        ("robo", "Robo"),
        ("otro", "Otro"),
    ]

    ESTADO_INCIDENTE = [
        ("en_proceso", "En Proceso"),
        ("resuelto", "Resuelto"),
        ("no_resuelto", "No Resuelto"),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_INCIDENTE)
    descripcion = models.TextField(null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    hora_registro = models.TimeField(auto_now_add=True)
    fecha_incidente = models.DateTimeField()
    hora_incidente = models.TimeField()
    latitud = models.FloatField(default=0.0)
    longitud = models.FloatField(default=0.0)
    location = models.PointField(geography=True, srid=4326, default=Point(0.0, 0.0))
    gravedad = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])  # 1 a 5
    estado = models.CharField(
        max_length=20, choices=ESTADO_INCIDENTE, default="no_resuelto"
    )
    zona_riesgo = models.ForeignKey(
        "ZonaRiesgo", null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return f"{self.tipo} - {self.fecha_incidente}"

    class Meta:
        db_table = "incidente"
        indexes = [
            models.Index(fields=["latitud", "longitud"]),
            models.Index(fields=["fecha_incidente"]),
            models.Index(fields=["gravedad"]),
        ]


class ZonaRiesgo(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(null=True, blank=True)
    poligono = (
        models.PolygonField()
    )  # Se usa un tipo de dato geográfico para definir zonas de riesgo

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = "zonariesgo"
