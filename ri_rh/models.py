import calendar
from datetime import date, datetime, timedelta
import os
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from simple_history.models import HistoricalRecords
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from django.utils.timezone import now
from django.db.models import Sum
from dateutil.relativedelta import relativedelta
from django.db.models import F
from ri_compras.models import Nomina, NominaResidentesPracticantes, Vacaciones,Isr,AportacionObreroPatronales

# Puesto
class Puesto(models.Model):
    TIPO_PUESTO_CHOICES = [
        ('administrativo', 'Administrativo'),
        ('directo', 'Directo'),
        ('indirecto', 'Indirecto'),
    ]
    
    nombre = models.CharField(max_length=255, unique=True)
    tipos = models.CharField(max_length=15, choices=TIPO_PUESTO_CHOICES)

    class Meta:
        indexes = [
            models.Index(fields=['nombre']),
            models.Index(fields=['tipos']),
        ]

    def __str__(self):
        return f"{self.nombre} - {self.get_tipos_display()}"


# Tabla de empleado
class Empleado(models.Model):
    ESCOLARIDAD_CHOICES = [
        ('primaria', 'Primaria'),
        ('secundaria', 'Secundaria'),
        ('preparatoria', 'Preparatoria'),
        ('universidad', 'Universidad'),
        ('postgrado', 'Postgrado'),
    ]
    
    ESTATUS_CHOICES = [
        ('activo', 'Activo'),
        ('proceso_finiquito', 'Proceso Finiquito'),
        ('finiquitado', 'Finiquitado'),
    ]
    
    # Campos básicos de información personal
    nombre_completo = models.CharField(max_length=255)
    identificacion_oficial = models.FileField(upload_to='DocumentosEmpleado/Identificacion/')
    puesto = models.ForeignKey(Puesto, on_delete=models.CASCADE)
    fecha_nacimiento = models.DateField()
    acta_nacimiento = models.FileField(upload_to='DocumentosEmpleado/ActaNacimiento/')
    escolaridad = models.CharField(max_length=15, choices=ESCOLARIDAD_CHOICES)
    constancia_estudio = models.FileField(upload_to='DocumentosEmpleado/ConstanciaEstudio/')
    salario_diario = models.DecimalField(max_digits=10, decimal_places=2)
    clabe_interbancaria = models.CharField(max_length=18)
    estado_cuenta = models.FileField(upload_to='DocumentosEmpleado/EstadosDeCuentas/')
    numero_contacto = models.CharField(max_length=80)
    contacto_emergencia = models.CharField(max_length=80)
    rfc = models.CharField(max_length=13)
    constancia_situacion_fiscal = models.FileField(upload_to='DocumentosEmpleado/ConstanciaSituacionFiscal/')
    curp = models.CharField(max_length=18)
    pdf_curp = models.FileField(upload_to='DocumentosEmpleado/CURP/')
    
    # Información de seguridad social y otros documentos
    numero_seguro_social = models.CharField(max_length=11)
    comprobante_nss = models.FileField(upload_to='DocumentosEmpleado/NSS/')
    alta_imss = models.FileField(upload_to='DocumentosEmpleado/AltaIMSS/', blank=True, null=True)
    
    # Información de dirección y otros documentos personales
    direccion_completa = models.TextField()
    comprobante_domicilio = models.FileField(upload_to='DocumentosEmpleado/ComprobanteDeDomicilio/')
    monto_retencion_infonavit = models.DecimalField(max_digits=10, decimal_places=2)
    aviso_retencion_infonavit = models.FileField(upload_to='DocumentosEmpleado/AvisoDeRetencionInfonavit/')
    
    # Cartas de recomendación y otros documentos laborales
    carta_recomendacion_1 = models.FileField(upload_to='DocumentosEmpleado/CartasDeRecomendacion/')
    carta_recomendacion_2 = models.FileField(upload_to='DocumentosEmpleado/CartasDeRecomendacion/')
    carta_recomendacion_3 = models.FileField(upload_to='DocumentosEmpleado/CartasDeRecomendacion/')
    carta_no_antecedentes_penales = models.FileField(upload_to='DocumentosEmpleado/CartaDeNoAntecedentesPenales/')
    contrato_laboral = models.FileField(upload_to='DocumentosEmpleado/ContratoLaboral/')
    curriculum_vitae = models.FileField(upload_to='DocumentosEmpleado/CurriculumVitae/')
    carta_oferta = models.FileField(upload_to='DocumentosEmpleado/CartaOferta/', blank=True, null=True)
    examen_medico = models.FileField(upload_to='DocumentosEmpleado/ExamenMedico/')

    # Campos adicionales opcionales relacionados al proceso de finiquito
    carta_renuncia = models.FileField(upload_to='DocumentosEmpleado/CartaRenuncia/', blank=True, null=True)
    finiquito_firmado = models.FileField(upload_to='DocumentosEmpleado/FiniquitoFirmado/', blank=True, null=True)
    baja_imss = models.FileField(upload_to='DocumentosEmpleado/BajaImss/', blank=True, null=True)
    comprobante_transferencia_finiquito = models.FileField(upload_to='DocumentosEmpleado/ComprobanteTransferenciaFiniquito/', blank=True, null=True)

    # Estatus del empleado
    estatus = models.CharField(max_length=20, choices=ESTATUS_CHOICES, default='activo')
    
    # Fecha de alta del empleado (automática y no editable)
    fecha_alta = models.DateField(auto_now_add=True, editable=False)

    # Fecha de baja del empleado (opcional)
    fecha_baja = models.DateField(blank=True, null=True)

    def antiguedad(self):
        anio_actual = timezone.now().year 
        diferencia = anio_actual - self.fecha_alta.year

        if diferencia <= 1:
         diferencia = 1
         
         return diferencia
        else:
         
         return diferencia
     
    def calcular_vacaciones(self):
        """
        Calcula los días de vacaciones basados en la antigüedad y la tabla de Vacaciones.
        """
        antiguedad = self.antiguedad()
        vacaciones = Vacaciones.objects.filter(años__lte=antiguedad).order_by('-años').first()
        if vacaciones:
            return vacaciones.dias
        return 0  # Si no hay registro en la tabla, retorna 0 días

    def __str__(self):
        return self.nombre_completo
    

