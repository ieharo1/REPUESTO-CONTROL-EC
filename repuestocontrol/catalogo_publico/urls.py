from django.urls import path
from . import views

app_name = "catalogo_publico"

urlpatterns = [
    path("", views.catalogo, name="catalogo"),
    path("repuesto/<int:pk>/", views.repuesto_detail, name="repuesto_detail"),
]
