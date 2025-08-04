import logging
from django.db import models
from django.forms import ValidationError
from ri_compras.models import Usuarios
from django.db import models
from django.core.validators import RegexValidator
from django.core.validators import MinValueValidator
from django.utils.timezone import now
from django.utils import timezone
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

## Modelo de espesor de materiales
from django.db import models

## Modelo de espesor de materiales
class Espesor(models.Model):
    nombre_comercial = models.CharField(
        max_length=50,
        db_index=True,
        unique=True,
        verbose_name="Nombre Comercial",
        help_text="Ejemplo: 3/16, 1/4, etc."
    )
    valor_pulgadas = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        verbose_name="Valor en Pulgadas",
        help_text="Valor decimal en pulgadas, por ejemplo: 0.1875"
    )

    class Meta:
        verbose_name = "Espesor"
        verbose_name_plural = "Espesores"
        ordering = ["valor_pulgadas"]
        indexes = [
            models.Index(fields=["nombre_comercial"]),
            models.Index(fields=["valor_pulgadas"]),
        ]

    def __str__(self):
        return f"{self.nombre_comercial} ({self.valor_pulgadas}\" pulgadas)"
    
class PresentacionMaterial(models.Model):
    nombre_comercial = models.CharField(
        max_length=100,
        verbose_name="Nombre comercial",
        help_text="Ejemplo: Calibre 18, 1/4\", 3 mm",
    )
    largo = models.DecimalField(
        max_digits=20, decimal_places=9,
        null=True, blank=True,
        db_index=True,
        verbose_name="Largo (pulgadas)",
        help_text="Largo en pulgadas"
    )
    ancho = models.DecimalField(
        max_digits=20, decimal_places=9,
        null=True, blank=True,
        db_index=True,
        verbose_name="Ancho (pulgadas)",
        help_text="Ancho en pulgadas"
    )
    diametro = models.DecimalField(
        max_digits=20, decimal_places=9,
        null=True, blank=True,
        db_index=True,
        verbose_name="Diámetro (pulgadas)",
        help_text="Diámetro si es un tubo, barra, etc. (en pulgadas)"
    )
    espesor = models.ForeignKey(
        "Espesor",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="presentaciones",
        db_index=True,
        verbose_name="Espesor asociado",
        help_text="Espesor si aplica a esta presentación"
    )
    requiere_placa_lamina = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Requiere placa o lamina",
        help_text="Indica si la pieza requiere placa o lamina"
    )

    class Meta:
        verbose_name = "Presentación de Material"
        verbose_name_plural = "Presentaciones de Material"
        ordering = ["nombre_comercial"]

    def __str__(self):
        return self.nombre_comercial
    

## Modelo de materiales
class Material(models.Model):
    TIPO_OPCIONES = [
        ("Aluminio", "Aluminio"),
        ("Plastico", "Plastico"),
        ("Acero Negro", "Acero Negro"),
        ("Inoxidable", "Inoxidable"),
        ("Otro", "Otro"),
    ]
    nombre = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name="Nombre del Material",
        help_text="Ejemplo: Acero Inoxidable, Policarbonato"
    )
    tipo = models.CharField(
        max_length=50,
        choices=TIPO_OPCIONES,
        db_index=True,
        verbose_name="Tipo de Material",
        help_text="Selecciona el tipo de material"
    )


    class Meta:
        verbose_name = "Material"
        verbose_name_plural = "Materiales"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.tipo})"


class OrdenProduccion(models.Model):
    ESTADO_OPCIONES = [
        ("Activo", "Activo"),
        ("Finalizado", "Finalizado"),
        ("Rechazado", "Rechazado"),
    ]

    codigo_orden = models.CharField(
        max_length=50,
        unique=True,  # Evita duplicados
        db_index=True,
        verbose_name="Código de Orden",
        help_text="Código único de la orden de producción"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,  # Se asigna automáticamente la fecha al crear
        verbose_name="Fecha de Creación"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_OPCIONES,  # Solo permite los valores definidos
        db_index=True,
        default="Activo",
        verbose_name="Estado de la Orden",
        help_text="Estado actual de la orden de producción"
    )

    class Meta:
        verbose_name = "Orden de Producción"
        verbose_name_plural = "Órdenes de Producción"
        ordering = ["-fecha_creacion"]  # Ordena por las más recientes primero

    def __str__(self):
        return f"{self.codigo_orden} - {self.estado}"
    
    
