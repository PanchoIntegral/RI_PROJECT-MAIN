from django.contrib import admin
from django.urls import path, include

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from django.conf import settings
from django.conf.urls.static import static

from ri_project.views import home

schema_view = get_schema_view(
    openapi.Info(
        title="API de RI Compras",
        default_version='v1.13.20',
        description="Documentación Oficial de la API de RI Compras",
        terms_of_service="no avaible",
        contact=openapi.Contact(email="cerberusprogrammer@gmail.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('api/', include('ri_compras.urls')),
    path('api/rh/', include('ri_rh.urls')),  # Incluye las URLs de ri_rh
    path('api/produccion/', include('ri_produccion.urls')),
    path('api/doc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Agrega estas líneas al final del archivo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
