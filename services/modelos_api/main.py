"""Microservicio API de Modelos Predictivos en Produccion (Entregable E3).
Expone endpoints REST para inferencia en tiempo real:
- GET /health: Comprobacion de salud del servicio y disponibilidad de binarios
- GET /api/v1/pronostico: Pronostico de 7 a 30 dias con intervalos de confianza del 80% y 95% (SARIMA)
- POST /api/v1/clasificar: Evaluacion de riesgo de impago/morosidad de arrendatarios
- GET /api/v1/modelos/comparativa: Tabla comparativa de los 4 clasificadores y matrices de confusion
- GET /api/v1/modelos/info: Metadatos y parametros de los modelos productivos
Documentacion OpenAPI / Swagger interactiva disponible en /docs.
"""
import os
import sys
import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Query, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from services.modelos.arima_forecaster import generar_pronostico, entrenar_y_guardar_sarima
from services.modelos.clasificador_riesgo import clasificar_arrendatario, entrenar_y_comparar_clasificadores

app = FastAPI(
    title="RentMetrics · API de Modelos Predictivos (E3)",
    description="Servicio en la nube para inferencia en produccion: Pronostico SARIMA(1,1,1)x(1,0,1,7) y Clasificador de Riesgo de Inquilinos.",
    version="3.0.0",
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


# ==============================================================================
# ESQUEMAS PYDANTIC (VALIDACION ESTRICTA)
# ==============================================================================

class PrediccionDiaItem(BaseModel):
    dia_idx: int
    fecha: str
    dia_semana: str
    pronostico_ingreso: float
    limite_inferior_80: float
    limite_superior_80: float
    limite_inferior_95: float
    limite_superior_95: float


class PronosticoResponse(BaseModel):
    status: str
    horizonte_dias: int
    modelo: str
    total_proyectado_periodo: float
    promedio_diario_proyectado: float
    metricas_historicas: Dict[str, float]
    justificacion: str
    predicciones: List[PrediccionDiaItem]
    timestamp: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))


class ClasificacionRequest(BaseModel):
    arrendatario_id: Optional[str] = Field("INQ-104", description="Identificador unico del contrato o inquilino")
    dias_mora: float = Field(..., ge=0, le=90, description="Dias transcurridos tras la fecha limite de pago", example=12.0)
    ratio_gasto_canon: float = Field(..., ge=0, le=2.0, description="Proporcion de gastos operativos reportados sobre la renta", example=0.28)
    variacion_flujo_pct: float = Field(..., ge=-1.0, le=2.0, description="Variacion porcentual del ingreso del mes anterior", example=-0.10)
    fraccionamiento_pagos: int = Field(..., ge=1, le=10, description="Numero de abonos parciales realizados para cubrir la renta", example=2)
    meses_contrato: int = Field(..., ge=1, le=120, description="Antiguedad del contrato en meses", example=14)
    canon_mensual: float = Field(..., gt=0, description="Importe de la renta mensual fijada en MXN", example=11500.0)


class ClasificacionResponse(BaseModel):
    status: str
    arrendatario_id: Optional[str]
    modelo: str
    es_moroso_en_riesgo: int
    probabilidad_riesgo: float
    probabilidad_porcentaje: str
    nivel_riesgo: str
    color_semaforo: str
    recomendacion_operativa: str
    timestamp: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    entregable: str
    sarima_disponible: bool
    clasificador_disponible: bool
    timestamp: datetime.datetime


# ==============================================================================
# ENDPOINTS
# ==============================================================================

@app.get("/", tags=["General"])
def root():
    return {
        "sistema": "RentMetrics - Model Serving API",
        "version": "3.0.0",
        "entregable": "E3 - Inteligencia en Produccion",
        "documentacion": "/docs",
        "salud": "/health",
    }


@app.get("/health", response_model=HealthResponse, tags=["Monitoreo"])
def health_check():
    sarima_path = os.path.join(BASE_DIR, "models", "sarima_model.pkl")
    clf_path = os.path.join(BASE_DIR, "models", "clasificador_riesgo.pkl")

    return HealthResponse(
        status="OK",
        service="RentMetrics-ModelServing",
        version="3.0.0",
        entregable="E3",
        sarima_disponible=os.path.exists(sarima_path),
        clasificador_disponible=os.path.exists(clf_path),
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )


@app.get(
    "/api/v1/pronostico",
    response_model=PronosticoResponse,
    summary="Pronostico de ingresos futuros (SARIMA con bandas de confianza)",
    tags=["Modelos Predictivos"]
)
def obtener_pronostico(
    horizonte_dias: int = Query(30, ge=7, le=30, description="Numero de dias a pronosticar (7 a 30 dias)")
):
    """
    Genera el pronostico del flujo de ingresos diario a 7, 14, 21 o 30 dias con bandas de confianza del 80% y 95%.
    Utiliza el modelo optimizado SARIMA(1,1,1)x(1,0,1,7).
    """
    try:
        res = generar_pronostico(horizonte_dias=horizonte_dias)
        return PronosticoResponse(**res)
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando pronostico SARIMA: {str(ex)}"
        )


@app.post(
    "/api/v1/clasificar",
    response_model=ClasificacionResponse,
    summary="Clasificacion temprana de riesgo de impago / morosidad",
    tags=["Modelos Predictivos"]
)
def clasificar_riesgo(request: ClasificacionRequest):
    """
    Evalua el perfil de pago de un inquilino y predice la probabilidad de caer en impago.
    Retorna semaforo predictivo (BAJO, MODERADO, CRITICO) y recomendacion operativa.
    """
    try:
        res = clasificar_arrendatario(
            dias_mora=request.dias_mora,
            ratio_gasto_canon=request.ratio_gasto_canon,
            variacion_flujo_pct=request.variacion_flujo_pct,
            fraccionamiento_pagos=request.fraccionamiento_pagos,
            meses_contrato=request.meses_contrato,
            canon_mensual=request.canon_mensual,
        )
        return ClasificacionResponse(
            arrendatario_id=request.arrendatario_id,
            **res
        )
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en clasificacion de riesgo: {str(ex)}"
        )


@app.get("/api/v1/modelos/comparativa", tags=["Modelos Predictivos"])
def obtener_comparativa_modelos():
    """Consulta la tabla comparativa de los 4 clasificadores (Naive Bayes, KNN, SVM, Random Forest)."""
    meta_path = os.path.join(BASE_DIR, "models", "clasificador_metadata.json")
    if not os.path.exists(meta_path):
        entrenar_y_comparar_clasificadores()

    import json
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    return meta