class Pieza(models.Model):
    ESTADOS_TRACKING = [
        ("Diseño", "Diseño"),
        ("Asignación de Material/Presentación", "Asignación de Material/Presentación"),
        ("Asignación de Nesteo", "Asignación de Nesteo"),
        ("Asignación de procesos", "Asignación de procesos"),
        ("Manufactura", "Manufactura"),
        ("Calidad", "Calidad"),
        ("Finalizado", "Finalizado"),
        ("Finalizado en Rack", "Finalizado en Rack"),
        ("Scrap de Diseño", "Scrap de Diseño"),
        ("Retrabajo de Diseño", "Retrabajo de Diseño"),
    ]

    ESTADOS_PRODUCCION = [
        ("Pendiente", "Pendiente"),
        ("Rechazado", "Rechazado"),
        ("Aprobado", "Aprobado"),
        ("Finalizado", "Finalizado"),
    ]

    consecutivo = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name="Consecutivo de Pieza",
        help_text="Código único que identifica la pieza"
    )
    orden_produccion = models.ForeignKey(
        "OrdenProduccion",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="piezas",
        verbose_name="Orden de Producción",
        help_text="Orden de producción a la que pertenece la pieza"
    )
    material = models.ForeignKey(
        "Material",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="piezas",
        verbose_name="Material de la Pieza",
        help_text="Material utilizado para fabricar la pieza"
    )
    presentacion = models.ForeignKey(
    "PresentacionMaterial",
    null=True,
    blank=True,
    on_delete=models.SET_NULL,
    related_name="piezas",
    verbose_name="Presentación Asociada",
    help_text="Presentación específica usada en esta pieza"
    )
    total_piezas = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Total de Piezas",
        help_text="Cantidad total de piezas a producir"
    )
    piezas_por_consecutivo = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Piezas por Consecutivo",
        help_text="Cantidad de piezas fabricadas por cada consecutivo"
    )
    piezas_manufacturadas = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Piezas Manufacturadas",
        help_text="Cantidad de piezas que ya han sido fabricadas"
    )
    pdf = models.FileField(
        upload_to="planos_pdfs/",  # Directorio donde se guardarán los PDFs dentro de MEDIA_ROOT
        null=True,
        blank=True,
        verbose_name="PDF de la Pieza",
        help_text="Sube un archivo PDF con detalles de la pieza"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    creado_por = models.ForeignKey(
        Usuarios,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="piezas_creadas",
        verbose_name="Creado por",
        help_text="Usuario que creó la pieza"
    )
    prioritario = models.BooleanField(
        default=False,
        verbose_name="Prioritario",
        help_text="Indica si la pieza tiene prioridad alta"
    )
    estatus_tracking = models.CharField(
        max_length=50,
        choices=ESTADOS_TRACKING,
        null=True,
        blank=True,
        verbose_name="Estatus de Tracking",
        help_text="Estado de la pieza en la línea de producción"
    )
    estado_produccion = models.CharField(
        max_length=50,
        choices=ESTADOS_PRODUCCION,
        null=True,
        blank=True,
        verbose_name="Estado de Producción",
        help_text="Fase actual en la producción de la pieza"
    )
    requiere_nesteo = models.BooleanField(
        default=False,
        verbose_name="Requiere Nesteo",
        help_text="Indica si la pieza requiere proceso de nesteo"
    )
    es_scrap = models.BooleanField(
        default=False,
        verbose_name="Es scrap",
        help_text="Indica si la piezas se tomaran como scrap"
    )
    scrap_piezas = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Total de Piezas en scrap",
        help_text="Cantidad total de pieza en scrap"
    )
    retrabajo = models.BooleanField(
        default=False,
        verbose_name="Retrabajo",
        help_text="Indica si la pieza ha sido enviada a retrabajo"
    )
    comentario_retrabajo = models.TextField(
        null=True,
        blank=True,
        verbose_name="Comentario de Retrabajo",
        help_text="Notas adicionales sobre el retrabajo de la pieza"
    )
    comentario_scrap = models.TextField(
        null=True,
        blank=True,
        verbose_name="Comentario del Scrap",
        help_text="Notas adicionales para indicar el scrap de la pieza"
    )
    asignacionFinalizada = models.BooleanField(
        default=False,
        blank=True,
        verbose_name="asignación Finalizada",
        help_text="Indica si ya no necesita asignarProceso"
    )

    class Meta:
        verbose_name = "Pieza"
        verbose_name_plural = "Piezas"
        ordering = ["-fecha_creacion"]  # Ordena por las más recientes primero

    def __str__(self):
        return f"{self.consecutivo} - {self.orden_produccion.codigo_orden if self.orden_produccion else 'Sin Orden'}"
    
    

