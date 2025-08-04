import calendar
from datetime import date, datetime, timedelta
import logging
from django.db import models
from django.http import HttpResponseBadRequest
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
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Q

class Producto(models.Model):
    MONEDAS = (
        ('MXN', 'MXN'),
        ('USD', 'USD'),
    )
    
    identificador = models.CharField(max_length=100, null=True,blank=True, help_text="Codigo o numero identificador")
    nombre = models.CharField(max_length=100, help_text="Nombre comercial del producto")
    descripcion = models.TextField(default="Sin descripcion")
    costo = models.DecimalField(max_digits=30, decimal_places=6)
    divisa = models.CharField(max_length=5, default="MXN", choices=MONEDAS)
    cantidad = models.DecimalField(max_digits=20, decimal_places=2)
    unidad_de_medida = models.CharField(max_length=40, null=True)

    def __str__(self):
        return self.nombre

class ProductoRequisicion(models.Model):
    MONEDAS = (
        ('MXN', 'MXN'),
        ('USD', 'USD'),
    )

    identificador = models.CharField(max_length=100, null=True, blank=True, help_text="Codigo o numero identificador")
    nombre = models.CharField(max_length=100, help_text="Nombre comercial del producto")
    descripcion = models.TextField(default="Sin descripcion")
    costo = models.DecimalField(max_digits=30, decimal_places=6)
    divisa = models.CharField(max_length=5, default="MXN", choices=MONEDAS)
    cantidad = models.DecimalField(max_digits=20, decimal_places=2)
    unidad_de_medida = models.CharField(max_length=100, null=True)
    cantidad_recibida = models.DecimalField(max_digits=30, decimal_places=2, default=0)

    def __str__(self):
        return self.nombre

class Servicio(models.Model):
    MONEDAS = (
        ('MXN', 'MXN'),
        ('USD', 'USD'),
    )
    
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    costo = models.DecimalField(max_digits=30, decimal_places=6)
    divisa = models.CharField(max_length=5, default="MXN", choices=MONEDAS)

    def __str__(self):
        return self.nombre

class ServicioRequisicion(models.Model):
    MONEDAS = (
        ('MXN', 'MXN'),
        ('USD', 'USD'),
    )
    
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    costo = models.DecimalField(max_digits=30, decimal_places=6)
    divisa = models.CharField(max_length=5, default="MXN", choices=MONEDAS)

    def __str__(self):
        return self.nombre

class Departamento(models.Model):
    MONEDAS = (
        ('MXN', 'MXN'),
        ('USD', 'USD'),
    )
    
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(max_length=400, blank=True)
    presupuesto = models.DecimalField(max_digits=30, decimal_places=6, help_text="Dinero actual en el departamento.")
    ingreso_fijo = models.DecimalField(max_digits=30, decimal_places=6, help_text="El ingreso que se mantendra mes con mes.")
    divisa = models.CharField(max_length=5, default="MXN", choices=MONEDAS)
    
    def __str__(self):
        return self.nombre

class UsuariosManager(BaseUserManager):
    def create_user(self, username, correo=None, password=None):
        if not username:
            raise ValueError('El nombre de usuario es obligatorio')
        if not correo:
            raise ValueError('El correo electrónico es obligatorio')

        user = self.model(username=username, correo=correo)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, correo, password=None):
        if not password:
            raise ValueError('La contraseña es obligatoria')

        user = self.create_user(username, correo, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

    def get_by_natural_key(self, username):
        return self.get(username=username)

class Usuarios(AbstractBaseUser, PermissionsMixin):
    PUESTOS = (
        ('MASTER', 'Master'),
        ('ADMINISTRADOR', 'Administrador'),
        ('COMPRADOR', 'Comprador'),
        ('LIDER', 'Lider'),
        ('OPERADOR', 'Operador'),
    )

    is_staff = models.BooleanField(default=False)
    joined_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    username = models.CharField(max_length=50, unique=True, db_index=True)
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15, blank=True)
    correo = models.EmailField(unique=True, db_index=True)
    rol = models.CharField(max_length=15, choices=PUESTOS, null=True, db_index=True)
    departamento = models.ForeignKey('Departamento', on_delete=models.SET_NULL, related_name='usuarios', null=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['correo']

    password = models.CharField(max_length=128)
    objects = UsuariosManager()

    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="usuarios_set",
        related_query_name="user",
    )

    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="usuarios_set",
        related_query_name="user",
    )

    history = HistoricalRecords(inherit=True)

    @property
    def history_user(self):
        return self.username

    @history_user.setter
    def history_user(self, value):
        self._history_user = value

    def __str__(self):
        return f'{self.username} - {self.nombre} ({self.rol})'
    
        # Agrega estos métodos:
    def get_short_name(self):
        """Devuelve el nombre corto del usuario."""
        return self.nombre

    def get_full_name(self):
        """Devuelve el nombre completo del usuario."""
        return self.nombre  # Puedes ajustar esto si tienes nombres y apellidos separados

class Project(models.Model):
    MONEDAS = (
        ('MXN', 'MXN'),
        ('USD', 'USD'),
    )
    
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(max_length=400, blank=True)
    presupuesto_inicial = models.DecimalField(max_digits=30, decimal_places=6, help_text="Dinero inicial del proyecto.")
    presupuesto = models.DecimalField(max_digits=30, decimal_places=6, help_text="Dinero actual del proyecto.", default=Decimal('0.0'))
    divisa = models.CharField(max_length=5, default="MXN", choices=MONEDAS)
    usuario = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, related_name='proyectos', null=True)
    habilitado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Contacto(models.Model):
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15)
    correo = models.CharField(max_length=100, null=True)
    
    def __str__(self):
        return self.nombre

class Proveedor(models.Model):
    REGIMEN_FISCAL = (
        ('General de Ley Personas Morales', 'General de Ley Personas Morales'),
        ('Arrendamiento', 'Arrendamiento'),
        ('Personas Físicas con Actividades Empresariales y Profesionales', 'Personas Físicas con Actividades Empresariales y Profesionales'),
        ('Sin obligaciones fiscales', 'Sin obligaciones fiscales'),
        ('Incorporación Fiscal', 'Incorporación Fiscal'),
        ('Régimen Simplificado de Confianza', 'Régimen Simplificado de Confianza'),
        ('Sociedad Anónima de Capital Variable', 'Sociedad Anónima de Capital Variable'),
        ('Regimen de los Coordinados', 'Regimen de los Coordinados'),
        
    )
    
    TIPO_PERSONA = (
        ('', 'Sin seleccionar'),  
        ('FISICA', 'Persona Física'),
        ('MORAL', 'Persona Moral'),
    )

    nombre = models.CharField(max_length=100)
    razon_social = models.CharField(max_length=200)
    rfc = models.CharField(max_length=100)
    regimen_fiscal = models.CharField(max_length=150, choices=REGIMEN_FISCAL)
    tipo_persona = models.CharField(max_length=10, choices=TIPO_PERSONA, default='', blank=True)
    codigo_postal = models.CharField(max_length=10)
    direccion = models.CharField(max_length=250, help_text="Ej. Avenida Soles #8193")
    direccion_geografica = models.CharField(max_length=100, help_text="Ej. Mexicali, B.C, Mexico")
    telefono = models.CharField(max_length=15, null=True)
    correo = models.CharField(max_length=100, null=True)
    pagina = models.URLField(null=True)
    tiempo_de_entegra_estimado = models.CharField(max_length=120, null=True)
    iva = models.DecimalField(max_digits=20, decimal_places=6)
    iva_retenido = models.DecimalField(max_digits=20, decimal_places=6, null=True)
    isr_retenido = models.DecimalField(max_digits=20, decimal_places=6, null=True)
    dias_de_credito = models.CharField(max_length=100, null=True)
    credito = models.DecimalField(max_digits=30, decimal_places=6, null=True)
    divisa = models.CharField(max_length=5, default='MXN')
    contactos = models.ManyToManyField(Contacto)
    calidad = models.DecimalField(max_digits=2, decimal_places=2, blank=True, help_text="0.0 al 0.9")
    servicio_profesional_no_comercial = models.BooleanField(default=False, help_text="Indica si el proveedor ofrece servicios profesionales o no comerciales.")

    def __str__(self):
        return f'PV_{self.id} | {self.razon_social}' # type: ignore

class Requisicion(models.Model):
    ESTADO_APROBACION = (
        ('RECHAZADO', 'Rechazado'),
        ('PENDIENTE', 'Pendiente'),
        ('APROBADO', 'Aprobado'),
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_aprobado = models.DateTimeField(null=True)
    fecha_entrega_estimada = models.DateTimeField(null=True)
    fecha_ordenado = models.DateTimeField(null=True)
    motivo = models.TextField(blank=True, null=True)
    total = models.DecimalField(max_digits=30, decimal_places=6, null=True)
    aprobado = models.CharField(max_length=50, choices=ESTADO_APROBACION, default="PENDIENTE")
    ordenado = models.BooleanField(default=False)
    usuario = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, related_name='requisiciones', null=True)
    proyecto = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='requisiciones', null=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='requisiciones', null=True)
    productos = models.ManyToManyField(ProductoRequisicion, blank=True)
    servicios = models.ManyToManyField(ServicioRequisicion, blank=True)
    archivo_pdf = models.FileField(upload_to='pdfs/', blank=True, null=True)
    tipo_de_cambio = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)

    def __str__(self):
        if self.usuario:
            username_formatted = self.usuario.nombre.lower().replace(' ', '_')
            departamento_nombre = self.usuario.departamento.nombre if self.usuario.departamento else "Sin departamento"
        else:
            username_formatted = "sin_usuario"
            departamento_nombre = "Sin departamento"

        return f'RC_{self.id}_{username_formatted} | {self.aprobado} | {departamento_nombre} | {self.fecha_creacion.day}/{self.fecha_creacion.month}/{self.fecha_creacion.year} {self.fecha_creacion.hour}:{self.fecha_creacion.minute}'

class OrdenDeCompra(models.Model):
    ESTADO_ENVIO = (
        ('RECHAZADO', 'RECHAZADO'),
        ('EN SOLICITUD','EN SOLICITUD'),
        ('EN CAMINO', 'EN CAMINO'),
        ('EN ALMACEN', 'EN ALMACEN'),
    )
    
    DIVISA_OPCIONES = (
        ('MXN', 'MXN'),
        ('USD', 'USD'),
        ('No especificado', 'No especificado'),
    )
    
    fecha_emision = models.DateTimeField(auto_now_add=True)
    fecha_entrega = models.DateTimeField(null=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True)
    requisicion = models.ForeignKey(Requisicion, on_delete=models.SET_NULL, null=True)
    usuario = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, related_name='ordenes_de_compra', null=True)
    estado = models.CharField(max_length=50, choices=ESTADO_ENVIO, default="EN SOLICITUD")
    url_pdf = models.CharField(max_length=255, null=True)
    orden_recibida = models.BooleanField(default=False)
    orden_compra_pdf = models.FileField(upload_to='pdfs/', blank=True, null=True)
    factura_pdf = models.FileField(upload_to='pdfs/', blank=True, null=True)
    folio_factura = models.TextField(blank=True, null=True)
    total_factura = models.DecimalField(max_digits=30, decimal_places=6, blank=True, null=True)
    total = models.DecimalField(max_digits=30, decimal_places=6)
    # Nuevos campos opcionales
    fecha_cfdi = models.DateField(null=True, blank=True)
    fecha_contrarecibo = models.DateField(null=True, blank=True)
    divisa = models.CharField(max_length=20, choices=DIVISA_OPCIONES, default='No especificado')  # 🔹 Nuevo campo agregado



    def __str__(self):
        if self.requisicion and self.requisicion.usuario:
            username_formatted = self.requisicion.usuario.nombre.lower().replace(' ', '_')
        else:
            username_formatted = "sin_usuario"
        
        return f'OC_{self.id}_{username_formatted} | {self.estado}'

class Rack(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre

class Estante(models.Model):
    numero = models.CharField(max_length=50)
    rack = models.ForeignKey(Rack, on_delete=models.CASCADE, related_name='estantes')

    class Meta:
        unique_together = ('numero', 'rack',)

    def __str__(self):
        return f'{self.rack.nombre}{self.numero}'

class ProductoAlmacen(models.Model):
    MONEDAS = (
        ('MXN', 'MXN'),
        ('USD', 'USD'),
    )
    
    identificador = models.CharField(max_length=100, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(default="Sin descripcion")
    costo = models.FloatField()
    divisa = models.CharField(max_length=5, default="MXN", choices=MONEDAS)
    cantidad = models.IntegerField()
    minimo = models.IntegerField(blank=True, null=True)
    maximo = models.IntegerField(blank=True, null=True)
    orden_compra = models.ForeignKey(OrdenDeCompra, on_delete=models.CASCADE, related_name='productos_almacen', null=True)
    orden_liberada = models.BooleanField(default=False)
    posicion = models.ForeignKey(Estante, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos')
    
    def __str__(self):
        return f'{self.nombre} -> {self.cantidad}'

class Pedido(models.Model):
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos')
    producto = models.ForeignKey(ProductoAlmacen, on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos')
    cantidad = models.IntegerField(help_text="Cantidad del producto que se pide")

    usuario_nombre = models.CharField(max_length=100, null=True, blank=True)
    producto_nombre = models.CharField(max_length=100, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.usuario:
            self.usuario_nombre = self.usuario.nombre
        if self.producto:
            self.producto_nombre = self.producto.nombre
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.usuario_nombre} pidió {self.cantidad} de {self.producto_nombre} el {self.fecha_pedido}'

class Factura(models.Model):
    folio = models.TextField()

class Recibo(models.Model):
    orden = models.ManyToManyField(OrdenDeCompra, blank=False)
    estado = models.BooleanField(default=False)
    descripcion = models.CharField(max_length=255, default="Sin descripcion")

    def __str__(self):
        return f'Recibo #{self.id}'

class Message(models.Model):
    user = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, related_name='messages', null=True)
    from_user = models.ForeignKey(Usuarios, on_delete=models.SET_NULL, related_query_name=None, null=True)
    title = models.CharField(max_length=100)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.from_user} to {self.user} | {self.created_at.day}/{self.created_at.month}/{self.created_at.year} {self.created_at.hour}:{self.created_at.minute}'
    
    #Hello
class CuentaPorCobrar(models.Model):
    DIVISA_CHOICES = [
        ('MXN', 'MXN'),
        ('USD', 'USD'),
    ]

    ESTATUS_CHOICES = [
    ('programada', 'Programada'),
    ('cancelada', 'Cancelada'),
    ('pagada', 'Pagada'),
    ]

    razon_social = models.CharField(max_length=255, verbose_name="Razón Social Cliente", default="")
    responsable = models.CharField(max_length=255, default="")
    oc_po = models.CharField(max_length=100, verbose_name="OC / PO", default="")
    pdf_oc_po = models.FileField(upload_to='oc_po_pdf/', null=True, blank=True)
    fecha_oc_po = models.DateField(verbose_name="Fecha OC / PO", default=timezone.now)
    numero_proyecto_interno_ri = models.CharField(max_length=100, verbose_name="Número Proyecto Interno RI", default="")
    importe_total_oc_po_sin_iva = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Importe Total OC / PO Sin IVA", default=Decimal('0.00'))
    importe_iva_total_oc_po = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Importe IVA Total OC / PO", default=Decimal('0.00'))
    porcentaje_facturacion = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="% Facturación", default=Decimal('0.00'))
    importe_total_facturado = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Importe Total Facturado", default=Decimal('0.00'))
    iva_importe_facturado = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="IVA Importe Facturado", default=Decimal('0.00'))
    importe_total_facturado_con_iva = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Importe Total Facturado con IVA", default=Decimal('0.00'))
    fecha_cfdi = models.DateField(verbose_name="Fecha CFDI", default=timezone.now)
    tipo_cfdi = models.CharField(max_length=50, verbose_name="Tipo CFDI", default="")
    folio_cfdi = models.CharField(max_length=100, verbose_name="Folio CFDI", default="")
    pdf_cfdi = models.FileField(upload_to='cfdi_pdf/', null=True, blank=True)
    fecha_ideal_pago = models.DateField(verbose_name="Fecha Ideal de Pago", default=timezone.now)
    fecha_programada_pago = models.DateField(verbose_name="Fecha Programada Pago", default=timezone.now)
    saldo = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    divisa = models.CharField(max_length=3, choices=DIVISA_CHOICES, default="MXN")
    dias_vencidos = models.IntegerField(default=0)
    importe_pago = models.DecimalField(max_digits=16, decimal_places=6, verbose_name="Importe Pago", default=Decimal('0.00'))
    estatus = models.CharField(max_length=50, choices=ESTATUS_CHOICES, default="programada")
    iva = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="IVA", default=Decimal('0.00'))
    nombre_factura = models.CharField(max_length=255, verbose_name="nombre de la factura", default="")
    monto_total = models.DecimalField(max_digits=20, decimal_places=2, verbose_name="Monto Total", default=Decimal('0.00'))
    xml_cancelacion = models.FileField(upload_to='xml_cancelacion/', null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['razon_social']),
            models.Index(fields=['oc_po']),
            models.Index(fields=['numero_proyecto_interno_ri']),
        ]
        ordering = ['-fecha_programada_pago']

    def save(self, *args, **kwargs):
        try:
            porcentaje_facturacion_decimal = Decimal(self.porcentaje_facturacion)
            tasa_iva = Decimal('0.16')

            self.importe_total_facturado = self.importe_total_oc_po_sin_iva * (porcentaje_facturacion_decimal / Decimal('100'))
            self.iva_importe_facturado = self.importe_total_facturado * tasa_iva
            self.importe_total_facturado_con_iva = self.importe_total_facturado + self.iva_importe_facturado


            self.saldo = self.importe_total_facturado_con_iva - self.importe_pago

        except (InvalidOperation, ValueError) as e:
            raise ValueError("Error al calcular los valores: " + str(e))

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.razon_social} - {self.oc_po}"
    
    def calcular_facturacion_restante(razon_social, oc_po):
        total_facturacion = CuentaPorCobrar.objects.filter(
            razon_social=razon_social,
            oc_po=oc_po,
        ).exclude(estatus="cancelada").aggregate(total=Sum('porcentaje_facturacion'))['total'] or 0
        
        porcentaje_restante = 100 - total_facturacion
        return max(porcentaje_restante, 0) 

