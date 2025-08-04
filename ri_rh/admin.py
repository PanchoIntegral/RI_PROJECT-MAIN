from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from ri_compras.models import Nomina
from ri_rh.models import CatalogoDocumento, DocumentoCargado, DocumentoEmpleado, Empleado, PracticanteResidente, Puesto, Universidad, DocumentoRequisitos

@admin.register(Puesto)
class PuestoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'get_tipos_display')
    search_fields = ('nombre',)
    list_filter = ('tipos',)

    # Método para mostrar el tipo legible en la lista de administración
    def get_tipos_display(self, obj):
        return obj.get_tipos_display()
    get_tipos_display.short_description = 'Tipo de Puesto'


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = (
        'nombre_completo',
        'puesto',
        'estatus',
        'fecha_alta',
        'fecha_baja',
    )
    search_fields = ('nombre_completo', 'rfc', 'curp', 'numero_contacto')
    list_filter = ('estatus', 'puesto', 'escolaridad', 'fecha_alta')
    readonly_fields = ('fecha_alta',)
    

@admin.register(DocumentoEmpleado)
class DocumentoEmpleadoAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'tipo_documento', 'fecha')
    list_filter = ('tipo_documento', 'fecha')
    search_fields = ('empleado__nombre_completo', 'tipo_documento')
    date_hierarchy = 'fecha'

    def get_readonly_fields(self, request, obj=None):
        """Prevent changing 'fecha' after creation."""
        if obj:  # If editing an existing object
            return self.readonly_fields + ('fecha',)
        return self.readonly_fields
    

@admin.register(Universidad)
class UniversidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'direccion', 'numero_contacto')
    search_fields = ('nombre',)
    
    
@admin.register(PracticanteResidente)
class PracticanteResidenteAdmin(admin.ModelAdmin):
    list_display = (
        'nombre_completo',
        'tipo',
        'universidad',
        'puesto',
        'fecha_nacimiento',
        'estado',
        'fecha_alta',
        'fecha_baja',
    )
    list_filter = ('tipo', 'estado', 'universidad', 'puesto', 'fecha_alta', 'fecha_baja')
    search_fields = ('nombre_completo', 'rfc', 'curp', 'numero_contacto')
    readonly_fields = ('fecha_alta',)


@admin.register(CatalogoDocumento)
class CatalogoDocumentoAdmin(admin.ModelAdmin):
    list_display = ('universidad', 'tipo', 'nombre_documento', 'obligatorio')
    list_filter = ('universidad', 'tipo', 'obligatorio')
    search_fields = ('nombre_documento', 'universidad__nombre')


@admin.register(DocumentoCargado)
class DocumentoCargadoAdmin(admin.ModelAdmin):
    list_display = ('practicante_residente', 'catalogo_documento', 'archivo', 'fecha_carga')
    list_filter = ('catalogo_documento__tipo', 'fecha_carga')
    search_fields = ('practicante_residente__nombre_completo', 'catalogo_documento__nombre_documento')
    
@admin.register(DocumentoRequisitos)
class DocumentoRequisitosAdmin(admin.ModelAdmin):
    list_display = ('id', 'pdfRequisitosDocumentacion')
    search_fields = ('pdfRequisitosDocumentacion',)