import customtkinter as ctk
from tkinter import ttk
from PIL import Image, ImageTk
import sqlite3
import os
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Ventana mini
root = ctk.CTk()
root.title("Prueba Resto")
root.geometry("900x600")

# Gráfico
fig, ax = plt.subplots(figsize=(5, 3))
canvas = FigureCanvasTkAgg(fig, root)
canvas.get_tk_widget().pack(pady=10)

# Imagen
img_label = ctk.CTkLabel(root, text="Sin imagen")
img_label.pack(pady=10)

# Tabla
tree = ttk.Treeview(root, columns=('ID', 'Nombre'), show='headings')
tree.heading('ID', text='ID')
tree.heading('Nombre', text='Nombre')
tree.pack(fill="both", expand=True, padx=20, pady=10)

# Insertar fila de prueba
tree.insert("", "end", values=(1, "Juan"))

# Función de clic
def mostrar_imagen(event):
    print("Clic detectado")

# Vincular clic
tree.bind("<ButtonRelease-1>", mostrar_imagen)

root.mainloop()