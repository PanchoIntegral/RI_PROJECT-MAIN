from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from ri_produccion.models import HorarioProduccion, PersonalMaquina

from .models import AbonoTarjeta, AbonoProveedor, AmortizacionCuota, AportacionObreroPatronales, AportacionPatronalesIMSS, AportacionRetiroIMSS, CeavIMSS, CeavPatronal, ComprobantePagoNomina, ComprobantePagoResidentePracticante, CreditoPrestamo, CuentaBancaria, CuentaPorPagarProveedor, DetalleCxC, Estante, Isr, Message, MovimientoTarjeta, Nomina, NominaResidentesPracticantes, OtroGasto, PagoCreditoPrestamo, PagoMensualTarjeta, PagoOtroGasto, PagoPorPeriodo, Pedido, ProductoAlmacen, ProductoRequisicion, Rack, ProductoRequisicion, SalarioMinimo, ServiciosFactura, TarjetaCredito, TipoOtroGasto, Usuarios, Vacaciones
from .models import Departamento
from .models import Producto
from .models import Servicio
from .models import Requisicion
from .models import Proveedor
from .models import OrdenDeCompra
from .models import Recibo
from .models import Project
from .models import Contacto
from .models import CuentaPorCobrar, DetalleCxC
from .models import PagoPeriodoAbono
from .models import BancoModelo,MovimientoBanco,AbonoBanco

class ProjectAdmin(SimpleHistoryAdmin):
    def history_view(self, request, object_id, extra_context=None):
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()
        
        return super().history_view(request, object_id, extra_context=extra_context)

    def get_change_reason(self):
        return None

admin.site.register(Project, ProjectAdmin)

class ProductosAdmin(SimpleHistoryAdmin):
    def history_view(self, request, object_id, extra_context=None):
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()

        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(Producto, ProductosAdmin)

class ProductosRequisicionAdmin(SimpleHistoryAdmin):
    def history_view(self, request, object_id, extra_context=None):
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()

        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(ProductoRequisicion, ProductosRequisicionAdmin)

class PedidosAdmin(SimpleHistoryAdmin):
    def history_view(self, request, object_id, extra_context=None):
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()

        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(Pedido, PedidosAdmin)

class ProductosAlmacenAdmin(SimpleHistoryAdmin):
    def history_view(self, request, object_id, extra_context=None):
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()

        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(ProductoAlmacen, ProductosAlmacenAdmin)

class RackAdmin(SimpleHistoryAdmin):
    def history_view(self, request, object_id, extra_context=None):
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()

        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(Rack, RackAdmin)

class EstanteAdmin(SimpleHistoryAdmin):
    def history_view(self, request, object_id, extra_context=None):
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()

        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(Estante, EstanteAdmin)

class MaquinasAsignadasInline(admin.TabularInline):
    model = PersonalMaquina
    extra = 0
    autocomplete_fields = ["maquina"]
    fields = ("maquina",)
    verbose_name = "Máquina asignada"
    verbose_name_plural = "Máquinas asignadas "
    
class HorarioProduccionInline(admin.TabularInline):
    model = HorarioProduccion
    extra = 1
    fields = (
        "dia", "hora_entrada", "hora_salida",
        "tiene_horario_comida", "hora_comida_inicio", "hora_comida_fin"
    )
    verbose_name = "Horario de Producción"
    verbose_name_plural = "Horarios de Producción"


class UsuariosAdmin(SimpleHistoryAdmin):
    list_display = ("id", "nombre", "correo")  
    search_fields = ("nombre", "correo") 

    inlines = [MaquinasAsignadasInline, HorarioProduccionInline]

    def history_view(self, request, object_id, extra_context=None):
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()
        return super().history_view(request, object_id, extra_context=extra_context)


admin.site.register(Usuarios, UsuariosAdmin)

class DepartamentoAdmin(SimpleHistoryAdmin):
    def history_view(self, request, object_id, extra_context=None):
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()

        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(Departamento, DepartamentoAdmin)

class ServicioAdmin(SimpleHistoryAdmin):
    def history_view(self, request, object_id, extra_context=None):
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()

        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(Servicio, ServicioAdmin)

class RequisicionAdmin(SimpleHistoryAdmin):
    def history_view(self, request, object_id, extra_context=None):
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()

        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(Requisicion, RequisicionAdmin)

