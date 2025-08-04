from pyexpat.errors import messages
from django.contrib import admin
from django.forms import ValidationError
from django.http import HttpResponse
import csv
from ri_compras.models import Usuarios  # Asegúrate de importar el modelo
from .models import AsignacionProceso, AsignacionTratamientoCalidad, Espesor, EstanteProduccion, EtapaCalidad, FlujoCalidad, HorarioProduccion, InventarioMaterial, Maquina, MaquinaProceso, Material, Nesteo, OrdenProduccion, PersonalMaquina, Pieza, PiezaNesteo, PresentacionMaterial, Proceso, ProveedorTratamiento, RackProduccion, ScrapCalidad, TratamientoCalidad, UbicacionPieza

# admmin de Espesores
@admin.register(Espesor)
class EspesorAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre_comercial", "valor_pulgadas")
    list_filter = ("nombre_comercial",)
    search_fields = ("nombre_comercial",)
    ordering = ("valor_pulgadas",)
    list_per_page = 25
    readonly_fields = ("id",)
    actions = ["exportar_csv", "duplicar_espesor"]

    def exportar_csv(self, request, queryset):
        """ Exporta espesores seleccionados a un archivo CSV """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="espesores.csv"'
        writer = csv.writer(response)
        writer.writerow(["ID", "Nombre Comercial", "Valor en Pulgadas"])
        for espesor in queryset:
            writer.writerow([
                espesor.id,
                espesor.nombre_comercial,
                float(espesor.valor_pulgadas)
            ])
        return response
    exportar_csv.short_description = "📂 Exportar CSV"

    def duplicar_espesor(self, request, queryset):
        """ Duplica los espesores seleccionados """
        for obj in queryset:
            obj.pk = None
            obj.save()
    duplicar_espesor.short_description = "📝 Duplicar Espesor"

@admin.register(PresentacionMaterial)
class PresentacionMaterialAdmin(admin.ModelAdmin):
    list_display = (
        "id", "nombre_comercial", "largo", "ancho", "diametro", 
        "espesor"
    )
    list_filter = ("espesor",)
    search_fields = ("nombre_comercial",)
    ordering = ("nombre_comercial",)
    list_per_page = 25
    list_select_related = ("espesor",)
    readonly_fields = ("id",)
    autocomplete_fields = ("espesor",)

    actions = ["exportar_csv", "duplicar_presentacion"]

    def exportar_csv(self, request, queryset):
        """ Exporta presentaciones seleccionadas a un archivo CSV """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="presentaciones_material.csv"'
        writer = csv.writer(response)
        writer.writerow([
            "ID", "Nombre", "Largo", "Ancho", "Diámetro",
            "Espesor (ID)"
        ])
        for presentacion in queryset:
            writer.writerow([
                presentacion.id,
                presentacion.nombre,
                presentacion.largo or "",
                presentacion.ancho or "",
                presentacion.diametro or "",
                presentacion.espesor.id if presentacion.espesor else "",
            ])
        return response
    exportar_csv.short_description = "📂 Exportar CSV"

    def duplicar_presentacion(self, request, queryset):
        """ Duplica las presentaciones seleccionadas """
        for obj in queryset:
            obj.pk = None
            obj.save()
    duplicar_presentacion.short_description = "📝 Duplicar Presentación"
    
## Admin materiales

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "tipo", )  
    list_filter = ("tipo", )  # Filtro actualizado
    search_fields = ("nombre", "tipo",)  
    ordering = ("nombre",)
    list_per_page = 25


    readonly_fields = ("id",)

    actions = ["exportar_csv", "duplicar_material"]

    def exportar_csv(self, request, queryset):
        """ Exporta materiales seleccionados a un archivo CSV """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="materiales.csv"'
        writer = csv.writer(response)
        writer.writerow(["ID", "Nombre", "Tipo", ])
        for material in queryset:
            writer.writerow([
                material.id,
                material.nombre,
                material.tipo,
            ])
        return response
    exportar_csv.short_description = "📂 Exportar CSV"

    def duplicar_material(self, request, queryset):
        """ Duplica los materiales seleccionados """
        for obj in queryset:
            obj.pk = None
            obj.save()
    duplicar_material.short_description = "📝 Duplicar Material"
    
    
