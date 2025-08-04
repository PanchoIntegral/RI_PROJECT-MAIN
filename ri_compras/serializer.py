from decimal import Decimal
import logging
from rest_framework import serializers
from django.utils import timezone
from ri_rh.serializer import EmpleadoSerializer

from .models import AbonoTarjeta, AmortizacionCuota, AportacionObreroPatronales, AportacionPatronalesIMSS, AportacionRetiroIMSS, CeavIMSS, Contacto, CreditoPrestamo, CuentaBancaria, CuentaPorCobrar, DetalleCxC, Estante, Isr, MovimientoTarjeta, OtroGasto, PagoCreditoPrestamo, PagoMensualTarjeta, PagoOtroGasto, PagoPeriodoAbono, PagoPorPeriodo, Pedido, ProductoAlmacen, Rack, SalarioMinimo, ServiciosFactura, TarjetaCredito, TipoOtroGasto, Vacaciones, BancoModelo,MovimientoBanco,AbonoBanco
from .models import AbonoTarjeta, AbonoProveedor, AmortizacionCuota, AportacionObreroPatronales, AportacionPatronalesIMSS, AportacionRetiroIMSS, CeavIMSS, CeavPatronal, ComprobantePagoNomina, ComprobantePagoResidentePracticante, Contacto, CreditoPrestamo, CuentaBancaria, CuentaPorCobrar, CuentaPorPagarProveedor, DetalleCxC, Estante, Isr, MovimientoTarjeta, Nomina, NominaResidentesPracticantes, OtroGasto, PagoCreditoPrestamo, PagoMensualTarjeta, PagoOtroGasto, PagoPeriodoAbono, PagoPorPeriodo, Pedido, ProductoAlmacen, Rack, SalarioMinimo, ServiciosFactura, TarjetaCredito, TipoOtroGasto, Vacaciones
from .models import ServicioRequisicion
from .models import Departamento
from .models import Message
from .models import ProductoRequisicion
from .models import Usuarios
from .models import Producto
from .models import Servicio
from .models import Requisicion
from .models import Proveedor
from .models import OrdenDeCompra
from .models import Recibo
from .models import Project
from .models import Sum
from django.conf import settings
from django.utils.functional import LazyObject

class UsuarioDepartamentoSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Usuarios
        fields = ['id', 'nombre', 'telefono', 'correo'] 

class DepartamentoSerializer(serializers.ModelSerializer):
    lider = serializers.SerializerMethodField()

    class Meta:
        model = Departamento
        fields = ['id', 'nombre', 'descripcion', 'presupuesto', 'divisa', 'lider']

    def get_lider(self, obj):
        lider = Usuarios.objects.filter(departamento=obj, rol='LIDER').first()
        return UsuarioDepartamentoSerializer(lider).data if lider else None

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'

class ContactoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contacto
        fields = '__all__'

class SimpleUserProjectSerializer(serializers.ModelSerializer):
    departamento = DepartamentoSerializer()
    
    class Meta:
        model = Usuarios
        fields = ['id', 'username', 'nombre', 'telefono', 'correo', 'rol', 'departamento']

class SimpleProjectSerializer(serializers.ModelSerializer):
    usuario = SimpleUserProjectSerializer(read_only=True)
    
    class Meta:
        model = Project
        fields = ['id', 'nombre', 'descripcion', 'usuario', 'presupuesto','habilitado', 'divisa']

class SimpleProveedorSerializer(serializers.ModelSerializer):
    contactos = ContactoSerializer(many=True, read_only=True)
    
    class Meta:
        model = Proveedor
        fields = '__all__'

class SimpleServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = ['id', 'nombre', 'descripcion', 'costo', 'divisa']

class SimpleRequisicionSerializer(serializers.ModelSerializer):
    usuario = SimpleUserProjectSerializer()
    proyecto = SimpleProjectSerializer(read_only=True)
    proveedor = SimpleProveedorSerializer(read_only=True)
    productos = ProductoSerializer(many=True, read_only=True)
    servicios = SimpleServicioSerializer(many=True, read_only=True)
    fecha_creacion = serializers.SerializerMethodField()
    fecha_aprobado = serializers.SerializerMethodField()
    fecha_entrega_estimada = serializers.SerializerMethodField()

    class Meta:
        model = Requisicion
        fields = ['id', 'usuario', 'proyecto', 'proveedor', 'productos', 'servicios', 'fecha_creacion', 'fecha_aprobado', 'fecha_entrega_estimada', 'motivo', 'total', 'aprobado','ordenado', 'archivo_pdf', 'tipo_de_cambio']

    def get_fecha_creacion(self, obj):
        return timezone.localtime(obj.fecha_creacion)

    def get_fecha_aprobado(self, obj):
        return timezone.localtime(obj.fecha_aprobado)

    def get_fecha_entrega_estimada(self, obj):
        return timezone.localtime(obj.fecha_entrega_estimada)

class UserMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuarios
        fields = ['id', 'username', 'nombre', 'telefono', 'correo']

class MessageSerializer(serializers.ModelSerializer):
    user = UserMessageSerializer(read_only=True)
    from_user = UserMessageSerializer(read_only=True)

    class Meta:
        model = Message
        fields = '__all__'

    def create(self, validated_data):
        user_id = self.context['request'].data.get('user')
        from_user_id = self.context['request'].data.get('from_user')

        user = Usuarios.objects.get(id=user_id)
        from_user = Usuarios.objects.get(id=from_user_id)

        message = Message.objects.create(
            user=user,
            from_user=from_user,
            title=validated_data.get('title'),
            message=validated_data.get('message')
        )

        return message

class UsuariosSerializer(serializers.ModelSerializer):
    requisiciones = SimpleRequisicionSerializer(many=True, read_only=True)
    messages = MessageSerializer(many=True, read_only=True)
    departamento = DepartamentoSerializer(read_only=True)
    password = serializers.CharField(write_only=True)
    proyectos = SimpleProjectSerializer(many=True, read_only=True)

    class Meta:
        model = Usuarios
        fields = ['id', 'username', 'nombre', 'telefono', 'correo', 'rol', 'departamento', 'requisiciones', 'password', 'messages', 'proyectos']
        read_only_fields = ['requisiciones']

    def validate_departamento(self, value):
        if not value:
            raise serializers.ValidationError("El departamento es obligatorio")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Usuarios.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password is not None:
            user.set_password(password)
            user.save()
        return user

class RackSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Rack
        fields = '__all__'
        
class EstanteSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Estante
        fields = '__all__'

class ProductoRequisicionSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ProductoRequisicion
        fields = '__all__'

class PedidoSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Pedido
        fields = '__all__'

class ProductoAlmacenSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ProductoAlmacen
        fields = '__all__'

class UsuariosVerySimpleSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Usuarios
        fields = ['id', 'username', 'nombre', 'telefono', 'correo', 'rol']

class ProjectSerializer(serializers.ModelSerializer):
    usuario = UsuariosVerySimpleSerializer(read_only=True)
    
    class Meta:
        model = Project
        fields = '__all__'

class ServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = ['id', 'nombre', 'descripcion', 'costo', 'divisa']

class ProveedorSerializer(serializers.ModelSerializer):
    contactos = ContactoSerializer(many=True)

    class Meta:
        model = Proveedor
        fields = '__all__'

    def create(self, validated_data):
        contactos_data = validated_data.pop('contactos')
        proveedor = Proveedor.objects.create(**validated_data)
        for contacto_data in contactos_data:
            contacto = Contacto.objects.create(**contacto_data)
            proveedor.contactos.add(contacto)
        return proveedor

    def update(self, instance, validated_data):
        contactos_data = validated_data.pop('contactos')
        instance = super().update(instance, validated_data)

        for contacto_data in contactos_data:
            contacto_id = contacto_data.get('id', None)
            if contacto_id:
                # update existing contact
                Contacto.objects.filter(id=contacto_id).update(**contacto_data)
            else:
                # create new contact
                contacto = Contacto.objects.create(**contacto_data)
                instance.contactos.add(contacto)

        return instance

class SimpleUsuariosSerializer(serializers.ModelSerializer):
    departamento = DepartamentoSerializer(read_only=True)

    class Meta:
        model = Usuarios
        fields = ['id', 'username', 'nombre', 'telefono', 'correo', 'rol', 'departamento']

class SimpleOrdenDeCompraSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdenDeCompra
        fields = ['id', 'fecha_emision', 'estado']

    def get_fecha_emision(self, obj):
        return timezone.localtime(obj.fecha_emision)

