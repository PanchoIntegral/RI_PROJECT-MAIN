from django.forms import ValidationError
from rest_framework import serializers
from ri_compras.models import  Usuarios
from ri_compras.serializer import SimpleUsuariosSerializer
from ri_produccion.models import AsignacionProceso, Espesor, EstanteProduccion, EtapaCalidad, FlujoCalidad, HorarioProduccion, InventarioMaterial, Maquina, MaquinaProceso, Material, Nesteo, OrdenProduccion, PersonalMaquina, Pieza, PiezaNesteo, PresentacionMaterial, Proceso, ProveedorTratamiento, RackProduccion, ScrapCalidad, AsignacionTratamientoCalidad, TratamientoCalidad, UbicacionPieza



class EspesorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Espesor
        fields = "__all__"
        extra_kwargs = {
            "nombre_comercial": {
                "error_messages": {
                    "unique": "Ya existe un espesor con este nombre comercial.",
                    "required": "El nombre comercial es obligatorio.",
                }
            },
            "valor_pulgadas": {
                "error_messages": {
                    "required": "El valor en pulgadas es obligatorio.",
                    "invalid": "El valor debe ser numérico (decimal)."
                }
            },
        }

    def validate(self, data):
        """ Validación para evitar duplicados """
        if Espesor.objects.filter(
            nombre_comercial=data["nombre_comercial"],
            valor_pulgadas=data["valor_pulgadas"]
        ).exists():
            raise serializers.ValidationError(
                "Ya existe un espesor con este nombre comercial y valor en pulgadas."
            )
        return data
    

class PresentacionMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = PresentacionMaterial
        fields = "__all__"
        extra_kwargs = {
            "nombre_comercial": {"error_messages": {"required": "El nombre es obligatorio."}},
        }

    def validate(self, data):
        """
        Validaciones adicionales:
        - Asegurar que al menos uno de los campos físicos está presente.
        - Evitar nombres duplicados (si es necesario).
        """
        if not any([
            data.get("largo"),
            data.get("ancho"),
            data.get("diametro"),
            data.get("espesor")
        ]):
            raise serializers.ValidationError(
                "Debe especificar al menos una dimensión física o el espesor."
            )

        return data

## Serializer de materiales
class MaterialSerializer(serializers.ModelSerializer):

    class Meta:
        model = Material
        fields = ["id", "nombre", "tipo",]
        read_only_fields = ["id"]
        extra_kwargs = {
            "nombre": {"error_messages": {"unique": "Este material ya existe."}},
            "tipo": {"error_messages": {"invalid_choice": "Selecciona un tipo válido."}},
        }

    def validate_tipo(self, value):
        """ Valida que el tipo de material sea uno de los permitidos """
        tipos_validos = dict(Material.TIPO_OPCIONES).keys()
        if value not in tipos_validos:
            raise serializers.ValidationError(f"Tipo no válido. Usa: {', '.join(tipos_validos)}")
        return value


class OrdenProduccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdenProduccion
        fields = ["id", "codigo_orden", "fecha_creacion", "estado"]
        read_only_fields = ["id", "fecha_creacion"]  # Evita modificaciones en estos campos
        extra_kwargs = {
            "codigo_orden": {"error_messages": {"unique": "Este código de orden ya existe."}},
            "estado": {"error_messages": {"invalid_choice": "Selecciona un estado válido."}},
        }

    def validate_codigo_orden(self, value):
        """Valida que el código de orden solo contenga números, espacios y guiones"""
        cleaned_value = value.replace(" ", "").replace("-", "")
        if not cleaned_value.isdigit():
            raise serializers.ValidationError(
                "El código de orden solo puede contener números, espacios y guiones."
            )
        return value

    def validate_estado(self, value):
        """ Valida que el estado sea uno de los permitidos """
        estados_validos = dict(OrdenProduccion.ESTADO_OPCIONES).keys()
        if value not in estados_validos:
            raise serializers.ValidationError(f"Estado no válido. Usa: {', '.join(estados_validos)}")
        return value
    

