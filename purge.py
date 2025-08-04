import pandas as pd
import requests
import json

class Rack:
    def __init__(self, nombre):
        self.nombre = nombre

class Estante:
    def __init__(self, numero, rack):
        self.numero = numero
        self.rack = rack

class ProductoAlmacen:
    def __init__(self, nombre, identificador, costo, cantidad, divisa, posicion):
        self.nombre = nombre
        self.identificador = identificador
        self.costo = costo
        self.cantidad = cantidad
        self.divisa = divisa
        self.posicion = posicion

fila_inicio = 583

archivo = "C:\\Users\\cerbe\\Downloads\\NUEVO INVENTARIO 3.xlsx"
df = pd.read_excel(archivo)

rack_endpoint = "http://192.168.100.254/api/rack/"
estante_endpoint = "http://192.168.100.254/api/estantes/"
producto_almacen_endpoint = "http://192.168.100.254/api/productos_almacen/"

headers = {
    "Authorization": "Token 84993c9fff91c584e0a79f5e282a67ad7e175d8b"
}

productos_almacen = []

for index, row in df.iterrows():
    if index < fila_inicio - 1:
        continue
    
    print(f"Procesando fila {index + 1}...")
    rack_nombre = row['RACK']
    estante_numero = row['REPISA']

    response = requests.get(rack_endpoint, params={"nombre": rack_nombre}, headers=headers)
    if response.status_code == 200 and response.text:
        try:
            rack_id = response.json()[0]['id']
        except IndexError:
            rack = Rack(rack_nombre)
            response = requests.post(rack_endpoint, data=rack.__dict__, headers=headers)
            if response.status_code == 201:
                rack_id = response.json()['id']
            else:
                print(f"Error al crear el rack: {response.text}")
                continue
    else:
        rack = Rack(rack_nombre)
        response = requests.post(rack_endpoint, data=rack.__dict__, headers=headers)
        if response.status_code == 201:
            rack_id = response.json()['id']
        else:
            print(f"Error al crear el rack: {response.text}")
            continue

    response = requests.get(estante_endpoint, params={"estante": estante_numero, "rack": rack_id}, headers=headers)
    if response.status_code == 200 and response.text:
        try:
            estante_id = response.json()[0]['id']
        except IndexError:
            estante = Estante(estante_numero, rack_id)
            response = requests.post(estante_endpoint, data=estante.__dict__, headers=headers)
            if response.status_code == 201:
                estante_id = response.json()['id']
            else:
                print(f"Error al crear el estante: {response.text}")
                continue
    else:
        estante = Estante(estante_numero, rack_id)
        response = requests.post(estante_endpoint, data=estante.__dict__, headers=headers)
        if response.status_code == 201:
            estante_id = response.json()['id']
        else:
            print(f"Error al crear el estante: {response.text}")
            continue

    if pd.isna(row['No. Parte']):
        row['No. Parte'] = row['Nombre del Material']
    
    if pd.isna(row['PRECIO UNITARIO']):
        row['PRECIO UNITARIO'] = 0
    
    if pd.isna(row['DIVISA']):
        row['DIVISA'] = 'MXN'
    
    if pd.isnull(row['Total en Existencia']) or row['Total en Existencia'].split(' ')[0] == '':
        cantidad = 0
    else:
        cantidad = int(row['Total en Existencia'].split(' ')[0])

    producto = ProductoAlmacen(row['Nombre del Material'], row['No. Parte'], row['PRECIO UNITARIO'], cantidad, row['DIVISA'], estante_id)
    productos_almacen.append(producto.__dict__)
    
    response = requests.post(producto_almacen_endpoint, data=producto.__dict__, headers=headers)
    if response.status_code == 201:
        print(f"Producto almacenado correctamente: {response.json()}")
    else:
        print(f"Error al almacenar el producto: {response.text}")
        continue