class Proceso(models.Model):
    TIPO_OPCIONES = [
        ("Individual", "Individual"),
        ("Nesteo", "Nesteo"),
    ]
    
    AREAS_OPCIONES = [
            ("CNC", "CNC"),
            ("Torno", "Torno"),
            ("Sheet Metal", "Sheet Metal"),
            ("Corte", "Corte"),
            ("Soldadura", "Soldadura"),
    ]

    nombre = models.CharField(
        max_length=100,
        unique=True,  # Evita nombres duplicados
        db_index=True,
        verbose_name="Nombre del Proceso",
        help_text="Ejemplo: Corte Láser, Soldadura, Pintura"
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_OPCIONES,
        db_index=True,
        verbose_name="Tipo de Proceso",
        help_text="Selecciona si el proceso es Individual o Nesteo"
    )
    
    area = models.CharField(
        max_length=50,
        choices=AREAS_OPCIONES,
        db_index=True,
        verbose_name="Área",
        help_text="Área de la planta donde se realiza el proceso",
        null=True,  # Permite valores nulos
        blank=True   # Permite que el campo esté vacío en formularios
    )

    class Meta:
        verbose_name = "Proceso"
        verbose_name_plural = "Procesos"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.tipo})"
    
    

class Maquina(models.Model):
    ESTADO_OPCIONES = [
        ("Activo", "Activo"),
        ("Mantenimiento", "Mantenimiento"),
        ("Averiada", "Averiada"),
    ]

    nombre = models.CharField(
        max_length=100,
        unique=True,  # Evita nombres duplicados
        db_index=True,
        verbose_name="Nombre de la Máquina",
        help_text="Ejemplo: LaserCut 5000, Prensa Hidráulica"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_OPCIONES,
        default="Activo",
        db_index=True,
        verbose_name="Estado de la Máquina",
        help_text="Selecciona el estado actual de la máquina"
    )

    class Meta:
        verbose_name = "Máquina"
        verbose_name_plural = "Máquinas"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.estado})"
    
    
class MaquinaProceso(models.Model):
    maquina = models.ForeignKey(
        "Maquina",
        on_delete=models.CASCADE,
        related_name="procesos",
        verbose_name="Máquina",
        help_text="Máquina asignada al proceso"
    )
    proceso = models.ForeignKey(
        "Proceso",
        on_delete=models.CASCADE,
        related_name="maquinas",
        verbose_name="Proceso",
        help_text="Proceso en el que participa la máquina"
    )

    class Meta:
        verbose_name = "Relación Máquina - Proceso"
        verbose_name_plural = "Relaciones Máquina - Proceso"
        unique_together = ("maquina", "proceso")  # Evita combinaciones duplicadas
        ordering = ["maquina"]

    def __str__(self):
        return f"{self.maquina.nombre} - {self.proceso.nombre}"
    