@admin.register(OrdenProduccion)
class OrdenProduccionAdmin(admin.ModelAdmin):
    list_display = ("id", "codigo_orden", "estado", "fecha_creacion")  # Muestra estas columnas en la lista
    list_filter = ("estado",)  # Agrega filtros por estado
    search_fields = ("codigo_orden",)  # Habilita búsqueda en tiempo real
    ordering = ("-fecha_creacion",)  # Ordena por defecto mostrando las más recientes primero
    list_per_page = 25  # Paginación para evitar carga lenta
    
    readonly_fields = ("id", "fecha_creacion")  # Evita edición manual del ID y la fecha

    actions = ["exportar_csv", "duplicar_orden"]  # Agrega opciones personalizadas

    def exportar_csv(self, request, queryset):
        """ Exporta órdenes seleccionadas a un archivo CSV """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="ordenes_produccion.csv"'
        writer = csv.writer(response)
        writer.writerow(["ID", "Código de Orden", "Estado", "Fecha de Creación"])
        for orden in queryset:
            writer.writerow([orden.id, orden.codigo_orden, orden.estado, orden.fecha_creacion])
        return response
    exportar_csv.short_description = "📂 Exportar CSV"

    def duplicar_orden(self, request, queryset):
        """ Duplica las órdenes seleccionadas """
        for obj in queryset:
            obj.pk = None  # Elimina el ID para crear un nuevo registro
            obj.save()
    duplicar_orden.short_description = "📝 Duplicar Orden"



# --- Inlines para Pieza ---

class PiezaNesteoInline(admin.TabularInline):
    """ Permite gestionar los nesteos dentro de la vista de una pieza """
    model = PiezaNesteo
    extra = 1  # Permite agregar nuevos nesteos directamente
    autocomplete_fields = ["nesteo"]  # Facilita la selección del nesteo
    fields = ("nesteo", "cantidad", "estado")

class FlujoCalidadInline(admin.TabularInline):
    """ Permite gestionar las etapas de calidad desde la vista de una pieza """
    model = FlujoCalidad
    extra = 1
    autocomplete_fields = ["etapa_calidad"]
    fields = ("etapa_calidad", "estado", "piezas_asignadas", "piezas_liberadas", "fecha_finalizacion")

class ScrapCalidadInline(admin.TabularInline):
    """ Permite gestionar los registros de scrap desde la vista de una pieza """
    model = ScrapCalidad
    extra = 1
    autocomplete_fields = ["etapa_calidad"]
    fields = ("etapa_calidad", "cantidad_scrap", "motivo")

class AsignacionTratamientoCalidadInline(admin.TabularInline):
    """ Permite gestionar los tratamientos aplicados a una pieza desde su vista """
    model = AsignacionTratamientoCalidad
    extra = 1
    autocomplete_fields = ["proveedor"]
    fields = ("tratamiento", "proveedor", "fecha_salida", "fecha_entrega", "fecha_recepcion")

class AsignacionProcesoInline(admin.TabularInline):
    model = AsignacionProceso
    extra = 1
    autocomplete_fields = ["proceso"] 
    fields = ("proceso", "usuario", "estado", "piezas_asignadas", "piezas_liberadas", "piezas_scrap")


# --- Admin para Pieza ---
@admin.register(Pieza)
class PiezaAdmin(admin.ModelAdmin):
    list_display = (
        "id", "consecutivo", "orden_produccion", "material", "presentacion",
        "prioritario", "creado_por", "fecha_creacion"
    )
    list_filter = (
        "orden_produccion", "material", "presentacion", "prioritario", "creado_por"
    )
    search_fields = ("consecutivo", "creado_por__nombre", "presentacion__nombre_comercial")
    ordering = ("-fecha_creacion",)
    list_per_page = 25
    list_select_related = ("orden_produccion", "material", "presentacion", "creado_por")
    autocomplete_fields = ["orden_produccion", "material", "presentacion", "creado_por"]
    readonly_fields = ("id", "fecha_creacion")

    inlines = [
        PiezaNesteoInline, FlujoCalidadInline, ScrapCalidadInline,
        AsignacionTratamientoCalidadInline, AsignacionProcesoInline
    ]

    actions = ["exportar_csv", "duplicar_pieza"]

    def exportar_csv(self, request, queryset):
        """Exporta piezas seleccionadas a un archivo CSV"""
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="piezas.csv"'
        writer = csv.writer(response)
        writer.writerow([
            "ID", "Consecutivo", "Orden de Producción", "Material", "Presentación",
            "Prioritario", "Creado Por", "Fecha de Creación"
        ])
        for pieza in queryset:
            writer.writerow([
                pieza.id, pieza.consecutivo,
                pieza.orden_produccion.codigo_orden if pieza.orden_produccion else "Sin Orden",
                pieza.material.nombre if pieza.material else "Sin Material",
                pieza.presentacion.nombre_comercial if pieza.presentacion else "Sin Presentación",
                "Sí" if pieza.prioritario else "No",
                pieza.creado_por.nombre if pieza.creado_por else "Sin Usuario",
                pieza.fecha_creacion
            ])
        return response
    exportar_csv.short_description = "📂 Exportar CSV"

    def duplicar_pieza(self, request, queryset):
        """Duplica las piezas seleccionadas"""
        for obj in queryset:
            obj.pk = None
            obj.save()
    duplicar_pieza.short_description = "📝 Duplicar Pieza"


    
# --- Inline para vincular Procesos en Maquinas ---
class MaquinaProcesoInline(admin.TabularInline):
    model = MaquinaProceso
    extra = 1  # Permite añadir nuevas relaciones directamente
    autocomplete_fields = ["proceso"]  # Facilita la selección de procesos

