"""
app.py
===========

Aplicación minimalista para gestionar una empresa de renta de autos usando
MongoDB como base de datos no relacional y Flask como micro‑framework web.
Se utilizan operaciones CRUD básicas para satisfacer los requerimientos
funcionales del caso de estudio.  El código fue diseñado para
facilitar su lectura y modificación.

Para ejecutar este servidor:

    python app.py

El servidor escuchará en http://127.0.0.1:5000/ y expondrá distintos
endpoints RESTful.  Requiere tener MongoDB en ejecución en el puerto 27017.

Dependencias: Flask, pymongo.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, request, render_template, redirect, url_for
from bson.objectid import ObjectId
from pymongo import MongoClient


# ---------------------------------------------------------------------------
# Configuración de Flask y conexión a MongoDB
#
# Se crea la aplicación Flask y se establece una conexión con MongoDB.
# La conexión apunta a una base de datos local llamada `renta_autos`.  Si
# necesitas usar un servidor remoto, modifica la URI a tu gusto.
#
# PyMongo permite abrir la conexión simplemente proporcionando la URI.
# La documentación oficial muestra cómo conectar y seleccionar una base de datos
# específica【788983236826060†L95-L116】.
# ---------------------------------------------------------------------------

app = Flask(__name__)

# Conectar a MongoDB en localhost sin autenticación.  Cambia la URI según
# tus necesidades.  La base de datos se llama `renta_autos`.
client: MongoClient = MongoClient("mongodb://localhost:27017/")
db = client["renta_autos"]


# ---------------------------------------------------------------------------
# Funciones auxiliares
#
# Las siguientes utilidades ayudan a convertir documentos de MongoDB a
# estructuras serializables por JSON.  Mongo almacena objetos de tipo
# ObjectId y datetime que no son compatibles con JSON de manera directa.
# Estas funciones realizan las conversiones necesarias.
# ---------------------------------------------------------------------------

def serialize_datetime(value: Any) -> Any:
    """Convierte objetos datetime en cadenas ISO (YYYY-MM-DD)."""
    if isinstance(value, datetime):
        # Ajustamos a fecha local sin zona horaria; se formatea como AAAA-MM-DD
        return value.strftime("%Y-%m-%d")
    return value


def serialize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convierte un documento MongoDB a un diccionario apto para JSON.

    - Convierte campos `_id` y cualquier otro campo que sea ObjectId a str.
    - Convierte objetos datetime a cadenas.
    - Devuelve una copia del documento original para no alterar la base.
    """
    if doc is None:
        return {}
    serialized: Dict[str, Any] = {}
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            serialized[key] = str(value)
        elif isinstance(value, datetime):
            serialized[key] = serialize_datetime(value)
        else:
            serialized[key] = value
    # Convertir id
    if "_id" in serialized:
        serialized["_id"] = str(serialized["_id"])
    return serialized


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Intenta convertir una cadena en fecha (formato AAAA-MM-DD).

    Si no se proporciona la cadena o el formato es incorrecto, devuelve None.
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Rutas de Clientes (RF01)
# ---------------------------------------------------------------------------

@app.route("/clientes", methods=["GET"])
def listar_clientes() -> Any:
    """Devuelve la lista completa de clientes."""
    clientes: List[Dict[str, Any]] = list(db.clientes.find())
    return jsonify([serialize_document(c) for c in clientes]), 200


@app.route("/clientes", methods=["POST"])
def crear_cliente() -> Any:
    """Crea un nuevo cliente.

    Espera en el cuerpo JSON campos como `nombre`, `apellido`, `telefono`,
    `direccion`, etc.  Todos los datos se almacenan tal cual se reciben.
    """
    data: Dict[str, Any] = request.get_json(force=True) or {}
    if not data:
        return jsonify({"error": "Datos de cliente no proporcionados"}), 400
    result = db.clientes.insert_one(data)
    cliente = db.clientes.find_one({"_id": result.inserted_id})
    return jsonify(serialize_document(cliente)), 201