class RequisicionSerializer(serializers.ModelSerializer):
    usuario = SimpleUserProjectSerializer(read_only=True)
    usuario_id = serializers.IntegerField(write_only=True)
    proyecto = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all(), allow_null=True)
    proveedor = serializers.PrimaryKeyRelatedField(queryset=Proveedor.objects.all())
    productos = ProductoRequisicionSerializer(many=True)
    servicios = ServicioSerializer(many=True)
    ordenes = serializers.SerializerMethodField()
    fecha_creacion = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z") # type: ignore
    fecha_aprobado = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z", allow_null=True) # type: ignore
    fecha_entrega_estimada = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z", allow_null=True) # type: ignore
    fecha_ordenado = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z", allow_null=True) # type: ignore

    class Meta:
        model = Requisicion
        fields = '__all__'
    
    def get_fecha_creacion(self, obj):
        return timezone.localtime(obj.fecha_creacion)

    def get_fecha_aprobado(self, obj):
        if obj.fecha_aprobado:
            return timezone.localtime(obj.fecha_aprobado)

    def get_fecha_entrega_estimada(self, obj):
        if obj.fecha_entrega_estimada:
            return timezone.localtime(obj.fecha_entrega_estimada)

    def get_fecha_ordenado(self, obj):
        if obj.fecha_ordenado:
            return timezone.localtime(obj.fecha_ordenado)

    def get_ordenes(self, obj):
        ordenes = OrdenDeCompra.objects.filter(requisicion=obj)
        return SimpleOrdenDeCompraSerializer(ordenes, many=True).data

    def create(self, validated_data):
        archivo_pdf = validated_data.pop('archivo_pdf', None)
        usuario_id = validated_data.pop('usuario_id')
        validated_data['usuario'] = Usuarios.objects.get(id=usuario_id)
        productos_data = validated_data.pop('productos', [])
        servicios_data = validated_data.pop('servicios', [])
        requisicion = Requisicion.objects.create(**validated_data)

        for producto_data in productos_data:
            producto_requisicion = ProductoRequisicion.objects.create(**producto_data)
            requisicion.productos.add(producto_requisicion)
            producto_requisicion.save()

        for servicio_data in servicios_data:
            servicio_requisicion = ServicioRequisicion.objects.create(**servicio_data)
            requisicion.servicios.add(servicio_requisicion)
            servicio_requisicion.save()

        if archivo_pdf is not None:
            requisicion.archivo_pdf = archivo_pdf

        requisicion.save()
        return requisicion

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['usuario'] = SimpleUserProjectSerializer(instance.usuario).data
        representation['proyecto'] = SimpleProjectSerializer(instance.proyecto).data
        representation['proveedor'] = ProveedorSerializer(instance.proveedor).data
        return representation
 
#Ordenes 
class OrdenDeCompraSerializer(serializers.ModelSerializer):
    # Campos para la lectura (GET)
    usuario_detail = SimpleUsuariosSerializer(source='usuario', read_only=True)
    proveedor_detail = ProveedorSerializer(source='proveedor', read_only=True)
    requisicion_detail = RequisicionSerializer(source='requisicion', read_only=True)

    # Campos para la escritura (POST)
    usuario = serializers.PrimaryKeyRelatedField(queryset=Usuarios.objects.all())
    proveedor = serializers.PrimaryKeyRelatedField(queryset=Proveedor.objects.all())
    requisicion = serializers.PrimaryKeyRelatedField(queryset=Requisicion.objects.all())
    fecha_entrega = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z", allow_null=True)  # type: ignore
    
    fecha_emision = serializers.SerializerMethodField()

    class Meta:
        model = OrdenDeCompra
        fields = '__all__'

    def get_fecha_emision(self, obj):
        return timezone.localtime(obj.fecha_emision)

    def get_fecha_entrega(self, obj):
        if obj.fecha_entrega:
            return timezone.localtime(obj.fecha_entrega)

class ReciboSerializer(serializers.ModelSerializer):
    orden = OrdenDeCompraSerializer(many=True)

    class Meta:
        model = Recibo
        fields = ['orden', 'estado', 'descripcion']
        
class DetalleCxCSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleCxC
        fields = '__all__'