# --- Inline para vincular Máquinas en Procesos ---
class ProcesoMaquinaInline(admin.TabularInline):
    model = MaquinaProceso
    extra = 1
    autocomplete_fields = ["maquina"]  # Facilita la selección de máquinas


@admin.register(Maquina)
class MaquinaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "estado")  
    list_filter = ("estado",)  
    search_fields = ("nombre",)  
    ordering = ("nombre",)  
    list_per_page = 25  
    readonly_fields = ("id",)  
    inlines = [MaquinaProcesoInline]  # Agrega el inline para mostrar procesos relacionados

    actions = ["exportar_csv", "duplicar_maquina"]  

    def exportar_csv(self, request, queryset):
        """ Exporta máquinas seleccionadas a un archivo CSV """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="maquinas.csv"'
        writer = csv.writer(response)
        writer.writerow(["ID", "Nombre", "Estado"])
        for maquina in queryset:
            writer.writerow([maquina.id, maquina.nombre, maquina.estado])
        return response
    exportar_csv.short_description = "📂 Exportar CSV"

    def duplicar_maquina(self, request, queryset):
        """ Duplica las máquinas seleccionadas """
        for obj in queryset:
            obj.pk = None  
            obj.save()
    duplicar_maquina.short_description = "📝 Duplicar Máquina"


@admin.register(Proceso)
class ProcesoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "tipo", "area")  
    list_filter = ("tipo",)  
    search_fields = ("nombre",)  
    ordering = ("nombre",)  
    list_per_page = 25  
    readonly_fields = ("id",)  
    inlines = [ProcesoMaquinaInline]  # Agrega el inline para mostrar máquinas relacionadas

    actions = ["exportar_csv", "duplicar_proceso"]  

    def exportar_csv(self, request, queryset):
        """ Exporta procesos seleccionados a un archivo CSV """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="procesos.csv"'
        writer = csv.writer(response)
        writer.writerow(["ID", "Nombre", "Tipo"])
        for proceso in queryset:
            writer.writerow([proceso.id, proceso.nombre, proceso.tipo])
        return response
    exportar_csv.short_description = "📂 Exportar CSV"

    def duplicar_proceso(self, request, queryset):
        """ Duplica los procesos seleccionados """
        for obj in queryset:
            obj.pk = None  
            obj.save()
    duplicar_proceso.short_description = "📝 Duplicar Proceso"


@admin.register(MaquinaProceso)
class MaquinaProcesoAdmin(admin.ModelAdmin):
    list_display = ("id", "maquina", "proceso")  
    list_filter = ("maquina", "proceso")  
    search_fields = ("maquina__nombre", "proceso__nombre")  
    ordering = ("maquina",)  
    list_per_page = 25  
    list_select_related = ("maquina", "proceso")  
    readonly_fields = ("id",)  

    actions = ["exportar_csv", "duplicar_maquina_proceso"]  

    def exportar_csv(self, request, queryset):
        """ Exporta las relaciones máquina-proceso seleccionadas a un archivo CSV """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="maquina_proceso.csv"'
        writer = csv.writer(response)
        writer.writerow(["ID", "Máquina", "Proceso"])
        for relacion in queryset:
            writer.writerow([relacion.id, relacion.maquina.nombre, relacion.proceso.nombre])
        return response
    exportar_csv.short_description = "📂 Exportar CSV"

    def duplicar_maquina_proceso(self, request, queryset):
        """ Duplica las relaciones seleccionadas """
        for obj in queryset:
            obj.pk = None  
            obj.save()
    duplicar_maquina_proceso.short_description = "📝 Duplicar Relación Máquina-Proceso"
    
@admin.register(TratamientoCalidad)
class TratamientoCalidadAdmin(admin.ModelAdmin):
    list_display = (
        "nombre", 
        "get_tipo_material_display", 
        "get_tipo_tratamiento_display", 
        "descripcion_corta",
    )
    list_filter = ("tipo_material", "tipo_tratamiento")
    search_fields = ("nombre", "descripcion")
    ordering = ("nombre",)
    list_per_page = 25
    readonly_fields = ("id",)
    actions = ["exportar_csv"]

    def descripcion_corta(self, obj):
        return (obj.descripcion[:40] + "...") if obj.descripcion and len(obj.descripcion) > 40 else obj.descripcion
    descripcion_corta.short_description = "Descripción"

    def exportar_csv(self, request, queryset):
        """ Exporta los tratamientos de calidad a un archivo CSV """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="tratamientos_calidad.csv"'
        writer = csv.writer(response)
        writer.writerow([
            "ID", "Nombre", "Tipo de Material", 
            "Tipo de Tratamiento", "Descripción"
        ])
        for obj in queryset:
            writer.writerow([
                obj.id,
                obj.nombre,
                obj.get_tipo_material_display(),
                obj.get_tipo_tratamiento_display(),
                obj.descripcion or "",
            ])
        return response
    exportar_csv.short_description = "📥 Exportar como CSV"
    