@app.route("/clientes/<string:cliente_id>", methods=["PUT"])
def actualizar_cliente(cliente_id: str) -> Any:
    """Actualiza un cliente existente identificado por su `_id`.

    El cuerpo JSON contiene los campos a actualizar.  Si el cliente no se
    encuentra, devuelve un error 404.
    """
    data: Dict[str, Any] = request.get_json(force=True) or {}
    try:
        oid = ObjectId(cliente_id)
    except Exception:
        return jsonify({"error": "Identificador de cliente inválido"}), 400
    result = db.clientes.update_one({"_id": oid}, {"$set": data})
    if result.matched_count == 0:
        return jsonify({"error": "Cliente no encontrado"}), 404
    cliente = db.clientes.find_one({"_id": oid})
    return jsonify(serialize_document(cliente)), 200


@app.route("/clientes/<string:cliente_id>", methods=["DELETE", "POST"])
def eliminar_cliente(cliente_id: str) -> Any:
    """Elimina un cliente por su identificador."""
    try:
        oid = ObjectId(cliente_id)
    except Exception:
        return jsonify({"error": "Identificador de cliente inválido"}), 400
    result = db.clientes.delete_one({"_id": oid})
    if result.deleted_count == 0:
        return jsonify({"error": "Cliente no encontrado"}), 404
    # Si la solicitud proviene de un formulario HTML (POST), redirige a la lista
    if request.method == "POST":
        return redirect(url_for("listar_clientes_html"))
    return jsonify({"mensaje": "Cliente eliminado"}), 200


# ---------------------------------------------------------------------------
# Rutas de Autos (RF02 y RF07)
# ---------------------------------------------------------------------------

@app.route("/autos", methods=["GET"])
def listar_autos() -> Any:
    """Devuelve la lista de todos los autos."""
    autos: List[Dict[str, Any]] = list(db.autos.find())
    return jsonify([serialize_document(a) for a in autos]), 200


@app.route("/autos", methods=["POST"])
def crear_auto() -> Any:
    """Crea un registro de auto.

    Se esperan campos como `marca`, `modelo`, `anio` y opcionalmente `disponible`.
    Si no se indica `disponible`, se asumirá `True`.
    """
    data: Dict[str, Any] = request.get_json(force=True) or {}
    if not data:
        return jsonify({"error": "Datos de auto no proporcionados"}), 400
    # Si no se especifica disponibilidad, se establece en True
    data.setdefault("disponible", True)
    result = db.autos.insert_one(data)
    auto = db.autos.find_one({"_id": result.inserted_id})
    return jsonify(serialize_document(auto)), 201


@app.route("/autos/<string:auto_id>", methods=["PUT"])
def actualizar_auto(auto_id: str) -> Any:
    """Actualiza los datos de un auto existente."""
    data: Dict[str, Any] = request.get_json(force=True) or {}
    try:
        oid = ObjectId(auto_id)
    except Exception:
        return jsonify({"error": "Identificador de auto inválido"}), 400
    result = db.autos.update_one({"_id": oid}, {"$set": data})
    if result.matched_count == 0:
        return jsonify({"error": "Auto no encontrado"}), 404
    auto = db.autos.find_one({"_id": oid})
    return jsonify(serialize_document(auto)), 200


@app.route("/autos/<string:auto_id>", methods=["DELETE", "POST"])
def eliminar_auto(auto_id: str) -> Any:
    """Elimina un auto de la colección."""
    try:
        oid = ObjectId(auto_id)
    except Exception:
        return jsonify({"error": "Identificador de auto inválido"}), 400
    result = db.autos.delete_one({"_id": oid})
    if result.deleted_count == 0:
        return jsonify({"error": "Auto no encontrado"}), 404
    if request.method == "POST":
        return redirect(url_for("listar_autos_html"))
    return jsonify({"mensaje": "Auto eliminado"}), 200