from django.db.models.signals import post_save
from django.dispatch import receiver
@receiver(post_save, sender=Empleado)
def crear_nomina_inicial(sender, instance, created, **kwargs):
    """
    Crea automáticamente una nómina inicial para un empleado recién creado.
    """
    from decimal import Decimal  # Asegúrate de importar Decimal
    if created:  # Solo cuando el empleado es creado por primera vez
        Nomina.objects.create(
            empleado=instance,
            dias_trabajados=0,
            tiempo_extra=Decimal('0.0'),
            vales_despensa=Decimal('0.0'),
            vales_gasolina=Decimal('0.0'),
            monto_aprobado_nomina=Decimal('0.0'),
            deduccion_infonavit=Decimal('0.0'),
            deduccion_prestamos=Decimal('0.0'),
            subsidio_empleo=Decimal('0.0'),
            salario_diario_integral=Decimal('0.0'),
            bruto_semanal=Decimal('0.0'),
            suma_percepciones=Decimal('0.0'),
            impuestos_isr=Decimal('0.0'),
            imss_obrero=Decimal('0.0'),
            cuota_fija=Decimal('0.0'),
            excedente_obrero=Decimal('0.0'),
            gmp_obrero=Decimal('0.0'),
            rt_obrero=Decimal('0.0'),
            iv_obrero=Decimal('0.0'),
            gps_obrero=Decimal('0.0'),
            en_dinero_obrero=Decimal('0.0'),
            imss_patronal=Decimal('0.0'),
            cuota_fija_patronal=Decimal('0.0'),
            excedente_patronal=Decimal('0.0'),
            gmp_patronal=Decimal('0.0'),
            rt_patronal=Decimal('0.0'),
            iv_patronal=Decimal('0.0'),
            gps_patronal=Decimal('0.0'),
            en_dinero_patronal=Decimal('0.0'),
            infonavit_patronal=Decimal('0.0'),
            aportacion_retiro_imss=Decimal('0.0'),
            ceav_obrero=Decimal('0.0'),
            ceav_patronal=Decimal('0.0'),
            suma_deducciones=Decimal('0.0'),
            nomina_a_depositar=Decimal('0.0'),
            total_impuestos=Decimal('0.0'),
            nomina_semanal_fiscal=Decimal('0.0'),
            observaciones="",
            estatus='inicial',
            fecha_nomina=timezone.now().date(),
        )
    

def documento_upload_path(instance, filename):
    # Define una carpeta basada en el tipo de documento
    tipo_carpeta = instance.get_tipo_documento_display().replace(" ", "_")
    # Devuelve el path donde se almacenará el archivo
    return f'DocumentosEmpleado/{tipo_carpeta}/{filename}'

class DocumentoEmpleado(models.Model):
    TIPOS_DOCUMENTO_CHOICES = [
        ('actas_administrativas', 'Actas Administrativas'),
        ('antidoping', 'Antidopings'),
        ('aumento_sueldo', 'Aumento de Sueldo'),
        ('capacitaciones', 'Capacitaciones'),
        ('descuento_pension', 'Descuento de Pensión Alimenticia'),
        ('uniforme_seguridad', 'Entrega de Uniforme y Seguridad'),
        ('vacaciones', 'Vacaciones'),
        ('aguinaldo', 'Pago de Aguinaldo'),
        ('prima_vacacional', 'Prima Vacacional'),
        ('prestaciones', 'Prestaciones'),
        ('ptu', 'PTU'),
        ('incapacidades', 'Incapacidades'),
        ('recibo_nomina', 'Recibo de Nómina'),
        ('entradas_salidas', 'Entradas y Salidas'),
    ]

    empleado = models.ForeignKey('Empleado', on_delete=models.CASCADE, related_name='documentos')
    tipo_documento = models.CharField(max_length=50, choices=TIPOS_DOCUMENTO_CHOICES)
    archivo = models.FileField(upload_to=documento_upload_path)
    fecha = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.empleado.nombre_completo} - {self.get_tipo_documento_display()}"
    
    