@admin.register(AsignacionProceso)
class AsignacionProcesoAdmin(admin.ModelAdmin):
    list_display = ("id", "proceso", "pieza", "nesteo", "usuario", "estado", "prioridad", "fecha_asignacion")  
    list_filter = ("proceso", "usuario", "estado", "prioridad")  
    search_fields = ("pieza__consecutivo", "usuario__nombre")  
    ordering = ("-fecha_asignacion", "prioridad")  
    list_per_page = 25  
    list_select_related = ("proceso", "pieza", "usuario")  

    readonly_fields = ("id", )  

    actions = ["exportar_csv", "duplicar_asignacion"]  

    def exportar_csv(self, request, queryset):
        """ Exporta las asignaciones seleccionadas a un archivo CSV """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="asignaciones_proceso.csv"'
        writer = csv.writer(response)
        writer.writerow(["ID", "Proceso", "Pieza", "Usuario", "Estado", "Prioridad", "Fecha de Asignación"])
        for asignacion in queryset:
            writer.writerow([
                asignacion.id,
                asignacion.proceso.nombre if asignacion.proceso else "Sin Proceso",
                asignacion.pieza.consecutivo if asignacion.pieza else "Sin Pieza",
                asignacion.usuario.nombre if asignacion.usuario else "Sin Usuario",
                asignacion.estado,
                asignacion.prioridad,
                asignacion.fecha_asignacion
            ])
        return response
    exportar_csv.short_description = "📂 Exportar CSV"
    
    def save_model(self, request, obj, form, change):
        try:
            obj.full_clean()  # Ejecuta clean() y validaciones de modelo
            super().save_model(request, obj, form, change)
        except ValidationError as e:
            self.message_user(request, f"❌ Error al guardar: {e}", level=messages.ERROR)
            
    def duplicar_asignacion(self, request, queryset):
        """ Duplica las asignaciones seleccionadas """
        for obj in queryset:
            obj.pk = None  
            obj.save()
    duplicar_asignacion.short_description = "📝 Duplicar Asignación"
    
    

@admin.register(InventarioMaterial)
class InventarioMaterialAdmin(admin.ModelAdmin):
    list_display = ("id", "material", "cantidad_disponible", "ubicacion")  
    list_filter = ("material", "ubicacion")  
    search_fields = ("material__nombre", "ubicacion")  
    ordering = ("material",)  
    list_per_page = 25  
    list_select_related = ("material",)  

    readonly_fields = ("id",)  

    actions = ["exportar_csv", "duplicar_inventario"]  

    def exportar_csv(self, request, queryset):
        """ Exporta el inventario seleccionado a un archivo CSV """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="inventario_materiales.csv"'
        writer = csv.writer(response)
        writer.writerow(["ID", "Material", "Cantidad Disponible", "Ubicación"])
        for item in queryset:
            writer.writerow([
                item.id,
                item.material.nombre if item.material else "Sin Material",
                item.cantidad_disponible,
                item.ubicacion
            ])
        return response
    exportar_csv.short_description = "📂 Exportar CSV"

    def duplicar_inventario(self, request, queryset):
        """ Duplica los registros seleccionados en el inventario """
        for obj in queryset:
            obj.pk = None  
            obj.save()
    duplicar_inventario.short_description = "📝 Duplicar Inventario"
    

# --- Inline para gestionar las piezas dentro de un nesteo ---
class PiezaNesteoInline(admin.TabularInline):
    model = PiezaNesteo
    extra = 1  # Permite agregar nuevas piezas fácilmente desde Nesteo
    autocomplete_fields = ["pieza"]  # Facilita la selección de piezas

@admin.register(Nesteo)
class NesteoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre_placa", "material", "descripcion", "activo")  
    list_filter = ("material", "activo")  
    search_fields = ("nombre_placa", "material__nombre")  
    ordering = ("nombre_placa",)  
    list_per_page = 25  
    list_select_related = ("material",)  
    inlines = [PiezaNesteoInline]  # 🔥 Agrega las piezas vinculadas dentro del admin de Nesteo

    readonly_fields = ("id",)  

    actions = ["exportar_csv", "duplicar_nesteo", "restaurar_nesteo"]  

    def get_queryset(self, request):
        """ Sobrescribimos para ocultar los registros inactivos por defecto """
        return super().get_queryset(request).filter(activo=True)

    def delete_queryset(self, request, queryset):
        """ Realiza un borrado lógico en lugar de eliminar físicamente """
        queryset.update(activo=False)

    def exportar_csv(self, request, queryset):
        """ Exporta los nesteos seleccionados a un archivo CSV """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="nesteos.csv"'
        writer = csv.writer(response)
        writer.writerow(["ID", "Nombre Placa", "Material", "Descripción", "Activo"])
        for item in queryset:
            writer.writerow([
                item.id,
                item.nombre_placa,
                item.material.nombre if item.material else "Sin Material",
                item.descripcion if item.descripcion else "Sin Descripción",
                "Sí" if item.activo else "No"
            ])
        return response
    exportar_csv.short_description = "📂 Exportar CSV"

    def duplicar_nesteo(self, request, queryset):
        """ Duplica los registros seleccionados en nesteos """
        for obj in queryset:
            obj.pk = None  
            obj.save()
    duplicar_nesteo.short_description = "📝 Duplicar Nesteo"

    def restaurar_nesteo(self, request, queryset):
        """ Restaura registros previamente desactivados """
        queryset.update(activo=True)
    restaurar_nesteo.short_description = "🔄 Restaurar Nesteo"


