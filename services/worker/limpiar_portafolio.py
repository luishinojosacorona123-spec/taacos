"""Limpieza reproducible de la bitacora diaria sintetica (Unidad 1.2 / E1 y modulo base del worker de E2).
raw/bitacora_diaria_portafolio_raw.csv -> clean/bitacora_diaria_portafolio_clean.csv
Cuenta cuantos registros se corrigen de cada uno de los 5 tipos de error.
"""
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIARIO_PATH = os.path.join(BASE_DIR, "raw", "bitacora_diaria_portafolio_raw.csv")
CLEAN_DIARIO_PATH = os.path.join(BASE_DIR, "clean", "bitacora_diaria_portafolio_clean.csv")

NOMBRES_CANONICOS = {
    n.lower(): n for n in [
        "Carlos Chávez", "Palma kerpis", "Moscú", "Agua Dulce", "Gasera 1", "Gasera 2",
        "Carretera", "Aguacatera", "Ceibas", "Versa 1", "Versa 2",
    ]
}


def limpiar_bitacora_diaria(raw_path: str = RAW_DIARIO_PATH, clean_path: str = CLEAN_DIARIO_PATH):
    """Devuelve (df_limpio, reporte). El total original no se altera: se usa para recuperar unidades."""
    df = pd.read_csv(raw_path)
    n_raw = len(df)

    # Faltantes, negativos y atipicos se cuentan ANTES de corregirlos
    n_faltantes = int(df["unidades"].isna().sum())
    n_negativos = int((df["unidades"] < 0).sum())
    n_atipicos = int((df["unidades"] >= 900).sum())

    # Formato: nombres de activo en minusculas / con espacios
    antes = df["producto"].astype(str)
    df["producto"] = antes.str.strip().str.lower().map(lambda x: NOMBRES_CANONICOS.get(x, x))
    n_formato = int((antes != df["producto"]).sum())

    # Duplicados exactos por (fecha, activo)
    df = df.drop_duplicates(subset=["fecha", "producto"], keep="first").copy()
    n_duplicados = n_raw - len(df)

    # Errores logicos / atipicos / faltantes: se recupera unidades = total / precio_unitario
    df["unidades"] = df["unidades"].abs()
    malos = df["unidades"].isna() | (df["unidades"] >= 900)
    df.loc[malos, "unidades"] = (df.loc[malos, "total"] / df.loc[malos, "precio_unitario"]).round()
    df["unidades"] = df["unidades"].astype(int)
    df["total"] = (df["unidades"] * df["precio_unitario"]).astype(float)
    df["propiedad"] = df["producto"]
    df["ingreso_diario"] = df["total"]
    df["utilidad_diaria"] = df["total"]

    df = df.sort_values(["fecha", "producto"]).reset_index(drop=True)
    df.to_csv(clean_path, index=False)

    reporte = pd.DataFrame([
        {"Tipo de error": "1. Valores faltantes (NaN)", "Registros corregidos": n_faltantes},
        {"Tipo de error": "2. Duplicados", "Registros corregidos": n_duplicados},
        {"Tipo de error": "3. Errores de formato (minúsculas)", "Registros corregidos": n_formato},
        {"Tipo de error": "4. Errores lógicos (unidades negativas)", "Registros corregidos": n_negativos},
        {"Tipo de error": "5. Valores atípicos (999)", "Registros corregidos": n_atipicos},
    ])
    return df, reporte


if __name__ == "__main__":
    df_c, rep = limpiar_bitacora_diaria()
    print(f"[CLEAN] {len(df_c):,} registros limpios")
    print(rep.to_string(index=False))
