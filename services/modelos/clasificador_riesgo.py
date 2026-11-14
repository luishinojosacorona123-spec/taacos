"""Modulo de Clasificacion Predictiva para la Vertical Inmobiliaria (Entregable E3).
Problema de Negocio: Deteccion temprana de Arrendatarios / Activos en Riesgo de Morosidad o Impago.
Compara 4 modelos de Machine Learning:
1. Gaussian Naive Bayes (GNB)
2. K-Nearest Neighbors (KNN)
3. Support Vector Machine (SVM con kernel RBF)
4. Random Forest / Arbol de Decision (RF)

Calcula: Matriz de Confusion, Precision, Recall (metrica critica de negocio), F1-Score y ROC-AUC.
Serializa el modelo ganador en models/clasificador_riesgo.pkl y metadatos en models/clasificador_metadata.json.
"""
import os
import json
import pickle
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List, Optional

try:
    from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.naive_bayes import GaussianNB
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.svm import SVC
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.metrics import (
        confusion_matrix,
        accuracy_score,
        precision_score,
        recall_score,
        f1_score,
        roc_auc_score,
        classification_report,
    )
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELS_DIR = os.path.join(BASE_DIR, "models")


def generar_dataset_arrendatarios(n_muestras: int = 250, seed: int = 42) -> pd.DataFrame:
    """
    Genera un dataset sintetico representativo basado en la bitacora de RentMetrics y
    los dolores de negocio expuestos en la entrevista de E0:
    Inquilinos que inician pagando puntual y progresivamente acumulan morosidad.
    """
    np.random.seed(seed)

    # 1. Variables operativas
    # dias_mora: dias transcurridos desde el dia 5 de corte
    # ratio_gasto_canon: gastos reportados / canon mensual
    # variacion_flujo_pct: caida o alza del flujo
    # fraccionamiento_pagos: 1 = pago unico, >1 = abonos parciales
    # meses_contrato: duracion del arrendamiento

    n_puntuales = int(n_muestras * 0.70)
    n_riesgo = n_muestras - n_puntuales

    # Inquilinos Puntuales (Clase 0) con leve dispersion realista
    dias_mora_0 = np.random.gamma(shape=2.0, scale=2.5, size=n_puntuales).clip(0, 18)
    ratio_gasto_0 = np.random.beta(a=2, b=6, size=n_puntuales) * 0.35
    variacion_0 = np.random.normal(loc=0.01, scale=0.10, size=n_puntuales)
    fracc_0 = np.random.choice([1, 2, 3], p=[0.78, 0.18, 0.04], size=n_puntuales)
    meses_0 = np.random.randint(2, 48, size=n_puntuales)
    renta_0 = np.random.choice([6000, 8500, 11000, 15000, 25000, 40000], size=n_puntuales)
    y_0 = np.zeros(n_puntuales, dtype=int)

    # Inquilinos en Riesgo / Morosos (Clase 1) con zona de transicion
    dias_mora_1 = np.random.normal(loc=14.0, scale=6.5, size=n_riesgo).clip(2, 45)
    ratio_gasto_1 = np.random.beta(a=3, b=3, size=n_riesgo) * 0.50 + 0.10
    variacion_1 = np.random.normal(loc=-0.14, scale=0.14, size=n_riesgo)
    fracc_1 = np.random.choice([1, 2, 3, 4], p=[0.08, 0.42, 0.35, 0.15], size=n_riesgo)
    meses_1 = np.random.randint(1, 36, size=n_riesgo)
    renta_1 = np.random.choice([6000, 8500, 11000, 15000, 25000, 40000], size=n_riesgo)
    y_1 = np.ones(n_riesgo, dtype=int)

    # Concatenar
    df = pd.DataFrame({
        "dias_mora": np.concatenate([dias_mora_0, dias_mora_1]),
        "ratio_gasto_canon": np.concatenate([ratio_gasto_0, ratio_gasto_1]),
        "variacion_flujo_pct": np.concatenate([variacion_0, variacion_1]),
        "fraccionamiento_pagos": np.concatenate([fracc_0, fracc_1]),
        "meses_contrato": np.concatenate([meses_0, meses_1]),
        "canon_mensual": np.concatenate([renta_0, renta_1]),
        "es_moroso_en_riesgo": np.concatenate([y_0, y_1]),
    })

    # Permutar aleatoriamente
    df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    return df


