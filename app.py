"""
CONTROL DE GASTOS ESTUDIANTILES - UNIFRANZ
Backend en Flask. Guarda usuarios y datos en archivos JSON.
"""

from flask import Flask, jsonify, request, render_template
import json
import os

app = Flask(__name__)

# Rutas a los archivos JSON
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
USUARIOS_FILE = os.path.join(DATA_DIR, "usuarios.json")

os.makedirs(DATA_DIR, exist_ok=True)


# ---------- FUNCIONES AUXILIARES ----------

def cargar_usuarios():
    """Lee el archivo usuarios.json y devuelve un diccionario."""
    if not os.path.exists(USUARIOS_FILE):
        return {}
    with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def guardar_usuarios(usuarios):
    """Escribe el diccionario de usuarios en usuarios.json."""
    with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=4, ensure_ascii=False)


# ---------- RUTAS DE PÁGINAS ----------

@app.route("/")
def index():
    return render_template("index.html")


# ---------- API: AUTENTICACIÓN ----------

@app.route("/api/registro", methods=["POST"])
def registro():
    body = request.get_json()
    usuario = body.get("usuario", "").strip()
    contrasena = body.get("contrasena", "")

    if not usuario or not contrasena:
        return jsonify({"ok": False, "mensaje": "Todos los campos son obligatorios."}), 400

    usuarios = cargar_usuarios()

    if usuario in usuarios:
        return jsonify({"ok": False, "mensaje": "El usuario ya existe."}), 400

    usuarios[usuario] = {
        "contrasena": contrasena,
        "saldo": 0,
        "total_gastos": 0,
        "total_ingresos": 0,
        "gastos": []
    }
    guardar_usuarios(usuarios)

    return jsonify({"ok": True, "mensaje": "Usuario registrado correctamente."})


@app.route("/api/login", methods=["POST"])
def login():
    body = request.get_json()
    usuario = body.get("usuario", "").strip()
    contrasena = body.get("contrasena", "")

    usuarios = cargar_usuarios()
    datos = usuarios.get(usuario)

    if not datos or datos["contrasena"] != contrasena:
        return jsonify({"ok": False, "mensaje": "Usuario o contraseña incorrectos."}), 401

    return jsonify({
        "ok": True,
        "usuario": usuario,
        "saldo": datos["saldo"],
        "total_gastos": datos["total_gastos"],
        "total_ingresos": datos["total_ingresos"],
        "gastos": datos["gastos"]
    })


# ---------- API: INGRESOS Y GASTOS ----------

@app.route("/api/ingreso", methods=["POST"])
def registrar_ingreso():
    body = request.get_json()
    usuario = body.get("usuario")
    monto = body.get("monto")

    if monto is None or monto <= 0:
        return jsonify({"ok": False, "mensaje": "Debe ingresar un monto mayor a 0."}), 400

    usuarios = cargar_usuarios()
    if usuario not in usuarios:
        return jsonify({"ok": False, "mensaje": "Usuario no encontrado."}), 404

    usuarios[usuario]["saldo"] += monto
    usuarios[usuario]["total_ingresos"] += monto
    guardar_usuarios(usuarios)

    return jsonify({
        "ok": True,
        "saldo": usuarios[usuario]["saldo"],
        "total_ingresos": usuarios[usuario]["total_ingresos"]
    })


@app.route("/api/gasto", methods=["POST"])
def registrar_gasto():
    body = request.get_json()
    usuario = body.get("usuario")
    fecha = body.get("fecha", "").strip()
    monto = body.get("monto")
    categoria = body.get("categoria", "").strip()

    if not fecha:
        return jsonify({"ok": False, "mensaje": "La fecha es obligatoria."}), 400
    if monto is None or monto <= 0:
        return jsonify({"ok": False, "mensaje": "Debe ingresar un monto mayor a 0."}), 400
    if not categoria:
        return jsonify({"ok": False, "mensaje": "La categoría no puede quedar vacía."}), 400

    usuarios = cargar_usuarios()
    if usuario not in usuarios:
        return jsonify({"ok": False, "mensaje": "Usuario no encontrado."}), 404

    datos = usuarios[usuario]

    if monto > datos["saldo"]:
        return jsonify({"ok": False, "mensaje": "Saldo insuficiente."}), 400

    datos["saldo"] -= monto
    datos["total_gastos"] += monto
    datos["gastos"].insert(0, {
        "fecha": fecha,
        "categoria": categoria,
        "monto": monto
    })

    guardar_usuarios(usuarios)

    return jsonify({
        "ok": True,
        "saldo": datos["saldo"],
        "total_gastos": datos["total_gastos"],
        "gastos": datos["gastos"]
    })


# ---------- INICIO DEL SERVIDOR ----------

if __name__ == "__main__":
    app.run(debug=True)