class DetalleCxC(models.Model):
    TIPO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
        ('cheque', 'Cheque'),
        ('terceros', 'Terceros'),
    ]
    
    propuesta_cxc = models.ForeignKey(CuentaPorCobrar, related_name='detalles', on_delete=models.CASCADE)
    abono = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    referencia_transferencia = models.CharField(max_length=100, default="")
    pdf_factura = models.FileField(upload_to='facturas/', null=True, blank=True)
    fecha_pago = models.DateField(null=True, blank=True)  # Nuevo campo fecha_pago
    tipo_de_pago = models.CharField(max_length=15, choices=TIPO_PAGO_CHOICES, default='transferencia')
    numero_cuenta = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['referencia_transferencia']),
        ]
        
    def save(self, *args, **kwargs):
        is_new = self.pk is None  # Determinar si es un nuevo registro

        if is_new:
            # Caso: Tipo de pago es transferencia o cheque
            if self.tipo_de_pago in ['transferencia', 'cheque']:
                if not self.numero_cuenta:
                    raise ValueError("Se requiere un número de cuenta válido para procesar un abono por transferencia o cheque.")

                # Buscar la instancia de BancoModelo usando el número de cuenta
                try:
                    cuenta_bancaria = BancoModelo.objects.get(id=self.numero_cuenta)
                except BancoModelo.DoesNotExist:
                    raise ValueError(f"No se encontró una cuenta bancaria con el ID {self.numero_cuenta}.")

                # Crear AbonoBanco usando la instancia de BancoModelo
                AbonoBanco.objects.create(
                    numero_cuenta=cuenta_bancaria,
                    monto_movimiento=self.abono,
                    tipo_movimiento='ingreso',
                    fecha_movimiento=self.fecha_pago,
                    referencia=self.referencia_transferencia,
                    pdf_comprobante=self.pdf_factura,
                    comentarios='Ingreso desde CxC',
                    proveedor=self.propuesta_cxc.razon_social,
                    entrada_salida='entrada',
                )

        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.propuesta_cxc.razon_social} - Abono: {self.abono}"

# Modelo para créditos y préstamos
class CreditoPrestamo(models.Model):
    DIVISA_CHOICES = [
        ('MXN', 'MXN'),
        ('USD', 'USD'),
    ]
    
    ESTATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('rechazado', 'Rechazado'),
        ('programado', 'Programado'),
        ('pagado', 'Pagado'),
        ('inicial', 'Inicial'),
    ]

    PERIODICIDAD_CHOICES = [
        ('semanal', 'Semanal'),
        ('mensual', 'Mensual'),
        ('bimestral', 'Bimestral'),
        ('trimestral', 'Trimestral'),
        ('anual', 'Anual'),
        ('unico','Unico')
    ]

    EMITIDO_RECIBIDO_CHOICES = [
        ('emitido', 'Emitido'),
        ('recibido', 'Recibido'),
    ]
    
    TIPO_TRANSACCION_CHOICES = [
        ('credito', 'Credito'),
        ('prestamo', 'Prestamo'),
    ]

    # Campos básicos
    emisor = models.CharField(max_length=255)
    receptor = models.CharField(max_length=255)
    tipo_transaccion = models.CharField(max_length=10, choices=TIPO_TRANSACCION_CHOICES)  
    importe = models.DecimalField(max_digits=15, decimal_places=2)
    numero_transaccion = models.CharField(max_length=100, unique=True)
    
    # Opcionales
    tasa_interes_normal = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tasa_interes_moratorio = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Fechas
    fecha_realizacion = models.DateField()
    fecha_vencimiento = models.DateField()

    # Divisa y periodicidad
    divisa = models.CharField(max_length=3, choices=DIVISA_CHOICES, default='MXN')
    periodicidad = models.CharField(max_length=10, choices=PERIODICIDAD_CHOICES, default='mensual')
    emitido_recibido = models.CharField(max_length=10, choices=EMITIDO_RECIBIDO_CHOICES)

    # Estatus
    estatus = models.CharField(max_length=10, choices=ESTATUS_CHOICES, default='inicial')
    termino = models.IntegerField(null=True, blank=True)

    #Cuenta bancaria
    numero_cuenta = models.CharField(max_length=30, null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)  # Campo de descripción
    comprobantepdf = models.FileField(upload_to='CreditoPrestamoComprobante/', null=True, blank=True)  # Campo para el PDF


    class Meta:
        indexes = [
            models.Index(fields=['numero_transaccion']),
            models.Index(fields=['emisor', 'receptor']),
            models.Index(fields=['tipo_transaccion']),
            models.Index(fields=['estatus']),
            models.Index(fields=['fecha_vencimiento']),
        ]

    @property
    def total_abonos(self):
        # Calcular la suma total de los pagos de abono para este crédito
        return self.amortizaciones.aggregate(total_abonos=Sum('pagos__abono'))['total_abonos'] or Decimal(0)
    
    def crear_abono(self, *args, **kwargs):
        try:
            cuenta_banco = BancoModelo.objects.get(id=self.numero_cuenta)
        except BancoModelo.DoesNotExist:
            return HttpResponseBadRequest("Error: No se encontró la cuenta bancaria asociada.")

        movimiento = 'ingreso'
        movimiento2 = 'entrada'

        # Solo validamos el saldo si es un egreso
        if self.emitido_recibido == 'emitido':
            movimiento = 'egreso'
            movimiento2 = 'salida'

            if cuenta_banco.saldo < self.importe:
                raise ValueError("Fondos insuficientes en la cuenta bancaria para realizar el egreso.")

        # Crear el abono (ya sea ingreso o egreso)
        abono = AbonoBanco(
            numero_cuenta=cuenta_banco,
            monto_movimiento=self.importe,
            tipo_movimiento='diario',
            fecha_movimiento=self.fecha_realizacion,
            referencia=self.descripcion,
            comentarios=f'{movimiento} por {self.tipo_transaccion}',
            entrada_salida=movimiento2,
            pdf_comprobante=self.comprobantepdf
        )

        abono.save()

    def calcular_intereses_insolutos(self):
        """
        Suma de los intereses pendientes (incluyendo intereses moratorios) para todas las cuotas no pagadas.
        """
        amortizaciones_pendientes = self.amortizaciones.filter(estatus_pago__in=['pendiente', 'moroso'])
        intereses_insolutos = amortizaciones_pendientes.aggregate(
            total_interes=Sum('interes') + Sum('interes_moratorio')
        )['total_interes'] or Decimal(0)
        return intereses_insolutos

    def calcular_saldo_a_liquidar(self):
        """
        Suma del balance restante (capital + interés + IVA) para las cuotas pendientes menos los pagos realizados.
        """
        amortizaciones_pendientes = self.amortizaciones.filter(estatus_pago__in=['pendiente', 'moroso'])
        
        # Calcular el saldo de las cuotas pendientes
        saldo_pendiente = amortizaciones_pendientes.aggregate(
            saldo_total=Sum(F('principal') + F('interes') + F('interes_moratorio') + F('iva_interes'))
        )['saldo_total'] or Decimal(0)
        
        # Resta de los abonos para obtener el saldo neto a liquidar
        saldo_a_liquidar = saldo_pendiente - self.total_abonos
        return max(Decimal(0), saldo_a_liquidar)  # Asegura que el saldo no sea negativo

    def calcular_capital_restante(self):
        """
        Suma de los valores principales pendientes de las cuotas no pagadas.
        """
        amortizaciones_pendientes = self.amortizaciones.filter(estatus_pago__in=['pendiente', 'moroso'])
        capital_restante = amortizaciones_pendientes.aggregate(total_principal=Sum('principal'))['total_principal'] or Decimal(0)
        return capital_restante

    def __str__(self):
        return f"Transacción {self.numero_transaccion} - {self.tipo_transaccion} ({self.emisor} a {self.receptor})"
    
    # Método para generar la tabla de amortización
    def generar_tabla_amortizacion(self):
        """
        Genera la tabla de amortización según la periodicidad seleccionada y ajusta las fechas de pago en consecuencia.
        """
        tasa_periodica = Decimal(self.tasa_interes_normal or 0) / Decimal(100) / Decimal(12)  # Tasa de interés mensual
        n = self.termino if self.periodicidad != 'unico' else 1  # Si es 'unico', solo hay una cuota
        P = Decimal(self.importe)  # Monto del préstamo
        iva_tasa = Decimal('0.16')  # IVA del 16% sobre el interés

        # Calcular el pago (único o amortizado)
        if tasa_periodica == 0:
            # Si la tasa de interes es 0, el pago mensual es el monto dividido entre el numeo de pagos
            pago_mensual = P / n
        else:
            # Formula estándar de amortización
            pago_mensual = P * tasa_periodica / (1 - (1 + tasa_periodica) ** -n)

        saldo_restante = P
        fecha_pago = self.fecha_realizacion

        for cuota_num in range(1, n + 1):
            if tasa_periodica == 0:
                # Si la tasa de interes es 0, no hay intereses
                interes = Decimal(0)
                iva_interes = Decimal(0)
                principal = pago_mensual
            else:
                interes = saldo_restante * tasa_periodica
                iva_interes = interes * iva_tasa  # Calcular el IVA del interes
                principal = pago_mensual - interes

            saldo_restante -= principal
            saldo_restante = max(0, saldo_restante)

            #  Si la periodicidad es 'unico', la fecha de pago será igual a `fecha_vencimiento`
            if self.periodicidad == 'unico':
                fecha_pago = self.fecha_vencimiento
            else:
                fecha_pago = AmortizacionCuota.ajustar_fecha_pago(fecha_pago, self.periodicidad)

            # Crear la cuota en la tabla de amortización
            AmortizacionCuota.objects.create(
                credito_prestamo=self,
                numero_mes=cuota_num,
                pago=round(principal + interes + iva_interes, 2),
                principal=round(principal, 2),
                interes=round(interes, 2),
                iva_interes=round(iva_interes, 2),
                balance_restante=round(saldo_restante, 2),
                fecha_pago_programada=fecha_pago,  # ✅ Se ajusta según la periodicidad
                estatus_pago='pendiente'
            )

            # Si queda algún saldo menor que 0 (por aproximaciones), ajustamos
            if saldo_restante <= 0:
                break
            

    def recalcular_amortizacion(self, nuevo_importe=None):
        """
        Recalcula la tabla de amortización cuando cambia el saldo, o cuando
        hay una reestructuración de la deuda. Este método también se llama
        cuando un abono excede el saldo pendiente.
        """
        if nuevo_importe:
            self.importe += nuevo_importe  # Incrementar el saldo con el nuevo abono
        else:
            abonos = self.pagos.aggregate(total_abonos=Sum('abono'))['total_abonos'] or 0
            self.importe = self.calcular_capital_restante()  # Si no hay nuevo importe, ajustamos el saldo restante.

        # Eliminar las cuotas anteriores para recalcular
        self.amortizaciones.all().delete()

        # Generar la nueva tabla de amortización
        self.generar_tabla_amortizacion()

    def aplicar_abono_y_recalcular(self, abono):
        """
        Aplica un abono al capital del crédito y recalcula la tabla de amortización si es necesario.
        Si el abono excede el saldo restante, recalculamos la tabla.
        """
        saldo_actual = self.calcular_capital_restante()

        if abono >= saldo_actual:
            exceso_abono = abono - saldo_actual
            # Aplicamos el exceso al capital
            self.recalcular_amortizacion(nuevo_importe=exceso_abono)
        else:
            # Solo aplicamos el abono al saldo pendiente
            self.aplicar_abono_a_cuotas(abono)

    def aplicar_abono_a_cuotas(self, abono):
        """
        Aplica el abono a las cuotas pendientes, empezando por la más antigua.
        """
        cuotas_pendientes = self.amortizaciones.filter(estatus_pago__in=['pendiente', 'moroso']).order_by('numero_mes')
        saldo_abono = abono

        for cuota in cuotas_pendientes:
            if saldo_abono <= 0:
                break

            total_cuota = cuota.principal + cuota.interes + cuota.interes_moratorio
            if saldo_abono >= total_cuota:
                # Si el abono cubre la cuota completa
                cuota.marcar_como_pagado()
                saldo_abono -= total_cuota
            else:
                # Abono parcial: Reducimos el principal de la cuota
                cuota.principal -= saldo_abono
                if cuota.estatus_pago == 'moroso':
                    cuota.interes_moratorio = max(0, cuota.interes_moratorio - saldo_abono)
                cuota.save()
                break

        self.save()

# Modelo para los pagos realizados
class AmortizacionCuota(models.Model):
    credito_prestamo = models.ForeignKey(CreditoPrestamo, related_name='amortizaciones', on_delete=models.CASCADE)
    numero_mes = models.IntegerField()
    pago = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    principal = models.DecimalField(max_digits=15, decimal_places=2)
    interes = models.DecimalField(max_digits=15, decimal_places=2)
    interes_moratorio = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    iva_interes = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance_restante = models.DecimalField(max_digits=15, decimal_places=2)
    fecha_pago_programada = models.DateField()
    estatus_pago = models.CharField(max_length=10, choices=[('pendiente', 'Pendiente'), ('pagado', 'Pagado'), ('moroso', 'Moroso')], default='pendiente')
    propuesta_pago = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return f"Cuota {self.numero_mes} de {self.credito_prestamo.numero_transaccion}"


    def marcar_como_pagado(self):
        """
        Marca la cuota como pagada para evitar modificaciones futuras.
        """
        self.estatus_pago = 'pagado'
        self.save()
    

    def marcar_todas_como_pagadas(self):
        """
        Marca todas las cuotas restantes de este crédito como pagadas y pone balance en 0.
        """
        cuotas_restantes = self.credito_prestamo.amortizaciones.filter(
            numero_mes__gte=self.numero_mes
        )

        for cuota in cuotas_restantes:
            cuota.estatus_pago = 'pagado'
            cuota.balance_restante = Decimal(0)
            cuota.principal = Decimal(0)
            cuota.interes = Decimal(0)
            cuota.interes_moratorio = Decimal(0)
            cuota.iva_interes = Decimal(0)
            cuota.save()
    
    def aplicar_pago(self, monto_pagado):
        """
        Aplica el pago a esta cuota. Si el pago cubre completamente la cuota, marca la cuota como pagada.
        Si esta era la última cuota pendiente, se actualiza el estatus del crédito a "pagado".
        """
        saldo_cuota = self.pago

        if monto_pagado >= saldo_cuota:
            # Pago completo con posible excedente
            excedente = monto_pagado - saldo_cuota
            self.marcar_como_pagado()  # Marcar como pagado para evitar futuras modificaciones
            logging.debug(f"Excedente: {excedente}")

            # Verificar si todas las cuotas del crédito están pagadas
            credito = self.credito_prestamo
            cuotas_pendientes = credito.amortizaciones.filter(estatus_pago='pendiente')

            if not cuotas_pendientes.exists():  # No hay cuotas pendientes
                logging.debug(f"EstaPagado")
                credito.estatus = 'pagado'
                credito.save(update_fields=['estatus'])
            else:
                logging.debug(f"Regresa a inicial")
                credito.estatus = 'inicial'
                credito.save(update_fields=['estatus'])

            return excedente
        else:
            # Pago parcial, no marca como pagado hasta que se complete
            self.principal -= monto_pagado
            self.save()
            return Decimal(0)
    

    def recalcular_cuotas_posteriores(self, numero_mes_actual, balance_restante):
            """
            Recalcula las cuotas restantes utilizando el balance restante ajustado. Ignora las cuotas con
            `estatus_pago = 'pagado'` y la cuota a la que se aplica el pago actualmente.
            """
            cuotas_posteriores = self.credito_prestamo.amortizaciones.filter(numero_mes__gt=numero_mes_actual).order_by('numero_mes')
            tasa_interes_mensual = Decimal(self.credito_prestamo.tasa_interes_normal or 0) / Decimal(100) / Decimal(12)
            iva_tasa = Decimal('0.16')  # Tasa del IVA sobre el interés
            n = cuotas_posteriores.count()

            if n == 0 or balance_restante <= 0:
                return  # No hay cuotas para recalcular o el saldo está saldado

            # Cálculo del pago mensual ajustado para las cuotas restantes, incluyendo IVA sobre el interés
            if (tasa_interes_mensual == 0):
                pago_base = Decimal(balance_restante) / n
            else:
                pago_base = Decimal(balance_restante) * tasa_interes_mensual / (1 - (1 + tasa_interes_mensual) ** -n)

            for i, cuota in enumerate(cuotas_posteriores, start=1):
                if cuota.estatus_pago == 'pagado' or cuota.numero_mes == numero_mes_actual:
                    continue  # Ignorar cuotas pagadas y la cuota actual del pago

                interes = balance_restante * tasa_interes_mensual
                iva_interes = interes * iva_tasa
                principal = pago_base - interes

                if i == n:
                    principal = balance_restante  # Ajustamos el principal para que balance_restante llegue a 0
                    cuota.balance_restante = Decimal(0)
                else:
                    cuota.balance_restante = balance_restante - principal

                pago_mensual = principal + interes + iva_interes
                cuota.pago = pago_mensual.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                cuota.principal = principal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                cuota.interes = interes.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                cuota.iva_interes = iva_interes.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                cuota.save()

                balance_restante -= principal
                if balance_restante <= 0:
                    break

            self.credito_prestamo.save()


    @staticmethod
    def ajustar_fecha_pago(fecha_actual, periodicidad):
        """
        Ajusta la fecha de pago en función de la periodicidad de la cuota.
        """
        if periodicidad == 'semanal':
            return fecha_actual + timedelta(weeks=1)
        elif periodicidad == 'mensual':
            return AmortizacionCuota._ajustar_mes(fecha_actual, 1)
        elif periodicidad == 'bimestral':
            return AmortizacionCuota._ajustar_mes(fecha_actual, 2)
        elif periodicidad == 'trimestral':
            return AmortizacionCuota._ajustar_mes(fecha_actual, 3)
        elif periodicidad == 'anual':
            return fecha_actual.replace(year=fecha_actual.year + 1)
        return fecha_actual

    @staticmethod
    def _ajustar_mes(fecha, meses_a_sumar):
        nuevo_mes = (fecha.month - 1 + meses_a_sumar) % 12 + 1
        nuevo_anio = fecha.year + (fecha.month - 1 + meses_a_sumar) // 12

        try:
            nueva_fecha = fecha.replace(year=nuevo_anio, month=nuevo_mes)
        except ValueError:
            _, ultimo_dia = calendar.monthrange(nuevo_anio, nuevo_mes)
            nueva_fecha = fecha.replace(day=ultimo_dia, month=nuevo_mes)
        return nueva_fecha



