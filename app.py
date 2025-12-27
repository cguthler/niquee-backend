# app.py — NIQUEE FÚTBOL CLUB (Flask) — Opción A (guardar DB en repo con db_sync)
from flask import (
    Flask, render_template_string, request, redirect,
    url_for, send_from_directory, session
)
import sqlite3
import os
from datetime import date
from werkzeug.utils import secure_filename
import atexit

# ------------------------------------------------------------------
# 1.  Imports opcionales (db_sync deshabilitado por ahora)
# ------------------------------------------------------------------
# from db_sync import pull_db, push_db, close_repo

# ------------------------------------------------------------------
# 2.  Cloudinary
# ------------------------------------------------------------------
import cloudinary
from cloudinary.uploader import upload, destroy
from cloudinary.utils import cloudinary_url

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True
)

# ------------------------------------------------------------------
# 3.  db_sync deshabilitado
# ------------------------------------------------------------------
# repo, tmp_dir = pull_db()
tmp_dir = "/tmp"  # dummy para que no falle el print
print("db_sync: repo clonado en:", tmp_dir)

def _final_sync():
    """Fallback al cerrar el proceso."""
    # try:
    #     push_db(repo, tmp_dir)
    #     print("db_sync: push final OK (atexit)")
    # except Exception as e:
    #     print("db_sync: error en push final (atexit):", e)
    # try:
    #     close_repo(repo, tmp_dir)
    # except Exception as e:
    #     print("db_sync: error cerrando repo:", e)
    pass

# atexit.register(_final_sync)

# ------------------------------------------------------------------
# 4.  Flask init
# ------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "clave_secreta_niquee")

UPLOAD_IMG = "static/uploads"
UPLOAD_DOCS = "static/uploads/docs"
os.makedirs(UPLOAD_IMG, exist_ok=True)
os.makedirs(UPLOAD_DOCS, exist_ok=True)

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "jeremias123")
PDF_PASSWORD = os.environ.get("PDF_PASSWORD", "guthler")
DB_FILE = "jugadores.db"

# ------------------------------------------------------------------
# 5.  Base de datos
# ------------------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
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

    # push para persistir estructura (deshabilitado)
    # try:
    #     push_db(repo, tmp_dir)
    #     print("db_sync: push en init_db -> OK")
    # except Exception as e:
    #     print("db_sync: fallo push en init_db:", e)

# ------------------------------------------------------------------
# 6.  Rutas
# ------------------------------------------------------------------
@app.route("/")
def index():
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    rows = cursor.execute(
        "SELECT * FROM jugadores ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return render_template_string(
        INDEX_HTML,
        jugadores=rows,
        PDF_PASSWORD=PDF_PASSWORD
    )

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_panel"))
        else:
            return "❌ Contraseña incorrecta"
    return render_template_string(ADMIN_LOGIN_HTML)

@app.route("/admin/panel")
def admin_panel():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    rows = cursor.execute(
        "SELECT * FROM jugadores ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return render_template_string(ADMIN_PANEL_HTML, jugadores=rows)

@app.route("/guardar", methods=["POST"])
def guardar():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    nombre = request.form.get("nombre", "").strip()
    anio = request.form.get("anio_nacimiento", "").strip() or "0"
    posicion = request.form.get("posicion", "").strip()
    goles = request.form.get("goles", "0").strip() or "0"
    asistencias = request.form.get("asistencias", "0").strip() or "0"

    imagen = ""
    if "imagen" in request.files:
        file = request.files["imagen"]
        if file and file.filename != "":
            result = upload(file, folder="niquee/jugadores")
            imagen = result["secure_url"]

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO jugadores "
        "(nombre, anio_nacimiento, posicion, goles, asistencias, "
        "imagen, fecha_ingreso, pdf) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            nombre, int(anio), posicion, int(goles), int(asistencias),
            imagen, date.today().isoformat(), ""
        )
    )
    conn.commit()
    conn.close()

    # push inmediato (deshabilitado)
    # try:
    #     push_db(repo, tmp_dir)
    #     print("db_sync: push en guardar -> OK")
    # except Exception as e:
    #     print("db_sync: fallo push en guardar:", e)

    return redirect(url_for("admin_panel"))

@app.route("/subir_pdf/<int:jugador_id>", methods=["POST"])
def subir_pdf(jugador_id):
    if "pdf" not in request.files:
        return "Archivo no válido", 400
    file = request.files["pdf"]
    if file and file.filename.lower().endswith(".pdf"):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        row = cursor.execute(
            "SELECT nombre FROM jugadores WHERE id = ?", (jugador_id,)
        ).fetchone()
        if not row:
            conn.close()
            return "Jugador no encontrado", 404
        nombre_jugador = row[0] or f"jugador_{jugador_id}"
        safe_name = secure_filename(f"{nombre_jugador}_{jugador_id}.pdf")
        path = os.path.join(UPLOAD_DOCS, safe_name)
        file.save(path)
        cursor.execute(
            "UPDATE jugadores SET pdf = ? WHERE id = ?",
            (safe_name, jugador_id)
        )
        conn.commit()
        conn.close()

        # push inmediato (deshabilitado)
        # try:
        #     push_db(repo, tmp_dir)
        #     print("db_sync: push en subir_pdf -> OK")
        # except Exception as e:
        #     print("db_sync: fallo push en subir_pdf:", e)

        return redirect(url_for("index"))
    return "Archivo no válido (debe ser .pdf)", 400

@app.route("/uploads/<path:name>")
def serve_img(name):
    if not name:
        return send_from_directory("static", "placeholder.png")
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
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    row = cursor.execute(
        "SELECT imagen, pdf FROM jugadores WHERE id = ?", (jugador_id,)
    ).fetchone()
    if row:
        imagen, pdf = row
        if imagen and imagen.startswith("http"):
            public_id = imagen.split("/")[-1].split(".")[0]
            destroy(f"niquee/jugadores/{public_id}")
        if pdf:
            try:
                os.remove(os.path.join(UPLOAD_DOCS, pdf))
            except Exception:
                pass

    cursor.execute("DELETE FROM jugadores WHERE id = ?", (jugador_id,))
    conn.commit()
    conn.close()

    # push inmediato (deshabilitado)
    # try:
    #     push_db(repo, tmp_dir)
    #     print("db_sync: push en borrar -> OK")
    # except Exception as e:
    #     print("db_sync: fallo push en borrar:", e)

    return redirect(url_for("admin_panel"))

# ------------------------------------------------------------------
# 7.  Plantillas HTML
# ------------------------------------------------------------------
INDEX_HTML = """..."""  # (muy larga, se deja igual)
ADMIN_LOGIN_HTML = """..."""
ADMIN_PANEL_HTML = """..."""

# ------------------------------------------------------------------
# 8.  Arranque
# ------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Iniciando app Flask en 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port)