class ContactoInline(admin.TabularInline):
    model = Proveedor.contactos.through

class ProveedorAdmin(SimpleHistoryAdmin):
    inlines = [
        ContactoInline,
    ]
    exclude = ('contactos',)
     
     
    def history_view(self, request, object_id, extra_context=None):
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()

        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(Proveedor, ProveedorAdmin)


class OrdenDeCompraAdmin(SimpleHistoryAdmin):
    list_display = ('id', 'fecha_emision', 'proveedor', 'usuario', 'estado', 'total', 'divisa', 'orden_recibida')
    search_fields = ('id', 'proveedor__nombre', 'usuario__username', 'estado', 'total')
    list_filter = ('estado', 'orden_recibida', 'fecha_emision', 'divisa')

    actions = ['marcar_como_recibida', 'cambiar_estado_a_en_camino']

    def marcar_como_recibida(self, request, queryset):
        """Acción para marcar las órdenes seleccionadas como recibidas."""
        queryset.update(orden_recibida=True)
        self.message_user(request, "Las órdenes seleccionadas han sido marcadas como recibidas.")

    marcar_como_recibida.short_description = "Marcar como recibida"

    def cambiar_estado_a_en_camino(self, request, queryset):
        """Acción para cambiar el estado de las órdenes a 'EN CAMINO'."""
        queryset.update(estado='EN CAMINO')
        self.message_user(request, "El estado de las órdenes seleccionadas ha sido cambiado a 'EN CAMINO'.")

    cambiar_estado_a_en_camino.short_description = "Cambiar estado a 'EN CAMINO'"

    def history_view(self, request, object_id, extra_context=None):
        """Optimiza la visualización del historial de cambios de la orden de compra."""
        obj = self.model.objects.get(pk=object_id)
        extra_context = extra_context or {}
        extra_context['history'] = obj.history.all()
        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(OrdenDeCompra, OrdenDeCompraAdmin)

class ReciboAdmin(SimpleHistoryAdmin):
    def history_view(self, request, object_id, extra_context=None):
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()

        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(Recibo, ReciboAdmin)
admin.site.register(Contacto)

class MessageAdmin(SimpleHistoryAdmin):
    def history_view(self, request, object_id, extra_context=None):
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()

        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(Message, MessageAdmin)


# Admin personalizado para CuentaPorCobrar
@admin.register(CuentaPorCobrar)
class PropuestaCxCAdmin(SimpleHistoryAdmin):
    list_display = (
        'razon_social',
        'oc_po',
        'numero_proyecto_interno_ri',
        'importe_total_facturado_con_iva',
        'importe_pago',
        'saldo',
        'divisa',
        'estatus',
        'fecha_programada_pago',
    )
    list_filter = ('estatus', 'divisa', 'fecha_programada_pago')
    search_fields = ('razon_social', 'oc_po', 'folio_cfdi', 'numero_proyecto_interno_ri')
    date_hierarchy = 'fecha_programada_pago'
    ordering = ('-fecha_programada_pago',)

    def history_view(self, request, object_id, extra_context=None):
        obj = self.model.objects.get(pk=object_id)
        history = obj.history.all()
        return super().history_view(request, object_id, extra_context=extra_context)


# Admin personalizado para DetalleCxC
@admin.register(DetalleCxC)
class DetalleCxCAdmin(SimpleHistoryAdmin):
    list_display = (
        'propuesta_cxc',
        'abono',
        'tipo_de_pago',
        'referencia_transferencia',
        'fecha_pago',
        'numero_cuenta',
    )
    list_filter = ('tipo_de_pago', 'fecha_pago')
    search_fields = ('propuesta_cxc__razon_social', 'referencia_transferencia', 'numero_cuenta')
    date_hierarchy = 'fecha_pago'
    ordering = ('-fecha_pago',)

    def history_view(self, request, object_id, extra_context=None):
        obj = self.model.objects.get(pk=object_id)
        history = obj.history.all()
        return super().history_view(request, object_id, extra_context=extra_context)
    