class PropuestaCxCSerializer(serializers.ModelSerializer):
    detalles = DetalleCxCSerializer(many=True, read_only=True)

    class Meta:
        model = CuentaPorCobrar
        fields = [
            'id', 'razon_social', 'responsable', 'oc_po', 'pdf_oc_po', 'fecha_oc_po',
            'numero_proyecto_interno_ri', 'importe_total_oc_po_sin_iva',
            'importe_iva_total_oc_po', 'porcentaje_facturacion',
            'importe_total_facturado', 'iva_importe_facturado',
            'importe_total_facturado_con_iva', 'fecha_cfdi', 'tipo_cfdi',
            'folio_cfdi', 'pdf_cfdi', 'fecha_ideal_pago', 'fecha_programada_pago',
            'saldo', 'divisa', 'dias_vencidos', 'importe_pago',
            'estatus','nombre_factura', 'detalles', 'monto_total','xml_cancelacion'
        ]


class CuentaBancariaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CuentaBancaria
        fields = ['numero_cuenta', 'clave_interbancaria', 'banco']
        

class PagoPeriodoAbonoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PagoPeriodoAbono
        fields = '__all__'

class PagoPorPeriodoSerializer(serializers.ModelSerializer):
    abono = serializers.DecimalField(max_digits=15, decimal_places=2, required=False, write_only=True)

    class Meta:
        model = PagoPorPeriodo
        fields = '__all__'

    def validate_abono(self, value):
        if self.instance and value > self.instance.saldo_pendiente:
            raise serializers.ValidationError("El abono no puede ser mayor que el saldo pendiente.")
        return value

    def update(self, instance, validated_data):
        abono = validated_data.pop('abono', None)
        if abono is not None:
            instance.aplicar_abono(abono)
        # Actualizar otros campos si es necesario
        return super().update(instance, validated_data)
    
    def get_dias_vencidos(self, obj):
        return obj.dias_vencidos()

class ServicioFacturaSerializer(serializers.ModelSerializer):
    saldo = serializers.SerializerMethodField()
    dias_vencidos = serializers.SerializerMethodField()
    cuentas_bancarias = CuentaBancariaSerializer(many=True, read_only=True)
    pagos_por_periodo = PagoPorPeriodoSerializer(many=True, read_only=True)

    class Meta:
        model = ServiciosFactura
        fields = [
            'id', 'fecha_creacion', 'nombre_servicio', 'folio_servicio', 'total_a_pagar',
            'divisa', 'fecha_vencimiento', 'fecha_corte', 'periodicidad', 'estatus',
            'saldo', 'dias_vencidos', 'propuesta_pago', 'cuentas_bancarias',
            'pagos_por_periodo',
        ]

    def get_saldo(self, obj):
        total_saldo = obj.pagos_por_periodo.aggregate(total_saldo=Sum('saldo_pendiente'))['total_saldo']
        saldo_pendiente_total = total_saldo if total_saldo is not None else Decimal('0')
        return saldo_pendiente_total

    def get_dias_vencidos(self, obj):
        pagos_vencidos = obj.pagos_por_periodo.filter(
            estatus='vencido', saldo_pendiente__gt=0
        ).order_by('-fecha_vencimiento')
        if pagos_vencidos.exists():
            return (timezone.now().date() - pagos_vencidos.first().fecha_vencimiento).days
        return 0

#Serializer para el modelo AmortizacionCuota
class AmortizacionCuotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = AmortizacionCuota
        fields = ['id', 'credito_prestamo', 'numero_mes', 'pago', 'principal', 'interes', 'iva_interes', 'interes_moratorio', 'balance_restante', 'fecha_pago_programada', 'estatus_pago', 'propuesta_pago']

# Serializer para el modelo CreditoPrestamo
class CreditoPrestamoSerializer(serializers.ModelSerializer):
    intereses_insolutos = serializers.SerializerMethodField()
    saldo_a_liquidar = serializers.SerializerMethodField()
    capital_restante = serializers.SerializerMethodField()
    amortizaciones = AmortizacionCuotaSerializer(many=True, read_only=True)

    class Meta:
        model = CreditoPrestamo
        fields = [
            'id', 'emisor', 'receptor', 'tipo_transaccion', 'importe', 'numero_transaccion',
            'tasa_interes_normal', 'tasa_interes_moratorio', 'fecha_realizacion', 'fecha_vencimiento',
            'divisa', 'estatus', 'periodicidad', 'emitido_recibido', 'termino',
            'intereses_insolutos', 'saldo_a_liquidar', 'capital_restante', 'amortizaciones', 'numero_cuenta',
            'descripcion','comprobantepdf'
        ]

    def get_crear_abono(self, obj):
        return obj.crear_abono()

    def get_intereses_insolutos(self, obj):
        return obj.calcular_intereses_insolutos()

    def get_saldo_a_liquidar(self, obj):
        return obj.calcular_saldo_a_liquidar()

    def get_capital_restante(self, obj):
        return obj.calcular_capital_restante()



