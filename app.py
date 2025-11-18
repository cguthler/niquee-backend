# ---------------  app.py (Flask + Admin + PDF)  ---------------
from flask import Flask, render_template_string, request, redirect, url_for, send_from_directory, session
import sqlite3, os
from datetime import date
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "clave_secreta_niquee"

UPLOAD_IMG = "static/uploads"
UPLOAD_DOCS = "static/uploads/docs"
os.makedirs(UPLOAD_IMG, exist_ok=True)
os.makedirs(UPLOAD_DOCS, exist_ok=True)

ADMIN_PASSWORD = "admin123"  # ← la cambias aquí cuando quieras

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
    init_db()
    conn = sqlite3.connect("jugadores.db")
    cursor = conn.cursor()
    rows = cursor.execute("SELECT * FROM jugadores ORDER BY id DESC").fetchall()
    conn.close()
    return render_template_string(INDEX_HTML, jugadores=rows)

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
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
        if file.filename != "":
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
    if file and file.filename.endswith(".pdf"):
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
    return "Archivo no válido", 400

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
    a{color:#ffff00}
  </style>
</head>
<body>
  <h1>⚽ NIQUEE FÚTBOL CLUB</h1>
  <div class="lista">
    <h2>Plantilla</h2>
    {% for j in jugadores %}
      <div class="item">
        <strong>{{ j[1] }}</strong> | {{ j[2] }} | {{ j[3] }} | ⚽{{ j[4] }} | 🅰️{{ j[5] }} | Ingreso: {{ j[7] }}
        {% if j[6] %}
          <br><img src="{{ url_for('serve_img', name=j[6]) }}" alt="Foto">
        {% endif %}
        <br>
        {% if j[8] %}
          ✅ PDF subido
        {% else %}
          ❌ Sin PDF
        {% endif %}
        <form action="{{ url_for('subir_pdf', jugador_id=j[0]) }}" method="post" enctype="multipart/form-data" style="margin-top:8px;">
          <input type="file" name="pdf" accept="application/pdf" required>
          <button type="submit">Subir PDF</button>
        </form>
      </div>
    {% endfor %}
  </div>
  <br>
  <div style="text-align:center">
    <a href="/admin" style="background:#415a77;padding:10px 20px;border-radius:8px;color:#ffff00;text-decoration:none;">Panel Admin</a>
  </div>
</body>
</html>
"""

ADMIN_LOGIN_HTML = """
<form method="post" style="max-width:300px;margin:auto">
  <h2>Admin Login</h2>
  <input type="password" name="password" placeholder="Contraseña" style="width:100%;padding:8px">
  <button type="submit" style="width:100%;margin-top:10px">Entrar</button>
</form>
"""

ADMIN_PANEL_HTML = """
<h2>Panel Admin</h2>
<a href="/">Ver vista pública</a>
<form method="post" action="/guardar" enctype="multipart/form-data">
  <label>Nombre completo</label><input name="nombre" required>
  <label>Año de nacimiento</label><input type="number" name="anio_nacimiento" required>
  <label>Posición</label><input name="posicion" required>
  <label>Goles</label><input type="number" name="goles" required>
  <label>Asistencias</label><input type="number" name="asistencias" required>
  <label>Foto</label><input type="file" name="imagen" accept="image/*">
  <button type="submit">Guardar Jugador</button>
</form>
<hr>
{% for j in jugadores %}
  <div>
    <strong>{{ j[1] }}</strong> |
    <a href="/docs/{{ j[8] }}">📄 Ver PDF</a> |
    <a href="/borrar/{{ j[0] }}" onclick="return confirm('¿Borrar?')">🗑️ Borrar</a>
  </div>
{% endfor %}
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))