# ---------------  app.py (Flask)  ---------------
from flask import Flask, render_template_string, request, redirect, url_for, send_from_directory
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

# ---------- RUTAS ----------
@app.route("/")
def index():
    init_db()
    conn = sqlite3.connect("jugadores.db")
    cursor = conn.cursor()
    rows = cursor.execute("SELECT * FROM jugadores ORDER BY id DESC").fetchall()
    conn.close()
    return render_template_string(INDEX_HTML, jugadores=rows)

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

# ---------- HTML ----------
INDEX_HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>⚽ NIQUEE FÚTBOL CLUB</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    body{font-family:Segoe UI,system-ui,sans-serif;background:#0d1b2a;color:#ffff00;margin:0;padding:20px}
    h1{text-align:center;margin-bottom:30px}
    form{background:#1b263b;padding:20px;border-radius:12px;max-width:400px;margin:auto}
    label{display:block;margin:8px 0 4px}
    input,select{width:100%;padding:8px;border:none;border-radius:6px}
    button{width:100%;padding:10px;margin-top:12px;border:none;border-radius:8px;background:#415a77;color:#ffff00;font-weight:bold;cursor:pointer}
    button:hover{background:#5a7fb0}
    .lista{background:#1b263b;margin-top:30px;padding:15px;border-radius:12px}
    .item{background:#415a77;margin:8px 0;padding:10px;border-radius:8px}
    img{max-width:120px;border-radius:6px}
  </style>
</head>
<body>
  <h1>⚽ NIQUEE FÚTBOL CLUB</h1>
  <form action="/guardar" method="post" enctype="multipart/form-data">
    <label>Nombre completo</label>
    <input type="text" name="nombre" required>
    <label>Año de nacimiento</label>
    <input type="number" name="anio_nacimiento" required>
    <label>Posición</label>
    <input type="text" name="posicion" required>
    <label>Goles</label>
    <input type="number" name="goles" required>
    <label>Asistencias</label>
    <input type="number" name="asistencias" required>
    <label>Foto del jugador</label>
    <input type="file" name="imagen" accept="image/*">
    <button type="submit">Guardar Jugador</button>
  </form>

  <div class="lista">
    <h2>Plantilla</h2>
    {% for j in jugadores %}
      <div class="item">
        <strong>{{ j[1] }}</strong> | {{ j[2] }} | {{ j[3] }} | ⚽{{ j[4] }} | 🅰️{{ j[5] }} | Ingreso: {{ j[7] }}
        {% if j[6] %}
          <br><img src="{{ url_for('serve_img', name=j[6]) }}" alt="Foto">
        {% endif %}
      </div>
    {% endfor %}
  </div>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))