# Admin para el modelo ServiciosFactura
class ServiciosFacturaAdmin(SimpleHistoryAdmin):
    list_display = ('nombre_servicio', 'folio_servicio', 'total_a_pagar', 'divisa', 'fecha_vencimiento', 'periodicidad', 'estatus')
    search_fields = ('nombre_servicio', 'folio_servicio')
    list_filter = ('divisa', 'estatus', 'periodicidad', 'fecha_vencimiento')
    ordering = ('-fecha_creacion',)
    readonly_fields = ('fecha_creacion',)

    def history_view(self, request, object_id, extra_context=None):
        # Mostrar histórico de cambios del servicio
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()
        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(ServiciosFactura, ServiciosFacturaAdmin)


class CreditoPrestamoAdmin(SimpleHistoryAdmin):
    # Campos que se mostrarán en la lista de objetos
    list_display = (
        'emisor', 'receptor', 'tipo_transaccion', 'importe', 'numero_transaccion',
        'fecha_realizacion', 'fecha_vencimiento', 'estatus', 'numero_cuenta',
        'descripcion', 'comprobantepdf'  # Nuevos campos
    )

    # Campos por los que se puede buscar
    search_fields = (
        'emisor', 'receptor', 'numero_transaccion', 'tipo_transaccion',
        'descripcion'  # Nuevo campo de búsqueda
    )

    # Filtros disponibles en el panel de administración
    list_filter = (
        'divisa', 'estatus', 'periodicidad', 'fecha_vencimiento', 'emitido_recibido'
    )

    # Ordenamiento por defecto
    ordering = ('-fecha_realizacion',)

    # Campos editables directamente en la lista
    list_editable = ('estatus',)  # Permite editar el estatus directamente en la lista

    # Campos que se mostrarán en el formulario de edición
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'emisor', 'receptor', 'tipo_transaccion', 'importe', 'numero_transaccion',
                'descripcion', 'comprobantepdf'  # Nuevos campos
            ),
        }),
        ('Detalles del Crédito/Préstamo', {
            'fields': (
                'tasa_interes_normal', 'tasa_interes_moratorio', 'fecha_realizacion',
                'fecha_vencimiento', 'divisa', 'periodicidad', 'emitido_recibido', 'termino',
                'numero_cuenta'
            ),
        }),
        ('Estatus', {
            'fields': ('estatus',),
        }),
    )

    # Método para personalizar la vista de historial
    def history_view(self, request, object_id, extra_context=None):
        # Obtener el objeto y su historial
        obj = self.model.objects.get(pk=object_id)
        history = obj.history.all()

        # Agregar el historial al contexto adicional
        extra_context = extra_context or {}
        extra_context['history'] = history

        return super().history_view(request, object_id, extra_context=extra_context)

# Registrar el modelo con el admin personalizado
admin.site.register(CreditoPrestamo, CreditoPrestamoAdmin)


# Admin para el modelo PagoCreditoPrestamo
class PagoCreditoPrestamoAdmin(SimpleHistoryAdmin):
    list_display = ('amortizacion_cuota', 'abono', 'fecha_pago', 'referencia_transferencia')
    search_fields = ('referencia_transferencia', 'credito_prestamo__numero_transaccion', 'credito_prestamo__emisor', 'credito_prestamo__receptor')
    list_filter = ('fecha_pago',)
    ordering = ('-fecha_pago',)

    def history_view(self, request, object_id, extra_context=None):
        # Mostrar el histórico de cambios del pago
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()
        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(PagoCreditoPrestamo, PagoCreditoPrestamoAdmin)

# Admin para el modelo AmortizacionCuota
class AmortizacionCuotaAdmin(SimpleHistoryAdmin):
    list_display = ('credito_prestamo', 'numero_mes', 'principal', 'interes', 'interes_moratorio', 'balance_restante', 'fecha_pago_programada', 'estatus_pago')
    search_fields = ('credito_prestamo__numero_transaccion', 'credito_prestamo__emisor', 'credito_prestamo__receptor')
    list_filter = ('estatus_pago', 'fecha_pago_programada', 'credito_prestamo__tipo_transaccion')
    ordering = ('-fecha_pago_programada', 'numero_mes')

    def history_view(self, request, object_id, extra_context=None):
        # Mostrar el histórico de cambios de la cuota de amortización
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()
        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(AmortizacionCuota, AmortizacionCuotaAdmin)