# Modelo para los pagos realizados
class PagoCreditoPrestamo(models.Model):
    TIPO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
        ('cheque', 'Cheque'),
        ('terceros', 'Terceros'),
    ]
    
    TIPO_TARJETA = [
        ('credito', 'Credito'),
        ('debito', 'Debito'),
    ]
    amortizacion_cuota = models.ForeignKey(AmortizacionCuota, related_name='pagos', on_delete=models.CASCADE, null=True, blank=True)
    abono = models.DecimalField(max_digits=15, decimal_places=2)
    fecha_pago = models.DateField()
    referencia_transferencia = models.CharField(max_length=100, null=True, blank=True)
    pdf = models.FileField(upload_to='referencias/', null=True, blank=True)
    #nuevos campos
    tipo_de_pago = models.CharField(max_length=15, choices=TIPO_PAGO_CHOICES, default='transferencia')
    numero_tarjeta = models.CharField(max_length=19, null=True, blank=True)
    tipo_tarjeta = models.CharField(max_length=15, choices=TIPO_TARJETA, null=True, blank=True)
    numero_cuenta = models.CharField(max_length=19, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['amortizacion_cuota', 'fecha_pago']),  # Índice para buscar por cuota y fecha de pago
            models.Index(fields=['abono']),                              # Índice para buscar pagos por abono
        ]
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None  # Determinar si es un nuevo registro

        super().save(*args, **kwargs)

        logging.debug(f'informacion de pago {self.tipo_de_pago}, {self.numero_tarjeta}, {self.tipo_tarjeta}, {self.numero_cuenta}')
        if is_new:
            # Caso 1: Tipo de pago es tarjeta
            if self.tipo_de_pago == 'tarjeta':
                if not self.numero_tarjeta:
                    raise ValueError("El número de tarjeta es obligatorio para pagos con tarjeta.")
                
                try:
                    tarjeta = TarjetaCredito.objects.get(numero_tarjeta=self.numero_tarjeta)
                except TarjetaCredito.DoesNotExist:
                    raise ValueError(f"No se encontró una tarjeta asociada al número {self.numero_tarjeta}")

                if self.tipo_tarjeta == 'credito':
                    pago_mensual_actual = tarjeta.pagos_mensuales.filter(actual=True).first()
                    if not pago_mensual_actual:
                        raise ValueError("No se encontró un PagoMensualTarjeta marcado como actual para la tarjeta.")

                    # Crear MovimientoTarjeta
                    MovimientoTarjeta.objects.create(
                        tarjeta=tarjeta,
                        monto=self.abono,
                        concepto=self.referencia_transferencia,
                        fecha=self.fecha_pago.date(),
                        origen='credito/prestamo',
                        pago_mensual=pago_mensual_actual,
                    )

                elif self.tipo_tarjeta == 'debito':
                    # Buscar la tarjeta de débito en TarjetaCredito
                    try:
                        tarjeta_debito = TarjetaCredito.objects.get(numero_tarjeta=self.numero_tarjeta, tipo_tarjeta='debito')
                    except TarjetaCredito.DoesNotExist:
                        raise ValueError(f"No se encontró una tarjeta de débito asociada al número {self.numero_tarjeta}")

                    # Buscar la relación en TarjetasBanco
                    try:
                        tarjeta_banco = TarjetasBanco.objects.get(tarjeta=tarjeta_debito)
                        banco_asociado = tarjeta_banco.banco
                    except TarjetasBanco.DoesNotExist:
                        raise ValueError(f"No se encontró un banco asociado a la tarjeta de débito {self.numero_tarjeta}")

                    # Crear AbonoBanco usando el banco asociado
                    movimiento = 'salida'
                if (self.amortizacion_cuota.credito_prestamo.emitido_recibido == 'emitido'):
                    movimiento = 'entrada'
                    AbonoBanco.objects.create(
                        numero_cuenta=banco_asociado,
                        monto_movimiento=self.abono,
                        tipo_movimiento='diario',
                        fecha_movimiento=self.fecha_pago.date(),
                        referencia=self.referencia_transferencia,
                        pdf_comprobante=self.pdf,
                        comentarios=f'Gasto desde ${self.amortizacion_cuota.credito_prestamo.tipo_transaccion}/${self.amortizacion_cuota.credito_prestamo.emitido_recibido}',
                        entrada_salida='salida',
                    )

            # Caso 3: Tipo de pago es transferencia o cheque
            elif self.tipo_de_pago in ['transferencia', 'cheque']:
                if not self.numero_cuenta:
                    raise ValueError("Se requiere un número de cuenta válido para procesar un abono por transferencia o cheque.")

                # Buscar la instancia de BancoModelo usando el número de cuenta
                try:
                    cuenta_bancaria = BancoModelo.objects.get(id=self.numero_cuenta)
                except BancoModelo.DoesNotExist:
                    raise ValueError(f"No se encontró una cuenta bancaria con el ID {self.numero_cuenta}.")

                # Crear AbonoBanco usando la instancia de BancoModelo
                movimiento = 'salida'
                if (self.amortizacion_cuota.credito_prestamo.emitido_recibido == 'emitido'):
                    movimiento = 'entrada'
                AbonoBanco.objects.create(
                    numero_cuenta=cuenta_bancaria,
                    monto_movimiento=self.abono,
                    tipo_movimiento='diario',
                    fecha_movimiento=self.fecha_pago,
                    referencia=self.referencia_transferencia,
                    pdf_comprobante=self.pdf,
                    comentarios=f'Gasto desde ${self.amortizacion_cuota.credito_prestamo.tipo_transaccion}/${self.amortizacion_cuota.credito_prestamo.emitido_recibido}',
                    proveedor='Pago credito/prestamo',
                    entrada_salida=movimiento,
                )
            
            # Caso 4: Tipo de pago terceros crear OtroGasto
            if self.tipo_de_pago == 'terceros':
                OtroGasto.objects.create(
                    tipo_gasto=TipoOtroGasto.objects.get(nombre='terceros'),  
                    proveedor=f'{self.amortizacion_cuota.credito_prestamo.emisor}/{self.amortizacion_cuota.credito_prestamo.receptor}',
                    descripcion='Abono de Credito como terceros',
                    divisa=f'{self.amortizacion_cuota.credito_prestamo.divisa}',
                    tipo_pago='terceros',
                    monto_total=self.abono,
                    fecha_gasto=self.fecha_pago,
                    ticket_factura=self.pdf,
                    estatus='inicial',
                )
        

    def __str__(self):
        return f"Pago de {self.abono} para Cuota {self.amortizacion_cuota.numero_mes} de {self.amortizacion_cuota.credito_prestamo.numero_transaccion}"


class TarjetaCredito(models.Model):
    DIVISA_CHOICES = [
        ('MXN', 'MXN'),
        ('USD', 'USD'),
    ]
    ESTATUS_CHOICES = [
        ('inicial', 'Inicial'),
        ('pendiente', 'Pendiente'),
        ('programado', 'Programado'),
        ('pagado', 'Pagado'),
        ('moroso', 'Moroso'),
        ('activa', 'Activa'),
        ('inactiva', 'Inactiva'),
        ('bloqueada', 'Bloqueada'),
    ]
    
    TIPO_TARJETA = [
        ('credito', 'Credito'),
        ('debito', 'Debito'),
    ]

    banco = models.CharField(max_length=255)
    numero_tarjeta = models.CharField(max_length=19, unique=True)
    saldo = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    limite_credito = models.DecimalField(max_digits=15, decimal_places=2,null=True, blank=True)
    divisa = models.CharField(max_length=3, choices=DIVISA_CHOICES, default='MXN')
    tasa_interes = models.DecimalField(max_digits=5, decimal_places=2,null=True, blank=True)
    tasa_moratoria = models.DecimalField(max_digits=5, decimal_places=2,null=True, blank=True)
    fecha_pago = models.DateField(null=True, blank=True)
    fecha_corte = models.DateField(null=True, blank=True)
    estatus = models.CharField(max_length=12, choices=ESTATUS_CHOICES, default='inicial')
    multa_por_morosidad = models.BooleanField(default=False)
    monto_multa_morosidad = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    propuesta_pago = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=0)
    saldo_restante = models.DecimalField(max_digits=15, decimal_places=2,null=True, blank=True, default=0)
    pago_minimo = models.DecimalField(max_digits=15, decimal_places=2,null=True, blank=True, default=0)
    tipo_tarjeta = models.CharField(max_length=15, choices=TIPO_TARJETA,null=True, blank=True)
    ultima_ejecucion = models.DateField(null=True, blank=True)
    banco_asociado = models.CharField(max_length=255, null=True, blank=True)  # Almacenar el ID del banco como cadena
    
    def __str__(self):
        return f"Tarjeta {self.numero_tarjeta} - {self.banco}"
    
    def actualizar_datos_desde_pago_actual(self):
        pago_actual = self.pagos_mensuales.filter(actual=True).first()
        if pago_actual:
            self.saldo = pago_actual.saldo_pendiente or Decimal(0)
            self.fecha_corte = pago_actual.fecha_corte
            self.fecha_pago = pago_actual.fecha_vencimiento
            self.estatus = pago_actual.estatus
            # Actualizar los campos sin llamar a save() para evitar recursión
            TarjetaCredito.objects.filter(pk=self.pk).update(
                saldo=self.saldo,
                fecha_corte=self.fecha_corte,
                fecha_pago=self.fecha_pago,
                estatus=self.estatus,
            )
        
    def save(self, *args, **kwargs):
        is_new = self.pk is None  # Verificar si la tarjeta es nueva
        fecha_actual = timezone.now().date()

        # Comportamiento para tarjetas de débito
        if self.tipo_tarjeta == 'debito':
            self.limite_credito = None
            self.tasa_interes = None
            self.tasa_moratoria = None
            self.fecha_pago = None
            self.fecha_corte = None
            self.multa_por_morosidad = False
            self.monto_multa_morosidad = 0
            self.propuesta_pago = None
            self.saldo_restante = None
            self.pago_minimo = None

            # Guardar la tarjeta primero para obtener un pk válido
            super(TarjetaCredito, self).save(*args, **kwargs)

            # Si se proporcionó un banco_asociado, buscar el banco y verificar si la relación ya existe
            if self.banco_asociado:
                try:
                    banco = BancoModelo.objects.get(id=self.banco_asociado)  # Buscar el banco por ID
                    
                    # **Verificar si la relación ya existe antes de crearla**
                    if not TarjetasBanco.objects.filter(banco=banco, tarjeta=self).exists():
                        TarjetasBanco.objects.create(
                            banco=banco,
                            tarjeta=self,
                        )
                except BancoModelo.DoesNotExist:
                    raise ValueError(f"No se encontró un banco con el ID {self.banco_asociado}.")
            return

        # Resto del código para tarjetas de crédito...
        if is_new:
            # Guardar la tarjeta primero para obtener un pk válido
            super(TarjetaCredito, self).save(*args, **kwargs)

            # Crear el primer registro de pago mensual
            primer_pago = PagoMensualTarjeta.objects.create(
                tarjeta=self,
                mes=1,
                saldo_pendiente=self.saldo,
                pago_minimo=self.pago_minimo,
                interes=0,
                fecha_corte=self.fecha_corte,
                fecha_vencimiento=self.fecha_pago,
                estatus='inicial',
                archivado=False,
                actual=self.saldo > 0 and fecha_actual <= self.fecha_pago,
                usado=False,
            )

            # Agregar pagos automáticos para los meses siguientes
            self.agregar_pagos_automaticos()

            # Si la fecha actual es mayor a la fecha de vencimiento, ajustar los registros
            if fecha_actual > self.fecha_pago:
                self._procesar_meses_vencidos(primer_pago, fecha_actual)

        else:
            # Actualizar el saldo de la tarjeta con el saldo del pago mensual actual
            pago_actual = self.pagos_mensuales.filter(actual=True).first()
            if pago_actual:
                self.saldo = pago_actual.saldo_pendiente

            super(TarjetaCredito, self).save(*args, **kwargs)
            self.actualizar_datos_desde_pago_actual()

    class Meta:
        # Ordena por fecha de creación descendente
        ordering = ['-fecha_creacion']

    def calcular_interes_mensual(self, capital):
        return (self.tasa_interes / Decimal(100)) * capital / 12

    def verificar_y_actualizar_estado(self):
        """
        Verifica pagos y multas pendientes antes de cada operación GET.
        Actualiza el estatus de los pagos vencidos y aplica multas si corresponde.
        """
        self.aplicar_multa_automatica()
        self.actualizar_estatus_pagos_pendientes()

    def cerrar_ciclo_facturacion(self):
        """
        Cierra el ciclo de facturación actual, aplicando los intereses 
        y actualizando las fechas de corte y pago, solo una vez al día.
        """
        fecha_actual = timezone.now().date()
        if (self.fecha_corte and fecha_actual >= self.fecha_pago and 
                (not self.ultima_ejecucion_cierre or self.ultima_ejecucion_cierre < fecha_actual)):
            # Aplicar intereses si hay saldo pendiente
            if self.saldo > 0:
                intereses = self.calcular_interes_mensual(self.saldo)
                self.saldo += intereses
                MovimientoTarjeta.objects.create(
                    tarjeta=self,
                    monto=intereses,
                    concepto="Intereses mensuales",
                    fecha=fecha_actual,
                    origen= 'prueba de posible error'
                )
            # Actualizar las fechas de corte y pago al próximo mes
            self.fecha_corte += relativedelta(months=1)
            self.fecha_pago = self.fecha_corte + timedelta(days=15)
            # Registrar la última ejecución
            self.ultima_ejecucion_cierre = fecha_actual
            self.save()

    def actualizar_estatus_pagos_pendientes(self):
        """
        Actualiza el estatus de pagos pendientes a morosos si han vencido.
        """
        pagos_vencidos = self.pagos_mensuales.filter(fecha_vencimiento__lt=timezone.now().date(), estatus='inicial')
        for pago in pagos_vencidos:
            pago.estatus = 'moroso'
            pago.save()


    def agregar_pagos_automaticos(self):
        meses_existentes = set(self.pagos_mensuales.values_list('mes', flat=True))
        meses_pendientes = set(range(1, 14)) - meses_existentes

        for mes in sorted(meses_pendientes):
            months_offset = mes - 1

            PagoMensualTarjeta.objects.create(
                tarjeta=self,
                mes=mes,
                pago_minimo=self.pago_minimo if mes == 1 else Decimal(0),
                interes=Decimal(0),
                fecha_corte=self.fecha_corte + relativedelta(months=months_offset),
                fecha_vencimiento=self.fecha_pago + relativedelta(months=months_offset),
                estatus='inicial',
                actual=(mes == 1),
            )

    def aplicar_multa_automatica(self):
        """Aplica la multa si la tarjeta está configurada y el último pago está vencido"""
        ultimo_pago = self.pagos_mensuales.order_by('-fecha_vencimiento').first()
        if self.multa_por_morosidad and ultimo_pago and ultimo_pago.estatus == 'moroso':
            self.saldo += self.monto_multa_morosidad
            self.movimientos.create(
                monto=self.monto_multa_morosidad,
                concepto="Multa automática por morosidad",
                fecha=timezone.now()
            )
            self.save()

    def actualizar_estado_pagos(self):
        """
        Actualiza el estado de los pagos mensuales según las fechas de corte y vencimiento.
        """
        fecha_actual = timezone.now().date()
        pagos = self.pagos_mensuales.order_by('mes')

        for pago in pagos:
            if pago.fecha_corte <= fecha_actual:
                # Si la fecha actual es mayor o igual a la fecha de corte, marcar como usado
                pago.usado = True

            if pago.fecha_corte <= fecha_actual <= pago.fecha_vencimiento:
                # Si la fecha actual está dentro del rango, marcar como actual
                pago.actual = True
            else:
                # Si no, desmarcar como actual
                pago.actual = False

            pago.save()

        # Establecer el próximo registro como actual si el registro actual ya venció
        pago_actual = pagos.filter(actual=True).first()
        if not pago_actual or fecha_actual > pago_actual.fecha_vencimiento:
            siguiente_pago = pagos.filter(usado=False, actual=False).first()
            if siguiente_pago:
                siguiente_pago.actual = True
                siguiente_pago.save()

    def verificar_estado_moroso(self):
        fecha_actual = timezone.now().date()

        # Verificar si la fecha de vencimiento de la tarjeta está en el pasado
        if self.fecha_pago < fecha_actual:
            # Si el saldo es mayor a 0, el estado puede cambiar a 'moroso'
            if self.saldo > 0:
                self.estatus = 'moroso'
            else:
                # Si el saldo es 0, mantener el estado en 'pendiente' o similar
                self.estatus = 'inicial'
            self.save()

        # Verificar los pagos mensuales relacionados
        pagos_pendientes = self.pagos_mensuales.filter(estatus='pendiente')
        for pago in pagos_pendientes:
            if pago.fecha_vencimiento < fecha_actual:
                pago.estatus = 'moroso'
                pago.save()
                
    def _procesar_meses_vencidos(self, primer_pago, fecha_actual):
        pagos = self.pagos_mensuales.order_by('mes')
        saldo_acumulado = Decimal(0)

        for pago in pagos:
            if fecha_actual > pago.fecha_vencimiento:
                if pago.saldo_pendiente and pago.saldo_pendiente > 0:
                    # Aplicar multa si corresponde
                    multa = self.monto_multa_morosidad if self.multa_por_morosidad else Decimal(0)
                    saldo_con_multa = pago.saldo_pendiente + multa

                    # Calcular intereses normales y moratorios
                    intereses_normales = (self.tasa_interes / Decimal(100)) * saldo_con_multa / 12
                    intereses_moratorios = (self.tasa_moratoria / Decimal(100)) * saldo_con_multa / 12

                    # Actualizar saldo pendiente con multa e intereses
                    pago.saldo_pendiente += multa + intereses_normales + intereses_moratorios
                    pago.interes += intereses_normales + intereses_moratorios

                    # Registrar movimientos (como en tu código original)

                    # Acumular saldo pendiente
                    saldo_acumulado += pago.saldo_pendiente

                    # Marcar como archivado y moroso
                    pago.estatus = 'moroso'
                    pago.archivado = True
                    pago.actual = False
                    pago.usado = False
                    pago.save()
                elif pago.saldo_pendiente <= 0:
                    pago.estatus = 'pagado'
                    pago.archivado = True
                    pago.actual = False
                    pago.usado = False
                    pago.save()
            else:
                # Encontramos el mes actual
                if saldo_acumulado > 0:
                    # Agregar saldo acumulado al saldo pendiente del mes actual
                    if pago.saldo_pendiente is None:
                        pago.saldo_pendiente = Decimal(0)
                    pago.saldo_pendiente += saldo_acumulado

                pago.actual = True
                self.saldo = pago.saldo_pendiente or Decimal(0)  # Sincronizar saldo de la tarjeta
                pago.usado = False
                pago.archivado = False
                # Por esta línea:
                if pago.saldo_pendiente and pago.saldo_pendiente > 0:
                    # Mantener el estatus actual o cambiar a 'moroso' si ya está vencido
                    if fecha_actual > pago.fecha_vencimiento:
                        pago.estatus = 'moroso'
                    else:
                        # No cambiar el estatus automáticamente a 'pendiente'
                        pago.estatus = pago.estatus  # Mantener el estatus actual
                else:
                    pago.estatus = 'inicial'
                pago.save()
                self.actualizar_datos_desde_pago_actual()
                break

