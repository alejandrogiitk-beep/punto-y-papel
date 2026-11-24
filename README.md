# Punto & Papel

Sistema web de control de inventario para papelería, desarrollado como **Proyecto Integrador Final** de los submódulos *Construye aplicaciones web* e *Implementa aplicaciones web* (5.º Programación A, CECyTE Guanajuato, Unidad Académica Coroneo).

---

## Propósito

Muchas papelerías pequeñas de la comunidad llevan el control de su mercancía en libretas o de memoria. Eso provoca que no se sepa con exactitud qué hay en existencia, que se agoten artículos muy pedidos por los estudiantes y que se pierda tiempo buscando precios.

**Punto & Papel** resuelve esa necesidad con una aplicación web donde el personal de la papelería puede registrarse, iniciar sesión y administrar el inventario (crear, consultar, actualizar y eliminar productos), con alertas de productos con pocas existencias y un buscador en tiempo real.

## Funcionalidades

- **Página pública de inicio** con la presentación de la papelería y el número de productos registrados.
- **Registro de usuarios** con validación de datos y contraseña cifrada (hash `scrypt` de Werkzeug), guardado en **SQLite**.
- **Inicio y cierre de sesión** con sesiones de Flask; las rutas administrativas están protegidas con el decorador `login_requerido`.
- **Panel administrativo** con el total de productos y el número de productos con poco stock (5 piezas o menos).
- **CRUD completo de productos** en **MongoDB**:
  - Crear: formulario con nombre, categoría, descripción, precio y existencias.
  - Consultar: tabla ordenada por nombre, con aviso visual de stock bajo.
  - Actualizar: formulario de edición desplegable en cada fila.
  - Eliminar: botón con confirmación antes de borrar.
- **Búsqueda en tiempo real** por nombre o categoría mediante `fetch` a la API JSON `/api/productos`.
- **Validaciones en tres niveles**: HTML5 (`required`, `minlength`, `min`, `type="email"`), JavaScript (antes de enviar) y Python (en el servidor).
- **Mensajes de éxito y error** (mensajes *flash*) y manejo de errores (correo duplicado, datos inválidos, identificadores inexistentes).
- **Diseño responsivo y accesible**: menú adaptable, cuadrículas que pasan a una columna en móvil, enlace para saltar al contenido, foco visible y áreas táctiles de 44 px.

## Tecnologías utilizadas

| Capa | Tecnología |
|---|---|
| Frontend | HTML5, CSS3 (Grid, Flexbox, media queries), JavaScript (DOM, `fetch`, `async/await`) |
| Backend | Python 3.14, Flask 3.1, Jinja2, Werkzeug |
| Base de datos relacional | SQLite (módulo `sqlite3` de Python) |
| Base de datos no relacional | MongoDB (local o Atlas) con PyMongo 4.20 |
| Configuración | python-dotenv (archivo `.env`) |
| Pruebas | pytest y mongomock |
| Control de versiones | Git y GitHub |

## Estructura de carpetas

```
punto-y-papel/
├── app.py                  Aplicación Flask: rutas, login, CRUD y API
├── crear_admin.py          Carga el inventario inicial en MongoDB
├── conexion_prueba.py      Práctica: prueba de conexión a MongoDB
├── mostrar_datos.py        Práctica: lectura de documentos
├── requirements.txt        Dependencias de Python
├── README.md               Este documento
├── integrantes.txt         Integrantes del equipo
├── .env.example            Plantilla de variables de entorno
├── .gitignore              Archivos que no se suben a GitHub
├── database/               usuarios.db (SQLite, se crea al iniciar)
├── static/
│   ├── css/styles.css      Estilos y diseño responsivo
│   ├── js/script.js        Validaciones y búsqueda en tiempo real
│   └── img/                Logotipo e imagen principal
├── templates/
│   ├── base.html           Plantilla base (encabezado, menú, pie)
│   ├── index.html          Página de inicio
│   ├── registro.html       Crear cuenta
│   ├── login.html          Iniciar sesión
│   ├── dashboard.html      Panel administrativo
│   └── productos.html      CRUD del inventario
├── tests/
│   └── test_app.py         18 pruebas automatizadas
└── Docs/
    ├── Reporte_Tecnico_Punto_y_Papel.docx
    ├── Reporte_Tecnico_Punto_y_Papel.pdf
    ├── Presentacion_Punto_y_Papel.pptx
    ├── diagramas/          Arquitectura, modelos de datos, flujo y wireframes
    └── capturas/           Pantallas de la aplicación
```

## Requisitos previos

- **Python 3.10 o superior** (el proyecto se desarrolló con Python 3.14).
- **MongoDB**: puede ser un servidor local (MongoDB Community Server, puerto 27017) o un clúster gratuito de **MongoDB Atlas**.
- **Git** para clonar el repositorio.
- Un navegador web actualizado.
- SQLite **no necesita instalación**: viene incluido en Python.

## Instalación de dependencias

```bash
# 1. Clonar el repositorio
git clone https://github.com/alejandrogiitk-beep/punto-y-papel.git
cd punto-y-papel

# 2. Crear y activar un entorno virtual
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Instalar las dependencias
pip install -r requirements.txt
```