@app.route("/autos/disponibles", methods=["GET"])
def autos_disponibles() -> Any:
    """Lista los autos que tienen el campo `disponible` en True."""
    autos: List[Dict[str, Any]] = list(db.autos.find({"disponible": True}))
    return jsonify([serialize_document(a) for a in autos]), 200

# ===========================================================================
# Vistas HTML (interfaz gráfica)
# ===========================================================================

@app.route("/")
def home() -> Any:
    """Página de inicio que muestra opciones principales."""
    return render_template("index.html")


# ---------------------------------------------------------------------------
# Clientes - interfaz HTML
# ---------------------------------------------------------------------------

@app.route("/clientes/lista")
def listar_clientes_html() -> Any:
    """Lista de clientes en una tabla HTML."""
    clientes: List[Dict[str, Any]] = list(db.clientes.find())
    clientes = [serialize_document(c) for c in clientes]
    return render_template("clientes.html", clientes=clientes)


@app.route("/clientes/nuevo", methods=["GET", "POST"])
def nuevo_cliente() -> Any:
    """Formulario para crear un nuevo cliente."""
    if request.method == "POST":
        nombre = request.form.get("nombre")
        apellido = request.form.get("apellido")
        telefono = request.form.get("telefono")
        direccion = request.form.get("direccion")
        datos = {
            "nombre": nombre,
            "apellido": apellido,
            "telefono": telefono,
            "direccion": direccion,
        }
        db.clientes.insert_one(datos)
        return redirect(url_for("listar_clientes_html"))
    # GET
    return render_template("cliente_form.html", cliente=None)


@app.route("/clientes/<string:cliente_id>/editar", methods=["GET", "POST"])
def editar_cliente(cliente_id: str) -> Any:
    """Formulario para editar un cliente existente."""
    try:
        oid = ObjectId(cliente_id)
    except Exception:
        return "ID inválido", 400
    cliente = db.clientes.find_one({"_id": oid})
    if not cliente:
        return "Cliente no encontrado", 404
    if request.method == "POST":
        # Actualizar campos
        data = {
            "nombre": request.form.get("nombre"),
            "apellido": request.form.get("apellido"),
            "telefono": request.form.get("telefono"),
            "direccion": request.form.get("direccion"),
        }
        db.clientes.update_one({"_id": oid}, {"$set": data})
        return redirect(url_for("listar_clientes_html"))
    # GET: mostrar formulario con datos
    return render_template("cliente_form.html", cliente=serialize_document(cliente))


# ---------------------------------------------------------------------------
# Autos - interfaz HTML
# ---------------------------------------------------------------------------

@app.route("/autos/lista")
def listar_autos_html() -> Any:
    """Lista de autos en una tabla HTML."""
    autos: List[Dict[str, Any]] = list(db.autos.find())
    autos = [serialize_document(a) for a in autos]
    return render_template("autos.html", autos=autos)


@app.route("/autos/nuevo", methods=["GET", "POST"])
def nuevo_auto() -> Any:
    """Formulario para crear un nuevo auto."""
    if request.method == "POST":
        marca = request.form.get("marca")
        modelo = request.form.get("modelo")
        anio = request.form.get("anio")
        disponible = True if request.form.get("disponible") == "on" else False
        datos = {
            "marca": marca,
            "modelo": modelo,
            "anio": anio,
            "disponible": disponible,
        }
        db.autos.insert_one(datos)
        return redirect(url_for("listar_autos_html"))
    return render_template("auto_form.html", auto=None)


@app.route("/autos/<string:auto_id>/editar", methods=["GET", "POST"])
def editar_auto(auto_id: str) -> Any:
    """Formulario para editar un auto existente."""
    try:
        oid = ObjectId(auto_id)
    except Exception:
        return "ID inválido", 400
    auto = db.autos.find_one({"_id": oid})
    if not auto:
        return "Auto no encontrado", 404
    if request.method == "POST":
        data = {
            "marca": request.form.get("marca"),
            "modelo": request.form.get("modelo"),
            "anio": request.form.get("anio"),
            # checkbox 'disponible' regresa None si no está seleccionado
            "disponible": True if request.form.get("disponible") == "on" else False,
        }
        db.autos.update_one({"_id": oid}, {"$set": data})
        return redirect(url_for("listar_autos_html"))
    return render_template("auto_form.html", auto=serialize_document(auto))