class PagoMensualTarjeta(models.Model):
    ESTATUS_CHOICES = [
        ('inicial', 'Inicial'),
        ('pendiente', 'Pendiente'),
        ('programado', 'Programado'),
        ('pagado', 'Pagado'),
        ('moroso', 'Moroso'),
    ]

    tarjeta = models.ForeignKey(TarjetaCredito, related_name='pagos_mensuales', on_delete=models.CASCADE)
    mes = models.IntegerField()
    pago_minimo = models.DecimalField(max_digits=15, decimal_places=2)
    interes = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    fecha_corte = models.DateField(null=True, blank=True)
    fecha_vencimiento = models.DateField()
    estatus = models.CharField(max_length=10, choices=ESTATUS_CHOICES, default='inicial')
    propuesta_pago = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    saldo_pendiente = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    usado = models.BooleanField(default=False)
    actual = models.BooleanField(default=False)
    archivado = models.BooleanField(default=False)

    def __str__(self):
        return f"Pago Mensual {self.mes} para Tarjeta {self.tarjeta.numero_tarjeta}"

    def calcular_intereses_normales(self):
        """
        Calcula los intereses normales y los agrega al saldo.
        """
        interes_normal = (self.tarjeta.tasa_interes / Decimal(100)) * self.saldo_pendiente / 12
        self.saldo_pendiente += interes_normal
        self.interes += interes_normal

        # Registrar movimiento
        MovimientoTarjeta.objects.create(
            tarjeta=self.tarjeta,
            monto=interes_normal,
            concepto="Intereses normales",
            fecha=timezone.now(),
            origen='Intereses Mensuales',
            pago_mensual=self,
        )

    def procesar_intereses_y_morosidad(self):
        """
        Procesa los intereses y la morosidad para el registro actual si corresponde.
        """
        fecha_actual = timezone.now().date()

        # Si está dentro de su ciclo de corte
        if self.actual and fecha_actual >= self.fecha_corte:
            self.usado = True
            self.actual = False

            # Calcular intereses normales
            self.calcular_intereses_normales()

            # Mover el campo actual al siguiente mes
            siguiente_pago = self.tarjeta.pagos_mensuales.filter(mes=self.mes + 1).first()
            if siguiente_pago:
                siguiente_pago.actual = True
                siguiente_pago.save()
            self.tarjeta.actualizar_datos_desde_pago_actual()

        # Si está vencido y no se ha abonado el mínimo
        if self.usado and fecha_actual > self.fecha_vencimiento:
            total_abonos = self.abonos.aggregate(Sum('monto_abono'))['monto_abono__sum'] or 0

            if total_abonos < self.pago_minimo:
                # Aplicar multa si corresponde
                if self.tarjeta.multa_por_morosidad:
                    self.saldo_pendiente += self.tarjeta.monto_multa_morosidad
                    MovimientoTarjeta.objects.create(
                        tarjeta=self.tarjeta,
                        monto=self.tarjeta.monto_multa_morosidad,
                        concepto="Multa por morosidad",
                        fecha=fecha_actual,
                        origen='Multa',
                        pago_mensual=self,
                    )

                # Calcular intereses moratorios
                interes_moratorio = (self.tarjeta.tasa_moratoria / Decimal(100)) * self.saldo_pendiente / 12
                self.saldo_pendiente += interes_moratorio
                self.interes += interes_moratorio

                # Registrar movimiento
                MovimientoTarjeta.objects.create(
                    tarjeta=self.tarjeta,
                    monto=interes_moratorio,
                    concepto="Intereses moratorios",
                    fecha=fecha_actual,
                    origen='Intereses Moratorios',
                    pago_mensual=self,
                )

                # Transferir saldo al siguiente mes
                siguiente_pago = self.tarjeta.pagos_mensuales.filter(mes=self.mes + 1).first()
                if siguiente_pago:
                    siguiente_pago.saldo_pendiente += self.saldo_pendiente
                    siguiente_pago.save()

                # Archivar el mes actual
                self.archivado = True
                self.usado = False
                self.actual = False
                self.estatus = 'moroso'

        self.save()

    def save(self, *args, **kwargs):
        # Verificar si saldo_pendiente es None antes de comparar
        if self.saldo_pendiente is not None and self.saldo_pendiente <= 0:
            self.estatus = 'inicial'
            self.usado = False
            self.actual = False
            self.archivado = False

        # Llamar a la función que limpia el pago mínimo
        self.limpiar_pago_minimo()

        super().save(*args, **kwargs)


    def limpiar_pago_minimo(self):
        """
        Limpia el campo pago_minimo de los registros que no correspondan al primer mes.
        """
        if self.mes != 1:
            self.pago_minimo = 0
    def actualizar_estado_y_saldo(self):
            fecha_actual = timezone.now().date()

            try:
                pago_moroso = PagoMensualTarjeta.objects.get(
                    tarjeta=self.tarjeta, 
                    estatus='moroso', 
                    archivado=False
                )
            except PagoMensualTarjeta.DoesNotExist:
                pago_moroso = None

            if pago_moroso:
                # Archivar el mes moroso
                pago_moroso.archivado = True
                pago_moroso.estatus = 'moroso'
                pago_moroso.save()

                # Obtener el siguiente mes
                try:
                    siguiente_mes = PagoMensualTarjeta.objects.get(
                        tarjeta=self.tarjeta, 
                        mes=pago_moroso.mes + 1,
                        archivado=False
                    )
                except PagoMensualTarjeta.DoesNotExist:
                    siguiente_mes = None

                if siguiente_mes:
                    # Actualizar el siguiente mes
                    siguiente_mes.actual = True
                    siguiente_mes.saldo_pendiente = pago_moroso.saldo_pendiente
                    siguiente_mes.estatus = 'inicial'  # O el estado que corresponda
                    siguiente_mes.save()
            
    

class MovimientoTarjeta(models.Model):
    fecha = models.DateTimeField(default=timezone.now)
    monto = models.DecimalField(max_digits=15, decimal_places=2)
    concepto = models.CharField(max_length=255)
    tarjeta = models.ForeignKey(TarjetaCredito, on_delete=models.CASCADE, related_name='movimientos')
    origen = models.CharField(
        max_length=50,
        choices=[
            ('Servicios', 'Servicios'),
            ('Otros Gastos', 'Otros Gastos'),
        ],
        default='Servicios',
    )
    pago_mensual = models.ForeignKey(
        PagoMensualTarjeta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos',
    )

    def save(self, *args, **kwargs):  # Aquí está la corrección
        # Actualizar saldo de la tarjeta
        self.tarjeta.saldo += self.monto
        self.tarjeta.save()

        # Actualizar saldo pendiente del pago mensual actual
        try:
            pago_mensual_actual = PagoMensualTarjeta.objects.get(
                Q(tarjeta=self.tarjeta) & Q(actual=True)
            )
            pago_mensual_actual.saldo_pendiente += self.monto
            pago_mensual_actual.save()
        except PagoMensualTarjeta.DoesNotExist:
            # Manejar el caso en que no se encuentre un pago mensual actual
            pass

        # Guardar el movimiento
        super().save(*args, **kwargs)

    def __str__(self):  # Corrige el método str a __str__
        return f"Movimiento {self.concepto} de {self.monto} para Tarjeta {self.tarjeta.numero_tarjeta} origen {self.origen}"

class AbonoTarjeta(models.Model):
    TIPO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('cheque', 'Cheque'),
        ('terceros', 'Terceros'),
    ]
    
    pago_mensual = models.ForeignKey(PagoMensualTarjeta, related_name='abonos', on_delete=models.CASCADE, null=True, blank=True)
    fecha_abono = models.DateField()
    monto_abono = models.DecimalField(max_digits=15, decimal_places=2)
    referencia_transferencia = models.CharField(max_length=100, null=True, blank=True)
    pdf_comprobante = models.FileField(upload_to='abonos/', null=True, blank=True)
    tipo_de_pago = models.CharField(max_length=20, choices=TIPO_PAGO_CHOICES, default='efectivo')
    numero_cuenta = models.CharField(max_length=30, null=True, blank=True)

    def save(self, *args, **kwargs):
        """
        Procesa los abonos en función del estado y las fechas del pago mensual,
        y gestiona la creación de AbonoBanco para transferencias y cheques.
        """
        is_new = self.pk is None  # Determinar si es un nuevo registro
        fecha_actual = timezone.now().date()

        if not self.pago_mensual:
            raise ValueError("El abono debe estar asociado a un registro de pago mensual.")

        # Caso 1: Antes de la fecha de corte
        if fecha_actual <= self.pago_mensual.fecha_corte:
            # Restar saldo pendiente y saldo de la tarjeta
            self.pago_mensual.saldo_pendiente -= self.monto_abono
            self.pago_mensual.tarjeta.saldo -= self.monto_abono
            self.pago_mensual.save()
            if self.pago_mensual.tarjeta:
                self.pago_mensual.tarjeta.save()

        # Caso 2: Después de la fecha de corte y antes de la fecha de vencimiento
        elif self.pago_mensual.pago_minimo > 0 and fecha_actual > self.pago_mensual.fecha_corte and fecha_actual <= self.pago_mensual.fecha_vencimiento:
            if self.monto_abono >= self.pago_mensual.pago_minimo:
                self.pago_mensual.saldo_pendiente -= self.monto_abono
                self.pago_mensual.estatus = 'pagado'
                self.pago_mensual.tarjeta.saldo -= self.monto_abono
                self.pago_mensual.archivado = True  # Archivar al cubrir el pago mínimo
                self.pago_mensual.actual = False
                self.pago_mensual.usado = False
            else:
                self.pago_mensual.saldo_pendiente -= self.monto_abono  # Reducir saldo, pero no cambiar estado
            self.pago_mensual.save()
            if self.pago_mensual.tarjeta:
                self.pago_mensual.tarjeta.save()

        # Caso 3: Después de la fecha de vencimiento (no permitido)
        elif fecha_actual > self.pago_mensual.fecha_vencimiento:
            raise ValueError("No se permite abonar a un registro de pago mensual vencido.")

        # Guardar el abono
        super().save(*args, **kwargs)

        # Lógica para transferencias y cheques (solo para nuevos registros)
        if is_new and self.tipo_de_pago in ['transferencia', 'cheque']:
            if not self.numero_cuenta:
                raise ValueError("Se requiere un número de cuenta válido para procesar un abono por transferencia o cheque.")

            try:
                cuenta_bancaria = BancoModelo.objects.get(id=self.numero_cuenta)
            except BancoModelo.DoesNotExist:
                raise ValueError(f"No se encontró una cuenta bancaria con el ID {self.numero_cuenta}.")

            AbonoBanco.objects.create(
                numero_cuenta=cuenta_bancaria,
                monto_movimiento=self.monto_abono,
                tipo_movimiento='egreso',
                fecha_movimiento=self.fecha_abono,
                referencia=self.referencia_transferencia,
                pdf_comprobante=self.pdf_comprobante,
                comentarios='Egreso Tarjeta',
                proveedor=self.pago_mensual.tarjeta.numero_tarjeta,
                entrada_salida='salida',
            )

            
class ServiciosFactura(models.Model):
    DIVISA_CHOICES = [
        ('MXN', 'MXN'),
        ('USD', 'USD'),
    ]
    
    PERIODICIDAD_CHOICES = [
        ('semanal', 'Semanal'),
        ('mensual', 'Mensual'),
        ('bimestral', 'Bimestral'),
        ('trimestral', 'Trimestral'),
        ('anual', 'Anual'),
        ('pago unico', 'Pago unico'),
    ]
    
    ESTATUS_CHOICES = [
        ('inicial', 'Inicial'),
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('rechazado', 'Rechazado'),
        ('programado', 'Programado'),
        ('vencido', 'Vencido'),
    ]
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    nombre_servicio = models.CharField(max_length=255)
    folio_servicio = models.CharField(max_length=100, unique=True)
    total_a_pagar = models.DecimalField(max_digits=15, decimal_places=2)
    divisa = models.CharField(max_length=3, choices=DIVISA_CHOICES, default='MXN')
    fecha_vencimiento = models.DateField(null=True, blank=True)
    periodicidad = models.CharField(max_length=10, choices=PERIODICIDAD_CHOICES)
    estatus = models.CharField(max_length=10, choices=ESTATUS_CHOICES, default='inicial')
    propuesta_pago = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, default=0)
    fecha_corte = models.DateField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['folio_servicio']),        # Indexar para búsquedas rápidas por folio
            models.Index(fields=['estatus']),               # Indexar para búsquedas por estatus
            models.Index(fields=['fecha_vencimiento']),     # Indexar para búsquedas por fecha de vencimiento
        ]

    def __str__(self):
        return f"{self.nombre_servicio} ({self.folio_servicio})"

    # Método para calcular los días vencidos
    def dias_vencidos(self):
        # Comparar la fecha de vencimiento con la fecha actual
        dias_vencidos = (now().date() - self.fecha_corte).days
        # Si los días vencidos son negativos, no hay días vencidos (todavía no se ha vencido)
        return max(dias_vencidos, 0) if dias_vencidos > 0 else 0
    
    def crear_pagos_por_periodo(self):
        fecha_corte_inicial = self.fecha_vencimiento
        periodicidad = self.periodicidad
        es_primer_registro = True  # Variable para marcar el primer registro

        for i in range(12):
            fecha_corte = self.calcular_fecha_corte(fecha_corte_inicial, i, periodicidad)
            fecha_vencimiento = self.calcular_fecha_vencimiento(fecha_corte, periodicidad)

            total_a_pagar = self.total_a_pagar if i == 0 else 0
            propuesta_pago = self.propuesta_pago if i == 0 else 0

            # Determina el estado inicial del periodo
            if fecha_corte < timezone.now().date():
                estatus_inicial = 'vencido'
            else:
                estatus_inicial = 'inicial'
            
            # Crea el registro de PagoPorPeriodo con el estado inicial adecuado
            PagoPorPeriodo.objects.create(
                servicio=self,
                fecha_corte=fecha_corte,
                fecha_vencimiento=fecha_vencimiento,
                saldo_pendiente=total_a_pagar,
                total_a_pagar=total_a_pagar,
                divisa=self.divisa,
                estatus=estatus_inicial,
                propuesta_pago=propuesta_pago,
                actual=es_primer_registro  # Solo el primer registro tiene actual=True
            )

            es_primer_registro = False  # Desactivamos para el resto de registros

            
    def verificar_estado_servicio(self):
        existen_periodos_vencidos = self.pagos_por_periodo.filter(estatus='vencido').exists()
        ultimo_periodo_pagado = self.pagos_por_periodo.filter(estatus='pagado', usado=True).order_by('fecha_vencimiento').last()

        if ultimo_periodo_pagado:
            self.propuesta_pago = 0
            self.total_a_pagar = 0
            self.save()

            if existen_periodos_vencidos:
                return
            
            self.estatus = 'pagado'
            self.save()

            if timezone.now().date() > ultimo_periodo_pagado.fecha_corte:
                self.estatus = 'inicial'
                self.save()

            siguiente_periodo = (
                self.pagos_por_periodo
                .filter(fecha_corte__gt=timezone.now().date(), usado=False)
                .order_by('fecha_corte')
                .first()
            )

            if siguiente_periodo:
                siguiente_periodo.actual = True
                siguiente_periodo.save()

                self.estatus = siguiente_periodo.estatus
                self.propuesta_pago = siguiente_periodo.propuesta_pago
                self.total_a_pagar = siguiente_periodo.saldo_pendiente
                self.fecha_corte = siguiente_periodo.fecha_corte
                self.fecha_vencimiento = siguiente_periodo.fecha_vencimiento
                self.save()

            self.pagos_por_periodo.exclude(pk=siguiente_periodo.pk if siguiente_periodo else None).update(actual=False)
        else:
            pass

    @staticmethod
    def calcular_fecha_corte(fecha_base, increment, periodicidad):
        if periodicidad == 'semanal':
            return fecha_base + timedelta(weeks=increment)
        elif periodicidad == 'mensual':
            return fecha_base + relativedelta(months=increment)
        elif periodicidad == 'bimestral':
            return fecha_base + relativedelta(months=increment * 2)
        elif periodicidad == 'trimestral':
            return fecha_base + relativedelta(months=increment * 3)
        elif periodicidad == 'anual':
            return fecha_base + relativedelta(years=increment)
        else:
            return fecha_base

    @staticmethod
    def calcular_fecha_vencimiento(fecha_corte, periodicidad):
        return ServiciosFactura.calcular_fecha_corte(fecha_corte, 1, periodicidad)
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super(ServiciosFactura, self).save(*args, **kwargs)
        if is_new:
            self.crear_pagos_por_periodo()


class PagoPorPeriodo(models.Model):
    servicio = models.ForeignKey(
        ServiciosFactura, related_name='pagos_por_periodo', on_delete=models.CASCADE
    )
    
    ESTATUS_CHOICES = [
        ('inicial', 'Inicial'),
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('rechazado', 'Rechazado'),
        ('programado', 'Programado'),
        ('vencido', 'Vencido'),
    ]
    
    TIPO_TARJETA = [
        ('credito', 'Credito'),
        ('debito', 'Debito'),
    ]
    
    fecha_corte = models.DateField()
    fecha_vencimiento = models.DateField()
    saldo_pendiente = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_a_pagar = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    divisa = models.CharField(max_length=3, choices=ServiciosFactura.DIVISA_CHOICES)
    estatus = models.CharField(max_length=10, choices=ESTATUS_CHOICES, default='pendiente')
    propuesta_pago = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    usado = models.BooleanField(default=False)
    actual = models.BooleanField(default=False)
    tipo_tarjeta = models.CharField(max_length=15, choices=TIPO_TARJETA, null=True, blank=True)
    
    class Meta:
        ordering = ['fecha_vencimiento']

    def aplicar_abono(self, monto_abono):
        self.saldo_pendiente -= monto_abono
        if self.saldo_pendiente <= 0:
            self.saldo_pendiente = 0
            self.estatus = 'pagado'
            self.usado = True
            self.actual = False
        self.save()

        self.servicio.verificar_estado_servicio()
    
    def update_saldo_pendiente(self, monto):
        self.saldo_pendiente -= monto
        if self.saldo_pendiente <= 0:
            self.saldo_pendiente = 0
            self.estatus = 'pagado'
            self.usado = True
        elif timezone.now().date() > self.fecha_vencimiento:
            self.estatus = 'vencido'
        self.save()

        self.servicio.verificar_estado_servicio()
    
    def verificar_estado_periodo(self):
        if self.saldo_pendiente > 0 and self.fecha_vencimiento < timezone.now().date():
            self.estatus = 'vencido'
            self.save()
            
    def dias_vencidos(self):
        dias_vencidos = (timezone.now().date() - self.fecha_vencimiento).days
        return max(dias_vencidos, 0) if dias_vencidos > 0 else 0
    
    def save(self, *args, **kwargs):
        if self.estatus == 'inicial' and self.propuesta_pago > 0:
            self.estatus = 'pendiente'
        super(PagoPorPeriodo, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.servicio.nombre_servicio} - Pago Por Periodo ({self.fecha_corte} a {self.fecha_vencimiento})"
    

