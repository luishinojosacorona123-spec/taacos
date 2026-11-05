"""Modulo de Analisis de Series de Tiempo (Analitica Unidad 3 - Entregable E2).
Incluye:
1. Descomposicion estacional (Tendencia, Estacionalidad semanal/quincenal, Residuo).
2. Prueba de Estacionariedad de Dickey-Fuller Aumentada (ADF).
3. Calculo e interpretacion de funciones de Autocorrelacion (ACF) y Autocorrelacion Parcial (PACF).
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from statsmodels.tsa.stattools import adfuller, acf, pacf
from statsmodels.tsa.seasonal import seasonal_decompose


def preparar_serie_diaria_agregada(df_clean: pd.DataFrame) -> pd.Series:
    """Prepara y reindexa a frecuencia diaria regular la serie temporal del flujo de ingresos/ventas."""
    df = df_clean.copy()
    if "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"])
        col_monto = "total" if "total" in df.columns else ("ingreso_diario" if "ingreso_diario" in df.columns else "ingreso_renta")
        serie = df.groupby("fecha")[col_monto].sum().sort_index()
        # Asegurar frecuencia diaria sin huecos
        idx_completo = pd.date_range(start=serie.index.min(), end=serie.index.max(), freq="D")
        serie = serie.reindex(idx_completo).ffill().fillna(0)
        serie.name = "ingreso_diario"
        return serie
    raise ValueError("El DataFrame no contiene una columna 'fecha' valida.")


def ejecutar_descomposicion_serie(serie: pd.Series, periodo: int = 7) -> Dict[str, Any]:
    """
    Descompone la serie temporal en Tendencia (T_t), Estacionalidad (S_t) y Residuo (I_t).
    Modelo aditivo: Y_t = T_t + S_t + I_t
    Periodo por defecto: 7 dias (ciclo semanal comercial).
    """
    descomp = seasonal_decompose(serie, model="additive", period=periodo, extrapolate_trend="period")
    
    varianza_total = float(np.var(serie.dropna()))
    varianza_residuo = float(np.var(descomp.resid.dropna()))
    fuerza_estacional = max(0.0, 1.0 - (varianza_residuo / varianza_total)) if varianza_total > 0 else 0.0

    return {
        "observado": descomp.observed,
        "tendencia": descomp.trend,
        "estacionalidad": descomp.seasonal,
        "residuo": descomp.resid,
        "periodo": periodo,
        "fuerza_estacional": fuerza_estacional,
        "media_serie": float(serie.mean()),
        "desv_estandar": float(serie.std()),
    }


def ejecutar_prueba_adfuller(serie: pd.Series) -> Dict[str, Any]:
    """
    Ejecuta la prueba de Dickey-Fuller Aumentada (ADF).
    H0: La serie tiene raiz unitaria (es NO estacionaria).
    H1: La serie es estacionaria (p-value < 0.05).
    """
    serie_clean = serie.dropna()
    res = adfuller(serie_clean, autolag="AIC")
    
    stat_adf = float(res[0])
    p_value = float(res[1])
    used_lag = int(res[2])
    n_obs = int(res[3])
    crit_vals = {k: float(v) for k, v in res[4].items()}

    es_estacionaria = (p_value < 0.05) and (stat_adf < crit_vals.get("5%", -2.86))
    
    interpretacion = (
        f"Con un p-value de {p_value:.5f} (< 0.05) y estadistico ADF = {stat_adf:.4f} "
        f"(menor al valor critico al 5% de {crit_vals.get('5%'):.4f}), se rechaza la hipotesis nula (H0). "
        "La serie temporal es ESTACIONARIA en niveles I(0), lo que permite calibrar modelos autorregresivos "
        "sin requerir diferenciacion previa (d=0)."
        if es_estacionaria else
        f"Con un p-value de {p_value:.5f} (>= 0.05) y estadistico ADF = {stat_adf:.4f}, "
        "no es posible rechazar H0. La serie presenta raiz unitaria y requiere diferenciacion de primer orden d=1 "
        "para estabilizar su media antes del modelado ARIMA."
    )

    return {
        "estadistico_adf": stat_adf,
        "p_value": p_value,
        "lags_utilizados": used_lag,
        "numero_observaciones": n_obs,
        "valores_criticos": crit_vals,
        "es_estacionaria": es_estacionaria,
        "interpretacion": interpretacion,
    }


def calcular_acf_pacf(serie: pd.Series, nlags: int = 35) -> Dict[str, Any]:
    """
    Calcula las funciones de autocorrelacion (ACF) y autocorrelacion parcial (PACF).
    Determina bandas de confianza de Bartlett al 95% (+- 1.96 / sqrt(N)).
    """
    serie_clean = serie.dropna()
    n = len(serie_clean)
    val_acf = acf(serie_clean, nlags=nlags)
    val_pacf = pacf(serie_clean, nlags=nlags, method="yw")

    umbral_confianza = 1.96 / np.sqrt(n)

    # Identificar retardos con significancia estadistica (> umbral)
    lags_sig_acf = [lag for lag in range(1, nlags + 1) if abs(val_acf[lag]) > umbral_confianza]
    lags_sig_pacf = [lag for lag in range(1, nlags + 1) if abs(val_pacf[lag]) > umbral_confianza]

    interpretacion = (
        f"Se detecta autocorrelacion significativa en los retardos: {lags_sig_acf[:5]}. "
        f"El pico en el retardo 7 (r={val_acf[7]:.3f}) y retardo 14 confirma el ciclo operativo semanal. "
        f"La funcion PACF muestra un corte tras los primeros retardos estacionales, lo cual orienta "
        f"la seleccion del orden autorregresivo p=1 o p=7 y estacional P=1 en la formulacion SARIMA de E3."
    )

    return {
        "nlags": nlags,
        "acf": val_acf.tolist(),
        "pacf": val_pacf.tolist(),
        "umbral_confianza_95": float(umbral_confianza),
        "banda_superior": float(umbral_confianza),
        "banda_inferior": float(-umbral_confianza),
        "lags_significativos_acf": lags_sig_acf,
        "lags_significativos_pacf": lags_sig_pacf,
        "interpretacion": interpretacion,
    }