class PiezaSerializer(serializers.ModelSerializer):
    pdf = serializers.FileField(required=False, allow_null=True)

    orden_produccion = serializers.PrimaryKeyRelatedField(
        queryset=OrdenProduccion.objects.all(),
        required=False,
        allow_null=True
    )
    orden_produccion_detalle = serializers.SerializerMethodField()

    material = serializers.PrimaryKeyRelatedField(
        queryset=Material.objects.all(),
        required=False,
        allow_null=True
    )
    material_detalle = serializers.SerializerMethodField()

    presentacion = serializers.PrimaryKeyRelatedField(
        queryset=PresentacionMaterial.objects.all(),
        required=False,
        allow_null=True
    )
    presentacion_detalle = serializers.SerializerMethodField()

    creado_por = serializers.PrimaryKeyRelatedField(
        queryset=Usuarios.objects.all(),
        required=False,
        allow_null=True
    )
    creado_por_detalle = serializers.SerializerMethodField()

    class Meta:
        model = Pieza
        fields = [
            "id", "consecutivo", "orden_produccion", "orden_produccion_detalle",
            "material", "material_detalle", "presentacion", "presentacion_detalle",
            "total_piezas", "piezas_por_consecutivo", "piezas_manufacturadas",
            "pdf", "fecha_creacion", "creado_por", "creado_por_detalle",
            "prioritario", "estatus_tracking", "estado_produccion",
            "requiere_nesteo", "retrabajo", "comentario_retrabajo","comentario_scrap", "asignacionFinalizada", "es_scrap", "scrap_piezas",
        ]
        read_only_fields = ["id", "fecha_creacion"]

    def get_orden_produccion_detalle(self, obj):
        if obj.orden_produccion:
            return {
                "id": obj.orden_produccion.id,
                "codigo_orden": obj.orden_produccion.codigo_orden,
                "estado": obj.orden_produccion.estado
            }
        return None

    def get_creado_por_detalle(self, obj):
        if obj.creado_por:
            return {
                "id": obj.creado_por.id,
                "nombre": obj.creado_por.nombre,
                "correo": obj.creado_por.correo
            }
        return None

    def get_presentacion_detalle(self, obj):
        if obj.presentacion:
            return {
                "id": obj.presentacion.id,
                "nombre_comercial": obj.presentacion.nombre_comercial,
                "largo": obj.presentacion.largo,
                "ancho": obj.presentacion.ancho,
                "diametro": obj.presentacion.diametro,
                "espesor": obj.presentacion.espesor.id if obj.presentacion.espesor else None
            }
        return None
    
    def get_material_detalle(self, obj):
        """ Devuelve detalles del material si existe """
        if obj.material:
            return {"id": obj.material.id, "nombre": obj.material.nombre, "tipo": obj.material.tipo}
        return None


class ProcesoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proceso
        fields = ["id", "nombre", "tipo", "area"]
        read_only_fields = ["id"]
        extra_kwargs = {
            "nombre": {"error_messages": {"unique": "Este proceso ya existe."}},
            "tipo": {"error_messages": {"invalid_choice": "Selecciona un tipo válido."}},
        }

    def validate_nombre(self, value):
        """ Valida que el nombre solo contenga caracteres válidos """
        if not value.replace(" ", "").isalnum():
            raise serializers.ValidationError("El nombre solo puede contener letras y números.")
        return value

    def validate_tipo(self, value):
        """ Valida que el tipo de proceso sea uno de los permitidos """
        tipos_validos = dict(Proceso.TIPO_OPCIONES).keys()
        if value not in tipos_validos:
            raise serializers.ValidationError(f"Tipo no válido. Usa: {', '.join(tipos_validos)}")
        return value
    

class MaquinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Maquina
        fields = ["id", "nombre", "estado"]
        read_only_fields = ["id"]
        extra_kwargs = {
            "nombre": {"error_messages": {"unique": "Este nombre de máquina ya existe."}},
            "estado": {"error_messages": {"invalid_choice": "Selecciona un estado válido."}},
        }

    def validate_nombre(self, value):
        """ Valida que el nombre solo contenga caracteres válidos """
        if not value.replace(" ", "").isalnum():
            raise serializers.ValidationError("El nombre solo puede contener letras y números.")
        return value

    def validate_estado(self, value):
        """ Valida que el estado de la máquina sea uno de los permitidos """
        estados_validos = dict(Maquina.ESTADO_OPCIONES).keys()
        if value not in estados_validos:
            raise serializers.ValidationError(f"Estado no válido. Usa: {', '.join(estados_validos)}")
        return value
    
    

class MaquinaProcesoSerializer(serializers.ModelSerializer):
    maquina = serializers.PrimaryKeyRelatedField(
        queryset=Maquina.objects.all(),
        required=True
    )
    proceso = serializers.PrimaryKeyRelatedField(
        queryset=Proceso.objects.all(),
        required=True
    )
    maquina_detalle = serializers.SerializerMethodField()
    proceso_detalle = serializers.SerializerMethodField()

    class Meta:
        model = MaquinaProceso
        fields = ["id", "maquina", "maquina_detalle", "proceso", "proceso_detalle"]
        read_only_fields = ["id"]

    def get_maquina_detalle(self, obj):
        """ Devuelve detalles de la máquina si existe """
        if obj.maquina:
            return {"id": obj.maquina.id, "nombre": obj.maquina.nombre, "estado": obj.maquina.estado}
        return None

    def get_proceso_detalle(self, obj):
        """ Devuelve detalles del proceso si existe """
        if obj.proceso:
            return {"id": obj.proceso.id, "nombre": obj.proceso.nombre, "tipo": obj.proceso.tipo}
        return None

    def validate(self, data):
        """ Validación para evitar registros duplicados """
        if MaquinaProceso.objects.filter(maquina=data["maquina"], proceso=data["proceso"]).exists():
            raise serializers.ValidationError("Esta relación entre máquina y proceso ya existe.")
        return data
    
    

class AsignacionProcesoSerializer(serializers.ModelSerializer):
    proceso = serializers.PrimaryKeyRelatedField(
        queryset=Proceso.objects.all(),
        required=True
    )
    pieza = serializers.PrimaryKeyRelatedField(
        queryset=Pieza.objects.all(),
        required=False,
        allow_null=True
    )
    usuario = serializers.PrimaryKeyRelatedField(
        queryset=Usuarios.objects.all(),  # Filtra solo usuarios con rol OPERADOR
        required=False,
        allow_null=True
    )
    nesteo = serializers.PrimaryKeyRelatedField(
        queryset=Nesteo.objects.all(),
        required=False,
        allow_null=True
    )
    proceso_detalle = serializers.SerializerMethodField()
    pieza_detalle = serializers.SerializerMethodField()
    usuario_detalle = serializers.SerializerMethodField()
    nesteo_detalle = serializers.SerializerMethodField()
    maquina_detalle = serializers.SerializerMethodField()

    class Meta:
        model = AsignacionProceso
        fields = [
            "id", "proceso", "proceso_detalle", "pieza", "pieza_detalle", 
            "usuario", "usuario_detalle", "nesteo", "nesteo_detalle", "maquina", "maquina_detalle", "estado", "piezas_asignadas", 
            "piezas_liberadas", "piezas_scrap", "tiempo_realizacion_min", 
            "fecha_asignacion", "fecha_inicio", "fecha_finalizacion_estimada", 
            "fecha_finalizacion_real", "pre_asignado", "prioridad",
        ]
        read_only_fields = ["id", "fecha_asignacion"]

    def get_proceso_detalle(self, obj):
        """ Devuelve detalles del proceso si existe """
        if obj.proceso:
            return {"id": obj.proceso.id, "nombre": obj.proceso.nombre, "tipo": obj.proceso.tipo, "area": obj.proceso.area}
        return None

    def get_pieza_detalle(self, obj):
        """ Devuelve detalles de la pieza si existe """
        if obj.pieza:
            return {"id": obj.pieza.id, "consecutivo": obj.pieza.consecutivo}
        return None

    def get_usuario_detalle(self, obj):
        """ Devuelve detalles del usuario si existe """
        if obj.usuario:
            return {"id": obj.usuario.id, "nombre": obj.usuario.nombre, "rol": obj.usuario.rol}
        return None
    
    def get_nesteo_detalle(self, obj):
        """ Devuelve detalles del nesteo si existe """
        if obj.nesteo:
            return {"id": obj.nesteo.id, "nombre": obj.nesteo.nombre_placa}
        return None
    
    def get_maquina_detalle(self, obj):
        """ Devuelve detalles de la maquina si existe """
        if obj.maquina:
            return {"id": obj.maquina.id, "nombre": obj.maquina.nombre, "estado": obj.maquina.estado}
        return None
    
    def validate(self, data):
        proceso = data.get('proceso')

        # Si el proceso es de tipo 'Individual', nos aseguramos de que no se asigne a un nesteo.
        if proceso and proceso.tipo == 'Individual':
            # Si se envió un `nesteo`, lo ignoramos para evitar el error y el comportamiento no deseado.
            if 'nesteo' in data:
                data['nesteo'] = None
        
        # Si el proceso es de tipo 'Nesteo', nos aseguramos de que sí tenga un nesteo.
        elif proceso and proceso.tipo == 'Nesteo':
            if not data.get('nesteo'):
                raise serializers.ValidationError(
                    "Un proceso de tipo 'Nesteo' debe estar asignado a un nesteo."
                )

        # Construye una instancia parcial para validarla con `clean()`
        instance = AsignacionProceso(**data)
        if self.instance:
            instance.pk = self.instance.pk
            # Marcamos que es una actualización parcial
            instance._partial_update = self.partial

        try:
            instance.clean()
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else e.messages)

        return data