# Serializer para PagoCreditoPrestamo
class PagoCreditoPrestamoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PagoCreditoPrestamo
        fields = [
            'id', 'amortizacion_cuota', 'abono', 'fecha_pago', 'referencia_transferencia', 'pdf',
            'tipo_de_pago', 'numero_tarjeta', 'tipo_tarjeta', 'numero_cuenta', 
            
        ]


# Serializer para el modelo TipoOtroGasto
class TipoOtroGastoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoOtroGasto
        fields = ['id', 'nombre']


# Serializer para el modelo PagoOtroGasto
class PagoOtroGastoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PagoOtroGasto
        fields = '__all__' 

# Serializer para el modelo OtroGasto
class OtroGastoSerializer(serializers.ModelSerializer):
    saldo = serializers.SerializerMethodField()
    tipo_gasto = serializers.PrimaryKeyRelatedField(queryset=TipoOtroGasto.objects.all(), write_only=True)
    tipo_gasto_detalle = TipoOtroGastoSerializer(source='tipo_gasto', read_only=True)
    tipo_pago = serializers.ChoiceField(choices=OtroGasto.TIPO_PAGO_CHOICES)
    tipo_tarjeta = serializers.ChoiceField(choices=OtroGasto.TIPO_TARJETA, required=False)  # Campo para tipo de tarjeta
    tarjeta = serializers.PrimaryKeyRelatedField(queryset=TarjetaCredito.objects.all(), required=False)  # Selección de tarjeta
    tarjeta_detalle = serializers.SerializerMethodField()  # Para mostrar detalles de la tarjeta
    
    abonos = PagoOtroGastoSerializer(many=True, read_only=True)  # Para mostrar los abonos en los detalles del gasto

    class Meta:
        model = OtroGasto
        fields = [
            'id', 'fecha', 'proveedor', 'descripcion', 'tipo_gasto', 'tipo_gasto_detalle',
            'monto_total', 'divisa', 'estatus', 'ticket_factura', 'fecha_aprobacion',
            'fecha_pago', 'saldo', 'fecha_gasto', 'tipo_pago', 'tipo_tarjeta', 'tarjeta', 
            'tarjeta_detalle', 'abonos','numero_cuenta'
        ]
        read_only_fields = ['id']
        
    def get_saldo(self, obj):
        return obj.calcular_saldo()

    def get_tarjeta_detalle(self, obj):
        """
        Retorna detalles de la tarjeta si está asociada al gasto.
        """
        if obj.tarjeta:
            return {
                'id': obj.tarjeta.id,
                'banco': obj.tarjeta.banco,
                'numero_tarjeta': obj.tarjeta.numero_tarjeta,
                'saldo': obj.tarjeta.saldo,
                'divisa': obj.tarjeta.divisa,
            }
        return None

# Serializer for the MovimientoTarjeta model to include transaction history
class MovimientoTarjetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoTarjeta
        fields = ['id', 'monto', 'concepto', 'fecha', 'tarjeta', 'origen']


# Updated Serializer for the TarjetaCredito model
class TarjetaCreditoSerializer(serializers.ModelSerializer):
    pagos_mensuales = serializers.SerializerMethodField()
    saldo_actual = serializers.DecimalField(max_digits=15, decimal_places=2, source='saldo')
    movimientos = serializers.SerializerMethodField()  # Historial de movimientos

    class Meta:
        model = TarjetaCredito
        fields = [
            'id', 'banco', 'numero_tarjeta', 'saldo', 'limite_credito', 'divisa',
            'tasa_interes', 'tasa_moratoria', 'fecha_pago', 'fecha_corte', 'estatus',
            'multa_por_morosidad', 'monto_multa_morosidad',
            'saldo_actual', 'pagos_mensuales', 'movimientos','fecha_creacion','propuesta_pago',
            'saldo_restante','pago_minimo','tipo_tarjeta','ultima_ejecucion', 'banco_asociado'
        ]

    def get_pagos_mensuales(self, obj):
        # Retorna los pagos mensuales programados
        pagos = obj.pagos_mensuales.all()
        return PagoMensualTarjetaSerializer(pagos, many=True).data

    def get_movimientos(self, obj):
        # Retorna el historial de movimientos de la tarjeta
        movimientos = obj.movimientos.all().order_by('-fecha')
        return MovimientoTarjetaSerializer(movimientos, many=True).data



