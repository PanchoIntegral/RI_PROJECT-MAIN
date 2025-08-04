from decimal import Decimal
from rest_framework import serializers
from django.utils import timezone

from ri_rh.models import CatalogoDocumento, DocumentoCargado, DocumentoEmpleado, Empleado, PracticanteResidente, Puesto, Universidad, DocumentoRequisitos

class PuestoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Puesto
        fields = '__all__'
        

class EmpleadoSerializer(serializers.ModelSerializer):
    antiguedad = serializers.SerializerMethodField()
    dias_vacaciones = serializers.SerializerMethodField()

    class Meta:
        model = Empleado
        fields = [
            'id',
            'nombre_completo',
            'identificacion_oficial',
            'puesto',
            'fecha_nacimiento',
            'acta_nacimiento',
            'escolaridad',
            'constancia_estudio',
            'salario_diario',
            'clabe_interbancaria',
            'estado_cuenta',
            'numero_contacto',
            'contacto_emergencia',
            'rfc',
            'constancia_situacion_fiscal',
            'curp',
            'pdf_curp',
            'numero_seguro_social',
            'comprobante_nss',
            'alta_imss',
            'direccion_completa',
            'comprobante_domicilio',
            'monto_retencion_infonavit',
            'aviso_retencion_infonavit',
            'carta_recomendacion_1',
            'carta_recomendacion_2',
            'carta_recomendacion_3',
            'carta_no_antecedentes_penales',
            'contrato_laboral',
            'curriculum_vitae',
            'carta_oferta',
            'examen_medico',
            'carta_renuncia',
            'finiquito_firmado',
            'baja_imss',
            'comprobante_transferencia_finiquito',
            'estatus',
            'fecha_alta',
            'fecha_baja',
            'antiguedad',
            'dias_vacaciones',
        ]
        read_only_fields = ['fecha_alta']

    def get_antiguedad(self, obj):
        return obj.antiguedad()

    def get_dias_vacaciones(self, obj):
        return obj.calcular_vacaciones()


class DocumentoEmpleadoSerializer(serializers.ModelSerializer):
    tipo_documento_display = serializers.CharField(source='get_tipo_documento_display', read_only=True)

    class Meta:
        model = DocumentoEmpleado
        fields = [
            'id',  # Para tener una referencia única del documento en la API
            'empleado',
            'tipo_documento',
            'tipo_documento_display',  # Campo de solo lectura para mostrar el nombre legible del tipo de documento
            'archivo',
            'fecha',
        ]
        read_only_fields = ['fecha']
        

class UniversidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Universidad
        fields = ['id', 'nombre', 'direccion', 'numero_contacto']
        
        

class PracticanteResidenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticanteResidente
        fields = [
            'id',
            'nombre_completo',
            'identificacion_oficial',
            'tipo',
            'universidad',
            'puesto',
            'fecha_nacimiento',
            'acta_nacimiento',
            'salario_diario',
            'clabe_interbancaria',
            'estado_cuenta',
            'numero_contacto',
            'contacto_emergencia',
            'rfc',
            'pdf_rfc',
            'curp',
            'pdf_curp',
            'numero_seguro_social',
            'pdf_numero_seguro_social',
            'direccion_completa',
            'comprobante_domicilio',
            'carta_presentacion',
            'curriculum_vitae',
            'estado',
            'fecha_alta',
            'fecha_baja',
        ]
        read_only_fields = ['fecha_alta']
        
        

class CatalogoDocumentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogoDocumento
        fields = ['id', 'universidad', 'tipo', 'nombre_documento', 'obligatorio']


class DocumentoCargadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentoCargado
        fields = ['id', 'practicante_residente', 'catalogo_documento', 'archivo', 'fecha_carga']
        read_only_fields = ['fecha_carga']  # Make sure fecha_carga is read-only

class DocumentoRequisitosSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentoRequisitos
        fields = '__all__'