@admin.register(PiezaNesteo)
class PiezaNesteoAdmin(admin.ModelAdmin):
    list_display = ("id", "pieza", "nesteo", "cantidad", "estado", "fecha_asignacion")  
    list_filter = ("nesteo", "estado")  
    search_fields = ("pieza__consecutivo", "nesteo__nombre_placa")  
    ordering = ("-fecha_asignacion",)  
    list_per_page = 25  
    list_select_related = ("pieza", "nesteo")  

    readonly_fields = ("id", "fecha_asignacion")  

    actions = ["exportar_csv", "duplicar_asignacion"]  

    def exportar_csv(self, request, queryset):
        """ Exporta las asignaciones de piezas a nesteos seleccionadas a un archivo CSV """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="pieza_nesteo.csv"'
        writer = csv.writer(response)
        writer.writerow(["ID", "Pieza", "Nesteo", "Cantidad", "Estado", "Fecha de Asignación"])
        for asignacion in queryset:
            writer.writerow([
                asignacion.id,
                asignacion.pieza.consecutivo if asignacion.pieza else "Sin Pieza",
                asignacion.nesteo.nombre_placa if asignacion.nesteo else "Sin Nesteo",
                asignacion.cantidad,
                asignacion.estado,
                asignacion.fecha_asignacion
            ])
        return response
    exportar_csv.short_description = "📂 Exportar CSV"

    def duplicar_asignacion(self, request, queryset):
        """ Duplica las asignaciones seleccionadas """
        for obj in queryset:
            obj.pk = None  
            obj.save()
    duplicar_asignacion.short_description = "📝 Duplicar Asignación"
    

@admin.register(EtapaCalidad)
class EtapaCalidadAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "descripcion")  
    search_fields = ("nombre",)  
    ordering = ("nombre",)  
    list_per_page = 25  

    readonly_fields = ("id",)  

    actions = ["exportar_csv", "duplicar_etapa"]  

    def exportar_csv(self, request, queryset):
        """ Exporta las etapas de calidad seleccionadas a un archivo CSV """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="etapas_calidad.csv"'
        writer = csv.writer(response)
        writer.writerow(["ID", "Nombre", "Descripción"])
        for item in queryset:
            writer.writerow([
                item.id,
                item.nombre,
                item.descripcion
            ])
        return response
    exportar_csv.short_description = "📂 Exportar CSV"

    def duplicar_etapa(self, request, queryset):
        """ Duplica las etapas seleccionadas """
        for obj in queryset:
            obj.pk = None  
            obj.save()
    duplicar_etapa.short_description = "📝 Duplicar Etapa de Calidad"

@admin.register(FlujoCalidad)
class FlujoCalidadAdmin(admin.ModelAdmin):
    list_display = ("id", "pieza", "etapa_calidad", "estado", "piezas_asignadas", "piezas_liberadas", "fecha_inicio")  
    list_filter = ("estado", "etapa_calidad")  
    search_fields = ("pieza__consecutivo", "etapa_calidad__nombre")  
    ordering = ("-fecha_inicio",)  
    list_per_page = 25  
    list_select_related = ("pieza", "etapa_calidad")  

    readonly_fields = ("id",)  

    actions = ["exportar_csv", "duplicar_flujo"]  

    def exportar_csv(self, request, queryset):
        """ Exporta los flujos de calidad seleccionados a un archivo CSV """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="flujos_calidad.csv"'
        writer = csv.writer(response)
        writer.writerow(["ID", "Pieza", "Etapa de Calidad", "Estado", "Piezas Asignadas", "Piezas Liberadas", "Fecha de Inicio", "Fecha de Finalización"])
        for flujo in queryset:
            writer.writerow([
                flujo.id,
                flujo.pieza.consecutivo if flujo.pieza else "Sin Pieza",
                flujo.etapa_calidad.nombre if flujo.etapa_calidad else "Sin Etapa",
                flujo.estado,
                flujo.piezas_asignadas,
                flujo.piezas_liberadas,
                flujo.fecha_inicio,
                flujo.fecha_finalizacion if flujo.fecha_finalizacion else "En proceso"
            ])
        return response
    exportar_csv.short_description = "📂 Exportar CSV"

    def duplicar_flujo(self, request, queryset):
        """ Duplica los flujos de calidad seleccionados """
        for obj in queryset:
            obj.pk = None  
            obj.save()
    duplicar_flujo.short_description = "📝 Duplicar Flujo de Calidad"
    

