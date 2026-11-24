
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

cliente = MongoClient(os.getenv("MONGO_URI"))

db = cliente["escuela"]
estudiantes = db["estudiantes"]

print("===== LISTA DE ESTUDIANTES =====")

for estudiante in estudiantes.find():
    print("---------------------------")
    print("Nombre:", estudiante["nombre"])
    print("Edad:", estudiante["edad"])
    print("Grupo:", estudiante["grupo"])
    print("Carrera:", estudiante["carrera"])
    print("Promedio:", estudiante["promedio"])

cliente.close()