class InventarioMaterialSerializer(serializers.ModelSerializer):
    material = serializers.PrimaryKeyRelatedField(
        queryset=Material.objects.all(),
        required=True
    )
    material_detalle = serializers.SerializerMethodField()

    class Meta:
        model = InventarioMaterial
        fields = ["id", "material", "material_detalle", "cantidad_disponible", "ubicacion"]
        read_only_fields = ["id"]

    def get_material_detalle(self, obj):
        """ Devuelve detalles del material si existe """
        if obj.material:
            return {"id": obj.material.id, "nombre": obj.material.nombre, "tipo": obj.material.tipo}
        return None

    def validate_cantidad_disponible(self, value):
        """ Valida que la cantidad disponible no sea negativa """
        if value < 0:
            raise serializers.ValidationError("La cantidad disponible no puede ser negativa.")
        return value
    

class NesteoSerializer(serializers.ModelSerializer):
    material = serializers.PrimaryKeyRelatedField(
        queryset=Material.objects.all(),
        required=False,
        allow_null=True
    )
    material_detalle = serializers.SerializerMethodField()

    class Meta:
        model = Nesteo
        fields = ["id", "nombre_placa", "material", "material_detalle", "descripcion", "activo"]
        read_only_fields = ["id"]

    def get_material_detalle(self, obj):
        """ Devuelve detalles del material si existe """
        if obj.material:
            return {"id": obj.material.id, "nombre": obj.material.nombre, "tipo": obj.material.tipo}
        return None

    # def validate_nombre_placa(self, value):
    #     """ Valida que el nombre de la placa no tenga caracteres inválidos """
    #     if not value.replace(" ", "").isalnum():
    #         raise serializers.ValidationError("El nombre de la placa solo puede contener letras, números y espacios.")
    #     return value

    
