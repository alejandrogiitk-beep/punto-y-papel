
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

try:
    cliente = MongoClient(
        os.getenv("MONGO_URI"),
        serverSelectionTimeoutMS=5000
    )

    cliente.admin.command("ping")
    print("Conexion exitosa con MongoDB")

    db = cliente["escuela"]
    estudiantes = db["estudiantes"]

    datos = [
        {
            "nombre": "Ana Lopez",
            "edad": 17,
            "grupo": "5A",
            "carrera": "Programacion",
            "promedio": 9.5
        },
        {
            "nombre": "Carlos Perez",
            "edad": 18,
            "grupo": "5B",
            "carrera": "Programacion",
            "promedio": 8.9
        },
        {
            "nombre": "Maria Garcia",
            "edad": 17,
            "grupo": "5A",
            "carrera": "Contabilidad",
            "promedio": 9.2
        },
        {
            "nombre": "Luis Hernandez",
            "edad": 18,
            "grupo": "5C",
            "carrera": "Ofimatica",
            "promedio": 8.7
        }
    ]

    resultado = estudiantes.insert_many(datos)

    print("Documentos insertados:", len(resultado.inserted_ids))

    cliente.close()

except Exception as error:
    print("Error de conexion:", error)
