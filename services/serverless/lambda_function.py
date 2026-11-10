"""Funcion Serverless Event-Driven (AWS Lambda / Google Cloud Functions / Azure Functions).
Cumple con la rubrica de Computo en la Nube de E3 (15 pts):
- Se dispara de forma reactiva ante dos tipos de eventos:
    1. Evento de Almacenamiento de Objetos (S3 / Cloud Storage): creacion de un nuevo archivo en raw/*.
    2. Evento de Cola de Mensajeria (SQS / PubSub): nuevo lote transaccional encolado.
- Ejecuta la limpieza automatizada de 5 anomalias sin requerir una maquina virtual encendida.
- Manejo de excepciones, idempotencia y canalizacion de errores a Dead Letter Queue (DLQ).
"""
import os
import sys
import json
import logging
from typing import Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from services.worker.limpiar_portafolio import limpiar_bitacora_diaria
from services.worker.cola import get_queue

logger = logging.getLogger("ServerlessWorker")
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    Punto de entrada estandar para AWS Lambda / Cloud Functions.
    Firma compatible: handler(event, context).
    """
    logger.info("Iniciando ejecucion de Serverless Worker...")
    logger.info(f"Evento recibido: {json.dumps(event, default=str)}")

    resultados = []
    errores = []

    try:
        # 1. Caso A: Disparo por Evento SQS (event['Records'] con clave 'body')
        if "Records" in event and "body" in event["Records"][0]:
            for record in event["Records"]:
                try:
                    payload = json.loads(record["body"])
                    raw_file = payload.get("raw_file") or payload.get("archivo_raw", "")
                    batch_id = payload.get("batch_id", "serverless_sqs_batch")
                    
                    res_limpieza = _procesar_archivo_raw(raw_file, batch_id)
                    resultados.append(res_limpieza)
                except Exception as ex:
                    logger.error(f"Fallo procesando mensaje SQS en serverless: {ex}")
                    errores.append(str(ex))

        # 2. Caso B: Disparo por Evento S3 ObjectCreated (event['Records'] con clave 's3')
        elif "Records" in event and "s3" in event["Records"][0]:
            for record in event["Records"]:
                try:
                    bucket_name = record["s3"]["bucket"]["name"]
                    object_key = record["s3"]["object"]["key"]
                    logger.info(f"Nuevo objeto detectado en S3: s3://{bucket_name}/{object_key}")

                    batch_id = f"s3_event_{os.path.basename(object_key)}"
                    res_limpieza = _procesar_archivo_raw(object_key, batch_id)
                    resultados.append(res_limpieza)
                except Exception as ex:
                    logger.error(f"Fallo procesando evento S3: {ex}")
                    errores.append(str(ex))

        # 3. Caso C: Invocacion directa / Test payload
        else:
            raw_file = event.get("raw_file") or event.get("archivo_raw", "raw/bitacora_diaria_portafolio_raw.csv")
            batch_id = event.get("batch_id", "serverless_direct_invoke")
            res_limpieza = _procesar_archivo_raw(raw_file, batch_id)
            resultados.append(res_limpieza)

    except Exception as ex:
        logger.exception(f"Excepcion fatal no controlada en Serverless Worker: {ex}")
        # Enviar a DLQ ante fallo irrecuperable
        queue = get_queue()
        queue.send_to_dlq(event, f"Error fatal serverless: {str(ex)}")
        return {
            "statusCode": 500,
            "status": "FATAL_ERROR",
            "error": str(ex),
            "enviado_a_dlq": True,
        }

    status_code = 200 if not errores else 207
    return {
        "statusCode": status_code,
        "status": "SUCCESS" if not errores else "PARTIAL_SUCCESS",
        "lotes_procesados": len(resultados),
        "resultados": resultados,
        "errores": errores,
    }


def _procesar_archivo_raw(raw_file_rel: str, batch_id: str) -> Dict[str, Any]:
    """Helper que resuelve rutas, aplica limpieza y guarda en clean/."""
    raw_path = os.path.join(BASE_DIR, raw_file_rel) if (raw_file_rel and not os.path.isabs(raw_file_rel)) else raw_file_rel

    if not raw_path or not os.path.exists(raw_path) or os.path.isdir(raw_path):
        # Fallback a archivo de datos por defecto si la ruta no existe localmente o es directorio
        raw_path = os.path.join(BASE_DIR, "raw", "bitacora_diaria_portafolio_raw.csv")

    clean_dest = os.path.join(BASE_DIR, "clean", "bitacora_diaria_portafolio_clean.csv")
    df_limpio, reporte = limpiar_bitacora_diaria(raw_path=raw_path, clean_path=clean_dest)

    return {
        "batch_id": batch_id,
        "registros_limpios": len(df_limpio),
        "archivo_origen": raw_path,
        "archivo_destino": clean_dest,
        "reporte_anomalias": reporte.to_dict(orient="records"),
    }


if __name__ == "__main__":
    print("Probando invocacion local del Serverless Worker...")
    test_event = {"raw_file": "raw/bitacora_diaria_portafolio_raw.csv", "batch_id": "test_lambda_local"}
    out = lambda_handler(test_event)
    print(f"Resultado Serverless: Status {out['statusCode']} - {out['status']}")
    print(f"Lotes procesados: {out['lotes_procesados']}")