class AsignacionProceso(models.Model):
    ESTADO_OPCIONES = [
        ("Pendiente", "Pendiente"),
        ("En Curso", "En Curso"),
        ("Finalizado", "Finalizado"),
        ("Con Scrap", "Con Scrap"),
    ]

    proceso = models.ForeignKey(
        "Proceso",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="asignaciones",
        db_index=True,
        verbose_name="Proceso",
        help_text="Proceso asignado"
    )
    pieza = models.ForeignKey(
        "Pieza",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="asignaciones",
        db_index=True,
        verbose_name="Pieza",
        help_text="Pieza en la que se realiza el proceso"
    )
    usuario = models.ForeignKey(
        Usuarios,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="asignaciones",
        db_index=True,
        verbose_name="Operador",
        help_text="Usuario operador asignado al proceso",
    )
    nesteo = models.ForeignKey(
        "Nesteo",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="asignaciones",
        db_index=True,
        verbose_name="Nesteo",
        help_text="Nesteo asociado al proceso"
    )
    maquina = models.ForeignKey(
        "Maquina",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="asignaciones",
        db_index=True,
        verbose_name="Máquina",
        help_text="Máquina asignada al proceso"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_OPCIONES,
        db_index=True,
        verbose_name="Estado",
        help_text="Estado de la asignación del proceso"
    )
    piezas_asignadas = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Piezas Asignadas",
        help_text="Número total de piezas asignadas al proceso"
    )
    piezas_liberadas = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Piezas Liberadas",
        help_text="Cantidad de piezas liberadas"
    )
    piezas_scrap = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Piezas Scrap",
        help_text="Número de piezas descartadas como scrap"
    )
    tiempo_realizacion_min = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Tiempo de Realización (min)",
        help_text="Tiempo estimado de realización en minutos"
    )
    fecha_asignacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Asignación",
        help_text="Fecha en la que se asignó el proceso"
    )
    fecha_inicio = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de Inicio",
        help_text="Fecha de inicio del proceso"
    )
    fecha_finalizacion_estimada = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha Estimada de Finalización",
        help_text="Fecha estimada de finalización del proceso"
    )
    fecha_finalizacion_real = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha Real de Finalización",
        help_text="Fecha real de finalización del proceso"
    )
    pre_asignado = models.BooleanField(
        default=False,
        verbose_name="Pre-Asignado",
        help_text="Indica si la asignación fue planificada previamente"
    )
    prioridad = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Prioridad",
        help_text="Nivel de prioridad en la asignación"
    )
    
    def clean(self):
        errores = []
        is_partial_update = getattr(self, '_partial_update', False)
        
        # Si es PATCH, solo validar campos que están siendo actualizados
        if not is_partial_update:
            # Validaciones completas para POST/PUT
            if not self.nesteo and not self.pieza:
                errores.append(_("❌ Debes especificar al menos un Nesteo o una Pieza."))
            
            if self.piezas_asignadas is None or self.piezas_asignadas <= 0:
                errores.append(_("❌ Las piezas asignadas deben ser mayores a 0."))
                
            if not self.fecha_inicio or not self.fecha_finalizacion_estimada:
                errores.append(_("❌ Debes establecer fecha de inicio y finalización estimada."))
            
            # Validaciones de solapamiento solo para creaciones/updates completos
            if self.fecha_inicio and self.fecha_finalizacion_estimada:
                # Base query para detectar solapamientos de tiempo
                base_query = Q(fecha_inicio__lt=self.fecha_finalizacion_estimada) & Q(fecha_finalizacion_estimada__gt=self.fecha_inicio)
                
                # Excluir el propio objeto si estamos actualizando
                exclude_id = getattr(self, 'id', None)
                
                # Validar solapamiento de operador
                if self.usuario:
                    operador_ocupado = AsignacionProceso.objects.filter(
                        base_query,
                        usuario=self.usuario
                    )
                    if exclude_id:
                        operador_ocupado = operador_ocupado.exclude(id=exclude_id)
                    
                    if operador_ocupado.exists():
                        errores.append(_("❌ El operador ya tiene un proceso asignado en ese rango de tiempo."))
                
                # Validar solapamiento de máquina
                if self.maquina:
                    maquina_ocupada = AsignacionProceso.objects.filter(
                        base_query,
                        maquina=self.maquina
                    )
                    if exclude_id:
                        maquina_ocupada = maquina_ocupada.exclude(id=exclude_id)
                    
                    if maquina_ocupada.exists():
                        errores.append(_("❌ La máquina ya está ocupada en ese rango de tiempo."))
                
                # Si hay proceso pero no hay máquina específica, validar las máquinas requeridas
                elif self.proceso:
                    maquinas_requeridas = list(self.proceso.maquinas.values_list("maquina_id", flat=True))
                    if maquinas_requeridas:
                        maquinas_ocupadas = AsignacionProceso.objects.filter(
                            base_query,
                            maquina__id__in=maquinas_requeridas
                        )
                        if exclude_id:
                            maquinas_ocupadas = maquinas_ocupadas.exclude(id=exclude_id)
                        
                        if maquinas_ocupadas.exists():
                            errores.append(_("❌ Una o más máquinas del proceso ya están ocupadas en ese rango."))

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        self.full_clean()  # 🛡️ Ejecuta clean() automáticamente antes de guardar
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Asignación de Proceso"
        verbose_name_plural = "Asignaciones de Procesos"
        ordering = ["-fecha_asignacion", "prioridad"]
        indexes = [
            models.Index(fields=["proceso"]),
            models.Index(fields=["pieza"]),
            models.Index(fields=["nesteo"]),
            models.Index(fields=["maquina"]),
            models.Index(fields=["usuario"]),
        ]

    def __str__(self):
        return f"{self.proceso.nombre if self.proceso else 'Sin Proceso'} - {self.pieza.consecutivo if self.pieza else 'Sin Pieza'}"
    