class PiezaNesteoSerializer(serializers.ModelSerializer):
    pieza = serializers.PrimaryKeyRelatedField(
        queryset=Pieza.objects.all(),
        required=True
    )
    nesteo = serializers.PrimaryKeyRelatedField(
        queryset=Nesteo.objects.all(),
        required=True
    )
    pieza_detalle = serializers.SerializerMethodField(read_only=True)
    nesteo_detalle = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PiezaNesteo
        fields = [
            "id", "pieza", "pieza_detalle", "nesteo", "nesteo_detalle", 
            "cantidad", "estado", "fecha_asignacion", "asignacionFinalizada"
        ]
        read_only_fields = ["id", "fecha_asignacion"]

    def get_pieza_detalle(self, obj):
        """ Devuelve detalles de la pieza si existe """
        # Si 'obj' es un diccionario (datos validados), acceder por clave
        if isinstance(obj, dict):
            pieza_id = obj.get('pieza')
            if pieza_id:
                pieza = Pieza.objects.filter(id=pieza_id).first()
                return {"id": pieza.id, "consecutivo": pieza.consecutivo} if pieza else None
            return None
        # Si 'obj' es una instancia de PiezaNesteo
        if obj.pieza:
            return {"id": obj.pieza.id, "consecutivo": obj.pieza.consecutivo}
        return None

    def get_nesteo_detalle(self, obj):
        """ Devuelve detalles del nesteo si existe """
        if obj.nesteo:
            return {"id": obj.nesteo.id, "nombre_placa": obj.nesteo.nombre_placa}
        return None

    def validate_cantidad(self, value):
        """ Valida que la cantidad asignada sea mayor a 0 """
        if value <= 0:
            raise serializers.ValidationError("La cantidad asignada debe ser mayor a 0.")
        return value

    def validate_estado(self, value):
        """ Valida que el estado sea uno de los permitidos """
        estados_validos = dict(PiezaNesteo.ESTADO_OPCIONES).keys()
        if value not in estados_validos:
            raise serializers.ValidationError(f"Estado no válido. Usa: {', '.join(estados_validos)}")
        return value

class EtapaCalidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtapaCalidad
        fields = ["id", "nombre", "descripcion"]
        read_only_fields = ["id"]

    def validate_nombre(self, value):
        """ Valida que el nombre de la etapa sea único y sin caracteres inválidos """
        if not value.replace(" ", "").isalnum():
            raise serializers.ValidationError("El nombre solo puede contener letras, números y espacios.")
        return value
    
class FlujoCalidadSerializer(serializers.ModelSerializer):
    pieza = serializers.PrimaryKeyRelatedField(
        queryset=Pieza.objects.all(),
        required=True
    )
    etapa_calidad = serializers.PrimaryKeyRelatedField(
        queryset=EtapaCalidad.objects.all(),
        required=True
    )
    pieza_detalle = serializers.SerializerMethodField()
    etapa_calidad_detalle = serializers.SerializerMethodField()

    class Meta:
        model = FlujoCalidad
        fields = [
            "id", "pieza", "pieza_detalle", "etapa_calidad", "etapa_calidad_detalle",
            "estado", "piezas_asignadas", "piezas_liberadas", "fecha_inicio", "fecha_finalizacion"
        ]
        read_only_fields = ["id"]

    def get_pieza_detalle(self, obj):
        """ Devuelve detalles de la pieza si existe """
        if obj.pieza:
            return {"id": obj.pieza.id, "consecutivo": obj.pieza.consecutivo}
        return None

    def get_etapa_calidad_detalle(self, obj):
        """ Devuelve detalles de la etapa de calidad si existe """
        if obj.etapa_calidad:
            return {"id": obj.etapa_calidad.id, "nombre": obj.etapa_calidad.nombre}
        return None

    def validate_piezas_asignadas(self, value):
        """ Valida que las piezas asignadas sean mayores o iguales a 0 """
        if value < 0:
            raise serializers.ValidationError("El número de piezas asignadas no puede ser negativo.")
        return value

    def validate_piezas_liberadas(self, value):
        """ Valida que las piezas liberadas sean mayores o iguales a 0 """
        if value < 0:
            raise serializers.ValidationError("El número de piezas liberadas no puede ser negativo.")
        return value

    def validate_estado(self, value):
        """ Valida que el estado sea uno de los permitidos """
        estados_validos = dict(FlujoCalidad.ESTADO_OPCIONES).keys()
        if value not in estados_validos:
            raise serializers.ValidationError(f"Estado no válido. Usa: {', '.join(estados_validos)}")
        return value
    

