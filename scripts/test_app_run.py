import os
import sys
from streamlit.testing.v1 import AppTest

print("Iniciando prueba de renderizado con Streamlit AppTest...")
app_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "taacos.py")
at = AppTest.from_file(app_path)
at.run(timeout=45)

if at.exception:
    print("Excepcion detectada en AppTest:")
    for exc in at.exception:
        print(f"  - Mensaje: {exc.message}")
        print(f"  - Traza: {exc.stack_trace}")
    sys.exit(1)
else:
    print("Streamlit AppTest superado EXITOSAMENTE sin excepciones ni errores de renderizado!")
