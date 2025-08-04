from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AsignacionProcesoViewSet, EspesorViewSet, EstanteProduccionViewSet, EtapaCalidadViewSet, FlujoCalidadViewSet, HorarioProduccionViewSet, InventarioMaterialViewSet, MaquinaProcesoViewSet, MaquinaViewSet, MaterialViewSet, NesteoViewSet, OrdenProduccionViewSet, PersonalMaquinaViewSet, PiezaNesteoViewSet, PiezaViewSet, PresentacionMaterialViewSet, ProcesoViewSet, ProveedorTratamientoViewSet, RackProduccionViewSet, ScrapCalidadViewSet, AsignacionTratamientoCalidadViewSet, TratamientoCalidadViewSet, UbicacionPiezaViewSet

# Creamos el router y registramos los ViewSets
router = DefaultRouter()
router.register(r'espesores', EspesorViewSet, basename='espesor')
router.register(r'presentacion', PresentacionMaterialViewSet, basename='presentacion')
router.register(r'materiales', MaterialViewSet, basename='material')
router.register(r'ordenes-produccion', OrdenProduccionViewSet, basename='orden-produccion')
router.register(r'piezas', PiezaViewSet, basename='pieza')
router.register(r'procesos', ProcesoViewSet, basename='proceso')
router.register(r'maquinas', MaquinaViewSet, basename='maquina')
router.register(r'maquina-proceso', MaquinaProcesoViewSet, basename='maquina-proceso')
router.register(r'asignaciones-procesos', AsignacionProcesoViewSet, basename='asignacion-proceso')
router.register(r'inventario-materiales', InventarioMaterialViewSet, basename='inventario-material')
router.register(r'nesteos', NesteoViewSet, basename='nesteo')
router.register(r'pieza-nesteo', PiezaNesteoViewSet, basename='pieza-nesteo')
router.register(r'etapas-calidad', EtapaCalidadViewSet, basename='etapa-calidad')
router.register(r'flujos-calidad', FlujoCalidadViewSet, basename='flujo-calidad')
router.register(r'scrap-calidad', ScrapCalidadViewSet, basename='scrap-calidad')
router.register(r'proveedores-tratamientos', ProveedorTratamientoViewSet, basename='proveedor-tratamiento')
router.register(r'tratamiento-calidad', TratamientoCalidadViewSet, basename='tratamiento-calidad')
router.register(r'asignacion-tratamientos-calidad', AsignacionTratamientoCalidadViewSet, basename='asignacion-tratamiento-calidad')
router.register(r'racks-produccion', RackProduccionViewSet, basename='rack-produccion')
router.register(r'estantes-produccion', EstanteProduccionViewSet, basename='estante-produccion')
router.register(r'ubicacion-piezas', UbicacionPiezaViewSet, basename='ubicacion-pieza')
router.register(r'personal-maquina', PersonalMaquinaViewSet, basename='personal-maquina')
router.register(r'horarios-produccion', HorarioProduccionViewSet, basename='horario-produccion')

# Definimos las URLs de la aplicación
urlpatterns = [
    path('', include(router.urls)),
]
