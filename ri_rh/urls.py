from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ( 
    CatalogoDocumentoViewSet,
    DocumentoCargadoViewSet,
    DocumentoEmpleadoViewSet,
    EmpleadoViewSet,
    PracticanteResidenteViewSet,
    PuestoViewSet,
    UniversidadViewSet, 
    DocumentoRequisitosViewSet,
)


router = DefaultRouter(
)


router.register(r'puesto', PuestoViewSet)
router.register(r'empleados', EmpleadoViewSet)
router.register(r'documentosEvento', DocumentoEmpleadoViewSet)
router.register(r'Universidad', UniversidadViewSet)
router.register(r'PracticantesResidentes', PracticanteResidenteViewSet)
router.register(r'catalogo-documentos', CatalogoDocumentoViewSet)
router.register(r'documentos-cargados', DocumentoCargadoViewSet)
router.register(r'documentacion-requisitos', DocumentoRequisitosViewSet)


urlpatterns = [
    path('', include(router.urls)),
]