class InventarioMaterial(models.Model):
    material = models.ForeignKey(
        "Material",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="inventario",
        db_index=True,
        verbose_name="Material",
        help_text="Material almacenado en inventario"
    )
    cantidad_disponible = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="Cantidad Disponible",
        help_text="Cantidad actual de este material en inventario"
    )
    ubicacion = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name="Ubicación",
        help_text="Ubicación del material dentro del almacén"
    )

    class Meta:
        verbose_name = "Inventario de Material"
        verbose_name_plural = "Inventario de Materiales"
        ordering = ["material", "ubicacion"]

    def __str__(self):
        return f"{self.material.nombre if self.material else 'Sin Material'} - {self.cantidad_disponible} unidades"

class Nesteo(models.Model):
    nombre_placa = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name="Nombre de la Placa",
        help_text="Nombre único de la placa nesteada"
    )
    material = models.ForeignKey(
        "Material",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="nesteos",
        db_index=True,
        verbose_name="Material",
        help_text="Material utilizado para el nesteo"
    )
    descripcion = models.TextField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Descripción",
        help_text="Descripción opcional del nesteo"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el nesteo está activo o ha sido marcado como eliminado"
    )

    class Meta:
        verbose_name = "Nesteo"
        verbose_name_plural = "Nesteos"
        ordering = ["nombre_placa"]

    def __str__(self):
        return f"{self.nombre_placa} - {self.material.nombre if self.material else 'Sin Material'}"
    
class PiezaNesteo(models.Model):
    ESTADO_OPCIONES = [
        ("Pendiente", "Pendiente"),
        ("Procesado", "Procesado"),
        ("Completado", "Completado"),
    ]

    pieza = models.ForeignKey(
        "Pieza",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="nesteos",
        db_index=True,
        verbose_name="Pieza",
        help_text="Pieza asignada al nesteo"
    )
    nesteo = models.ForeignKey(
        "Nesteo",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="piezas",
        db_index=True,
        verbose_name="Nesteo",
        help_text="Nesteo donde se encuentra la pieza"
    )
    cantidad = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Cantidad",
        help_text="Cantidad de piezas asignadas al nesteo"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_OPCIONES,
        default="Pendiente",
        db_index=True,
        verbose_name="Estado",
        help_text="Estado del proceso de nesteo"
    )
    fecha_asignacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Asignación",
        help_text="Fecha en la que se asignó la pieza al nesteo"
    )
    asignacionFinalizada = models.BooleanField(
        default=False,
        blank=True,
        verbose_name="asignación Finalizada",
        help_text="Indica si ya no necesita asignar procesos"
    )

    class Meta:
        verbose_name = "Pieza en Nesteo"
        verbose_name_plural = "Piezas en Nesteo"
        ordering = ["-fecha_asignacion", "pieza"]

    def __str__(self):
        return f"{self.pieza.consecutivo if self.pieza else 'Sin Pieza'} - {self.nesteo.nombre_placa if self.nesteo else 'Sin Nesteo'}"
    

class EtapaCalidad(models.Model):
    nombre = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name="Nombre de la Etapa",
        help_text="Nombre único de la etapa de calidad"
    )
    descripcion = models.TextField(
        verbose_name="Descripción",
        help_text="Detalles sobre la etapa de calidad"
    )

    class Meta:
        verbose_name = "Etapa de Calidad"
        verbose_name_plural = "Etapas de Calidad"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
    
class FlujoCalidad(models.Model):
    ESTADO_OPCIONES = [
        ("Pendiente", "Pendiente"),
        ("En Curso", "En Curso"),
        ("Aprobada", "Aprobada"),
        ("Scrap", "Scrap"),
    ]

    pieza = models.ForeignKey(
        "Pieza",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="flujos_calidad",
        db_index=True,
        verbose_name="Pieza",
        help_text="Pieza asociada al flujo de calidad"
    )
    etapa_calidad = models.ForeignKey(
        "EtapaCalidad",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="flujos_calidad",
        db_index=True,
        verbose_name="Etapa de Calidad",
        help_text="Etapa de calidad en la que se encuentra la pieza"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_OPCIONES,
        default="Pendiente",
        db_index=True,
        verbose_name="Estado",
        help_text="Estado del flujo de calidad"
    )
    piezas_asignadas = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        default=0,
        verbose_name="Piezas Asignadas",
        help_text="Número de piezas asignadas a esta etapa de calidad"
    )
    piezas_liberadas = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        default=0,
        verbose_name="Piezas Liberadas",
        help_text="Número de piezas liberadas en esta etapa de calidad"
    )
    fecha_inicio = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Inicio",
        help_text="Fecha en la que inició el proceso de calidad"
    )
    fecha_finalizacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de Finalización",
        help_text="Fecha en la que se finalizó el proceso de calidad"
    )

    class Meta:
        verbose_name = "Flujo de Calidad"
        verbose_name_plural = "Flujos de Calidad"
        ordering = ["-fecha_inicio", "pieza"]

    def __str__(self):
        return f"{self.pieza.consecutivo if self.pieza else 'Sin Pieza'} - {self.etapa_calidad.nombre if self.etapa_calidad else 'Sin Etapa'} ({self.estado})"
    