class Universidad(models.Model):
    nombre = models.CharField(max_length=255, unique=True)  # Name of the university
    direccion = models.TextField()  # Address of the university
    numero_contacto = models.CharField(max_length=15)  # Contact number

    def __str__(self):
        return self.nombre
    
    

class PracticanteResidente(models.Model):
    TIPO_CHOICES = [
        ('practicante', 'Practicante'),
        ('residente', 'Residente'),
    ]

    ESTADO_CHOICES = [
        ('alta', 'Alta'),
        ('baja', 'Baja'),
    ]

    nombre_completo = models.CharField(max_length=255)
    identificacion_oficial = models.FileField(upload_to='PracticantesResidentes/Identificacion/')
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    universidad = models.ForeignKey('Universidad', on_delete=models.CASCADE, related_name='practicantes_residentes')
    puesto = models.ForeignKey('Puesto', on_delete=models.CASCADE, related_name='practicantes_residentes')
    fecha_nacimiento = models.DateField()
    acta_nacimiento = models.FileField(upload_to='PracticantesResidentes/ActaNacimiento/')
    salario_diario = models.DecimalField(max_digits=10, decimal_places=2)
    clabe_interbancaria = models.CharField(max_length=18)
    estado_cuenta = models.FileField(upload_to='PracticantesResidentes/EstadosDeCuenta/')
    numero_contacto = models.CharField(max_length=80)
    contacto_emergencia = models.CharField(max_length=80)
    rfc = models.CharField(max_length=13)
    pdf_rfc = models.FileField(upload_to='PracticantesResidentes/RFC/')
    curp = models.CharField(max_length=18)
    pdf_curp = models.FileField(upload_to='PracticantesResidentes/CURP/')
    numero_seguro_social = models.CharField(max_length=11)
    pdf_numero_seguro_social = models.FileField(upload_to='PracticantesResidentes/SeguroSocial/')
    direccion_completa = models.TextField()
    comprobante_domicilio = models.FileField(upload_to='PracticantesResidentes/ComprobanteDomicilio/')
    carta_presentacion = models.FileField(upload_to='PracticantesResidentes/CartaPresentacion/')
    curriculum_vitae = models.FileField(upload_to='PracticantesResidentes/CurriculumVitae/')
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='alta')
    fecha_alta = models.DateField(auto_now_add=True, editable=False)
    fecha_baja = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre_completo} ({self.tipo})"
    
    
    

@receiver(post_save, sender=PracticanteResidente)
def crear_nomina_practicante_residente(sender, instance, created, **kwargs):
    """
    Crea automáticamente una nómina inicial en cero para un practicante o residente recién creado.
    """
    if created:  # Solo cuando el practicante/residente es creado por primera vez
        NominaResidentesPracticantes.objects.create(
            practicante_residente=instance,
            estatus='inicial',
            fecha_nomina=instance.fecha_alta,  # Utiliza la fecha de alta del practicante
            monto_aprobado=Decimal('0.0'),
            apoyo_economico=Decimal('0.0'),
            observaciones=" "
        )
        
    

def documento_cargado_upload_path(instance, filename):
    """
    Genera la ruta de subida para los documentos cargados.
    La estructura es: PracticantesResidentes/<Universidad>/<Practicantes|Residentes>/<Documento>/<filename>
    """
    universidad = instance.practicante_residente.universidad.nombre.replace(" ", "_")
    tipo = instance.practicante_residente.tipo
    documento = instance.catalogo_documento.nombre_documento.replace(" ", "_")
    
    return os.path.join(
        'PracticantesResidentes',
        universidad,
        tipo,
        documento,
        filename
    )

    
class CatalogoDocumento(models.Model):
    TIPO_CHOICES = [
        ('practicante', 'Practicante'),
        ('residente', 'Residente'),
    ]

    universidad = models.ForeignKey(Universidad, on_delete=models.CASCADE, related_name='documentos_catalogo')
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    nombre_documento = models.CharField(max_length=255)
    obligatorio = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.universidad.nombre} - {self.get_tipo_display()} - {self.nombre_documento}"



class DocumentoCargado(models.Model):
    practicante_residente = models.ForeignKey(
        'PracticanteResidente', on_delete=models.CASCADE, related_name='documentos_cargados'
    )
    catalogo_documento = models.ForeignKey(CatalogoDocumento, on_delete=models.CASCADE, related_name='documentos_cargados')
    archivo = models.FileField(upload_to=documento_cargado_upload_path)  # Ruta personalizada
    fecha_carga = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.practicante_residente.nombre_completo} - {self.catalogo_documento.nombre_documento}"
        
class DocumentoRequisitos(models.Model):
    pdfRequisitosDocumentacion = models.FileField(upload_to='DocumentosRequisitos/')

    def __str__(self):
        return f"{self.pdfRequisitosDocumentacion}"
