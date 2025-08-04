# Django Imports
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware, is_naive, now
from django.db.models import (
    Count, Min, Max, Sum, F, Q, Exists, OuterRef, 
    DurationField, ExpressionWrapper, fields
)
from django.db.models.functions import Coalesce
from django.utils.dateparse import parse_date

# Django REST Framework Imports
from rest_framework import viewsets, filters, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from django.db import transaction

# Third-party Packages
from django_filters.rest_framework import DjangoFilterBackend

# Local Imports (Models & Serializers)
from ri_compras.models import Usuarios
from ri_compras.serializer import (
    UsuarioDepartamentoSerializer, 
    UsuariosSerializer, 
    UsuariosVerySimpleSerializer
)
from ri_produccion import models


import logging
from django.views.decorators.cache import cache_control

# cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache

from ri_produccion.serializers import AsignacionProcesoSerializer, EspesorSerializer, EstanteProduccionSerializer, EtapaCalidadSerializer, FlujoCalidadSerializer, HorarioProduccionSerializer, InventarioMaterialSerializer, MaquinaProcesoSerializer, MaquinaSerializer, MaterialSerializer, NesteoSerializer, OrdenProduccionSerializer, PersonalMaquinaSerializer, PiezaNesteoSerializer, PiezaSerializer, PresentacionMaterialSerializer, ProcesoSerializer, ProveedorTratamientoSerializer, RackProduccionSerializer, ScrapCalidadSerializer, AsignacionTratamientoCalidadSerializer, TratamientoCalidadSerializer, UbicacionPiezaSerializer
logger = logging.getLogger(__name__)


## Views de los modelos 


## ViewSet para gestionar espesores
class EspesorViewSet(viewsets.ModelViewSet):
    queryset = models.Espesor.objects.all()
    serializer_class = EspesorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["nombre_comercial"]
    search_fields = ["nombre_comercial"]
    ordering_fields = ["valor_pulgadas", "nombre_comercial"]
    ordering = ["valor_pulgadas"]

    @method_decorator(cache_control(no_cache=True, no_store=True, must_revalidate=True))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save()
        self.clear_cache() 

    def perform_update(self, serializer):
        serializer.save()
        self.clear_cache()

    def perform_destroy(self, instance):
        instance.delete()
        self.clear_cache()

    @action(detail=False, methods=["get"], url_path="contar")
    def contar_espesores(self, request):
        total = self.get_queryset().count()
        return Response({"total_espesores": total})

    @action(detail=False, methods=["get"], url_path="nombres")
    def listar_nombres_comerciales(self, request):
        nombres = self.get_queryset().values_list("nombre_comercial", flat=True).distinct()
        return Response({"nombres_comerciales": list(nombres)})

    @action(detail=False, methods=["post"], url_path="clear-cache")
    def clear_espesores_cache(self, request):
        self.clear_cache()
        return Response({"mensaje": ":white_check_mark: Caché limpiado correctamente."})

    def clear_cache(self):
        keys = cache.keys("*espesores*")
        for key in keys:
            cache.delete(key)
        cache.delete_many([
            "espesores_list", 
            "espesores_contar",
            "espesores_nombres",
        ])

class PresentacionMaterialViewSet(viewsets.ModelViewSet):
    queryset = models.PresentacionMaterial.objects.select_related("espesor").all()
    serializer_class = PresentacionMaterialSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    filterset_fields = [
        "espesor", 
        "requiere_placa_lamina", 
        "largo",  
        "ancho", 
        "diametro",
    ]
    search_fields = ["nombre_comercial",]
    ordering_fields = ["nombre_comercial", "largo", "ancho", "diametro"]
    ordering = ["nombre_comercial"]

    def list(self, request, *args, **kwargs):
        requiere_placa = request.query_params.get('requiere_placa_lamina')
        if requiere_placa is not None:

            self.queryset = self.queryset.filter(requiere_placa_lamina=requiere_placa)
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save()
        self.clear_cache()

    def perform_update(self, serializer):
        serializer.save()
        self.clear_cache()

    def perform_destroy(self, instance):
        instance.delete()
        self.clear_cache()

    @action(detail=False, methods=["post"], url_path="clear-cache")
    def clear_presentaciones_cache(self, request):
        self.clear_cache()
        return Response({"mensaje": "✅ Caché limpiado correctamente."})

    def clear_cache(self):
        keys = cache.keys("*presentaciones*")
        for key in keys:
            cache.delete(key)
        cache.delete_many([
            "presentaciones_tipos",
        ])
        
## Viewset Materiales
class MaterialViewSet(viewsets.ModelViewSet):
    """
    ViewSet optimizado para gestionar materiales.
    Permite listar, crear, actualizar y eliminar materiales con alto rendimiento.
    """
    queryset = models.Material.objects.only(
        "id", "nombre", "tipo", 
    ).all()
    serializer_class = MaterialSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["tipo",] 
    search_fields = ["nombre"]
    ordering_fields = ["nombre", "tipo"]
    ordering = ["nombre"]

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        instance.delete()

    
## Viewset Ordenes de produccion
class OrdenProduccionViewSet(viewsets.ModelViewSet):
    """
    ViewSet optimizado para gestionar órdenes de producción.
    Permite listar, crear, actualizar y eliminar órdenes con alto rendimiento.
    """
    queryset = models.OrdenProduccion.objects.only("id", "codigo_orden", "fecha_creacion", "estado").all()
    serializer_class = OrdenProduccionSerializer
    permission_classes = [IsAuthenticated]  # Protege el endpoint con autenticación
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["estado"]  # Permite filtrar por estado
    search_fields = ["codigo_orden"]  # Habilita búsqueda rápida por código de orden
    ordering_fields = ["fecha_creacion", "codigo_orden"]  # Permite ordenar por fecha o código
    ordering = ["-fecha_creacion"]  # Ordena por defecto mostrando las más recientes primero

    def perform_create(self, serializer):
        """ Guarda la orden de producción en la BD """
        serializer.save()

    def perform_update(self, serializer):
        """ Optimiza actualización asegurando cambios en campos esenciales """
        serializer.save()

    def perform_destroy(self, instance):
        """ Optimiza eliminación con manejo seguro de integridad referencial """
        instance.delete()
        

    @action(detail=True, methods=["patch"], url_path="cambiar-estado")
    def cambiar_estado(self, request, pk=None):
        """ Cambia el estado de una orden de producción """
        orden = self.get_object()
        nuevo_estado = request.data.get("estado")

        if not nuevo_estado:
            return Response({"error": "Debe proporcionar un nuevo estado."}, status=400)

        orden.estado = nuevo_estado
        orden.save()
        return Response({"mensaje": f"Estado actualizado a '{nuevo_estado}'"}, status=200)

    @action(detail=False, methods=["get"], url_path="filtrar-por-fechas")
    def filtrar_por_fechas(self, request):
        """ Filtra órdenes de producción por un rango de fechas y opcionalmente por estado """
        fecha_inicio = request.query_params.get("fecha_inicio")
        fecha_fin = request.query_params.get("fecha_fin")
        estado = request.query_params.get("estado", None)  # Opcional

        if not fecha_inicio or not fecha_fin:
            return Response({"error": "Debe proporcionar 'fecha_inicio' y 'fecha_fin' en formato YYYY-MM-DD."}, status=400)

        fecha_inicio = parse_date(fecha_inicio)
        fecha_fin = parse_date(fecha_fin)

        if not fecha_inicio or not fecha_fin:
            return Response({"error": "Formato de fecha inválido."}, status=400)

        ordenes = self.get_queryset().filter(fecha_creacion__range=[fecha_inicio, fecha_fin])
        
        if estado:
            ordenes = ordenes.filter(estado=estado)

        serializer = self.get_serializer(ordenes, many=True)
        return Response(serializer.data)
    

