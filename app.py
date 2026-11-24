
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash, jsonify
)
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from dotenv import load_dotenv
from functools import wraps
import sqlite3
import os
import re

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

if not app.config["SECRET_KEY"]:
    raise RuntimeError("No se encontro la SECRET_KEY")

# =====================================
# CONEXION SQLITE
# =====================================

os.makedirs("database", exist_ok=True)

def conectar_sqlite():
    conexion = sqlite3.connect("database/usuarios.db")
    conexion.row_factory = sqlite3.Row
    return conexion


def crear_tabla():
    conexion = conectar_sqlite()

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            correo TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conexion.commit()
    conexion.close()


crear_tabla()

# =====================================
# CONEXION MONGODB
# =====================================

cliente = MongoClient(
    os.getenv("MONGO_URI"),
    serverSelectionTimeoutMS=5000
)

cliente.admin.command("ping")

db = cliente["punto_papel"]
productos = db["productos"]

# =====================================
# PROTECCION DE RUTAS
# =====================================

def login_requerido(funcion):
    @wraps(funcion)
    def decorador(*args, **kwargs):
        if "usuario" not in session:
            flash("Inicia sesion para continuar", "error")
            return redirect(url_for("login"))

        return funcion(*args, **kwargs)

    return decorador


# =====================================
# PAGINA PRINCIPAL
# =====================================

@app.route("/")
def inicio():
    cantidad = productos.count_documents({})
    return render_template("index.html", cantidad=cantidad)


# =====================================
# REGISTRO
# =====================================

@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":

        nombre = request.form.get("nombre", "").strip()
        correo = request.form.get("correo", "").strip().lower()
        password = request.form.get("password", "")

        if not nombre or not correo or len(password) < 8:
            flash("Completa los campos y usa una contraseña de 8 caracteres.", "error")
            return redirect(url_for("registro"))

        conexion = conectar_sqlite()

        try:
            conexion.execute("""
                INSERT INTO usuarios (nombre, correo, password)
                VALUES (?, ?, ?)
            """, (
                nombre,
                correo,
                generate_password_hash(password)
            ))

            conexion.commit()
            flash("Cuenta creada correctamente", "success")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("Este correo ya esta registrado", "error")

        finally:
            conexion.close()

    return render_template("registro.html")


# =====================================
# INICIO DE SESION
# =====================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        correo = request.form.get("correo", "").strip().lower()
        password = request.form.get("password", "")

        conexion = conectar_sqlite()

        usuario = conexion.execute("""
            SELECT * FROM usuarios
            WHERE correo = ?
        """, (correo,)).fetchone()

        conexion.close()

        if usuario and check_password_hash(
            usuario["password"], password
        ):

            session.clear()
            session["usuario"] = usuario["nombre"]
            session["usuario_id"] = usuario["id"]

            return redirect(url_for("dashboard"))

        flash("Correo o contraseña incorrectos", "error")

    return render_template("login.html")


# =====================================
# PANEL ADMINISTRATIVO
# =====================================

@app.route("/dashboard")
@login_requerido
def dashboard():

    total = productos.count_documents({})
    bajo_stock = productos.count_documents({
        "stock": {"$lte": 5}
    })

    return render_template(
        "dashboard.html",
        total=total,
        bajo_stock=bajo_stock
    )


# =====================================
# CONSULTAR PRODUCTOS
# =====================================

@app.route("/productos")
@login_requerido
def ver_productos():

    lista = list(productos.find().sort("nombre", 1))

    for producto in lista:
        producto["id"] = str(producto["_id"])

    return render_template(
        "productos.html",
        productos=lista
    )


# =====================================
# CREAR PRODUCTO
# =====================================

@app.route("/productos/crear", methods=["POST"])
@login_requerido
def crear_producto():

    nombre = request.form.get("nombre", "").strip()
    categoria = request.form.get("categoria", "").strip()
    descripcion = request.form.get("descripcion", "").strip()

    try:
        precio = float(request.form.get("precio", ""))
        stock = int(request.form.get("stock", ""))
    except (ValueError, TypeError):
        flash("Precio o existencias invalidos", "error")
        return redirect(url_for("ver_productos"))

    if not nombre or not categoria or precio <= 0 or stock < 0:
        flash("Revisa los datos del producto", "error")
        return redirect(url_for("ver_productos"))

    productos.insert_one({
        "nombre": nombre,
        "categoria": categoria,
        "descripcion": descripcion,
        "precio": precio,
        "stock": stock
    })

    flash("Producto registrado correctamente", "success")
    return redirect(url_for("ver_productos"))


# =====================================
# ACTUALIZAR PRODUCTO
# =====================================

@app.route("/productos/actualizar/<id>", methods=["POST"])
@login_requerido
def actualizar_producto(id):

    nombre = request.form.get("nombre", "").strip()
    categoria = request.form.get("categoria", "").strip()
    descripcion = request.form.get("descripcion", "").strip()

    try:
        precio = float(request.form.get("precio", ""))
        stock = int(request.form.get("stock", ""))

        if not nombre or not categoria or precio <= 0 or stock < 0:
            raise ValueError()

        resultado = productos.update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "nombre": nombre,
                "categoria": categoria,
                "descripcion": descripcion,
                "precio": precio,
                "stock": stock
            }}
        )

        if resultado.matched_count == 0:
            flash("Producto no encontrado", "error")
        else:
            flash("Producto actualizado correctamente", "success")

    except (ValueError, TypeError):
        flash("Datos invalidos", "error")
    except Exception:
        flash("No se pudo actualizar el producto", "error")

    return redirect(url_for("ver_productos"))


# =====================================
# ELIMINAR PRODUCTO
# =====================================

@app.route("/productos/eliminar/<id>", methods=["POST"])
@login_requerido
def eliminar_producto(id):

    try:
        resultado = productos.delete_one({
            "_id": ObjectId(id)
        })

        if resultado.deleted_count:
            flash("Producto eliminado correctamente", "success")
        else:
            flash("Producto no encontrado", "error")

    except Exception:
        flash("No se pudo eliminar el producto", "error")

    return redirect(url_for("ver_productos"))


# =====================================
# BUSCADOR DE PRODUCTOS
# =====================================

@app.route("/api/productos")
@login_requerido
def buscar_productos():

    termino = request.args.get("q", "").strip()

    if len(termino) > 80:
        return jsonify({"error": "Busqueda demasiado larga"}), 400

    # re.escape evita que caracteres como ( o * rompan la consulta
    patron = re.escape(termino)

    consulta = {
        "$or": [
            {"nombre": {"$regex": patron, "$options": "i"}},
            {"categoria": {"$regex": patron, "$options": "i"}}
        ]
    }

    resultados = []

    for producto in productos.find(consulta).limit(50):
        resultados.append({
            "id": str(producto["_id"]),
            "nombre": producto["nombre"],
            "categoria": producto["categoria"],
            "precio": producto["precio"],
            "stock": producto["stock"]
        })

    return jsonify(resultados)


# =====================================
# CERRAR SESION
# =====================================

@app.route("/logout")
def logout():
    session.clear()
    flash("Sesion cerrada correctamente", "success")
    return redirect(url_for("inicio"))


# =====================================
# EJECUTAR APLICACION
# =====================================

if __name__ == "__main__":
    app.run(debug=True)