# ---------------------------------------------------------------------------
# Reparaciones - interfaz HTML
# ---------------------------------------------------------------------------

@app.route("/reparaciones/lista")
def listar_reparaciones_html() -> Any:
    """Lista de reparaciones en tabla HTML."""
    reparaciones: List[Dict[str, Any]] = list(db.reparaciones.find())
    # Convertir auto_id y formato de fecha
    reparaciones = [serialize_document(r) for r in reparaciones]
    # Añadir datos del auto (marca y modelo) para mostrar en la tabla
    for r in reparaciones:
        try:
            auto = db.autos.find_one({"_id": ObjectId(r.get("auto_id"))})
            if auto:
                r["auto"] = f"{auto.get('marca', '')} {auto.get('modelo', '')}"
        except Exception:
            pass
    return render_template("reparaciones.html", reparaciones=reparaciones)


@app.route("/reparaciones/nueva", methods=["GET", "POST"])
def nueva_reparacion() -> Any:
    """Formulario para registrar una reparación."""
    autos_disponibles = [serialize_document(a) for a in db.autos.find()]
    if request.method == "POST":
        auto_id = request.form.get("auto_id")
        descripcion = request.form.get("descripcion")
        fecha = parse_date(request.form.get("fecha"))
        costo_str = request.form.get("costo")
        if not auto_id or not descripcion or not fecha or not costo_str:
            return render_template(
                "reparacion_form.html",
                autos=autos_disponibles,
                error="Todos los campos son obligatorios"
            )
        try:
            auto_oid = ObjectId(auto_id)
        except Exception:
            return render_template(
                "reparacion_form.html",
                autos=autos_disponibles,
                error="Auto inválido"
            )
        try:
            costo = float(costo_str)
        except ValueError:
            return render_template(
                "reparacion_form.html",
                autos=autos_disponibles,
                error="Costo debe ser numérico"
            )
        reparacion = {
            "auto_id": auto_oid,
            "descripcion": descripcion,
            "fecha": fecha,
            "costo": costo,
        }
        db.reparaciones.insert_one(reparacion)
        return redirect(url_for("listar_reparaciones_html"))
    return render_template("reparacion_form.html", autos=autos_disponibles, error=None)


# ---------------------------------------------------------------------------
# Rentas - interfaz HTML
# ---------------------------------------------------------------------------

@app.route("/rentas/lista")
def listar_rentas_html() -> Any:
    rentas: List[Dict[str, Any]] = list(db.rentas.find())
    rentas = [serialize_document(r) for r in rentas]
    # Añadir nombres para auto y cliente
    for r in rentas:
        try:
            auto = db.autos.find_one({"_id": ObjectId(r.get("auto_id"))})
            cliente = db.clientes.find_one({"_id": ObjectId(r.get("cliente_id"))})
            if auto:
                r["auto"] = f"{auto.get('marca', '')} {auto.get('modelo', '')}"
            if cliente:
                r["cliente"] = f"{cliente.get('nombre', '')} {cliente.get('apellido', '')}"
        except Exception:
            pass
    return render_template("rentas.html", rentas=rentas)