# Admin para TipoOtroGasto
class TipoOtroGastoAdmin(SimpleHistoryAdmin):
    list_display = ('nombre',)  # Mostrar el nombre del tipo de gasto
    search_fields = ('nombre',)  # Habilitar búsqueda por nombre
    ordering = ('nombre',)  # Ordenar por nombre

    def history_view(self, request, object_id, extra_context=None):
        # Mostrar histórico de cambios para el tipo de gasto
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()
        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(TipoOtroGasto, TipoOtroGastoAdmin)

# Admin para OtroGasto

class OtroGastoAdmin(SimpleHistoryAdmin):
    """
    Admin para el modelo OtroGasto, permite la visualización y edición de los gastos.
    """
    list_display = ('descripcion', 'monto_total', 'calcular_saldo', 'divisa', 'estatus', 'fecha_aprobacion')
    search_fields = ('descripcion', 'tipo_gasto__nombre')
    list_filter = ('divisa', 'estatus', 'fecha_aprobacion', 'fecha_pago')
    ordering = ('-fecha',)

    # Aquí solo mantenemos readonly_fields para el campo 'fecha', que es autogenerado
    readonly_fields = ('fecha',)

    def history_view(self, request, object_id, extra_context=None):
        """
        Mostrar el historial de cambios de un registro.
        """
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()
        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(OtroGasto, OtroGastoAdmin)

# Admin para PagoOtroGasto
class PagoOtroGastoAdmin(SimpleHistoryAdmin):
    list_display = ('otro_gasto', 'abono', 'fecha_abono', 'referencia')
    search_fields = ('referencia', 'otro_gasto__descripcion')
    list_filter = ('fecha_abono',)
    ordering = ('-fecha_abono',)

    def history_view(self, request, object_id, extra_context=None):
        # Mostrar histórico de cambios para el pago
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()
        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(PagoOtroGasto, PagoOtroGastoAdmin)

class CuentaBancariaAdmin(SimpleHistoryAdmin):
    list_display = ('servicio', 'numero_cuenta', 'clave_interbancaria', 'banco')
    
    search_fields = ('numero_cuenta', 'banco', 'servicio__nombre_servicio')
    
    list_filter = ('banco',)
    
    ordering = ('banco',)
    
    def history_view(self, request, object_id, extra_context=None):
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()
        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(CuentaBancaria, CuentaBancariaAdmin)

class TarjetaCreditoAdmin(SimpleHistoryAdmin):
    list_display = ('banco', 'numero_tarjeta', 'saldo', 'limite_credito', 'divisa', 'estatus', 'fecha_corte', 'fecha_pago')
    search_fields = ('banco', 'numero_tarjeta')
    list_filter = ('estatus', 'divisa', 'fecha_corte', 'fecha_pago')
    ordering = ('-fecha_corte',)

    def history_view(self, request, object_id, extra_context=None):
        # Mostrar histórico de cambios para la tarjeta de crédito
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()
        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(TarjetaCredito, TarjetaCreditoAdmin)

class MovimientoTarjetaAdmin(SimpleHistoryAdmin):
    list_display = ('tarjeta', 'monto', 'concepto', 'fecha')
    search_fields = ('tarjeta__numero_tarjeta', 'concepto')
    list_filter = ('fecha',)
    ordering = ('-fecha',)

    def history_view(self, request, object_id, extra_context=None):
        # Mostrar histórico de cambios para los movimientos de tarjeta
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()
        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(MovimientoTarjeta, MovimientoTarjetaAdmin)

class PagoMensualTarjetaAdmin(SimpleHistoryAdmin):
    list_display = ('tarjeta', 'mes', 'pago_minimo', 'interes', 'fecha_vencimiento', 'estatus','saldo_pendiente','fecha_corte')
    search_fields = ('tarjeta__numero_tarjeta',)
    list_filter = ('estatus', 'fecha_vencimiento')
    ordering = ('-fecha_vencimiento',)

    def history_view(self, request, object_id, extra_context=None):
        # Mostrar histórico de cambios para los pagos mensuales de tarjeta
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()
        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(PagoMensualTarjeta, PagoMensualTarjetaAdmin)

