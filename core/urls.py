from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("calculate_route/", views.calculate_route, name="calculate_route"),
    path("add/", views.add_incident, name="add_incident"),
    path("show/", views.incident_list, name="incident_list"),
]