@app.route("/rentas/nueva", methods=["GET", "POST"])
def nueva_renta() -> Any:
    """Formulario para crear una nueva renta."""
    # Listar autos disponibles
    autos_disp = [serialize_document(a) for a in db.autos.find({"disponible": True})]
    clientes = [serialize_document(c) for c in db.clientes.find()]
    if request.method == "POST":
        auto_id = request.form.get("auto_id")
        cliente_id = request.form.get("cliente_id")
        fecha_inicio = parse_date(request.form.get("fecha_inicio"))
        fecha_fin = parse_date(request.form.get("fecha_fin")) if request.form.get("fecha_fin") else None
        costo_str = request.form.get("costo")
        if not auto_id or not cliente_id or not fecha_inicio or not costo_str:
            return render_template(
                "renta_form.html",
                autos=autos_disp,
                clientes=clientes,
                error="Todos los campos obligatorios deben completarse"
            )
        try:
            auto_oid = ObjectId(auto_id)
            cliente_oid = ObjectId(cliente_id)
        except Exception:
            return render_template(
                "renta_form.html",
                autos=autos_disp,
                clientes=clientes,
                error="Identificadores inválidos"
            )
        try:
            costo = float(costo_str)
        except ValueError:
            return render_template(
                "renta_form.html",
                autos=autos_disp,
                clientes=clientes,
                error="Costo debe ser numérico"
            )
        auto = db.autos.find_one({"_id": auto_oid})
        if not auto or not auto.get("disponible", True):
            return render_template(
                "renta_form.html",
                autos=autos_disp,
                clientes=clientes,
                error="El auto no está disponible"
            )
        renta = {
            "auto_id": auto_oid,
            "cliente_id": cliente_oid,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "costo": costo,
            "estado": "activa"
        }
        db.rentas.insert_one(renta)
        # Marcar auto como no disponible
        db.autos.update_one({"_id": auto_oid}, {"$set": {"disponible": False}})
        return redirect(url_for("listar_rentas_html"))
    # GET
    return render_template("renta_form.html", autos=autos_disp, clientes=clientes, error=None)


# ---------------------------------------------------------------------------
# Devoluciones - interfaz HTML
# ---------------------------------------------------------------------------

@app.route("/devoluciones/lista")
def listar_devoluciones_html() -> Any:
    devoluciones: List[Dict[str, Any]] = list(db.devoluciones.find())
    devoluciones = [serialize_document(d) for d in devoluciones]
    # Añadir datos de auto y cliente mediante la renta
    for d in devoluciones:
        try:
            renta = db.rentas.find_one({"_id": ObjectId(d.get("renta_id"))})
            if renta:
                auto = db.autos.find_one({"_id": renta.get("auto_id")})
                cliente = db.clientes.find_one({"_id": renta.get("cliente_id")})
                if auto:
                    d["auto"] = f"{auto.get('marca', '')} {auto.get('modelo', '')}"
                if cliente:
                    d["cliente"] = f"{cliente.get('nombre', '')} {cliente.get('apellido', '')}"
        except Exception:
            pass
    return render_template("devoluciones.html", devoluciones=devoluciones)


@app.route("/devoluciones/nueva", methods=["GET", "POST"])
def nueva_devolucion() -> Any:
    """Formulario para registrar devolución."""
    # Filtrar rentas activas
    rentas_activas = [serialize_document(r) for r in db.rentas.find({"estado": "activa"})]
    if request.method == "POST":
        renta_id = request.form.get("renta_id")
        condicion = request.form.get("condicion")
        observaciones = request.form.get("observaciones")
        if not renta_id or not condicion:
            return render_template(
                "devolucion_form.html",
                rentas=rentas_activas,
                error="Selecciona la renta y la condición"
            )
        try:
            renta_oid = ObjectId(renta_id)
        except Exception:
            return render_template(
                "devolucion_form.html",
                rentas=rentas_activas,
                error="Identificador de renta inválido"
            )
        renta = db.rentas.find_one({"_id": renta_oid})
        if not renta:
            return render_template(
                "devolucion_form.html",
                rentas=rentas_activas,
                error="Renta no encontrada"
            )
        ahora = datetime.now()
        # Actualizar renta y auto
        db.rentas.update_one({"_id": renta_oid}, {"$set": {"estado": "devuelta", "fecha_fin": ahora}})
        db.autos.update_one({"_id": renta.get("auto_id")}, {"$set": {"disponible": True}})
        # Registrar devolución
        devolucion = {
            "renta_id": renta_oid,
            "auto_id": renta.get("auto_id"),
            "fecha_devolucion": ahora,
            "condicion": condicion,
            "observaciones": observaciones,
        }
        db.devoluciones.insert_one(devolucion)
        # Crear alerta si condición es mala
        condicion_lower = condicion.strip().lower()
        if condicion_lower in {"malo", "mal", "defectuoso", "dañado", "deteriorado"}:
            alerta = {
                "auto_id": renta.get("auto_id"),
                "fecha_alerta": ahora,
                "descripcion": "Vehículo devuelto en mal estado",
                "condicion": condicion_lower,
            }
            db.alertas.insert_one(alerta)
        return redirect(url_for("listar_devoluciones_html"))
    return render_template("devolucion_form.html", rentas=rentas_activas, error=None)