@admin.register(ScrapCalidad)
class ScrapCalidadAdmin(admin.ModelAdmin):
    list_display = ("id", "pieza", "etapa_calidad", "cantidad_scrap", "motivo", "fecha_registro")  
    list_filter = ("etapa_calidad",)  
    search_fields = ("pieza__consecutivo", "etapa_calidad__nombre", "motivo")  
    ordering = ("-fecha_registro",)  
    list_per_page = 25  
    list_select_related = ("pieza", "etapa_calidad")  

    readonly_fields = ("id", "fecha_registro")  

    actions = ["exportar_csv", "duplicar_scrap"]  

    def exportar_csv(self, request, queryset):
        """ Exporta los registros de scrap de calidad seleccionados a un archivo CSV """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="scrap_calidad.csv"'
        writer = csv.writer(response)
        writer.writerow(["ID", "Pieza", "Etapa de Calidad", "Cantidad Scrap", "Motivo", "Fecha de Registro"])
        for scrap in queryset:
            writer.writerow([
                scrap.id,
                scrap.pieza.consecutivo if scrap.pieza else "Sin Pieza",
                scrap.etapa_calidad.nombre if scrap.etapa_calidad else "Sin Etapa",
                scrap.cantidad_scrap,
                scrap.motivo,
                scrap.fecha_registro
            ])
        return response
    exportar_csv.short_description = "📂 Exportar CSV"

    def duplicar_scrap(self, request, queryset):
        """ Duplica los registros de scrap seleccionados """
        for obj in queryset:
            obj.pk = None  
            obj.save()
    duplicar_scrap.short_description = "📝 Duplicar Registro de Scrap"
    

@admin.register(ProveedorTratamiento)
class ProveedorTratamientoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "tipo", "nombre_de_contacto", "correo_de_contacto", "telefono_de_contacto", "fecha_entrega_estimada", "unidad_de_tiempo")  
    list_filter = ("tipo",)  
    search_fields = ("nombre", "nombre_de_contacto", "correo_de_contacto")  
    ordering = ("nombre",)  
    list_per_page = 25  

    readonly_fields = ("id",)  

    actions = ["exportar_csv", "duplicar_proveedor"]  

    def exportar_csv(self, request, queryset):
        """ Exporta los registros de proveedores de tratamiento seleccionados a un archivo CSV """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="proveedores_tratamientos.csv"'
        writer = csv.writer(response)
        writer.writerow(["ID", "Nombre", "Tipo", "Nombre de Contacto", "Correo", "Teléfono", "Tiempo de Entrega", "Unidad de Tiempo"])
        for proveedor in queryset:
            writer.writerow([
                proveedor.id,
                proveedor.nombre,
                proveedor.tipo,
                proveedor.nombre_de_contacto,
                proveedor.correo_de_contacto,
                proveedor.telefono_de_contacto,
                proveedor.fecha_entrega_estimada,
                proveedor.unidad_de_tiempo
            ])
        return response
    exportar_csv.short_description = "📂 Exportar CSV"

    def duplicar_proveedor(self, request, queryset):
        """ Duplica los registros de proveedores seleccionados """
        for obj in queryset:
            obj.pk = None  
            obj.save()
    duplicar_proveedor.short_description = "📝 Duplicar Proveedor de Tratamiento"
    

@admin.register(AsignacionTratamientoCalidad)
class AsignacionTratamientoCalidadAdmin(admin.ModelAdmin):
    list_display = (
        "id", "pieza", "tratamiento", "proveedor",
        "fecha_salida", "fecha_entrega", "fecha_recepcion"
    )
    list_filter = ("tratamiento", "proveedor")
    search_fields = ("pieza__consecutivo", "proveedor__nombre", "tratamiento__nombre")
    ordering = ("-fecha_salida",)
    list_per_page = 25
    list_select_related = ("pieza", "proveedor", "tratamiento")
    readonly_fields = ("id",)

    actions = ["exportar_csv", "duplicar_tratamiento"]

    def exportar_csv(self, request, queryset):
        """ Exporta los registros seleccionados a CSV """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="tratamientos_calidad.csv"'
        writer = csv.writer(response)
        writer.writerow([
            "ID", "Pieza", "Tratamiento", "Proveedor",
            "Fecha de Salida", "Fecha de Entrega", "Fecha de Recepción"
        ])
        for tratamiento in queryset:
            writer.writerow([
                tratamiento.id,
                tratamiento.pieza.consecutivo if tratamiento.pieza else "Sin Pieza",
                tratamiento.tratamiento.nombre if tratamiento.tratamiento else "Sin Tratamiento",
                tratamiento.proveedor.nombre if tratamiento.proveedor else "Sin Proveedor",
                tratamiento.fecha_salida,
                tratamiento.fecha_entrega or "Pendiente",
                tratamiento.fecha_recepcion or "Pendiente"
            ])
        return response
    exportar_csv.short_description = "📂 Exportar CSV"

    def duplicar_tratamiento(self, request, queryset):
        """ Duplica los tratamientos seleccionados """
        for obj in queryset:
            obj.pk = None
            obj.save()
    duplicar_tratamiento.short_description = "📝 Duplicar Tratamiento de Calidad"
    

