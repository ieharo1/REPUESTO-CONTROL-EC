from django import forms
from .models import Marca, Modelo, Categoria, Repuesto


class MarcaForm(forms.ModelForm):
    class Meta:
        model = Marca
        fields = ["nombre", "pais", "activa"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "pais": forms.TextInput(attrs={"class": "form-control"}),
            "activa": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ModeloForm(forms.ModelForm):
    class Meta:
        model = Modelo
        fields = ["nombre", "marca", "anio_inicio", "anio_fin"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "marca": forms.Select(attrs={"class": "form-select"}),
            "anio_inicio": forms.NumberInput(
                attrs={"class": "form-control", "min": "1900", "max": "2030"}
            ),
            "anio_fin": forms.NumberInput(
                attrs={"class": "form-control", "min": "1900", "max": "2030"}
            ),
        }


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "descripcion"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class RepuestoForm(forms.ModelForm):
    class Meta:
        model = Repuesto
        fields = [
            "codigo",
            "nombre",
            "descripcion",
            "marca",
            "modelo",
            "categoria",
            "precio_compra",
            "precio_venta",
            "stock_actual",
            "stock_minimo",
            "ubicacion",
            "imagen",
            "activo",
        ]
        widgets = {
            "codigo": forms.TextInput(attrs={"class": "form-control"}),
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "marca": forms.Select(attrs={"class": "form-select"}),
            "modelo": forms.Select(attrs={"class": "form-select"}),
            "categoria": forms.Select(attrs={"class": "form-select"}),
            "precio_compra": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "precio_venta": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "stock_actual": forms.NumberInput(
                attrs={"class": "form-control", "min": "0"}
            ),
            "stock_minimo": forms.NumberInput(
                attrs={"class": "form-control", "min": "0"}
            ),
            "ubicacion": forms.Select(attrs={"class": "form-select"}),
            "imagen": forms.FileInput(attrs={"class": "form-control"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
