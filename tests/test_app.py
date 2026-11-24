"""
Pruebas automatizadas de Punto & Papel.

Se ejecutan con:  python -m pytest -v

MongoDB se sustituye por mongomock (una base en memoria que imita a MongoDB)
y SQLite se crea en una carpeta temporal, asi las pruebas no modifican
los datos reales del proyecto.
"""

import importlib
import sqlite3
import sys
from pathlib import Path

import mongomock
import pymongo
import pytest

RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    """Carga app.py con una base SQLite temporal y MongoDB simulado."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SECRET_KEY", "clave-de-pruebas")
    monkeypatch.setenv("MONGO_URI", "mongodb://localhost:27017")
    monkeypatch.setattr(pymongo, "MongoClient", mongomock.MongoClient)
    monkeypatch.syspath_prepend(str(RAIZ))

    sys.modules.pop("app", None)
    modulo = importlib.import_module("app")
    modulo.app.config.update(TESTING=True)
    modulo.app.template_folder = str(RAIZ / "templates")
    modulo.app.static_folder = str(RAIZ / "static")

    yield modulo, tmp_path

    sys.modules.pop("app", None)


@pytest.fixture
def cliente(entorno):
    modulo, _ = entorno
    return modulo.app.test_client()


def registrar(cliente, correo="ana@correo.com", password="Segura123"):
    return cliente.post("/registro", data={
        "nombre": "Ana Prueba",
        "correo": correo,
        "password": password,
    })


def iniciar_sesion(cliente, correo="ana@correo.com", password="Segura123"):
    registrar(cliente, correo, password)
    return cliente.post("/login", data={"correo": correo, "password": password})


def crear(cliente, nombre="Cuaderno rayado", categoria="Cuadernos",
          precio="35.50", stock="20"):
    return cliente.post("/productos/crear", data={
        "nombre": nombre,
        "categoria": categoria,
        "descripcion": "Producto de prueba",
        "precio": precio,
        "stock": stock,
    }, follow_redirects=True)


# ---------------------------------------------------------------
# Paginas publicas
# ---------------------------------------------------------------

def test_inicio_muestra_pagina_publica(cliente):
    respuesta = cliente.get("/")
    assert respuesta.status_code == 200
    assert "productos registrados en nuestro sistema" in respuesta.get_data(as_text=True)


def test_plantilla_enlaza_css_y_js_existentes(cliente):
    html = cliente.get("/").get_data(as_text=True)
    assert "/static/css/styles.css" in html
    assert "/static/js/script.js" in html
    assert (RAIZ / "static/js/script.js").exists()


# ---------------------------------------------------------------
# Registro y autenticacion (SQLite)
# ---------------------------------------------------------------

def test_registro_guarda_usuario_con_contrasena_cifrada(entorno):
    modulo, carpeta = entorno
    respuesta = registrar(modulo.app.test_client())
    assert respuesta.status_code == 302

    conexion = sqlite3.connect(carpeta / "database" / "usuarios.db")
    fila = conexion.execute(
        "SELECT nombre, correo, password FROM usuarios"
    ).fetchone()
    conexion.close()

    assert fila[0] == "Ana Prueba"
    assert fila[1] == "ana@correo.com"
    assert fila[2] != "Segura123"
    assert fila[2].startswith("scrypt:")


def test_registro_rechaza_correo_duplicado(cliente):
    registrar(cliente)
    respuesta = registrar(cliente)
    assert "ya esta registrado" in respuesta.get_data(as_text=True)


def test_registro_rechaza_contrasena_corta(cliente):
    respuesta = registrar(cliente, password="123")
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/registro")


def test_login_correcto_redirige_al_panel(cliente):
    respuesta = iniciar_sesion(cliente)
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/dashboard")


def test_login_incorrecto_muestra_error(cliente):
    registrar(cliente)
    respuesta = cliente.post("/login", data={
        "correo": "ana@correo.com",
        "password": "contrasena-equivocada",
    })
    assert "Correo o contraseña incorrectos" in respuesta.get_data(as_text=True)


def test_rutas_protegidas_exigen_sesion(cliente):
    for ruta in ["/dashboard", "/productos", "/api/productos"]:
        respuesta = cliente.get(ruta)
        assert respuesta.status_code == 302
        assert "/login" in respuesta.headers["Location"]


def test_cerrar_sesion_bloquea_el_panel(cliente):
    iniciar_sesion(cliente)
    cliente.get("/logout")
    respuesta = cliente.get("/dashboard")
    assert respuesta.status_code == 302


# ---------------------------------------------------------------
# CRUD de productos (MongoDB)
# ---------------------------------------------------------------

def test_crear_y_consultar_producto(entorno):
    modulo, _ = entorno
    cliente = modulo.app.test_client()
    iniciar_sesion(cliente)

    respuesta = crear(cliente)
    html = respuesta.get_data(as_text=True)

    assert "Producto registrado correctamente" in html
    assert "Cuaderno rayado" in html
    documento = modulo.productos.find_one({"nombre": "Cuaderno rayado"})
    assert documento["precio"] == 35.5
    assert documento["stock"] == 20


def test_crear_producto_rechaza_precio_invalido(entorno):
    modulo, _ = entorno
    cliente = modulo.app.test_client()
    iniciar_sesion(cliente)

    respuesta = crear(cliente, precio="0")

    assert "Revisa los datos del producto" in respuesta.get_data(as_text=True)
    assert modulo.productos.count_documents({}) == 0


def test_actualizar_producto(entorno):
    modulo, _ = entorno
    cliente = modulo.app.test_client()
    iniciar_sesion(cliente)
    crear(cliente)
    identificador = str(modulo.productos.find_one()["_id"])

    respuesta = cliente.post(f"/productos/actualizar/{identificador}", data={
        "nombre": "Cuaderno rayado",
        "categoria": "Cuadernos",
        "descripcion": "Precio actualizado",
        "precio": "39.90",
        "stock": "3",
    }, follow_redirects=True)

    assert "Producto actualizado correctamente" in respuesta.get_data(as_text=True)
    documento = modulo.productos.find_one()
    assert documento["precio"] == 39.9
    assert documento["stock"] == 3


def test_actualizar_con_id_invalido_no_rompe_la_app(cliente):
    iniciar_sesion(cliente)
    respuesta = cliente.post("/productos/actualizar/no-es-un-id", data={
        "nombre": "X", "categoria": "Otros", "precio": "10", "stock": "1",
    }, follow_redirects=True)
    assert respuesta.status_code == 200
    assert "No se pudo actualizar el producto" in respuesta.get_data(as_text=True)


def test_eliminar_producto(entorno):
    modulo, _ = entorno
    cliente = modulo.app.test_client()
    iniciar_sesion(cliente)
    crear(cliente)
    identificador = str(modulo.productos.find_one()["_id"])

    respuesta = cliente.post(
        f"/productos/eliminar/{identificador}", follow_redirects=True
    )

    assert "Producto eliminado correctamente" in respuesta.get_data(as_text=True)
    assert modulo.productos.count_documents({}) == 0


def test_panel_cuenta_productos_con_poco_stock(entorno):
    modulo, _ = entorno
    cliente = modulo.app.test_client()
    iniciar_sesion(cliente)
    crear(cliente, nombre="Lapiz HB", categoria="Escritura", stock="100")
    crear(cliente, nombre="Colores", categoria="Arte", stock="4")

    html = cliente.get("/dashboard").get_data(as_text=True)

    assert "<strong>2</strong>" in html
    assert "<strong>1</strong>" in html


# ---------------------------------------------------------------
# Busqueda en tiempo real (API JSON)
# ---------------------------------------------------------------

def test_busqueda_por_nombre_o_categoria_sin_importar_mayusculas(cliente):
    iniciar_sesion(cliente)
    crear(cliente, nombre="Lapiz HB", categoria="Escritura")
    crear(cliente, nombre="Carpeta carta", categoria="Oficina")

    por_nombre = cliente.get("/api/productos?q=lapiz").get_json()
    por_categoria = cliente.get("/api/productos?q=OFICINA").get_json()

    assert [p["nombre"] for p in por_nombre] == ["Lapiz HB"]
    assert [p["nombre"] for p in por_categoria] == ["Carpeta carta"]


def test_busqueda_con_caracteres_especiales(cliente):
    iniciar_sesion(cliente)
    respuesta = cliente.get("/api/productos?q=(")
    assert respuesta.status_code == 200
    assert respuesta.get_json() == []


def test_busqueda_demasiado_larga(cliente):
    iniciar_sesion(cliente)
    respuesta = cliente.get("/api/productos?q=" + "a" * 81)
    assert respuesta.status_code == 400