class ScrapCalidadSerializer(serializers.ModelSerializer):
    pieza = serializers.PrimaryKeyRelatedField(
        queryset=Pieza.objects.all(),
        required=True
    )
    etapa_calidad = serializers.PrimaryKeyRelatedField(
        queryset=EtapaCalidad.objects.all(),
        required=True
    )
    pieza_detalle = serializers.SerializerMethodField()
    etapa_calidad_detalle = serializers.SerializerMethodField()

    class Meta:
        model = ScrapCalidad
        fields = [
            "id", "pieza", "pieza_detalle", "etapa_calidad", "etapa_calidad_detalle",
            "cantidad_scrap", "motivo", "fecha_registro"
        ]
        read_only_fields = ["id", "fecha_registro"]

    def get_pieza_detalle(self, obj):
        """ Devuelve detalles de la pieza si existe """
        if obj.pieza:
            return {"id": obj.pieza.id, "consecutivo": obj.pieza.consecutivo}
        return None

    def get_etapa_calidad_detalle(self, obj):
        """ Devuelve detalles de la etapa de calidad si existe """
        if obj.etapa_calidad:
            return {"id": obj.etapa_calidad.id, "nombre": obj.etapa_calidad.nombre}
        return None

    def validate_cantidad_scrap(self, value):
        """ Valida que la cantidad de scrap sea mayor o igual a 0 """
        if value < 0:
            raise serializers.ValidationError("El número de piezas en scrap no puede ser negativo.")
        return value

    def validate_motivo(self, value):
        """ Valida que el motivo del scrap no esté vacío """
        if not value.strip():
            raise serializers.ValidationError("El motivo del scrap no puede estar vacío.")
        return value


class ProveedorTratamientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProveedorTratamiento
        fields = [
            "id", "nombre", "tipo", "nombre_de_contacto",
            "correo_de_contacto", "telefono_de_contacto",
            "fecha_entrega_estimada", "unidad_de_tiempo"
        ]
        read_only_fields = ["id"]

    def validate_telefono_de_contacto(self, value):
        """ Valida que el número de teléfono sea correcto """
        import re
        if not re.match(r"^\+?\d{7,15}$", value):
            raise serializers.ValidationError("Número de teléfono inválido. Debe tener entre 7 y 15 dígitos.")
        return value

    def validate_fecha_entrega_estimada(self, value):
        """ Valida que el tiempo de entrega estimado sea positivo """
        if value <= 0:
            raise serializers.ValidationError("El tiempo de entrega estimado debe ser mayor a 0.")
        return value

    def validate_unidad_de_tiempo(self, value):
        """ Valida que la unidad de tiempo no esté vacía """
        if not value.strip():
            raise serializers.ValidationError("La unidad de tiempo no puede estar vacía.")
        return value

class TratamientoCalidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = TratamientoCalidad
        fields = [
            "id",
            "nombre",
            "tipo_material",
            "tipo_tratamiento",
            "descripcion",
        ]
        read_only_fields = ["id"]

    def validate_tipo_material(self, value):
        tipos_validos = dict(TratamientoCalidad.TIPO_MATERIAL_OPCIONES).keys()
        if value not in tipos_validos:
            raise serializers.ValidationError(
                f"Tipo de material no válido. Usa: {', '.join(tipos_validos)}"
            )
        return value

    def validate_tipo_tratamiento(self, value):
        tipos_validos = dict(TratamientoCalidad.TIPO_TRATAMIENTO_OPCIONES).keys()
        if value not in tipos_validos:
            raise serializers.ValidationError(
                f"Tipo de tratamiento no válido. Usa: {', '.join(tipos_validos)}"
            )
        return value
    
    
