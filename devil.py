import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ri_project.settings')
django.setup()

from django.db import connection
from ri_compras.models import ProductoRequisicion, Requisicion

tablas = [
    #"authtoken_token",
    #"ri_compras_contacto",
    #"ri_compras_departamento",
    #"ri_compras_message",
    #"ri_compras_ordendecompra",
    #"ri_compras_producto",
    #"ri_compras_productorequisicion",
    #"ri_compras_project",
    #"ri_compras_proveedor",
    #"ri_compras_proveedor_contactos",
    #"ri_compras_recibo",
    #"ri_compras_recibo_orden",
    #"ri_compras_requisicion",
    #"ri_compras_requisicion_productos",
    #"ri_compras_requisicion_servicios",
    #"ri_compras_servicio",
    #"ri_compras_serviciorequisicion",
    #"ri_compras_usuarios",
    #"ri_produccion_material",
    #"ri_produccion_notificacion"
    #"ri_produccion_pieza"
    #"ri_produccion_pieza_procesos"
    #"ri_produccion_piezaplaca"
    #"ri_produccion_placa"
    #"ri_produccion_proceso"
]

def reset_sequences(tablas):
    with connection.cursor() as cursor:
        for tabla in tablas:
            cursor.execute(f"""
                SELECT setval(pg_get_serial_sequence('{tabla}', 'id'), 
                COALESCE((SELECT MAX(id)+1 FROM {tabla}), 1), false);
            """)

reset_sequences(tablas)