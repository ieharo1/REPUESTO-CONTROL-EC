from django.contrib import admin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ["username", "first_name", "last_name", "email", "rol", "is_active"]
    list_filter = ["rol", "is_active", "is_staff"]
    search_fields = ["username", "first_name", "last_name", "email"]
    ordering = ["-date_joined"]