class AsignacionTratamientoCalidadSerializer(serializers.ModelSerializer):
    pieza = serializers.PrimaryKeyRelatedField(
        queryset=Pieza.objects.all(),
        required=True
    )
    proveedor = serializers.PrimaryKeyRelatedField(
        queryset=ProveedorTratamiento.objects.all(),
        required=False,
        allow_null=True
    )
    tratamiento = serializers.PrimaryKeyRelatedField(
        queryset=TratamientoCalidad.objects.all(),
        required=True
    )

    pieza_detalle = serializers.SerializerMethodField()
    proveedor_detalle = serializers.SerializerMethodField()
    tratamiento_detalle = serializers.SerializerMethodField()

    class Meta:
        model = AsignacionTratamientoCalidad
        fields = [
            "id", "pieza", "pieza_detalle", "tratamiento", "tratamiento_detalle",
            "proveedor", "proveedor_detalle", "fecha_salida", "fecha_entrega", "fecha_recepcion"
        ]
        read_only_fields = ["id"]

    def get_pieza_detalle(self, obj):
        if obj.pieza:
            return {"id": obj.pieza.id, "consecutivo": obj.pieza.consecutivo}
        return None

    def get_proveedor_detalle(self, obj):
        if obj.proveedor:
            return {"id": obj.proveedor.id, "nombre": obj.proveedor.nombre}
        return None

    def get_tratamiento_detalle(self, obj):
        if obj.tratamiento:
            return {
                "id": obj.tratamiento.id,
                "nombre": obj.tratamiento.nombre,
                "tipo_material": obj.tratamiento.tipo_material,
                "tipo_tratamiento": obj.tratamiento.tipo_tratamiento,
                "descripcion": obj.tratamiento.descripcion
            }
        return None

class RackProduccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RackProduccion
        fields = ["id", "codigo_rack", "ubicacion", "estado"]
        read_only_fields = ["id"]

    def validate_codigo_rack(self, value):
        """ Valida que el código del rack sea único y tenga un formato válido """
        if not value.strip():
            raise serializers.ValidationError("El código del rack no puede estar vacío.")
        return value


    def validate_estado(self, value):
        """ Valida que el estado del rack sea válido """
        estados_validos = dict(RackProduccion.ESTADO_OPCIONES).keys()
        if value not in estados_validos:
            raise serializers.ValidationError(f"Estado no válido. Usa: {', '.join(estados_validos)}")
        return value
    

class EstanteProduccionSerializer(serializers.ModelSerializer):
    rack = serializers.PrimaryKeyRelatedField(
        queryset=RackProduccion.objects.all(),  # Permite asociar un rack existente
        allow_null=True,  # Permite que sea opcional
        required=False  # Evita errores si no se envía en la solicitud
    )
    class Meta:
        model = EstanteProduccion
        fields = ["id", "codigo_estante", "rack", "estado"]  # Actualizado
        read_only_fields = ["id"]

    def get_rack(self, obj):
        """Devuelve el rack como objeto (incluso si es null)"""
        if obj.rack:
            return {
                "id": obj.rack.id,
                "codigo_rack": obj.rack.codigo_rack
            }
        return None 

    def validate_codigo_estante(self, value):
        """ Valida que el código del estante no esté vacío """
        if not value.strip():
            raise serializers.ValidationError("El código del estante no puede estar vacío.")
        return value

    def validate_estado(self, value):
        """ Valida que el estado del estante sea válido """
        estados_validos = dict(EstanteProduccion.ESTADO_OPCIONES).keys()
        if value not in estados_validos:
            raise serializers.ValidationError(f"Estado no válido. Usa: {', '.join(estados_validos)}")
        return value
    