class AbonoTarjetaAdmin(SimpleHistoryAdmin):
    list_display = ('fecha_abono', 'monto_abono', 'referencia_transferencia')
    search_fields = ('tarjeta__numero_tarjeta', 'referencia_transferencia')
    list_filter = ('fecha_abono',)
    ordering = ('-fecha_abono',)

    def history_view(self, request, object_id, extra_context=None):
        # Mostrar histórico de cambios para los abonos
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()
        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(AbonoTarjeta, AbonoTarjetaAdmin)

class PagoPorPeriodoAdmin(SimpleHistoryAdmin):
    list_display = ('servicio', 'fecha_corte', 'fecha_vencimiento', 'saldo_pendiente', 'divisa', 'estatus', 'propuesta_pago')
    search_fields = ('servicio__nombre_servicio',)
    list_filter = ('divisa', 'estatus', 'fecha_corte', 'fecha_vencimiento')
    ordering = ('-fecha_corte',)

    def history_view(self, request, object_id, extra_context=None):
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()
        return super().history_view(request, object_id, extra_context=extra_context)
    
admin.site.register(PagoPorPeriodo, PagoPorPeriodoAdmin)


# Admin para ISR
class IsrAdmin(SimpleHistoryAdmin):
    list_display = ('limite_inferior', 'limite_superior', 'cuota_fija', 'porcentaje_excedente', 'estatus', 'fecha_modificacion')
    search_fields = ('limite_inferior', 'limite_superior')
    list_filter = ('estatus', 'fecha_modificacion')
    ordering = ('-fecha_modificacion',)

admin.site.register(Isr, IsrAdmin)


#Admin para vacacionesAdmin.
class VacacionesAdmin(admin.ModelAdmin):
    list_display = ('años', 'dias','estatus', 'fecha_modificacion')
    search_fields = ('años',)
    ordering = ('-fecha_modificacion',)

admin.site.register(Vacaciones, VacacionesAdmin)


# Admin para Aportaciones Obrero Patronales IMSS
class AportacionObreroPatronalesAdmin(SimpleHistoryAdmin):
    list_display = ('concepto', 'patron', 'trabajador', 'estatus', 'fecha_modificacion')
    search_fields = ('concepto',)
    list_filter = ('estatus', 'fecha_modificacion')
    ordering = ('-fecha_modificacion',)

admin.site.register(AportacionObreroPatronales, AportacionObreroPatronalesAdmin)


# Admin para Aportaciones Patronales IMSS
class AportacionPatronalesIMSSAdmin(SimpleHistoryAdmin):
    list_display = ('concepto', 'patron', 'trabajador', 'estatus', 'fecha_modificacion')
    search_fields = ('concepto',)
    list_filter = ('estatus', 'fecha_modificacion')
    ordering = ('-fecha_modificacion',)

admin.site.register(AportacionPatronalesIMSS, AportacionPatronalesIMSSAdmin)


# Admin para Aportaciones Retiro IMSS
class AportacionRetiroIMSSAdmin(SimpleHistoryAdmin):
    list_display = ('concepto', 'patron', 'trabajador', 'estatus', 'fecha_modificacion')
    search_fields = ('concepto',)
    list_filter = ('estatus', 'fecha_modificacion')
    ordering = ('-fecha_modificacion',)

admin.site.register(AportacionRetiroIMSS, AportacionRetiroIMSSAdmin)


# Admin para CEAV IMSS
class CeavIMSSAdmin(SimpleHistoryAdmin):
    list_display = ('concepto', 'patron', 'trabajador', 'estatus', 'fecha_modificacion')
    search_fields = ('concepto',)
    list_filter = ('estatus', 'fecha_modificacion')
    ordering = ('-fecha_modificacion',)

admin.site.register(CeavIMSS, CeavIMSSAdmin)


# Admin para Salario Mínimo y UMA
class SalarioMinimoAdmin(SimpleHistoryAdmin):
    list_display = ('salario_minimo', 'uma', 'estatus', 'fecha_modificacion')
    search_fields = ('salario_minimo', 'uma')
    list_filter = ('estatus', 'fecha_modificacion')
    ordering = ('-fecha_modificacion',)

admin.site.register(SalarioMinimo, SalarioMinimoAdmin)


class CeavPatronalAdmin(SimpleHistoryAdmin):
    list_display = ('limite_inferior', 'limite_superior', 'porcentaje', 'estatus', 'fecha_modificacion')
    search_fields = ('limite_inferior', 'limite_superior')
    list_filter = ('estatus', 'fecha_modificacion')
    ordering = ('-fecha_modificacion',)

