from flask import Flask, request, redirect, url_for, send_from_directory
from pathlib import Path
import sqlite3, os
from datetime import date
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "clave_secreta_niquee"

UPLOAD_IMG = "static/uploads"
UPLOAD_DOCS = "static/uploads/docs"
os.makedirs(UPLOAD_IMG, exist_ok=True)
os.makedirs(UPLOAD_DOCS, exist_ok=True)

ADMIN_PASSWORD = "admin123"

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

init_db()

# ---------- HTML ----------
ADMIN_LOGIN_HTML = """
<form method="post" style="max-width:300px;margin:auto">
  <h2>Admin Login</h2>
  <input type="password" name="password" placeholder="Contraseña" style="width:100%;padding:8px">
  <button type="submit" style="width:100%;margin-top:10px">Entrar</button>
</form>
"""

admin_panel_html = Path("templates/admin_panel.html").read_text(encoding="utf-8")

# ---------- rutas ----------
@app.route("/")
def index():
    return "Vista pública 👍"

@app.route("/admin")
def admin():
    return admin_panel_html

@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            return redirect(url_for("admin"))
        return "Clave incorrecta <a href='.'>Reintentar</a>"
    return ADMIN_LOGIN_HTML

# ---------- para Render ----------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)