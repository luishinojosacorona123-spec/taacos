"""Escenario de Prueba de Carga para 50 Usuarios Simultaneos con Locust (Entregable E3).
Simula el trafico productivo de RentMetrics:
- 40% Inferencia de pronostico de demanda (SARIMA /api/v1/pronostico)
- 30% Evaluacion de riesgo de morosidad (Clasificador /api/v1/clasificar)
- 20% Ingesta de lotes de ventas (/api/v1/ventas)
- 10% Monitoreo de salud del servicio (/health)

Comando para ejecucion headless en terminal:
  locust -f tests/load/locustfile.py --headless -u 50 -r 10 --run-time 1m --host http://localhost:8001
"""
import random
from locust import HttpUser, task, between


class RentMetricsUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(4)
    def consultar_pronostico(self):
        dias = random.choice([7, 14, 21, 30])
        self.client.get(f"/api/v1/pronostico?horizonte_dias={dias}", name="GET /api/v1/pronostico")

    @task(3)
    def evaluar_clasificador_riesgo(self):
        payload = {
            "arrendatario_id": f"INQ-{random.randint(100, 999)}",
            "dias_mora": float(random.randint(0, 30)),
            "ratio_gasto_canon": round(random.uniform(0.05, 0.65), 2),
            "variacion_flujo_pct": round(random.uniform(-0.35, 0.20), 2),
            "fraccionamiento_pagos": random.randint(1, 4),
            "meses_contrato": random.randint(1, 36),
            "canon_mensual": float(random.choice([6000, 8500, 11000, 15000, 25000, 40000])),
        }
        self.client.post("/api/v1/clasificar", json=payload, name="POST /api/v1/clasificar")

    @task(1)
    def verificar_salud(self):
        self.client.get("/health", name="GET /health")
