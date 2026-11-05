"""Microservicio de Ingesta de Datos (FastAPI).
Permite recepcion de ventas diarias por API REST (JSON) o carga de archivos CSV.
Guarda los datos en la zona raw/ del Data Lake y despacha eventos a la cola de mensajes
para desacoplamiento asincrono y procesamiento resiliente.
"""
import os
import sys
import uuid
import datetime
import pandas as pd
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Asegurar importacion relativa de modulos hermanos
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICES_DIR = os.path.dirname(CURRENT_DIR)
ROOT_DIR = os.path.dirname(SERVICES_DIR)
sys.path.insert(0, ROOT_DIR)

from services.ingesta.database import (
    get_db, init_db, IngestaLogModel, OperacionDiariaModel, ActivoModel
)
from services.worker.cola import get_queue
from services.worker.worker import procesar_un_ciclo_worker

app = FastAPI(
    title="RentMetrics Ingestion API",
    description="""
    **Microservicio de Ingesta y Desacoplamiento en la Nube (Unidad 2 - Entregable E2)**
    
    Proporciona endpoints robustos con validacion Pydantic y documentacion OpenAPI para:
    * Ingesta de operaciones diarias individuales o por lote (JSON).
    * Subida masiva de bitacoras y estados de cuenta en archivos CSV.
    * Almacenamiento no bloqueante en la zona `raw/` del Data Lake.
    * Publicacion automatica de eventos a la cola de mensajes (Amazon SQS / Cola con DLQ).
    * Monitoreo de salud del servicio, base de datos y metricas de cola.
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar tablas al arrancar
@app.on_event("startup")
def startup_event():
    init_db()


# ==============================================================================
# ESQUEMAS PYDANTIC (VALIDACION DE ENTRADA ESTRICTA)
# ==============================================================================

class VentaItem(BaseModel):
    fecha: datetime.date = Field(..., description="Fecha de la operacion (AAAA-MM-DD)", example="2026-10-26")
    producto: str = Field(..., min_length=2, max_length=50, description="Nombre del activo o concepto", example="Carlos Chávez")
    unidades: int = Field(..., gt=0, description="Cantidad de operaciones o servicios", example=15)
    precio_unitario: float = Field(..., gt=0, description="Tarifa o canon unitario en MXN", example=515.0)
    categoria: Optional[str] = Field("Casas", description="Categoria patrimonial del activo", example="Casas")
    ubicacion: Optional[str] = Field("Colima", description="Municipio del inmueble", example="Colima")
    total: Optional[float] = Field(None, description="Importe total (si se omite, se calcula automaticamente)")


class VentasBatchRequest(BaseModel):
    origen: Optional[str] = Field("API_REST", description="Identificador del canal de origen")
    operaciones: List[VentaItem] = Field(..., min_items=1, description="Lista de transacciones diarias")


class IngestaResponse(BaseModel):
    status: str = Field(..., example="QUEUED")
    batch_id: str = Field(..., example="batch-8b3d6c7e")
    total_recibidos: int = Field(..., example=25)
    archivo_raw: str = Field(..., example="raw/inbox_batch_8b3d6c7e.csv")
    message_id_cola: str = Field(..., example="msg-5f9a2b")
    mensaje: str = Field(..., example="Datos almacenados en raw/ y despachados a la cola exitosamente.")
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
    cola_stats: dict
    timestamp: datetime.datetime


# ==============================================================================
# ENDPOINTS DE CONTROL Y MONITOREO
# ==============================================================================

@app.get("/", tags=["General"])
def read_root():
    return {
        "sistema": "RentMetrics Ingestion API",
        "version": "2.0.0",
        "entregable": "E2 - Cimientos en la Nube",
        "documentacion": "/docs",
        "salud": "/health",
    }


@app.get("/health", response_model=HealthResponse, tags=["Monitoreo"])
def health_check(db: Session = Depends(get_db)):
    db_status = "ONLINE"
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "DEGRADED"

    queue = get_queue()
    cola_stats = queue.get_stats()

    return HealthResponse(
        status="OK" if db_status == "ONLINE" else "WARNING",
        service="RentMetrics-Ingesta",
        version="2.0.0",
        database=db_status,
        cola_stats=cola_stats,
        timestamp=datetime.datetime.utcnow(),
    )


@app.get("/api/v1/cola/stats", tags=["Monitoreo"])
def get_queue_metrics():
    """Consulta el estado del middleware de mensajeria y Dead Letter Queue (DLQ)."""
    queue = get_queue()
    return queue.get_stats()


# ==============================================================================
# ENDPOINTS DE INGESTA DE DATOS
# ==============================================================================

@app.post(
    "/api/v1/ventas",
    response_model=IngestaResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Ingesta"],
    summary="Registrar lote de operaciones diarias (JSON)"
)
def recibir_ventas_json(request: VentasBatchRequest, db: Session = Depends(get_db)):
    """
    Recibe un lote de operaciones en formato JSON con validacion Pydantic estricta.
    1. Genera un identificador unico de lote (batch_id).
    2. Vuelca el contenido a un nuevo archivo en la zona `raw/`.
    3. Registra el evento en la tabla `ingesta_logs`.
    4. Publica un mensaje en la cola para procesamiento desacoplado en segundo plano.
    """
    batch_id = f"batch_{uuid.uuid4().hex[:10]}"
    raw_filename = f"inbox_{batch_id}.csv"
    raw_path = os.path.join(ROOT_DIR, "raw", raw_filename)

    filas = []
    for item in request.operaciones:
        calc_total = item.total if item.total is not None else float(item.unidades * item.precio_unitario)
        filas.append({
            "fecha": str(item.fecha),
            "producto": item.producto,
            "categoria": item.categoria,
            "ubicacion": item.ubicacion,
            "unidades": item.unidades,
            "precio_unitario": item.precio_unitario,
            "total": calc_total,
        })

    df = pd.DataFrame(filas)
    os.makedirs(os.path.dirname(raw_path), exist_ok=True)
    df.to_csv(raw_path, index=False)

    # Registro en log de base de datos
    log_entry = IngestaLogModel(
        batch_id=batch_id,
        origen=request.origen or "API_REST",
        archivo_raw=f"raw/{raw_filename}",
        total_registros=len(df),
        estado="QUEUED",
        reintentos=0,
    )
    db.add(log_entry)
    db.commit()

    # Publicar a la cola de mensajes
    queue = get_queue()
    payload = {
        "event": "NEW_RAW_FILE",
        "batch_id": batch_id,
        "raw_file": f"raw/{raw_filename}",
        "total_registros": len(df),
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }
    msg_id = queue.send_message(payload)

    return IngestaResponse(
        status="QUEUED",
        batch_id=batch_id,
        total_recibidos=len(df),
        archivo_raw=f"raw/{raw_filename}",
        message_id_cola=msg_id,
        mensaje="Lote almacenado en raw/ y encolado para procesamiento asincrono.",
    )


@app.post(
    "/api/v1/upload-csv",
    response_model=IngestaResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Ingesta"],
    summary="Subir archivo CSV de bitacora a la zona raw/"
)
async def upload_csv_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Recibe un archivo CSV subido por el usuario o administrador inmobiliario.
    Valida el formato, lo guarda en `raw/` y notifica a la cola para limpieza automatica.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se aceptan archivos con extension .csv"
        )

    batch_id = f"upload_{uuid.uuid4().hex[:10]}"
    raw_filename = f"inbox_{batch_id}_{file.filename}"
    raw_path = os.path.join(ROOT_DIR, "raw", raw_filename)

    try:
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El archivo CSV esta vacio.")

        os.makedirs(os.path.dirname(raw_path), exist_ok=True)
        with open(raw_path, "wb") as f:
            f.write(contents)

        # Validacion preliminar de cabeceras
        df_preview = pd.read_csv(raw_path)
        total_filas = len(df_preview)

    except Exception as e:
        if os.path.exists(raw_path):
            os.remove(raw_path)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error al analizar el archivo CSV: {str(e)}"
        )

    # Registrar en base de datos
    log_entry = IngestaLogModel(
        batch_id=batch_id,
        origen="CSV_UPLOAD",
        archivo_raw=f"raw/{raw_filename}",
        total_registros=total_filas,
        estado="QUEUED",
        reintentos=0,
    )
    db.add(log_entry)
    db.commit()

    # Publicar a la cola
    queue = get_queue()
    payload = {
        "event": "NEW_RAW_FILE",
        "batch_id": batch_id,
        "raw_file": f"raw/{raw_filename}",
        "total_registros": total_filas,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }
    msg_id = queue.send_message(payload)

    return IngestaResponse(
        status="QUEUED",
        batch_id=batch_id,
        total_recibidos=total_filas,
        archivo_raw=f"raw/{raw_filename}",
        message_id_cola=msg_id,
        mensaje="Archivo CSV subido a raw/ y publicado en la cola de procesamiento.",
    )


@app.post("/api/v1/trigger-worker", tags=["Ingesta"], summary="Ejecutar ciclo de limpieza del worker")
def trigger_worker_cycle():
    """
    Dispara manualmente un ciclo del worker para procesar los mensajes en cola.
    Util para la demostracion de punta a punta en vivo (< 5 minutos).
    """
    resultado = procesar_un_ciclo_worker()
    return resultado


# ==============================================================================
# ENDPOINTS DE CONSULTAS
# ==============================================================================

@app.get("/api/v1/registros", tags=["Consultas"], summary="Consultar transacciones en base de datos")
def consultar_registros(limit: int = 50, estado: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(OperacionDiariaModel)
    if estado:
        query = query.filter(OperacionDiariaModel.estado == estado.upper())
    total = query.count()
    rows = query.order_by(OperacionDiariaModel.fecha.desc()).limit(limit).all()
    return {
        "total_en_base": total,
        "mostrados": len(rows),
        "registros": [
            {
                "id": r.id,
                "fecha": str(r.fecha),
                "producto": r.producto,
                "categoria": r.categoria,
                "ubicacion": r.ubicacion,
                "unidades": r.unidades,
                "precio_unitario": float(r.precio_unitario),
                "total": float(r.total),
                "estado": r.estado,
            }
            for r in rows
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.ingesta.main:app", host="0.0.0.0", port=8000, reload=True)