class PiezaViewSet(viewsets.ModelViewSet):
    """
    ViewSet optimizado para gestionar piezas.
    Permite listar, crear, actualizar y eliminar piezas con alto rendimiento.
    """
    queryset = models.Pieza.objects.select_related(
        "orden_produccion",
        "material",
        "presentacion",
        "creado_por"
    ).prefetch_related(
        "nesteos"
    ).all()

    serializer_class = PiezaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        "orden_produccion", "material", "presentacion", "prioritario", "estatus_tracking", "estado_produccion"
    ]
    search_fields = ["consecutivo"]
    ordering_fields = ["fecha_creacion", "consecutivo"]
    ordering = ["-fecha_creacion"]
    def perform_create(self, serializer):
        """ Guarda la pieza en la BD y maneja la subida de PDF """
        serializer.save()

    def perform_update(self, serializer):
        """ Optimiza actualización asegurando que el PDF no se borre accidentalmente """
        instance = self.get_object()
        if not self.request.FILES.get("pdf"):  # Si no se sube un nuevo archivo, mantiene el existente
            serializer.validated_data["pdf"] = instance.pdf
        serializer.save()

    def perform_destroy(self, instance):
        """ Optimiza eliminación con manejo seguro de integridad referencial """
        instance.delete()


    @action(detail=False, methods=["post"], url_path="buscar-por-codigo-orden")
    def buscar_por_codigo_orden(self, request):
        """ Busca piezas por el código de la orden de producción (Recibe el código en el body) """
        codigo_orden = request.data.get("codigo_orden", None)

        if not codigo_orden:
            return Response({"error": "Debe proporcionar un 'codigo_orden' en el body."}, status=status.HTTP_400_BAD_REQUEST)

        # Filtra las piezas basándose en el código de orden de producción
        piezas = self.get_queryset().filter(orden_produccion__codigo_orden=codigo_orden)

        if not piezas.exists():
            return Response({"mensaje": "No se encontraron piezas para la orden especificada."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(piezas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    @action(detail=False, methods=["post"], url_path="total-piezas-por-orden")
    def total_piezas_por_orden(self, request):
        """
        Devuelve la suma total de piezas por orden de producción.
        Se espera un JSON con {"codigo_orden": "valor"} en el body.
        """
        codigo_orden = request.data.get("codigo_orden")

        if not codigo_orden:
            return Response({"error": "Debe proporcionar un 'codigo_orden'."}, status=status.HTTP_400_BAD_REQUEST)

        total_piezas = models.Pieza.objects.filter(orden_produccion__codigo_orden=codigo_orden).aggregate(
            total_piezas=Sum("total_piezas")
        )["total_piezas"]

        return Response({"codigo_orden": codigo_orden, "total_piezas": total_piezas or 0}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="total-piezas-manufacturadas")
    def total_piezas_manufacturadas_por_orden(self, request):
        """
        Devuelve la suma total de piezas manufacturadas por orden de producción.
        Se espera un JSON con {"codigo_orden": "valor"} en el body.
        """
        codigo_orden = request.data.get("codigo_orden")

        if not codigo_orden:
            return Response({"error": "Debe proporcionar un 'codigo_orden'."}, status=status.HTTP_400_BAD_REQUEST)

        total_manufacturadas = models.Pieza.objects.filter(orden_produccion__codigo_orden=codigo_orden).aggregate(
            total_manufacturadas=Sum("piezas_manufacturadas")
        )["total_manufacturadas"]

        return Response({"codigo_orden": codigo_orden, "total_piezas_manufacturadas": total_manufacturadas or 0}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=["post"], url_path="count-piezas-por-orden")
    def count_piezas_por_orden(self, request):
        """
        Devuelve la cantidad total de piezas creadas para una orden de producción.
        Se espera un JSON con {"codigo_orden": "valor"} en el body.
        """
        codigo_orden = request.data.get("codigo_orden")

        if not codigo_orden:
            return Response({"error": "Debe proporcionar un 'codigo_orden'."}, status=status.HTTP_400_BAD_REQUEST)

        count_piezas = models.Pieza.objects.filter(orden_produccion__codigo_orden=codigo_orden).count()

        return Response({
            "codigo_orden": codigo_orden,
            "total_piezas_creadas": count_piezas
        }, status=status.HTTP_200_OK)
        
    @action(detail=True, methods=["patch"], url_path="actualizar-tracking")
    def actualizar_tracking(self, request, pk=None):
        """
        Actualiza el estatus de tracking de una pieza específica.
        Se espera un JSON con {"estatus_tracking": "Nuevo Estado"} en el body.
        """
        pieza = self.get_object()
        nuevo_estatus = request.data.get("estatus_tracking")

        if not nuevo_estatus:
            return Response({"error": "Debe proporcionar un 'estatus_tracking'."}, status=status.HTTP_400_BAD_REQUEST)

        pieza.estatus_tracking = nuevo_estatus
        pieza.save()

        return Response({
            "mensaje": "Estatus de tracking actualizado correctamente.",
            "id_pieza": pieza.id,
            "nuevo_estatus_tracking": pieza.estatus_tracking
        }, status=status.HTTP_200_OK)
        
    @action(detail=True, methods=["patch"], url_path="actualizar-produccion")
    def actualizar_produccion(self, request, pk=None):
        """
        Actualiza el estatus de producción de una pieza específica.
        Se espera un JSON con {"estado_produccion": "Nuevo Estado"} en el body.
        """
        pieza = self.get_object()
        nuevo_estado = request.data.get("estado_produccion")

        if not nuevo_estado:
            return Response({"error": "Debe proporcionar un 'estado_produccion'."}, status=status.HTTP_400_BAD_REQUEST)

        pieza.estado_produccion = nuevo_estado
        pieza.save()

        return Response({
            "mensaje": "Estatus de producción actualizado correctamente.",
            "id_pieza": pieza.id,
            "nuevo_estado_produccion": pieza.estado_produccion
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=["patch"], url_path="actualizar-prioritario")
    def actualizar_prioritario(self, request, pk=None):
        """
        Cambia el estado del booleano 'prioritario' de una pieza.
        Se espera un JSON con {"prioritario": true/false} en el body.
        """
        pieza = self.get_object()
        nuevo_valor = request.data.get("prioritario")

        if nuevo_valor is None:
            return Response({"error": "Debe proporcionar un valor para 'prioritario'."}, status=status.HTTP_400_BAD_REQUEST)

        pieza.prioritario = nuevo_valor
        pieza.save()

        return Response({
            "mensaje": "Estado de 'prioritario' actualizado correctamente.",
            "id_pieza": pieza.id,
            "nuevo_valor": pieza.prioritario
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=["patch"], url_path="actualizar-requiere-nesteo")
    def actualizar_requiere_nesteo(self, request, pk=None):
        """
        Cambia el estado del booleano 'requiere_nesteo' de una pieza.
        Se espera un JSON con {"requiere_nesteo": true/false} en el body.
        """
        pieza = self.get_object()
        nuevo_valor = request.data.get("requiere_nesteo")

        if nuevo_valor is None:
            return Response({"error": "Debe proporcionar un valor para 'requiere_nesteo'."}, status=status.HTTP_400_BAD_REQUEST)

        pieza.requiere_nesteo = nuevo_valor
        pieza.save()

        return Response({
            "mensaje": "Estado de 'requiere_nesteo' actualizado correctamente.",
            "id_pieza": pieza.id,
            "nuevo_valor": pieza.requiere_nesteo
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=["patch"], url_path="actualizar-retrabajo")
    def actualizar_retrabajo(self, request, pk=None):
        """
        Cambia el estado del booleano 'retrabajo' de una pieza y permite agregar un comentario.
        Se espera un JSON con {"retrabajo": true/false, "comentario_retrabajo": "Texto"} en el body.
        """
        pieza = self.get_object()
        nuevo_valor = request.data.get("retrabajo")
        comentario = request.data.get("comentario_retrabajo", "")

        if nuevo_valor is None:
            return Response({"error": "Debe proporcionar un valor para 'retrabajo'."}, status=status.HTTP_400_BAD_REQUEST)

        pieza.retrabajo = nuevo_valor
        pieza.comentario_retrabajo = comentario
        pieza.save()

        return Response({
            "mensaje": "Estado de 'retrabajo' actualizado correctamente.",
            "id_pieza": pieza.id,
            "nuevo_valor": pieza.retrabajo,
            "comentario_retrabajo": pieza.comentario_retrabajo
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="piezas-por-nesteo")
    def piezas_por_nesteo(self, request):
        """
        Obtiene todas las piezas asociadas a un nesteo.
        Se espera un JSON con {"nesteo_id": ID} en el body.
        """
        nesteo_id = request.data.get("nesteo_id")

        if not nesteo_id:
            return Response({"error": "Debe proporcionar un 'nesteo_id' en el body."}, status=status.HTTP_400_BAD_REQUEST)

        # Filtra las piezas que están vinculadas al nesteo dado
        piezas = models.Pieza.objects.filter(nesteos__id=nesteo_id).distinct()

        if not piezas.exists():
            return Response({"mensaje": "No se encontraron piezas asociadas a este nesteo."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(piezas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=["post"], url_path="procesos-por-pieza")
    def procesos_por_pieza(self, request):
        """
        Retorna los procesos asignados a una pieza específica, ya sea directamente o a través de un nesteo.
        Espera un JSON con {"pieza_id": ID} en el body.
        """
        pieza_id = request.data.get("pieza_id")

        if not pieza_id:
            return Response(
                {"error": "Debe proporcionar un 'pieza_id' en el body."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Primero, obtenemos los IDs de los nesteos asociados a la pieza
        nesteo_ids = models.PiezaNesteo.objects.filter(pieza_id=pieza_id).values_list('nesteo_id', flat=True)

        # Construimos una consulta que incluya:
        # 1. Procesos asignados directamente a la pieza.
        # 2. Procesos asignados a cualquiera de los nesteos de la pieza.
        query = Q(pieza_id=pieza_id) | Q(nesteo_id__in=list(nesteo_ids))

        queryset = models.AsignacionProceso.objects.select_related(
            "proceso", "pieza", "usuario", "nesteo"
        ).filter(query).distinct()

        if not queryset.exists():
            return Response(
                {"mensaje": "No se encontraron procesos asignados a esta pieza o a sus nesteos."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AsignacionProcesoSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=["patch"], url_path="actualizar-material-presentacion")
    def actualizar_material_y_presentacion(self, request, pk=None):
        pieza = self.get_object()
        material_id = request.data.get("material_id")
        presentacion_id = request.data.get("presentacion_id")

        if material_id is None:
            return Response(
                {"error": "Debe proporcionar un valor para 'material_id'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if presentacion_id is None:
            return Response(
                {"error": "Debe proporcionar un valor para 'presentacion_id'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Obtener las instancias completas de los modelos
            material = models.Material.objects.get(id=material_id)
            presentacion = models.PresentacionMaterial.objects.get(id=presentacion_id)
            
            # Asignar las instancias
            pieza.material = material
            pieza.presentacion = presentacion
            pieza.save()

            # Serializar la respuesta
            serializer = self.get_serializer(pieza)
            return Response({
                "mensaje": "Material y presentación actualizados correctamente.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except models.Material.DoesNotExist:
            return Response(
                {"error": f"Material con ID {material_id} no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        except models.PresentacionMaterial.DoesNotExist:
            return Response(
                {"error": f"Presentación con ID {presentacion_id} no encontrada"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    @action(detail=True, methods=["patch"], url_path="cambiar-estado-asignacion-finalizada")
    def cambiar_estado_asignacion_finalizada(self, request, pk=None):
        """
        Permite actualizar el estado del asignacionFinalizada de Pieza.
        """
        pieza = self.get_object()
        nuevo_estado = request.data.get("asignacionFinalizada", False)

        # Actualizar el estado de la pieza en el nesteo
        pieza.asignacionFinalizada = nuevo_estado
        pieza.estatus_tracking = "Manufactura"
        pieza.save()
        
        # Actualizar el estado de todas las PiezaNesteo asociadas a la pieza
        if models.PiezaNesteo.objects.filter(pieza=pieza).exists():
            models.PiezaNesteo.objects.filter(pieza=pieza).update(asignacionFinalizada=nuevo_estado)

        return Response(
            {"mensaje": f"El estado de asignacionFinalizada de la pieza {pieza.consecutivo} ha sido actualizado a '{nuevo_estado}'."},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['patch'], url_path='actualizar-pdf')
    def actualizar_pdf(self, request, pk=None):
        """
        Actualiza solo el PDF de una pieza específica.
        Se espera un archivo PDF en el campo 'pdf' del form-data.
        """
        pieza = self.get_object()

        if 'pdf' not in request.FILES:
            return Response(
                {"error": "Debe proporcionar un archivo PDF en el campo 'pdf'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        """Validar que el archivo sea PDF"""
        pdf_file = request.FILES['pdf']
        if not pdf_file.name.lower().endswith('.pdf'):
            return Response(
                {"error": "El archivo debe ser un PDF."},
                status=status.HTTP_400_BAD_REQUEST
            )

        """Eliminar el PDF anterior si existe"""
        if pieza.pdf:
            pieza.pdf.delete(save=False)

        """Asignar el nuevo PDF"""
        pieza.pdf = pdf_file
        pieza.save()

        return Response({
            "mensaje": "PDF actualizado correctamente.",
            "id_pieza": pieza.id,
            "nuevo_pdf_url": request.build_absolute_uri(pieza.pdf.url) if pieza.pdf else None
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=["patch"], url_path="limpiar-material-presentacion")
    def limpiar_material_presentacion(self, request, pk=None):
        """Establece material y presentación de la pieza como null."""
        pieza = self.get_object()
        
        pieza.material = None
        pieza.presentacion = None
        pieza.save()

        return Response({
            "mensaje": "Material y presentación limpiados correctamente.",
            "data": self.get_serializer(pieza).data
        }, status=status.HTTP_200_OK)
    
class ProcesoViewSet(viewsets.ModelViewSet):
    """
    ViewSet optimizado para gestionar procesos.
    Permite listar, crear, actualizar y eliminar procesos con alto rendimiento.
    """
    queryset = models.Proceso.objects.only("id", "nombre", "tipo", "area").all()
    serializer_class = ProcesoSerializer
    permission_classes = [IsAuthenticated]  # Protege el endpoint con autenticación
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["tipo", "area"]  # Permite filtrar por tipo de proceso
    search_fields = ["nombre", "area"]  # Habilita búsqueda rápida por nombre
    ordering_fields = ["nombre"]  # Permite ordenar por nombre
    ordering = ["nombre"]  # Ordena alfabéticamente

    def perform_create(self, serializer):
        """ Guarda el proceso en la BD """
        serializer.save()

    def perform_update(self, serializer):
        """ Optimiza actualización asegurando cambios en campos esenciales """
        serializer.save()

    def perform_destroy(self, instance):
        """ Optimiza eliminación con manejo seguro de integridad referencial """
        instance.delete()  

class MaquinaViewSet(viewsets.ModelViewSet):
    """
    ViewSet optimizado para gestionar máquinas.
    Permite listar, crear, actualizar y eliminar máquinas con alto rendimiento.
    """
    queryset = models.Maquina.objects.only("id", "nombre", "estado").all()
    serializer_class = MaquinaSerializer
    permission_classes = [IsAuthenticated]  # Protege el endpoint con autenticación
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["estado"]  # Permite filtrar por estado de la máquina
    search_fields = ["nombre"]  # Habilita búsqueda rápida por nombre
    ordering_fields = ["nombre"]  # Permite ordenar por nombre
    ordering = ["nombre"]  # Ordena alfabéticamente

    def perform_create(self, serializer):
        """ Guarda la máquina en la BD """
        serializer.save()

    def perform_update(self, serializer):
        """ Optimiza actualización asegurando cambios en campos esenciales """
        serializer.save()

    def perform_destroy(self, instance):
        """ Optimiza eliminación con manejo seguro de integridad referencial """
        instance.delete()
    
    @action(detail=True, methods=["patch"], url_path="cambiar-estado")
    def cambiar_estado(self, request, pk=None):
        """
        Cambia el estado de una máquina.
        Se espera un JSON con {"nuevo_estado": "Activo" | "Mantenimiento" | "Averiada"} en el body.
        """
        maquina = self.get_object()
        nuevo_estado = request.data.get("nuevo_estado")

        # Validar que el nuevo estado sea válido
        estados_validos = dict(models.Maquina.ESTADO_OPCIONES).keys()
        if nuevo_estado not in estados_validos:
            return Response(
                {"error": f"Estado no válido. Opciones permitidas: {list(estados_validos)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Actualizar el estado de la máquina
        maquina.estado = nuevo_estado
        maquina.save()

        return Response(
            {"mensaje": f"Estado de la máquina '{maquina.nombre}' actualizado a '{nuevo_estado}'"},
            status=status.HTTP_200_OK
        )


class MaquinaProcesoViewSet(viewsets.ModelViewSet):
    """
    ViewSet optimizado para gestionar la relación entre máquinas y procesos.
    Permite listar, crear, actualizar y eliminar registros con alto rendimiento.
    """
    queryset = models.MaquinaProceso.objects.select_related("maquina", "proceso").only("id", "maquina", "proceso").all()
    serializer_class = MaquinaProcesoSerializer
    permission_classes = [IsAuthenticated]  # Protege el endpoint con autenticación
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["maquina", "proceso"]  # Permite filtrar por máquina y proceso
    ordering_fields = ["maquina", "proceso"]  # Permite ordenar por máquina y proceso
    ordering = ["maquina"]  # Ordena alfabéticamente por máquina

    def perform_create(self, serializer):
        """ Guarda la relación máquina-proceso en la BD """
        serializer.save()

    def perform_update(self, serializer):
        """ Optimiza actualización asegurando cambios en campos esenciales """
        serializer.save()

    def perform_destroy(self, instance):
        """ Optimiza eliminación con manejo seguro de integridad referencial """
        instance.delete()
        
    @action(detail=False, methods=['get'], url_path='obtener-maquinas-por-proceso/(?P<proceso_id>[^/.]+)')
    def obtener_maquinas_por_proceso(self, request, proceso_id=None):
        """
        Obtiene todas las máquinas asociadas a un proceso específico.
        """
        try:
            # Obtiene solo las máquinas (no las relaciones completas)
            maquinas = models.Maquina.objects.filter(
                id__in=models.MaquinaProceso.objects.filter(
                    proceso_id=proceso_id
                ).values_list('maquina_id', flat=True)
            ).distinct().filter(estado="Activo")
            
            serializer = MaquinaSerializer(maquinas, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AsignacionProcesoViewSet(viewsets.ModelViewSet):
    """
    ViewSet optimizado para gestionar asignaciones de procesos.
    Permite listar, crear, actualizar y eliminar registros con alto rendimiento.
    """
    queryset = models.AsignacionProceso.objects.select_related("proceso", "pieza", "usuario").only(
        "id", "proceso", "pieza", "usuario", "estado", "prioridad", "fecha_asignacion"
    ).all()
    serializer_class = AsignacionProcesoSerializer
    permission_classes = [IsAuthenticated]  # Protege el endpoint con autenticación
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["proceso", "pieza", "nesteo", "maquina", "usuario", "estado", "pre_asignado", "prioridad"]
    search_fields = ["pieza__consecutivo", "usuario__nombre"]  # Búsqueda rápida por número de pieza o usuario
    ordering_fields = ["fecha_asignacion", "prioridad", "piezas_asignadas"]
    ordering = ["-fecha_asignacion", "prioridad"]  # Ordena por asignaciones más recientes y prioridad alta

    def perform_create(self, serializer):
        """ Guarda la asignación de proceso en la BD """
        serializer.save()

    def perform_update(self, serializer):
        """ Optimiza actualización asegurando cambios en campos esenciales """
        serializer.save()

    def perform_destroy(self, instance):
        """ Optimiza eliminación con manejo seguro de integridad referencial """
        instance.delete()
    
    @action(detail=True, methods=["patch"], url_path="cambiar-prioridad")
    def cambiar_prioridad(self, request, pk=None):
        """
        Cambia la prioridad de una asignación de proceso.
        Se espera un JSON con {"nueva_prioridad": int} en el body.
        """
        asignacion = self.get_object()
        nueva_prioridad = request.data.get("nueva_prioridad")

        if nueva_prioridad is None or not isinstance(nueva_prioridad, int) or nueva_prioridad < 0:
            return Response(
                {"error": "Debe proporcionar un valor entero positivo en 'nueva_prioridad'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Actualizar la prioridad
        asignacion.prioridad = nueva_prioridad
        asignacion.save()

        return Response(
            {"mensaje": f"La prioridad de la asignación {asignacion.id} se ha actualizado a {nueva_prioridad}."},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["patch"], url_path="cambiar-estado")
    def cambiar_estado(self, request, pk=None):
        """
        Cambia el estado de una asignación de proceso.
        Se espera un JSON con {"nuevo_estado": "Pendiente" | "En Curso" | "Finalizado"} en el body.
        """
        asignacion = self.get_object()
        nuevo_estado = request.data.get("nuevo_estado")

        # Validar que el nuevo estado sea válido
        estados_validos = dict(models.AsignacionProceso.ESTADO_OPCIONES).keys()
        if nuevo_estado not in estados_validos:
            return Response(
                {"error": f"Estado no válido. Opciones permitidas: {list(estados_validos)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Actualizar el estado
        asignacion.estado = nuevo_estado
        asignacion.save()

        return Response(
            {"mensaje": f"El estado de la asignación {asignacion.id} ha sido cambiado a '{nuevo_estado}'."},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], url_path='procesos-asignados')
    def filtros_avanzados(self, request):
        queryset = models.AsignacionProceso.objects.select_related("proceso", "pieza", "usuario").filter(
            estado__in=["En Curso", "Pendiente"]
        )
        
        # 1. Filtro por área múltiple (ej: ?area=CNC,Torno)
        area_param = request.query_params.get('area')
        if area_param:
            areas_list = [a.strip() for a in area_param.split(',') if a.strip()]
            areas_validas = dict(models.Proceso.AREAS_OPCIONES).keys()
            
            # Validar áreas
            invalid_areas = [a for a in areas_list if a not in areas_validas]
            if invalid_areas:
                return Response(
                    {
                        "error": f"Áreas inválidas: {', '.join(invalid_areas)}",
                        "opciones_validas": list(areas_validas)
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Aplicar filtro de áreas solo si hay áreas válidas
            queryset = queryset.filter(proceso__area__in=areas_list)

        # 2. Filtro por nombre (solo si se proporciona)
        nombre = request.query_params.get('nombre')
        if nombre:
            queryset = queryset.filter(proceso__nombre__icontains=nombre)
        
        # 3. Filtro por operador (solo si se proporciona)
        operador_id = request.query_params.get('operador_id')
        if operador_id:
            try:
                operador_id = int(operador_id)
                queryset = queryset.filter(usuario__id=operador_id)
            except (ValueError, TypeError):
                return Response(
                    {"error": "operador_id debe ser un número entero"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        # 4. Filtro por prioridad (solo si se proporciona)
        prioridad = request.query_params.get('prioridad')
        if prioridad:
            try:
                prioridad = int(prioridad)
                queryset = queryset.filter(prioridad=prioridad)
            except (ValueError, TypeError):
                return Response(
                    {"error": "prioridad debe ser un número entero"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        # 5. Nuevo filtro por fecha (case-insensitive, solo fecha)
        filtro_fecha = request.query_params.get('filtro_fecha')
        if filtro_fecha:
            hoy = timezone.now().date()  # Solo fecha, sin hora
            filtro_fecha_lower = filtro_fecha.lower()  # Convertir a minúsculas para comparación
            
            if filtro_fecha_lower == 'actuales':
                queryset = queryset.filter(fecha_inicio__date=hoy)
            elif filtro_fecha_lower == 'futuras':
                queryset = queryset.filter(fecha_inicio__date__gt=hoy)
            elif filtro_fecha_lower == 'retrasadas':
                queryset = queryset.filter(fecha_inicio__date__lt=hoy)
            else:
                return Response(
                    {
                        "error": "filtro_fecha inválido",
                        "opciones_validas": ["Actuales", "Futuras", "Retrasadas"],
                        "detalle": "El filtro no distingue mayúsculas/minúsculas"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Ordenamiento por defecto
        queryset = queryset.order_by('prioridad', 'proceso__nombre')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        return Response(self.get_serializer(queryset, many=True).data)
    
    @action(detail=False, methods=['get'], url_path='procesos-finalizados')
    def filtros_avanzados_finalizados(self, request):
        queryset = models.AsignacionProceso.objects.select_related("proceso", "pieza", "usuario").filter(
            estado__in=["Finalizado"]
        )
        
        # 1. Filtro por área múltiple (ej: ?area=CNC,Torno)
        area_param = request.query_params.get('area')
        if area_param:
            areas_list = [a.strip() for a in area_param.split(',') if a.strip()]
            areas_validas = dict(models.Proceso.AREAS_OPCIONES).keys()
            
            # Validar áreas
            invalid_areas = [a for a in areas_list if a not in areas_validas]
            if invalid_areas:
                return Response(
                    {
                        "error": f"Áreas inválidas: {', '.join(invalid_areas)}",
                        "opciones_validas": list(areas_validas)
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Aplicar filtro de áreas solo si hay áreas válidas
            queryset = queryset.filter(proceso__area__in=areas_list)

        # 2. Filtro por nombre (solo si se proporciona)
        nombre = request.query_params.get('nombre')
        if nombre:
            queryset = queryset.filter(proceso__nombre__icontains=nombre)
        
        # 3. Filtro por operador (solo si se proporciona)
        operador_id = request.query_params.get('operador_id')
        if operador_id:
            try:
                operador_id = int(operador_id)
                queryset = queryset.filter(usuario__id=operador_id)
            except (ValueError, TypeError):
                return Response(
                    {"error": "operador_id debe ser un número entero"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        # 4. Filtro por prioridad (solo si se proporciona)
        prioridad = request.query_params.get('prioridad')
        if prioridad:
            try:
                prioridad = int(prioridad)
                queryset = queryset.filter(prioridad=prioridad)
            except (ValueError, TypeError):
                return Response(
                    {"error": "prioridad debe ser un número entero"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Ordenamiento por defecto
        queryset = queryset.order_by('prioridad', 'proceso__nombre')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        return Response(self.get_serializer(queryset, many=True).data)
    
    
    @action(detail=False, methods=['get'], url_path='procesos-con-scrap')
    def procesos_con_scrap(self, request):
        """Endpoint para obtener procesos con estado 'Con Scrap'"""
        queryset = models.AsignacionProceso.objects.select_related(
            "proceso", "pieza", "usuario"
        ).filter(
            estado="Con Scrap" 
        ).order_by(
            'prioridad', 'proceso__nombre'  # Ordenamiento por prioridad y nombre
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        return Response(self.get_serializer(queryset, many=True).data)

class InventarioMaterialViewSet(viewsets.ModelViewSet):
    """
    ViewSet optimizado para gestionar inventario de materiales.
    Permite listar, crear, actualizar y eliminar registros con alto rendimiento.
    """
    queryset = models.InventarioMaterial.objects.select_related("material").only(
        "id", "material", "cantidad_disponible", "ubicacion"
    ).all()
    serializer_class = InventarioMaterialSerializer
    permission_classes = [IsAuthenticated]  # Protege el endpoint con autenticación
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["material", "ubicacion"]  # Permite filtrar por material y ubicación
    search_fields = ["material__nombre", "ubicacion"]  # Búsqueda rápida por nombre de material o ubicación
    ordering_fields = ["cantidad_disponible", "material"]  # Permite ordenar por cantidad o material
    ordering = ["material"]  # Ordena por material alfabéticamente

    def perform_create(self, serializer):
        """ Guarda el inventario de material en la BD """
        serializer.save()

    def perform_update(self, serializer):
        """ Optimiza actualización asegurando cambios en campos esenciales """
        serializer.save()

    def perform_destroy(self, instance):
        """ Optimiza eliminación con manejo seguro de integridad referencial """
        instance.delete()

    @action(detail=True, methods=["patch"], url_path="actualizar-cantidad")
    def actualizar_cantidad(self, request, pk=None):
        """
        Actualiza la cantidad disponible de un material en el inventario.
        Se espera un JSON con {"nueva_cantidad": int} en el body.
        """
        inventario = self.get_object()
        nueva_cantidad = request.data.get("nueva_cantidad")

        if nueva_cantidad is None or not isinstance(nueva_cantidad, int) or nueva_cantidad < 0:
            return Response(
                {"error": "Debe proporcionar un valor entero positivo en 'nueva_cantidad'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Actualizar la cantidad disponible
        inventario.cantidad_disponible = nueva_cantidad
        inventario.save()

        return Response(
            {
                "mensaje": f"La cantidad de '{inventario.material.nombre}' en '{inventario.ubicacion}' ha sido actualizada a {nueva_cantidad}.",
                "material": inventario.material.nombre,
                "ubicacion": inventario.ubicacion,
                "nueva_cantidad": nueva_cantidad
            },
            status=status.HTTP_200_OK
        )


class NesteoViewSet(viewsets.ModelViewSet):
    """
    ViewSet optimizado para gestionar nesteos.
    Permite listar, crear, actualizar y eliminar registros con alto rendimiento.
    """
    queryset = models.Nesteo.objects.select_related("material").only(
        "id", "nombre_placa", "material", "descripcion"
    ).all()
    serializer_class = NesteoSerializer
    permission_classes = [IsAuthenticated]  # Protege el endpoint con autenticación
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["material", "nombre_placa"]  # Permite filtrar por material y nombre de placa
    search_fields = ["nombre_placa", "material__nombre"]  # Búsqueda rápida por nombre de placa o material
    ordering_fields = ["nombre_placa", "material"]  # Permite ordenar por nombre o material
    ordering = ["nombre_placa"]  # Ordena por nombre de placa alfabéticamente

    def perform_create(self, serializer):
        """ Guarda el nesteo en la BD """
        serializer.save()

    def perform_update(self, serializer):
        """ Optimiza actualización asegurando cambios en campos esenciales """
        serializer.save()

    def perform_destroy(self, instance):
        """ Optimiza eliminación con manejo seguro de integridad referencial """
        instance.delete()
        
    @action(detail=True, methods=["patch"], url_path="cambiar-estado")
    def cambiar_estado(self, request, pk=None):
        """
        Activa o desactiva un nesteo específico.
        Se espera un JSON con {"activo": true/false} en el body.
        """
        nesteo = self.get_object()
        nuevo_estado = request.data.get("activo")

        if nuevo_estado is None or not isinstance(nuevo_estado, bool):
            return Response(
                {"error": "Debe proporcionar un valor booleano en 'activo' (true o false)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Actualizar el estado del nesteo
        nesteo.activo = nuevo_estado
        nesteo.save()

        estado_texto = "activado" if nuevo_estado else "desactivado"
        
        return Response(
            {
                "mensaje": f"El nesteo '{nesteo.nombre_placa}' ha sido {estado_texto}.",
                "nesteo_id": nesteo.id,
                "nombre_placa": nesteo.nombre_placa,
                "activo": nuevo_estado
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["get"], url_path="piezas-nesteo")
    def obtener_piezas_nesteo(self, request, pk=None):
        """
        Devuelve todas las piezas asociadas a un nesteo específico.
        """
        nesteo = self.get_object()
        piezas_nesteo = models.PiezaNesteo.objects.filter(nesteo=nesteo)

        if not piezas_nesteo.exists():
            return Response(
                {"mensaje": f"No hay piezas asignadas al nesteo '{nesteo.nombre_placa}'."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PiezaNesteoSerializer(piezas_nesteo, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PiezaNesteoViewSet(viewsets.ModelViewSet):
    """
    ViewSet optimizado para gestionar la asignación de piezas a nesteos.
    Permite listar, crear, actualizar y eliminar registros con alto rendimiento.
    """
    queryset = models.PiezaNesteo.objects.select_related("pieza", "nesteo").only(
        "id", "pieza", "nesteo", "cantidad", "estado", "fecha_asignacion"
    ).all()
    serializer_class = PiezaNesteoSerializer
    permission_classes = [IsAuthenticated]  # Protege el endpoint con autenticación
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["pieza", "nesteo", "estado"]  # Permite filtrar por pieza, nesteo y estado
    search_fields = ["pieza__consecutivo", "nesteo__nombre_placa"]  # Búsqueda rápida por número de pieza o nombre de placa
    ordering_fields = ["fecha_asignacion", "cantidad"]  # Permite ordenar por fecha de asignación o cantidad
    ordering = ["-fecha_asignacion"]  # Ordena por fecha de asignación (más recientes primero)

    def perform_create(self, serializer):
        pieza = serializer.validated_data.get("pieza")
        nesteo = serializer.validated_data.get("nesteo")
        cantidad_nueva = serializer.validated_data.get("cantidad")

        with transaction.atomic():
            obj, creado = models.PiezaNesteo.objects.select_for_update().get_or_create(
                pieza=pieza,
                nesteo=nesteo,
                defaults={
                    "cantidad": cantidad_nueva, 
                    "estado": serializer.validated_data.get("estado", "Pendiente")
                }
            )
            if not creado:
                obj.cantidad += cantidad_nueva
                obj.estado = serializer.validated_data.get("estado", obj.estado)
                obj.save()
            # Forzar la actualización del serializer con la instancia guardada
            serializer.instance = obj  # ¡Esta línea es clave!


    def perform_update(self, serializer):
        """ Optimiza actualización asegurando cambios en campos esenciales """
        serializer.save()

    def perform_destroy(self, instance):
        """ Optimiza eliminación con manejo seguro de integridad referencial """
        instance.delete()

    @action(detail=True, methods=["patch"], url_path="cambiar-estado")
    def cambiar_estado(self, request, pk=None):
        """
        Permite actualizar el estado de una PiezaNesteo.
        """
        pieza_nesteo = self.get_object()
        nuevo_estado = request.data.get("estado", None)

        # Validar que el estado proporcionado sea válido
        estados_validos = dict(models.PiezaNesteo.ESTADO_OPCIONES).keys()
        if nuevo_estado not in estados_validos:
            return Response(
                {"error": f"Estado inválido. Opciones disponibles: {', '.join(estados_validos)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Actualizar el estado de la pieza en el nesteo
        pieza_nesteo.estado = nuevo_estado
        pieza_nesteo.save()
        
        # Verificar si todas las demás PiezaNesteo de esta pieza están en estado "Procesado"
        pieza_id = pieza_nesteo.pieza_id
        nesteo_id = pieza_nesteo.nesteo_id
        todas_procesadas = models.PiezaNesteo.objects.filter(
            pieza_id=pieza_id,
            estado="Procesado",
        ).count() == 0
        
        logger.debug(f'Todas procesadas: ${todas_procesadas}');

        if todas_procesadas:
            return Response(
            {"mensaje": f"El estado de la pieza {pieza_nesteo.pieza.consecutivo} en nesteo '{pieza_nesteo.nesteo.nombre_placa}' ha sido actualizado a '{nuevo_estado}'. Todas las piezas del mismo nesteo han sido procesadas"},
            status=status.HTTP_200_OK
            )

        return Response(
            {"mensaje": f"El estado de la pieza {pieza_nesteo.pieza.consecutivo} en nesteo '{pieza_nesteo.nesteo.nombre_placa}' ha sido actualizado a '{nuevo_estado}'."},
            status=status.HTTP_200_OK
        )
        
    @action(detail=True, methods=["patch"], url_path="cambiar-estado-asignacion-finalizada")
    def cambiar_estado_asignacion_finalizada(self, request, pk=None):
        """
        Permite actualizar el estado del asignacionFinalizada de una PiezaNesteo.
        """
        pieza_nesteo = self.get_object()
        nuevo_estado = request.data.get("asignacionFinalizada", False)

        # Actualizar el estado de la pieza en el nesteo
        pieza_nesteo.asignacionFinalizada = nuevo_estado
        pieza_nesteo.save()
        
        # Verificar si todas las demás PiezaNesteo de esta pieza están en estado "Procesado"
        pieza_id = pieza_nesteo.pieza_id
        todas_procesadas = models.PiezaNesteo.objects.filter(
            pieza_id=pieza_id,
            asignacionFinalizada=False,
        ).count() == 0
        
        if todas_procesadas:
            # Actualizar el estado de la pieza relacionada
            pieza = models.Pieza.objects.get(pk=pieza_id)
            pieza.estatus_tracking = "Manufactura"
            pieza.asignacionFinalizada = True
            pieza.save()
            return Response(
            {"mensaje": f"El estado de asignacionFinalizada de la pieza {pieza_nesteo.pieza.consecutivo} en nesteo '{pieza_nesteo.nesteo.nombre_placa}' ha sido actualizado a '{nuevo_estado}'. Todas las piezas del mismo nesteo han sido procesadas"},
            status=status.HTTP_200_OK
            )

        return Response(
            {"mensaje": f"El estado de asignacionFinalizada de la pieza {pieza_nesteo.pieza.consecutivo} en nesteo '{pieza_nesteo.nesteo.nombre_placa}' ha sido actualizado a '{nuevo_estado}'."},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], url_path='total-por-pieza/(?P<pieza_id>[^/.]+)')
    def total_piezas_por_pieza(self, request, pieza_id=None):
        """
        Devuelve el total de piezas asignadas a nesteos para una pieza específica."""
        try:
            # Total general
            total = models.PiezaNesteo.objects.filter(
                pieza_id=pieza_id
            ).aggregate(
                total_piezas=Sum('cantidad')
            )['total_piezas'] or 0

            # Desglose por estado
            por_estado = models.PiezaNesteo.objects.filter(
                pieza_id=pieza_id
            ).values('estado').annotate(
                total=Sum('cantidad')
            ).order_by('estado')

            return Response({
                ##'pieza_id': pieza_id,
                'total_piezas': total,
                #'desglose_por_estado': list(por_estado),
                #'mensaje': f'Total de piezas asignadas a Nesteos para la pieza {pieza_id}'
            })
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class EtapaCalidadViewSet(viewsets.ModelViewSet):
    """
    ViewSet optimizado para gestionar las etapas de calidad.
    Permite listar, crear, actualizar y eliminar registros con alto rendimiento.
    """
    queryset = models.EtapaCalidad.objects.only("id", "nombre", "descripcion").all()
    serializer_class = EtapaCalidadSerializer
    permission_classes = [IsAuthenticated]  # Protege el endpoint con autenticación
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["nombre"]  # Permite filtrar por nombre de la etapa
    search_fields = ["nombre", "descripcion"]  # Búsqueda rápida por nombre o descripción
    ordering_fields = ["nombre"]  # Permite ordenar por nombre
    ordering = ["nombre"]  # Ordena por nombre alfabéticamente

    def perform_create(self, serializer):
        """ Guarda la etapa de calidad en la BD """
        serializer.save()

    def perform_update(self, serializer):
        """ Optimiza actualización asegurando cambios en campos esenciales """
        serializer.save()

    def perform_destroy(self, instance):
        """ Optimiza eliminación con manejo seguro de integridad referencial """
        instance.delete()

class FlujoCalidadViewSet(viewsets.ModelViewSet):
    """
    ViewSet optimizado para gestionar el flujo de calidad de las piezas.
    Permite listar, crear, actualizar y eliminar registros con alto rendimiento.
    """
    queryset = models.FlujoCalidad.objects.select_related("pieza", "etapa_calidad").only(
        "id", "pieza", "etapa_calidad", "estado", "piezas_asignadas", 
        "piezas_liberadas", "fecha_inicio", "fecha_finalizacion"
    ).all()
    serializer_class = FlujoCalidadSerializer
    permission_classes = [IsAuthenticated]  # Protege el endpoint con autenticación
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["pieza", "etapa_calidad", "estado"]  # Permite filtrar por pieza, etapa de calidad y estado
    search_fields = ["pieza__consecutivo", "etapa_calidad__nombre"]  # Búsqueda rápida por número de pieza o etapa de calidad
    ordering_fields = ["fecha_inicio", "piezas_asignadas", "piezas_liberadas"]  # Permite ordenar por fecha de inicio, piezas asignadas o liberadas
    ordering = ["-fecha_inicio"]  # Ordena por fecha de inicio (más recientes primero)

    def perform_create(self, serializer):
        """ Guarda el flujo de calidad en la BD """
        serializer.save()

    def perform_update(self, serializer):
        """ Optimiza actualización asegurando cambios en campos esenciales """
        serializer.save()

    def perform_destroy(self, instance):
        """ Optimiza eliminación con manejo seguro de integridad referencial """
        instance.delete()

    @action(detail=True, methods=["patch"], url_path="cambiar-estado")
    def cambiar_estado(self, request, pk=None):
        """
        Permite actualizar el estado del flujo de calidad de una pieza.
        """
        flujo_calidad = self.get_object()
        nuevo_estado = request.data.get("estado", None)

        # Validar que el estado proporcionado sea válido
        estados_validos = dict(models.FlujoCalidad.ESTADO_OPCIONES).keys()
        if nuevo_estado not in estados_validos:
            return Response(
                {"error": f"Estado inválido. Opciones disponibles: {', '.join(estados_validos)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Actualizar el estado del flujo de calidad
        flujo_calidad.estado = nuevo_estado
        flujo_calidad.save()

        return Response(
            {"mensaje": f"El estado del flujo de calidad para la pieza {flujo_calidad.pieza.consecutivo} ha sido actualizado a '{nuevo_estado}'."},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["patch"], url_path="actualizar-piezas-liberadas")
    def actualizar_piezas_liberadas(self, request, pk=None):
        """
        Permite actualizar la cantidad de piezas liberadas en un flujo de calidad.
        """
        flujo_calidad = self.get_object()
        nuevas_piezas_liberadas = request.data.get("piezas_liberadas", None)

        if nuevas_piezas_liberadas is None or not isinstance(nuevas_piezas_liberadas, int):
            return Response({"error": "Debe proporcionar un número entero válido para 'piezas_liberadas'."}, status=400)

        # Validar que no se asignen más piezas liberadas que las piezas asignadas
        if nuevas_piezas_liberadas > flujo_calidad.piezas_asignadas:
            return Response(
                {"error": f"No puede liberar más piezas ({nuevas_piezas_liberadas}) de las asignadas ({flujo_calidad.piezas_asignadas})."},
                status=400
            )

        # Actualizar la cantidad de piezas liberadas
        flujo_calidad.piezas_liberadas = nuevas_piezas_liberadas
        flujo_calidad.save()

        return Response(
            {"mensaje": f"Se actualizaron las piezas liberadas para la pieza {flujo_calidad.pieza.consecutivo} en la etapa {flujo_calidad.etapa_calidad.nombre} a {nuevas_piezas_liberadas}."},
            status=200
        )


class ScrapCalidadViewSet(viewsets.ModelViewSet):
    """
    ViewSet optimizado para gestionar los registros de scrap de calidad.
    Permite listar, crear, actualizar y eliminar registros con alto rendimiento.
    """
    queryset = models.ScrapCalidad.objects.select_related("pieza", "etapa_calidad").only(
        "id", "pieza", "etapa_calidad", "cantidad_scrap", "motivo", "fecha_registro"
    ).all()
    serializer_class = ScrapCalidadSerializer
    permission_classes = [IsAuthenticated]  # Protege el endpoint con autenticación
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["pieza", "etapa_calidad"]  # Permite filtrar por pieza y etapa de calidad
    search_fields = ["pieza__consecutivo", "etapa_calidad__nombre", "motivo"]  # Búsqueda rápida por número de pieza, etapa o motivo
    ordering_fields = ["fecha_registro", "cantidad_scrap"]  # Permite ordenar por fecha de registro o cantidad de scrap
    ordering = ["-fecha_registro"]  # Ordena por fecha de registro (más recientes primero)

    def perform_create(self, serializer):
        """ Guarda el registro de scrap en la BD """
        serializer.save()

    def perform_update(self, serializer):
        """ Optimiza actualización asegurando cambios en campos esenciales """
        serializer.save()

    def perform_destroy(self, instance):
        """ Optimiza eliminación con manejo seguro de integridad referencial """
        instance.delete()

    @action(detail=True, methods=["get"], url_path="total-scrap-pieza")
    def total_scrap(self, request, pk=None):
        """
        Retorna la suma total de scrap generado para una pieza específica.
        """
        try:
            pieza = models.Pieza.objects.get(pk=pk)
        except models.Pieza.DoesNotExist:
            return Response({"error": "La pieza especificada no existe."}, status=status.HTTP_404_NOT_FOUND)

        # Sumar todos los registros de scrap asociados a la pieza
        total_scrap = models.ScrapCalidad.objects.filter(pieza=pieza).aggregate(
            total_scrap=Coalesce(Sum("cantidad_scrap"), 0)
        )["total_scrap"]

        return Response(
            {
                "pieza": pieza.consecutivo,
                "total_scrap": total_scrap
            },
            status=status.HTTP_200_OK
        )


class ProveedorTratamientoViewSet(viewsets.ModelViewSet):
    """
    ViewSet optimizado para gestionar proveedores de tratamientos de calidad.
    Permite listar, crear, actualizar y eliminar registros con alto rendimiento.
    """
    queryset = models.ProveedorTratamiento.objects.only(
        "id", "nombre", "tipo", "nombre_de_contacto", "correo_de_contacto", 
        "telefono_de_contacto", "fecha_entrega_estimada", "unidad_de_tiempo"
    ).all()
    serializer_class = ProveedorTratamientoSerializer
    permission_classes = [IsAuthenticated]  # Protege el endpoint con autenticación
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["tipo"]  # Permite filtrar por tipo de tratamiento
    search_fields = ["nombre", "nombre_de_contacto", "correo_de_contacto"]  # Búsqueda rápida por nombre, contacto o correo
    ordering_fields = ["nombre", "fecha_entrega_estimada"]  # Permite ordenar por nombre y tiempo estimado de entrega
    ordering = ["nombre"]  # Ordena alfabéticamente por nombre de proveedor

    def perform_create(self, serializer):
        """ Guarda el proveedor en la BD """
        serializer.save()

    def perform_update(self, serializer):
        """ Optimiza actualización asegurando cambios en campos esenciales """
        serializer.save()

    def perform_destroy(self, instance):
        """ Optimiza eliminación con manejo seguro de integridad referencial """
        instance.delete()
        
class TratamientoCalidadViewSet(viewsets.ModelViewSet):
    """
    ViewSet optimizado para gestionar los tipos de tratamientos de calidad disponibles.
    Permite listar, crear, actualizar y eliminar registros eficientemente.
    """
    queryset = models.TratamientoCalidad.objects.only(
        "id", "nombre", "tipo_material", "tipo_tratamiento", "descripcion"
    )
    serializer_class = TratamientoCalidadSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["tipo_material", "tipo_tratamiento"]
    search_fields = ["nombre", "descripcion"]
    ordering_fields = ["nombre", "tipo_material", "tipo_tratamiento"]
    ordering = ["nombre"]

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        instance.delete()
    

class AsignacionTratamientoCalidadViewSet(viewsets.ModelViewSet):
    """
    ViewSet optimizado para gestionar los tratamientos de calidad de las piezas.
    Permite listar, crear, actualizar y eliminar registros con alto rendimiento.
    """
    queryset = models.AsignacionTratamientoCalidad.objects.select_related(
        "pieza", "proveedor", "tratamiento"
    ).only(
        "id", "pieza", "proveedor", "tratamiento", "fecha_salida",
        "fecha_entrega", "fecha_recepcion"
    ).all()

    serializer_class = AsignacionTratamientoCalidadSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["pieza", "proveedor", "tratamiento"]  
    search_fields = [
        "pieza__consecutivo", "proveedor__nombre", "tratamiento__nombre"
    ]
    ordering_fields = ["fecha_salida", "fecha_entrega", "fecha_recepcion"]
    ordering = ["-fecha_salida"]

    def perform_create(self, serializer):
        """Crear asignacion"""
        serializer.save()

    def perform_update(self, serializer):
        """Actualizar asignacion"""
        serializer.save()

    def perform_destroy(self, instance):
        """Borrar una asignacion"""
        instance.delete()
    

class RackProduccionViewSet(viewsets.ModelViewSet):
    """
    ViewSet optimizado para gestionar racks de producción.
    Permite listar, crear, actualizar y eliminar registros con alto rendimiento.
    """
    queryset = models.RackProduccion.objects.only(
        "id", "codigo_rack", "ubicacion", "estado"
    ).all()
    serializer_class = RackProduccionSerializer
    permission_classes = [IsAuthenticated]  
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["estado", "ubicacion"]
    search_fields = ["codigo_rack", "ubicacion"]
    ordering_fields = ["codigo_rack"]
    ordering = ["codigo_rack"]

    def perform_create(self, serializer):
        """ Guarda el rack en la BD """
        serializer.save()

    def perform_update(self, serializer):
        """ Optimiza actualización asegurando cambios en campos esenciales """
        serializer.save()

    def perform_destroy(self, instance):
        """ Optimiza eliminación con manejo seguro de integridad referencial """
        instance.delete()
        

class EstanteProduccionViewSet(viewsets.ModelViewSet):
    """
    ViewSet optimizado para gestionar estantes de producción.
    Permite listar, crear, actualizar y eliminar registros con alto rendimiento.
    """
    queryset = models.EstanteProduccion.objects.select_related("rack").only(
        "id", "codigo_estante", "rack", "estado"
    ).all()
    serializer_class = EstanteProduccionSerializer
    permission_classes = [IsAuthenticated]  # Protege el endpoint con autenticación
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["estado", "rack"]  # Permite filtrar por estado y rack asociado
    search_fields = ["codigo_estante", "rack__codigo_rack"]  # Búsqueda rápida por código de estante o rack
    ordering_fields = ["codigo_estante"]  # Permite ordenar por código de estante
    ordering = ["codigo_estante"]

    def perform_create(self, serializer):
        """ Guarda el estante en la BD """
        serializer.save()

    def perform_update(self, serializer):
        """ Optimiza actualización asegurando cambios en campos esenciales """
        serializer.save()

    def perform_destroy(self, instance):
        """ Optimiza eliminación con manejo seguro de integridad referencial """
        instance.delete()
        

class UbicacionPiezaViewSet(viewsets.ModelViewSet):
    """
    ViewSet optimizado para gestionar la ubicación de piezas en producción.
    Permite listar, crear, actualizar y eliminar registros con alto rendimiento.
    """
    queryset = models.UbicacionPieza.objects.select_related("pieza", "estante").only(
        "id", "pieza", "estante", "cantidad", "fecha_registro", "fecha_salida", "responsable"
    ).all()
    serializer_class = UbicacionPiezaSerializer
    permission_classes = [IsAuthenticated]  # Protege el endpoint con autenticación
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["pieza", "estante", "responsable"]  # Permite filtrar por pieza, estante y responsable
    search_fields = ["pieza__consecutivo", "estante__codigo_estante", "responsable"]  # Búsqueda rápida
    ordering_fields = ["fecha_registro", "fecha_salida", "cantidad"]  # Permite ordenar por fecha y cantidad
    ordering = ["-fecha_registro"]  # Ordena por fecha de registro descendente

    def perform_create(self, serializer):
        """ Guarda la ubicación de la pieza en la BD """
        serializer.save()

    def perform_update(self, serializer):
        """ Optimiza actualización asegurando cambios en campos esenciales """
        serializer.save()

    def perform_destroy(self, instance):
        """ Optimiza eliminación con manejo seguro de integridad referencial """
        instance.delete()
        
    @action(detail=True, methods=["patch"], url_path="actualizar-cantidad")
    def actualizar_cantidad(self, request, pk=None):
        """
        Permite actualizar la cantidad de una ubicación de pieza específica.
        """
        try:
            ubicacion = models.UbicacionPieza.objects.get(pk=pk)
        except models.UbicacionPieza.DoesNotExist:
            return Response({"error": "La ubicación especificada no existe."}, status=status.HTTP_404_NOT_FOUND)

        nueva_cantidad = request.data.get("cantidad", None)

        if nueva_cantidad is None:
            return Response({"error": "Debe proporcionar un valor para 'cantidad'."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            nueva_cantidad = int(nueva_cantidad)
            if nueva_cantidad < 0:
                return Response({"error": "La cantidad no puede ser negativa."}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "El valor de 'cantidad' debe ser un número entero válido."}, status=status.HTTP_400_BAD_REQUEST)

        ubicacion.cantidad = nueva_cantidad
        ubicacion.save()

        return Response(
            {
                "mensaje": "Cantidad actualizada exitosamente.",
                "id": ubicacion.id,
                "pieza": ubicacion.pieza.consecutivo,
                "estante": ubicacion.estante.codigo_estante,
                "nueva_cantidad": ubicacion.cantidad
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["patch"], url_path="actualizar-responsable")
    def actualizar_responsable(self, request, pk=None):
        """
        Permite actualizar el responsable de una ubicación de pieza específica.
        """
        try:
            ubicacion = models.UbicacionPieza.objects.get(pk=pk)
        except models.UbicacionPieza.DoesNotExist:
            return Response({"error": "La ubicación especificada no existe."}, status=status.HTTP_404_NOT_FOUND)

        nuevo_responsable_id = request.data.get("responsable", None)

        if nuevo_responsable_id is None:
            return Response({"error": "Debe proporcionar un 'responsable' válido."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            nuevo_responsable = Usuarios.objects.get(pk=nuevo_responsable_id)
        except Usuarios.DoesNotExist:
            return Response({"error": "El usuario especificado no existe."}, status=status.HTTP_404_NOT_FOUND)

        ubicacion.responsable = nuevo_responsable
        ubicacion.save()

        return Response(
            {
                "mensaje": "Responsable actualizado exitosamente.",
                "id": ubicacion.id,
                "pieza": ubicacion.pieza.consecutivo,
                "estante": ubicacion.estante.codigo_estante,
                "nuevo_responsable": {
                    "id": nuevo_responsable.id,
                    "nombre": nuevo_responsable.nombre,
                    "correo": nuevo_responsable.correo
                }
            },
            status=status.HTTP_200_OK
        )


class PersonalMaquinaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar las asignaciones de máquinas al personal.
    Permite listar, crear, actualizar y eliminar asignaciones.
    """
    queryset = models.PersonalMaquina.objects.select_related("personal", "maquina").all()
    serializer_class = PersonalMaquinaSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["personal", "maquina"]  # Permite filtrar por usuario o máquina
    search_fields = ["personal__nombre", "maquina__nombre"]  # Búsqueda rápida
    ordering_fields = ["personal", "maquina"]  # Permite ordenar
    ordering = ["personal"]  # Orden predeterminado

    def perform_create(self, serializer):
        """ Asigna máquina a usuario """
        serializer.save()

    def perform_update(self, serializer):
        """ Actualiza una asignación existente """
        serializer.save()

    def perform_destroy(self, instance):
        """ Elimina la asignación """
        instance.delete()
        
    @action(detail=False, methods=["get"], url_path="por-usuario/(?P<usuario_id>[^/.]+)")
    def obtener_por_usuario(self, request, usuario_id=None):
        """
        Retorna todas las asignaciones de máquinas para un usuario dado por su ID.
        """
        asignaciones = self.queryset.filter(personal__id=usuario_id)
        page = self.paginate_queryset(asignaciones)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(asignaciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='obtener-personal-por-maquinas/(?P<maquina_id>[^/.]+)')
    def obtener_personal_por_maquina(self, request, maquina_id=None):
        """
        Obtiene todas las máquinas asociadas a un proceso específico.
        """
        try:
            # Obtiene solo las máquinas (no las relaciones completas)
            operadores = models.Usuarios.objects.filter(
                id__in=models.PersonalMaquina.objects.filter(
                    maquina_id=maquina_id
                ).values_list('personal_id', flat=True)
            ).distinct()
            
            # Usa el serializer de Maquina en lugar de MaquinaProceso
            serializer = UsuariosVerySimpleSerializer(operadores, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class HorarioProduccionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar los horarios de producción de los usuarios.
    Permite listar, crear, actualizar y eliminar los horarios asignados.
    """
    queryset = models.HorarioProduccion.objects.select_related("usuario").all()
    serializer_class = HorarioProduccionSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["usuario", "tiene_comida", "dias_trabajo"]
    search_fields = ["usuario__nombre", "usuario__correo"]
    ordering_fields = ["hora_entrada", "hora_salida", "hora_inicio_comida"]
    ordering = ["hora_entrada"]

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        instance.delete()

    @action(detail=False, methods=["get"], url_path="por-usuario/(?P<usuario_id>[^/.]+)")
    def obtener_por_usuario(self, request, usuario_id=None):
        """
        Retorna todos los horarios de producción de un usuario dado por su ID.
        """
        horarios = self.queryset.filter(usuario__id=usuario_id)
        page = self.paginate_queryset(horarios)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(horarios, many=True)
        return Response(serializer.data)