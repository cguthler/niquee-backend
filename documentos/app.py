# ---------------  app.py (Flask + Render)  ---------------
from flask import Flask, request, redirect, url_for, send_from_directory
from pathlib import Path
import sqlite3, os
from datetime import date
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

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
            fecha_ingreso TEXT
        )
    """)
    conn.commit()
    conn.close()

# ---------- HTML ----------
index_html = Path("templates/index.html").read_text(encoding="utf-8")

# ---------- RUTAS ----------
@app.route("/")
def index():
    init_db()
    conn = sqlite3.connect("jugadores.db")
    cursor = conn.cursor()
    rows = cursor.execute("SELECT * FROM jugadores ORDER BY id DESC").fetchall()
    conn.close()

    # reemplazo simple sin Jinja
    filas = ""
    for j in rows:
        img_tag = f"<br><img src='/uploads/{j[6]}' style='max-width:120px;border-radius:6px'>" if j[6] else ""
        filas += f"""
        <div class="item">
          <strong>{j[1]}</strong> | {j[2]} | {j[3]} | ⚽{j[4]} | 🅰️{j[5]} | Ingreso: {j[7]} {img_tag}
        </div>
        """
    return index_html.replace("{{filas}}", filas)

@app.route("/guardar", methods=["POST"])
def guardar():
    nombre = request.form["nombre"]
    anio = request.form["anio_nacimiento"]
    posicion = request.form["posicion"]
    goles = request.form["goles"]
    asistencias = request.form["asistencias"]
    imagen = ""
    if "imagen" in request.files:
        file = request.files["imagen"]
        if file.filename != "":
            filename = secure_filename(file.filename)
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(path)
            imagen = filename
    conn = sqlite3.connect("jugadores.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO jugadores (nombre, anio_nacimiento, posicion, goles, asistencias, imagen, fecha_ingreso) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (nombre, int(anio), posicion, int(goles), int(asistencias), imagen, date.today().isoformat())
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

@app.route("/uploads/<path:name>")
def serve_img(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)