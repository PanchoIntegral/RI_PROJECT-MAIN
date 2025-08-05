from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal, InvalidOperation
import json
import logging
from django.forms import DecimalField
from django.shortcuts import get_object_or_404
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework import filters
from django.db.models import CharField
from django.db.models.functions import Cast
from django.db.models import Count
from .models import AbonoTarjeta, AbonoProveedor, AportacionObreroPatronales, AportacionPatronalesIMSS, AportacionRetiroIMSS, CeavIMSS, CeavPatronal, ComprobantePagoNomina, ComprobantePagoResidentePracticante, CuentaPorPagarProveedor, MovimientoTarjeta, Nomina, NominaResidentesPracticantes, PagoMensualTarjeta, PagoPorPeriodo, SalarioMinimo, Sum, TarjetaCredito, Vacaciones

from ri_project import settings
from .models import Contacto, CreditoPrestamo, CuentaBancaria, CuentaPorCobrar, Departamento, DetalleCxC, Estante, Message, OtroGasto, PagoCreditoPrestamo, PagoOtroGasto, Pedido, ProductoAlmacen, Rack, ServiciosFactura, TipoOtroGasto,PagoPeriodoAbono,Isr
from .models import Usuarios
from .models import Producto
from .models import Servicio
from .models import Requisicion
from .models import Proveedor
from .models import OrdenDeCompra
from .models import Recibo
from .models import Project, AmortizacionCuota
from .models import BancoModelo,MovimientoBanco,AbonoBanco
from .serializer import AbonoTarjetaSerializer, AmortizacionCuotaSerializer, AportacionObreroPatronalesSerializer, AportacionPatronalesIMSSSerializer, AportacionRetiroIMSSSerializer, CEAVIMSSSerializer, ContactoSerializer, CreditoPrestamoSerializer, CuentaBancariaSerializer, DepartamentoSerializer, DetalleCxCSerializer, EstanteSerializer, IsrSerializer, MovimientoTarjetaSerializer, OtroGastoSerializer, PagoCreditoPrestamoSerializer, PagoMensualTarjetaSerializer, PagoOtroGastoSerializer, PagoPorPeriodoSerializer, PedidoSerializer, ProductoAlmacenSerializer, PropuestaCxCSerializer, RackSerializer, SalarioMinimoSerializer, ServicioFacturaSerializer, TarjetaCreditoSerializer, TipoOtroGastoSerializer,PagoPeriodoAbonoSerializer,IsrSerializer, UsuariosVerySimpleSerializer, VacacionesSerializer
from .serializer import AbonoProveedorSerializer, AbonoTarjetaSerializer, AmortizacionCuotaSerializer, AportacionObreroPatronalesSerializer, AportacionPatronalesIMSSSerializer, AportacionRetiroIMSSSerializer, CEAVIMSSSerializer, CeavPatronalSerializer, ComprobantePagoResidentePracticanteSerializer, ComprobantePagoSerializer, ContactoSerializer, CreditoPrestamoSerializer, CuentaBancariaSerializer, CuentaPorPagarProveedorSerializer, DepartamentoSerializer, DetalleCxCSerializer, EstanteSerializer, IsrSerializer, MovimientoTarjetaSerializer, NominaResidentesPracticantesSerializer, NominaSerializer, OtroGastoSerializer, PagoCreditoPrestamoSerializer, PagoMensualTarjetaSerializer, PagoOtroGastoSerializer, PagoPorPeriodoSerializer, PedidoSerializer, ProductoAlmacenSerializer, PropuestaCxCSerializer, RackSerializer, SalarioMinimoSerializer, ServicioFacturaSerializer, TarjetaCreditoSerializer, TipoOtroGastoSerializer,PagoPeriodoAbonoSerializer,IsrSerializer, VacacionesSerializer
from .serializer import MessageSerializer
from .serializer import UsuariosSerializer
from .serializer import ProductoSerializer
from .serializer import ServicioSerializer
from .serializer import RequisicionSerializer
from .serializer import ProveedorSerializer
from .serializer import OrdenDeCompraSerializer
from .serializer import ReciboSerializer
from .serializer import ProjectSerializer
from .serializer import ProductoRequisicionSerializer
from .serializer import BancoModeloSerializer,MovimientoBancoSerializer,AbonoBancoSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import F, FloatField

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from django.db.models import Q
from django.http import FileResponse
from rest_framework.views import APIView

import os
from django.http import FileResponse
from datetime import datetime, timedelta, timezone
from xhtml2pdf import pisa
from io import BytesIO
from jinja2 import Environment, FileSystemLoader
from django.db.models import F, ExpressionWrapper, Case, When, IntegerField, Value

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ServiciosFactura
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from datetime import date
from django.db.models import Max
from django.db.models import OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.db import models
from django.db import transaction
from django.utils.timezone import now
from django.db.models.functions import ExtractYear


ERROR_CREDENCIALES_INVALIDAS = "Credenciales inválidas."
ERROR_TOKEN_INVALIDO = "Token inválido."
ERROR_TOKEN_NO_PROPORCIONADO = "Token no proporcionado."

class CustomObtainAuthToken(APIView):
    def post(self, request, *args, **kwargs) -> Response:
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': ERROR_CREDENCIALES_INVALIDAS}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=username, password=password)

        if user:
            token, _ = Token.objects.get_or_create(user=user)
            user_serializer = UsuariosSerializer(user)
            return Response({'token': token.key, 'user': user_serializer.data})

        return Response({'error': ERROR_CREDENCIALES_INVALIDAS}, status=status.HTTP_400_BAD_REQUEST)

class GetUserFromToken(APIView):
    def get(self, request, *args, **kwargs) -> Response:
        token_header = request.META.get('HTTP_AUTHORIZATION')

        if not token_header or not token_header.startswith('Token '):
            return Response({'error': ERROR_TOKEN_NO_PROPORCIONADO}, status=status.HTTP_400_BAD_REQUEST)

        token_key = token_header.split(' ')[1]

        try:
            token = Token.objects.select_related('user').get(key=token_key)
            user_serializer = UsuariosSerializer(token.user)
            return Response({'user': user_serializer.data})
        except Token.DoesNotExist:
            return Response({'error': ERROR_TOKEN_INVALIDO}, status=status.HTTP_400_BAD_REQUEST)
        except IndexError:
            return Response({'error': ERROR_TOKEN_INVALIDO}, status=status.HTTP_400_BAD_REQUEST)

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().order_by('-id')
    serializer_class = ProjectSerializer
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    ordering_fields = ['nombre']
    
    def get_queryset(self):
        queryset = Project.objects.all().order_by('-id')
        nombre = self.request.query_params.get('nombre', None)
        usuario = self.request.query_params.get('usuario', None)

        if nombre is not None:
            queryset = queryset.filter(nombre__icontains=nombre)
        if usuario is not None:
            queryset = queryset.filter(usuario__username=usuario)

        return queryset
    
    def list(self, request, *args, **kwargs):
        username = request.query_params.get('search', None)
        if username is not None:
            self.queryset = self.queryset.filter(usuario__username=username)
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def requisiciones_proyecto(self, request, id_proyecto=None):
        if id_proyecto is not None:
            requisiciones = Requisicion.objects.filter(proyecto__id=id_proyecto).order_by('-id')
            serializer = self.get_serializer(requisiciones, many=True)
            return Response(serializer.data)
        else:
            return Response({"error": "No se proporcionó un ID de proyecto."})
    
    @action(detail=False, methods=['get'])
    def requisiciones_pendientes_proyecto(self, request, id_proyecto=None):
        if id_proyecto is not None:
            requisiciones = Requisicion.objects.filter(proyecto__id=id_proyecto, aprobado='PENDIENTE').order_by('-id')
            serializer = self.get_serializer(requisiciones, many=True)
            return Response(serializer.data)
        else:
            return Response({"error": "No se proporcionó un ID de proyecto."})

    @action(detail=False, methods=['get'])
    def requisiciones_rechazadas_proyecto(self, request, id_proyecto=None):
        if id_proyecto is not None:
            requisiciones = Requisicion.objects.filter(proyecto__id=id_proyecto, aprobado='RECHAZADO').order_by('-id')
            serializer = self.get_serializer(requisiciones, many=True)
            return Response(serializer.data)
        else:
            return Response({"error": "No se proporcionó un ID de proyecto."})

    @action(detail=False, methods=['get'])
    def requisiciones_aprobadas_proyecto(self, request, id_proyecto=None):
        if id_proyecto is not None:
            requisiciones = Requisicion.objects.filter(proyecto__id=id_proyecto, aprobado='APROBADO').order_by('-id')
            serializer = self.get_serializer(requisiciones, many=True)
            return Response(serializer.data)
        else:
            return Response({"error": "No se proporcionó un ID de proyecto."})

