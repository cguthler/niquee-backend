import customtkinter as ctk
from tkinter import ttk

# Ventana mini
root = ctk.CTk()
root.title("Prueba Tabla y Clic")
root.geometry("400x300")

# Crear tabla
tree = ttk.Treeview(root, columns=('ID', 'Nombre'), show='headings')
tree.heading('ID', text='ID')
tree.heading('Nombre', text='Nombre')
tree.pack()

# Insertar fila de prueba
tree.insert("", "end", values=(1, "Juan"))

# Función de clic
def mostrar_imagen(event):
    print("Clic detectado")

# Vincular clic
tree.bind("<ButtonRelease-1>", mostrar_imagen)

root.mainloop()