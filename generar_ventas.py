"""Generador de operaciones diarias SINTETICAS adaptado al portafolio inmobiliario.
Basado en el generador oficial del Proyecto Integrador (kit de arranque, pags. 23-24): misma semilla (42),
mismo periodo (2025-01-01 a 2026-09-30, 638 dias), mismos factores de tendencia, ciclo semanal,
efecto quincena, temporada de calor y fiestas, y los mismos 5 tipos de errores sembrados.

IMPORTANTE: estos datos son SIMULADOS. No son registros del cliente; sirven para tener volumen diario
(>12 meses, >5,000 registros) y para el analisis espectral. Los datos reales del cliente son la matriz
mensual raw/portafolio_inmuebles_raw.csv.

Cambios respecto al kit: los 12 productos de la tiendita se sustituyen por los 11 activos del portafolio
y el precio_unitario representa la tarifa por servicio/cobro. Volumen bruto: 638 dias x 11 activos = 7,018
+ 30 duplicados = 7,048 registros.
Uso: python generar_ventas.py -> raw/bitacora_diaria_portafolio_raw.csv
"""
import os
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
dias = pd.date_range("2025-01-01", "2026-09-30", freq="D")

# activo: (precio MXN por servicio/cobro, volumen base diario)
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
    "Versa 1": (150, 10),
    "Versa 2": (150, 10),
}

CATALOGO_INFO = {
    "Carlos Chávez": ("Casas", "Colima"),
    "Palma kerpis": ("Casas", "Colima"),
    "Moscú": ("Casas", "Villa de Álvarez"),
    "Agua Dulce": ("Casas", "Villa de Álvarez"),
    "Gasera 1": ("Terrenos", "Colima"),
    "Gasera 2": ("Terrenos", "Colima"),
    "Carretera": ("Terrenos", "Colima"),
    "Aguacatera": ("Terrenos", "Colima"),
    "Ceibas": ("Departamento", "Manzanillo"),
    "Versa 1": ("Vehículos", "Colima"),
    "Versa 2": ("Vehículos", "Colima"),
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
        cat, ubic = CATALOGO_INFO[prod]
        filas.append([dia.date(), prod, cat, ubic, unidades, precio, unidades * precio])

df = pd.DataFrame(
    filas,
    columns=["fecha", "producto", "categoria", "ubicacion", "unidades", "precio_unitario", "total"],
)

# Errores sembrados (los mismos del kit oficial)
n = len(df)
df.loc[rng.choice(n, 40, replace=False), "unidades"] = np.nan       # 40 faltantes
df.loc[rng.choice(n, 15, replace=False), "unidades"] *= -1          # 15 errores logicos (negativos)
df.loc[rng.choice(n, 10, replace=False), "unidades"] = 999          # 10 atipicos
idx = rng.choice(n, 25, replace=False)
df.loc[idx, "producto"] = df.loc[idx, "producto"].str.lower()       # 25 errores de formato
df = pd.concat([df, df.sample(30, random_state=1)])                 # 30 duplicados
df = df.sample(frac=1, random_state=2).reset_index(drop=True)

os.makedirs("raw", exist_ok=True)
df.to_csv("raw/bitacora_diaria_portafolio_raw.csv", index=False)
print(f"[RAW] {len(df):,} registros sinteticos de {dias[0].date()} a {dias[-1].date()}")
