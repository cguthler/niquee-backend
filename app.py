# ---------------  app.py (Flask + Admin + PDF) ---------------
import os
import secrets
import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, send_from_directory, session
from datetime import date
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET") or secrets.token_hex(32)

UPLOAD_IMG = "static/uploads"
UPLOAD_DOCS = "static/uploads/docs"
os.makedirs(UPLOAD_IMG, exist_ok=True)
os.makedirs(UPLOAD_DOCS, exist_ok=True)

ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH") or generate_password_hash("admin123")


# ---------- BD ----------
def init_db():
    conn = sqlite3.connect("jugadores.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jugadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            anio_nacimiento INTEGER,
            posicion TEXT,
            goles INTEGER,
            asistencias INTEGER,
            imagen TEXT,
            fecha_ingreso TEXT,
            pdf TEXT
        )
    """)
    conn.commit()
    conn.close()


# ---------- RUTAS ----------
@app.route("/")
def index():
    conn = sqlite3.connect("jugadores.db")
    cursor = conn.cursor()
    rows = cursor.execute("SELECT * FROM jugadores ORDER BY id DESC").fetchall()
    conn.close()
    return render_template_string(INDEX_HTML, jugadores=rows)


@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if check_password_hash(ADMIN_PASSWORD_HASH, request.form["password"]):
            session["admin"] = True
            return redirect(url_for("admin_panel"))
        else:
            return "❌ Contraseña incorrecta"
    return render_template_string(ADMIN_LOGIN_HTML)


@app.route("/admin/panel")
def admin_panel():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    conn = sqlite3.connect("jugadores.db")
    cursor = conn.cursor()
    rows = cursor.execute("SELECT * FROM jugadores ORDER BY id DESC").fetchall()
    conn.close()
    return render_template_string(ADMIN_PANEL_HTML, jugadores=rows)


@app.route("/guardar", methods=["POST"])
def guardar():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    nombre = request.form["nombre"]
    anio = request.form["anio_nacimiento"]
    posicion = request.form["posicion"]
    goles = request.form["goles"]
    asistencias = request.form["asistencias"]
    imagen = ""
    if "imagen" in request.files:
        file = request.files["imagen"]
        if file and file.filename != "":
            ext = file.filename.rsplit(".", 1)[1].lower()
            if ext not in {"png", "jpg", "jpeg", "gif", "webp"} or file.content_length > 2 * 1024 * 1024:
                return "Imagen no permitida o muy pesada", 400
            filename = secure_filename(file.filename)
            path = os.path.join(UPLOAD_IMG, filename)
            file.save(path)
            imagen = filename
    conn = sqlite3.connect("jugadores.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO jugadores (nombre, anio_nacimiento, posicion, goles, asistencias, imagen, fecha_ingreso, pdf) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (nombre, int(anio), posicion, int(goles), int(asistencias), imagen, date.today().isoformat(), "")
    )
    conn.commit()
    conn.close()
    return redirect(url_for("admin_panel"))


@app.route("/subir_pdf/<int:jugador_id>", methods=["POST"])
def subir_pdf(jugador_id):
    file = request.files["pdf"]
    if not (file and file.filename.endswith(".pdf") and file.content_length <= 3 * 1024 * 1024):
        return "Archivo no válido", 400
    conn = sqlite3.connect("jugadores.db")
    cursor = conn.cursor()
    row = cursor.execute("SELECT nombre FROM jugadores WHERE id = ?", (jugador_id,)).fetchone()
    if not row:
        conn.close()
        return "Jugador no encontrado", 404
    nombre_jugador = row[0]
    filename = f"{nombre_jugador}.pdf"
    path = os.path.join(UPLOAD_DOCS, filename)
    file.save(path)
    cursor.execute("UPDATE jugadores SET pdf = ? WHERE id = ?", (filename, jugador_id))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/uploads/<path:name>")
def serve_img(name):
    return send_from_directory(UPLOAD_IMG, name)


@app.route("/docs/<path:name>")
def serve_pdf(name):
    if not session.get("admin"):
        return "❌ Acceso denegado"
    return send_from_directory(UPLOAD_DOCS, name)


@app.route("/borrar/<int:jugador_id>")
def borrar(jugador_id):
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    conn = sqlite3.connect("jugadores.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jugadores WHERE id = ?", (jugador_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_panel"))


# ---------- HTML ----------
INDEX_HTML = """..."""  # (todo tu bloque HTML sin cambios)

ADMIN_LOGIN_HTML = """..."""

ADMIN_PANEL_HTML = """..."""

# ---------- Inicializar BD al arrancar ----------
if not os.path.exists("jugadores.db"):
    init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))