class ScrapCalidad(models.Model):
    pieza = models.ForeignKey(
        "Pieza",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="scraps_calidad",
        db_index=True,
        verbose_name="Pieza",
        help_text="Pieza afectada por el scrap"
    )
    etapa_calidad = models.ForeignKey(
        "EtapaCalidad",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="scraps_calidad",
        db_index=True,
        verbose_name="Etapa de Calidad",
        help_text="Etapa de calidad en la que se generó el scrap"
    )
    cantidad_scrap = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="Cantidad de Scrap",
        help_text="Número de piezas afectadas por el scrap"
    )
    motivo = models.TextField(
        verbose_name="Motivo",
        help_text="Descripción de la causa del scrap"
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Registro",
        help_text="Fecha en la que se registró el scrap"
    )

    class Meta:
        verbose_name = "Scrap de Calidad"
        verbose_name_plural = "Scraps de Calidad"
        ordering = ["-fecha_registro", "pieza"]

    def __str__(self):
        return f"{self.pieza.consecutivo if self.pieza else 'Sin Pieza'} - {self.etapa_calidad.nombre if self.etapa_calidad else 'Sin Etapa'} - {self.cantidad_scrap} piezas"
    

class ProveedorTratamiento(models.Model):
    TIPO_TRATAMIENTO_OPCIONES = [
        ("Termico", "Térmico"),
        ("Estetico", "Estético"),
        ("Esteticos/Termicos", "Estéticos/Térmicos"),
    ]

    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre del Proveedor",
        help_text="Nombre de la empresa que ofrece tratamientos de calidad"
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_TRATAMIENTO_OPCIONES,
        verbose_name="Tipo de Tratamiento",
        help_text="Tipo de tratamiento que ofrece el proveedor"
    )
    nombre_de_contacto = models.CharField(
        max_length=100,
        verbose_name="Nombre de Contacto",
        help_text="Nombre de la persona de contacto en el proveedor"
    )
    correo_de_contacto = models.EmailField(
        unique=True,
        verbose_name="Correo de Contacto",
        help_text="Correo electrónico de la persona de contacto"
    )
    telefono_de_contacto = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r"^\+?\d{7,15}$", message="Número de teléfono inválido")],
        verbose_name="Teléfono de Contacto",
        help_text="Número de teléfono de la persona de contacto"
    )
    fecha_entrega_estimada = models.IntegerField(
        verbose_name="Tiempo de Entrega Estimado",
        help_text="Tiempo estimado de entrega del tratamiento en unidades especificadas"
    )
    unidad_de_tiempo = models.CharField(
        max_length=20,
        verbose_name="Unidad de Tiempo",
        help_text="Unidad de tiempo utilizada para la estimación (ejemplo: días, semanas, horas)"
    )

    class Meta:
        verbose_name = "Proveedor de Tratamiento"
        verbose_name_plural = "Proveedores de Tratamiento"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} - {self.tipo}"
    
from django.db import models


