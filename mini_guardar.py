import sqlite3
conn = sqlite3.connect('jugadores.db')
cursor = conn.cursor()
cursor.execute(
    'INSERT INTO jugadores (nombre, edad, posicion, goles, asistencias, imagen) VALUES (?, ?, ?, ?, ?, ?)',
    ('Juan', 20, 'Delantero', 5, 2, '')
)
conn.commit()
conn.close()
print('Guardar OK')