# Updated Serializer for the PagoMensualTarjeta model
class PagoMensualTarjetaSerializer(serializers.ModelSerializer):
    tarjeta_id = serializers.PrimaryKeyRelatedField(source='tarjeta.id', read_only=True)
    tarjeta_numero = serializers.CharField(source='tarjeta.numero_tarjeta', read_only=True)

    class Meta:
        model = PagoMensualTarjeta
        fields = [
            'id', 'tarjeta_id', 'tarjeta_numero', 'mes', 'pago_minimo', 'interes','fecha_corte',
            'fecha_vencimiento', 'estatus', 'propuesta_pago', 'usado', 'actual','saldo_pendiente','archivado',
        ]

    def validate_pago_minimo(self, value):
        if value <= 0:
            raise serializers.ValidationError("El pago mÃ­nimo debe ser positivo.")
        return value


# Updated Serializer for the Abono model
class AbonoTarjetaSerializer(serializers.ModelSerializer):
    tarjeta_id = serializers.PrimaryKeyRelatedField(source='tarjeta.id', read_only=True)
    tarjeta_numero = serializers.CharField(source='tarjeta.numero_tarjeta', read_only=True)
    pago_mensual_id = serializers.PrimaryKeyRelatedField(source='pago_mensual.id', read_only=True)
    pago_mensual_mes = serializers.IntegerField(source='pago_mensual.mes', read_only=True)
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = AbonoTarjeta
        fields = [
            'id', 'tarjeta_id', 'tarjeta_numero', 'pago_mensual_id', 'pago_mensual_mes',
            'fecha_abono', 'monto_abono', 'referencia_transferencia',
            'pdf_comprobante', 'pdf_url','tipo_de_pago','numero_cuenta','pago_mensual'
        ]

    def get_pdf_url(self, obj):
        # Devuelve la URL completa del PDF
        request = self.context.get('request')
        if obj.pdf_comprobante and request:
            return request.build_absolute_uri(obj.pdf_comprobante.url)
        return None
    
    def validate_tipo_pago(self, value):
        if value not in dict(AbonoTarjeta.TIPO_PAGO_CHOICES):
            raise serializers.ValidationError("Tipo de pago no válido.")
        return value

    def validate_monto_abono(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto del abono debe ser un valor positivo.")
        return value


# Serializer para ISR
class IsrSerializer(serializers.ModelSerializer):
    class Meta:
        model = Isr
        fields = [
            'id', 'limite_inferior', 'limite_superior', 'cuota_fija', 'porcentaje_excedente',
            'estatus','fecha_creacion', 'fecha_modificacion'
        ]


# Serializer para Vacaciones
class VacacionesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vacaciones
        fields = [
            'id', 'años', 'dias',
            'estatus','fecha_creacion', 'fecha_modificacion'
        ]


# Serializer para Aportaciones Obrero Patronales IMSS
class AportacionObreroPatronalesSerializer(serializers.ModelSerializer):
    class Meta:
        model = AportacionObreroPatronales
        fields = [
            'id', 'concepto', 'patron', 'trabajador',
            'estatus','fecha_creacion', 'fecha_modificacion'
        ]


# Serializer para Aportaciones Patronales IMSS
class AportacionPatronalesIMSSSerializer(serializers.ModelSerializer):
    class Meta:
        model = AportacionPatronalesIMSS
        fields = [
            'id', 'concepto', 'patron', 'trabajador',
            'estatus','fecha_creacion', 'fecha_modificacion'
        ]


# Serializer para Aportaciones Retiro IMSS
class AportacionRetiroIMSSSerializer(serializers.ModelSerializer):
    class Meta:
        model = AportacionRetiroIMSS
        fields = [
            'id', 'concepto', 'patron', 'trabajador',
            'estatus','fecha_creacion', 'fecha_modificacion'
        ]


# Serializer para CEAV IMSS
class CEAVIMSSSerializer(serializers.ModelSerializer):
    class Meta:
        model = CeavIMSS
        fields = [
            'id', 'concepto', 'patron', 'trabajador',
            'estatus','fecha_creacion', 'fecha_modificacion'
        ]


# Serializer para Salario Mínimo y UMA
class SalarioMinimoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalarioMinimo
        fields = [
            'id', 'salario_minimo', 'uma',
            'estatus','fecha_creacion', 'fecha_modificacion'
        ]
        
class BancoModeloSerializer(serializers.ModelSerializer):
    class Meta:
        model = BancoModelo
        fields = '__all__' 
        
        
class MovimientoBancoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoBanco
        fields = '__all__' 
        
class AbonoBancoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AbonoBanco
        fields = '__all__' 

# Serializer para CEAV Patronal
class CeavPatronalSerializer(serializers.ModelSerializer):
    class Meta:
        model = CeavPatronal
        fields = [
            'id', 'limite_inferior', 'limite_superior', 'porcentaje', 
            'estatus', 'fecha_creacion', 'fecha_modificacion'
        ]

class NominaListSerializer(serializers.ModelSerializer):
    """
    Serializador ligero para la lista de nóminas.
    Solo muestra datos pre-calculados y almacenados en la BD.
    """
    empleado = EmpleadoSerializer(read_only=True)

    class Meta:
        model = Nomina
        fields = [
            'id',
            'empleado',
            'fecha_nomina',
            'estatus',
            'nomina_a_depositar', 
            'monto_aprobado_nomina'
        ]
        read_only_fields = fields

class NominaSerializer(serializers.ModelSerializer):
    semana_nomina = serializers.SerializerMethodField()

    class Meta:
        model = Nomina
        fields = [
            # Identificación
            'id',
            'empleado',


            # Información básica de nómina
            'dias_trabajados',
            'horas_retardo', 
            'tiempo_extra',
            'vales_despensa',
            'vales_gasolina',
            'monto_aprobado_nomina',
            'observaciones',
            'estatus',
            'fecha_nomina',

            # Campos calculados de percepciones
            'salario_diario_integral',
            'bruto_semanal',
            'suma_percepciones',

            # Deducciones e impuestos
            'impuestos_isr',
            'imss_obrero',
            'cuota_fija',
            'excedente_obrero',
            'gmp_obrero',
            'rt_obrero',
            'iv_obrero',
            'gps_obrero',
            'en_dinero_obrero',
            'imss_patronal',
            'cuota_fija_patronal',
            'excedente_patronal',
            'gmp_patronal',
            'rt_patronal',
            'iv_patronal',
            'gps_patronal',
            'en_dinero_patronal',
            'infonavit_patronal',
            'deduccion_infonavit',
            'deduccion_prestamos',
            'subsidio_empleo',
            'ceav_obrero',
            'ceav_patronal',
            'calcular_aportacion_retiro_imss',

            # Resumen de deducciones e impuestos
            'suma_deducciones',
            'total_impuestos',

            # Campos de resumen
            'nomina_a_depositar',
            'nomina_semanal_fiscal',

            # Campo de la semana de la nómina
            'semana_nomina',
        ]

        read_only_fields = [
            # Campos calculados
            'salario_diario_integral',
            'bruto_semanal',
            'suma_percepciones',
            'impuestos_isr',
            'imss_obrero',
            'cuota_fija',
            'cuota_fija_patronal',
            'excedente_obrero',
            'gmp_obrero',
            'rt_obrero',
            'iv_obrero',
            'gps_obrero',
            'imss_patronal',
            'excedente_patronal',
            'gmp_patronal',
            'rt_patronal',
            'iv_patronal',
            'gps_patronal',
            'infonavit_patronal',
            'deduccion_infonavit',
            'ceav_obrero',
            'ceav_patronal',
            'calcular_aportacion_retiro_imss',

            # Resumen de deducciones e impuestos
            'suma_deducciones',
            'total_impuestos',

            # Resumen de la nómina
            'nomina_a_depositar',
            'nomina_semanal_fiscal',

            # Campo de la semana de la nómina (es solo de lectura)
            'semana_nomina',
        ]

    def get_semana_nomina(self, obj):
        """
        Obtiene la semana del año de la fecha de la nómina.
        """
        if not obj.fecha_nomina:
            return None
        return obj.fecha_nomina.isocalendar()[1]
    
    

class ComprobantePagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComprobantePagoNomina
        fields = [
            'id', 
            'nomina', 
            'tipo_pago', 
            'monto', 
            'fecha_pago', 
            'referencia', 
            'pdf', 
            'fecha_creacion', 
            'fecha_modificacion',
            'numero_tarjeta',
            'tipo_tarjeta',
            'numero_cuenta'
        ]


class NominaResidentesPracticantesSerializer(serializers.ModelSerializer):
    class Meta:
        model = NominaResidentesPracticantes
        fields = [
            'id',
            'practicante_residente',
            'estatus',
            'dias_trabajados',
            'horas_retardos',
            'fecha_nomina',
            'semana_nomina',  # Incluye el campo calculado
            'monto_aprobado',  # Entrada manual
            'apoyo_economico',  # Campo calculado y guardado
            'observaciones',
        ]
        read_only_fields = ['semana_nomina', 'apoyo_economico']  # Solo lectura para campos calculados


class ComprobantePagoResidentePracticanteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComprobantePagoResidentePracticante
        fields = [
            'id',
            'nomina',
            'tipo_pago',
            'monto',
            'fecha_pago',
            'referencia',
            'pdf',
            'fecha_creacion',
            'fecha_modificacion',
            'numero_cuenta'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_modificacion']


class AbonoProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = AbonoProveedor
        fields = [
            'id', 'cuenta', 'cantidad_abono', 'fecha_pago', 'tipo_de_pago',
            'referencia_transferencia', 'pdf','numero_tarjeta','tipo_de_pago',
            'tipo_tarjeta','numero_cuenta'
        ]

class CuentaPorPagarProveedorSerializer(serializers.ModelSerializer):
    abonos = AbonoProveedorSerializer(many=True)  # Incluye los abonos relacionados
    proveedores = serializers.SerializerMethodField()  # Campo personalizado para devolver solo el nombre del proveedor
    orden_compra_pdf = serializers.SerializerMethodField()  # Utiliza ahora `url_pdf`
    factura_pdf = serializers.SerializerMethodField()  # Campo personalizado para obtener el PDF de la factura
    departamento = serializers.SerializerMethodField()  # Devuelve el nombre en lugar del ID
    proyecto = serializers.SerializerMethodField()  # Devuelve el nombre en lugar del ID

    class Meta:
        model = CuentaPorPagarProveedor
        fields = [
            'id', 'orden', 'fecha_cfdi', 'proveedores', 'proyecto', 'departamento',
            'folio_factura', 'dias_de_credito', 'fecha_contrarecibo', 'fecha_pago',
            'total_factura', 'divisa', 'estatus', 'saldo_pendiente', 'propuesta_pago', 
            'orden_compra_pdf', 'factura_pdf', 'abonos'
        ]
        
    def get_proyecto(self, obj):
        """
        Devuelve el nombre del proyecto en lugar del ID.
        Si no hay proyecto asignado, devuelve None.
        """
        return obj.proyecto.nombre if obj.proyecto else None
    
    def get_departamento(self, obj):
        """
        Devuelve el nombre del departamento en lugar del ID.
        Si no hay departamento asignado, devuelve None.
        """
        return obj.departamento.nombre if obj.departamento else None
    
    def get_proveedores(self, obj):
        """
        Devuelve el nombre del proveedor.
        Si no existe un proveedor relacionado, devuelve None.
        """
        return obj.proveedor.razon_social if obj.proveedor else None

    def get_orden_compra_pdf(self, obj):
        """
        Obtiene la URL completa de `url_pdf` de la orden de compra si está disponible.
        """
        if obj.orden and obj.orden.url_pdf:
            return self._build_full_url(obj.orden.url_pdf)  # Usar `url_pdf` en lugar de `orden_compra_pdf`
        return None

    def get_factura_pdf(self, obj):
        """
        Obtiene la URL completa del PDF de la factura si está disponible.
        """
        if obj.factura_pdf:  # Verifica si factura_pdf está presente en el objeto
            return self._build_full_url(obj.factura_pdf.url)  # Construye la URL completa
        return None

    def _build_full_url(self, path):
        """
        Construye una URL completa a partir de un path relativo,
        reemplazando cualquier barra invertida con barras normales.
        """
        # Reemplaza las barras invertidas con barras normales
        normalized_path = path.replace('\\', '/')
        
        request = self.context.get('request')  # Obtener la solicitud actual del contexto
        if request:
            return request.build_absolute_uri(normalized_path)  # Construir URL completaz
        default_host = getattr(settings, 'DEFAULT_HOST', 'http://192.168.100.254/')
        return f"{default_host}{normalized_path}"