admin.site.register(CeavPatronal, CeavPatronalAdmin)

class PagoPeriodoAbonoAdmin(SimpleHistoryAdmin):
    list_display = ('periodo', 'numero_tarjeta', 'abono', 'fecha_abono', 'referencia', 'tipo_de_pago',)
    search_fields = ('periodo',)
    ordering = ('-periodo',)

    def history_view(self, request, object_id, extra_context=None):
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()
        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(PagoPeriodoAbono, PagoPeriodoAbonoAdmin)

class BancoModeloAdmin(SimpleHistoryAdmin):
    list_display = (
        'banco', 
        'numero_cuenta', 
        'numero_tarjeta', 
        'saldo', 
        'divisa', 
        'estatus', 
        'fecha_vencimiento'
    )
    search_fields = ('banco', 'numero_cuenta', 'numero_tarjeta')
    list_filter = ('estatus', 'divisa', 'fecha_vencimiento')
    ordering = ('-fecha_vencimiento',)

    def history_view(self, request, object_id, extra_context=None):
        # Mostrar histórico de cambios para BancoModelo
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()
        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(BancoModelo, BancoModeloAdmin)

class MovimientoBancoAdmin(SimpleHistoryAdmin):
    list_display = (
        'numero_cuenta', 
        'monto_movimiento', 
        'tipo_movimiento', 
        'fecha_movimiento', 
        'referencia'
    )
    search_fields = ('numero_cuenta__numero_cuenta', 'referencia', 'cliente', 'proveedor')
    list_filter = ('tipo_movimiento', 'fecha_movimiento', 'divisa')
    ordering = ('-fecha_movimiento',)

    def history_view(self, request, object_id, extra_context=None):
        # Mostrar histórico de cambios para los movimientos bancarios
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()
        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(MovimientoBanco, MovimientoBancoAdmin)

class AbonoBancoAdmin(SimpleHistoryAdmin):
    list_display = (
        'numero_cuenta', 
        'monto_movimiento', 
        'tipo_movimiento', 
        'fecha_movimiento', 
        'referencia'
    )
    search_fields = ('numero_cuenta__numero_cuenta', 'referencia', 'cliente')
    list_filter = ('tipo_movimiento', 'fecha_movimiento')
    ordering = ('-fecha_movimiento',)

    def history_view(self, request, object_id, extra_context=None):
        # Mostrar histórico de cambios para los abonos
        object = self.model.objects.get(pk=object_id)
        history = object.history.all()
        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(AbonoBanco, AbonoBancoAdmin)