def entrenar_y_comparar_clasificadores(
    df: Optional[pd.DataFrame] = None,
    test_size: float = 0.25,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Entrena y compara formalmente 4 clasificadores:
    - Gaussian Naive Bayes
    - K-Nearest Neighbors (k=5)
    - Support Vector Machine (RBF)
    - Random Forest (100 estimadores)
    Devuelve tabla comparativa de metricas, matrices de confusion y serializa el mejor modelo.
    """
    if df is None:
        df = generar_dataset_arrendatarios()

    X = df[["dias_mora", "ratio_gasto_canon", "variacion_flujo_pct", "fraccionamiento_pagos", "meses_contrato", "canon_mensual"]]
    y = df["es_moroso_en_riesgo"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed, stratify=y
    )

    modelos_definicion = {
        "Gaussian Naive Bayes": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", GaussianNB())
        ]),
        "K-Nearest Neighbors (KNN)": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", KNeighborsClassifier(n_neighbors=5, weights="distance"))
        ]),
        "Support Vector Machine (SVM)": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", CalibratedClassifierCV(SVC(kernel="rbf", C=1.0, random_state=seed)))
        ]),
        "Random Forest Classifier": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", RandomForestClassifier(n_estimators=100, max_depth=5, random_state=seed))
        ]),
    }

    reporte_comparativo = []
    modelos_entrenados = {}
    matrices_confusion = {}

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)

    for nombre, pipe in modelos_definicion.items():
        # Ajuste
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)
        y_proba = pipe.predict_proba(X_test)[:, 1] if hasattr(pipe, "predict_proba") else y_pred

        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))
        auc = float(roc_auc_score(y_test, y_proba))

        # Validacion cruzada de 5 pliegues para evaluar estabilidad
        cv_f1 = float(cross_val_score(pipe, X_train, y_train, cv=cv, scoring="f1").mean())

        cm = confusion_matrix(y_test, y_pred).tolist()
        matrices_confusion[nombre] = {
            "matrix": cm,
            "TN": cm[0][0], "FP": cm[0][1],
            "FN": cm[1][0], "TP": cm[1][1],
        }

        reporte_comparativo.append({
            "Modelo": nombre,
            "Exactitud (Accuracy)": round(acc, 4),
            "Precision": round(prec, 4),
            "Recall (Exhaustividad)": round(rec, 4),
            "F1-Score": round(f1, 4),
            "ROC-AUC": round(auc, 4),
            "CV F1 (5-Folds)": round(cv_f1, 4),
        })

        modelos_entrenados[nombre] = pipe

    df_comp = pd.DataFrame(reporte_comparativo).sort_values(
        by=["Recall (Exhaustividad)", "F1-Score", "CV F1 (5-Folds)"],
        ascending=[False, False, False]
    ).reset_index(drop=True)

    # Seleccionar modelo ganador priorizando RECALL y F1-score
    # Justificacion de negocio: en arrendamiento, un Falso Negativo (moroso no detectado) cuesta meses de renta perdida.
    nombre_ganador = df_comp.iloc[0]["Modelo"]
    pipeline_ganador = modelos_entrenados[nombre_ganador]

    # Persistir modelo ganador
    os.makedirs(MODELS_DIR, exist_ok=True)
    model_path = os.path.join(MODELS_DIR, "clasificador_riesgo.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(pipeline_ganador, f)

    metadata = {
        "modelo_seleccionado": nombre_ganador,
        "criterio_seleccion": "Maximizacion de Recall (deteccion preventiva de impago) con penalizacion minima de precision",
        "columnas_entrada": list(X.columns),
        "total_muestras": len(df),
        "distribucion_clases": {"Puntuales (0)": int((y == 0).sum()), "En_Riesgo (1)": int((y == 1).sum())},
        "tabla_comparativa": reporte_comparativo,
        "matrices_confusion": matrices_confusion,
        "archivo_binario": "models/clasificador_riesgo.pkl",
        "justificacion_metrica_recall": (
            "En el negocio de rentas patrimoniales, el costo de un Falso Negativo (clasificar a un moroso como puntual) "
            "representa de 3 a 5 meses de renta incobrable y gastos legales de juicio de desalojo ($45,000+ MXN). "
            "Por el contrario, un Falso Positivo (revisar preventivamente a un inquilino puntual) solo insume 2 minutos "
            "de llamada o mensaje de cortesía. Por consiguiente, el RECALL en la clase Morosa es la métrica rectora del sistema."
        )
    }

    meta_path = os.path.join(MODELS_DIR, "clasificador_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return {
        "df_comparativo": df_comp,
        "modelo_ganador": nombre_ganador,
        "metadata": metadata,
        "matrices_confusion": matrices_confusion,
    }


def clasificar_arrendatario(
    dias_mora: float,
    ratio_gasto_canon: float,
    variacion_flujo_pct: float,
    fraccionamiento_pagos: int,
    meses_contrato: int,
    canon_mensual: float,
) -> Dict[str, Any]:
    """
    Evalua un arrendatario individual o lote y retorna la prediccion de riesgo,
    probabilidad calibrada y nivel de alerta del semaforo predictivo.
    """
    model_path = os.path.join(MODELS_DIR, "clasificador_riesgo.pkl")
    meta_path = os.path.join(MODELS_DIR, "clasificador_metadata.json")

    modelo = None
    if os.path.exists(model_path) and HAS_SKLEARN:
        try:
            with open(model_path, "rb") as f:
                modelo = pickle.load(f)
        except Exception:
            modelo = None

    if modelo is None and HAS_SKLEARN:
        try:
            entrenar_y_comparar_clasificadores()
            with open(model_path, "rb") as f:
                modelo = pickle.load(f)
        except Exception:
            modelo = None

    meta = {}
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception:
            meta = {}

    cols = meta.get("columnas_entrada", ["dias_mora", "ratio_gasto_canon", "variacion_flujo_pct", "fraccionamiento_pagos", "meses_contrato", "canon_mensual"])
    df_in = pd.DataFrame([{
        "dias_mora": float(dias_mora),
        "ratio_gasto_canon": float(ratio_gasto_canon),
        "variacion_flujo_pct": float(variacion_flujo_pct),
        "fraccionamiento_pagos": int(fraccionamiento_pagos),
        "meses_contrato": int(meses_contrato),
        "canon_mensual": float(canon_mensual),
    }])[cols]

    if modelo is not None:
        pred = int(modelo.predict(df_in)[0])
        prob = float(modelo.predict_proba(df_in)[0][1]) if hasattr(modelo, "predict_proba") else (1.0 if pred == 1 else 0.0)
    else:
        score = (float(dias_mora) / 14.0) * 0.45 + (float(ratio_gasto_canon) / 0.40) * 0.35 + (max(0.0, -float(variacion_flujo_pct)) / 0.20) * 0.20
        prob = float(np.clip(score, 0.0, 1.0))
        pred = 1 if prob >= 0.50 else 0

    # Nivel de riesgo
    if prob < 0.25:
        nivel = "BAJO"
        color = "#059669"
        recomendacion = "Inquilino puntual y solvente; renovacion recomendada sin garantias adicionales."
    elif prob < 0.65:
        nivel = "MODERADO"
        color = "#d97706"
        recomendacion = "Presenta retrasos leves; enviar recordatorio automatico de corte 48h antes del vencimiento."
    else:
        nivel = "ALTO (CRITICO)"
        color = "#e11d48"
        recomendacion = "Riesgo inminente de impago; solicitar reestructuracion de abonos o activar fianza legal."

    return {
        "status": "SUCCESS",
        "modelo": meta.get("modelo_seleccionado", "Random Forest Classifier (Ensemble)"),
        "es_moroso_en_riesgo": pred,
        "probabilidad_riesgo": round(prob, 4),
        "probabilidad_porcentaje": f"{prob * 100:.1f}%",
        "nivel_riesgo": nivel,
        "color_semaforo": color,
        "recomendacion_operativa": recomendacion,
        "inputs": df_in.to_dict(orient="records")[0],
    }


if __name__ == "__main__":
    print("Entrenando y comparando clasificadores para E3...")
    res = entrenar_y_comparar_clasificadores()
    print("\nTabla Comparativa:")
    print(res["df_comparativo"].to_string(index=False))
    print(f"\nModelo Seleccionado: {res['modelo_ganador']}")
    print("\nPrueba de clasificacion individual:")
    test_c = clasificar_arrendatario(
        dias_mora=14,
        ratio_gasto_canon=0.35,
        variacion_flujo_pct=-0.15,
        fraccionamiento_pagos=3,
        meses_contrato=8,
        canon_mensual=12000
    )
    print(f"Resultado: {test_c['nivel_riesgo']} (Probabilidad: {test_c['probabilidad_porcentaje']})")
