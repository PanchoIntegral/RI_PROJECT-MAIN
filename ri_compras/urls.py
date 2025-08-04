from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AbonoProveedorViewSet,
    AbonoTarjetaViewSet,
    AportacionObreroPatronalesViewSet,
    AportacionPatronalesIMSSViewSet,
    AportacionRetiroIMSSViewSet,
    CeavIMSSViewSet,
    CeavPatronalViewSet,
    ComprobantePagoResidentePracticanteViewSet,
    ComprobantePagoViewSet,
    CreditoPrestamoViewSet,
    CuentaBancariaViewSet,
    CuentaPorPagarProveedorViewSet, 
    DepartamentoViewSet, 
    DetalleCxCViewSet, 
    EstanteViewSet,
    ISRViewSet,
    MovimientoTarjetaViewSet,
    NominaResidentesPracticantesViewSet,
    NominaViewSet,
    OtroGastoViewSet, 
    PagoCreditoPrestamoViewSet,
    PagoMensualTarjetaViewSet,
    PagoOtroGastoViewSet,
    PagoPorPeriodoViewSet, 
    PedidoViewSet, 
    ProductoAlmacenViewSet, 
    PropuestaCxCViewSet, 
    RackViewSet,
    SalarioMinimoViewSet, 
    ServiciosFacturaViewSet,
    TarjetaCreditoViewSet,
    TipoOtroGastoViewSet, 
    UsuariosViewSet, 
    ProductoViewSet, 
    RequisicionViewSet, 
    ProveedorViewSet, 
    OrdenDeCompraViewSet, 
    ReciboViewSet, 
    ServicioViewSet, 
    CustomObtainAuthToken, 
    GetUserFromToken, 
    ProjectViewSet, 
    MessageViewSet, 
    ContactoViewSet,
    VacacionesViewSet,
    PagoPeriodoAbonoViewSet,
    AmortizacionCuotaViewSet,
    BancoModeloViewSet,
    MovimientoBancoViewSet,
    AbonoBancoViewSet
)


router = DefaultRouter()
router.register(r'departamentos', DepartamentoViewSet)
router.register(r'usuarios', UsuariosViewSet)
router.register(r'productos', ProductoViewSet)
router.register(r'rack', RackViewSet)
router.register(r'estantes', EstanteViewSet)
router.register(r'productos_almacen', ProductoAlmacenViewSet)
router.register(r'pedidos', PedidoViewSet)
router.register(r'servicios', ServicioViewSet)
router.register(r'requisiciones', RequisicionViewSet)
router.register(r'proveedores', ProveedorViewSet)
router.register(r'ordenes', OrdenDeCompraViewSet)
router.register(r'recibos', ReciboViewSet)
router.register(r'proyectos', ProjectViewSet)
router.register(r'messages', MessageViewSet)
router.register(r'contactos', ContactoViewSet)
router.register(r'CuentasXcobrar', PropuestaCxCViewSet)
router.register(r'detalleCxc', DetalleCxCViewSet)
router.register(r'ServiciosFactura', ServiciosFacturaViewSet)
router.register(r'PagoPorPeriodo', PagoPorPeriodoViewSet)
router.register(r'CreditosPrestamos', CreditoPrestamoViewSet)
router.register(r'PagoCreditosPrestamos', PagoCreditoPrestamoViewSet)
router.register(r'TipoOtroGasto', TipoOtroGastoViewSet)
router.register(r'OtroGasto', OtroGastoViewSet)
router.register(r'PagoOtroGasto', PagoOtroGastoViewSet)
router.register(r'CuentaBancaria', CuentaBancariaViewSet)
router.register(r'TarjetaCredito', TarjetaCreditoViewSet)
router.register(r'PagoMensualTarjetaCredito', PagoMensualTarjetaViewSet)
router.register(r'MovimientoTarjetaCredito', MovimientoTarjetaViewSet)
router.register(r'PagoPorPeriodo', PagoPorPeriodoViewSet)
router.register(r'Isr', ISRViewSet)
router.register(r'Vacaciones', VacacionesViewSet)
router.register(r'AportacionObrero', AportacionObreroPatronalesViewSet)
router.register(r'AportacionPatronales', AportacionPatronalesIMSSViewSet)
router.register(r'AportacionRetiro', AportacionRetiroIMSSViewSet)
router.register(r'AportacionCeav', CeavIMSSViewSet)
router.register(r'SalarioMinimo', SalarioMinimoViewSet)
router.register(r'CeavPatronal', CeavPatronalViewSet)
router.register(r'PagoPeriodoAbono', PagoPeriodoAbonoViewSet)
router.register(r'Amortizacion', AmortizacionCuotaViewSet)
router.register(r'AbonoTarjeta', AbonoTarjetaViewSet)
router.register(r'BancoModelo', BancoModeloViewSet)
router.register(r'MovimientoBanco', MovimientoBancoViewSet)
router.register(r'AbonoBanco', AbonoBancoViewSet)
router.register(r'Nomina', NominaViewSet)
router.register(r'PagoNomina', ComprobantePagoViewSet)
router.register(r'NominaPracticantesResidentes', NominaResidentesPracticantesViewSet)
router.register(r'PagoNominaPracticanteResidente', ComprobantePagoResidentePracticanteViewSet)
router.register(r'CuentaPorPagarProveedor', CuentaPorPagarProveedorViewSet)
router.register(r'AbonoProveedor', AbonoProveedorViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('login/', CustomObtainAuthToken.as_view(), name='login'),
    path('loginbytoken/', GetUserFromToken.as_view(), name='loginbytoken'),
]