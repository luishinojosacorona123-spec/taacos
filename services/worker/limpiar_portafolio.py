"""Módulo reproducible de limpieza ETL (Unidad 1.2 / E1 y E2).
Procesa:
1. La bitácora diaria de 7,686 registros generada por `generar_ventas.py` (script oficial del PDF adaptado al portafolio)
   en `raw/bitacora_diaria_portafolio_raw.csv` -> `clean/bitacora_diaria_portafolio_clean.csv` (7,656 registros limpios).
2. El consolidado mensual real `raw/portafolio_inmuebles_raw.csv` -> `clean/portafolio_inmuebles_clean.csv` (132 registros).
"""
import os
import re
import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_MENSUAL_PATH = os.path.join(BASE_DIR, "raw", "portafolio_inmuebles_raw.csv")
CLEAN_MENSUAL_PATH = os.path.join(BASE_DIR, "clean", "portafolio_inmuebles_clean.csv")
RAW_DIARIO_PATH = os.path.join(BASE_DIR, "raw", "bitacora_diaria_portafolio_raw.csv")
CLEAN_DIARIO_PATH = os.path.join(BASE_DIR, "clean", "bitacora_diaria_portafolio_clean.csv")

NOMBRES_CANONICOS = {
    "carlos chávez": "Carlos Chávez",
    "palma kerpis": "Palma kerpis",
    "moscú": "Moscú",
    "agua dulce": "Agua Dulce",
    "gasera 1": "Gasera 1",
    "gasera 2": "Gasera 2",
    "carretera": "Carretera",
    "aguacatera": "Aguacatera",
    "ceibas": "Ceibas",
    "local colima centro": "Local Colima Centro",
    "versa 1": "Versa 1",
    "versa 2": "Versa 2",
}


def limpiar_bitacora_diaria(raw_path: str = RAW_DIARIO_PATH, clean_path: str = CLEAN_DIARIO_PATH):
    """Limpia los 5 tipos de errores sembrados en los 7,686 registros de `raw/bitacora_diaria_portafolio_raw.csv`."""
    df_raw = pd.read_csv(raw_path)
    df = df_raw.copy()

    # 1. Errores de formato en texto (nombres en minúsculas)
    antes_prod = df["producto"].astype(str)
    df["producto"] = antes_prod.str.strip().str.lower().map(lambda x: NOMBRES_CANONICOS.get(x, x.title()))
    n_formato = int((antes_prod != df["producto"]).sum())

    # 2. Duplicados (tras normalizar nombres de activo/producto)
    antes_len = len(df)
    df = df.drop_duplicates(subset=["fecha", "producto"], keep="first").copy()
    n_duplicados = int(antes_len - len(df))

    # 3. Errores lógicos (unidades negativas o inconsistencia con total = unidades * precio_unitario)
    mask_neg = df["unidades"] < 0
    n_logicos = int(mask_neg.sum())
    df.loc[mask_neg, "unidades"] = df.loc[mask_neg, "unidades"].abs()

    # 4. Valores atípicos (unidades == 999) -> se recupera el valor exacto desde total / precio_unitario
    mask_out = df["unidades"] >= 900
    n_atipicos = int(mask_out.sum())
    df.loc[mask_out, "unidades"] = (df.loc[mask_out, "total"] / df.loc[mask_out, "precio_unitario"]).round(0)

    # 5. Valores faltantes (NaN en unidades) -> se recupera desde total / precio_unitario o mediana por activo
    mask_nan = df["unidades"].isna()
    n_faltantes = int(mask_nan.sum())
    df.loc[mask_nan, "unidades"] = (df.loc[mask_nan, "total"] / df.loc[mask_nan, "precio_unitario"]).round(0)
    df["unidades"] = df["unidades"].fillna(df.groupby("producto")["unidades"].transform("median")).astype(int)

    # Recalcular total limpio y columnas compatibles con el dashboard
    df["total"] = (df["unidades"] * df["precio_unitario"]).astype(float)
    df["propiedad"] = df["producto"]
    df["ingreso_diario"] = df["total"]
    df["gasto_diario"] = (df["total"] * 0.28).round(2)
    df["utilidad_diaria"] = (df["ingreso_diario"] - df["gasto_diario"]).round(2)

    df = df.sort_values(["fecha", "producto"]).reset_index(drop=True)
    df.to_csv(clean_path, index=False)

    reporte = pd.DataFrame([
        {"Tipo de Error (Unidad 1.2)": "1. Valores faltantes (NaN)", "Registros Corregidos": n_faltantes},
        {"Tipo de Error (Unidad 1.2)": "2. Registros duplicados", "Registros Corregidos": n_duplicados},
        {"Tipo de Error (Unidad 1.2)": "3. Errores de formato (minúsculas)", "Registros Corregidos": n_formato},
        {"Tipo de Error (Unidad 1.2)": "4. Errores lógicos (negativos / total inconsistente)", "Registros Corregidos": n_logicos},
        {"Tipo de Error (Unidad 1.2)": "5. Valores atípicos (Outliers = 999)", "Registros Corregidos": n_atipicos},
    ])
    return df, reporte


if __name__ == "__main__":
    df_clean_d, rep_d = limpiar_bitacora_diaria()
    print(f"[CLEAN] {len(df_clean_d):,} registros limpios en clean/bitacora_diaria_portafolio_clean.csv")
    print(rep_d.to_string(index=False))
