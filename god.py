import psycopg2
from psycopg2.errors import UniqueViolation

# Conéctate a la base de datos de origen
conn_origen = psycopg2.connect(
    dbname="ri_data_test",
    user="postgres",
    password="$RIAutorizacion00",
    host="localhost",
    port="5432"
)

# Conéctate a la base de datos de destino
conn_destino = psycopg2.connect(
    dbname="data_main",
    user="postgres",
    password="$RIAutorizacion00",
    host="localhost",
    port="5432"
)

# Crea un cursor para cada conexión
cur_origen = conn_origen.cursor()
cur_destino = conn_destino.cursor()

# Lista de las tablas que deseas transferir, ordenadas por dependencias
tablas = [
    ##"django_content_type",
    ##"auth_permission",
    ##"auth_group",
    ##"auth_group_permissions",
    #?"authtoken_token",
    ##"django_admin_log",
    ##"django_migrations",
    ##"django_session",
    #?"ri_compras_contacto",
    #?"ri_compras_departamento",
    #"ri_compras_historicalusuarios",
    #?"ri_compras_message",
    #?"ri_compras_ordendecompra",
    #?"ri_compras_producto",
    #?"ri_compras_productorequisicion",
    #?"ri_compras_project",
    #?"ri_compras_proveedor",
    #?"ri_compras_proveedor_contactos",
    #?"ri_compras_recibo",
    #?"ri_compras_recibo_orden",
    #?"ri_compras_requisicion",
    #?"ri_compras_requisicion_productos",
    #?"ri_compras_requisicion_servicios",
    #"ri_compras_servicio",
    #"ri_compras_serviciorequisicion",
    #?"ri_compras_usuarios",
    ##"ri_compras_usuarios_groups",
    ##"ri_compras_usuarios_user_permissions",
    #?"ri_produccion_material",
    #?"ri_produccion_notificacion"
    #?"ri_produccion_pieza"
    #!"ri_produccion_pieza_procesos"
    #?"ri_produccion_piezaplaca"
    #?"ri_produccion_placa"
    #?"ri_produccion_proceso"
]

for tabla in tablas:
    # Extrae los datos de la tabla de la base de datos de origen
    cur_origen.execute(f"SELECT * FROM {tabla}")
    rows = cur_origen.fetchall()

    # Inserta los datos en la tabla de la base de datos de destino
    for row in rows:
        placeholders = ', '.join(['%s'] * len(row))
        query = f"INSERT INTO {tabla} VALUES ({placeholders})"
        try:
            cur_destino.execute(query, row)
        except UniqueViolation:
            conn_destino.rollback()
        else:
            conn_destino.commit()

# Cierra las conexiones
cur_origen.close()
cur_destino.close()
conn_origen.close()
conn_destino.close()