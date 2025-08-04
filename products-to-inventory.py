import pandas as pd

class ProductoAlmacen:
    def __init__(self, nombre, identificador, costo, cantidad, divisa):
        self.nombre = nombre
        self.identificador = identificador
        self.costo = costo
        self.cantidad = cantidad
        self.divisa = divisa

archivo = "C:\\Users\\cerbe\\Downloads\\NUEVO INVENTARIO 3.xlsx"

df = pd.read_excel(archivo)

for index, row in df.iterrows():
    if pd.isnull(row['No. Parte']):
        df.loc[index, 'No. Parte'] = row['Nombre del Material']
    
    if pd.isnull(row['PRECIO UNITARIO']):
        df.loc[index, 'PRECIO UNITARIO'] = 0
    
    if pd.isnull(row['DIVISA']):
        df.loc[index, 'DIVISA'] = 'MXN'

filas_procesadas = df.values.tolist()

productos_almacen = [ProductoAlmacen(fila[1], fila[0], fila[3], fila[2], fila[4]) for fila in filas_procesadas]

for producto in productos_almacen:
    print(producto.__dict__)