class EstanteProduccionInline(admin.TabularInline):
    """ Permite administrar los estantes dentro de la vista de racks """
    model = EstanteProduccion
    extra = 1  # Muestra un campo vacío para agregar un nuevo estante
    min_num = 0
    can_delete = True
    fields = ("codigo_estante", "estado")
    show_change_link = True  # Permite editar el estante desde la vista del rack


@admin.register(RackProduccion)
class RackProduccionAdmin(admin.ModelAdmin):
    list_display = ("id", "codigo_rack", "ubicacion", "estado")  
    list_display_links = ["codigo_rack"]  # Permite editar haciendo clic en el código del rack
    list_filter = ("estado",)  
    search_fields = ("codigo_rack", "ubicacion")  
    ordering = ("codigo_rack",)  
    list_per_page = 25  
    inlines = [EstanteProduccionInline]  # Relaciona estantes dentro de la vista del rack

    readonly_fields = ("id",)  

    actions = ["exportar_csv", "duplicar_rack"]  

    def exportar_csv(self, request, queryset):
        """ Exporta los registros de racks seleccionados a un archivo CSV """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="racks.csv"'
        writer = csv.writer(response)
        writer.writerow(["ID", "Código Rack", "Ubicación", "Estado"])
        for rack in queryset:
            writer.writerow([
                rack.id,
                rack.codigo_rack,
                rack.ubicacion,
                rack.estado,
            ])
        return response
    exportar_csv.short_description = "📂 Exportar CSV"

    def duplicar_rack(self, request, queryset):
        """ Duplica los registros de racks seleccionados """
        for obj in queryset:
            obj.pk = None  
            obj.save()
    duplicar_rack.short_description = "📝 Duplicar Rack"
    

@admin.register(EstanteProduccion)
class EstanteProduccionAdmin(admin.ModelAdmin):
    list_display = ("id", "codigo_estante", "rack", "estado")  
    list_filter = ("estado", "rack")  
    search_fields = ("codigo_estante", "rack__codigo_rack")  
    ordering = ("codigo_estante",)  
    list_per_page = 25  
    list_select_related = ("rack",)  

    readonly_fields = ("id",)  

    actions = ["exportar_csv", "duplicar_estante"]  

    def exportar_csv(self, request, queryset):
        """ Exporta los registros de estantes seleccionados a un archivo CSV """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="estantes_produccion.csv"'
        writer = csv.writer(response)
        writer.writerow(["ID", "Código Estante", "Rack", "Estado"])
        for estante in queryset:
            writer.writerow([
                estante.id,
                estante.codigo_estante,
                estante.rack.codigo_rack if estante.rack else "Sin Rack",
                estante.estado
            ])
        return response
    exportar_csv.short_description = "📂 Exportar CSV"

    def duplicar_estante(self, request, queryset):
        """ Duplica los registros de estantes seleccionados """
        for obj in queryset:
            obj.pk = None  
            obj.save()
    duplicar_estante.short_description = "📝 Duplicar Estante"
    

@admin.register(UbicacionPieza)
class UbicacionPiezaAdmin(admin.ModelAdmin):
    list_display = ("id", "pieza", "estante", "cantidad", "fecha_registro", "fecha_salida", "responsable")  
    list_filter = ("fecha_registro", "fecha_salida", "responsable")  
    search_fields = ("pieza__consecutivo", "estante__codigo_estante", "responsable__nombre")  
    ordering = ("-fecha_registro",)  
    list_per_page = 25  
    list_select_related = ("pieza", "estante", "responsable")  
    autocomplete_fields = ["responsable"]  # Permite búsqueda más rápida en usuarios

    readonly_fields = ("id", "fecha_registro")  

    actions = ["exportar_csv", "duplicar_ubicacion"]  

    def exportar_csv(self, request, queryset):
        """ Exporta los registros de ubicaciones de piezas seleccionados a un archivo CSV """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="ubicaciones_piezas.csv"'
        writer = csv.writer(response)
        writer.writerow(["ID", "Pieza", "Estante", "Cantidad", "Fecha Registro", "Fecha Salida", "Responsable"])
        for ubicacion in queryset:
            writer.writerow([
                ubicacion.id,
                ubicacion.pieza.consecutivo if ubicacion.pieza else "Sin Pieza",
                ubicacion.estante.codigo_estante if ubicacion.estante else "Sin Estante",
                ubicacion.cantidad,
                ubicacion.fecha_registro,
                ubicacion.fecha_salida if ubicacion.fecha_salida else "No ha salido",
                ubicacion.responsable.nombre if ubicacion.responsable else "Sin Responsable"
            ])
        return response
    exportar_csv.short_description = "📂 Exportar CSV"

    def duplicar_ubicacion(self, request, queryset):
        """ Duplica los registros de ubicaciones de piezas seleccionados """
        for obj in queryset:
            obj.pk = None  
            obj.save()
    duplicar_ubicacion.short_description = "📝 Duplicar Ubicación"


