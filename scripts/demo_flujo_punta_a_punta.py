"""Script de Demostracion del Flujo de Punta a Punta (Entregable E2 - Criterio 6).
Demuestra el ciclo de vida completo del dato en < 5 minutos:
1. Ingesta de nuevo lote de transacciones via API REST FastAPI (POST /api/v1/ventas).
2. Encolamiento asincrono en la cola desacoplada (LocalDiskQueue / AWS SQS).
3. Consumo, limpieza automatizada de 5 anomalias y persistencia por el Worker.
4. Registro transaccional en Base de Datos Relacional (PostgreSQL / SQLite).
5. Verificacion de logs de ingesta y disponibilidad para el Tablero v2.
"""
import os
import sys
import time
import datetime
from fastapi.testclient import TestClient

# Asegurar path raiz del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from services.ingesta.main import app
from services.worker.worker import procesar_un_ciclo_worker
from services.worker.cola import get_queue
from services.ingesta.database import SessionLocal, OperacionDiariaModel, IngestaLogModel


def ejecutar_demostracion_e2e():
    print("=" * 80)
    print("DEMOSTRACION DE FLUJO DE PUNTA A PUNTA - ENTREGABLE E2 (DATA STARTUP)")
    print("Rubrica Computo en la Nube: Ingesta -> Cola -> Worker -> BD en < 5 minutos")
    print("=" * 80)
    t_inicio = time.time()

    # 1. Comprobar salud de la API
    client = TestClient(app)
    print("\n[Paso 1] Verificacion del Microservicio de Ingesta (FastAPI)")
    res_health = client.get("/health")
    assert res_health.status_code == 200, f"Error en GET /health: {res_health.text}"
    health_data = res_health.json()
    print(f"  Estado del Servicio: {health_data['status']}")
    print(f"  Servicio: {health_data['service']} v{health_data['version']}")
    print(f"  Base de Datos: {health_data['database']}")
    print(f"  Cola: {health_data['cola_stats']}")

    # 2. Generar lote de ventas con datos validos y anomalias para el worker
    # Nota: la API valida el esquema JSON inicial, y el worker limpia formatos, faltantes y logica
    fecha_hoy = datetime.date.today().isoformat()
    lote_items = [
        {
            "fecha": fecha_hoy,
            "producto": "carlos chávez",  # Formato en minuscula a corregir por el worker
            "unidades": 10,
            "precio_unitario": 515.0,
            "categoria": "Casas",
            "ubicacion": "Colima",
            "total": 5150.0
        },
        {
            "fecha": fecha_hoy,
            "producto": "Palma kerpis",
            "unidades": 12,
            "precio_unitario": 490.0,
            "categoria": "Casas",
            "ubicacion": "Villa de Álvarez",
            "total": 5880.0
        },
        {
            "fecha": fecha_hoy,
            "producto": "Versa 1",
            "unidades": 8,
            "precio_unitario": 350.0,
            "categoria": "Vehículos",
            "ubicacion": "Colima",
            "total": 2800.0
        }
    ]

    payload_ingesta = {
        "origen": "Demo Terminal E2E",
        "operaciones": lote_items
    }

    # 3. Enviar lote a la API de Ingesta
    print("\n[Paso 2] Envio de transacciones a FastAPI (POST /api/v1/ventas)")
    res_post = client.post("/api/v1/ventas", json=payload_ingesta)
    assert res_post.status_code in (200, 202), f"Fallo al registrar ventas: {res_post.text}"
    ingesta_info = res_post.json()
    batch_id = ingesta_info["batch_id"]
    msg_id = ingesta_info["message_id_cola"]
    print(f"  Lote generado: {batch_id}")
    print(f"  Mensaje ID en Cola: {msg_id}")
    print(f"  Archivo temporal RAW: {ingesta_info['archivo_raw']}")
    print(f"  Total registros recibidos: {ingesta_info['total_recibidos']}")

    # 4. Inspeccionar estado de la Cola
    queue = get_queue()
    stats_cola = queue.get_stats()
    print("\n[Paso 3] Inspeccion de la Cola Desacoplada:")
    print(f"  Backend de Cola: {queue.__class__.__name__}")
    print(f"  Mensajes pendientes: {stats_cola['mensajes_en_cola']}")
    print(f"  Mensajes en DLQ: {stats_cola['mensajes_en_dlq']}")
    assert stats_cola["mensajes_en_cola"] >= 1, "Debe haber al menos 1 mensaje en cola tras la ingesta."

    # 5. Ejecutar Worker para procesar el lote
    print("\n[Paso 4] Despacho y Ejecucion del Worker de Limpieza:")
    worker_res = procesar_un_ciclo_worker(max_messages=5)
    print(f"  Estado del Worker: {worker_res['status']}")
    print(f"  Mensajes procesados: {worker_res['mensajes_procesados']}")
    print(f"  Mensajes con error: {worker_res['mensajes_con_error']}")
    assert worker_res["mensajes_procesados"] >= 1, "El worker debio procesar al menos 1 mensaje."

    # 6. Consultar la Base de Datos Relacional para verificar persistencia
    print("\n[Paso 5] Verificacion en Base de Datos Relacional (SQL):")
    db = SessionLocal()
    try:
        log_db = db.query(IngestaLogModel).filter(IngestaLogModel.batch_id == batch_id).first()
        assert log_db is not None, "El registro de log no existe en la base de datos."
        print(f"  Log de Ingesta: Lote={log_db.batch_id} | Estado={log_db.estado} | Limpios={log_db.registros_limpios} | Reintentos={log_db.reintentos}")
        assert log_db.estado == "PROCESSED", f"Estado esperado 'PROCESSED', se obtuvo '{log_db.estado}'"

        ops_db = db.query(OperacionDiariaModel).filter(OperacionDiariaModel.ingesta_id == batch_id).all()
        print(f"  Registros guardados en tabla 'operaciones_diarias': {len(ops_db)}")
        for op in ops_db:
            print(f"    - ID={op.id} | Fecha={op.fecha} | Activo='{op.producto}' | Unidades={op.unidades} | Total=${op.total:,.2f} | Estado={op.estado}")
        assert len(ops_db) == len(lote_items), f"Se esperaban {len(lote_items)} registros insertados en BD."
    finally:
        db.close()

    # 7. Resumen de tiempo y cumplimiento de la rubrica
    t_total = time.time() - t_inicio
    print("\n" + "=" * 80)
    print("RESULTADO DE LA DEMOSTRACION: EXITOSA (100% FUNCIONAL)")
    print(f"Tiempo Total de Ejecucion Punta a Punta: {t_total:.2f} segundos")
    print(f"Criterio de Evaluacion Oficial: < 300 segundos (5 minutos)")
    print(f"Margen de Rendimiento: {((300 - t_total) / 300) * 100:.1f}% mas rapido que el limite maximo")
    print("=" * 80)


if __name__ == "__main__":
    ejecutar_demostracion_e2e()
