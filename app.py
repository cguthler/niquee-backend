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
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:Segoe UI,system-ui,sans-serif;background:#0d1b2a;color:#ffff00;font-size:13px;line-height:1.3}
    h1{text-align:center;padding:12px 0 8px;font-size:1.4rem}
    .wrap{display:flex;gap:15px;max-width:1000px;margin:auto;padding:0 15px 30px}
    /* -------- columna izquierda -------- */
    .col-left{flex:0 0 260px;background:#1b263b;border-radius:10px;padding:10px;max-height:75vh;overflow-y:auto}
    .logo-titulo{text-align:center;margin-bottom:10px}
    .logo-titulo img{height:60px;border-radius:6px}
    .logo-titulo h2{margin-top:6px;font-size:1rem}
    .player{display:flex;align-items:center;gap:8px;margin-bottom:8px;background:#415a77;padding:6px;border-radius:6px}
    .player img{width:45px;height:45px;object-fit:cover;border-radius:50%}
    .info{font-size:11px}.info strong{display:block;font-size:12px;margin-bottom:1px}
    /* -------- columna derecha -------- */
    .col-right{flex:1 1 300px;background:#1b263b;border-radius:10px;padding:12px;text-align:center}
    .btns{margin-bottom:12px;display:flex;justify-content:center;gap:10px}
    .btn{background:#415a77;color:#ffff00;padding:6px 12px;border:none;border-radius:6px;cursor:pointer;font-size:12px;text-decoration:none}
    .btn:hover{background:#5a7fb0}
    .gallery{display:grid;grid-template-columns:1fr 1fr;gap:10px}
    .gallery img{width:100%;height:110px;object-fit:cover;border-radius:6px}
    /* -------- modal -------- */
    .modal{display:none;position:fixed;z-index:999;left:0;top:0;width:100%;height:100%;background:rgba(0,0,0,.7)}
    .modal-content{background:#1b263b;margin:10% auto;padding:20px;border-radius:10px;width:90%;max-width:500px;color:#ffff00;font-size:12px;line-height:1.4}
    .close{color:#ffff80;float:right;font-size:18px;font-weight:bold;cursor:pointer}
    .close:hover{color:#fff}
    /* -------- pie -------- */
    footer{text-align:center;padding:10px 5px;font-size:10px;background:#09101a;color:#ffff80;line-height:1.4}
    @media(max-width:700px){.wrap{flex-direction:column}.col-left{flex:1 1 auto}}
  </style>
</head>
<body>
  <h1>⚽ NIQUEE FÚTBOL CLUB</h1>

  <div class="wrap">
    <!--  COLUMNA IZQUIERDA  -->
    <section class="col-left">
      <div class="logo-titulo">
        <img src="{{ url_for('static', filename='uploads/logonegronique.jpg') }}" alt="Logo">
        <h2>Plantilla de jugadores</h2>
      </div>
      {% for j in jugadores %}
        <div class="player">
          <img src="{{ url_for('serve_img', name=j[6]) }}" alt="Foto">
          <div class="info">
            <strong>{{ j[1] }}</strong>
            <span>{{ j[2] }} • {{ j[3] }}</span>
            <span>G:{{ j[4] }} • A:{{ j[5] }}</span>
          </div>
        </div>
      {% endfor %}
    </section>

    <!--  COLUMNA DERECHA  -->
    <section class="col-right">
      <div class="btns">
        <a href="/admin" class="btn">Panel Admin</a>
        <button class="btn" onclick="document.getElementById('infoModal').style.display='block'">+ Info</button>
      </div>
      <h2>Fotos del Equipo</h2>
      <div class="gallery">
        <img src="{{ url_for('static', filename='uploads/niqueeblanco.jpg') }}" alt="Equipo 1">
        <img src="{{ url_for('static', filename='uploads/logo.png') }}" alt="Equipo 2">
        <img src="{{ url_for('static', filename='uploads/gruponique.jpg') }}" alt="Equipo 3">
        <img src="{{ url_for('static', filename='uploads/niqueazul.jpg') }}" alt="Equipo 4">
      </div>
    </section>
  </div>

  <!--  MODAL  -->
  <div id="infoModal" class="modal">
    <div class="modal-content">
      <span class="close" onclick="document.getElementById('infoModal').style.display='none'">&times;</span>
      <h3>Información del Club</h3>
      <p>
        Niquee Fútbol Club nació en 2017 en Guayaquil con la filosofía de adoracion a Dios, juego limpio y trabajo en equipo.
        Participamos en ligas barriales y torneos locales. ¡Buscamos talento honestidad lealtad!<br>
        Entrenamientos: lun/mié/vie 18:00-20:00 | Cancha: sinteticas futbol<br>
        Redes: <a href="https://www.facebook.com/share/1CWH1PEHMU/" target="_blank" style="color:#ffff80">Facebook</a>
      </p>
    </div>
  </div>

  <footer>
    @transguthler&asociados • Tfns 593958787986-593992123592<br>
    cguthler@hotmail.com • <a href="https://www.facebook.com/share/1CWH1PEHMU/" target="_blank" style="color:#ffff80">fb.me/share/1CWH1PEHMU</a><br>
    Guayaquil – Ecuador
  </footer>
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
@app.route("/")
def index():
    return "¡Hola! Tu editor visual está aquí. Ve a /editor para el formulario."
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))