class OtrasMaquinasDelUsuarioInline(admin.TabularInline):
    model = PersonalMaquina
    extra = 0
    verbose_name = "Máquina también asignada"
    verbose_name_plural = "Otras máquinas asignadas a este usuario"
    fields = ("maquina",)
    readonly_fields = ("maquina",)
    can_delete = False
    show_change_link = False

    def get_queryset(self, request):
        # Evita que intente usar el queryset general
        return super().get_queryset(request).none()

    def has_add_permission(self, request, obj=None):
        return False

# Inlines

class PersonalMaquinaInline(admin.TabularInline):
    model = PersonalMaquina
    extra = 1
    autocomplete_fields = ["maquina"]
    fields = ("maquina",)
    verbose_name = "Máquina asignada"
    verbose_name_plural = "Máquinas asignadas"
    show_change_link = True


@admin.register(PersonalMaquina)
class PersonalMaquinaAdmin(admin.ModelAdmin):
    list_display = ("id", "personal", "maquina")
    list_filter = ("maquina", "personal")
    search_fields = ("personal__nombre", "maquina__nombre")
    ordering = ("personal",)
    list_per_page = 25
    list_select_related = ("personal", "maquina")
    readonly_fields = ("id",)

    actions = ["exportar_csv", "duplicar_asignacion"]

    def exportar_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="personal_maquina.csv"'
        writer = csv.writer(response)
        writer.writerow(["ID", "Personal", "Máquina"])
        for asignacion in queryset:
            writer.writerow([
                asignacion.id,
                asignacion.personal.nombre if asignacion.personal else "Sin Usuario",
                asignacion.maquina.nombre if asignacion.maquina else "Sin Máquina",
            ])
        return response
    exportar_csv.short_description = "📂 Exportar CSV"

    def duplicar_asignacion(self, request, queryset):
        for obj in queryset:
            obj.pk = None
            obj.save()
    duplicar_asignacion.short_description = "📄 Duplicar Asignación"


class HorarioProduccionInline(admin.TabularInline):
    """
    Muestra los horarios de producción directamente en la vista del usuario.
    """
    model = HorarioProduccion
    extra = 1
    min_num = 0
    max_num = 7  # Como máximo 7 días (uno por día de la semana)
    autocomplete_fields = ["usuario"]
    fields = (
        "dia",
        "hora_entrada",
        "hora_salida",
        "tiene_horario_comida",
        "hora_comida_inicio",
        "hora_comida_fin",
    )
    readonly_fields = ("id",)
    verbose_name = "Horario de Producción"
    verbose_name_plural = "Horarios de Producción"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("usuario")

@admin.register(HorarioProduccion)
class HorarioProduccionAdmin(admin.ModelAdmin):
    """
    Admin detallado del modelo HorarioProduccion.
    """
    list_display = (
        "id",
        "usuario",
        "dia",
        "hora_entrada",
        "hora_salida",
        "tiene_horario_comida",
        "hora_comida_inicio",
        "hora_comida_fin",
    )
    list_filter = ("dia", "tiene_horario_comida")
    search_fields = ("usuario__nombre", "usuario__correo")
    autocomplete_fields = ["usuario"]
    ordering = ("usuario", "dia")
    readonly_fields = ("id",)
    list_select_related = ("usuario",)
    list_per_page = 25

    fieldsets = (
        ("Información General", {
            "fields": (
                "usuario",
                "dia",
            )
        }),
        ("Horario de Trabajo", {
            "fields": (
                "hora_entrada",
                "hora_salida",
            )
        }),
        ("Horario de Comida (si aplica)", {
            "fields": (
                "tiene_horario_comida",
                "hora_comida_inicio",
                "hora_comida_fin",
            )
        }),
    )

    actions = ["exportar_csv"]

    def exportar_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="horarios_produccion.csv"'
        writer = csv.writer(response)
        writer.writerow([
            "ID", "Usuario", "Día", "Hora Entrada", "Hora Salida",
            "Tiene Comida", "Inicio Comida", "Fin Comida"
        ])
        for h in queryset:
            writer.writerow([
                h.id,
                h.usuario.nombre if h.usuario else "Sin usuario",
                h.get_dia_display(),
                h.hora_entrada,
                h.hora_salida,
                "Sí" if h.tiene_horario_comida else "No",
                h.hora_comida_inicio if h.tiene_horario_comida else "N/A",
                h.hora_comida_fin if h.tiene_horario_comida else "N/A"
            ])
        return response
    exportar_csv.short_description = "📂 Exportar Horarios a CSV"