# ---------------------------------------------------------------------------
# Alertas - interfaz HTML
# ---------------------------------------------------------------------------

@app.route("/alertas/lista")
def listar_alertas_html() -> Any:
    alertas: List[Dict[str, Any]] = list(db.alertas.find())
    alertas = [serialize_document(a) for a in alertas]
    # Añadir dato de auto
    for a in alertas:
        try:
            auto = db.autos.find_one({"_id": ObjectId(a.get("auto_id"))})
            if auto:
                a["auto"] = f"{auto.get('marca', '')} {auto.get('modelo', '')}"
        except Exception:
            pass
    return render_template("alertas.html", alertas=alertas)


# ---------------------------------------------------------------------------
# Rutas de Reparaciones (RF03 y RF04)
# ---------------------------------------------------------------------------

@app.route("/reparaciones", methods=["POST"])
def registrar_reparacion() -> Any:
    """Registra una reparación para un auto.

    El cuerpo JSON debe incluir:
      - `auto_id`: identificador del auto.
      - `descripcion`: descripción de la reparación.
      - `fecha`: fecha de la reparación (AAAA-MM-DD).
      - `costo`: costo de la reparación.

    Las reparaciones no se eliminan; solo se registran o actualizan manualmente.
    """
    data: Dict[str, Any] = request.get_json(force=True) or {}
    required_fields = {"auto_id", "descripcion", "fecha", "costo"}
    if not required_fields.issubset(data):
        return jsonify({"error": "Faltan campos obligatorios en la reparación"}), 400
    try:
        auto_oid = ObjectId(data["auto_id"])
    except Exception:
        return jsonify({"error": "Identificador de auto inválido"}), 400
    fecha = parse_date(data.get("fecha"))
    if not fecha:
        return jsonify({"error": "Formato de fecha incorrecto. Use AAAA-MM-DD"}), 400
    # Construir documento de reparación
    reparacion = {
        "auto_id": auto_oid,
        "descripcion": data["descripcion"],
        "fecha": fecha,
        "costo": float(data.get("costo", 0))
    }
    result = db.reparaciones.insert_one(reparacion)
    inserted = db.reparaciones.find_one({"_id": result.inserted_id})
    return jsonify(serialize_document(inserted)), 201


@app.route("/reparaciones/consulta", methods=["GET"])
def consultar_reparaciones() -> Any:
    """Consulta reparaciones por periodo y costo (RF04).

    Recibe parámetros opcionales vía query:
      - `inicio`: fecha inicial (AAAA-MM-DD)
      - `fin`: fecha final (AAAA-MM-DD)
      - `costo_max`: costo máximo

    Devuelve todas las reparaciones que cumplan los filtros.
    """
    inicio_str = request.args.get("inicio")
    fin_str = request.args.get("fin")
    costo_max_str = request.args.get("costo_max")
    query: Dict[str, Any] = {}
    # Filtrar por fechas
    start = parse_date(inicio_str)
    end = parse_date(fin_str)
    if start and end:
        query["fecha"] = {"$gte": start, "$lte": end}
    elif start:
        query["fecha"] = {"$gte": start}
    elif end:
        query["fecha"] = {"$lte": end}
    # Filtrar por costo máximo
    if costo_max_str:
        try:
            costo_max = float(costo_max_str)
            query["costo"] = {"$lte": costo_max}
        except ValueError:
            return jsonify({"error": "costo_max debe ser numérico"}), 400
    reparaciones: List[Dict[str, Any]] = list(db.reparaciones.find(query))
    # Convertir auto_id a string al serializar
    return jsonify([serialize_document(r) for r in reparaciones]), 200


