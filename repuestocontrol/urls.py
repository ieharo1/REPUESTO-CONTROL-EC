from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("repuestocontrol.core.urls")),
    path("dashboard/", include("repuestocontrol.dashboard.urls")),
    path("inventario/", include("repuestocontrol.inventario.urls")),
    path("ventas/", include("repuestocontrol.ventas.urls")),
    path("catalogo/", include("repuestocontrol.catalogo_publico.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
