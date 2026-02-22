from django import forms
from .models import Cliente, Venta, DetalleVenta


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nombre", "cedula", "telefono", "email", "direccion"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "cedula": forms.TextInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "direccion": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ["cliente", "metodo_pago", "notas"]
        widgets = {
            "cliente": forms.Select(attrs={"class": "form-select"}),
            "metodo_pago": forms.Select(attrs={"class": "form-select"}),
            "notas": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class DetalleVentaForm(forms.ModelForm):
    class Meta:
        model = DetalleVenta
        fields = ["repuesto", "cantidad", "precio_unitario"]
        widgets = {
            "repuesto": forms.Select(attrs={"class": "form-select"}),
            "cantidad": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "precio_unitario": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
        }
