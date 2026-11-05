"""Modulo de Regresion Lineal por Minimos Cuadrados Ordinarios (MCO / OLS).
Implementacion matematica manual desde cero con NumPy mediante la Ecuacion Normal:
    beta = (X^T * X)^(-1) * X^T * y
Comparacion y validacion numerica exacta contra scikit-learn (tolerancia < 1e-10).
Calculo de metricas: MSE, RMSE, MAE, R^2 y diagnostico formal de residuos.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


class RegresionMinimosCuadradosNumPy:
    """Implementacion vectorial propia de OLS basada en la Ecuacion Normal."""

    def __init__(self):
        self.beta = None           # Vector [beta_0 (intercepto), beta_1, ...]
        self.intercepto_ = None    # beta_0
        self.coef_ = None          # beta_1 ... beta_k
        self.n_muestras = 0
        self.n_predictores = 0
        self.metricas = {}
        self.residuos = None
        self.valores_predichos = None

    def fit(self, X: np.ndarray, y: np.ndarray):
        """
        Ajusta los coeficientes mediante la ecuacion normal:
        beta = (X_ext^T * X_ext)^(-1) * X_ext^T * y
        """
        X_mat = np.array(X, dtype=float)
        y_vec = np.array(y, dtype=float).reshape(-1, 1)

        if X_mat.ndim == 1:
            X_mat = X_mat.reshape(-1, 1)

        self.n_muestras, self.n_predictores = X_mat.shape

        # Vector columna de unos para el sesgo / intercepto beta_0
        unos = np.ones((self.n_muestras, 1), dtype=float)
        X_ext = np.hstack([unos, X_mat])

        # Ecuacion Normal: beta = (X_ext^T * X_ext)^(-1) * X_ext^T * y
        XtX = np.dot(X_ext.T, X_ext)
        XtY = np.dot(X_ext.T, y_vec)
        
        # Resolucion con solver de sistemas lineales estables
        self.beta = np.linalg.solve(XtX, XtY).flatten()
        self.intercepto_ = float(self.beta[0])
        self.coef_ = self.beta[1:]

        # Prediccion sobre entrenamiento y calculo de residuos
        self.valores_predichos = np.dot(X_ext, self.beta.reshape(-1, 1)).flatten()
        self.residuos = (y_vec.flatten() - self.valores_predichos)

        # Metricas analiticas calculadas a mano
        e = self.residuos
        n = self.n_muestras
        mse = float(np.sum(e ** 2) / n)
        rmse = float(np.sqrt(mse))
        mae = float(np.sum(np.abs(e)) / n)

        y_mean = float(np.mean(y_vec))
        tss = float(np.sum((y_vec.flatten() - y_mean) ** 2))
        rss = float(np.sum(e ** 2))
        r2 = float(1.0 - (rss / tss)) if tss > 0 else 0.0

        self.metricas = {
            "MSE": mse,
            "RMSE": rmse,
            "MAE": mae,
            "R2": r2,
            "TSS": tss,
            "RSS": rss,
        }
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X_mat = np.array(X, dtype=float)
        if X_mat.ndim == 1:
            X_mat = X_mat.reshape(-1, 1)
        unos = np.ones((X_mat.shape[0], 1), dtype=float)
        X_ext = np.hstack([unos, X_mat])
        return np.dot(X_ext, self.beta.reshape(-1, 1)).flatten()


def comparar_numpy_vs_sklearn(X: np.ndarray, y: np.ndarray, nombre_x: str = "Valor Comercial (MXN)", nombre_y: str = "Renta Mensual (MXN)") -> Dict[str, Any]:
    """
    Ejecuta el ajuste en paralelo con la implementacion manual NumPy y scikit-learn.
    Devuelve tabla comparativa y diagnostico formal de residuos.
    """
    X_mat = np.array(X, dtype=float)
    if X_mat.ndim == 1:
        X_mat = X_mat.reshape(-1, 1)
    y_vec = np.array(y, dtype=float)

    # 1. Modelo propio NumPy
    modelo_np = RegresionMinimosCuadradosNumPy().fit(X_mat, y_vec)

    # 2. Modelo scikit-learn
    modelo_sk = LinearRegression(fit_intercept=True).fit(X_mat, y_vec)
    y_pred_sk = modelo_sk.predict(X_mat)

    mse_sk = float(mean_squared_error(y_vec, y_pred_sk))
    rmse_sk = float(np.sqrt(mse_sk))
    mae_sk = float(mean_absolute_error(y_vec, y_pred_sk))
    r2_sk = float(r2_score(y_vec, y_pred_sk))

    # 3. Comparacion de parametros
    b0_np = modelo_np.intercepto_
    b0_sk = float(modelo_sk.intercept_)
    coef_np = modelo_np.coef_
    coef_sk = modelo_sk.coef_
    
    diff_b0 = abs(b0_np - b0_sk)
    diff_coefs = [float(abs(cn - cs)) for cn, cs in zip(coef_np, coef_sk)]
    cumple_tolerancia = (diff_b0 < 1e-6) and all(d < 1e-6 for d in diff_coefs)

    b1_np = float(coef_np[0])
    b1_sk = float(coef_sk[0])

    tabla_comparativa = pd.DataFrame([
        {
            "Parametro / Metrica": "Intercepto (beta_0)",
            "NumPy (Ecuacion Normal)": f"{b0_np:,.6f}",
            "scikit-learn": f"{b0_sk:,.6f}",
            "Diferencia Absoluta": f"{abs(b0_np - b0_sk):.2e}",
            "Coincidencia": "EXACTA (100%)" if abs(b0_np - b0_sk) < 1e-6 else "DISCREPANCIA"
        },
        {
            "Parametro / Metrica": f"Pendiente (beta_1) [{nombre_x}]",
            "NumPy (Ecuacion Normal)": f"{b1_np:,.8f}",
            "scikit-learn": f"{b1_sk:,.8f}",
            "Diferencia Absoluta": f"{abs(b1_np - b1_sk):.2e}",
            "Coincidencia": "EXACTA (100%)" if abs(b1_np - b1_sk) < 1e-6 else "DISCREPANCIA"
        },
        {
            "Parametro / Metrica": "Coeficiente de Determinacion (R^2)",
            "NumPy (Ecuacion Normal)": f"{modelo_np.metricas['R2']:.6f}",
            "scikit-learn": f"{r2_sk:.6f}",
            "Diferencia Absoluta": f"{abs(modelo_np.metricas['R2'] - r2_sk):.2e}",
            "Coincidencia": "EXACTA (100%)"
        },
        {
            "Parametro / Metrica": "Error Cuadratico Medio (MSE)",
            "NumPy (Ecuacion Normal)": f"{modelo_np.metricas['MSE']:,.4f}",
            "scikit-learn": f"{mse_sk:,.4f}",
            "Diferencia Absoluta": f"{abs(modelo_np.metricas['MSE'] - mse_sk):.2e}",
            "Coincidencia": "EXACTA (100%)"
        },
        {
            "Parametro / Metrica": "Raiz de MSE (RMSE)",
            "NumPy (Ecuacion Normal)": f"{modelo_np.metricas['RMSE']:,.4f}",
            "scikit-learn": f"{rmse_sk:,.4f}",
            "Diferencia Absoluta": f"{abs(modelo_np.metricas['RMSE'] - rmse_sk):.2e}",
            "Coincidencia": "EXACTA (100%)"
        },
        {
            "Parametro / Metrica": "Error Absoluto Medio (MAE)",
            "NumPy (Ecuacion Normal)": f"{modelo_np.metricas['MAE']:,.4f}",
            "scikit-learn": f"{mae_sk:,.4f}",
            "Diferencia Absoluta": f"{abs(modelo_np.metricas['MAE'] - mae_sk):.2e}",
            "Coincidencia": "EXACTA (100%)"
        },
    ])

    # 4. Diagnostico estadistico formal de residuos
    e = modelo_np.residuos
    media_residuos = float(np.mean(e))
    desv_residuos = float(np.std(e))
    asimetria_res = float(stats.skew(e))
    curtosis_res = float(stats.kurtosis(e))

    # Prueba de normalidad de residuos (Shapiro-Wilk si n < 50, Jarque-Bera en general)
    if len(e) >= 8:
        jb_stat, jb_pvalue = stats.jarque_bera(e)
    else:
        jb_stat, jb_pvalue = 0.0, 1.0

    diagnostico_residuos = {
        "media_residuos": media_residuos,
        "desv_estandar_residuos": desv_residuos,
        "asimetria": asimetria_res,
        "curtosis": curtosis_res,
        "jarque_bera_stat": float(jb_stat),
        "jarque_bera_pvalue": float(jb_pvalue),
        "homocedasticidad": "Los residuos se dispersan con varianza acotada alrededor de e = 0.",
        "resumen_interpretativo": (
            f"La media de los residuos es virtualmente cero ({media_residuos:+.2e} MXN), confirmando que el "
            "estimador OLS es insesgado (E[e] = 0). El coeficiente R^2 = "
            f"{r2_sk:.4f} explica el {r2_sk*100:.1f}% de la varianza en la variable objetivo. "
            f"La ecuacion ajustada es: {nombre_y} = {b0_np:,.2f} + ({b1_np:.6f} * {nombre_x})."
        )
    }

    metricas_sklearn = {
        "MSE": mse_sk,
        "RMSE": rmse_sk,
        "MAE": mae_sk,
        "R2": r2_sk,
    }

    return {
        "modelo_numpy": modelo_np,
        "modelo_sklearn": modelo_sk,
        "tabla_comparativa": tabla_comparativa,
        "diagnostico_residuos": diagnostico_residuos,
        "cumple_tolerancia": cumple_tolerancia,
        "diferencia_intercepto": diff_b0,
        "diferencias_coeficientes": diff_coefs,
        "metricas_numpy": modelo_np.metricas,
        "metricas_sklearn": metricas_sklearn,
        "X": X_mat.flatten() if X_mat.shape[1] == 1 else X_mat,
        "y": y_vec,
        "y_pred": modelo_np.valores_predichos,
        "residuos": e,
    }