class TratamientoCalidad(models.Model):
    TIPO_MATERIAL_OPCIONES = [
        ("Aluminio", "Aluminio"),
        ("Plastico", "Plastico"),
        ("Acero Negro", "Acero Negro"),
        ("Inoxidable", "Inoxidable"),
        ("Otro", "Otro"),
    ]

    TIPO_TRATAMIENTO_OPCIONES = [
        ("Termico", "Térmico"),
        ("Estetico", "Estético"),
    ]

    nombre = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,  # 🔍 Indexado
        verbose_name="Nombre del Tratamiento",
        help_text="Nombre identificador del tratamiento de calidad"
    )

    tipo_material = models.CharField(
        max_length=20,
        choices=TIPO_MATERIAL_OPCIONES,
        db_index=True,  # 🔍 Indexado
        verbose_name="Tipo de Material",
        help_text="Tipo de material al que se le aplica el tratamiento"
    )

    tipo_tratamiento = models.CharField(
        max_length=20,
        choices=TIPO_TRATAMIENTO_OPCIONES,
        db_index=True,  # 🔍 Indexado
        verbose_name="Tipo de Tratamiento",
        help_text="Tipo de tratamiento aplicado (Estético o Térmico)"
    )

    descripcion = models.TextField(
        null=True,
        blank=True,
        verbose_name="Descripción",
        help_text="Descripción detallada del tratamiento"
    )

    class Meta:
        verbose_name = "Tratamiento de Calidad"
        verbose_name_plural = "Tratamientos de Calidad"
        ordering = ["nombre"]
        indexes = [
            models.Index(fields=["tipo_material"]),
            models.Index(fields=["tipo_tratamiento"]),
        ]

    def __str__(self):
        return self.nombre


class AsignacionTratamientoCalidad(models.Model):
    pieza = models.ForeignKey(
        "Pieza",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="asignaciones_tratamientos_calidad",
        db_index=True,
        verbose_name="Pieza",
        help_text="Pieza que se sometió a tratamiento de calidad"
    )
    tratamiento = models.ForeignKey(
        TratamientoCalidad,
        on_delete=models.CASCADE,
        related_name="asignaciones",
        verbose_name="Tratamiento Aplicado",
        help_text="Tratamiento aplicado a la pieza",
        null=True,  # 👈 Habilita nulo para migrar sin errores
        blank=True
    )
    proveedor = models.ForeignKey(
        "ProveedorTratamiento",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tratamientos",
        db_index=True,
        verbose_name="Proveedor",
        help_text="Proveedor que realizó el tratamiento"
    )
    fecha_salida = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha de Salida",
        help_text="Fecha en la que la pieza salió a tratamiento"
    )
    fecha_entrega = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de Entrega",
        help_text="Fecha en la que se espera recibir la pieza"
    )
    fecha_recepcion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de Recepción",
        help_text="Fecha en la que la pieza fue recibida tras el tratamiento"
    )

    class Meta:
        verbose_name = "Asignación Tratamiento de Calidad"
        verbose_name_plural = "Asignaciones Tratamientos de Calidad"
        ordering = ["-fecha_salida"]
        indexes = [
            models.Index(fields=["tratamiento"]),
        ]

    def __str__(self):
        return f"{self.pieza.consecutivo if self.pieza else 'Sin Pieza'} - {self.tratamiento.nombre} - {self.proveedor.nombre if self.proveedor else 'Sin Proveedor'}"    

class RackProduccion(models.Model):  # Nuevo nombre del modelo
    ESTADO_OPCIONES = [
        ("Disponible", "Disponible"),
        ("Ocupado", "Ocupado"),
    ]

    codigo_rack = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Código del Rack",
        help_text="Código único del rack para identificación"
    )
    ubicacion = models.CharField(
        max_length=100,
        verbose_name="Ubicación",
        help_text="Ubicación del rack dentro del almacén"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_OPCIONES,
        default="Disponible",
        verbose_name="Estado",
        help_text="Estado actual del rack (Disponible u Ocupado)"
    )

    class Meta:
        verbose_name = "Rack de Producción"
        verbose_name_plural = "Racks de Producción"
        ordering = ["codigo_rack"]

    def __str__(self):
        return f"{self.codigo_rack} - {self.estado}"
    

class EstanteProduccion(models.Model):  
    ESTADO_OPCIONES = [
        ("Disponible", "Disponible"),
        ("Ocupado", "Ocupado"),
    ]

    codigo_estante = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Código del Estante",
        help_text="Código único del estante para identificación"
    )
    rack = models.ForeignKey(
        RackProduccion, 
        on_delete=models.CASCADE, 
        related_name="estantes", 
        null=True, 
        blank=True,
        verbose_name="Rack Asociado",
        help_text="Rack en el que está ubicado este estante"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_OPCIONES,
        default="Disponible",
        verbose_name="Estado",
        help_text="Estado actual del estante (Disponible u Ocupado)"
    )

    class Meta:
        verbose_name = "Estante de Producción"
        verbose_name_plural = "Estantes de Producción"
        ordering = ["codigo_estante"]

    def __str__(self):
        return f"{self.codigo_estante} - {self.estado}"

