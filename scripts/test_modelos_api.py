import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi.testclient import TestClient
from services.modelos_api.main import app

def test_api():
    with TestClient(app) as client:
        r_health = client.get('/health')
        print('Health:', r_health.status_code, r_health.json())
        assert r_health.status_code == 200

        r_fc = client.get('/api/v1/pronostico?horizonte_dias=14')
        print('Forecast:', r_fc.status_code, r_fc.json()['total_proyectado_periodo'], 'MXN')
        assert r_fc.status_code == 200

        r_clf = client.post('/api/v1/clasificar', json={
            'arrendatario_id': 'INQ-TEST',
            'dias_mora': 15.0,
            'ratio_gasto_canon': 0.35,
            'variacion_flujo_pct': -0.12,
            'fraccionamiento_pagos': 3,
            'meses_contrato': 6,
            'canon_mensual': 14000.0
        })
        print('Clasificar:', r_clf.status_code, r_clf.json()['nivel_riesgo'], r_clf.json()['probabilidad_porcentaje'])
        assert r_clf.status_code == 200
        print('All Model Serving endpoints OK!')

if __name__ == '__main__':
    test_api()
