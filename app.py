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

ADMIN_PASSWORD = "admin123"   # ← la cambias aquí cuando quieras

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
    body{font-family:Segoe UI,system-ui,sans-serif;background:#0d1b2a;color:#ffff00;font-size:14px;line-height:1.4}
    h1{text-align:center;padding:14px 0 10px;font-size:1.5rem}
    .wrap{display:flex;gap:20px;max-width:1280px;margin:auto;padding:0 20px 40px}
    /* -------- columna izquierda -------- */
    .col-left{flex:0 0 320px;background:#1b263b;border-radius:12px;padding:12px;max-height:75vh;overflow-y:auto}
    .logo-titulo{text-align:center;margin-bottom:12px}
    .logo-titulo img{height:70px;border-radius:8px}
    .logo-titulo h2{margin-top:8px;font-size:1.1rem}
    .player{display:flex;align-items:center;gap:10px;margin-bottom:10px;background:#415a77;padding:8px;border-radius:8px;cursor:pointer}
    .player img{width:50px;height:50px;object-fit:cover;border-radius:50%}
    .info{font-size:12px}.info strong{display:block;font-size:13px;margin-bottom:2px}
    /* -------- columna derecha -------- */
    .col-right{flex:1 1 300px;background:#1b263b;border-radius:12px;padding:15px;text-align:center}
    .btns{margin-bottom:15px;display:flex;justify-content:center;gap:12px}
    .btn{background:#415a77;color:#ffff00;padding:8px 14px;border:none;border-radius:6px;cursor:pointer;font-size:12px;text-decoration:none}
    .btn:hover{background:#5a7fb0}
    .gallery{display:grid;grid-template-columns:1fr 1fr;gap:12px}
    .gallery img{width:100%;height:120px;object-fit:cover;border-radius:8px}
    /* -------- modal jugador -------- */
    .player-modal{display:none;position:fixed;z-index:999;left:0;top:0;width:100%;height:100%;background:rgba(0,0,0,.7)}
    .player-modal-content{background:#1b263b;margin:5% auto;padding:25px;border-radius:12px;width:90%;max-width:500px;color:#ffff80;font-size:13px;line-height:1.5}
    .player-modal-content img{max-width:220px;border-radius:8px;margin-bottom:12px}
    .close-player{color:#ffff80;float:right;font-size:20px;font-weight:bold;cursor:pointer}
    .close-player:hover{color:#fff}
    /* -------- modal info general -------- */
    .modal{display:none;position:fixed;z-index:998;left:0;top:0;width:100%;height:100%;background:rgba(0,0,0,.7)}
    .modal-content{background:#1b263b;margin:10% auto;padding:20px;border-radius:10px;width:90%;max-width:500px;color:#ffff00;font-size:12px;line-height:1.4}
    .close{color:#ffff80;float:right;font-size:18px;font-weight:bold;cursor:pointer}
    .close:hover{color:#fff}
    /* -------- pie -------- */
    footer{text-align:center;padding:8px 5px;font-size:10px;background:#09101a;color:#ffff80;white-space:nowrap}
    @media(max-width:900px){.wrap{flex-direction:column}.col-left{flex:1 1 auto}}
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

      <!--  LISTA DE JUGADORES  -->
      <div id="player-list">
        {% for j in jugadores %}
          <div class="player" onclick="openPlayerModal({{ j[0] }}, '{{ j[1] }}', {{ j[2] }}, '{{ j[3] }}', {{ j[4] }}, {{ j[5] }}, '{{ j[6] }}', '{{ j[7] }}')">
            <img src="{{ url_for('serve_img', name=j[6]) }}" alt="Foto">
            <div class="info">
              <strong>{{ j[1] }}</strong>
              <span>{{ j[3] }}</span>
            </div>
          </div>
        {% endfor %}
      </div>
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
        <img src="{{ url_for('static', filename='uploads/niquenegro.jpg') }}" alt="Equipo 2">
        <img src="{{ url_for('static', filename='uploads/gruponique.jpg') }}" alt="Equipo 3">
        <img src="{{ url_for('static', filename='uploads/niqueazul.jpg') }}" alt="Equipo 4">
      </div>
    </section>
  </div>

  <!--  MODAL JUGADOR  -->
  <div id="playerModal" class="player-modal" onclick="if(event.target==this)this.style.display='none'">
    <div class="player-modal-content">
      <span class="close-player" onclick="document.getElementById('playerModal').style.display='none'">&times;</span>
      <div style="text-align:center">
        <img id="playerImg" src="" alt="Foto">
        <h3 id="playerName"></h3>
        <p><strong>Año:</strong> <span id="playerYear"></span></p>
        <p><strong>Posición:</strong> <span id="playerPos"></span></p>
        <p><strong>Goles:</strong> <span id="playerGoals"></span></p>
        <p><strong>Asistencias:</strong> <span id="playerAssists"></span></p>
        <p><strong>Ingreso:</strong> <span id="playerDate"></span></p>
        <!--  ÚNICO BOTÓN MODIFICABLE  -->
        <form id="pdfForm" action="" method="post" enctype="multipart/form-data" style="margin-top:12px;">
          <input type="file" name="pdf" accept="application/pdf" required>
          <button type="submit" class="btn">Adjuntar PDF</button>
        </form>
      </div>
    </div>
  </div>

  <!--  MODAL INFO GENERAL  -->
  <div id="infoModal" class="modal">
    <div class="modal-content">
      <span class="close" onclick="document.getElementById('infoModal').style.display='none'">&times;</span>
      <h3>Información del Club</h3>
      <p>
        Niquee Fútbol Club nació en 2017 en Guayaquil con la filosofía de adoración a Dios, juego limpio y trabajo en equipo.
        Participamos en ligas barriales y torneos locales. ¡Buscamos talento, honestidad, lealtad!<br>
        Entrenamientos: lun/mié/vie 18:00-20:00 | Cancha: sintéticas fútbol<br>
        Redes: <a href="https://www.facebook.com/share/1CWH1PEHMU/" target="_blank" style="color:#ffff80">Facebook</a>
      </p>
    </div>
  </div>

  <footer>
    @transguthler&asociados • Tfns 593958787986-593992123592 • cguthler@hotmail.com • <a href="https://www.facebook.com/share/1CWH1PEHMU/" target="_blank" style="color:#ffff80">fb.me/share/1CWH1PEHMU</a> • Guayaquil – Ecuador
  </footer>

  <script>
    function openPlayerModal(id, nombre, anio, posicion, goles, asistencias, imagen, fechaIng) {
      document.getElementById('playerModal').style.display = 'block';
      document.getElementById('playerImg').src = "{{ url_for('serve_img', name='') }}" + imagen;
      document.getElementById('playerName').textContent = nombre;
      document.getElementById('playerYear').textContent = anio;
      document.getElementById('playerPos').textContent = posicion;
      document.getElementById('playerGoals').textContent = goles;
      document.getElementById('playerAssists').textContent = asistencias;
      document.getElementById('playerDate').textContent = fechaIng;
      document.getElementById('pdfForm').action = "/subir_pdf/" + id;
    }
  </script>
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