class UbicacionPieza(models.Model):
    pieza = models.ForeignKey(
        Pieza, 
        on_delete=models.CASCADE, 
        related_name="ubicaciones",
        verbose_name="Pieza",
        help_text="Pieza que está almacenada en el estante"
    )
    estante = models.ForeignKey(
        EstanteProduccion, 
        on_delete=models.CASCADE, 
        related_name="ubicaciones",
        verbose_name="Estante",
        help_text="Estante donde está ubicada la pieza"
    )
    cantidad = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="Cantidad",
        help_text="Cantidad de piezas almacenadas en este estante"
    )
    fecha_registro = models.DateTimeField(
        default=now,
        verbose_name="Fecha de Registro",
        help_text="Fecha en la que se almacenó la pieza"
    )
    fecha_salida = models.DateTimeField(
        null=True, blank=True,
        verbose_name="Fecha de Salida",
        help_text="Fecha en la que la pieza fue retirada del estante"
    )
    responsable = models.ForeignKey(
        Usuarios, 
        null=True, blank=True, 
        on_delete=models.SET_NULL,
        related_name="ubicaciones_responsables",
        verbose_name="Responsable",
        help_text="Usuario responsable de almacenar la pieza"
    )


    class Meta:
        verbose_name = "Ubicación de Pieza"
        verbose_name_plural = "Ubicaciones de Piezas"
        ordering = ["-fecha_registro"]

    def save(self, *args, **kwargs):
        """ Valida que la fecha de salida no sea anterior a la fecha de registro """
        if self.fecha_salida and self.fecha_salida < self.fecha_registro:
            raise ValueError("La fecha de salida no puede ser anterior a la fecha de registro.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pieza.consecutivo} en {self.estante.codigo_estante} - {self.cantidad} piezas"

class PersonalMaquina(models.Model):
    personal = models.ForeignKey(
        "ri_compras.Usuarios",
        on_delete=models.CASCADE,
        related_name="maquinas_autorizadas",
        verbose_name="Personal",
        help_text="Usuario que puede operar la máquina"
    )
    maquina = models.ForeignKey(
        "Maquina",
        on_delete=models.CASCADE,
        related_name="operadores",
        verbose_name="Máquina",
        help_text="Máquina que puede ser operada por el usuario"
    )

    class Meta:
        verbose_name = "Asignación de Máquina a Personal"
        verbose_name_plural = "Asignaciones de Máquina a Personal"
        unique_together = ("personal", "maquina")  # Evita duplicados
        ordering = ["personal"]
        indexes = [
            models.Index(fields=["personal"]),
            models.Index(fields=["maquina"]),
            models.Index(fields=["personal", "maquina"]),  # Índice compuesto
        ]

    def __str__(self):
        return f"{self.personal.nombre} - {self.maquina.nombre}"

class HorarioProduccion(models.Model):
    DIAS_CHOICES = [
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes'),
        ('sabado', 'Sábado'),
        ('domingo', 'Domingo'),
    ]

    usuario = models.ForeignKey(
        Usuarios,
        on_delete=models.CASCADE,
        related_name="horarios_produccion"
    )
    dia = models.CharField(
        max_length=10,
        choices=DIAS_CHOICES
    )
    hora_entrada = models.TimeField()
    hora_salida = models.TimeField()
    tiene_horario_comida = models.BooleanField(default=False)
    hora_comida_inicio = models.TimeField(null=True, blank=True)
    hora_comida_fin = models.TimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Horario de Producción"
        verbose_name_plural = "Horarios de Producción"
        indexes = [
            models.Index(fields=["usuario"]),
            models.Index(fields=["hora_entrada"]),
            models.Index(fields=["hora_salida"]),
        ]

    def clean(self):
        if self.hora_entrada >= self.hora_salida:
            raise ValidationError("La hora de entrada debe ser antes que la hora de salida.")

        if self.tiene_horario_comida:
            if not self.hora_comida_inicio or not self.hora_comida_fin:
                raise ValidationError("Debe especificar el horario de comida si tiene comida.")
            if not (self.hora_entrada <= self.hora_comida_inicio < self.hora_comida_fin <= self.hora_salida):
                raise ValidationError("El horario de comida debe estar dentro del horario laboral.")

    def __str__(self):
        return f"Horario de {self.usuario.nombre}"