class PagoPeriodoAbono(models.Model):
    TIPO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
        ('cheque', 'Cheque'),
        ('terceros', 'Terceros'),
    ]
    
    TIPO_TARJETA = [
        ('credito', 'Credito'),
        ('debito', 'Debito'),
    ]
    
    periodo = models.ForeignKey(PagoPorPeriodo, on_delete=models.CASCADE, related_name='abonos')
    numero_tarjeta = models.CharField(max_length=19, null=True, blank=True)  # Número de la tarjeta
    abono = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_abono = models.DateTimeField()
    referencia = models.CharField(max_length=255)
    tipo_de_pago = models.CharField(max_length=15, choices=TIPO_PAGO_CHOICES, default='transferencia')
    tipo_tarjeta = models.CharField(max_length=15, choices=TIPO_TARJETA, null=True, blank=True)
    pdf_referencia = models.FileField(upload_to='pdf_referencias/', null=True, blank=True)
    numero_cuenta = models.CharField(max_length=19, null=True, blank=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None  # Determinar si es un nuevo registro

        if is_new:
            # Validaciones y movimientos ANTES de guardar
            if self.tipo_de_pago == 'tarjeta':
                if not self.numero_tarjeta:
                    raise ValueError("El número de tarjeta es obligatorio para pagos con tarjeta.")
                
                try:
                    tarjeta = TarjetaCredito.objects.get(numero_tarjeta=self.numero_tarjeta)
                except TarjetaCredito.DoesNotExist:
                    raise ValueError(f"No se encontró una tarjeta asociada al número {self.numero_tarjeta}")

                if self.tipo_tarjeta == 'credito':
                    pago_mensual_actual = tarjeta.pagos_mensuales.filter(actual=True).first()
                    if not pago_mensual_actual:
                        raise ValueError("No se encontró un PagoMensualTarjeta marcado como actual para la tarjeta.")
                elif self.tipo_tarjeta == 'debito':
                    try:
                        tarjeta_debito = TarjetaCredito.objects.get(numero_tarjeta=self.numero_tarjeta, tipo_tarjeta='debito')
                    except TarjetaCredito.DoesNotExist:
                        raise ValueError(f"No se encontró una tarjeta de débito asociada al número {self.numero_tarjeta}")
                    try:
                        tarjeta_banco = TarjetasBanco.objects.get(tarjeta=tarjeta_debito)
                        banco_asociado = tarjeta_banco.banco
                    except TarjetasBanco.DoesNotExist:
                        raise ValueError(f"No se encontró un banco asociado a la tarjeta de débito {self.numero_tarjeta}")
                    if banco_asociado.saldo < self.abono:
                        raise ValueError("El banco asociado a la tarjeta no tiene saldo suficiente para realizar este abono.")

            elif self.tipo_de_pago in ['transferencia', 'cheque']:
                if not self.numero_cuenta:
                    raise ValueError("Se requiere un número de cuenta válido para procesar un abono por transferencia o cheque.")
                try:
                    cuenta_bancaria = BancoModelo.objects.get(id=self.numero_cuenta)
                except BancoModelo.DoesNotExist:
                    raise ValueError(f"No se encontró una cuenta bancaria con el ID {self.numero_cuenta}.")
                if cuenta_bancaria.saldo < self.abono:
                    raise ValueError("La cuenta bancaria no tiene saldo suficiente para realizar este abono.")

        # Solo se guarda si no hay errores
        super().save(*args, **kwargs)

        if is_new:
            # Ya validado, ahora se puede crear el movimiento correspondiente
            if self.tipo_de_pago == 'tarjeta':
                tarjeta = TarjetaCredito.objects.get(numero_tarjeta=self.numero_tarjeta)
                if self.tipo_tarjeta == 'credito':
                    pago_mensual_actual = tarjeta.pagos_mensuales.filter(actual=True).first()
                    MovimientoTarjeta.objects.create(
                        tarjeta=tarjeta,
                        monto=self.abono,
                        concepto=self.referencia,
                        fecha=self.fecha_abono,
                        origen='Servicios',
                        pago_mensual=pago_mensual_actual,
                    )
                    pago_mensual_actual.saldo_pendiente += self.abono
                    pago_mensual_actual.save()
                elif self.tipo_tarjeta == 'debito':
                    tarjeta_debito = TarjetaCredito.objects.get(numero_tarjeta=self.numero_tarjeta, tipo_tarjeta='debito')
                    tarjeta_banco = TarjetasBanco.objects.get(tarjeta=tarjeta_debito)
                    banco_asociado = tarjeta_banco.banco
                    AbonoBanco.objects.create(
                        numero_cuenta=banco_asociado,
                        monto_movimiento=self.abono,
                        tipo_movimiento='egreso',
                        fecha_movimiento=self.fecha_abono.date(),
                        referencia=self.referencia,
                        pdf_comprobante=self.pdf_referencia,
                        comentarios='Gasto desde servicio',
                        proveedor='Pago Servicio',
                        entrada_salida='salida',
                    )

            elif self.tipo_de_pago in ['transferencia', 'cheque']:
                cuenta_bancaria = BancoModelo.objects.get(id=self.numero_cuenta)
                AbonoBanco.objects.create(
                    numero_cuenta=cuenta_bancaria,
                    monto_movimiento=self.abono,
                    tipo_movimiento='egreso',
                    fecha_movimiento=self.fecha_abono.date(),
                    referencia=self.referencia,
                    pdf_comprobante=self.pdf_referencia,
                    comentarios='Gasto desde servicio',
                    proveedor='Pago Servicio',
                    entrada_salida='salida',
                )

            elif self.tipo_de_pago == 'terceros':
                OtroGasto.objects.create(
                    tipo_gasto=TipoOtroGasto.objects.get(nombre='terceros'),  
                    proveedor=f'servicio de {self.periodo.servicio.nombre_servicio}',
                    descripcion='Abono de servicio como terceros',
                    divisa=f'{self.periodo.servicio.divisa}',
                    tipo_pago='terceros',
                    monto_total=self.abono,
                    fecha_gasto=self.fecha_abono.date(),
                    ticket_factura=self.pdf_referencia,
                    estatus='inicial',
                )

            # Actualizar saldo del periodo
            self.periodo.saldo_pendiente -= self.abono
            if self.periodo.saldo_pendiente <= 0:
                self.periodo.estatus = 'pagado'
                self.periodo.usado = True
                self.periodo.saldo_pendiente = 0.0
            self.periodo.propuesta_pago = 0.0
            self.periodo.save()

            self.periodo.servicio.verificar_estado_servicio()

    def __str__(self):
        return f"Abono {self.tipo_de_pago} de {self.abono} para el periodo {self.periodo.id}"


class TipoOtroGasto(models.Model):
    nombre = models.CharField(max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=['nombre']),
        ]

    def __str__(self):
        return self.nombre

class OtroGasto(models.Model):
    DIVISA_CHOICES = [
        ('MXN', 'MXN'),
        ('USD', 'USD'),
    ]

    ESTATUS_CHOICES = [
        ('inicial', 'Inicial'),
        ('pendiente', 'Pendiente'),
        ('rechazado', 'Rechazado'),
        ('programado', 'Programado'),
        ('pagado', 'Pagado'),
    ]
    
    TIPO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('tarjeta_confio', 'Tarjeta Confio'),
        ('transferencia', 'Transferencia'),
        ('cheque', 'Cheque'),
        ('terceros', 'Terceros'),
    ]
    
    TIPO_TARJETA = [
        ('credito', 'Credito'),
        ('debito', 'Debito'),
    ]

    tarjeta = models.ForeignKey(TarjetaCredito, on_delete=models.SET_NULL, null=True, blank=True, related_name='movimiento_otros_gastos')
    fecha = models.DateField(auto_now_add=True)
    fecha_gasto = models.DateField(null=True, blank=True)
    descripcion = models.TextField()
    proveedor = models.TextField(default='Bimbo', null=True, blank=True)
    tipo_gasto = models.ForeignKey(TipoOtroGasto, on_delete=models.CASCADE, related_name='gastos')
    monto_total = models.DecimalField(max_digits=15, decimal_places=2)
    divisa = models.CharField(max_length=3, choices=DIVISA_CHOICES, default='MXN')
    estatus = models.CharField(max_length=10, choices=ESTATUS_CHOICES, default='pendiente')
    ticket_factura = models.FileField(upload_to='facturas/', null=True, blank=True)
    fecha_aprobacion = models.DateField(null=True, blank=True)
    fecha_pago = models.DateField(null=True, blank=True)
    saldo = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tipo_pago = models.CharField(max_length=15, choices=TIPO_PAGO_CHOICES, null=True, blank=True)
    tipo_tarjeta = models.CharField(max_length=15, choices=TIPO_TARJETA, null=True, blank=True)
    numero_cuenta = models.CharField(max_length=30, null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['fecha']),
            models.Index(fields=['estatus']),
            models.Index(fields=['tipo_gasto']),
            models.Index(fields=['divisa']),
            models.Index(fields=['tipo_pago']),
        ]

    def __str__(self):
        return f"Otro Gasto: {self.descripcion} ({self.monto_total} {self.divisa})"

    def calcular_saldo(self):
        total_abonos = self.abonos.aggregate(Sum('abono'))['abono__sum'] or 0
        return self.monto_total - total_abonos
    def save(self, *args, **kwargs):
        # Si ya existe (update), solo guarda normalmente
        is_new = self.pk is None

        # Primero guarda el gasto para obtener el ID (pero no continúes si no es nuevo)
        if not is_new:
            super().save(*args, **kwargs)
            return

        # Validar saldo suficiente antes de continuar
        if self.tipo_pago == 'tarjeta' and self.tipo_tarjeta == 'debito':
            try:
                tarjeta_asociada = TarjetasBanco.objects.get(tarjeta=self.tarjeta)
                cuenta_banco = tarjeta_asociada.banco
            except TarjetasBanco.DoesNotExist:
                raise ValueError("Error: No se encontró la cuenta bancaria asociada a la tarjeta de débito.")

            if cuenta_banco.saldo < self.monto_total:
                raise ValueError(f"Saldo insuficiente. El saldo disponible es ${cuenta_banco.saldo} y el gasto es ${self.monto_total}.")

        elif self.tipo_pago in ('transferencia', 'cheque', 'efectivo'):
            try:
                cuenta_banco = BancoModelo.objects.get(id=self.numero_cuenta)
            except BancoModelo.DoesNotExist:
                raise ValueError("Error: No se encontró la cuenta bancaria.")

            if cuenta_banco.saldo < self.monto_total:
                raise ValueError(f"Saldo insuficiente. El saldo disponible es ${cuenta_banco.saldo} y el gasto es ${self.monto_total}.")

        # Si todo es válido, guarda el gasto
        super().save(*args, **kwargs)

        # Ahora sí, proceder con movimientos
        if self.tipo_pago == 'tarjeta':
            if self.tipo_tarjeta == 'credito':
                pago_mensual = PagoMensualTarjeta.objects.filter(
                    tarjeta__numero_tarjeta=self.tarjeta.numero_tarjeta,
                    actual=True
                ).first()

                if not pago_mensual:
                    raise ValueError("No se encontró un PagoMensualTarjeta actual para la tarjeta.")

                MovimientoTarjeta.objects.create(
                    monto=self.monto_total,
                    concepto=self.descripcion,
                    tarjeta=self.tarjeta,
                    origen='Otros Gastos',
                    pago_mensual=pago_mensual
                )
                self.tarjeta.saldo += self.monto_total
                self.tarjeta.save()

            elif self.tipo_tarjeta == 'debito':
                AbonoBanco.objects.create(
                    numero_cuenta=cuenta_banco,
                    monto_movimiento=self.monto_total,
                    tipo_movimiento='egreso',
                    fecha_movimiento=self.fecha_gasto or self.fecha,
                    referencia=f"Pago de Otro Gasto ID: {self.id} - Tarjeta: {self.tarjeta.numero_tarjeta}",
                    pdf_comprobante=self.ticket_factura,
                    comentarios=f"Egreso desde Otros Gastos - Proveedor: {self.proveedor}",
                    proveedor=self.proveedor,
                    entrada_salida='salida'
                )

        elif self.tipo_pago in ('transferencia', 'cheque', 'efectivo'):
            AbonoBanco.objects.create(
                numero_cuenta=cuenta_banco,
                monto_movimiento=self.monto_total,
                tipo_movimiento='egreso',
                fecha_movimiento=self.fecha_gasto or self.fecha,
                referencia=self.descripcion,
                pdf_comprobante=self.ticket_factura,
                comentarios='Egreso de Otros Gastos',
                proveedor=self.proveedor,
                entrada_salida='salida',
            )


class PagoOtroGasto(models.Model):
    TIPO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
        ('cheque', 'Cheque'),
        ('terceros', 'Terceros'),
    ]
    
    TIPO_TARJETA = [
        ('credito', 'Credito'),
        ('debito', 'Debito'),
    ]
    
    otro_gasto = models.ForeignKey(OtroGasto, on_delete=models.CASCADE, related_name='abonos')
    numero_tarjeta = models.CharField(max_length=19, null=True, blank=True)
    abono = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_abono = models.DateTimeField()
    referencia = models.CharField(max_length=255, null=True, blank=True)
    pdf_referencia = models.FileField(upload_to='pdf_referencias/', null=True, blank=True)
    tipo_de_pago = models.CharField(max_length=15, choices=TIPO_PAGO_CHOICES, default='transferencia')
    tipo_tarjeta = models.CharField(max_length=15, choices=TIPO_TARJETA, null=True, blank=True)
    numero_cuenta = models.CharField(max_length=19, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['fecha_abono']),
            models.Index(fields=['otro_gasto']),
        ]
        
    def save(self, *args, **kwargs):
        is_new = self.pk is None  # Verifica si es nuevo

        if is_new:
            # Obtener el proveedor del OtroGasto relacionado
            proveedor = self.otro_gasto.proveedor if self.otro_gasto and self.otro_gasto.proveedor else "Proveedor no especificado"

            # Validaciones previas a guardar
            if self.tipo_de_pago == 'tarjeta':
                if not self.numero_tarjeta:
                    raise ValueError("El número de tarjeta es obligatorio para pagos con tarjeta.")

                tarjeta = TarjetaCredito.objects.filter(numero_tarjeta=self.numero_tarjeta).first()
                if not tarjeta:
                    raise ValueError(f"No se encontró una tarjeta con número {self.numero_tarjeta}.")

                if self.tipo_tarjeta == 'credito':
                    pago_mensual_actual = tarjeta.pagos_mensuales.filter(actual=True).first()
                    if not pago_mensual_actual:
                        raise ValueError("No se encontró un PagoMensualTarjeta actual.")

                    # Guardar abono después
                elif self.tipo_tarjeta == 'debito':
                    tarjeta_asociada = TarjetasBanco.objects.filter(tarjeta=tarjeta).first()
                    if not tarjeta_asociada:
                        raise ValueError(f"No se encontró cuenta bancaria asociada a la tarjeta débito {tarjeta.numero_tarjeta}.")
                    
                    cuenta_bancaria = tarjeta_asociada.banco
                    if cuenta_bancaria.saldo < self.abono:
                        raise ValueError("Saldo insuficiente en la cuenta bancaria asociada a la tarjeta débito.")

            elif self.tipo_de_pago in ['transferencia', 'cheque', 'efectivo']:
                if not self.numero_cuenta:
                    raise ValueError("Se requiere un número de cuenta para pagos por transferencia, cheque o efectivo.")

                try:
                    if self.numero_cuenta.isdigit():
                        cuenta_bancaria = BancoModelo.objects.get(id=int(self.numero_cuenta))
                    else:
                        cuenta_bancaria = BancoModelo.objects.get(numero_cuenta=self.numero_cuenta)
                except BancoModelo.DoesNotExist:
                    raise ValueError(f"No se encontró una cuenta bancaria con el número o ID {self.numero_cuenta}.")

                if cuenta_bancaria.saldo < self.abono:
                    raise ValueError("Saldo insuficiente en la cuenta bancaria para realizar el abono.")

        # ✅ Si pasó las validaciones, ahora sí guarda y aplica movimientos
        super().save(*args, **kwargs)

        if is_new:
            proveedor = self.otro_gasto.proveedor or "Proveedor no especificado"

            if self.tipo_de_pago == 'tarjeta':
                tarjeta = TarjetaCredito.objects.get(numero_tarjeta=self.numero_tarjeta)
                if self.tipo_tarjeta == 'credito':
                    pago_mensual_actual = tarjeta.pagos_mensuales.filter(actual=True).first()
                    MovimientoTarjeta.objects.create(
                        tarjeta=tarjeta,
                        monto=self.abono,
                        concepto=self.referencia,
                        fecha=self.fecha_abono,
                        origen='Otros Gastos',
                        pago_mensual=pago_mensual_actual,
                    )
                    pago_mensual_actual.saldo_pendiente += self.abono
                    pago_mensual_actual.save()
                elif self.tipo_tarjeta == 'debito':
                    tarjeta_asociada = TarjetasBanco.objects.get(tarjeta=tarjeta)
                    cuenta_bancaria = tarjeta_asociada.banco
                    AbonoBanco.objects.create(
                        numero_cuenta=cuenta_bancaria,
                        monto_movimiento=self.abono,
                        tipo_movimiento='egreso',
                        fecha_movimiento=self.fecha_abono.date(),
                        referencia=self.referencia,
                        pdf_comprobante=self.pdf_referencia,
                        comentarios='Gasto desde Otros Gastos',
                        proveedor=proveedor,
                        entrada_salida='salida',
                    )

            elif self.tipo_de_pago in ['transferencia', 'cheque', 'efectivo']:
                if self.numero_cuenta.isdigit():
                    cuenta_bancaria = BancoModelo.objects.get(id=int(self.numero_cuenta))
                else:
                    cuenta_bancaria = BancoModelo.objects.get(numero_cuenta=self.numero_cuenta)

                AbonoBanco.objects.create(
                    numero_cuenta=cuenta_bancaria,
                    monto_movimiento=self.abono,
                    tipo_movimiento='egreso',
                    fecha_movimiento=self.fecha_abono.date(),
                    referencia=self.referencia,
                    pdf_comprobante=self.pdf_referencia,
                    comentarios='Gasto desde Otros Gastos',
                    proveedor=proveedor,
                    entrada_salida='salida',
                )

            if self.tipo_de_pago != 'terceros':
                self.otro_gasto.saldo -= self.abono
                if self.otro_gasto.saldo <= 0:
                    self.otro_gasto.estatus = 'pagado'
                    self.otro_gasto.saldo = 0.0
                self.otro_gasto.save()

    def __str__(self):
        return f"Abono {self.tipo_de_pago} de {self.abono} para el gasto {self.otro_gasto.id}"


    
