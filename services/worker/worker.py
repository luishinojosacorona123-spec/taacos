"""Worker de Limpieza y Persistencia Asincrona (E2).
Consume mensajes de la cola (SQS / Local), ejecuta la limpieza automatizada con conteo de errores,
escribe en la zona clean/ del Data Lake y sincroniza la base de datos relacional (PostgreSQL / SQLite).
Implementa politica de reintentos y envio a Dead Letter Queue (DLQ) ante excepciones irrecuperables.
"""
import os
import sys
import time
import json
import logging
from typing import Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from services.worker.cola import get_queue
from services.worker.limpiar_portafolio import limpiar_bitacora_diaria
from services.ingesta.database import SessionLocal, IngestaLogModel, OperacionDiariaModel, init_db
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RentMetricsWorker")


def procesar_un_ciclo_worker(max_messages: int = 10) -> Dict[str, Any]:
    """
    Ejecuta un ciclo de sondeo de la cola.
    Procesa hasta max_messages, ejecuta la limpieza, persiste en clean/ y base de datos,
    y canaliza a la Dead Letter Queue (DLQ) si se producen fallos irrecuperables.
    """
    init_db()
    queue = get_queue()
    mensajes = queue.receive_messages(max_messages=max_messages, visibility_timeout=30)

    if not mensajes:
        return {
            "status": "IDLE",
            "mensajes_procesados": 0,
            "cola_stats": queue.get_stats()
        }

    procesados = 0
    errores = 0
    db = SessionLocal()

    try:
        for msg in mensajes:
            msg_id = msg.get("MessageId")
            receipt_handle = msg.get("ReceiptHandle")
            attempts = msg.get("Attempts", 1)
            payload = msg.get("Payload", {})
            batch_id = payload.get("batch_id", "unknown")
            raw_file_rel = payload.get("raw_file", "")

            logger.info(f"Procesando mensaje {msg_id} (Intento {attempts}/3) - Lote: {batch_id}")
            raw_full_path = os.path.join(BASE_DIR, raw_file_rel) if not os.path.isabs(raw_file_rel) else raw_file_rel

            if not os.path.exists(raw_full_path):
                # Si el archivo raw no existe, fallo irrecuperable -> DLQ
                err_msg = f"El archivo origen '{raw_full_path}' no existe en disco."
                logger.error(err_msg)
                queue.send_to_dlq(payload, err_msg, receipt_handle)
                _actualizar_log_ingesta(db, batch_id, estado="DLQ", error=err_msg, reintentos=attempts)
                errores += 1
                continue

            try:
                # 1. Ejecutar limpieza con modulo reproducible
                master_clean = os.path.join(BASE_DIR, "clean", "bitacora_diaria_portafolio_clean.csv")
                is_inbox = "inbox_" in os.path.basename(raw_full_path)
                
                if is_inbox:
                    clean_dest = os.path.join(BASE_DIR, "clean", f"{os.path.splitext(os.path.basename(raw_full_path))[0]}_clean.csv")
                    df_limpio, reporte = limpiar_bitacora_diaria(raw_path=raw_full_path, clean_path=clean_dest)
                    # Integrar / anexar al consolidado maestro sin duplicar
                    if os.path.exists(master_clean):
                        df_master = pd.read_csv(master_clean)
                        df_unido = pd.concat([df_master, df_limpio], ignore_index=True)
                        df_unido = df_unido.drop_duplicates(subset=["fecha", "producto"], keep="last")
                        df_unido.to_csv(master_clean, index=False)
                else:
                    clean_dest = master_clean
                    df_limpio, reporte = limpiar_bitacora_diaria(raw_path=raw_full_path, clean_path=clean_dest)

                # 2. Persistir en la base de datos relacional (operaciones_diarias)
                nuevos_modelos = []
                # Tomar los registros relevantes para insertar/actualizar
                sample_df = df_limpio.tail(100) if len(df_limpio) > 100 else df_limpio
                for _, row in sample_df.iterrows():
                    m = OperacionDiariaModel(
                        fecha=pd.to_datetime(row["fecha"]).date(),
                        producto=str(row["producto"]),
                        categoria=str(row["categoria"]),
                        ubicacion=str(row["ubicacion"]),
                        unidades=int(row["unidades"]),
                        precio_unitario=float(row["precio_unitario"]),
                        total=float(row["total"]),
                        estado="CLEAN",
                        ingesta_id=batch_id,
                    )
                    nuevos_modelos.append(m)

                db.bulk_save_objects(nuevos_modelos)
                db.commit()

                # 3. Marcar log de ingesta como procesado
                _actualizar_log_ingesta(
                    db,
                    batch_id,
                    estado="PROCESSED",
                    registros_limpios=len(df_limpio),
                    reintentos=attempts
                )

                # 4. Eliminar mensaje de la cola
                queue.delete_message(receipt_handle)
                procesados += 1
                logger.info(f"Lote {batch_id} procesado con exito: {len(df_limpio):,} registros limpios.")

            except Exception as ex:
                err_str = str(ex)
                logger.exception(f"Error procesando lote {batch_id}: {err_str}")
                if attempts >= 3:
                    queue.send_to_dlq(payload, f"Error critico tras 3 intentos: {err_str}", receipt_handle)
                    _actualizar_log_ingesta(db, batch_id, estado="DLQ", error=err_str, reintentos=attempts)
                else:
                    _actualizar_log_ingesta(db, batch_id, estado="FAILED", error=err_str, reintentos=attempts)
                errores += 1

    finally:
        db.close()

    return {
        "status": "COMPLETED",
        "mensajes_procesados": procesados,
        "mensajes_con_error": errores,
        "cola_stats": queue.get_stats()
    }


def _actualizar_log_ingesta(db, batch_id: str, estado: str, registros_limpios: int = 0, error: str = None, reintentos: int = 0):
    try:
        log = db.query(IngestaLogModel).filter(IngestaLogModel.batch_id == batch_id).first()
        if log:
            log.estado = estado
            if registros_limpios > 0:
                log.registros_limpios = registros_limpios
            if error:
                log.error_detalle = error
            log.reintentos = reintentos
            db.commit()
    except Exception as e:
        logger.warning(f"No se pudo actualizar IngestaLog para {batch_id}: {e}")


def run_worker_daemon(poll_interval_sec: int = 5):
    """Bucle continuo para ejecutar el worker como servicio de fondo en VM / contenedor."""
    logger.info("Iniciando Worker Daemon de RentMetrics (sondeo cada %d seg)...", poll_interval_sec)
    while True:
        try:
            res = procesar_un_ciclo_worker()
            if res.get("mensajes_procesados", 0) > 0:
                logger.info("Ciclo finalizado: %s", res)
        except Exception as e:
            logger.error("Error en ciclo de worker: %s", e)
        time.sleep(poll_interval_sec)


if __name__ == "__main__":
    if "--daemon" in sys.argv:
        run_worker_daemon()
    else:
        resultado = procesar_un_ciclo_worker()
        print(json.dumps(resultado, indent=2))