## Variables de entorno

La aplicación lee su configuración de un archivo `.env` en la carpeta principal. Copia la plantilla y escribe tus valores:

```bash
# Windows
copy .env.example .env
# macOS / Linux
cp .env.example .env
```

| Variable | Descripción | Ejemplo |
|---|---|---|
| `SECRET_KEY` | Clave para firmar las sesiones de Flask. Es obligatoria: sin ella la app no arranca. | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `MONGO_URI` | Cadena de conexión a MongoDB. | `mongodb://localhost:27017/` |

> El archivo `.env` contiene claves privadas, por eso está en `.gitignore` y nunca se sube a GitHub.

## Configuración de SQLite y MongoDB

### SQLite (usuarios)

No requiere configuración. Al ejecutar `app.py` se crea la carpeta `database/` y el archivo `database/usuarios.db` con la tabla:

```sql
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    correo TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL      -- se guarda el hash, nunca la contraseña
);
```

Para revisar los datos puedes abrir `usuarios.db` con *DB Browser for SQLite* o con la extensión *SQLite Viewer* de VS Code.

### MongoDB (inventario)

1. Inicia tu servidor local de MongoDB o crea un clúster en MongoDB Atlas (en Atlas agrega tu IP en *Network Access* y crea un usuario de base de datos).
2. Escribe la cadena de conexión en `MONGO_URI` dentro de `.env`.
3. La aplicación usa la base de datos `punto_papel` y la colección `productos`; MongoDB las crea automáticamente con el primer registro.
4. (Opcional) Carga el inventario inicial de ejemplo:

```bash
python crear_admin.py
```

Estructura de un documento de la colección `productos`:

```json
{
  "_id": ObjectId("..."),
  "nombre": "Cuaderno profesional",
  "categoria": "Cuadernos",
  "descripcion": "Cuaderno de 100 hojas",
  "precio": 45.5,
  "stock": 30
}
```

## Instrucciones de ejecución

```bash
python app.py
```

Abre en el navegador: **http://127.0.0.1:5000**

Recorrido sugerido para la demostración:

1. Entra a **Registrarse** y crea una cuenta (contraseña de 8 caracteres o más) → se guarda en SQLite.
2. **Inicia sesión** con esa cuenta → llegas al panel administrativo.
3. En **Inventario** registra un producto, edítalo con *Editar* y elimínalo con *Eliminar* → los cambios se guardan en MongoDB.
4. Escribe en el **buscador** para filtrar productos sin recargar la página.
5. Pulsa **Salir** y comprueba que `/dashboard` ya no se puede abrir sin iniciar sesión.

### Rutas principales

| Ruta | Método | Protegida | Descripción | Base de datos |
|---|---|---|---|---|
| `/` | GET | No | Página de inicio | MongoDB (conteo) |
| `/registro` | GET, POST | No | Crear cuenta | SQLite (INSERT) |
| `/login` | GET, POST | No | Iniciar sesión | SQLite (SELECT) |
| `/dashboard` | GET | Sí | Panel con estadísticas | MongoDB (conteos) |
| `/productos` | GET | Sí | Consultar inventario | MongoDB (`find`) |
| `/productos/crear` | POST | Sí | Crear producto | MongoDB (`insert_one`) |
| `/productos/actualizar/<id>` | POST | Sí | Actualizar producto | MongoDB (`update_one`) |
| `/productos/eliminar/<id>` | POST | Sí | Eliminar producto | MongoDB (`delete_one`) |
| `/api/productos?q=` | GET | Sí | Búsqueda en JSON | MongoDB (`$regex`) |
| `/logout` | GET | No | Cerrar sesión | — |

## Pruebas

El proyecto incluye **18 pruebas automatizadas** en `tests/test_app.py` que revisan el registro, el inicio y cierre de sesión, la protección de rutas, las cuatro operaciones del CRUD, el panel y la búsqueda. Durante las pruebas MongoDB se sustituye por `mongomock` (una base en memoria) y SQLite se crea en una carpeta temporal, así que **no se modifican tus datos reales** ni se necesita conexión a internet.

```bash
python -m pytest -v
```

Resultado esperado: `18 passed`.

Además se realizaron pruebas manuales en el navegador (escritorio y móvil) de cada formulario y de los mensajes de validación; los resultados están en el reporte técnico dentro de `Docs/`.

## Documentación

En la carpeta `Docs/` se encuentran:

- `Reporte_Tecnico_Punto_y_Papel.docx` y `.pdf`: reporte técnico completo.
- `Presentacion_Punto_y_Papel.pptx`: presentación para la Muestra de lo Aprendido.
- `diagramas/` y `capturas/`: arquitectura, modelos de datos, wireframes y pantallas de la aplicación.

## Autores

Equipo **Punto & Papel**, 5.º Programación A, CECyTE Guanajuato, Unidad Académica Coroneo:

- Pedro Emiliano Ramos
- Darío Daian Rodríguez Mejía
- Josué Alexander Soto Moreno

Noviembre de 2026.