class UsuariosViewSet(viewsets.ModelViewSet):
    serializer_class = UsuariosSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['departamento__nombre']
    ordering_fields = ['username']
    ordering = ['username']  # Orden predeterminado

    # Definición del queryset optimizado con select_related y prefetch_related
    queryset = Usuarios.objects.select_related('departamento').prefetch_related('requisiciones', 'messages', 'proyectos').all()
    
    @action(detail=False, methods=['get'], url_path='obtener-usuarios-simple')
    def obtener_usuarios_simple(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = UsuariosVerySimpleSerializer(queryset, many=True)
        return Response(serializer.data)
    
class DepartamentoViewSet(viewsets.ModelViewSet):
    queryset = Departamento.objects.all()
    serializer_class = DepartamentoSerializer
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def requisiciones_pendientes_departamento(self, request, id_departamento=None):
        if id_departamento is not None:
            requisiciones = Requisicion.objects.filter(usuario__departamento__id=id_departamento, aprobado='PENDIENTE').order_by('-id')
            serializer = RequisicionSerializer(requisiciones, many=True)
            return Response(serializer.data)
        else:
            return Response({"error": "No se proporcionó un ID de departamento."})

    @action(detail=False, methods=['get'])
    def requisiciones_rechazadas_departamento(self, request, id_departamento=None):
        if id_departamento is not None:
            requisiciones = Requisicion.objects.filter(usuario__departamento__id=id_departamento, aprobado='RECHAZADO').order_by('-id')
            serializer = RequisicionSerializer(requisiciones, many=True)
            return Response(serializer.data)
        else:
            return Response({"error": "No se proporcionó un ID de departamento."})

    @action(detail=False, methods=['get'])
    def requisiciones_aprobadas_departamento(self, request, id_departamento=None):
        if id_departamento is not None:
            requisiciones = Requisicion.objects.filter(usuario__departamento__id=id_departamento, aprobado='APROBADO').order_by('-id')
            serializer = RequisicionSerializer(requisiciones, many=True)
            return Response(serializer.data)
        else:
            return Response({"error": "No se proporcionó un ID de departamento."})

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all().order_by('-id')
    serializer_class = ProductoSerializer
    ordering_fields = ['nombre']

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def ultimos(self, request):
        ultimos_productos = Producto.objects.order_by('-id')[:10]
        serializer = self.get_serializer(ultimos_productos, many=True)
        return Response(serializer.data)
    
    def get_queryset(self):
        queryset = Producto.objects.all().order_by('-id')
        identificador = self.request.query_params.get('identificador', None)
        nombre = self.request.query_params.get('nombre', None)
        descripcion = self.request.query_params.get('descripcion', None)
        costo = self.request.query_params.get('costo', None)
        divisa = self.request.query_params.get('divisa', None)
        cantidad = self.request.query_params.get('cantidad', None)
        unidad_de_medida = self.request.query_params.get('medida', None)
        limit = self.request.query_params.get('limit', None)


        if identificador is not None:
            queryset = queryset.filter(identificador__icontains=identificador)

        if nombre is not None:
            queryset = queryset.filter(nombre__icontains=nombre)

        if descripcion is not None:
            queryset = queryset.filter(descripcion__icontains=descripcion)

        if costo is not None:
            if '>' in costo and '<' in costo:
                min_costo, max_costo = costo.split('<')
                min_costo = min_costo.replace('>', '')
                queryset = queryset.filter(costo__gt=min_costo, costo__lt=max_costo)
            elif '>' in costo:
                min_costo = costo.replace('>', '')
                queryset = queryset.filter(costo__gt=min_costo)
            elif '<' in costo:
                max_costo = costo.replace('<', '')
                queryset = queryset.filter(costo__lt=max_costo)
            else:
                queryset = queryset.filter(costo=costo)

        if divisa is not None:
            queryset = queryset.filter(divisa=divisa)

        if cantidad is not None:
            if '>' in cantidad and '<' in cantidad:
                min_cantidad, max_cantidad = cantidad.split('<')
                min_cantidad = min_cantidad.replace('>', '')
                queryset = queryset.filter(cantidad__gt=min_cantidad, cantidad__lt=max_cantidad)
            elif '>' in cantidad:
                min_cantidad = cantidad.replace('>', '')
                queryset = queryset.filter(cantidad__gt=min_cantidad)
            elif '<' in cantidad:
                max_cantidad = cantidad.replace('<', '')
                queryset = queryset.filter(cantidad__lt=max_cantidad)
            else:
                queryset = queryset.filter(cantidad=cantidad)

        if unidad_de_medida is not None:
            queryset = queryset.filter(unidad_de_medida__icontains=unidad_de_medida)
        
        if limit is not None:
            try:
                limit = int(limit)
                queryset = queryset[:limit]
            except ValueError:
                pass

        return queryset

class ProductoAlmacenViewSet(viewsets.ModelViewSet):
    queryset = ProductoAlmacen.objects.all().order_by('-id')
    serializer_class = ProductoAlmacenSerializer
    ordering_fields = ['nombre']

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        identificador = self.request.query_params.get('identificador', None)
        nombre = self.request.query_params.get('nombre', None)
        descripcion = self.request.query_params.get('descripcion', None)
        costo = self.request.query_params.get('costo', None)
        divisa = self.request.query_params.get('divisa', None)
        cantidad = self.request.query_params.get('cantidad', None)
        orden_compra_id = self.request.query_params.get('orden', None)
        posicion_id = self.request.query_params.get('posicion_id', None)
        id = self.request.query_params.get('id', None)
        rack_nombre = self.request.query_params.get('rack', None)
        estante_numero = self.request.query_params.get('estante', None)
        liberado = self.request.query_params.get('liberado', None)

        if rack_nombre is not None:
            queryset = queryset.filter(posicion__rack__nombre=rack_nombre)
            if estante_numero is not None:
                queryset = queryset.filter(posicion__numero=estante_numero)

        if identificador is not None:
            queryset = queryset.filter(identificador__icontains=identificador)
            
        if nombre is not None:
            queryset = queryset.filter(nombre__icontains=nombre)
            
        if descripcion is not None:
            queryset = queryset.filter(descripcion__icontains=descripcion)
            
        if costo is not None:
            if '>' in costo and '<' in costo:
                min_costo, max_costo = costo.split('<')
                min_costo = min_costo.replace('>', '')
                queryset = queryset.filter(costo__gt=min_costo, costo__lt=max_costo)
            elif '>' in costo:
                min_costo = costo.replace('>', '')
                queryset = queryset.filter(costo__gt=min_costo)
            elif '<' in costo:
                max_costo = costo.replace('<', '')
                queryset = queryset.filter(costo__lt=max_costo)
            else:
                queryset = queryset.filter(costo=costo)
            
        if divisa is not None:
            queryset = queryset.filter(divisa=divisa)
            
        if cantidad is not None:
            if '>' in cantidad and '<' in cantidad:
                min_cantidad, max_cantidad = cantidad.split('<')
                min_cantidad = min_cantidad.replace('>', '')
                queryset = queryset.filter(cantidad__gt=min_cantidad, cantidad__lt=max_cantidad)
            elif '>' in cantidad:
                min_cantidad = cantidad.replace('>', '')
                queryset = queryset.filter(cantidad__gt=min_cantidad)
            elif '<' in cantidad:
                max_cantidad = cantidad.replace('<', '')
                queryset = queryset.filter(cantidad__lt=max_cantidad)
            else:
                queryset = queryset.filter(cantidad=cantidad)
            
        if orden_compra_id is not None:
            queryset = queryset.filter(orden_compra__id=orden_compra_id)
            
        if posicion_id is not None:
            queryset = queryset.filter(posicion__id=posicion_id)
            
        if id is not None:
            queryset = queryset.filter(id=id)
        
        if liberado is not None:
            if liberado.lower() == 'true':
                queryset = queryset.filter(Q(orden_compra__isnull=True) | Q(orden_liberada=True))
            elif liberado.lower() == 'false':
                queryset = queryset.filter(Q(orden_compra__isnull=False) & Q(orden_liberada=False))

        return queryset

    @action(detail=True, methods=['get'])
    def obtener_pedidos(self, request, pk=None):
        producto = self.get_object()
        pedidos = producto.pedidos.all()

        serializer = PedidoSerializer(pedidos, many=True)

        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def obtener_inventariado(self, request):
        cantidad_total = ProductoAlmacen.objects.all().aggregate(Sum('cantidad'))['cantidad__sum']
        costo_total_pesos = ProductoAlmacen.objects.filter(divisa='MXN').aggregate(total=Sum(F('costo') * F('cantidad'), output_field=FloatField()))['total']
        costo_total_dolares = ProductoAlmacen.objects.filter(divisa='USD').aggregate(total=Sum(F('costo') * F('cantidad'), output_field=FloatField()))['total']
        pedido_total = Pedido.objects.all().aggregate(Sum('cantidad'))['cantidad__sum']

        usuarios_con_mas_pedidos = Pedido.objects.values('usuario_nombre').annotate(total_pedidos=Count('cantidad')).order_by('-total_pedidos')[:10]
        productos_mas_pedidos = Pedido.objects.values('producto_nombre').annotate(total_pedidos=Sum('cantidad')).order_by('-total_pedidos')[:10]
        fecha_con_mas_pedidos = Pedido.objects.extra({'fecha_pedido' : "date(fecha_pedido)"}).values('fecha_pedido').annotate(total_pedidos=Count('id')).order_by('-total_pedidos')[:10]
        cantidad_por_rack = ProductoAlmacen.objects.values('posicion__rack__nombre').annotate(total_productos=Sum('cantidad')).order_by('-total_productos')

        return Response({
            "cantidad_total": cantidad_total if cantidad_total else 0,
            "costo_total_pesos": costo_total_pesos if costo_total_pesos else 0.0,
            "costo_total_dolares": costo_total_dolares if costo_total_dolares else 0.0,
            "pedido_total": pedido_total if pedido_total else 0,
            "usuarios_con_mas_pedidos": usuarios_con_mas_pedidos,
            "productos_mas_pedidos": productos_mas_pedidos,
            "fecha_con_mas_pedidos": fecha_con_mas_pedidos,
            "cantidad_por_rack": cantidad_por_rack,
        })
        

    @action(detail=True, methods=['patch'])
    def actualizar_cantidad(self, request, pk=None):
        producto = self.get_object()
        nueva_cantidad = request.data.get('cantidad')
        
        if nueva_cantidad is not None:
            producto.cantidad = nueva_cantidad
            producto.save()
            return Response({'status': 'Cantidad actualizada'})
        else:
            return Response({'error': 'Cantidad no proporcionada'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'])
    def actualizar_descripcion(self, request, pk=None):
        producto = self.get_object()
        nueva_descripcion = request.data.get('descripcion')
        
        if nueva_descripcion is not None:
            producto.descripcion = nueva_descripcion
            producto.save()
            return Response({'status': 'Descripción actualizada'})
        else:
            return Response({'error': 'Descripción no proporcionada'}, status=status.HTTP_400_BAD_REQUEST)

class ServicioViewSet(viewsets.ModelViewSet):
    queryset = Servicio.objects.all()
    serializer_class = ServicioSerializer
    ordering_fields = ['nombre']
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def ultimos(self, request):
        ultimos_servicios = Servicio.objects.order_by('-id')[:10]
        serializer = self.get_serializer(ultimos_servicios, many=True)
        return Response(serializer.data)
    
    def get_queryset(self):
        queryset = Servicio.objects.all()
        search = self.request.query_params.get('search', None) # type: ignore
        if search is not None:
            queryset = queryset.filter(Q(nombre__icontains=search))
        return queryset

class ContactoViewSet(viewsets.ModelViewSet):
    queryset = Contacto.objects.all().order_by('-id')
    serializer_class = ContactoSerializer
    ordering_fields = ['nombre']
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

class RequisicionViewSet(viewsets.ModelViewSet):
    queryset = Requisicion.objects.all().order_by('-id')
    serializer_class = RequisicionSerializer
    ordering_fields = ['fecha_creacion', 'aprobado', 'usuario']
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        departamento_nombre = self.request.query_params.get('departamento', None)
        aprobado = self.request.query_params.get('aprobado', None)
        ordenado = self.request.query_params.get('ordenado', None)
        proyecto_nombre = self.request.query_params.get('proyecto', None)
        fecha_creacion = self.request.query_params.get('fecha_creacion', None)
        fecha_aprobado = self.request.query_params.get('fecha_aprobado', None)
        fecha_entrega_estimada = self.request.query_params.get('fecha_entrega_estimada', None)
        fecha_ordenado = self.request.query_params.get('fecha_ordenado', None)
        motivo = self.request.query_params.get('motivo', None)
        total = self.request.query_params.get('total', None)
        usuario_id = self.request.query_params.get('usuario', None)
        proveedor_id = self.request.query_params.get('proveedor', None)
        tipo_de_cambio = self.request.query_params.get('tipo_de_cambio', None)
        
        if fecha_creacion is not None:
            queryset = queryset.filter(fecha_creacion=fecha_creacion)
        if fecha_aprobado is not None:
            queryset = queryset.filter(fecha_aprobado=fecha_aprobado)
        if fecha_entrega_estimada is not None:
            queryset = queryset.filter(fecha_entrega_estimada=fecha_entrega_estimada)
        if fecha_ordenado is not None:
            queryset = queryset.filter(fecha_ordenado=fecha_ordenado)
        if motivo is not None:
            queryset = queryset.filter(motivo__icontains=motivo)
        if total is not None:
            queryset = queryset.filter(total=total)
        if usuario_id is not None:
            queryset = queryset.filter(usuario__id=usuario_id)
        if proveedor_id is not None:
            queryset = queryset.filter(proveedor__id=proveedor_id)
        if tipo_de_cambio is not None:
            queryset = queryset.filter(tipo_de_cambio=tipo_de_cambio)
        if departamento_nombre is not None:
            queryset = queryset.filter(usuario__departamento__nombre=departamento_nombre)
            queryset = queryset.filter(Q(proyecto__isnull=True) | Q(proyecto__nombre=''))
        if aprobado is not None:
            aprobado = aprobado.upper()
            if aprobado in dict(Requisicion.ESTADO_APROBACION).keys():
                queryset = queryset.filter(aprobado=aprobado)
        if ordenado is not None:
            if ordenado.lower() == 'true':
                queryset = queryset.filter(ordenado=True)
            elif ordenado.lower() == 'false':
                queryset = queryset.filter(ordenado=False)
        if proyecto_nombre is not None:
            queryset = queryset.filter(proyecto__nombre=proyecto_nombre)

        return queryset
    
    @action(detail=True, methods=['post'])
    def ultimas_requisiciones(self, request, pk=None):
        if pk is not None:
            ultimas_requisiciones = Requisicion.objects.filter(usuario__id=pk).order_by('-id')[:10]
            serializer = self.get_serializer(ultimas_requisiciones, many=True)
            return Response(serializer.data)
        else:
            return Response({"error": "No se proporcionó un ID de usuario."})

    @action(detail=True, methods=['get'])
    def requisiciones_rechazadas(self, request, pk=None):
        if pk is not None:
            requisiciones = Requisicion.objects.filter(usuario__id=pk, aprobado='RECHAZADO').order_by('-id')[:10]
            serializer = self.get_serializer(requisiciones, many=True)
            return Response(serializer.data)
        else:
            return Response({"error": "No se proporcionó un ID de usuario."})

    @action(detail=True, methods=['get'])
    def requisiciones_aprobadas(self, request, pk=None):
        if pk is not None:
            requisiciones = Requisicion.objects.filter(usuario__id=pk, aprobado='APROBADO').order_by('-id')[:10]
            serializer = self.get_serializer(requisiciones, many=True)
            return Response(serializer.data)
        else:
            return Response({"error": "No se proporcionó un ID de usuario."})

    @action(detail=True, methods=['post'])
    def requisiciones_departamento(self, request, pk=None):
        if pk is not None:
            requisiciones = Requisicion.objects.filter(usuario__id=pk, proyecto__isnull=True).order_by('-id')[:10]
            serializer = self.get_serializer(requisiciones, many=True)
            return Response(serializer.data)
        else:
            return Response({"error": "No se proporcionó un ID de usuario."})

    @action(detail=True, methods=['post'])
    def requisiciones_proyecto(self, request, pk=None):
        if pk is not None:
            requisiciones = Requisicion.objects.filter(usuario__id=pk, proyecto__isnull=False).order_by('-id')[:10]
            serializer = self.get_serializer(requisiciones, many=True)
            return Response(serializer.data)
        else:
            return Response({"error": "No se proporcionó un ID de usuario."})
        
    @action(detail=True, methods=['get'])
    def requisiciones_pendientes(self, request, pk=None):
        if pk is not None:
            requisiciones = Requisicion.objects.filter(usuario__id=pk, aprobado='PENDIENTE').order_by('-id')[:10]
            serializer = self.get_serializer(requisiciones, many=True)
            return Response(serializer.data)
        else:
            return Response({"error": "No se proporcionó un ID de usuario."})

    @action(detail=True, methods=['post'])
    def update_producto(self, request, pk=None):
        requisicion = self.get_object()
        producto_data = request.data.get('producto')

        producto = requisicion.productos.get(id=producto_data.get('id'))

        producto.nombre = producto_data.get('nombre', producto.nombre)
        producto.descripcion = producto_data.get('descripcion', producto.descripcion)
        producto.cantidad = producto_data.get('cantidad', producto.cantidad)
        producto.costo = producto_data.get('costo', producto.costo)
        producto.identificador = producto_data.get('identificador', producto.identificador)
        producto.divisa = producto_data.get('divisa', producto.divisa)

        producto.save()

        return Response({'status': 'Producto actualizado'})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        archivo_pdf = self.request.data.get('archivo_pdf', None) # type: ignore
        if archivo_pdf is not None:
            serializer.save(archivo_pdf=archivo_pdf)
        else:
            serializer.save()

    @action(detail=True, methods=['get'])
    def descargar_pdf(self, request, pk=None):
        requisicion = self.get_object()
        if requisicion.archivo_pdf:
            return FileResponse(requisicion.archivo_pdf, as_attachment=True, filename='archivo.pdf')
        else:
            return Response({'error': 'No hay archivo PDF para esta requisición'}, status=404)

class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all().order_by('-id')
    serializer_class = ProveedorSerializer
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Proveedor.objects.all()
        search = self.request.query_params.get('search', None) # type: ignore
        if search is not None:
            queryset = queryset.filter(Q(nombre__icontains=search))
        return queryset

class RackViewSet(viewsets.ModelViewSet):
    queryset = Rack.objects.all()
    serializer_class = RackSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Rack.objects.all().order_by('-id')
        nombre = self.request.query_params.get('nombre', None)
        productID = self.request.query_params.get('productID', None)

        if nombre is not None:
            queryset = queryset.filter(nombre__icontains=nombre)

        if productID is not None:
            producto = ProductoAlmacen.objects.get(id=productID)
            queryset = queryset.filter(estantes__productos=producto)

        return queryset

    def list(self, request, *args, **kwargs):
        productID = request.query_params.get('productID', None)

        if productID is not None:
            producto = ProductoAlmacen.objects.get(id=productID)
            estante = Estante.objects.get(productos=producto)
            rack = self.get_queryset().get(id=estante.rack.id)
            serializer = self.get_serializer(rack)
            data = serializer.data
            data['estante'] = estante.numero
            return Response(data)

        return super().list(request, *args, **kwargs)

class EstanteViewSet(viewsets.ModelViewSet):
    queryset = Estante.objects.all().order_by('-id')
    serializer_class = EstanteSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Estante.objects.all().order_by('-id')
        
        rack_id = self.request.query_params.get('rack', None)
        estante_numero = self.request.query_params.get('estante', None)

        if rack_id is not None:
            queryset = queryset.filter(rack__id=rack_id)

        if estante_numero is not None:
            queryset = queryset.filter(numero=estante_numero)

        return queryset

class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all().order_by('-id')
    serializer_class = PedidoSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        fecha_pedido = self.request.query_params.get('fecha', None)
        usuario_nombre = self.request.query_params.get('usuario', None)
        producto_nombre = self.request.query_params.get('producto', None)
        cantidad = self.request.query_params.get('cantidad', None)

        if fecha_pedido is not None:
            try:
                if '/' in fecha_pedido:
                    fecha_desde, fecha_hasta = fecha_pedido.split('/')
                    parsed_fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d')
                    parsed_fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d')
                    queryset = queryset.filter(
                        fecha_pedido__range=(parsed_fecha_desde, parsed_fecha_hasta)
                    )
                else:
                    parsed_date = datetime.strptime(fecha_pedido, '%Y-%m-%d')
                    queryset = queryset.filter(
                        fecha_pedido__year=parsed_date.year,
                        fecha_pedido__month=parsed_date.month,
                        fecha_pedido__day=parsed_date.day
                    )
            except ValueError:
                queryset = queryset.none()
            
        if usuario_nombre is not None:
            queryset = queryset.filter(usuario_nombre__icontains=usuario_nombre)
            
        if producto_nombre is not None:
            queryset = queryset.filter(producto_nombre__icontains=producto_nombre)
            
        if cantidad is not None:
            if '>' in cantidad and '<' in cantidad:
                min_cantidad, max_cantidad = cantidad.split('<')
                min_cantidad = min_cantidad.replace('>', '')
                queryset = queryset.filter(cantidad__gt=min_cantidad, cantidad__lt=max_cantidad)
            elif '>' in cantidad:
                min_cantidad = cantidad.replace('>', '')
                queryset = queryset.filter(cantidad__gt=min_cantidad)
            elif '<' in cantidad:
                max_cantidad = cantidad.replace('<', '')
                queryset = queryset.filter(cantidad__lt=max_cantidad)
            else:
                queryset = queryset.filter(cantidad=cantidad)

        return queryset
 
class OrdenDeCompraViewSet(viewsets.ModelViewSet):
    queryset = OrdenDeCompra.objects.all().order_by('-id')
    serializer_class = OrdenDeCompraSerializer
    ordering_fields = ['fecha_emision', 'total', 'usuario', 'id']
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
        
    def get_queryset(self):
        queryset = OrdenDeCompra.objects.all().order_by('-id')

        # Optimización: Usar select_related y prefetch_related para reducir consultas
        queryset = queryset.select_related(
            'proveedor',  # Relación ForeignKey
            'requisicion',  # Relación ForeignKey
            'usuario',  # Relación ForeignKey
        ).prefetch_related(
            'requisicion__productos',  # Relación ManyToMany o Reverse ForeignKey
            'requisicion__servicios',  # Relación ManyToMany o Reverse ForeignKey
        )

        # Filtros existentes
        id = self.request.query_params.get('id', None)
        fecha_inicio = self.request.query_params.get('fecha_inicio', None)
        fecha_fin = self.request.query_params.get('fecha_fin', None)
        orden_recibida = self.request.query_params.get('orden', None)
        proveedor_nombre = self.request.query_params.get('proveedor', None)
        requisicion_id = self.request.query_params.get('requisicion', None)
        usuario_username = self.request.query_params.get('usuario', None)
        estado = self.request.query_params.get('estado', None)
        recibido = self.request.query_params.get('recibido', None)
        limit = self.request.query_params.get('limit', None)
        hayEntrega = self.request.query_params.get('hayEntrega', None)
        anio = self.request.query_params.get('anio', None)  # Nuevo filtro de año


        if id is not None:
            queryset = queryset.annotate(id_str=Cast('id', CharField())).filter(id_str__icontains=id)

        # Filtro por año de emisión
        if anio is not None:
            try:
                anio = int(anio)
                queryset = queryset.annotate(anio_emision=ExtractYear('fecha_emision')).filter(anio_emision=anio)
            except ValueError:
                pass  # Ignorar si el valor de anio no es válido
            
        if hayEntrega is not None:
            hayEntrega = hayEntrega.lower() in ['true', '1']
            if hayEntrega:
                queryset = queryset.exclude(fecha_entrega__isnull=True)
            else:
                queryset = queryset.filter(fecha_entrega__isnull=True)
        
        if fecha_inicio is not None and fecha_fin is not None:
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
            queryset = queryset.filter(fecha_entrega__range=[fecha_inicio, fecha_fin])
        elif fecha_inicio is not None:
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            queryset = queryset.filter(fecha_entrega__gte=fecha_inicio)
        elif fecha_fin is not None:
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
            queryset = queryset.filter(fecha_entrega__lte=fecha_fin)

        if orden_recibida is not None:
            orden_recibida = orden_recibida.lower() in ['true', '1']
            queryset = queryset.filter(orden_recibida=orden_recibida)

        if proveedor_nombre is not None:
            queryset = queryset.filter(proveedor__nombre=proveedor_nombre)

        if requisicion_id is not None:
            queryset = queryset.filter(requisicion__id=requisicion_id)

        if usuario_username is not None:
            queryset = queryset.filter(usuario__username=usuario_username)

        if estado is not None:
            queryset = queryset.filter(estado=estado)
            
        if recibido is not None:
            queryset = queryset.filter(orden_recibida=recibido)
            
        if limit is not None:
            try:
                limit = int(limit)
                queryset = queryset[:limit]
            except ValueError:
                pass
        
        return queryset

    def list(self, request, *args, **kwargs):
        count = request.query_params.get('count', 'false').lower() == 'true'
        if count:
            queryset = self.filter_queryset(self.get_queryset())
            count = queryset.count()
            return Response({'ordenes': count})
        else:
            return super().list(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def actualizar_productos_recibidos(self, request, pk=None):
        orden = self.get_object()
        productos_data = request.data

        productos_almacen = []
        print("Received data:", productos_data)


        for producto_data in productos_data:
            id_producto = producto_data.get('id')
            cantidad_recibida = Decimal(producto_data.get('cantidad_recibida'))

            producto_requisicion = get_object_or_404(orden.requisicion.productos, id=id_producto)

            producto_requisicion.cantidad_recibida += cantidad_recibida
            producto_requisicion.save()

            producto_almacen, created = ProductoAlmacen.objects.get_or_create(
                orden_compra=orden,
                nombre=producto_requisicion.nombre,
                defaults={
                    'identificador': producto_requisicion.identificador,
                    'descripcion': producto_requisicion.descripcion,
                    'costo': producto_requisicion.costo,
                    'cantidad': Decimal('0.00')
                }
            )

            producto_almacen.cantidad += cantidad_recibida
            producto_almacen.save()

            productos_almacen.append(ProductoAlmacenSerializer(producto_almacen).data)

        todos_recibidos = all(producto.cantidad <= producto.cantidad_recibida for producto in orden.requisicion.productos.all())

        if todos_recibidos:
            orden.orden_recibida = False
            orden.estado = "EN CAMINO"
            orden.save()

        orden = self.get_object()

        serializer = self.get_serializer(orden)
        data = serializer.data
        data['productos_almacen'] = productos_almacen
        return Response(data)

    @action(detail=False, methods=['post'])
    def exportar(self, request):
        try:
            data = request.data
            variables = data

            subtotal = Decimal(0)
            for i in range(len(data['requisicion_detail']['productos'])):
                costo = Decimal(data['requisicion_detail']['productos'][i]['costo']) * Decimal(data['requisicion_detail']['productos'][i]['cantidad'])
                subtotal += costo
                variables['requisicion_detail']['productos'][i]['costo_total'] = str(costo.quantize(Decimal('0.01'), rounding=ROUND_CEILING))

            for i in range(len(data['requisicion_detail']['servicios'])):
                subtotal += Decimal(data['requisicion_detail']['servicios'][i]['costo'])

            # Cálculo del IVA
            iva_value = Decimal(variables['proveedor_detail']['iva']) if variables['proveedor_detail']['iva'] is not None else Decimal(0)
            iva = (subtotal * iva_value).quantize(Decimal('0.01'), rounding=ROUND_CEILING)

            # Obtener régimen fiscal, tipo de persona y si es servicio profesional o no comercial
            regimen_fiscal = variables['proveedor_detail'].get('regimen_fiscal', '')
            tipo_persona = variables['proveedor_detail'].get('tipo_persona', '')
            servicio_profesional_no_comercial = variables['proveedor_detail'].get('servicio_profesional_no_comercial', False)

            # Cálculo del IVA Retenido
            if (
                regimen_fiscal == 'Régimen Simplificado de Confianza' 
                and tipo_persona == 'FISICA' 
                and servicio_profesional_no_comercial
            ):
                iva_retenido = (iva / 3 * 2).quantize(Decimal('0.01'), rounding=ROUND_CEILING) if iva > 0 else Decimal(0)
            else:
                iva_retenido = Decimal(0)

            # Cálculo del ISR Retenido
            isr_retenido_value = Decimal(variables['proveedor_detail']['isr_retenido']) if variables['proveedor_detail']['isr_retenido'] is not None else Decimal(0)
            isr_retenido = (subtotal * isr_retenido_value).quantize(Decimal('0.01'), rounding=ROUND_FLOOR)

            # Cálculo del total
            total = subtotal + iva - isr_retenido - iva_retenido
            total_decimal = total % 1  # Obtiene los decimales del total

            # Si el total tiene decimales entre .98 y .99, se redondea hacia arriba
            if total_decimal >= Decimal('0.98'):
                total = total.quantize(Decimal('1'), rounding=ROUND_CEILING)
            else:
                total = total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Asignar valores formateados con 2 decimales
            variables['subtotal'] = str(subtotal.quantize(Decimal('0.01'), rounding=ROUND_CEILING))
            variables['iva'] = str(iva)
            variables['isr_retenido'] = str(isr_retenido)
            variables['iva_retenido'] = str(iva_retenido)
            variables['total'] = str(total)

            # 🔹 **Determinar la divisa correcta**
            divisa = variables.get('divisa', None)

            if not divisa or divisa == 'No especificado':  # Si no hay divisa, buscar en los productos o servicios
                if variables['requisicion_detail']['productos']:
                    divisa = variables['requisicion_detail']['productos'][0].get('divisa', 'No especificado')
                elif variables['requisicion_detail']['servicios']:
                    divisa = variables['requisicion_detail']['servicios'][0].get('divisa', 'No especificado')

            # 🔹 **Actualizar la Orden de Compra con el total calculado y la divisa**
            requisicion_id = variables.get('requisicion_detail', {}).get('id')

            if requisicion_id:
                try:
                    orden_compra = OrdenDeCompra.objects.get(requisicion_id=requisicion_id)
                    orden_compra.total = total  # Asignamos el total calculado
                    orden_compra.divisa = divisa  # Asignamos la divisa obtenida correctamente
                    orden_compra.save()  # Guardamos cambios en la base de datos
                except OrdenDeCompra.DoesNotExist:
                    return Response({'error': 'No se encontró la Orden de Compra para la requisición proporcionada'}, status=status.HTTP_404_NOT_FOUND)


            # Verificación de crédito
            credito_value = variables['proveedor_detail']['credito']
            variables['hay_credito'] = "Credito disponible" if credito_value is not None and Decimal(credito_value) > 0 else "Sin credito disponible"

            # Determinar la divisa si no hay productos o servicios
            if not variables['requisicion_detail']['productos']:
                variables['divisa'] = variables['requisicion_detail']['servicios'][0]['divisa']

            if not variables['requisicion_detail']['servicios']:
                variables['divisa'] = variables['requisicion_detail']['productos'][0]['divisa']

            # Generación del nombre del archivo PDF
            username = data.get("usuario_detail", {}).get("username")
            username = username.lower().replace(' ', '_')
            id = variables['id']
            variables['usuario_detail']['username'] = username

            pdf_file_name = f'OC_{id}_{username}.pdf'

            pdf_relative_path = os.path.join('pdfs', pdf_file_name)
            pdf_full_path = os.path.join(settings.MEDIA_ROOT, pdf_relative_path)
            pdf_media_url = os.path.join(settings.MEDIA_URL, pdf_relative_path)

            # Renderizado del HTML con Jinja2
            template_dir = os.path.join(settings.BASE_DIR, 'ri_compras', 'templates')
            env = Environment(loader=FileSystemLoader(template_dir))
            template = env.get_template('miTabla.html')

            html_content = template.render(variables=variables)

            # Creación del PDF
            pdf_buffer = BytesIO()
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)

            if pisa_status.err:  # type: ignore
                print("Error al generar el PDF")
            else:
                with open(pdf_full_path, 'wb') as pdf_file:
                    pdf_file.write(pdf_buffer.getvalue())

                return Response({'pdf_link': pdf_media_url})

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def crear_cuenta_por_pagar(self, request, pk=None):
        orden = self.get_object()
        # Obtenemos datos necesarios
        requisicion = orden.requisicion
        proveedor = orden.proveedor
        
        if not proveedor:
            return Response({'error': 'La orden no tiene proveedor asignado.'}, status=status.HTTP_400_BAD_REQUEST)

        # proyecto y departamento
        proyecto = requisicion.proyecto if requisicion else None
        departamento = requisicion.usuario.departamento if requisicion and requisicion.usuario else None

        # Dias de crédito del proveedor
        try:
            dias_credito = int(float(proveedor.dias_de_credito.split()[0]))  # si "30 Dias", tomamos el primer valor "30"
        except:
            dias_credito = 0

        # Crear el registro en CuentaPorPagarProveedor
        cuenta = CuentaPorPagarProveedor.objects.create(
            orden=orden,
            fecha_cfdi=orden.fecha_cfdi,
            proveedor=proveedor,
            proyecto=proyecto,
            departamento=departamento,
            folio_factura=orden.folio_factura,
            dias_de_credito=dias_credito,
            fecha_contrarecibo=orden.fecha_contrarecibo,
            total_factura=orden.total_factura if orden.total_factura else Decimal('0.00'),
            divisa=orden.divisa,
            estatus='inicial',  # valor inicial
            # saldo_pendiente se calcula en el save()
            # propuesta_pago por defecto 0.00
        )

        return Response({
            'message': 'Cuenta por pagar creada exitosamente',
            'cuenta_id': cuenta.id,
            'saldo_pendiente': str(cuenta.saldo_pendiente),
            'estatus': cuenta.estatus,
        }, status=status.HTTP_201_CREATED)
    

    @action(detail=True, methods=['post'])
    def crear_cuenta_por_pagar_a_contado(self, request, pk=None):
        orden = self.get_object()
        # Obtenemos datos necesarios
        json_data = request.data.get('json_data')
        if json_data:
            try:
                data = json.loads(json_data)  # Parsear el JSON
                fecha_pago_str = data.get('fecha_pago')
                total_factura = data.get('total_factura')
                pago_a_contado = data.get('pago_a_contado')
                folio_factura = data.get('folio_factura')
            except json.JSONDecodeError:
                return Response({'error': 'JSON mal formado.'}, status=400)
        else:
            return Response({'error': 'Falta el campo json_data.'}, status=400)

        # Extraer el archivo PDF
        factura_pdf = request.FILES.get('factura_pdf')
        if not factura_pdf:
            return Response({'error': 'Falta el archivo de factura PDF.'}, status=400)

        requisicion = orden.requisicion
        proveedor = orden.proveedor
        
        if not proveedor:
            return Response({'error': 'La orden no tiene proveedor asignado.'}, status=status.HTTP_400_BAD_REQUEST)

        # proyecto y departamento
        proyecto = requisicion.proyecto if requisicion else None
        departamento = requisicion.usuario.departamento if requisicion and requisicion.usuario else None
        
        if fecha_pago_str:
            try:
                fecha_pago = datetime.fromisoformat(fecha_pago_str).date()
            except ValueError:
                return Response({'error': 'Formato de fecha inválido. Debe ser YYYY-MM-DD o ISO8601.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            fecha_pago = None  # o manejar como error


        # Crear el registro en CuentaPorPagarProveedor
        cuenta = CuentaPorPagarProveedor.objects.create(
            orden=orden,
            fecha_cfdi=orden.fecha_cfdi,
            proveedor=proveedor,
            proyecto=proyecto,
            departamento=departamento,
            folio_factura=folio_factura,
            dias_de_credito='0',
            fecha_pago=fecha_pago,
            fecha_contrarecibo=fecha_pago,
            total_factura=total_factura if total_factura else Decimal('0.00'),
            factura_pdf=factura_pdf,
            pago_a_contado=pago_a_contado,
            divisa=orden.divisa,
            estatus='inicial', # valor inicial
            # saldo_pendiente se calcula en el save()
            # propuesta_pago por defecto 0.00
        )

        return Response({
            'message': 'Cuenta por pagar creada exitosamente',
            'cuenta_id': cuenta.id,
            'saldo_pendiente': str(cuenta.saldo_pendiente),
            'estatus': cuenta.estatus,
        }, status=status.HTTP_201_CREATED)
        
    @action(detail=True, methods=['get'])
    def cuentas_por_pagar_orden(self, request, pk=None):
        orden_id = pk
        logging.debug(f'ID de la orden: {orden_id}')
        cuentas = CuentaPorPagarProveedor.objects.filter(orden_id=orden_id)
        logging.debug(f'Cuentas por pagar: {cuentas}')
        serializer = CuentaPorPagarProveedorSerializer(cuentas, many=True)
        return Response(serializer.data)
    

class ReciboViewSet(viewsets.ModelViewSet):
    queryset = Recibo.objects.all()
    serializer_class = ReciboSerializer
    
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all().order_by('-id')
    serializer_class = MessageSerializer
    
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__username']

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

class PropuestaCxCViewSet(viewsets.ModelViewSet):
    queryset = CuentaPorCobrar.objects.all().order_by('-id')
    serializer_class = PropuestaCxCSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['razon_social', 'responsable', 'oc_po']
    ordering_fields = ['fecha_oc_po', 'importe_total_facturado_con_iva']
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related('detalles')

        razon_social = self.request.query_params.get('razon_social', None)
        estatus = self.request.query_params.get('estatus', None)
        divisa = self.request.query_params.get('divisa', None)
        dias_vencidos = self.request.query_params.get('dias_vencidos', None)
        xml_cancelacion = self.request.query_params.get('xml_cancelacion', None)

        if razon_social:
            queryset = queryset.filter(razon_social__icontains=razon_social)
        if estatus:
            queryset = queryset.filter(estatus=estatus)
        if divisa:
            queryset = queryset.filter(divisa=divisa)
        if dias_vencidos:
            queryset = queryset.filter(dias_vencidos__lte=dias_vencidos)
        if xml_cancelacion:
            queryset = queryset.filter(xml_cancelacion=xml_cancelacion)

        return queryset

    @action(detail=True, methods=['get'])
    def detalles(self, request, pk=None):
        propuesta = self.get_object()
        detalles = DetalleCxC.objects.filter(propuesta_cxc=propuesta)
        serializer = DetalleCxCSerializer(detalles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def totales(self, request):
        totales = CuentaPorCobrar.objects.aggregate(
            total_facturado=Sum('importe_total_facturado'),  # Sin multiplicar por la divisa
            total_saldo=Sum('saldo')  # Sin multiplicar por la divisa
        )
        return Response(totales)

    @action(detail=True, methods=['patch'])
    def cambiar_estatus(self, request, pk=None):
        propuesta = self.get_object()
        nuevo_estatus = request.data.get('estatus')
        
        if nuevo_estatus not in dict(CuentaPorCobrar.ESTATUS_CHOICES):
            return Response({'error': 'Estatus no válido.'}, status=400)

        propuesta.estatus = nuevo_estatus
        propuesta.save()

        return Response({'status': 'Estatus actualizado correctamente', 'nuevo_estatus': nuevo_estatus})
    
    #Nueva acción para cancelar cuenta por cobrar
    @action(detail=True, methods=['patch'])
    def cambiar_a_cancelada(self, request, pk=None):
        propuesta = self.get_object()
        nuevo_estatus = request.data.get('estatus')
        nuevo_xml_cancelacion = request.data.get('xml_cancelacion')

        if nuevo_estatus not in dict(CuentaPorCobrar.ESTATUS_CHOICES):
            return Response({'error': 'Estatus no válido.'}, status=400)
        
        propuesta.estatus = nuevo_estatus
        propuesta.xml_cancelacion = nuevo_xml_cancelacion
        propuesta.save()

        return Response({'status': 'Cuenta por cobrar cancelada correctamente', 'nuevo_estatus': nuevo_estatus})
    
    # Nueva acción para obtener el porcentaje de facturación restante
    @action(detail=False, methods=['get'], url_path='facRestante')
    def calcular_facturacion_restante(self, request):
        razon_social = request.query_params.get('razon_social')
        oc_po = request.query_params.get('oc_po')

        if not razon_social or not oc_po:
            return Response({'error': 'razon_social y oc_po son requeridos'}, status=400)

        porcentaje_restante = CuentaPorCobrar.calcular_facturacion_restante(razon_social, oc_po)
        return Response({'porcentaje_restante': porcentaje_restante})
    
    @action(detail=False, methods=['get'], url_path='saldo-total-sl', url_name='saldo_total_sl')
    def saldo_total_por_divisa_semana_laboral(self, request):
        """
        Endpoint para calcular el saldo total de cuentas por cobrar (basado en importe_total_facturado)
        por semana laboral.
        """
        today = now().date()
        start_of_week = today - timedelta(days=today.weekday())  # Lunes
        end_of_week = start_of_week + timedelta(days=6)  # Domingo

        # Filtrar registros de la semana laboral usando fecha_programada_pago
        cuentas_filtradas = CuentaPorCobrar.objects.filter(
            fecha_programada_pago__range=(start_of_week, end_of_week)
        )

        # Sumar los totales por divisa usando importe_total_facturado
        saldo_mxn = cuentas_filtradas.filter(divisa='MXN').aggregate(
            total_mxn=Sum('importe_pago')
        )['total_mxn'] or 0

        saldo_usd = cuentas_filtradas.filter(divisa='USD').aggregate(
            total_usd=Sum('importe_pago')
        )['total_usd'] or 0

        return Response({
            'saldo_total': {
                'MXN': saldo_mxn,
                'USD': saldo_usd,
            }
        }, status=200)

class DetalleCxCViewSet(viewsets.ModelViewSet):
    queryset = DetalleCxC.objects.all().order_by('-id')
    serializer_class = DetalleCxCSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['referencia_transferencia']
    ordering_fields = ['fecha_pago', 'abono']
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset().select_related('propuesta_cxc')
        
        propuesta_id = self.request.query_params.get('propuesta', None)
        referencia_transferencia = self.request.query_params.get('referencia_transferencia', None)
        fecha_pago = self.request.query_params.get('fecha_pago', None)

        if propuesta_id:
            queryset = queryset.filter(propuesta_cxc_id=propuesta_id)
        if referencia_transferencia:
            queryset = queryset.filter(referencia_transferencia__icontains=referencia_transferencia)
        if fecha_pago:
            queryset = queryset.filter(fecha_pago=fecha_pago)

        return queryset
    
# ViewSet para el modelo CreditoPrestamo
class CreditoPrestamoViewSet(viewsets.ModelViewSet):
    queryset = CreditoPrestamo.objects.all().order_by('-fecha_realizacion')
    serializer_class = CreditoPrestamoSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['emisor', 'receptor', 'numero_transaccion']
    ordering_fields = ['fecha_vencimiento', 'importe', 'estatus']

    def list(self, request, *args, **kwargs):
        """
        Al obtener la lista de créditos, actualizamos la fecha de vencimiento de cada crédito
        según el estado de sus cuotas:
        - Si todas las cuotas están pagadas, usamos la fecha de la última cuota pagada.
        - Si todas están pendientes, usamos la fecha de la primera cuota.
        - Si hay una mezcla de cuotas pagadas y pendientes, usamos la fecha de la primera cuota pendiente.
        """
        for credito_prestamo in self.queryset:
            amortizaciones = credito_prestamo.amortizaciones.order_by('numero_mes')
            cuotas_pendientes = amortizaciones.filter(estatus_pago='pendiente')
            cuotas_pagadas = amortizaciones.filter(estatus_pago='pagado')

            if cuotas_pendientes.exists() and cuotas_pagadas.exists():
                # Caso con cuotas pagadas y pendientes: tomar la fecha de la primera cuota pendiente
                nueva_fecha_vencimiento = cuotas_pendientes.first().fecha_pago_programada
            elif cuotas_pagadas.exists() and not cuotas_pendientes.exists():
                # Caso con todas las cuotas pagadas: tomar la fecha de la última cuota pagada
                nueva_fecha_vencimiento = cuotas_pagadas.last().fecha_pago_programada
            elif cuotas_pendientes.exists() and not cuotas_pagadas.exists():
                # Caso con todas las cuotas pendientes: tomar la fecha de la primera cuota pendiente
                nueva_fecha_vencimiento = cuotas_pendientes.first().fecha_pago_programada
            else:
                # No hay cuotas disponibles (no debería ocurrir en un caso normal)
                nueva_fecha_vencimiento = credito_prestamo.fecha_vencimiento

            # Actualizar la fecha de vencimiento si es diferente
            if nueva_fecha_vencimiento != credito_prestamo.fecha_vencimiento:
                credito_prestamo.fecha_vencimiento = nueva_fecha_vencimiento
                credito_prestamo.save(update_fields=['fecha_vencimiento'])

        # Procesar la lista como normalmente se haría
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    

    def create(self, request, *args, **kwargs):
        """
        Crear un nuevo crédito y generar la tabla de amortización.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            credito_prestamo = serializer.save()
            # Generar tabla de amortización automáticamente
            credito_prestamo.crear_abono()
            credito_prestamo.generar_tabla_amortizacion()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=True, methods=['get'], url_path='amortizacion')
    def generar_amortizacion(self, request, pk=None):
        """
        Genera la tabla de amortización para un crédito específico y recalcula si hay pagos morosos.
        Recalcula el balance restante y el capital de las siguientes cuotas si una es marcada como morosa.
        Las cuotas pagadas no se recalculan.
        """
        try:
            credito_prestamo = self.get_object()
        except CreditoPrestamo.DoesNotExist:
            return Response({'error': 'Crédito no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        amortizaciones = credito_prestamo.amortizaciones.all().order_by('numero_mes')

        fecha_actual = timezone.now().date()
        recalculated_amortizations = []

        saldo_restante = credito_prestamo.importe
        tasa_interes_moratorio = (credito_prestamo.tasa_interes_moratorio or 0) / 100 / 12  # Tasa mensual moratoria
        tasa_interes_normal = (credito_prestamo.tasa_interes_normal or 0) / 100 / 12  # Tasa mensual normal

        # Definir la tasa del IVA como Decimal
        iva_tasa = Decimal('0.16')  # IVA del 16%

        recalcular = False

        for amortizacion in amortizaciones:
            if amortizacion.estatus_pago == 'pagado':
                saldo_restante -= amortizacion.principal
                recalculated_amortizations.append(amortizacion)
                continue

            if amortizacion.fecha_pago_programada < fecha_actual and amortizacion.estatus_pago == 'pendiente':
                amortizacion.estatus_pago = 'moroso'
                amortizacion.interes_moratorio = saldo_restante * tasa_interes_moratorio
                amortizacion.interes = 0
                amortizacion.iva_interes = amortizacion.interes_moratorio * iva_tasa  # Calcular IVA sobre interés moratorio
                amortizacion.pago = amortizacion.principal + amortizacion.interes_moratorio + amortizacion.iva_interes
                recalcular = True
            else:
                if recalcular:
                    amortizacion.interes = saldo_restante * tasa_interes_normal
                    amortizacion.iva_interes = amortizacion.interes * iva_tasa  # IVA sobre el interés normal
                    amortizacion.interes_moratorio = 0
                    amortizacion.pago = amortizacion.principal + amortizacion.interes + amortizacion.iva_interes

            saldo_restante -= amortizacion.principal
            amortizacion.balance_restante = max(0, saldo_restante)

            amortizacion.save()

            recalculated_amortizations.append(amortizacion)

        # Serializar y devolver la tabla de amortización recalculada
        serializer = AmortizacionCuotaSerializer(recalculated_amortizations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cambiar_estatus(self, request, pk=None):
        """
        Cambiar el estatus de un crédito.
        """
        credito_prestamo = self.get_object()
        nuevo_estatus = request.data.get('estatus')
        if nuevo_estatus in [choice[0] for choice in CreditoPrestamo.ESTATUS_CHOICES]:
            credito_prestamo.estatus = nuevo_estatus
            credito_prestamo.save()
            return Response({'status': 'Estatus actualizado'}, status=status.HTTP_200_OK)
        return Response({'error': 'Estatus inválido'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def totales_por_tipo_y_divisa(self, request):
        # Define una función para obtener el balance_restante del último mes pagado de cada crédito
        def obtener_capital_restante(queryset):
            # Subconsulta para obtener el balance_restante del último mes pagado
            ultimo_balance_subquery = AmortizacionCuota.objects.filter(
                credito_prestamo=OuterRef('pk'),
                estatus_pago='pagado'
            ).order_by('-numero_mes').values('balance_restante')[:1]

            # Anotamos el balance_restante correspondiente al último mes pagado o el importe total si no hay pagos
            queryset = queryset.annotate(
                ultimo_balance_restante=Coalesce(Subquery(ultimo_balance_subquery), F('importe'))
            )

            # Sumamos todos los balances restantes anotados como capital restante total
            return queryset.aggregate(
                total_capital_restante=Coalesce(Sum('ultimo_balance_restante'), Decimal(0))
            )['total_capital_restante']

        # Calcular los totales de importes y capital restante por tipo y divisa
        total_creditos_mxn = CreditoPrestamo.objects.filter(tipo_transaccion='credito', divisa='MXN').aggregate(
            total_importe=Sum('importe')
        )['total_importe'] or Decimal(0)
        total_creditos_usd = CreditoPrestamo.objects.filter(tipo_transaccion='credito', divisa='USD').aggregate(
            total_importe=Sum('importe')
        )['total_importe'] or Decimal(0)

        # Préstamos emitidos y recibidos
        prestamos_emitidos_mxn = CreditoPrestamo.objects.filter(
            tipo_transaccion='prestamo', emitido_recibido='emitido', divisa='MXN'
        )
        prestamos_emitidos_usd = CreditoPrestamo.objects.filter(
            tipo_transaccion='prestamo', emitido_recibido='emitido', divisa='USD'
        )
        prestamos_recibidos_mxn = CreditoPrestamo.objects.filter(
            tipo_transaccion='prestamo', emitido_recibido='recibido', divisa='MXN'
        )
        prestamos_recibidos_usd = CreditoPrestamo.objects.filter(
            tipo_transaccion='prestamo', emitido_recibido='recibido', divisa='USD'
        )

        # Obtener totales de capital restante para cada conjunto
        creditos_mxn_restante = obtener_capital_restante(CreditoPrestamo.objects.filter(tipo_transaccion='credito', divisa='MXN'))
        creditos_usd_restante = obtener_capital_restante(CreditoPrestamo.objects.filter(tipo_transaccion='credito', divisa='USD'))
        prestamos_emitidos_mxn_restante = obtener_capital_restante(prestamos_emitidos_mxn)
        prestamos_emitidos_usd_restante = obtener_capital_restante(prestamos_emitidos_usd)
        prestamos_recibidos_mxn_restante = obtener_capital_restante(prestamos_recibidos_mxn)
        prestamos_recibidos_usd_restante = obtener_capital_restante(prestamos_recibidos_usd)

        # Calcular intereses insolutos por cada conjunto
        def calcular_intereses_insolutos(queryset):
            return queryset.filter(amortizaciones__estatus_pago__in=['pendiente', 'moroso']).aggregate(
                total_intereses_insolutos=Coalesce(
                    Sum('amortizaciones__interes') + Sum('amortizaciones__interes_moratorio'),
                    Decimal(0)
                )
            )['total_intereses_insolutos']

        creditos_mxn_intereses = calcular_intereses_insolutos(CreditoPrestamo.objects.filter(tipo_transaccion='credito', divisa='MXN'))
        creditos_usd_intereses = calcular_intereses_insolutos(CreditoPrestamo.objects.filter(tipo_transaccion='credito', divisa='USD'))
        prestamos_emitidos_mxn_intereses = calcular_intereses_insolutos(prestamos_emitidos_mxn)
        prestamos_emitidos_usd_intereses = calcular_intereses_insolutos(prestamos_emitidos_usd)
        prestamos_recibidos_mxn_intereses = calcular_intereses_insolutos(prestamos_recibidos_mxn)
        prestamos_recibidos_usd_intereses = calcular_intereses_insolutos(prestamos_recibidos_usd)

        # Preparar el resultado para la respuesta
        return Response({
            'creditos': {
                'MXN': {
                    'total_importe': total_creditos_mxn,
                    'total_capital_restante': creditos_mxn_restante,
                    'total_intereses_insolutos': creditos_mxn_intereses
                },
                'USD': {
                    'total_importe': total_creditos_usd,
                    'total_capital_restante': creditos_usd_restante,
                    'total_intereses_insolutos': creditos_usd_intereses
                }
            },
            'prestamos_emitidos': {
                'MXN': {
                    'total_importe': prestamos_emitidos_mxn.aggregate(total_importe=Sum('importe'))['total_importe'] or Decimal(0),
                    'total_capital_restante': prestamos_emitidos_mxn_restante,
                    'total_intereses_insolutos': prestamos_emitidos_mxn_intereses
                },
                'USD': {
                    'total_importe': prestamos_emitidos_usd.aggregate(total_importe=Sum('importe'))['total_importe'] or Decimal(0),
                    'total_capital_restante': prestamos_emitidos_usd_restante,
                    'total_intereses_insolutos': prestamos_emitidos_usd_intereses
                }
            },
            'prestamos_recibidos': {
                'MXN': {
                    'total_importe': prestamos_recibidos_mxn.aggregate(total_importe=Sum('importe'))['total_importe'] or Decimal(0),
                    'total_capital_restante': prestamos_recibidos_mxn_restante,
                    'total_intereses_insolutos': prestamos_recibidos_mxn_intereses
                },
                'USD': {
                    'total_importe': prestamos_recibidos_usd.aggregate(total_importe=Sum('importe'))['total_importe'] or Decimal(0),
                    'total_capital_restante': prestamos_recibidos_usd_restante,
                    'total_intereses_insolutos': prestamos_recibidos_usd_intereses
                }
            }
        }, status=status.HTTP_200_OK)
        

# ViewSet para el modelo PagoCreditoPrestamo
class PagoCreditoPrestamoViewSet(viewsets.ModelViewSet):
    queryset = PagoCreditoPrestamo.objects.all().order_by('-fecha_pago')
    serializer_class = PagoCreditoPrestamoSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    filter_backends = [filters.SearchFilter]
    search_fields = ['amortizacion_cuota__credito_prestamo']

        
    def create(self, request, *args, **kwargs):
        """
        Crear un nuevo pago y aplicarlo a la cuota correspondiente.
        Si es el último pago pendiente del crédito, cambia su estatus a "pagado".
        """
        cuota_id = request.data.get('amortizacion_cuota')
        abono = Decimal(request.data.get('abono', '0'))

        try:
            cuota = AmortizacionCuota.objects.get(pk=cuota_id)
        except AmortizacionCuota.DoesNotExist:
            return Response({'error': 'Cuota de amortización no encontrada'}, status=status.HTTP_404_NOT_FOUND)

        # Aplicar el abono y obtener el excedente
        excedente_abono = cuota.aplicar_pago(abono)

        # Recalcular cuotas posteriores si hay un excedente
        if excedente_abono > 0:
            nuevo_balance_restante = cuota.balance_restante - excedente_abono
            cuota.recalcular_cuotas_posteriores(cuota.numero_mes, nuevo_balance_restante)

        # Ajuste final en la cuota en la que se realizó el pago:
        cuota.principal += excedente_abono
        cuota.balance_restante -= excedente_abono
        cuota.pago = cuota.principal + cuota.interes + cuota.iva_interes
        cuota.save()

        # Crear el registro de pago en la base de datos
        response = super().create(request, *args, **kwargs)

        # Verificar si todas las cuotas de este crédito están pagadas
        credito = cuota.credito_prestamo
        cuotas_pendientes = credito.amortizaciones.filter(estatus_pago='pendiente')

        if not cuotas_pendientes.exists():  # Si ya no hay cuotas pendientes
            credito.estatus = 'pagado'
            credito.save(update_fields=['estatus'])

        return response
    
    def destroy(self, request, *args, **kwargs):
        """
        Eliminar un pago y recalcular el saldo de la cuota correspondiente.
        """
        pago = self.get_object()
        cuota = pago.amortizacion_cuota

        response = super().destroy(request, *args, **kwargs)

        total_abonos = cuota.pagos.aggregate(Sum('abono'))['abono__sum'] or Decimal(0)
        cuota.balance_restante = cuota.principal + cuota.interes + cuota.interes_moratorio - total_abonos
        cuota.save()

        return response

    def list(self, request, *args, **kwargs):
        """
        Listar todos los pagos realizados, filtrados por `credito_prestamo`.
        """
        # Verificar si se proporciona el parámetro `credito_prestamo` en la URL
        credito_prestamo_id = request.query_params.get('credito_prestamo')

        if credito_prestamo_id:
            # Filtrar pagos solo para el `credito_prestamo` especificado
            self.queryset = self.queryset.filter(amortizacion_cuota__credito_prestamo_id=credito_prestamo_id)

        # Serializar y devolver los datos filtrados
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
        Actualizar parcialmente un pago.
        """
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='pago-a-capital-con-reduccion-terminos')
    def pago_a_capital_con_reduccion_terminos(self, request, pk=None):
        """
        Realiza un abono a capital, ajusta el registro de la cuota, elimina términos no utilizados,
        registra el pago, marca la cuota como pagada y recalcula las cuotas restantes.
        """
        cuota_id = request.data.get('amortizacion_cuota')
        abono = Decimal(request.data.get('abono', '0'))
        nuevos_terminos = int(request.data.get('nuevos_terminos', 0))

        # Validación de abono positivo y términos adecuados
        if abono <= 0:
            return Response({'error': 'El abono debe ser mayor a cero'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cuota = AmortizacionCuota.objects.get(pk=cuota_id)
            credito_prestamo = cuota.credito_prestamo
        except AmortizacionCuota.DoesNotExist:
            return Response({'error': 'Cuota de amortización no encontrada'}, status=status.HTTP_404_NOT_FOUND)

        # Validación del número de términos
        if nuevos_terminos >= credito_prestamo.termino or nuevos_terminos < 1:
            return Response({'error': f'El número de términos debe ser menor a {credito_prestamo.termino} y mayor a 1'}, status=status.HTTP_400_BAD_REQUEST)

        if nuevos_terminos == 1:
            credito = cuota.credito_prestamo
            logging.debug(f"EstaPagado")
            credito.estatus = 'pagado'
            credito.save(update_fields=['estatus'])

        with transaction.atomic():
            # Calcular la diferencia entre el pago actual y el abono recibido
            diferencia = abono - cuota.pago
            
            # Actualizar el principal sumando la diferencia
            cuota.principal += diferencia

            # Ajustar el balance restante restando la diferencia
            cuota.balance_restante -= diferencia

            # Recalcular el pago con principal, interes, interes moratorio e IVA sobre interes
            cuota.pago = cuota.principal + cuota.interes + cuota.interes_moratorio + cuota.iva_interes
            cuota.save()

            # Actualizar el crédito con el nuevo número de términos
            credito_prestamo.termino = nuevos_terminos
            credito_prestamo.save()

            # Eliminar los términos no utilizados (los que excedan el nuevo número de términos)
            credito_prestamo.amortizaciones.filter(numero_mes__gt=nuevos_terminos).delete()

            # Crear el registro del pago en la base de datos
            pago_data = {
                'amortizacion_cuota': cuota,  # Asignación directa de instancia
                'abono': abono,
                'fecha_pago': request.data.get('fecha_pago'),
                'referencia_transferencia': request.data.get('referencia_transferencia'),
                'pdf': request.data.get('pdf'),
                'tipo_de_pago': request.get('tipo_de_pago'),
                'numero_tarjeta': request.get('numero_tarjeta'),
                'tipo_tarjeta': request.get('tipo_tarjeta'),
                'numero_cuenta': request.get('numero_cuenta'),
            }
            PagoCreditoPrestamo.objects.create(**pago_data)
            PagoCreditoPrestamo.save()

            # Marcar la cuota como "pagada"
            cuota.estatus_pago = 'pagado'
            cuota.save()

            # Recalculo de las cuotas restantes usando el balance restante de la cuota actual como nuevo capital
            saldo_restante = cuota.balance_restante
            tasa_interes_mensual = Decimal(credito_prestamo.tasa_interes_normal or 0) / Decimal(100) / 12
            iva_tasa = Decimal('0.16')  # IVA del 16%
            
            # Calcular el pago mensual ajustado para las cuotas restantes
            n = min(nuevos_terminos, credito_prestamo.amortizaciones.filter(numero_mes__gt=cuota.numero_mes).count())
            if n > 0:
                pago_mensual = (saldo_restante * tasa_interes_mensual / (1 - (1 + tasa_interes_mensual) ** -n)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                cuotas_pendientes = credito_prestamo.amortizaciones.filter(
                    estatus_pago__in=['pendiente', 'moroso'],
                    numero_mes__gt=cuota.numero_mes
                ).order_by('numero_mes')

                for i, cuota_pendiente in enumerate(cuotas_pendientes, start=1):
                    # Calcular interés e IVA sobre el saldo restante
                    interes = saldo_restante * tasa_interes_mensual
                    iva_interes = interes * iva_tasa
                    principal = pago_mensual - interes  # Pago base antes de agregar el IVA al total

                    # Última cuota: ajustar para que el balance sea cero
                    if i == len(cuotas_pendientes):
                        principal = saldo_restante  # Ajustamos el principal para que balance_restante llegue a 0
                        cuota_pendiente.balance_restante = Decimal(0)
                    else:
                        cuota_pendiente.balance_restante = saldo_restante - principal

                    # Recalcular el pago total para la cuota incluyendo el IVA sobre interés
                    cuota_pendiente.pago = (principal + interes + iva_interes).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    cuota_pendiente.principal = principal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    cuota_pendiente.interes = interes.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    cuota_pendiente.iva_interes = iva_interes.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    cuota_pendiente.save()

                    # Reducir el saldo restante para la siguiente cuota
                    saldo_restante -= principal

                    # Verificar que el saldo restante no sea negativo
                    if saldo_restante <= 0:
                        break

            # Serializar y devolver la tabla de amortización recalculada
            recalculated_amortizations = credito_prestamo.amortizaciones.order_by('numero_mes')
            serializer = AmortizacionCuotaSerializer(recalculated_amortizations, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class AmortizacionCuotaViewSet(viewsets.ModelViewSet):

    queryset = AmortizacionCuota.objects.all()
    serializer_class = AmortizacionCuotaSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    
    # Campos de búsqueda y ordenación
    search_fields = ['credito_prestamo__numero_transaccion']  # Puedes agregar más campos de búsqueda según sea necesario
    ordering_fields = ['numero_mes', 'pago', 'balance_restante']

    def get_queryset(self):
        """
        Filtra el queryset para ordenar por `fecha_pago_programada` descendente
        """
        return AmortizacionCuota.objects.all().order_by('-fecha_pago_programada')
    
class TipoOtroGastoViewSet(viewsets.ModelViewSet):
    queryset = TipoOtroGasto.objects.all().order_by('nombre')
    serializer_class = TipoOtroGastoSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        # Listar todos los tipos de gastos
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        # Obtener un solo tipo de gasto
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

class OtroGastoViewSet(viewsets.ModelViewSet):
    queryset = OtroGasto.objects.all().order_by('-fecha')
    serializer_class = OtroGastoSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['descripcion', 'proveedor']
    ordering_fields = ['fecha', 'monto_total', 'estatus']

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        pagos = instance.abonos.all()
        pagos_serializer = PagoOtroGastoSerializer(pagos, many=True)
        serializer = self.get_serializer(instance)
        
        return Response({
            'gasto': serializer.data,
            'pagos': pagos_serializer.data,
        })

    def perform_create(self, serializer):
        serializer.save()  # La lógica está manejada en el modelo

    def perform_update(self, serializer):
        serializer.save()  # La lógica está manejada en el modelo

    @action(detail=True, methods=['post'])
    def cambiar_estatus(self, request, pk=None):
        gasto = self.get_object()
        nuevo_estatus = request.data.get('estatus')

        if nuevo_estatus in [choice[0] for choice in OtroGasto.ESTATUS_CHOICES]:
            gasto.estatus = nuevo_estatus
            if nuevo_estatus == 'programado':
                gasto.fecha_aprobacion = date.today()
            gasto.save()
            return Response({'status': 'Estatus actualizado'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Estatus inválido'}, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['get'], url_path='saldo-total-sl', url_name='saldo_total_sl')
    def saldo_total_por_divisa_semana_laboral(self, request):
        """
        Endpoint para calcular el saldo total de otros gastos por semana laboral o estado pendiente.
        """
        today = now().date()
        start_of_week = today - timedelta(days=today.weekday())  # Lunes
        end_of_week = start_of_week + timedelta(days=6)  # Domingo

        # Filtrar registros de esta semana laboral o en estado pendiente
        otros_gastos_filtrados = OtroGasto.objects.filter(
            Q(fecha_gasto__range=(start_of_week, end_of_week)) |
            Q(estatus__iexact='pendiente')
        )

        # Sumar los totales por divisa
        saldo_mxn = otros_gastos_filtrados.filter(divisa='MXN').aggregate(
            total_mxn=Sum('monto_total')
        )['total_mxn'] or 0

        saldo_usd = otros_gastos_filtrados.filter(divisa='USD').aggregate(
            total_usd=Sum('monto_total')
        )['total_usd'] or 0

        return Response({
            'saldo_total': {
                'MXN': saldo_mxn,
                'USD': saldo_usd,
            }
        }, status=200)

class PagoOtroGastoViewSet(viewsets.ModelViewSet):
    queryset = PagoOtroGasto.objects.all().order_by('-fecha_abono')
    serializer_class = PagoOtroGastoSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        otro_gasto_id = self.request.query_params.get('otro_gasto', None)
        if otro_gasto_id is not None:
            queryset = queryset.filter(otro_gasto_id=otro_gasto_id)
        return queryset
    
    def create(self, request, *args, **kwargs):
        otro_gasto_id = request.data.get('otro_gasto')
        abono = request.data.get('abono')
        tarjeta_id = request.data.get('tarjeta_id')  # Recibir tarjeta asociada al pago
        
        try:
            abono = Decimal(abono)  # Convertir abono a Decimal
        except (TypeError, ValueError):
            return Response({'error': 'El valor del abono no es válido'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otro_gasto = OtroGasto.objects.get(pk=otro_gasto_id)
        except OtroGasto.DoesNotExist:
            return Response({'error': 'Gasto no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        total_abonos = otro_gasto.abonos.aggregate(Sum('abono'))['abono__sum'] or 0
        saldo_pendiente = otro_gasto.monto_total - total_abonos

        if saldo_pendiente <= 0:
            return Response({'error': 'No hay saldo pendiente para abonar'}, status=status.HTTP_400_BAD_REQUEST)

        if abono > saldo_pendiente:
            return Response({'error': 'El abono no puede exceder el saldo pendiente'}, status=status.HTTP_400_BAD_REQUEST)

        response = super().create(request, *args, **kwargs)
            
        total_abonos = otro_gasto.abonos.aggregate(Sum('abono'))['abono__sum'] or 0
        otro_gasto.saldo = otro_gasto.monto_total - total_abonos
        if otro_gasto.saldo == 0:
            otro_gasto.estatus = 'pagado'
        otro_gasto.save()

        return response

    def update(self, request, *args, **kwargs):
        otro_gasto_id = request.data.get('otro_gasto')
        abono = request.data.get('abono')

        try:
            abono = Decimal(abono)
        except (TypeError, ValueError):
            return Response({'error': 'El valor del abono no es válido'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otro_gasto = OtroGasto.objects.get(pk=otro_gasto_id)
        except OtroGasto.DoesNotExist:
            return Response({'error': 'Gasto no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
        pago_actual = self.get_object()
        total_abonos = otro_gasto.abonos.exclude(pk=pago_actual.pk).aggregate(Sum('abono'))['abono__sum'] or 0
        saldo_pendiente = otro_gasto.monto_total - total_abonos

        if abono > saldo_pendiente:
            return Response({'error': 'El abono no puede exceder el saldo pendiente'}, status=status.HTTP_400_BAD_REQUEST)

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # Eliminar un pago y recalcular el saldo del gasto
        pago = self.get_object()
        otro_gasto = pago.otro_gasto

        # Eliminar el pago
        response = super().destroy(request, *args, **kwargs)

        # Recalcular saldo del gasto después de eliminar el pago
        total_abonos = otro_gasto.abonos.aggregate(Sum('abono'))['abono__sum'] or 0
        otro_gasto.saldo = otro_gasto.monto_total - total_abonos
        otro_gasto.save()

        # Actualizar el estatus si el saldo llega a 0
        if otro_gasto.saldo == 0:
            otro_gasto.estatus = 'pagado'
            otro_gasto.save()

        return response

    def list(self, request, *args, **kwargs):
        # Listar todos los pagos
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        # Obtener un solo pago
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class TarjetaCreditoViewSet(viewsets.ModelViewSet):
    queryset = TarjetaCredito.objects.all().order_by('-fecha_creacion')
    serializer_class = TarjetaCreditoSerializer


    def perform_create(self, serializer):
        tarjeta = serializer.save()
        tarjeta.agregar_pagos_automaticos()
        tarjeta.verificar_estado_moroso()

    def retrieve(self, request, *args, **kwargs):
        tarjeta = self.get_object()
        
        # Actualizar saldo antes de devolver la tarjeta
        tarjeta.actualizar_datos_desde_pago_actual()
        tarjeta.save()

        return super().retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        tarjetas = self.get_queryset()

        # Actualizar el saldo de cada tarjeta
        for tarjeta in tarjetas:
            tarjeta.actualizar_datos_desde_pago_actual()
            tarjeta.save()

        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='realizar-cargo')
    def realizar_cargo(self, request, pk=None):
        tarjeta = self.get_object()
        monto = Decimal(request.data.get('monto', 0))
        concepto = request.data.get('concepto', 'Cargo sin especificar')

        # Validación de saldo y límite de crédito
        if tarjeta.saldo + monto > tarjeta.limite_credito:
            return Response({'error': 'El cargo excede el límite de crédito'}, status=status.HTTP_400_BAD_REQUEST)

        tarjeta.saldo += monto
        tarjeta.save()

        MovimientoTarjeta.objects.create(
            tarjeta=tarjeta,
            monto=monto,
            concepto=concepto,
            fecha=timezone.now()
        )
        return Response({'status': 'Cargo realizado'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='realizar-pago')
    def realizar_pago(self, request, pk=None):
        tarjeta = self.get_object()
        monto_abono = Decimal(request.data.get('monto_abono', 0))
        referencia = request.data.get('referencia_transferencia', None)
        pdf = request.data.get('pdf_comprobante', None)

        if monto_abono <= 0:
            return Response({'error': 'Monto inválido'}, status=status.HTTP_400_BAD_REQUEST)

        # Se aplica el pago mínimo para cada ciclo
        pago = tarjeta.pagos_mensuales.filter(estatus='pendiente').order_by('fecha_vencimiento').first()
        if pago and monto_abono >= pago.pago_minimo:
            pago.estatus = 'pagado'
            tarjeta.saldo -= monto_abono
            tarjeta.save()
            pago.save()

            Abono.objects.create(
                tarjeta=tarjeta,
                fecha_abono=timezone.now().date(),
                monto_abono=monto_abono,
                referencia_transferencia=referencia,
                pdf_comprobante=pdf
            )
            return Response({'status': 'Pago realizado'}, status=status.HTTP_200_OK)
        return Response({'error': 'El abono es insuficiente o no hay pagos pendientes'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='estado-cuenta')
    def estado_cuenta(self, request, pk=None):
        tarjeta = self.get_object()
        pagos_mensuales = tarjeta.pagos_mensuales.order_by('fecha_vencimiento')
        movimientos = tarjeta.movimientos.all()
        abonos = tarjeta.abonos.all()

        response_data = {
            'saldo_total': tarjeta.saldo,
            'cargos': MovimientoTarjetaSerializer(movimientos, many=True).data,
            'pagos': PagoMensualTarjetaSerializer(pagos_mensuales, many=True).data,
            'abonos': AbonoTarjetaSerializer(abonos, many=True).data,
            'intereses_generados': sum(pago.interes for pago in pagos_mensuales),
        }
        return Response(response_data)

    @action(detail=True, methods=['post'], url_path='simular-pago')
    def simular_pago(self, request, pk=None):
        tarjeta = self.get_object()
        monto = Decimal(request.data.get('monto', 0))

        if monto <= 0:
            return Response({'error': 'Monto inválido'}, status=status.HTTP_400_BAD_REQUEST)

        interes_actual = tarjeta.calcular_interes_mensual(tarjeta.saldo)
        pago_a_capital = max(Decimal(0), monto - interes_actual)
        nuevo_saldo = tarjeta.saldo - pago_a_capital

        response_data = {
            'saldo_proyectado': nuevo_saldo,
            'pago_aplicado_a_capital': pago_a_capital,
            'pago_aplicado_a_intereses': min(monto, interes_actual),
        }
        return Response(response_data)


    @action(detail=False, methods=['get'], url_path='totales')
    def totales(self, request):
        totales_por_divisa = TarjetaCredito.objects.values('divisa').annotate(
            saldo_total=Sum('saldo'), limite_credito_total=Sum('limite_credito')
        )

        # Convertir la lista a un diccionario
        response_data = {item['divisa']: item['saldo_total'] for item in totales_por_divisa}
        return Response(response_data, status=status.HTTP_200_OK)
    
    # Método para actualizar varios campos de una TarjetaCredito
    def partial_update(self, request, *args, **kwargs):
        """
        Actualización parcial de una TarjetaCredito.
        """
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='listar-tarjetas')
    def listar_tarjetas(self, request):
        tarjetas = self.get_queryset()
        for tarjeta in tarjetas:
            tarjeta.actualizar_datos_desde_pago_actual()
            tarjeta.save()

        serializer = self.get_serializer(tarjetas, many=True)
        return Response(serializer.data)
    
    # Endpoint para obtener el saldo restante
    @action(detail=True, methods=['get'], url_path='saldo-restante')
    def saldo_restante(self, request, pk=None):
        """
        Devuelve el saldo restante de una tarjeta específica.
        """
        tarjeta = self.get_object()
        return Response({
            "saldo_restante": tarjeta.saldo_restante
        }, status=200)


    # Endpoint para obtener el saldo restante por semana
    @action(detail=False, methods=['get'], url_path='saldo-total-sl', url_name='saldo_total_sl')
    def saldo_total_por_divisa_semana_laboral(self, request):
        """
        Endpoint para calcular el saldo total de las tarjetas de crédito
        filtradas por fecha de pago en la semana laboral actual o estado 'moroso',
        separados por divisa.
        """
        # Calcular la semana laboral actual (lunes a domingo)
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())  # Lunes
        end_of_week = start_of_week + timedelta(days=6)  # Domingo

        # Filtrar tarjetas de crédito por fecha de pago en esta semana o estado moroso
        tarjetas_filtradas = TarjetaCredito.objects.filter(
            Q(fecha_pago__range=(start_of_week, end_of_week)) | Q(estatus__iexact='moroso')
        )

        # Sumar los saldos separados por divisa
        saldo_mxn = tarjetas_filtradas.filter(divisa='MXN').aggregate(
            total_mxn=Sum('saldo')
        )['total_mxn'] or 0

        saldo_usd = tarjetas_filtradas.filter(divisa='USD').aggregate(
            total_usd=Sum('saldo')
        )['total_usd'] or 0

        # Construir y retornar la respuesta
        return Response({
            'saldo_total': {
                'MXN': saldo_mxn,
                'USD': saldo_usd,
            }
        }, status=status.HTTP_200_OK)
        
        
    @action(detail=False, methods=['post'])
    def aprobar(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({"error": "No se proporcionaron IDs"}, status=status.HTTP_400_BAD_REQUEST)

        tarjetas = TarjetaCredito.objects.filter(id__in=ids)
        pagos_actualizados = 0
        tarjetas_actualizadas = 0

        for tarjeta in tarjetas:
            # Filtrar el pago mensual actual de la tarjeta
            pago_actual = tarjeta.pagos_mensuales.filter(actual=True).first()
            if pago_actual:
                # Cambiar el estado del pago mensual a 'programado'
                pago_actual.estatus = 'programado'
                pago_actual.save()
                pagos_actualizados += 1

                # Si la tarjeta no está vencida, actualizar su estado a 'programado'
                if tarjeta.estatus.lower() != 'vencido':
                    tarjeta.estatus = 'programado'
                    tarjeta.save()
                    tarjetas_actualizadas += 1

        return Response({
            "message": f"{pagos_actualizados} pagos actuales fueron actualizados a 'Programado'.",
            "tarjetas_actualizadas": f"{tarjetas_actualizadas} tarjetas actualizadas a 'Programado'."
        })

class PagoMensualTarjetaViewSet(viewsets.ModelViewSet):
    queryset = PagoMensualTarjeta.objects.all().order_by('mes')
    serializer_class = PagoMensualTarjetaSerializer

    def list(self, request, *args, **kwargs):
        banco_nombre = request.query_params.get('banco')
        
        if banco_nombre:
            # Filtrar pagos mensuales según el banco de la tarjeta relacionada
            self.queryset = self.queryset.filter(tarjeta__banco__iexact=banco_nombre)

        self.update_estatus_vencidos()
        
        # Llamar al método para actualizar estado y saldo de cada instancia
        for pago in self.queryset:
            pago.actualizar_estado_y_saldo()

        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Llamar al método para actualizar el estado y saldo
        instance.actualizar_estado_y_saldo()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update_estatus_vencidos(self):
        vencidos = self.queryset.filter(fecha_vencimiento__lt=timezone.now().date(), estatus='pendiente')
        vencidos.update(estatus='moroso')

    def perform_create(self, serializer):
        pago_mensual = serializer.save()
        self._verificar_estado_pago(pago_mensual)

    # Método para actualizar varios campos de un PagoMensualTarjeta
    def partial_update(self, request, *args, **kwargs):
        """
        Actualización parcial de un PagoMensualTarjeta.
        """
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Llamar al método para actualizar el estado y saldo
        instance.actualizar_estado_y_saldo()
        
        self._verificar_estado_pago(instance)
        return Response(serializer.data)
 
    def _verificar_estado_pago(self, pago_mensual):
        fecha_actual = timezone.now().date()
        if pago_mensual.fecha_vencimiento < fecha_actual and pago_mensual.estatus == 'pendiente':
            pago_mensual.estatus = 'moroso'
            pago_mensual.save()
        
class MovimientoTarjetaViewSet(viewsets.ModelViewSet):
    queryset = MovimientoTarjeta.objects.all().order_by('-fecha')
    serializer_class = MovimientoTarjetaSerializer

    def create(self, request, *args, **kwargs):
        tarjeta = TarjetaCredito.objects.get(id=request.data.get('tarjeta'))
        monto = Decimal(request.data.get('monto', 0))

        if tarjeta.saldo + monto > tarjeta.limite_credito:
            return Response({'error': 'El cargo excede el límite de crédito'}, status=status.HTTP_400_BAD_REQUEST)

        tarjeta.saldo += monto
        tarjeta.save()
        
        return super().create(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'], url_path='detallado')
    def historial_detallado(self, request):
        concepto = request.query_params.get('concepto', None)
        fecha_inicio = request.query_params.get('fecha_inicio', None)
        fecha_fin = request.query_params.get('fecha_fin', None)
        movimientos = self.queryset

        if concepto:
            movimientos = movimientos.filter(concepto__icontains=concepto)
        if fecha_inicio and fecha_fin:
            movimientos = movimientos.filter(fecha__range=[fecha_inicio, fecha_fin])
        
        serializer = self.get_serializer(movimientos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='por-tarjeta')
    def movimientos_por_tarjeta(self, request):
        tarjeta_id = request.query_params.get('tarjeta_id')
        
        if tarjeta_id:
            movimientos = self.queryset.filter(tarjeta__id=tarjeta_id)
        else:
            return Response(
                {"error": "Debe proporcionar un tarjeta_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(movimientos, many=True)
        return Response(serializer.data)
    
class AbonoTarjetaViewSet(viewsets.ModelViewSet):
    queryset = AbonoTarjeta.objects.all()
    serializer_class = AbonoTarjetaSerializer

    def list(self, request, *args, **kwargs):
        pago_mensual_id = request.query_params.get('pago_mensual', None)
        if pago_mensual_id:
            try:
                pago_mensual_id = int(pago_mensual_id)  # Convertir a entero
                self.queryset = self.queryset.filter(pago_mensual__id=pago_mensual_id)
            except ValueError:
                # Manejar el caso en que pago_mensual_id no sea un entero válido
                return Response({'error': 'El ID del pago mensual debe ser un entero válido.'}, status=400)
        return super().list(request, *args, **kwargs)
    
class ServiciosFacturaViewSet(viewsets.ModelViewSet):
    queryset = ServiciosFactura.objects.all().order_by('-fecha_creacion')
    serializer_class = ServicioFacturaSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre_servicio', 'folio_servicio']
    ordering_fields = ['fecha_vencimiento', 'total_a_pagar', 'estatus']

    def get_queryset(self):
        queryset = super().get_queryset()
        for servicio in queryset:
            servicio.verificar_estado_servicio()
        
        return queryset
    
    def calcular_nueva_fecha(seg, fecha_base, periodicidad):
        """
        Calcula una nueva fecha en función de la periodicidad del servicio.
        """
        if periodicidad == 'semanal':
            return fecha_base + timedelta(weeks=1)
        elif periodicidad == 'mensual':
            nueva_fecha = fecha_base + relativedelta(months=1)
            if nueva_fecha.day != fecha_base.day:
                nueva_fecha = nueva_fecha + relativedelta(day=31)
            return nueva_fecha
        elif periodicidad == 'bimestral':
            nueva_fecha = fecha_base + relativedelta(months=2)
            if nueva_fecha.day != fecha_base.day:
                nueva_fecha = nueva_fecha + relativedelta(day=31)
            return nueva_fecha
        elif periodicidad == 'trimestral':
            nueva_fecha = fecha_base + relativedelta(months=3)
            if nueva_fecha.day != fecha_base.day:
                nueva_fecha = nueva_fecha + relativedelta(day=31)
            return nueva_fecha
        elif periodicidad == 'anual':
            nueva_fecha = fecha_base + relativedelta(years=1)
            return nueva_fecha
        else:
            return fecha_base  # Si no hay periodicidad definida, no se modifica la fecha

    @action(detail=True, methods=['post'])
    def cambiar_estatus(self, request, pk=None):
        servicio = self.get_object()
        nuevo_estatus = request.data.get('estatus')
        if nuevo_estatus in [choice[0] for choice in ServiciosFactura.ESTATUS_CHOICES]:
            servicio.estatus = nuevo_estatus
            servicio.save()
            return Response({'status': 'Estatus actualizado'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Estatus inválido'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='saldo-total', url_name='saldo_total')
    def saldo_total_por_divisa(self, request):
        return
    
    @action(detail=False, methods=['get'], url_path='saldo-total-sl', url_name='saldo_total_sl')
    def saldo_total_por_divisa_semana_laboral(self, request):
        """
        Endpoint para calcular el saldo total de las cuentas filtradas
        por fecha o estado, separados por divisa.
        """
        # Calcular la semana laboral actual (lunes a domingo)
        today = now().date()
        start_of_week = today - timedelta(days=today.weekday())  # Lunes
        end_of_week = start_of_week + timedelta(days=6)  # Domingo

        # Filtrar registros que cumplen con la semana actual o estado vencido
        servicios_filtrados = ServiciosFactura.objects.filter(
            Q(fecha_vencimiento__range=(start_of_week, end_of_week)) |
            Q(estatus__iexact='vencido')
        )

        # Sumar los totales separados por divisa
        saldo_mxn = servicios_filtrados.filter(divisa='MXN').aggregate(
            total_mxn=Sum('total_a_pagar')
        )['total_mxn'] or 0

        saldo_usd = servicios_filtrados.filter(divisa='USD').aggregate(
            total_usd=Sum('total_a_pagar')
        )['total_usd'] or 0

        # Retornar los resultados
        return Response({
            'saldo_total': {
                'MXN': saldo_mxn,
                'USD': saldo_usd,
            }
        }, status=200)

    @action(detail=False, methods=['post'])
    def aprobar(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({"error": "No se proporcionaron IDs"}, status=status.HTTP_400_BAD_REQUEST)

        # Filtrar los servicios que están en estado "pendiente" o "vencido"
        servicios = ServiciosFactura.objects.filter(id__in=ids, estatus__in=['pendiente', 'vencido'])
        pagos_actualizados = 0
        servicios_actualizados = 0

        for servicio in servicios:
            # Actualiza los pagos relacionados con propuesta_pago > 0
            pagos = servicio.pagos_por_periodo.filter(propuesta_pago__gt=0)
            pagos_actualizados += pagos.update(estatus='programado')

            # Verifica si el servicio NO está vencido y el pago actual es "Programado"
            if servicio.estatus != 'vencido':
                pago_actual = servicio.pagos_por_periodo.filter(actual=True, estatus='programado').first()
                if pago_actual:
                    # Cambia el estado del servicio a "Programado"
                    servicio.estatus = 'programado'
                    servicio.save()
                    servicios_actualizados += 1

        return Response({
            "message": f"{pagos_actualizados} pagos actualizados a 'Programado', {servicios_actualizados} servicios sincronizados."
        })
    
class PagoPorPeriodoViewSet(viewsets.ModelViewSet):
    queryset = PagoPorPeriodo.objects.all()
    serializer_class = PagoPorPeriodoSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        servicio_id = self.request.query_params.get('servicio', None)
        if servicio_id is not None:
            return self.queryset.filter(servicio_id=servicio_id)
        return self.queryset
    
    def update_saldo_pendiente(self, instance, monto):
        """
        Método que permite modificar el saldo pendiente y actualizar el estatus
        """
        instance.saldo_pendiente -= monto
        if instance.saldo_pendiente <= 0:
            instance.saldo_pendiente = 0
            instance.estatus = 'pagado'
            instance.usado = True
        elif timezone.now().date() > instance.fecha_vencimiento:
            instance.estatus = 'vencido'
        instance.save()

        # Actualizar estado general del servicio después de modificar el periodo
        servicio = instance.servicio
        servicio_viewset = ServiciosFacturaViewSet()
        servicio_viewset.verificar_estado_servicio(servicio)
    
    @action(detail=True, methods=['post'], url_path='modificar-saldo')
    def modificar_saldo(self, request, pk=None):
        """
        Permite modificar el saldo pendiente o estatus de un periodo específico sin afectar otros periodos.
        """
        instance = self.get_object()
        monto = Decimal(request.data.get('monto', 0))

        if monto <= 0:
            return Response({'error': 'El monto debe ser mayor a cero'}, status=status.HTTP_400_BAD_REQUEST)

        instance.aplicar_abono(monto)
        return Response({'status': 'Saldo modificado', 'nuevo_saldo': instance.saldo_pendiente})
    
    @action(detail=False, methods=['post'], url_path='bulk_create')
    def bulk_create(self, request):
        serializer = PagoPorPeriodoSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'Pagos por periodo creados exitosamente'}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='verificar-vencido')
    def verificar_vencido(self, request):
        servicio_id = request.query_params.get('servicio')
        if servicio_id is None:
            return Response({"error": "Falta el ID del servicio"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si existe algún periodo con estado 'vencido'
        existe_vencido = PagoPorPeriodo.objects.filter(servicio_id=servicio_id, estatus='vencido').exists()
        return Response({"existeVencido": existe_vencido}, status=status.HTTP_200_OK)

    
    @action(detail=True, methods=['post'], url_path='cambiar-estado')
    def cambiar_estado(self, request, pk=None):
        periodo = self.get_object()
        nuevo_estado = request.data.get('estatus')
        
        # Imprimir opciones de ESTATUS_CHOICES
        print([estado[0] for estado in PagoPorPeriodo.ESTATUS_CHOICES])
        
        if nuevo_estado not in [estado[0] for estado in PagoPorPeriodo.ESTATUS_CHOICES]:
            return Response({"error": "Estado inválido"}, status=status.HTTP_400_BAD_REQUEST)
        
        periodo.estatus = nuevo_estado
        periodo.save()
        
        # Actualiza el estado del servicio si es necesario
        periodo.servicio.verificar_estado_servicio()

        return Response({"estatus": periodo.estatus}, status=status.HTTP_200_OK)


class PagoPeriodoAbonoViewSet(viewsets.ModelViewSet):
    queryset = PagoPeriodoAbono.objects.all()
    serializer_class = PagoPeriodoAbonoSerializer

    def get_queryset(self):
        # Filtrar por periodo si se pasa como parámetro de consulta
        periodo_id = self.request.query_params.get('periodo', None)
        if periodo_id is not None:
            return self.queryset.filter(periodo_id=periodo_id)
        return self.queryset
    
class CuentaBancariaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar las cuentas bancarias asociadas a un servicio.
    """
    queryset = CuentaBancaria.objects.all()
    serializer_class = CuentaBancariaSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['numero_cuenta', 'banco']
    ordering_fields = ['banco']

    def list(self, request, *args, **kwargs):
        """
        Devuelve la lista de todas las cuentas bancarias.
        """
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Crear una nueva cuenta bancaria y asociarla a un servicio.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Verificar que el servicio al que se va a asociar la cuenta existe
            servicio_id = request.data.get('servicio_id')
            try:
                servicio = ServiciosFactura.objects.get(id=servicio_id)
                # Crear la cuenta bancaria
                serializer.save(servicio=servicio)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except ServiciosFactura.DoesNotExist:
                return Response({'error': 'Servicio no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='servicio', url_name='servicio')
    def obtener_cuentas_por_servicio(self, request, pk=None):
        """
        Devuelve todas las cuentas bancarias asociadas a un servicio específico.
        """
        try:
            # Obtener el servicio por su ID
            servicio = ServiciosFactura.objects.get(pk=pk)

            # Obtener todas las cuentas bancarias relacionadas con ese servicio
            cuentas = CuentaBancaria.objects.filter(servicio=servicio)

            # Serializar las cuentas bancarias relacionadas
            serializer = CuentaBancariaSerializer(cuentas, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except ServiciosFactura.DoesNotExist:
            return Response({'error': 'Servicio no encontrado'}, status=status.HTTP_404_NOT_FOUND)


# ViewSet para ISR
class ISRViewSet(viewsets.ModelViewSet):
    queryset = Isr.objects.all()  
    serializer_class = IsrSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['limite_inferior', 'limite_superior']
    ordering_fields = ['limite_inferior', 'limite_superior', 'cuota_fija', 'porcentaje_excedente']

    def get_queryset(self):
        queryset = Isr.objects.all().order_by('-fecha_creacion')
        # Actualizar estatus a 'desactualizado' si la última modificación fue antes del 1 de enero del año actual
        for obj in queryset:
            obj.verificar_actualizacion()
        return queryset


# ViewSet para Vacaciones (sin estatus)
class VacacionesViewSet(viewsets.ModelViewSet):
    queryset = Vacaciones.objects.all()
    serializer_class = VacacionesSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['años']
    ordering_fields = ['años', 'dias']

    def get_queryset(self):
        queryset = Vacaciones.objects.all().order_by('-fecha_creacion')
        # Actualizar estatus a 'desactualizado' si la última modificación fue antes del 1 de enero del año actual
        for obj in queryset:
            obj.verificar_actualizacion()
        return queryset
            
# ViewSet para Aportaciones Obrero Patronales IMSS
class AportacionObreroPatronalesViewSet(viewsets.ModelViewSet):
    queryset = AportacionObreroPatronales.objects.all() 
    serializer_class = AportacionObreroPatronalesSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['concepto']
    ordering_fields = ['patron', 'trabajador']

    def get_queryset(self):
        queryset = AportacionObreroPatronales.objects.all().order_by('-fecha_creacion')
        for obj in queryset:
            obj.verificar_actualizacion()
        return queryset


# ViewSet para Aportaciones Patronales IMSS
class AportacionPatronalesIMSSViewSet(viewsets.ModelViewSet):
    queryset = AportacionPatronalesIMSS.objects.all() 
    serializer_class = AportacionPatronalesIMSSSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['concepto']
    ordering_fields = ['patron', 'trabajador']

    def get_queryset(self):
        queryset = AportacionPatronalesIMSS.objects.all().order_by('-fecha_creacion')
        for obj in queryset:
            obj.verificar_actualizacion()
        return queryset


# ViewSet para Aportaciones Retiro IMSS
class AportacionRetiroIMSSViewSet(viewsets.ModelViewSet):
    queryset = AportacionRetiroIMSS.objects.all() 
    serializer_class = AportacionRetiroIMSSSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['concepto']
    ordering_fields = ['patron', 'trabajador']

    def get_queryset(self):
        queryset = AportacionRetiroIMSS.objects.all().order_by('-fecha_creacion')
        for obj in queryset:
            obj.verificar_actualizacion()
        return queryset


# ViewSet para CEAV IMSS
class CeavIMSSViewSet(viewsets.ModelViewSet):
    queryset = CeavIMSS.objects.all() 
    serializer_class = CEAVIMSSSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['concepto']
    ordering_fields = ['patron', 'trabajador']

    def get_queryset(self):
        queryset = CeavIMSS.objects.all().order_by('-fecha_creacion')
        for obj in queryset:
            obj.verificar_actualizacion()
        return queryset


# ViewSet para Salario Mínimo y UMA
class SalarioMinimoViewSet(viewsets.ModelViewSet):
    queryset = SalarioMinimo.objects.all()
    serializer_class = SalarioMinimoSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['salario_minimo', 'uma']
    ordering_fields = ['salario_minimo', 'uma']

    def get_queryset(self):
        queryset = SalarioMinimo.objects.all().order_by('-fecha_creacion')
        for obj in queryset:
            obj.verificar_actualizacion()
        return queryset
    
class BancoModeloViewSet(viewsets.ModelViewSet):
    queryset = BancoModelo.objects.all()
    serializer_class = BancoModeloSerializer

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        previous_numero_tarjeta = instance.numero_tarjeta  # Guardar el número anterior
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Verificar si el número de tarjeta ha cambiado y replicar tarjeta
        new_numero_tarjeta = serializer.validated_data.get('numero_tarjeta')
        if new_numero_tarjeta and new_numero_tarjeta != previous_numero_tarjeta:
            instance.replicar_tarjeta()

        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='buscar-cuenta')
    def buscar_cuenta_por_tarjeta(self, request):
        """
        Endpoint para buscar la cuenta bancaria asociada a un número de tarjeta.
        """
        numero_tarjeta = request.query_params.get('numero_tarjeta')
        if not numero_tarjeta:
            return Response(
                {"error": "Debe proporcionar un número de tarjeta."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Buscar la cuenta asociada al número de tarjeta
            cuenta = BancoModelo.objects.get(numero_tarjeta=numero_tarjeta)
            return Response(
                {
                    "id_cuenta": cuenta.id,
                    "banco": cuenta.banco,
                    "numero_cuenta": cuenta.numero_cuenta,
                    "tipo_tarjeta": cuenta.tipo_tarjeta,  # Incluyendo el tipo de tarjeta
                    "divisa": cuenta.divisa,
                    "saldo": str(cuenta.saldo),  # Convertir a string para evitar problemas de serialización
                    "estatus": cuenta.estatus,
                },
                status=status.HTTP_200_OK
            )
        except BancoModelo.DoesNotExist:
            return Response(
                {"error": "No se encontró una cuenta asociada al número de tarjeta proporcionado."},
                status=status.HTTP_404_NOT_FOUND
            )
    
class MovimientoBancoViewSet(viewsets.ModelViewSet):
    queryset = MovimientoBanco.objects.all()
    serializer_class = MovimientoBancoSerializer
    
    @action(detail=False, methods=['get'], url_path='por-banco/(?P<banco_id>[^/.]+)')
    def obtener_por_banco(self, request, banco_id=None):
        """
        Obtiene los movimientos asociados a un banco específico por ID.
        """
        try:
            movimientos = MovimientoBanco.objects.filter(numero_cuenta_id=banco_id)
            serializer = self.get_serializer(movimientos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"detail": f"Error al obtener movimientos: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
class AbonoBancoViewSet(viewsets.ModelViewSet):
    queryset = AbonoBanco.objects.all()
    serializer_class = AbonoBancoSerializer
    
# ViewSet para CEAV Patronal
class CeavPatronalViewSet(viewsets.ModelViewSet):
    queryset = CeavPatronal.objects.all()
    serializer_class = CeavPatronalSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['limite_inferior', 'limite_superior']
    ordering_fields = ['limite_inferior', 'limite_superior', 'porcentaje']

    def get_queryset(self):
        """
        Personaliza el queryset para incluir lógica de actualización de estatus.
        """
        queryset = CeavPatronal.objects.all().order_by('-fecha_creacion')
        # Actualizar estatus a 'desactualizado' si la última modificación fue antes del 1 de enero del año actual
        for obj in queryset:
            obj.verificar_actualizacion()
        return queryset

from .serializer import NominaSerializer, NominaListSerializer

from .serializer import NominaSerializer, NominaListSerializer

class NominaViewSet(viewsets.ModelViewSet):
    queryset = Nomina.objects.all().order_by('-fecha_nomina')
    serializer_class = NominaSerializer # Serializador por defecto

    def get_serializer_class(self):
        """
        Usa un serializador diferente para la acción 'list'.
        """
        if self.action == 'list':
            return NominaListSerializer
        # Para cualquier otra acción (detalle, crear, etc.), usa el completo.
        return self.serializer_class

    def get_queryset(self):
        """
        Optimiza la consulta para incluir los datos del empleado
        y evitar consultas adicionales (N+1).
        """
        queryset = super().get_queryset()
        if self.action == 'list':
            # Usamos select_related para hacer un JOIN eficiente.
            return queryset.select_related('empleado__puesto')
        
        # Aplicar filtros por parámetros de consulta
        semana = self.request.query_params.get('semana', None)
        año = self.request.query_params.get('año', None)

        if semana is not None:
            queryset = queryset.filter(fecha_nomina__week=int(semana))

        if año is not None:
            queryset = queryset.filter(fecha_nomina__year=int(año))

        return queryset


    def perform_create(self, serializer):
        """
        Método para manejar lógica personalizada al crear registros de nómina.
        """
        serializer.save()

    def perform_update(self, serializer):
        """
        Método para manejar lógica personalizada al actualizar registros de nómina.
        """
        serializer.save()
        
    # Acción personalizada para los totales de la semana
    @action(detail=False, methods=['get'], url_path='totales-semana-actual')
    def totales_semana_actual(self, request):
        """
        Obtiene los totales de la semana actual.
        """
        # Obtén el año y la semana actual
        today = date.today()
        current_year, current_week, _ = today.isocalendar()

        # Filtra las nóminas del año y de la semana actual
        queryset = self.get_queryset().filter(
            fecha_nomina__year=current_year,
            fecha_nomina__week=current_week
        )

        #  Calcula todos los totales en UNA SOLA consulta a la base de datos
        totales = queryset.aggregate(
            total_depositar=Sum('nomina_a_depositar'),
            total_imp=Sum('total_impuestos'),
            total_aprob=Sum('monto_aprobado_nomina')
        )

        # Asigna los valores desde el diccionario de totales
        total_nomina_a_depositar = totales.get('total_depositar') or 0
        total_impuestos = totales.get('total_imp') or 0
        total_aprobado = totales.get('total_aprob') or 0

        # Retorna los resultados
        return Response({
            'year': current_year,
            'week': current_week,
            'total_nomina_a_depositar': round(total_nomina_a_depositar, 2),
            'total_impuestos': round(total_impuestos, 2),
            'total_aprobado': round(total_aprobado, 2),
        })

    # Acción personalizada para cambiar el estado
    @action(detail=True, methods=['post'], url_path='cambiar-estado')
    def cambiar_estado(self, request, pk=None):
        """
        Cambia el estado de una nómina específica.
        """
        # Obtener la nómina por ID
        try:
            nomina = self.get_object()
        except Nomina.DoesNotExist:
            return Response(
                {"error": "No se encontró la nómina."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validar el nuevo estado
        nuevo_estado = request.data.get('estatus', '').lower()
        estados_validos = [choice[0] for choice in Nomina.ESTATUS_CHOICES]

        if nuevo_estado not in estados_validos:
            return Response(
                {"error": f"Estado inválido. Los estados válidos son: {', '.join(estados_validos)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Actualizar el estado
        nomina.estatus = nuevo_estado
        nomina.save(update_fields=['estatus'])

        return Response(
            {"message": "Estado actualizado correctamente.", "nuevo_estado": nuevo_estado},
            status=status.HTTP_200_OK
        )
        
    
    @action(detail=False, methods=['get'], url_path='semana-actual')
    def semana_actual(self, request):
        """
        Endpoint para obtener la semana actual del año y sus fechas de inicio y fin.
        """
        # Fecha actual
        today = date.today()

        # Año y semana actual
        current_year, current_week, _ = today.isocalendar()

        # Calculamos el primer día de la semana (lunes)
        start_of_week = today - timedelta(days=today.weekday())

        # Calculamos el último día de la semana (domingo)
        end_of_week = start_of_week + timedelta(days=6)

        return Response({
            "year": current_year,
            "week": current_week,
            "start_of_week": start_of_week.strftime('%Y-%m-%d'),
            "end_of_week": end_of_week.strftime('%Y-%m-%d'),
        })

class ComprobantePagoViewSet(viewsets.ModelViewSet):
    queryset = ComprobantePagoNomina.objects.all()
    serializer_class = ComprobantePagoSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nomina__empleado__nombre_completo', 'tipo_pago', 'referencia']
    ordering_fields = ['fecha_pago', 'monto']


class NominaResidentesPracticantesViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar la nómina de practicantes y residentes.
    """
    queryset = NominaResidentesPracticantes.objects.all()
    serializer_class = NominaResidentesPracticantesSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['practicante_residente__nombre_completo', 'estatus', 'fecha_nomina']
    ordering_fields = ['fecha_nomina', 'monto_aprobado', 'semana_nomina']


    def get_queryset(self):
        """
        Sobrescribe el método get_queryset para aplicar filtros personalizados y recalcular campos.
        """
        queryset = NominaResidentesPracticantes.objects.all().order_by('-fecha_nomina')

        # Recalcular campos para cada objeto en el queryset
        # for nomina in queryset:
        #     nomina.apoyo_economico = nomina.calcular_apoyo_economico()
        #     nomina.semana_nomina = nomina.calcular_semana_nomina()
        #     nomina.save(update_fields=[
        #         'apoyo_economico',
        #         'semana_nomina',
        #     ])

        # Aplicar filtros por parámetros de consulta
        semana = self.request.query_params.get('semana', None)
        año = self.request.query_params.get('año', None)

        if semana is not None:
            queryset = queryset.filter(fecha_nomina__week=int(semana))

        if año is not None:
            queryset = queryset.filter(fecha_nomina__year=int(año))

        return queryset
    def perform_create(self, serializer):
        """
        Sobrescribe el método para agregar lógica personalizada al crear registros.
        """
        serializer.save()

    def perform_update(self, serializer):
        """
        Sobrescribe el método para agregar lógica personalizada al actualizar registros.
        """
        serializer.save()


    @action(detail=False, methods=['get'], url_path='totales-semana-actual')
    def totales_semana_actual(self, request):
        """
        Obtiene los totales de la semana actual.
        """
        # Obtén el año y la semana actual
        today = date.today()
        current_year, current_week, _ = today.isocalendar()

        # Filtra las nóminas de la semana actual
        queryset = self.get_queryset().filter(
            fecha_nomina__year=current_year,
            semana_nomina=current_week
        )

        # Calcula ambos totales en una sola consulta a la base de datos
        totales = queryset.aggregate(
            total_aprobado=Sum('monto_aprobado'),
            total_apoyo=Sum('apoyo_economico')
        )

        # Asigna los valores desde el diccionario de totales
        total_monto_aprobado = totales.get('total_aprobado') or 0
        total_apoyo_economico = totales.get('total_apoyo') or 0

        # Retorna los resultados
        return Response({
            'year': current_year,
            'week': current_week,
            'total_monto_aprobado': round(total_monto_aprobado, 2),
            'total_apoyo_economico': round(total_apoyo_economico, 2),
        })

    @action(detail=True, methods=['post'], url_path='cambiar-estado')
    def cambiar_estado(self, request, pk=None):
        """
        Cambia el estado de una nómina específica.
        """
        # Obtener la nómina por ID
        try:
            nomina = self.get_object()
        except NominaResidentesPracticantes.DoesNotExist:
            return Response(
                {"error": "No se encontró la nómina."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validar el nuevo estado
        nuevo_estado = request.data.get('estatus', '').lower()
        estados_validos = [choice[0] for choice in NominaResidentesPracticantes.ESTATUS_CHOICES]

        if nuevo_estado not in estados_validos:
            return Response(
                {"error": f"Estado inválido. Los estados válidos son: {', '.join(estados_validos)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Actualizar el estado
        nomina.estatus = nuevo_estado
        nomina.save(update_fields=['estatus'])

        return Response(
            {"message": "Estado actualizado correctamente.", "nuevo_estado": nuevo_estado},
            status=status.HTTP_200_OK
        )
    

class ComprobantePagoResidentePracticanteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar los comprobantes de pago de nóminas para residentes y practicantes.
    """
    queryset = ComprobantePagoResidentePracticante.objects.all().order_by('-fecha_pago')
    serializer_class = ComprobantePagoResidentePracticanteSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nomina__practicante_residente__nombre_completo', 'tipo_pago', 'referencia']
    ordering_fields = ['fecha_pago', 'monto', 'tipo_pago']
    
    


class CuentaPorPagarProveedorViewSet(viewsets.ModelViewSet):
    queryset = CuentaPorPagarProveedor.objects.all().order_by('-id')
    serializer_class = CuentaPorPagarProveedorSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['folio_factura', 'proveedor__razon_social', 'orden__id']
    ordering_fields = ['fecha_contrarecibo', 'fecha_pago', 'total_factura', 'estatus']

    @action(detail=True, methods=['post'])
    def cambiar_estatus(self, request, pk=None):
        """
        Cambia el estatus de una cuenta por pagar a proveedor.
        Los estatus válidos están definidos en ESTATUS_CHOICES del modelo.
        """
        cuenta = self.get_object()
        nuevo_estatus = request.data.get('estatus')
        estatus_validos = [choice[0] for choice in CuentaPorPagarProveedor.ESTATUS_CHOICES]

        if nuevo_estatus not in estatus_validos:
            return Response({'error': f"Estatus inválido. Estatus válidos: {', '.join(estatus_validos)}"}, status=status.HTTP_400_BAD_REQUEST)

        cuenta.estatus = nuevo_estatus
        cuenta.save()
        return Response({'status': 'Estatus actualizado', 'nuevo_estatus': nuevo_estatus}, status=status.HTTP_200_OK)
    

    @action(detail=True, methods=['post'], url_path='agregar-pago')
    def agregar_pago(self, request, pk=None):
        """
        Agrega un abono a una cuenta por pagar. Si el saldo pendiente llega a 0,
        cambia el estatus a 'pagado'. Si no, lo deja en 'inicial'.
        """
        from decimal import Decimal  # Importación adicional si no está al inicio

        cuenta = self.get_object()

        # Validar campos necesarios en el request
        cantidad_abono = request.data.get('cantidad_abono')
        tipo_de_pago = request.data.get('tipo_de_pago')
        fecha_pago = request.data.get('fecha_pago', datetime.now().date())
        referencia_transferencia = request.data.get('referencia_transferencia')
        pdf = request.FILES.get('pdf')

        # Verificar que cantidad_abono esté presente y sea válida
        try:
            cantidad_abono = Decimal(cantidad_abono)
            if cantidad_abono <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {'error': 'La cantidad del abono es inválida o debe ser mayor a 0.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Crear el registro del abono
        abono = AbonoProveedor.objects.create(
            cuenta=cuenta,
            cantidad_abono=cantidad_abono,
            fecha_pago=fecha_pago,
            tipo_de_pago=tipo_de_pago,
            referencia_transferencia=referencia_transferencia,
            pdf=pdf
        )

        # Actualizar el saldo pendiente y estatus en la cuenta
        total_abonos = cuenta.abonos.aggregate(total=models.Sum('cantidad_abono'))['total'] or Decimal('0.00')
        cuenta.saldo_pendiente = cuenta.total_factura - total_abonos

        if cuenta.saldo_pendiente <= 0:
            cuenta.saldo_pendiente = Decimal('0.00')
            cuenta.estatus = 'pagado'
        else:
            cuenta.estatus = 'inicial'

        cuenta.save()

        # Responder con la información actualizada
        return Response({
            'status': 'Pago registrado con éxito',
            'nuevo_saldo_pendiente': float(cuenta.saldo_pendiente),
            'estatus_actual': cuenta.estatus,
            'abono': {
                'cantidad_abono': float(abono.cantidad_abono),
                'fecha_pago': abono.fecha_pago,
                'tipo_de_pago': abono.tipo_de_pago,
                'referencia': abono.referencia_transferencia
            }
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='totales')
    def totales(self, request):
        """
        Devuelve los totales agrupados por divisa y por proveedor dentro de cada divisa,
        incluyendo la cantidad de facturas por proveedor.

        Estructura de la respuesta:
        {
        "totales_por_divisa": {
            "MXN": total_mxn,
            "USD": total_usd,
            ...
        },
        "totales_por_proveedor": {
            "MXN": [
                {"proveedor": "Proveedor X", "total": 1234.56, "cantidad": 3},
                {"proveedor": "Proveedor Y", "total": 7890.12, "cantidad": 5},
                ...
            ],
            "USD": [
                {"proveedor": "Proveedor A", "total": 5555.55, "cantidad": 2},
                ...
            ]
        }
        }
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Totales por divisa
        totales_divisa = queryset.values('divisa').annotate(total=Sum('total_factura'))

        # Totales por proveedor, divisa, y la cantidad de registros por proveedor
        totales_proveedor_divisa = queryset.values('divisa', 'proveedor__razon_social') \
                                        .annotate(
                                            total=Sum('total_factura'),
                                            cantidad=Count('id')
                                        ) \
                                        .order_by('divisa', 'proveedor__razon_social')

        # Convertir el resultado de totales_divisa a un diccionario más legible
        totales_por_divisa = {item['divisa']: float(item['total']) for item in totales_divisa}

        # Estructura para almacenar los proveedores por divisa
        proveedores_por_divisa = {}

        # Inicializar las listas de proveedores para cada divisa que aparezca en totales_divisa
        for divisa in totales_por_divisa.keys():
            proveedores_por_divisa[divisa] = []

        # Llenar las listas de proveedores por divisa
        for item in totales_proveedor_divisa:
            divisa = item['divisa']
            proveedores_por_divisa[divisa].append({
                "proveedor": item['proveedor__razon_social'],
                "total": float(item['total']),
                "cantidad": int(item['cantidad'])  # Agregar la cantidad de registros
            })

        return Response({
            "totales_por_divisa": totales_por_divisa,
            "totales_por_proveedor": proveedores_por_divisa
        }, status=status.HTTP_200_OK)
        
    @action(detail=False, methods=['patch'], url_path='cuenta_por_pagar_cambiar_pdf_factura')
    def cuenta_por_pagar_cambiar_pdf_factura(self, request):
        """
        Cambia el PDF de la factura de una cuenta por pagar.
        """
        logging.debug(f'Request Data: {request.data}')  # Agregar logs para depuración
        logging.debug(f'Request POST: {request.POST}')
        logging.debug(f'Request FILES: {request.FILES}')
        
        cuenta_id = request.data.get('cuenta_id')
        pdf = request.FILES.get('factura_pdf')
        logging.debug(f'cuenta_id: {cuenta_id}')

        if not cuenta_id:
            return Response({'error': 'Falta el ID de la cuenta por pagar'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cuenta = CuentaPorPagarProveedor.objects.get(id=cuenta_id)
        except CuentaPorPagarProveedor.DoesNotExist:
            return Response({'error': 'Cuenta por pagar no encontrada'}, status=status.HTTP_404_NOT_FOUND)

        cuenta.factura_pdf = pdf
        cuenta.save(update_fields=['factura_pdf'])

        return Response({'status': 'PDF de factura actualizado correctamente'}, status=status.HTTP_200_OK)


class AbonoProveedorViewSet(viewsets.ModelViewSet):
    queryset = AbonoProveedor.objects.all().order_by('-fecha_pago')
    serializer_class = AbonoProveedorSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['proveedor__razon_social', 'referencia_transferencia']
    ordering_fields = ['fecha_pago', 'cantidad_abono']

    def get_queryset(self):
        queryset = super().get_queryset()
        cuenta_id = self.request.query_params.get('cuenta_id', None)
        if cuenta_id is not None:
            queryset = queryset.filter(cuenta_id=cuenta_id)
        return queryset