# ---------------------------------------------------------------------------
# Rutas de Rentas (RF05, RF06)
# ---------------------------------------------------------------------------

@app.route("/rentas", methods=["POST"])
def registrar_renta() -> Any:
    """Registra una renta nueva (RF05).

    Campos requeridos en el cuerpo JSON:
      - `auto_id`: ObjectId del auto a rentar.
      - `cliente_id`: ObjectId del cliente que realiza la renta.
      - `fecha_inicio`: fecha de inicio (AAAA-MM-DD).
      - `costo`: costo de la renta.
    Campos opcionales:
      - `fecha_fin`: fecha prevista de devolución (AAAA-MM-DD).

    Verifica que el auto esté disponible antes de registrar la renta.  Una vez
    creada la renta, se cambia el campo `disponible` del auto a `False`.
    """
    data: Dict[str, Any] = request.get_json(force=True) or {}
    required_fields = {"auto_id", "cliente_id", "fecha_inicio", "costo"}
    if not required_fields.issubset(data):
        return jsonify({"error": "Faltan campos obligatorios en la renta"}), 400
    try:
        auto_oid = ObjectId(data["auto_id"])
        cliente_oid = ObjectId(data["cliente_id"])
    except Exception:
        return jsonify({"error": "Identificadores inválidos"}), 400
    # Verificar que el auto exista y esté disponible
    auto = db.autos.find_one({"_id": auto_oid})
    if not auto:
        return jsonify({"error": "Auto no encontrado"}), 404
    if not auto.get("disponible", True):
        return jsonify({"error": "El auto no está disponible"}), 409
    fecha_inicio = parse_date(data.get("fecha_inicio"))
    if not fecha_inicio:
        return jsonify({"error": "Formato de fecha_inicio incorrecto"}), 400
    fecha_fin = parse_date(data.get("fecha_fin"))
    # Construir documento de renta
    renta = {
        "auto_id": auto_oid,
        "cliente_id": cliente_oid,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "costo": float(data.get("costo", 0)),
        "estado": "activa"
    }
    result = db.rentas.insert_one(renta)
    # Marcar auto como no disponible
    db.autos.update_one({"_id": auto_oid}, {"$set": {"disponible": False}})
    inserted = db.rentas.find_one({"_id": result.inserted_id})
    return jsonify(serialize_document(inserted)), 201


@app.route("/rentas/<string:renta_id>", methods=["PUT"])
def actualizar_renta(renta_id: str) -> Any:
    """Actualiza una renta existente.

    Permite modificar la fecha_fin, el costo o cualquier otro campo.  No
    permite cambiar el auto ni el cliente asociado.  Si la renta no existe,
    devuelve 404.
    """
    data: Dict[str, Any] = request.get_json(force=True) or {}
    try:
        renta_oid = ObjectId(renta_id)
    except Exception:
        return jsonify({"error": "Identificador de renta inválido"}), 400
    # Si se incluye fecha_inicio o fecha_fin en string, transformarlos a datetime
    if "fecha_inicio" in data:
        fecha_inicio = parse_date(data.get("fecha_inicio"))
        if not fecha_inicio:
            return jsonify({"error": "Formato de fecha_inicio incorrecto"}), 400
        data["fecha_inicio"] = fecha_inicio
    if "fecha_fin" in data and data.get("fecha_fin"):
        fecha_fin = parse_date(data.get("fecha_fin"))
        if not fecha_fin:
            return jsonify({"error": "Formato de fecha_fin incorrecto"}), 400
        data["fecha_fin"] = fecha_fin
    if "costo" in data:
        try:
            data["costo"] = float(data["costo"])
        except ValueError:
            return jsonify({"error": "El costo debe ser numérico"}), 400
    result = db.rentas.update_one({"_id": renta_oid}, {"$set": data})
    if result.matched_count == 0:
        return jsonify({"error": "Renta no encontrada"}), 404
    renta = db.rentas.find_one({"_id": renta_oid})
    return jsonify(serialize_document(renta)), 200