class CuentaBancaria(models.Model):
    servicio = models.ForeignKey(ServiciosFactura, related_name='cuentas_bancarias', on_delete=models.CASCADE)
    numero_cuenta = models.CharField(max_length=20)
    clave_interbancaria = models.CharField(max_length=18)
    banco = models.CharField(max_length=100)

    def __str__(self):
        return f"Cuenta {self.numero_cuenta} - {self.banco} (Servicio: {self.servicio.nombre_servicio})"


# Tabla para el ISR
class Isr(models.Model):
    limite_inferior = models.DecimalField(max_digits=15, decimal_places=2)
    limite_superior = models.DecimalField(max_digits=15, decimal_places=2)
    cuota_fija = models.DecimalField(max_digits=15, decimal_places=2)
    porcentaje_excedente = models.CharField(max_length=255)  # Asumiendo un porcentaje como 0.00 formato

    estatus = models.CharField(max_length=20, choices=[('actualizado', 'Actualizado'), ('desactualizado', 'Desactualizado')], default='actualizado')
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def verificar_actualizacion(self):
        inicio_anio_actual = timezone.datetime(timezone.now().year, 1, 1, tzinfo=timezone.utc)
        if self.fecha_modificacion < inicio_anio_actual:
            self.estatus = 'desactualizado'
        else:
            self.estatus = 'actualizado'
        self.save(update_fields=['estatus'])
        
    class Meta:
        verbose_name = "ISR"
        verbose_name_plural = "ISR"
        
    def __str__(self):
        return f"ISR: {self.limite_inferior} - {self.limite_superior}"


# Tabla para vacaciones
class Vacaciones(models.Model):
    años = models.IntegerField()
    dias = models.IntegerField()

    estatus = models.CharField(max_length=20, choices=[('actualizado', 'Actualizado'), ('desactualizado', 'Desactualizado')], default='actualizado')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def verificar_actualizacion(self):
        inicio_anio_actual = timezone.datetime(timezone.now().year, 1, 1, tzinfo=timezone.utc)
        if self.fecha_modificacion < inicio_anio_actual:
            self.estatus = 'desactualizado'
        else:
            self.estatus = 'actualizado'
        self.save(update_fields=['estatus'])
    class Meta:
        verbose_name = "Vacaciones"
        verbose_name_plural = "Vacaciones"
        
    def str(self):
        return f"Vacaciones: {self.años} años - {self.dias} días"


# Tabla para aportaciones obrero-patronales IMSS
class AportacionObreroPatronales(models.Model):
    concepto = models.CharField(max_length=255)
    patron = models.CharField(max_length=255)
    trabajador = models.CharField(max_length=255)

    estatus = models.CharField(max_length=20, choices=[('actualizado', 'Actualizado'), ('desactualizado', 'Desactualizado')], default='actualizado')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def verificar_actualizacion(self):
        inicio_anio_actual = timezone.datetime(timezone.now().year, 1, 1, tzinfo=timezone.utc)
        if self.fecha_modificacion < inicio_anio_actual:
            self.estatus = 'desactualizado'
        else:
            self.estatus = 'actualizado'
        self.save(update_fields=['estatus'])
        
    class Meta:
        verbose_name = "Aportaciones Obrero patronales IMSS"
        verbose_name_plural = "Aportaciones Obrero patronales IMSS"
        
    def __str__(self):
        return f"Aportación Obrero Patronal: {self.concepto}"


# Tabla para aportaciones patronales IMSS
class AportacionPatronalesIMSS(models.Model):
    concepto = models.CharField(max_length=255)
    patron = models.CharField(max_length=255)
    trabajador = models.CharField(max_length=255)

    estatus = models.CharField(max_length=20, choices=[('actualizado', 'Actualizado'), ('desactualizado', 'Desactualizado')], default='actualizado')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def verificar_actualizacion(self):
        inicio_anio_actual = timezone.datetime(timezone.now().year, 1, 1, tzinfo=timezone.utc)
        if self.fecha_modificacion < inicio_anio_actual:
            self.estatus = 'desactualizado'
        else:
            self.estatus = 'actualizado'
        self.save(update_fields=['estatus'])

    class Meta:
        verbose_name = "Aportaciones patronales Infonavit"
        verbose_name_plural = "Aportaciones patronales Infonavit"
        
    def __str__(self):
        return f"Aportación Patronal IMSS: {self.concepto}"


# Tabla para aportaciones retiro IMSS
class AportacionRetiroIMSS(models.Model):
    concepto = models.CharField(max_length=255)
    patron = models.CharField(max_length=255)
    trabajador = models.CharField(max_length=255)

    estatus = models.CharField(max_length=20, choices=[('actualizado', 'Actualizado'), ('desactualizado', 'Desactualizado')], default='actualizado')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def verificar_actualizacion(self):
        inicio_anio_actual = timezone.datetime(timezone.now().year, 1, 1, tzinfo=timezone.utc)
        if self.fecha_modificacion < inicio_anio_actual:
            self.estatus = 'desactualizado'
        else:
            self.estatus = 'actualizado'
        self.save(update_fields=['estatus'])

    class Meta:
        verbose_name = "Aportaciones retiro IMSS"
        verbose_name_plural = "Aportaciones retiro IMSS"
        
    def __str__(self):
        return f"Aportación Retiro IMSS: {self.concepto}"


# Tabla para CEAV IMSS
class CeavIMSS(models.Model):
    concepto = models.CharField(max_length=255)
    patron = models.CharField(max_length=255)
    trabajador = models.CharField(max_length=255)

    estatus = models.CharField(max_length=20, choices=[('actualizado', 'Actualizado'), ('desactualizado', 'Desactualizado')], default='actualizado')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def verificar_actualizacion(self):
        inicio_anio_actual = timezone.datetime(timezone.now().year, 1, 1, tzinfo=timezone.utc)
        if self.fecha_modificacion < inicio_anio_actual:
            self.estatus = 'desactualizado'
        else:
            self.estatus = 'actualizado'
        self.save(update_fields=['estatus'])
        
    class Meta:
        verbose_name = "CEAV IMSS"
        verbose_name_plural = "CEAV IMSS"
        
    def __str__(self):
        return f"CEAV IMSS: {self.concepto}"


# Tabla para CEAV Patronal
class CeavPatronal(models.Model):
    limite_inferior = models.DecimalField(max_digits=15, decimal_places=2)
    limite_superior = models.DecimalField(max_digits=15, decimal_places=2)
    porcentaje = models.DecimalField(max_digits=10, decimal_places=6)  # Para soportar porcentajes precisos

    estatus = models.CharField(
        max_length=20, 
        choices=[('actualizado', 'Actualizado'), ('desactualizado', 'Desactualizado')], 
        default='actualizado'
    )
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def verificar_actualizacion(self):
        """
        Actualiza el estatus de la tabla si la fecha de modificación es menor al inicio del año actual.
        """
        inicio_anio_actual = timezone.datetime(timezone.now().year, 1, 1, tzinfo=timezone.utc)
        if self.fecha_modificacion < inicio_anio_actual:
            self.estatus = 'desactualizado'
        else:
            self.estatus = 'actualizado'
        self.save(update_fields=['estatus'])
    class Meta:
        verbose_name = "CEAV patronal"
        verbose_name_plural = "CEAV patronal"
        
    def __str__(self):
        return f"CEAV Patronal: {self.limite_inferior} - {self.limite_superior}"


# Tabla para salario mínimo y UMA
class SalarioMinimo(models.Model):
    salario_minimo = models.CharField(max_length=255)
    uma = models.CharField(max_length=255)

    estatus = models.CharField(max_length=20, choices=[('actualizado', 'Actualizado'), ('desactualizado', 'Desactualizado')], default='actualizado')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def verificar_actualizacion(self):
        inicio_anio_actual = timezone.datetime(timezone.now().year, 1, 1, tzinfo=timezone.utc)
        if self.fecha_modificacion < inicio_anio_actual:
            self.estatus = 'desactualizado'
        else:
            self.estatus = 'actualizado'
        self.save(update_fields=['estatus'])

    class Meta:
        verbose_name = "Salario Minimo"
        verbose_name_plural = "Salario Minimo"

    def __str__(self):
        return f"Salario Mínimo: {self.salario_minimo} - UMA: {self.uma}"
    
class BancoModelo(models.Model):
    ESTATUS_CHOICES = [
        ('activa', 'Activa'),
        ('inactiva', 'Inactiva'),
        ('bloqueada', 'Bloqueada'),
    ]
    DIVISA_CHOICES = [
        ('MXN', 'MXN'),
        ('USD', 'USD'),
    ]
    TIPO_TARJETA = [
        ('credito', 'Credito'),
        ('debito', 'Debito'),
    ]

    banco = models.CharField(max_length=255)
    numero_cuenta = models.CharField(max_length=19, unique=True)
    numero_tarjeta = models.CharField(max_length=19, unique=True, null=True, blank=True)
    fecha_vencimiento = models.DateField()
    estatus = models.CharField(max_length=10, choices=ESTATUS_CHOICES, default='activa')
    saldo = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    divisa = models.CharField(max_length=3, choices=DIVISA_CHOICES, default='MXN')
    comentarios = models.CharField(max_length=255, null=True, blank=True)
    cliente = models.CharField(max_length=255)
    cuenta_ejecutivo = models.CharField(max_length=255, null=True, blank=True)
    telefono_ejecutivo = models.CharField(max_length=255, null=True, blank=True)
    pdf_comprobante = models.FileField(upload_to='bancos/', null=True, blank=True)
    tipo_tarjeta = models.CharField(max_length=15, choices=TIPO_TARJETA, null=True, blank=True)

    def __str__(self):
        return f"Cuenta {self.numero_cuenta} - Banco {self.banco}"

    def save(self, *args, **kwargs):
        # Guardar cambios en BancoModelo y replicar la tarjeta si corresponde
        super().save(*args, **kwargs)
        if self.tipo_tarjeta == 'debito' and self.numero_tarjeta:
            self.replicar_tarjeta()

    def replicar_tarjeta(self):
        """Crear una entrada en TarjetaCredito para la tarjeta de débito"""
        if not TarjetaCredito.objects.filter(numero_tarjeta=self.numero_tarjeta).exists():
            TarjetaCredito.objects.create(
                banco=self.banco,  # Nombre del banco
                numero_tarjeta=self.numero_tarjeta,  # Número de tarjeta
                saldo=self.saldo,  # Saldo inicial
                divisa=self.divisa,  # Divisa
                tipo_tarjeta='debito',  # Tipo de tarjeta
                estatus='activa',  # Estatus inicial
                fecha_creacion=timezone.now(),  # Fecha de creación
                banco_asociado=str(self.id),  # Pasar el ID del banco como cadena
            )
    
            
class MovimientoBanco(models.Model):
    TIPO_MOVIMIENTO = [
        ('ingreso', 'Ingreso'),
        ('egreso', 'Egreso'),
        ('diario', 'Diario'),
    ]

    numero_cuenta = models.ForeignKey(BancoModelo,on_delete=models.CASCADE,related_name='movimientos_banco')
    saldo_anterior = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    monto_movimiento = models.DecimalField(max_digits=15, decimal_places=2)
    tipo_movimiento = models.CharField(max_length=20, choices=TIPO_MOVIMIENTO, default='ingreso')
    fecha_movimiento = models.DateTimeField()
    divisa = models.CharField(max_length=3, choices=BancoModelo.DIVISA_CHOICES, default='MXN')
    nuevo_saldo = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    referencia = models.CharField(max_length=255, null=True, blank=True)
    cliente = models.CharField(max_length=255, null=True, blank=True)
    proveedor = models.CharField(max_length=255, null=True, blank=True)
    comentarios = models.CharField(max_length=255, null=True, blank=True)
    pdf_comprobante = models.FileField(upload_to='bancos/', null=True, blank=True)

    def __str__(self):
        return f"Movimiento {self.tipo_movimiento} - {self.monto_movimiento} para {self.numero_cuenta.numero_cuenta}"


