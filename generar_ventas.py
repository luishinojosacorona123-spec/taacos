"""Generador de operaciones diarias sinteticas adaptado al giro del Portafolio Inmobiliario (12 unidades/conceptos).
Basado directamente en el script oficial del Proyecto Integrador (páginas 23 y 24):
- Periodo: 2025-01-01 a 2026-09-30 (21 meses diarios, 638 días)
- Volumen bruto: 7,686 registros (7,656 base + 30 duplicados)
- Errores sembrados: 40 faltantes (NaN), 15 negativos, 10 atípicos (999), 25 en minúsculas, 30 duplicados
  e inconsistencia lógica en la columna `total`.
Uso: python generar_ventas.py -> raw/bitacora_diaria_portafolio_raw.csv y clean/bitacora_diaria_portafolio_clean.csv
"""
import os
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
dias = pd.date_range("2025-01-01", "2026-09-30", freq="D")

# Adaptación al giro inmobiliario (12 activos/conceptos de cobro y servicio del portafolio en Colima, VdA y Manzanillo)
# activo: (tarifa_base_mxn, frecuencia_operativa_base_diaria)
productos = {
    "Carlos Chávez": (515, 18),
    "Palma kerpis": (330, 15),
    "Moscú": (485, 16),
    "Agua Dulce": (215, 14),
    "Gasera 1": (100, 12),
    "Gasera 2": (150, 12),
    "Carretera": (200, 14),
    "Aguacatera": (635, 20),
    "Ceibas": (550, 22),
    "Local Colima Centro": (420, 15),
    "Versa 1": (150, 10),
    "Versa 2": (150, 10),
}

CATALOGO_INFO = {
    "Carlos Chávez": ("Casas", "Colima", 3500000, 15500),
    "Palma kerpis": ("Casas", "Colima", 2000000, 9900),
    "Moscú": ("Casas", "Villa de Álvarez", 2700000, 14500),
    "Agua Dulce": ("Casas", "Villa de Álvarez", 1450000, 6500),
    "Gasera 1": ("Terrenos", "Colima", 3000000, 3000),
    "Gasera 2": ("Terrenos", "Colima", 2500000, 4500),
    "Carretera": ("Terrenos", "Colima", 1500000, 6000),
    "Aguacatera": ("Terrenos", "Colima", 5000000, 19000),
    "Ceibas": ("Departamento", "Manzanillo", 2750000, 16500),
    "Local Colima Centro": ("Casas", "Colima", 1800000, 8500),
    "Versa 1": ("Vehículos", "Colima", 125000, 0),
    "Versa 2": ("Vehículos", "Colima", 125000, 0),
}

semana = np.array([0.85, 0.80, 0.85, 0.90, 1.10, 1.35, 1.20])  # lun..dom
filas = []
for dia in dias:
    t = (dia - dias[0]).days
    tendencia = 1 + 0.0004 * t
    quincena = 1.25 if dia.day in (15, 16, 30, 31, 1) else 1.0
    calor = 1.30 if dia.month in (4, 5, 6) else 1.0
    fiestas = 1.40 if (dia.month == 12 and dia.day >= 15) else 1.0
    for prod, (precio, base) in productos.items():
        efecto_calor = calor if prod in ("Carlos Chávez", "Ceibas", "Aguacatera") else 1.0
        lam = base * tendencia * semana[dia.weekday()] * quincena * efecto_calor * fiestas
        unidades = rng.poisson(lam)
        cat, ubic, val_prop, renta_mes = CATALOGO_INFO[prod]
        filas.append([
            dia.date(), prod, cat, ubic, unidades, precio, unidades * precio
        ])

df = pd.DataFrame(
    filas,
    columns=["fecha", "producto", "categoria", "ubicacion", "unidades", "precio_unitario", "total"],
)

# Errores sembrados para practicar preprocesamiento (exactamente los del PDF página 24)
n = len(df)
df.loc[rng.choice(n, 40, replace=False), "unidades"] = np.nan       # 40 faltantes
df.loc[rng.choice(n, 15, replace=False), "unidades"] *= -1          # 15 errores lógicos (negativos e inconsistencia con total)
df.loc[rng.choice(n, 10, replace=False), "unidades"] = 999          # 10 atípicos (outliers = 999)
idx = rng.choice(n, 25, replace=False)
df.loc[idx, "producto"] = df.loc[idx, "producto"].str.lower()       # 25 errores de formato (minúsculas)
df = pd.concat([df, df.sample(30, random_state=1)])                 # 30 duplicados
df = df.sample(frac=1, random_state=2).reset_index(drop=True)

os.makedirs("raw", exist_ok=True)
os.makedirs("clean", exist_ok=True)
df.to_csv("raw/bitacora_diaria_portafolio_raw.csv", index=False)
print(f"[RAW] {len(df):,} registros generados de {dias[0].date()} a {dias[-1].date()}")
