from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
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

from ri_project import settings
from .serializer import CatalogoDocumentoSerializer, DocumentoCargadoSerializer, DocumentoEmpleadoSerializer, EmpleadoSerializer, PracticanteResidenteSerializer, PuestoSerializer, UniversidadSerializer, DocumentoRequisitosSerializer
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
from .models import CatalogoDocumento, DocumentoCargado, DocumentoEmpleado, DocumentoRequisitos, Empleado, PracticanteResidente, Puesto, Universidad
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from datetime import date
from django.db.models import Max
from django.db.models import OuterRef, Subquery
from django.db.models.functions import Coalesce
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from zipfile import ZipFile
import io
import requests
from ri_rh.models import Nomina, NominaResidentesPracticantes

class PuestoViewSet(viewsets.ModelViewSet):
    # Las clases que se encargan de autenticar y autorizar las peticiones
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Puesto.objects.all()
    serializer_class = PuestoSerializer
    

class EmpleadoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para realizar CRUD en el modelo Empleado.
    Incluye un endpoint adicional para cambiar el estatus del empleado.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoSerializer
    
    @action(detail=True, methods=['patch'], url_path='cambiar-estatus')
    def cambiar_estatus(self, request, pk=None):
        """
        Endpoint para cambiar el estatus de un empleado.
        Si el estatus cambia a 'proceso_finiquito', elimina las nóminas no pagadas del empleado.
        """
        empleado = self.get_object()
        serializer = EmpleadoSerializer(
            empleado, 
            data=request.data, 
            partial=True  # Permite actualizar solo algunos campos del modelo
        )

        if serializer.is_valid():
            nuevo_estatus = serializer.validated_data.get('estatus')
            empleado = serializer.save()  # Guarda los cambios en el empleado
            
            # Si el estatus cambia a 'proceso_finiquito', elimina las nóminas no pagadas
            if nuevo_estatus == 'proceso_finiquito':
                nominas_a_eliminar = Nomina.objects.filter(empleado=empleado).exclude(estatus='pagada')
                eliminadas = nominas_a_eliminar.count()
                nominas_a_eliminar.delete()
                return Response({
                    'status': 'Estatus actualizado correctamente',
                    'detalle': f'Se eliminaron {eliminadas} nóminas no pagadas del empleado.'
                }, status=status.HTTP_200_OK)
            
            return Response({'status': 'Estatus actualizado correctamente'}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
    # Endpoint descargar documentos
    @action(detail=True, methods=['get'], url_path='descargar-documentos')
    def descargar_documentos(self, request, pk=None):
        """
        Endpoint para descargar todos los documentos de un empleado en un archivo ZIP.
        """
        empleado = self.get_object()  # Obtener el empleado a partir del `pk`

        # Crear un buffer en memoria para el archivo ZIP
        zip_buffer = io.BytesIO()

        with ZipFile(zip_buffer, 'w') as zip_file:
            # Carpeta raíz con el nombre del empleado
            root_folder = empleado.nombre_completo.replace(" ", "_")

            # Documentos del usuario
            self._agregar_documentos_al_zip(zip_file, f'{root_folder}/Documentos del Usuario', [
                ('Identificación', empleado.identificacion_oficial.path),
                ('Acta de Nacimiento', empleado.acta_nacimiento.path),
                ('RFC', empleado.constancia_situacion_fiscal.path),
                ('CURP', empleado.pdf_curp.path),
                ('NSS', empleado.comprobante_nss.path),
                ('Alta IMSS', empleado.alta_imss.path if empleado.alta_imss else None),
                ('Comprobante de Domicilio', empleado.comprobante_domicilio.path),
                ('Estado de Cuenta', empleado.estado_cuenta.path),
                ('Constancia de Estudio', empleado.constancia_estudio.path),
                ('Contrato Laboral', empleado.contrato_laboral.path),
                ('Curriculum Vitae', empleado.curriculum_vitae.path),
            ])

            # Documentos de separación laboral
            self._agregar_documentos_al_zip(zip_file, f'{root_folder}/Documentos de Separación Laboral', [
                ('Carta de Renuncia', empleado.carta_renuncia.path if empleado.carta_renuncia else None),
                ('Finiquito Firmado', empleado.finiquito_firmado.path if empleado.finiquito_firmado else None),
                ('Baja del IMSS', empleado.baja_imss.path if empleado.baja_imss else None),
                ('Comprobante de Transferencia', empleado.comprobante_transferencia_finiquito.path if empleado.comprobante_transferencia_finiquito else None),
            ])

            # Documentos por eventos
            for documento in empleado.documentos.all():
                tipo_documento_folder = f'{root_folder}/Documentos por Eventos/{documento.get_tipo_documento_display()}'
                self._agregar_documento_individual_al_zip(zip_file, tipo_documento_folder, documento.archivo.path)

        # Finalizar el buffer y preparar para la descarga
        zip_buffer.seek(0)

        # Retornar el archivo ZIP como respuesta
        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename=documentos_{empleado.nombre_completo}.zip'
        return response


    def _agregar_documentos_al_zip(self, zip_file, carpeta, documentos):
        """
        Agrega una lista de documentos al archivo ZIP, utilizando rutas locales de los archivos.
        """
        for nombre, file_path in documentos:
            if file_path and os.path.exists(file_path):
                try:
                    # Leer el archivo directamente desde el sistema de archivos
                    with open(file_path, 'rb') as archivo:
                        file_name = f"{carpeta}/{nombre.replace(' ', '_')}.pdf"
                        zip_file.writestr(file_name, archivo.read())
                except Exception as e:
                    print(f"Error al agregar el archivo '{nombre}' desde {file_path}: {e}")


    def _agregar_documento_individual_al_zip(self, zip_file, carpeta, file_path):
        """
        Agrega un documento individual al archivo ZIP, utilizando su ruta local.
        """
        if file_path and os.path.exists(file_path):
            try:
                # Leer el archivo directamente desde el sistema de archivos
                with open(file_path, 'rb') as archivo:
                    # Obtener el nombre del archivo desde la ruta
                    file_name = os.path.basename(file_path)
                    # Agregar el archivo al ZIP
                    zip_file.writestr(f"{carpeta}/{file_name}", archivo.read())
            except Exception as e:
                print(f"Error al agregar el archivo desde {file_path}: {e}")

    

class DocumentoEmpleadoViewSet(viewsets.ModelViewSet):
    queryset = DocumentoEmpleado.objects.all()
    serializer_class = DocumentoEmpleadoSerializer

    # Endpoint adicional para obtener todos los documentos de un empleado específico
    @action(detail=False, methods=['get'], url_path='empleado/(?P<empleado_id>[^/.]+)')
    def documentos_por_empleado(self, request, empleado_id=None):
        """
        Devuelve todos los documentos de un empleado específico.
        """
        try:
            documentos = DocumentoEmpleado.objects.filter(empleado_id=empleado_id)
            serializer = self.get_serializer(documentos, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Empleado.DoesNotExist:
            return Response({"detail": "Empleado no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        

class UniversidadViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Universidad instances.
    """
    queryset = Universidad.objects.all()
    serializer_class = UniversidadSerializer
    permission_classes = [IsAuthenticated]  # Ensures only authenticated users can access this
    


class PracticanteResidenteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para el CRUD de Practicantes y Residentes
    """
    queryset = PracticanteResidente.objects.all()
    serializer_class = PracticanteResidenteSerializer


    @action(detail=True, methods=['patch'], url_path='cambiar-estado', url_name='cambiar_estado')
    def cambiar_estado(self, request, pk=None):
        """
        Endpoint para cambiar el estado de Practicante o Residente.
        Si el estado cambia a 'baja', elimina las nóminas no pagadas.
        """
        try:
            practicante_residente = self.get_object()
            nuevo_estado = request.data.get('estado')

            if nuevo_estado not in ['alta', 'baja']:
                return Response(
                    {"error": "Estado no válido. Debe ser 'alta' o 'baja'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            practicante_residente.estado = nuevo_estado

            if nuevo_estado == 'baja':
                # Establecer la fecha de baja, si se proporciona
                practicante_residente.fecha_baja = request.data.get('fecha_baja')

                # Eliminar nóminas no pagadas
                nominas_a_eliminar = NominaResidentesPracticantes.objects.filter(
                    practicante_residente=practicante_residente
                ).exclude(estatus='pagado')

                eliminadas = nominas_a_eliminar.count()
                nominas_a_eliminar.delete()

                # Guardar los cambios en el objeto practicante_residente
                practicante_residente.save()

                return Response(
                    {
                        "message": f"Estado cambiado a {nuevo_estado} exitosamente.",
                        "detalle": f"Se eliminaron {eliminadas} nóminas no pagadas."
                    },
                    status=status.HTTP_200_OK
                )

            # Guardar los cambios en el objeto practicante_residente
            practicante_residente.save()

            return Response(
                {"message": f"Estado cambiado a {nuevo_estado} exitosamente."},
                status=status.HTTP_200_OK
            )

        except PracticanteResidente.DoesNotExist:
            return Response(
                {"error": "Practicante o Residente no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )
        
    @action(detail=True, methods=['get'], url_path='descargar-documentos')
    def descargar_documentos(self, request, pk=None):
        """
        Endpoint para descargar todos los documentos de un practicante o residente en un archivo ZIP.
        """
        practicante_residente = self.get_object()  # Obtener el practicante/residente a partir del `pk`

        # Crear un buffer en memoria para el archivo ZIP
        zip_buffer = io.BytesIO()

        with ZipFile(zip_buffer, 'w') as zip_file:
            # Carpeta raíz con el nombre del practicante/residente y su universidad
            root_folder = os.path.join(
                practicante_residente.universidad.nombre.replace(" ", "_"),
                practicante_residente.tipo.capitalize(),
                practicante_residente.nombre_completo.replace(" ", "_")
            )

            # Documentos del practicante/residente
            self._agregar_documentos_al_zip(zip_file, f'{root_folder}/Documentos Personales', [
                ('Identificación', practicante_residente.identificacion_oficial.path),
                ('Acta de Nacimiento', practicante_residente.acta_nacimiento.path),
                ('RFC', practicante_residente.pdf_rfc.path),
                ('CURP', practicante_residente.pdf_curp.path),
                ('NSS', practicante_residente.pdf_numero_seguro_social.path),
                ('Comprobante de Domicilio', practicante_residente.comprobante_domicilio.path),
                ('Estado de Cuenta', practicante_residente.estado_cuenta.path),
                ('Carta de Presentación', practicante_residente.carta_presentacion.path),
                ('Curriculum Vitae', practicante_residente.curriculum_vitae.path),
            ])

            # Documentos cargados desde el catálogo
            for documento in practicante_residente.documentos_cargados.all():
                catalog_folder = os.path.join(root_folder, 'Documentos por Categoría', documento.catalogo_documento.nombre_documento.replace(" ", "_"))
                self._agregar_documento_individual_al_zip(zip_file, catalog_folder, documento.archivo.path)

        # Finalizar el buffer y preparar para la descarga
        zip_buffer.seek(0)

        # Retornar el archivo ZIP como respuesta
        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename=documentos_{practicante_residente.nombre_completo}.zip'
        return response

    def _agregar_documentos_al_zip(self, zip_file, carpeta, documentos):
        """
        Agrega una lista de documentos al archivo ZIP, utilizando rutas locales de los archivos.
        """
        for nombre, file_path in documentos:
            if file_path and os.path.exists(file_path):
                try:
                    # Leer el archivo directamente desde el sistema de archivos
                    with open(file_path, 'rb') as archivo:
                        file_name = f"{carpeta}/{nombre.replace(' ', '_')}.pdf"
                        zip_file.writestr(file_name, archivo.read())
                except Exception as e:
                    print(f"Error al agregar el archivo '{nombre}' desde {file_path}: {e}")

    def _agregar_documento_individual_al_zip(self, zip_file, carpeta, file_path):
        """
        Agrega un documento individual al archivo ZIP, utilizando su ruta local.
        """
        if file_path and os.path.exists(file_path):
            try:
                # Leer el archivo directamente desde el sistema de archivos
                with open(file_path, 'rb') as archivo:
                    # Obtener el nombre del archivo desde la ruta
                    file_name = os.path.basename(file_path)
                    # Agregar el archivo al ZIP
                    zip_file.writestr(f"{carpeta}/{file_name}", archivo.read())
            except Exception as e:
                print(f"Error al agregar el archivo desde {file_path}: {e}")



class CatalogoDocumentoViewSet(viewsets.ModelViewSet):
    """
    CRUD para el modelo CatalogoDocumento.
    """
    queryset = CatalogoDocumento.objects.all()
    serializer_class = CatalogoDocumentoSerializer

    def get_queryset(self):
        """
        Permite filtrar documentos por universidad o tipo.
        """
        universidad_id = self.request.query_params.get('universidad')
        tipo = self.request.query_params.get('tipo')
        queryset = super().get_queryset()
        if universidad_id:
            queryset = queryset.filter(universidad_id=universidad_id)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        return queryset


class DocumentoCargadoViewSet(viewsets.ModelViewSet):
    """
    CRUD para el modelo DocumentoCargado.
    """
    queryset = DocumentoCargado.objects.all()
    serializer_class = DocumentoCargadoSerializer

    def get_queryset(self):
        """
        Filtra documentos por practicante o residente.
        """
        practicante_residente_id = self.request.query_params.get('practicante_residente')
        queryset = super().get_queryset()
        if practicante_residente_id:
            queryset = queryset.filter(practicante_residente_id=practicante_residente_id)
        return queryset

    @action(detail=False, methods=['get'], url_path='practicante-residente-documentos')
    def documentos_por_practicante_residente(self, request):
        """
        Retorna todos los documentos cargados para un practicante o residente.
        """
        practicante_residente_id = request.query_params.get('practicante_residente')
        if not practicante_residente_id:
            return Response(
                {"error": "El parámetro 'practicante_residente' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST
            )
        documentos = self.queryset.filter(practicante_residente_id=practicante_residente_id)
        serializer = self.get_serializer(documentos, many=True)
        return Response(serializer.data)
    
class DocumentoRequisitosViewSet(viewsets.ModelViewSet):
    queryset = DocumentoRequisitos.objects.all()
    serializer_class = DocumentoRequisitosSerializer

    @action(detail=True, methods=['get'], url_path='requisitos')
    def mostrar_pdf(self, request, pk=None):
        """
        Endpoint para mostrar el PDF asociado a un DocumentoRequisitos en el navegador.
        """
        documento = self.get_object()
        pdf_file = documento.pdfRequisitosDocumentacion 

        try:
            response = FileResponse(pdf_file.open('rb'), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{pdf_file.name}"'
            return response
        except FileNotFoundError:
            return Response({"error": "El archivo no existe."}, status=404)