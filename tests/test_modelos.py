"""Pruebas unitarias para los modelos analiticos de E2:
1. Descomposicion de series de tiempo (aditiva Y_t = T_t + S_t + I_t), ADF, ACF y PACF.
2. Regresion lineal por Minimos Cuadrados Ordinarios (OLS) con NumPy frente a scikit-learn (< 1e-6 de diferencia).
3. Metricas y diagnostico de residuales.
"""
import numpy as np
import pandas as pd
import pytest
from services.modelos.series_tiempo import (
    preparar_serie_diaria_agregada,
    ejecutar_descomposicion_serie,
    ejecutar_prueba_adfuller,
    calcular_acf_pacf,
)
from services.modelos.regresion import (
    RegresionMinimosCuadradosNumPy,
    comparar_numpy_vs_sklearn,
)


def test_serie_tiempo_descomposicion_y_estacionariedad():
    # Crear serie sintetica con tendencia lineal y ciclo semanal (periodo 7)
    np.random.seed(42)
    fechas = pd.date_range("2026-01-01", periods=180, freq="D")
    t = np.arange(len(fechas))
    tendencia = 50000 + 150 * t
    estacionalidad = 8000 * np.sin(2 * np.pi * t / 7)
    ruido = np.random.normal(0, 1000, size=len(fechas))
    valores = tendencia + estacionalidad + ruido

    df_test = pd.DataFrame({"fecha": fechas, "ingreso_diario": valores})
    serie = preparar_serie_diaria_agregada(df_test)
    assert len(serie) == 180

    # 1. Descomposicion aditiva
    descomp = ejecutar_descomposicion_serie(serie, periodo=7)
    assert "observado" in descomp
    assert "tendencia" in descomp
    assert "estacionalidad" in descomp
    assert "residuo" in descomp
    
    # Reconstruccion aditiva Y_t = T_t + S_t + I_t
    obs = descomp["observado"]
    reconstruido = descomp["tendencia"] + descomp["estacionalidad"] + descomp["residuo"]
    diff = np.abs(obs - reconstruido).dropna()
    assert np.all(diff < 1e-5), "La reconstruccion aditiva Y_t = T_t + S_t + I_t debe coincidir exactamente."

    # 2. Prueba ADF
    res_adf = ejecutar_prueba_adfuller(serie)
    assert "estadistico_adf" in res_adf
    assert "p_value" in res_adf
    assert "valores_criticos" in res_adf
    assert isinstance(res_adf["es_estacionaria"], bool)

    # 3. ACF y PACF
    res_corr = calcular_acf_pacf(serie, nlags=20)
    assert len(res_corr["acf"]) == 21
    assert len(res_corr["pacf"]) == 21
    assert res_corr["banda_superior"] > 0
    assert res_corr["banda_inferior"] < 0


def test_regresion_numpy_vs_sklearn_exactitud():
    # Generar datos multivariados sinteticos
    np.random.seed(123)
    n = 250
    x1 = np.random.uniform(500000, 3000000, size=n)
    x2 = np.random.uniform(1000, 25000, size=n)
    X = np.column_stack([x1, x2])
    # y = beta_0 + 0.008*x1 - 1.2*x2 + epsilon
    y = 5000 + 0.008 * x1 - 1.2 * x2 + np.random.normal(0, 500, size=n)

    # Comparar NumPy vs scikit-learn
    comp = comparar_numpy_vs_sklearn(X, y, "Valores", "Rentas")
    
    assert comp["cumple_tolerancia"] is True, "La diferencia entre NumPy y scikit-learn debe ser < 1e-6."
    assert comp["diferencia_intercepto"] < 1e-6
    assert all(d < 1e-6 for d in comp["diferencias_coeficientes"])

    # Metricas
    met_np = comp["metricas_numpy"]
    met_sk = comp["metricas_sklearn"]
    assert np.isclose(met_np["R2"], met_sk["R2"], atol=1e-6)
    assert np.isclose(met_np["MSE"], met_sk["MSE"], atol=1e-4)
    assert np.isclose(met_np["MAE"], met_sk["MAE"], atol=1e-4)


def test_diagnostico_residuales_ols():
    np.random.seed(99)
    n = 150
    X = np.random.uniform(10, 100, size=(n, 1))
    y = 25 + 3.5 * X.flatten() + np.random.normal(0, 2, size=n)

    modelo = RegresionMinimosCuadradosNumPy().fit(X, y)
    residuos = modelo.residuos

    # Propiedad de MCO: la media de los residuos con intercepto es cero
    assert np.isclose(np.mean(residuos), 0.0, atol=1e-6), "La suma y media de los residuales de MCO debe ser 0."
    assert len(residuos) == n
    assert modelo.metricas["R2"] > 0.90
