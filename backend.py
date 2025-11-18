from flask import Flask, send_from_directory, request
import os

app = Flask(__name__)
UPLOAD = "documentos"
os.makedirs(UPLOAD, exist_ok=True)

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    if file:
        path = os.path.join(UPLOAD, file.filename)
        file.save(path)
        return {"url": f"/documentos/{file.filename}"}, 200
    return {"error": "Sin archivo"}, 400

@app.route("/documentos/<path:name>")
def serve_file(name):
    return send_from_directory(UPLOAD, name)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)