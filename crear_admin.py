
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

cliente = MongoClient(os.getenv("MONGO_URI"))

db = cliente["punto_papel"]
productos = db["productos"]

datos = [
    {
        "nombre": "Cuaderno profesional",
        "categoria": "Cuadernos",
        "descripcion": "Cuaderno de 100 hojas",
        "precio": 45.50,
        "stock": 30
    },
    {
        "nombre": "Lapiz HB",
        "categoria": "Escritura",
        "descripcion": "Lapiz de grafito para escritura",
        "precio": 8.00,
        "stock": 100
    },
    {
        "nombre": "Colores escolares",
        "categoria": "Arte",
        "descripcion": "Caja con 12 colores",
        "precio": 65.00,
        "stock": 4
    },
    {
        "nombre": "Carpeta tamaño carta",
        "categoria": "Oficina",
        "descripcion": "Carpeta de plastico",
        "precio": 25.00,
        "stock": 15
    }
]

for producto in datos:
    productos.update_one(
        {"nombre": producto["nombre"]},
        {"$setOnInsert": producto},
        upsert=True
    )

print("Inventario inicial cargado correctamente.")

cliente.close()
