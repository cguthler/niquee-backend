import traceback
import sys

# Capturar cualquier error
try:
    exec(open('app.py').read())
except Exception as e:
    print("Error detectado:")
    traceback.print_exc()
    input("Presiona Enter para salir...")