class AbonoBanco(models.Model):
    TIPO_MOVIMIENTO = [
        ('ingreso', 'Ingreso'),
        ('egreso', 'Egreso'),
        ('diario', 'Diario'),
    ]
    ENTRADA_SALIDA_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
    ]

    numero_cuenta = models.ForeignKey(BancoModelo,on_delete=models.CASCADE,related_name='abonos_banco')
    monto_movimiento = models.DecimalField(max_digits=15, decimal_places=2)
    tipo_movimiento = models.CharField(max_length=20, choices=TIPO_MOVIMIENTO, default='ingreso')
    fecha_movimiento = models.DateField()
    referencia = models.CharField(max_length=100, null=True, blank=True)
    pdf_comprobante = models.FileField(upload_to='bancos/', null=True, blank=True)
    comentarios = models.CharField(max_length=255, null=True, blank=True)
    cliente = models.CharField(max_length=255, null=True, blank=True)
    proveedor = models.CharField(max_length=255, null=True, blank=True)
    entrada_salida = models.CharField(max_length=10, choices=ENTRADA_SALIDA_CHOICES, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Actualizar saldo de la cuenta asociada
        cuenta = self.numero_cuenta
        saldo_anterior = cuenta.saldo

        # Lógica para ingresos y egresos
        if self.tipo_movimiento == 'ingreso':
            cuenta.saldo += self.monto_movimiento
        elif self.tipo_movimiento == 'egreso':
            cuenta.saldo -= self.monto_movimiento

        # Lógica adicional para entradas y salidas (diario)
        if self.tipo_movimiento == 'diario':
            if self.entrada_salida == 'entrada':
                cuenta.saldo += self.monto_movimiento
            elif self.entrada_salida == 'salida':
                cuenta.saldo -= self.monto_movimiento

        cuenta.save()

        # Crear un movimiento asociado, manejando valores nulos
        MovimientoBanco.objects.create(
            numero_cuenta=self.numero_cuenta,
            saldo_anterior=saldo_anterior,
            monto_movimiento=self.monto_movimiento,
            divisa=self.numero_cuenta.divisa,
            fecha_movimiento=self.fecha_movimiento,
            tipo_movimiento=self.tipo_movimiento,
            nuevo_saldo=cuenta.saldo,
            referencia=self.referencia,  
            cliente=self.cliente, 
            proveedor=self.proveedor,
            comentarios=self.comentarios, 
            pdf_comprobante=self.pdf_comprobante,  
        )

        super().save(*args, **kwargs)

        def __str__(self):
            return f"Abono {self.tipo_movimiento} de {self.monto_movimiento} para {self.numero_cuenta.numero_cuenta}"

class TarjetasBanco(models.Model):
    banco = models.ForeignKey(BancoModelo, on_delete=models.CASCADE, related_name='tarjetas_debito_asociadas')  # Relación con BancoModelo
    tarjeta = models.ForeignKey(TarjetaCredito, on_delete=models.CASCADE, related_name='bancos_asociados')  # Relación con TarjetaCredito
    fecha_asociacion = models.DateTimeField(auto_now_add=True)  # Fecha en que se asoció la tarjeta al banco

    def __str__(self):
        return f"Tarjeta Débito {self.tarjeta.numero_tarjeta} - Banco {self.banco.banco}"

    def save(self, *args, **kwargs):
        # Verificar que la tarjeta sea de débito antes de guardar
        if self.tarjeta.tipo_tarjeta != 'debito':
            raise ValueError("Solo se pueden asociar tarjetas de débito a un banco.")
        super().save(*args, **kwargs)
    
class Nomina(models.Model):
    ESTATUS_CHOICES = [
        ('inicial', 'Inicial'),
        ('pendiente', 'Pendiente'),
        ('programada', 'Programada'),
        ('pagada', 'Pagada'),
    ]

    empleado = models.ForeignKey('ri_rh.Empleado', on_delete=models.CASCADE, related_name='nominas')
    dias_trabajados = models.IntegerField(default=5)
    tiempo_extra = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    vales_despensa = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    vales_gasolina = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    monto_aprobado_nomina = models.DecimalField(max_digits=10, decimal_places=2)
    observaciones = models.TextField(blank=True, null=True)
    estatus = models.CharField(max_length=20, choices=ESTATUS_CHOICES, default='pendiente')
    fecha_nomina = models.DateField(default=timezone.now)
    deduccion_infonavit = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    deduccion_prestamos = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    subsidio_empleo = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    # Campos calculados
    salario_diario_integral = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    bruto_semanal = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    suma_percepciones = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    impuestos_isr = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    #Totales de imss obrero/ Patronal
    imss_obrero = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    imss_patronal = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    
    #Desglose de calculados IMSS obrero 
    cuota_fija = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    excedente_obrero = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    gmp_obrero = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    rt_obrero = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    iv_obrero = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    gps_obrero = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    en_dinero_obrero = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)


    #Desglose de calculados IMSS patronal
    cuota_fija_patronal = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    excedente_patronal = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    gmp_patronal = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    rt_patronal = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    iv_patronal = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    gps_patronal = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    en_dinero_patronal = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)

    infonavit_patronal = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    aportacion_retiro_imss = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    ceav_obrero = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    ceav_patronal = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    suma_deducciones = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    nomina_a_depositar = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    total_impuestos = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    nomina_semanal_fiscal = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0.0)
    horas_retardo = models.IntegerField(default=0)


    def calcular_nomina_semanal_fiscal(self):
        """
        Calcula la Nómina Semanal Fiscal como:
        Nomina a depositar +
        CEAV Patronal +
        Retiro Patronal +
        Infonavit Patronal +
        IMSS Patronal +
        CEAV Obrero +
        Cuota fija IMSS +
        IMSS Obrero +
        Impuesto ISR +
        Vales de despensa +
        Vales de gasolina
        """
        return (
            self.nomina_a_depositar +
            self.ceav_patronal +
            self.aportacion_retiro_imss +
            self.infonavit_patronal +
            self.imss_patronal +
            self.ceav_obrero +
            self.imss_obrero +
            self.impuestos_isr +
            self.vales_despensa +
            self.vales_gasolina
        )

    def calcular_total_impuestos(self):
        """
        Calcula el total de impuestos como la suma de:
        - Impuestos ISR
        - IMSS Obrero
        - IMSS Patronal
        - Cuota fija IMSS
        - Infonavit Patronal
        - Deducción de Infonavit
        - Deducción de Préstamo
        - Retiro Patronal
        - CEAV Obrero
        - CEAV Patronal
        """
        return (
            self.impuestos_isr +
            self.imss_obrero +
            self.imss_patronal +
            self.infonavit_patronal +
            self.deduccion_infonavit +
            self.deduccion_prestamos +
            self.aportacion_retiro_imss +
            self.ceav_obrero +
            self.ceav_patronal
        )


    def calcular_nomina_a_depositar(self):
        """
        Calcula la nómina a depositar como la diferencia entre suma de percepciones y suma de deducciones.
        """
        return self.suma_percepciones - self.suma_deducciones


    def calcular_suma_deducciones(self):
        """
        Calcula la suma de todas las deducciones:
        - Impuesto ISR
        - IMSS Obrero
        - Deducción INFONAVIT
        - Deducción Préstamos
        - CEAV Obrero
        - Subsidio Empleo
        """
        return (
            self.impuestos_isr +
            self.imss_obrero +
            self.deduccion_infonavit +
            self.deduccion_prestamos +
            self.ceav_obrero +
            self.subsidio_empleo  # Subsidio Empleo se resta si es negativo
        )


    def calcular_salario_diario_integral(self):
        dias_vacaciones = self.empleado.calcular_vacaciones()
        factor_integral = (((0.25 * dias_vacaciones) + 15) / 365) + 1
        return self.empleado.salario_diario * Decimal(factor_integral)

    def calcular_bruto_semanal(self):
        return (((self.dias_trabajados * 9) + 3) - self.horas_retardo) * (self.empleado.salario_diario * 7) / 48

    def calcular_suma_percepciones(self):
        return self.bruto_semanal + self.tiempo_extra

    def calcular_isr(self):
        suma_percepciones = self.suma_percepciones
        isr_entry = Isr.objects.filter(
            limite_inferior__lte=suma_percepciones,
            limite_superior__gte=suma_percepciones
        ).first()

        if not isr_entry:
            # Caso especial para valores fuera de rango superior
            isr_entry = Isr.objects.filter(limite_superior__isnull=True).first()

        if isr_entry:
            excedente = suma_percepciones - isr_entry.limite_inferior
            porcentaje = Decimal(isr_entry.porcentaje_excedente)
            return (excedente * porcentaje) + isr_entry.cuota_fija

        return Decimal('0.00')

    def calcular_cuota_fija(self):
        """
        Calcula la cuota fija para el IMSS Obrero.
        """
        if self.suma_percepciones == 0:
            return Decimal("0.00")
        # Configuración del logger
        
        salario_minimo_entry = SalarioMinimo.objects.last()
        if not salario_minimo_entry:
            raise ValueError("El registro de salario mínimo no está configurado.")

        uma_diaria = Decimal(salario_minimo_entry.uma)

        tasas = AportacionObreroPatronales.objects.filter(
            concepto__iexact="cuota fija por cada empleado hasta por tres veces la UMA"
        ).first()

        if not tasas:
            raise ValueError("No se encontraron tasas para la cuota fija.")

        patron_tasa = Decimal(tasas.trabajador)

        cuota_fija = uma_diaria * 7 * patron_tasa

        return round(cuota_fija, 2)

    def calcular_excedente_obrero(self):
        """
        Calcula el excedente del salario base de cotización (SBC) por encima de 3 veces la UMA.
        """
        if self.suma_percepciones == 0:
            return Decimal("0.00")

        salario_minimo_entry = SalarioMinimo.objects.last()
        if not salario_minimo_entry:
            raise ValueError("El registro de salario mínimo no está configurado.")

        uma_diaria = Decimal(salario_minimo_entry.uma)
        salario_integral = self.salario_diario_integral

        diferencia_sbc = max(salario_integral - (3 * uma_diaria), 0)

        tasas = AportacionObreroPatronales.objects.filter(
            concepto__iexact="cuota adicional por la diferencia del sbc y de 3 veces la uma"
        ).first()

        if not tasas:
            raise ValueError("No se encontraron tasas para el excedente.")

        trabajador_tasa = Decimal(tasas.trabajador)
        excedente_obrero = diferencia_sbc * trabajador_tasa * 7

        return round(excedente_obrero, 2)

    def calcular_gmp_obrero(self):
        """
        Calcula los gastos médicos para pensionados y beneficiarios (GMP) del IMSS Obrero.
        """
        if self.suma_percepciones == 0:
            return Decimal("0.00")

        salario_integral = self.salario_diario_integral

        tasas = AportacionObreroPatronales.objects.filter(
            concepto__iexact="gastos medicos para pensionados y beneficiarios"
        ).first()

        if not tasas:
            raise ValueError("No se encontraron tasas para GMP.")

        trabajador_tasa = Decimal(tasas.trabajador)
        gmp_obrero = salario_integral * trabajador_tasa * 7

        return round(gmp_obrero, 2)

    def calcular_rt_obrero(self):
        """
        Calcula los riesgos de trabajo (RT) del IMSS Obrero.
        """
        if self.suma_percepciones == 0:
            return Decimal("0.00")

        salario_integral = self.salario_diario_integral

        tasas = AportacionObreroPatronales.objects.filter(
            concepto__iexact="riesgos de trabajo"
        ).first()

        if not tasas:
            raise ValueError("No se encontraron tasas para RT.")

        trabajador_tasa = Decimal(tasas.trabajador)
        rt_obrero = salario_integral * trabajador_tasa * 7

        return round(rt_obrero, 2)

    def calcular_iv_obrero(self):
        """
        Calcula la invalidez y vida (IV) del IMSS Obrero.
        """
        if self.suma_percepciones == 0:
            return Decimal("0.00")

        salario_integral = self.salario_diario_integral

        tasas = AportacionObreroPatronales.objects.filter(
            concepto__iexact="invalidez y vida"
        ).first()

        if not tasas:
            raise ValueError("No se encontraron tasas para IV.")

        trabajador_tasa = Decimal(tasas.trabajador)
        iv_obrero = salario_integral * trabajador_tasa * 7

        return round(iv_obrero, 2)
    
    def calcular_gps_obrero(self):
        """
        Calcula las guarderías y prestaciones sociales (GPS) del IMSS Obrero.
        """
        if self.suma_percepciones == 0:
            return Decimal("0.00")

        salario_integral = self.salario_diario_integral

        tasas = AportacionObreroPatronales.objects.filter(
            concepto__iexact="guarderias y prestaciones sociales"
        ).first()

        if not tasas:
            raise ValueError("No se encontraron tasas para GPS.")

        trabajador_tasa = Decimal(tasas.trabajador)
        gps_obrero = salario_integral * trabajador_tasa * 7

        return round(gps_obrero, 2)
    
    def calcular_en_dinero_obrero(self):
        """
        Calcula en dinero
        """
        if self.suma_percepciones == 0:
            return Decimal("0.00")

        salario_integral = self.salario_diario_integral

        tasas = AportacionObreroPatronales.objects.filter(
            concepto__iexact="en dinero"
        ).first()

        if not tasas:
            raise ValueError("No se encontraron tasas para GMP.")

        trabajador_tasa = Decimal(tasas.trabajador)
        en_dinero = salario_integral * trabajador_tasa * 7

        return round(en_dinero, 2)

    def calcular_imss_obrero(self):
        """
        Calcula el total del IMSS Obrero sumando los valores de todos los conceptos individuales.
        """
        # Si no hay percepciones, devolver 0
        if self.suma_percepciones == 0:
            return Decimal("0.00")

        # Cálculo de cada concepto individual
        cuota_fija = self.calcular_cuota_fija()
        excedente_obrero = self.calcular_excedente_obrero()
        gmp_obrero = self.calcular_gmp_obrero()
        rt_obrero = self.calcular_rt_obrero()
        iv_obrero = self.calcular_iv_obrero()
        gps_obrero = self.calcular_gps_obrero()
        en_dinero_obrero = self.calcular_en_dinero_obrero()

        # Sumar todos los conceptos
        imss_obrero_total = (
            cuota_fija
            + excedente_obrero
            + gmp_obrero
            + rt_obrero
            + iv_obrero
            + gps_obrero
            + en_dinero_obrero
        )

        return round(imss_obrero_total, 2)

    def calcular_cuota_fija_patronal(self):
        """
        Calcula la cuota fija para el IMSS Patronal.
        """
        if self.suma_percepciones == 0:
            return Decimal("0.00")

        salario_minimo_entry = SalarioMinimo.objects.last()
        if not salario_minimo_entry:
            raise ValueError("El registro de salario mínimo no está configurado.")

        uma_diaria = Decimal(salario_minimo_entry.uma)
        dias_trabajados = self.dias_trabajados

        tasas = AportacionObreroPatronales.objects.filter(
            concepto__iexact="cuota fija por cada empleado hasta por tres veces la UMA"
        ).first()

        if not tasas:
            raise ValueError("No se encontraron tasas para la cuota fija patronal.")

        patron_tasa = Decimal(tasas.patron)
        cuota_fija_patronal = uma_diaria * 7 * patron_tasa

        return round(cuota_fija_patronal, 2)

    def calcular_excedente_patronal(self):
        """
        Calcula el excedente del salario base de cotización (SBC) por encima de 3 veces la UMA para el IMSS Patronal.
        """
        if self.suma_percepciones == 0:
            return Decimal("0.00")

        salario_minimo_entry = SalarioMinimo.objects.last()
        if not salario_minimo_entry:
            raise ValueError("El registro de salario mínimo no está configurado.")

        uma_diaria = Decimal(salario_minimo_entry.uma)
        salario_integral = self.salario_diario_integral

        diferencia_sbc = max(salario_integral - (3 * uma_diaria), 0)

        tasas = AportacionObreroPatronales.objects.filter(
            concepto__iexact="cuota adicional por la diferencia del sbc y de 3 veces la uma"
        ).first()

        if not tasas:
            raise ValueError("No se encontraron tasas para el excedente patronal.")

        patron_tasa = Decimal(tasas.patron)
        excedente_patronal = diferencia_sbc * patron_tasa * 7

        return round(excedente_patronal, 2)

    def calcular_gmp_patronal(self):
        """
        Calcula los gastos médicos para pensionados y beneficiarios (GMP) del IMSS Patronal.
        """
        if self.suma_percepciones == 0:
            return Decimal("0.00")

        salario_integral = self.salario_diario_integral

        tasas = AportacionObreroPatronales.objects.filter(
            concepto__iexact="gastos medicos para pensionados y beneficiarios"
        ).first()

        if not tasas:
            raise ValueError("No se encontraron tasas para GMP Patronal.")

        patron_tasa = Decimal(tasas.patron)
        gmp_patronal = salario_integral * patron_tasa * 7

        return round(gmp_patronal, 2)

    def calcular_rt_patronal(self):
        """
        Calcula los riesgos de trabajo (RT) del IMSS Patronal.
        """
        if self.suma_percepciones == 0:
            return Decimal("0.00")

        salario_integral = self.salario_diario_integral

        tasas = AportacionObreroPatronales.objects.filter(
            concepto__iexact="riesgos de trabajo"
        ).first()

        if not tasas:
            raise ValueError("No se encontraron tasas para RT Patronal.")

        patron_tasa = Decimal(tasas.patron)
        rt_patronal = salario_integral * patron_tasa * 7

        return round(rt_patronal, 2)

    def calcular_iv_patronal(self):
        """
        Calcula la invalidez y vida (IV) del IMSS Patronal.
        """
        if self.suma_percepciones == 0:
            return Decimal("0.00")

        salario_integral = self.salario_diario_integral

        tasas = AportacionObreroPatronales.objects.filter(
            concepto__iexact="invalidez y vida"
        ).first()

        if not tasas:
            raise ValueError("No se encontraron tasas para IV Patronal.")

        patron_tasa = Decimal(tasas.patron)
        iv_patronal = salario_integral * patron_tasa * 7

        return round(iv_patronal, 2)

    def calcular_gps_patronal(self):
        """
        Calcula las guarderías y prestaciones sociales (GPS) del IMSS Patronal.
        """
        if self.suma_percepciones == 0:
            return Decimal("0.00")

        salario_integral = self.salario_diario_integral

        tasas = AportacionObreroPatronales.objects.filter(
            concepto__iexact="guarderias y prestaciones sociales"
        ).first()

        if not tasas:
            raise ValueError("No se encontraron tasas para GPS Patronal.")

        patron_tasa = Decimal(tasas.patron)
        gps_patronal = salario_integral * patron_tasa * 7

        return round(gps_patronal, 2)

    def calcular_en_dinero_patron(self):
        """
        Calcula en dinero
        """
        if self.suma_percepciones == 0:
            return Decimal("0.00")

        salario_integral = self.salario_diario_integral

        tasas = AportacionObreroPatronales.objects.filter(
            concepto__iexact="en dinero"
        ).first()

        if not tasas:
            raise ValueError("No se encontraron tasas para GMP.")

        patron_tasa = Decimal(tasas.patron)
        en_dinero = salario_integral * patron_tasa * 7

        return round(en_dinero, 2)
    
    def calcular_imss_patronal(self):
        """
        Calcula el total de IMSS Patronal sumando todos los conceptos.
        """
        total_imss_patronal = (
            self.calcular_cuota_fija_patronal()
            + self.calcular_excedente_patronal()
            + self.calcular_gmp_patronal()
            + self.calcular_rt_patronal()
            + self.calcular_iv_patronal()
            + self.calcular_gps_patronal()
            + self.calcular_en_dinero_patron()
        )
        return round(total_imss_patronal, 2)


    def calcular_infonavit_patronal(self):
        """
        Calcula el Infonavit Patronal basado en la tabla de aportaciones y los días trabajados.
        """
        salario_integral = self.salario_diario_integral
        dias_trabajados = self.dias_trabajados

        aportacion_infonavit_entry = AportacionPatronalesIMSS.objects.filter(concepto__icontains="infonavit").first()
        tasa_infonavit_patronal = Decimal(aportacion_infonavit_entry.patron) if aportacion_infonavit_entry else Decimal(0.0)

        # Calcular la fórmula
        infonavit_patronal = (salario_integral * tasa_infonavit_patronal) * Decimal(dias_trabajados + 2)
        return round(infonavit_patronal, 2)


    def calcular_deduccion_infonavit(self):
        """
        Obtiene la deducción de INFONAVIT desde el campo del empleado relacionado.
        """
        return self.empleado.monto_retencion_infonavit

    def calcular_aportacion_retiro_imss(self):
        """
        Calcula la aportación de retiro IMSS.
        Fórmula: (L15 * 'Tabla ISR'!$E$58) * (M15 + 2)
        """
        salario_integral = self.salario_diario_integral
        dias_trabajados = self.dias_trabajados

        # Obtener la tasa de retiro desde la tabla de aportaciones
        aportacion_retiro_entry = AportacionRetiroIMSS.objects.filter(concepto__icontains="retiro").first()
        tasa_retiro_patronal = Decimal(aportacion_retiro_entry.patron) if aportacion_retiro_entry else Decimal(0.0)

        # Aplicar la fórmula
        aportacion_retiro = (salario_integral * tasa_retiro_patronal) * Decimal(dias_trabajados + 2)
        return round(aportacion_retiro, 2)
    

    def calcular_ceav_imss(self):
        """
        Calcula la CEAV IMSS.
        Fórmula: (L15 * 'Tabla ISR'!$F$64) * (M15 + 2)
        """
        salario_integral = self.salario_diario_integral
        dias_trabajados = self.dias_trabajados

        # Obtener la tasa CEAV desde la tabla `CeavIMSS`
        ceav_imss_entry = CeavIMSS.objects.filter(concepto__icontains="ceav").first()
        tasa_ceav_trabajador = Decimal(ceav_imss_entry.trabajador) if ceav_imss_entry else Decimal(0.0)

        # Aplicar la fórmula
        ceav = (salario_integral * tasa_ceav_trabajador) * Decimal(dias_trabajados + 2)
        return round(ceav, 2)

    def calcular_ceav_patronal(self):
        """
        Calcula el CEAV Patronal basado en la fórmula proporcionada.
        """

        # Validar si hay percepciones o salario diario integral
        if self.suma_percepciones == 0 or not self.salario_diario_integral:
            return Decimal("0.00")

        # Salario diario, salario integral y días trabajados
        salario_diario = Decimal(self.empleado.salario_diario)
        salario_integral = Decimal(self.salario_diario_integral)
        dias_trabajados = Decimal(self.dias_trabajados)

        # Obtener UMA diaria y salario mínimo
        salario_minimo_entry = SalarioMinimo.objects.last()
        if not salario_minimo_entry:
            raise ValueError("El registro de salario mínimo y UMA no está configurado.")

        uma_diaria = Decimal(salario_minimo_entry.uma)
        salario_minimo = Decimal(salario_minimo_entry.salario_minimo)

        # Relación entre salario diario y UMA diaria
        relacion_salario_uma = salario_diario / uma_diaria

        # Obtener el rango correspondiente desde la tabla CEAV Patronal
        ceav_entry = CeavPatronal.objects.filter(
            limite_inferior__lte=relacion_salario_uma,
            limite_superior__gte=relacion_salario_uma
        ).first()

        # Evaluar el último rango si no se encuentra el rango exacto
        if not ceav_entry:
            ceav_entry = CeavPatronal.objects.filter(
                limite_inferior__lte=relacion_salario_uma
            ).order_by('-limite_inferior').first()

        # Si no se encuentra ningún rango, retornar 0
        if not ceav_entry:
            return Decimal("0.00")

        # Obtener el porcentaje correspondiente del rango
        porcentaje_ceav = Decimal(ceav_entry.porcentaje)

        # Calcular CEAV Patronal: porcentaje aplicado al salario integral
        ceav_patronal = (salario_integral * porcentaje_ceav) * (dias_trabajados + 2)

        return round(ceav_patronal, 2)

    def calcular_semana_nomina(self):
        """
        Calcula la semana del año basada en la fecha de la nómina.
        """
        if not self.fecha_nomina:
            return None
        return self.fecha_nomina.isocalendar()[1]
    
    def save(self, *args, **kwargs):
        self.salario_diario_integral = self.calcular_salario_diario_integral()
        self.bruto_semanal = self.calcular_bruto_semanal()
        self.suma_percepciones = self.calcular_suma_percepciones()
        self.impuestos_isr = self.calcular_isr()
        self.imss_obrero = self.calcular_imss_obrero()
        self.cuota_fija = self.calcular_cuota_fija()
        self.excedente_obrero = self.calcular_excedente_obrero()
        self.gmp_obrero = self.calcular_gmp_obrero()
        self.rt_obrero = self.calcular_rt_obrero()
        self.iv_obrero = self.calcular_iv_obrero()
        self.gps_obrero = self.calcular_gps_obrero()
        self.en_dinero_obrero = self.calcular_en_dinero_obrero()
        self.imss_patronal = self.calcular_imss_patronal()
        self.cuota_fija_patronal = self.calcular_cuota_fija_patronal()
        self.excedente_patronal = self.calcular_excedente_patronal()
        self.gmp_patronal = self.calcular_gmp_patronal()
        self.rt_patronal = self.calcular_rt_patronal()
        self.iv_patronal = self.calcular_iv_patronal()
        self.gps_patronal = self.calcular_gps_patronal()
        self.en_dinero_patronal = self.calcular_en_dinero_patron()
        self.infonavit_patronal = self.calcular_infonavit_patronal()
        self.deduccion_infonavit = self.calcular_deduccion_infonavit() 
        self.aportacion_retiro_imss = self.calcular_aportacion_retiro_imss()
        self.ceav_obrero = self.calcular_ceav_imss()
        self.ceav_patronal = self.calcular_ceav_patronal() 
        self.suma_deducciones = self.calcular_suma_deducciones()
        self.nomina_a_depositar = self.calcular_nomina_a_depositar()
        self.total_impuestos = self.calcular_total_impuestos()  
        self.nomina_semanal_fiscal = self.calcular_nomina_semanal_fiscal()  
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Nómina de {self.empleado.nombre_completo} - {self.fecha_nomina} (Semana {self.calcular_semana_nomina()})"

