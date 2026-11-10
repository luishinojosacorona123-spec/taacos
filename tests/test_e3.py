"""Pruebas unitarias integrales para el Entregable 3 (E3):
1. Modelo SARIMA serializado (pronosticos a 7, 14, 30 dias con intervalos 80% y 95%).
2. Clasificador de riesgo de inquilinos (metricas de Recall, comparativa y prediccion).
3. API de modelos (FastAPI endpoints: /health, /api/v1/pronostico, /api/v1/clasificar, /api/v1/modelos/comparativa).
4. Funcion serverless (AWS Lambda handler para eventos S3 y SQS con manejo de errores y DLQ).
"""
import os
import sys
import json
import pickle
import numpy as np
import pandas as pd
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from services.serverless.lambda_function import lambda_handler
from services.modelos_api.main import (
    health_check,
    obtener_pronostico,
    clasificar_riesgo,
    obtener_comparativa_modelos,
    ClasificacionRequest,
)


def test_e3_sarima_model_and_forecast():
    """Valida que el modelo SARIMA serializado existe, carga y genera pronosticos con intervalos."""
    model_path = os.path.join(BASE_DIR, "models", "sarima_model.pkl")
    meta_path = os.path.join(BASE_DIR, "models", "sarima_metadata.json")

    assert os.path.exists(model_path), "El archivo models/sarima_model.pkl debe existir."
    assert os.path.exists(meta_path), "El archivo models/sarima_metadata.json debe existir."

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert meta["order"] == [1, 1, 1]
    assert meta["seasonal_order"] == [1, 0, 1, 7]
    assert "aic" in meta
    assert "metricas_holdout_30_dias" in meta

    with open(model_path, "rb") as f:
        model = pickle.load(f)

    # Generar pronostico a 14 dias
    forecast_res = model.get_forecast(steps=14)
    pred_mean = forecast_res.predicted_mean
    ci_80 = forecast_res.conf_int(alpha=0.20)
    ci_95 = forecast_res.conf_int(alpha=0.05)

    assert len(pred_mean) == 14
    assert len(ci_80) == 14
    assert len(ci_95) == 14

    # Los intervalos deben contener la media y ordenarse: ci_95_low <= ci_80_low <= mean <= ci_80_high <= ci_95_high
    for idx in range(14):
        p = pred_mean.iloc[idx]
        low_80 = ci_80.iloc[idx, 0]
        high_80 = ci_80.iloc[idx, 1]
        low_95 = ci_95.iloc[idx, 0]
        high_95 = ci_95.iloc[idx, 1]

        assert low_95 <= low_80, "La banda 95% debe ser mas amplia que la de 80% inferior."
        assert high_80 <= high_95, "La banda 95% debe ser mas amplia que la de 80% superior."
        assert low_80 <= p <= high_80, "La proyeccion puntual debe estar dentro del intervalo de 80%."


def test_e3_clasificador_riesgo():
    """Valida el pipeline clasificador, comparativa de 4 algoritmos y Recall critico."""
    model_path = os.path.join(BASE_DIR, "models", "clasificador_riesgo.pkl")
    meta_path = os.path.join(BASE_DIR, "models", "clasificador_metadata.json")

    assert os.path.exists(model_path), "El archivo models/clasificador_riesgo.pkl debe existir."
    assert os.path.exists(meta_path), "El archivo models/clasificador_metadata.json debe existir."

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert "tabla_comparativa" in meta
    model_names = [m["Modelo"] for m in meta["tabla_comparativa"]]
    assert any("Naive Bayes" in m for m in model_names)
    assert any("KNN" in m or "Neighbors" in m for m in model_names)
    assert any("SVM" in m or "Support Vector" in m for m in model_names)
    assert any("Random Forest" in m for m in model_names)

    # Validar que todos los modelos tengan Recall >= 0.90 en deteccion de riesgo
    for m in meta["tabla_comparativa"]:
        assert m["Recall (Exhaustividad)"] >= 0.90, f"El Recall de {m['Modelo']} debe ser prioritario y >= 0.90"

    with open(model_path, "rb") as f:
        pipeline = pickle.load(f)

    # Inquilino de prueba con alto riesgo
    df_critico = pd.DataFrame([{
        "dias_mora": 22.0,
        "ratio_gasto_canon": 0.45,
        "variacion_flujo_pct": -0.25,
        "fraccionamiento_pagos": 3,
        "meses_contrato": 6,
        "canon_mensual": 45000.0,
    }])

    pred = pipeline.predict(df_critico)[0]
    prob = pipeline.predict_proba(df_critico)[0]

    assert pred == 1, "Un inquilino con 22 dias mora y caida de flujo debe ser clasificado con Riesgo Alto (1)."
    assert prob[1] > 0.50


def test_e3_modelos_api_endpoints():
    """Valida las respuestas y contratos de la API de modelos FastAPI."""
    # 1. Health
    h = health_check()
    assert h.status == "OK"
    assert h.sarima_disponible is True
    assert h.clasificador_disponible is True

    # 2. Pronostico a 14 dias
    res_fc = obtener_pronostico(horizonte_dias=14)
    assert res_fc.status == "SUCCESS"
    assert res_fc.horizonte_dias == 14
    assert len(res_fc.predicciones) == 14
    assert res_fc.predicciones[0].limite_inferior_80 <= res_fc.predicciones[0].pronostico_ingreso <= res_fc.predicciones[0].limite_superior_80
    assert res_fc.total_proyectado_periodo > 0

    # 3. Clasificar inquilino de alto riesgo
    req_inq = ClasificacionRequest(
        dias_mora=25.0,
        ratio_gasto_canon=0.40,
        variacion_flujo_pct=-0.30,
        fraccionamiento_pagos=3,
        meses_contrato=4,
        canon_mensual=35000.0,
        arrendatario_id="INQ-TEST-999"
    )
    res_inq = clasificar_riesgo(req_inq)
    assert res_inq.es_moroso_en_riesgo == 1
    assert res_inq.nivel_riesgo in ["ALTO", "CRITICO", "ALTO (CRITICO)"]
    assert res_inq.probabilidad_riesgo > 0.60
    assert len(res_inq.recomendacion_operativa) > 0

    # 4. Comparativa de modelos
    res_comp = obtener_comparativa_modelos()
    assert "tabla_comparativa" in res_comp
    assert "justificacion_metrica_recall" in res_comp


def test_e3_serverless_lambda_handler():
    """Valida la ejecucion de la funcion serverless ante eventos S3 y SQS."""
    # Evento tipo S3 Put
    evento_s3 = {
        "Records": [
            {
                "eventSource": "aws:s3",
                "eventName": "ObjectCreated:Put",
                "s3": {
                    "bucket": {"name": "rentmetrics-datalake-test"},
                    "object": {"key": "raw/inmuebles_rentmetrics_e3.csv", "size": 1024}
                }
            }
        ]
    }
    res_s3 = lambda_handler(evento_s3, None)
    assert res_s3["statusCode"] == 200
    assert res_s3["status"] == "SUCCESS"
    assert res_s3["lotes_procesados"] == 1

    # Evento tipo SQS
    evento_sqs = {
        "Records": [
            {
                "eventSource": "aws:sqs",
                "messageId": "msg-unit-test-1234",
                "body": json.dumps({"lote_id": "LOTE-UNIT-01", "registros": 50})
            }
        ]
    }
    res_sqs = lambda_handler(evento_sqs, None)
    assert res_sqs["statusCode"] == 200
    assert res_sqs["status"] == "SUCCESS"
    assert res_sqs["lotes_procesados"] == 1