@admin.register(Nomina)
class NominaAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para la tabla Nomina.
    """
    list_display = (
        'empleado', 
        'fecha_nomina', 
        'dias_trabajados', 
        'horas_retardo',  # Nuevo campo añadido
        'salario_diario_integral', 
        'bruto_semanal', 
        'suma_percepciones', 
        'monto_aprobado_nomina', 
        'estatus'
    )
    list_filter = ('estatus', 'fecha_nomina')
    search_fields = ('empleado__nombre_completo', 'estatus', 'fecha_nomina')
    ordering = ('-fecha_nomina',)

    fieldsets = (
        (None, {
            'fields': ('empleado', 'fecha_nomina', 'observaciones', 'estatus')
        }),
        ('Información Básica', {
            'fields': (
                'dias_trabajados', 
                'horas_retardo',  # Nuevo campo añadido
                'tiempo_extra', 
                'vales_despensa', 
                'vales_gasolina', 
                'monto_aprobado_nomina'
            )
        }),
        ('Percepciones Calculadas', {
            'fields': (
                'salario_diario_integral', 
                'bruto_semanal', 
                'suma_percepciones'
            )
        }),
        ('Deducciones Calculadas', {
            'fields': (
                'impuestos_isr', 
                'imss_obrero', 
                'imss_patronal', 
                'infonavit_patronal', 
                'deduccion_infonavit', 
                'deduccion_prestamos', 
                'subsidio_empleo',
                'ceav_obrero', 
                'ceav_patronal', 
                'aportacion_retiro_imss'
            )
        }),
        ('Resumen de Nómina', {
            'fields': (
                'suma_deducciones', 
                'total_impuestos', 
                'nomina_a_depositar', 
                'nomina_semanal_fiscal'
            )
        }),
    )

    readonly_fields = (
        'salario_diario_integral', 
        'bruto_semanal', 
        'suma_percepciones', 
        'impuestos_isr', 
        'imss_obrero', 
        'imss_patronal', 
        'infonavit_patronal', 
        'deduccion_infonavit', 
        'ceav_obrero', 
        'ceav_patronal', 
        'aportacion_retiro_imss', 
        'suma_deducciones', 
        'total_impuestos', 
        'nomina_a_depositar', 
        'nomina_semanal_fiscal'
    )

    def get_readonly_fields(self, request, obj=None):
        """
        Sobrescribe los campos de solo lectura según sea creación o edición.
        """
        if obj:  # Si se está editando
            return self.readonly_fields + ('empleado', 'fecha_nomina')
        return self.readonly_fields

@admin.register(ComprobantePagoNomina)
class ComprobantePagoAdmin(admin.ModelAdmin):
    list_display = ('nomina', 'tipo_pago', 'monto', 'fecha_pago', 'referencia')
    search_fields = ('nomina__empleado__nombre_completo', 'tipo_pago', 'referencia')
    list_filter = ('tipo_pago', 'fecha_pago')
    ordering = ('-fecha_pago',)


@admin.register(NominaResidentesPracticantes)
class NominaResidentesPracticantesAdmin(admin.ModelAdmin):
    list_display = (
        'dias_trabajados',
        'horas_retardos',
        'practicante_residente',
        'fecha_nomina',
        'semana_nomina',  # Mostrar la semana
        'monto_aprobado',  # Monto aprobado manual
        'apoyo_economico',  # Mostrar el apoyo económico almacenado
        'estatus',
    )
    list_filter = ('estatus', 'fecha_nomina', 'semana_nomina')
    search_fields = ('practicante_residente__nombre_completo', 'estatus', 'fecha_nomina')
    ordering = ('-fecha_nomina',)
    readonly_fields = ('semana_nomina', 'apoyo_economico')  # Campos calculados como solo lectura


@admin.register(ComprobantePagoResidentePracticante)
class ComprobantePagoResidentePracticanteAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para los comprobantes de pago de residentes y practicantes.
    """
    list_display = (
        'nomina',
        'tipo_pago',
        'monto',
        'fecha_pago',
        'referencia',
    )
    list_filter = ('tipo_pago', 'fecha_pago')
    search_fields = ('nomina__practicante_residente__nombre_completo', 'referencia', 'tipo_pago')
    ordering = ('-fecha_pago',)
    
    

class CuentaPorPagarProveedorAdmin(SimpleHistoryAdmin):
    list_display = (
        'orden',
        'proveedor',
        'proyecto',
        'departamento',
        'folio_factura',
        'dias_de_credito',
        'fecha_contrarecibo',
        'fecha_pago',
        'total_factura',
        'divisa',
        'estatus',
        'saldo_pendiente',
        'propuesta_pago',
    )
    search_fields = ('folio_factura', 'proveedor__razon_social', 'orden__id')
    list_filter = ('divisa', 'estatus', 'fecha_contrarecibo', 'fecha_pago')
    ordering = ('-fecha_contrarecibo',)

    def history_view(self, request, object_id, extra_context=None):
        obj = self.model.objects.get(pk=object_id)
        history = obj.history.all()
        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(CuentaPorPagarProveedor, CuentaPorPagarProveedorAdmin)


class AbonoProveedorAdmin(SimpleHistoryAdmin):
    list_display = (
        'cuenta',
        'cantidad_abono',
        'fecha_pago',
        'tipo_de_pago',
        'referencia_transferencia',
    )
    search_fields = ('proveedor__razon_social', 'cuenta__folio_factura', 'referencia_transferencia')
    list_filter = ('tipo_de_pago', 'fecha_pago')
    ordering = ('-fecha_pago',)

    def history_view(self, request, object_id, extra_context=None):
        obj = self.model.objects.get(pk=object_id)
        history = obj.history.all()
        return super().history_view(request, object_id, extra_context=extra_context)

admin.site.register(AbonoProveedor, AbonoProveedorAdmin)
