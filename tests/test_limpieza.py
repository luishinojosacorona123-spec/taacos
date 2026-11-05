"""Bateria de Pruebas Unitarias para el Modulo de Limpieza y Pipeline del Worker (E2).
Verifica los 5 tipos de error de la Unidad 1.2 conforme a la rubrica de Analitica de Datos.
Ejecutar con: pytest tests/test_limpieza.py -v
"""
import os
import sys
import tempfile
import pandas as pd
import numpy as np
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from services.worker.limpiar_portafolio import limpiar_bitacora_diaria, NOMBRES_CANONICOS
from services.worker.cola import LocalDiskQueue


@pytest.fixture
def dataset_prueba_errores():
    """Genera un DataFrame temporal con los 5 tipos de error sembrados explicitamente."""
    filas = [
        # Registros base validos
        {"fecha": "2026-01-01", "producto": "Carlos Chávez", "categoria": "Casas", "ubicacion": "Colima", "unidades": 10, "precio_unitario": 500, "total": 5000.0},
        {"fecha": "2026-01-02", "producto": "Palma kerpis", "categoria": "Casas", "ubicacion": "Colima", "unidades": 5, "precio_unitario": 300, "total": 1500.0},
        # 1. Error de valor faltante (NaN)
        {"fecha": "2026-01-03", "producto": "Moscú", "categoria": "Casas", "ubicacion": "Villa de Álvarez", "unidades": np.nan, "precio_unitario": 400, "total": 4000.0},
        # 2. Error de duplicado exacto
        {"fecha": "2026-01-01", "producto": "Carlos Chávez", "categoria": "Casas", "ubicacion": "Colima", "unidades": 10, "precio_unitario": 500, "total": 5000.0},
        # 3. Error de formato (minusculas y espacios)
        {"fecha": "2026-01-04", "producto": "  gasera 1  ", "categoria": "Terrenos", "ubicacion": "Colima", "unidades": 8, "precio_unitario": 100, "total": 800.0},
        # 4. Error logico (unidades negativas)
        {"fecha": "2026-01-05", "producto": "Aguacatera", "categoria": "Terrenos", "ubicacion": "Colima", "unidades": -12, "precio_unitario": 600, "total": 7200.0},
        # 5. Valor atipico (outlier = 999)
        {"fecha": "2026-01-06", "producto": "Ceibas", "categoria": "Departamento", "ubicacion": "Manzanillo", "unidades": 999, "precio_unitario": 550, "total": 11000.0},
    ]
    df = pd.DataFrame(filas)
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", encoding="utf-8") as f_raw:
        df.to_csv(f_raw.name, index=False)
        raw_path = f_raw.name

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f_clean:
        clean_path = f_clean.name

    yield raw_path, clean_path

    if os.path.exists(raw_path):
        os.remove(raw_path)
    if os.path.exists(clean_path):
        os.remove(clean_path)


def test_limpieza_corrige_cinco_tipos_de_error(dataset_prueba_errores):
    """Verifica que el modulo detecte y corrija cada una de las 5 anomalias."""
    raw_path, clean_path = dataset_prueba_errores
    df_clean, reporte = limpiar_bitacora_diaria(raw_path=raw_path, clean_path=clean_path)

    # 1. Comprobar que no hay duplicados
    assert len(df_clean) == 6, "Debio eliminar 1 fila duplicada exacta (7 raw -> 6 clean)"
    assert df_clean.duplicated(subset=["fecha", "producto"]).sum() == 0

    # 2. Comprobar correccion de NaN
    assert df_clean["unidades"].isna().sum() == 0
    fila_nan = df_clean[df_clean["fecha"] == "2026-01-03"].iloc[0]
    assert fila_nan["unidades"] == 10, "El valor NaN debio reconstruirse a 10 (4000 / 400)"

    # 3. Comprobar formato y capitalizacion canonica
    fila_fmt = df_clean[df_clean["fecha"] == "2026-01-04"].iloc[0]
    assert fila_fmt["producto"] == "Gasera 1", "Debio normalizar '  gasera 1  ' a 'Gasera 1'"

    # 4. Comprobar correccion de negativos
    fila_neg = df_clean[df_clean["fecha"] == "2026-01-05"].iloc[0]
    assert fila_neg["unidades"] == 12, "Las unidades negativas -12 debieron convertirse a +12"

    # 5. Comprobar correccion de outlier 999
    fila_out = df_clean[df_clean["fecha"] == "2026-01-06"].iloc[0]
    assert fila_out["unidades"] == 20, "El outlier 999 debio restituirse a 20 unidades (11000 / 550)"

    # Consistencia aritmetica estricta
    assert np.allclose(df_clean["total"], df_clean["unidades"] * df_clean["precio_unitario"])


def test_integridad_bitacora_diaria_oficial():
    """Verifica la ejecucion sobre la bitacora diaria oficial del Data Lake (>7,000 registros)."""
    raw_oficial = os.path.join(BASE_DIR, "raw", "bitacora_diaria_portafolio_raw.csv")
    clean_oficial = os.path.join(BASE_DIR, "clean", "bitacora_diaria_portafolio_clean.csv")

    assert os.path.exists(raw_oficial), "El archivo raw oficial debe existir en el repositorio"
    df_c, reporte = limpiar_bitacora_diaria(raw_path=raw_oficial, clean_path=clean_oficial)

    assert len(df_c) >= 5000, f"Debe superar los 5,000 registros exigidos por la rubrica (actual: {len(df_c)})"
    assert df_c.isna().sum().sum() == 0, "No debe quedar ningun valor NaN en la zona clean/"
    assert (df_c["unidades"] < 0).sum() == 0, "No deben quedar unidades negativas"
    assert (df_c["unidades"] >= 900).sum() == 0, "No deben quedar valores atipicos sembrados (999)"
    assert set(df_c["producto"].unique()).issubset(set(NOMBRES_CANONICOS.values())), "Todos los productos deben coincidir con el catalogo canonico"


def test_politica_reintentos_y_dlq():
    """Verifica que un mensaje con archivo corrupto sea canalizado a la Dead Letter Queue."""
    cola = LocalDiskQueue(max_retries=2)
    payload_invalido = {"batch_id": "test_error", "raw_file": "raw/archivo_fantasma_no_existe.csv"}
    msg_id = cola.send_message(payload_invalido)

    # Intento 1
    msgs = cola.receive_messages(max_messages=1, visibility_timeout=0)
    assert len(msgs) == 1
    assert msgs[0]["Attempts"] == 1

    # Intento 2
    msgs = cola.receive_messages(max_messages=1, visibility_timeout=0)
    assert len(msgs) == 1
    assert msgs[0]["Attempts"] == 2

    # Intento 3: sobrepasa max_retries=2, debe moverse a DLQ
    msgs = cola.receive_messages(max_messages=1, visibility_timeout=0)
    assert len(msgs) == 0, "El mensaje debio canalizarse a la DLQ tras agotar reintentos"

    stats = cola.get_stats()
    assert stats["mensajes_en_dlq"] >= 1, "Debe registrarse al menos un mensaje en DLQ"