@app.route("/rentas/ultimos", methods=["GET"])
def rentas_ultimos_meses() -> Any:
    """Devuelve las rentas registradas en los últimos dos meses (RF06)."""
    # Definimos 60 días como aproximación de dos meses
    threshold = datetime.now() - timedelta(days=60)
    rentas: List[Dict[str, Any]] = list(db.rentas.find({"fecha_inicio": {"$gte": threshold}}))
    return jsonify([serialize_document(r) for r in rentas]), 200


# ---------------------------------------------------------------------------
# Rutas de Devoluciones y Alertas (RF09 y RF08)
# ---------------------------------------------------------------------------

@app.route("/devoluciones", methods=["POST"])
def registrar_devolucion() -> Any:
    """Registra la devolución de un auto (RF09).

    El cuerpo JSON debe incluir:
      - `renta_id`: identificador de la renta que se cierra.
      - `condicion`: estado del vehículo al devolverse (ej. "bueno" o "malo").
      - `observaciones`: observaciones opcionales.

    Si la condición del auto es mala, se genera una alerta (RF08).
    Además, se marca la renta como `devuelta`, se actualiza la fecha_fin con
    la fecha actual y se cambia el auto a disponible nuevamente.
    """
    data: Dict[str, Any] = request.get_json(force=True) or {}
    if not {"renta_id", "condicion"}.issubset(data):
        return jsonify({"error": "Se requiere renta_id y condicion"}), 400
    try:
        renta_oid = ObjectId(data["renta_id"])
    except Exception:
        return jsonify({"error": "Identificador de renta inválido"}), 400
    renta = db.rentas.find_one({"_id": renta_oid})
    if not renta:
        return jsonify({"error": "Renta no encontrada"}), 404
    # Actualizar renta: establecer estado devuelta y fecha_fin actual
    ahora = datetime.now()
    db.rentas.update_one(
        {"_id": renta_oid},
        {"$set": {"estado": "devuelta", "fecha_fin": ahora}}
    )
    # Actualizar auto a disponible
    auto_oid: ObjectId = renta["auto_id"]
    db.autos.update_one({"_id": auto_oid}, {"$set": {"disponible": True}})
    # Registrar devolución
    devolucion = {
        "renta_id": renta_oid,
        "auto_id": auto_oid,
        "fecha_devolucion": ahora,
        "condicion": data.get("condicion"),
        "observaciones": data.get("observaciones")
    }
    result = db.devoluciones.insert_one(devolucion)
    inserted_devolucion = db.devoluciones.find_one({"_id": result.inserted_id})
    # Generar alerta si la condición es mala
    condicion = data.get("condicion", "").strip().lower()
    if condicion in {"malo", "mal", "defectuoso", "dañado", "deteriorado"}:
        alerta = {
            "auto_id": auto_oid,
            "fecha_alerta": ahora,
            "descripcion": "Vehículo devuelto en mal estado",
            "condicion": condicion
        }
        db.alertas.insert_one(alerta)
    return jsonify(serialize_document(inserted_devolucion)), 201


@app.route("/alertas", methods=["GET"])
def listar_alertas() -> Any:
    """Devuelve todas las alertas generadas por devoluciones en mal estado."""
    alertas: List[Dict[str, Any]] = list(db.alertas.find())
    return jsonify([serialize_document(a) for a in alertas]), 200


if __name__ == "__main__":
    # Ejecutar la aplicación en modo debug para que recargue automáticamente
    app.run(debug=True)