class UbicacionPiezaSerializer(serializers.ModelSerializer):
    pieza = serializers.PrimaryKeyRelatedField(
        queryset=Pieza.objects.all(),
        required=True  
    )
    estante = serializers.PrimaryKeyRelatedField(
        queryset=EstanteProduccion.objects.all(),
        required=True  
    )
    responsable = serializers.PrimaryKeyRelatedField(
        queryset=Usuarios.objects.all(),
        required=False,
        allow_null=True
    )
    pieza_detalle = serializers.SerializerMethodField()
    estante_detalle = serializers.SerializerMethodField()
    responsable_detalle = serializers.SerializerMethodField()

    class Meta:
        model = UbicacionPieza
        fields = [
            "id", "pieza", "pieza_detalle", "estante", "estante_detalle", 
            "cantidad", "fecha_registro", "fecha_salida", "responsable", "responsable_detalle"
        ]
        read_only_fields = ["id", "fecha_registro"]

    def get_pieza_detalle(self, obj):
        """ Devuelve detalles de la pieza si existe """
        if obj.pieza:
            return {"id": obj.pieza.id, "consecutivo": obj.pieza.consecutivo}
        return None

    def get_estante_detalle(self, obj):
        """ Devuelve detalles del estante si existe """
        if obj.estante:
            return {"id": obj.estante.id, "codigo_estante": obj.estante.codigo_estante}
        return None

    def get_responsable_detalle(self, obj):
        """ Devuelve detalles del usuario responsable si existe """
        if obj.responsable:
            return {"id": obj.responsable.id, "nombre": obj.responsable.nombre}
        return None

    def validate_cantidad(self, value):
        """ Valida que la cantidad de piezas sea positiva """
        if value < 0:
            raise serializers.ValidationError("La cantidad de piezas no puede ser negativa.")
        return value

    def validate_fecha_salida(self, value):
        """ Valida que la fecha de salida no sea anterior a la fecha de registro """
        fecha_registro = self.instance.fecha_registro if self.instance else None
        if fecha_registro and value and value < fecha_registro:
            raise serializers.ValidationError("La fecha de salida no puede ser anterior a la fecha de registro.")
        return value
    
    

class PersonalMaquinaSerializer(serializers.ModelSerializer):
    personal = serializers.PrimaryKeyRelatedField(
        queryset=Usuarios.objects.all(),
        required=True
    )
    maquina = serializers.PrimaryKeyRelatedField(
        queryset=Maquina.objects.all(),
        required=True
    )
    personal_detalle = serializers.SerializerMethodField()
    maquina_detalle = serializers.SerializerMethodField()

    class Meta:
        model = PersonalMaquina
        fields = [
            "id", "personal", "personal_detalle",
            "maquina", "maquina_detalle"
        ]
        read_only_fields = ["id"]

    def get_personal_detalle(self, obj):
        if obj.personal:
            return {
                "id": obj.personal.id,
                "nombre": obj.personal.nombre,
                "correo": obj.personal.correo,
                "rol": obj.personal.rol
            }
        return None

    def get_maquina_detalle(self, obj):
        if obj.maquina:
            return {
                "id": obj.maquina.id,
                "nombre": obj.maquina.nombre,
                "estado": obj.maquina.estado
            }
        return None

    def validate(self, data):
        if PersonalMaquina.objects.filter(
            personal=data["personal"],
            maquina=data["maquina"]
        ).exists():
            raise serializers.ValidationError("Este usuario ya está asignado a esta máquina.")
        return data

class HorarioProduccionSerializer(serializers.ModelSerializer):
    usuario = serializers.PrimaryKeyRelatedField(
        queryset=Usuarios.objects.all(),
        required=True
    )
    usuario_detalle = serializers.SerializerMethodField()

    class Meta:
        model = HorarioProduccion
        fields = [
            "id",
            "usuario",
            "usuario_detalle",
            "dias_trabajo",
            "hora_entrada",
            "hora_salida",
            "tiene_comida",
            "hora_inicio_comida",
            "hora_fin_comida"
        ]
        read_only_fields = ["id"]

    def get_usuario_detalle(self, obj):
        if obj.usuario:
            return {
                "id": obj.usuario.id,
                "nombre": obj.usuario.nombre,
                "correo": obj.usuario.correo,
                "rol": obj.usuario.rol
            }
        return None

    def validate(self, data):
        entrada = data.get("hora_entrada")
        salida = data.get("hora_salida")

        if entrada and salida and entrada >= salida:
            raise serializers.ValidationError("La hora de entrada debe ser anterior a la de salida.")

        if data.get("tiene_comida"):
            inicio_comida = data.get("hora_inicio_comida")
            fin_comida = data.get("hora_fin_comida")

            if not inicio_comida or not fin_comida:
                raise serializers.ValidationError("Debe proporcionar el horario de comida si tiene comida.")
            if not (entrada <= inicio_comida < fin_comida <= salida):
                raise serializers.ValidationError("El horario de comida debe estar dentro del horario laboral.")

        return data