class ComprobantePagoNomina(models.Model):
    TIPO_PAGO_CHOICES = [
        ('Transferencia', 'Transferencia'),
        ('Efectivo', 'Efectivo'),
        ('Cheque', 'Cheque'),
        ('Terceros', 'Tercero'),
    ]

    nomina = models.ForeignKey('Nomina',on_delete=models.CASCADE,related_name='comprobantes_pago')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateField()
    referencia = models.CharField(max_length=255, blank=True, null=True)
    pdf = models.FileField(upload_to='comprobantes_pago/', blank=True, null=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    ##Campos que me importan para el abono muejejeje
    tipo_pago = models.CharField(max_length=20, choices=TIPO_PAGO_CHOICES)
    numero_tarjeta = models.CharField(max_length=30, null=True, blank=True)
    tipo_tarjeta = models.CharField(max_length=30, choices=TIPO_PAGO_CHOICES, null=True, blank=True)
    numero_cuenta = models.CharField(max_length=30, null=True, blank=True)
    

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        # Verificar saldo ANTES de guardar
        if is_new and self.tipo_pago in ['Transferencia', 'Cheque']:
            if not self.numero_cuenta:
                raise ValueError("Se requiere un número de cuenta válido para procesar un abono por transferencia o cheque.")

            try:
                cuenta_bancaria = BancoModelo.objects.get(id=self.numero_cuenta)
            except BancoModelo.DoesNotExist:
                raise ValueError(f"No se encontró una cuenta bancaria con el ID {self.numero_cuenta}.")

            if cuenta_bancaria.saldo < self.monto:
                raise ValueError(
                    f"La cuenta bancaria no tiene saldo suficiente. "
                    f"Saldo actual: ${cuenta_bancaria.saldo}, "
                    f"Monto requerido: ${self.monto}"
                )

        # Ahora sí guarda
        super().save(*args, **kwargs)

        # Solo si es nuevo y hay saldo, genera el movimiento
        if is_new and self.tipo_pago in ['Transferencia', 'Cheque']:
            cuenta_bancaria = BancoModelo.objects.get(id=self.numero_cuenta)
            nombre_completo_empleado = self.nomina.empleado.nombre_completo

            AbonoBanco.objects.create(
                numero_cuenta=cuenta_bancaria,
                monto_movimiento=self.monto,
                tipo_movimiento='egreso',
                fecha_movimiento=self.fecha_pago,
                referencia=self.referencia,
                pdf_comprobante=self.pdf,
                comentarios='Egreso de Nómina',
                proveedor=nombre_completo_empleado,
                entrada_salida='salida',
            )

    def __str__(self):
        return f"Comprobante {self.tipo_pago} - Nómina: {self.nomina.id} - Monto: {self.monto}"

@receiver(post_save, sender=ComprobantePagoNomina)
def crear_nomina_siguiente(sender, instance, created, **kwargs):
    """
    Crea automáticamente una nueva nómina para la semana siguiente 
    cuando se realiza el pago de una nómina y el estado cambia a "pagada".
    """
    if created:  # Solo al crear un nuevo comprobante de pago
        nomina = instance.nomina
        if nomina.estatus == 'pagada':  # Verifica si la nómina está en estado "pagada"
            # Calcula la fecha de la siguiente nómina (una semana después de la actual)
            fecha_siguiente_nomina = nomina.fecha_nomina + timedelta(weeks=1)
            
            # Crea la nueva nómina con los valores iniciales
            Nomina.objects.create(
                empleado=nomina.empleado,
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
                imss_patronal=Decimal('0.0'),
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
                fecha_nomina=fecha_siguiente_nomina,
            )

class NominaResidentesPracticantes(models.Model):
    ESTATUS_CHOICES = [
        ('inicial', 'Inicial'),
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('programada', 'Programada'),
    ]

    practicante_residente = models.ForeignKey(
        'ri_rh.PracticanteResidente',
        on_delete=models.CASCADE,
        related_name='nominas_residentes_practicantes'
    )
    estatus = models.CharField(max_length=20, choices=ESTATUS_CHOICES, default='pendiente')
    dias_trabajados = models.IntegerField(default=0)
    horas_retardos= models.IntegerField(default=0)
    fecha_nomina = models.DateField(default=timezone.now)
    semana_nomina = models.PositiveIntegerField(editable=False)  # Semana calculada automáticamente
    monto_aprobado = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # Entrada de pago 
    apoyo_economico = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # Guardado en la base de datos
    observaciones = models.TextField(blank=True, null=True)

    def calcular_apoyo_economico(self):
        """
        Calcula el apoyo económico basado en el salario diario del practicante/residente.
        """
        return self.practicante_residente.salario_diario

    def calcular_semana_nomina(self):
        """
        Calcula la semana del año basada en la fecha de la nómina.
        """
        if not self.fecha_nomina:
            return None
        return self.fecha_nomina.isocalendar()[1]

    def save(self, *args, **kwargs):
        # Calcula el apoyo económico y la semana antes de guardar
        self.apoyo_economico = self.calcular_apoyo_economico()
        self.semana_nomina = self.calcular_semana_nomina()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Nómina de {self.practicante_residente.nombre_completo} - {self.fecha_nomina} (Semana {self.semana_nomina})"

class ComprobantePagoResidentePracticante(models.Model):
    TIPO_PAGO_CHOICES = [
        ('Transferencia', 'Transferencia'),
        ('Efectivo', 'Efectivo'),
        ('Cheque', 'Cheque'),
        ('Tercero', 'Tercero'),
    ]

    nomina = models.ForeignKey(
        'NominaResidentesPracticantes', 
        on_delete=models.CASCADE, 
        related_name='comprobantes_pago'
    )
    tipo_pago = models.CharField(
        max_length=20, 
        choices=TIPO_PAGO_CHOICES
    )
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateField()
    referencia = models.CharField(max_length=255, blank=True, null=True)
    pdf = models.FileField(upload_to='comprobantes_pago_residentes_practicantes/', blank=True, null=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    numero_cuenta = models.CharField(max_length=30, null=True, blank=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if self.monto != self.nomina.monto_aprobado:
            raise ValueError("El monto del comprobante no coincide con el monto aprobado de la nómina.")

        if is_new and self.tipo_pago in ['Transferencia', 'Cheque']:
            if not self.numero_cuenta:
                raise ValueError("Se requiere un número de cuenta para procesar el abono.")

            try:
                cuenta_bancaria = BancoModelo.objects.get(id=self.numero_cuenta)
            except BancoModelo.DoesNotExist:
                raise ValueError(f"No se encontró una cuenta bancaria con el ID {self.numero_cuenta}.")

            if cuenta_bancaria.saldo < self.monto:
                raise ValueError(
                    f"Saldo insuficiente en la cuenta bancaria. "
                    f"Disponible: ${cuenta_bancaria.saldo}, Requerido: ${self.monto}"
                )

        # Si pasa las validaciones, ahora sí guarda
        super().save(*args, **kwargs)

        if is_new and self.tipo_pago in ['Transferencia', 'Cheque']:
            cuenta_bancaria = BancoModelo.objects.get(id=self.numero_cuenta)
            nombre_empleado = self.nomina.practicante_residente.nombre_completo

            AbonoBanco.objects.create(
                numero_cuenta=cuenta_bancaria,
                monto_movimiento=self.monto,
                tipo_movimiento='egreso',
                fecha_movimiento=self.fecha_pago,
                referencia=self.referencia,
                pdf_comprobante=self.pdf,
                comentarios='Egreso de Nómina PR',
                proveedor=nombre_empleado,
                entrada_salida='salida',
            )

    def __str__(self):
        return f"Comprobante {self.tipo_pago} - Nómina: {self.nomina.id} - Monto: {self.monto}"

@receiver(post_save, sender=ComprobantePagoResidentePracticante)
def crear_nomina_siguiente_practicante_residente(sender, instance, created, **kwargs):
    """
    Crea automáticamente una nueva nómina para la semana siguiente
    cuando se realiza el pago de una nómina residente/practicante y el estado cambia a "pagado".
    """
    if created:  # Solo al crear un nuevo comprobante de pago
        nomina_residente = instance.nomina  # NominaResidentesPracticantes asociada
        if nomina_residente.estatus == 'pagado':  # Verifica si el estatus es "pagado"
            # Calcula la fecha de la siguiente nómina (una semana después de la fecha de pago)
            fecha_siguiente_nomina = instance.fecha_pago + timedelta(weeks=1)

            # Crea la nueva nómina con valores iniciales
            NominaResidentesPracticantes.objects.create(
                practicante_residente=nomina_residente.practicante_residente,
                estatus='inicial',
                fecha_nomina=fecha_siguiente_nomina,
                monto_aprobado=Decimal('0.0'),
                apoyo_economico=nomina_residente.practicante_residente.salario_diario,  # Calcula el apoyo económico
                observaciones=" ",
            )
            
class CuentaPorPagarProveedor(models.Model):
    ESTATUS_CHOICES = [
        ('inicial', 'Inicial'),
        ('pendiente', 'Pendiente'),
        ('programado', 'Programado'),
        ('pagado', 'Pagado'),
        ('vencido', 'Vencido'),
    ]

    orden = models.ForeignKey('ri_compras.OrdenDeCompra', on_delete=models.CASCADE, related_name='cuentas_por_pagar')
    fecha_cfdi = models.DateField(null=True, blank=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True)
    proyecto = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    departamento = models.ForeignKey(Departamento, on_delete=models.SET_NULL, null=True, blank=True)
    folio_factura = models.CharField(max_length=255, null=True, blank=True)
    dias_de_credito = models.IntegerField(default=0)
    fecha_contrarecibo = models.DateField(null=True, blank=True)
    fecha_pago = models.DateField(null=True, blank=True)
    total_factura = models.DecimalField(max_digits=30, decimal_places=6, default=Decimal('0.00'))
    divisa = models.CharField(max_length=20, default='MXN')
    estatus = models.CharField(max_length=20, choices=ESTATUS_CHOICES, default='inicial')
    saldo_pendiente = models.DecimalField(max_digits=30, decimal_places=6, default=Decimal('0.00'))
    propuesta_pago = models.DecimalField(max_digits=30, decimal_places=6, default=Decimal('0.00'))
    factura_pdf = models.FileField(upload_to='facturas_proveedores/', null=True, blank=True)
    pago_a_contado = models.BooleanField(default=False)

    def calcular_fecha_pago(self):
        """
        Calcula la fecha de pago como la fecha de contrarecibo + días de crédito,
        luego ajusta al siguiente viernes.
        """
        if self.fecha_contrarecibo and self.dias_de_credito:
            fecha_inicial = self.fecha_contrarecibo + timedelta(days=self.dias_de_credito)
            # Ajustar al siguiente viernes
            # Si fecha_inicial ya es viernes, queda igual. De lo contrario, se mueve al siguiente viernes.
            # Lunes=0, Martes=1, ... Domingo=6, Viernes=4
            weekday = fecha_inicial.weekday()
            if weekday < 4: 
                # sumar (4 - weekday) días
                diferencia = 4 - weekday
                fecha_pago = fecha_inicial + timedelta(days=diferencia)
            elif weekday > 4:
                # si es sabado(5) o domingo(6), mover al siguiente viernes (sumar dias hasta el proximo viernes)
                # por ejemplo, si es sabado(5), faltan 6 dias para el siguiente viernes (5->4 en la prox semana)
                diferencia = (11 - weekday)  # 11 - 5 = 6 días si es sábado, 11 - 6 = 5 si es domingo
                fecha_pago = fecha_inicial + timedelta(days=diferencia)
            else:
                # Ya es viernes
                fecha_pago = fecha_inicial
            return fecha_pago
        return None

    def save(self, *args, **kwargs):
        if not self.fecha_pago and self.fecha_contrarecibo and self.dias_de_credito:
            self.fecha_pago = self.calcular_fecha_pago()
        
        # Por defecto el saldo pendiente es igual al total_factura al crear el registro
        if self.pk is None:
            self.saldo_pendiente = self.total_factura

        super().save(*args, **kwargs)



class AbonoProveedor(models.Model):
    TIPO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
        ('cheque', 'Cheque'),
        ('terceros', 'Terceros'),
    ]

    TIPO_TARJETA = [
        ('credito', 'Credito'),
        ('debito', 'Debito'),
    ]

    cuenta = models.ForeignKey(CuentaPorPagarProveedor, on_delete=models.CASCADE, related_name='abonos')
    cantidad_abono = models.DecimalField(max_digits=30, decimal_places=6, default=Decimal('0.00'))
    fecha_pago = models.DateField(null=True, blank=True)
    tipo_de_pago = models.CharField(max_length=20, choices=TIPO_PAGO_CHOICES, default='efectivo')
    referencia_transferencia = models.CharField(max_length=255, null=True, blank=True)
    pdf = models.FileField(upload_to='abonos_proveedores/', null=True, blank=True)
    numero_tarjeta = models.CharField(max_length=30, null=True, blank=True)
    tipo_de_pago = models.CharField(max_length=30, choices=TIPO_PAGO_CHOICES, default='efectivo')
    tipo_tarjeta = models.CharField(max_length=30, choices=TIPO_TARJETA, null=True, blank=True)
    numero_cuenta = models.CharField(max_length=30, null=True, blank=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        if is_new:
            # Obtener el proveedor del OtroGasto relacionado
            proveedor = getattr(self.cuenta.proveedor, 'nombre', 'Proveedor no especificado') or "Proveedor no especificado"

            # Caso 1: Tipo de pago es tarjeta
            if self.tipo_de_pago == 'tarjeta':
                if not self.numero_tarjeta:
                    raise ValueError("El número de tarjeta es obligatorio para pagos con tarjeta.")
                
                try:
                    tarjeta = TarjetaCredito.objects.get(numero_tarjeta=self.numero_tarjeta)
                except TarjetaCredito.DoesNotExist:
                    raise ValueError(f"No se encontró una tarjeta de crédito asociada al número {self.numero_tarjeta}")

                if self.tipo_tarjeta == 'credito':
                    pago_mensual_actual = tarjeta.pagos_mensuales.filter(actual=True).first()
                    if not pago_mensual_actual:
                        raise ValueError("No se encontró un PagoMensualTarjeta marcado como actual para la tarjeta.")

                    # Crear MovimientoTarjeta
                    MovimientoTarjeta.objects.create(
                        tarjeta=tarjeta,
                        monto=self.cantidad_abono,
                        concepto=self.referencia_transferencia,
                        fecha=self.fecha_pago,
                        origen='Proveedores',
                        pago_mensual=pago_mensual_actual,
                    )

                    # Actualizar saldo pendiente en el pago mensual
                    pago_mensual_actual.saldo_pendiente += self.cantidad_abono
                    pago_mensual_actual.save()

                elif self.tipo_tarjeta == 'debito':
                    # Buscar la cuenta bancaria asociada al número de tarjeta
                    try:
                        cuenta_bancaria = BancoModelo.objects.get(numero_tarjeta=self.numero_tarjeta)
                    except BancoModelo.DoesNotExist:
                        raise ValueError(f"No se encontró una cuenta bancaria asociada al número de tarjeta {self.numero_tarjeta}")
                    
                    # Verificar saldo disponible antes de crear AbonoBanco
                    if cuenta_bancaria.saldo < self.cantidad_abono:
                        raise ValueError(f"Saldo insuficiente en la cuenta bancaria asociada a la tarjeta débito ({cuenta_bancaria.numero_cuenta}).")
                    # Crear AbonoBanco
                    AbonoBanco.objects.create(
                        numero_cuenta=cuenta_bancaria,
                        monto_movimiento=self.cantidad_abono,
                        tipo_movimiento='egreso',
                        fecha_movimiento=self.fecha_pago,
                        referencia=self.referencia_transferencia,
                        pdf_comprobante=self.pdf,
                        comentarios='Gasto desde proveedores',
                        proveedor=proveedor,
                        entrada_salida='salida',
                    )

            # Caso 2: Tipo de pago es transferencia o cheque
            elif self.tipo_de_pago in ['transferencia', 'cheque']:
                if not self.numero_cuenta:
                    raise ValueError("Se requiere un número de cuenta válido para procesar un abono por transferencia o cheque.")

                try:
                    # Si el número de cuenta es un ID, obtener la instancia directamente
                    if self.numero_cuenta.isdigit():
                        cuenta_bancaria = BancoModelo.objects.get(id=int(self.numero_cuenta))
                    else:
                        cuenta_bancaria = BancoModelo.objects.get(numero_cuenta=self.numero_cuenta)
                except BancoModelo.DoesNotExist:
                    raise ValueError(f"No se encontró una cuenta bancaria con el número o ID {self.numero_cuenta}.")

                # Verificar saldo disponible antes de crear AbonoBanco
                if cuenta_bancaria.saldo < self.cantidad_abono:
                    raise ValueError(f"Saldo insuficiente en la cuenta bancaria {cuenta_bancaria.numero_cuenta}.")
                # Crear AbonoBanco usando la instancia de BancoModelo
                AbonoBanco.objects.create(
                    numero_cuenta=cuenta_bancaria,
                    monto_movimiento=self.cantidad_abono,
                    tipo_movimiento='egreso',
                    fecha_movimiento=self.fecha_pago,
                    referencia=self.referencia_transferencia,
                    pdf_comprobante=self.pdf,
                    comentarios='Gasto desde proveedores',
                    proveedor=proveedor,
                    entrada_salida='salida',
                )

            #Caso 3: Pago por terceros crear OtroGasto
            if self.tipo_de_pago == 'terceros':
                OtroGasto.objects.create(
                    tipo_gasto=TipoOtroGasto.objects.get(nombre='terceros'),  
                    proveedor=self.cuenta.proveedor.nombre,
                    descripcion='Abono de Proveedores como terceros',
                    divisa=f'{self.cuenta.divisa}',
                    tipo_pago='terceros',
                    monto_total=self.cantidad_abono,
                    fecha_gasto=self.fecha_pago,
                    ticket_factura=self.pdf,
                    estatus='inicial',
                )

            # Actualizar el saldo pendiente y estado del periodo
            self.cuenta.saldo_pendiente -= self.cantidad_abono
            if self.cuenta.saldo_pendiente <= 0:
                self.cuenta.estatus = 'pagado'
                self.cuenta.saldo_pendiente = Decimal('0.00')
            self.cuenta.save()
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Abono {self.tipo_de_pago} de {self.cantidad_abono} para el gasto {self.cuenta.id}"