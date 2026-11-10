# Entregable E3 · Inteligencia en Producción: El Modelo Vive en la Nube

**Proyecto Integrador:** DATA STARTUP · RentMetrics (Gestión y Analítica Patrimonial de Arrendamientos)  
**Institución:** Instituto Tecnológico de Colima (TecNM)  
**Materias:** Cómputo en la Nube (IAD-2408) & Analítica de Datos (IAD-2403)  
**Equipo de Trabajo:**
* **Manuel Alexander Hernández Chávez** · *Data Lead*
* **Luis Antonio Hinojosa Corona** · *Cloud Lead*
**Versión del Sistema:** RentMetrics v3.0  
**Fecha de Entrega:** Noviembre 2026  

---

## 1. Resumen Ejecutivo del Entregable E3

El Entregable E3 representa la culminación técnica del proyecto integrador, materializando el paradigma de **MLOps y Arquitectura en la Nube de Alta Disponibilidad**. En esta fase, los modelos predictivos y de aprendizaje automático dejan de ser artefactos exploratorios en cuadernos locales para convertirse en microservicios contenerizados, autoescalables y desacoplados, consumidos en tiempo real por la aplicación de toma de decisiones:

1. **Ingeniería de Modelos Serializados y Servidos:**
   * **Modelo SARIMA $(1, 1, 1) \times (1, 0, 1)_7$:** Proyección diaria del flujo de ingresos con descomposición estacional semanal, generando intervalos de predicción y bandas de confianza del **80% y 95%** para horizontes de 7 a 30 días. Serializado como binario productivo en `models/sarima_model.pkl` y validado en holdout de 30 días ($RMSE = \$17,334.07$, $MAPE = 22.49\%$).
   * **Clasificador Multimodelo de Riesgo de Arrendatarios:** Evaluación exhaustiva bajo validación cruzada estratificada (5-folds) de 4 familias algorítmicas: Gaussian Naive Bayes, K-Nearest Neighbors ($k=5$), Support Vector Machine (kernel RBF) y Random Forest. Selección fundamentada en el **Recall (100% de detección preventiva)**, evitando pérdidas patrimoniales por morosidad crítica ($>\$45,000$ MXN por juicio de desalojo). Serializado en `models/clasificador_riesgo.pkl`.
   * **Microservicio REST de Inferencia (`modelos_api`):** Servicio FastAPI independiente con contratos Pydantic estrictos, documentación interactiva Swagger UI (`/docs`), verificación de salud (`/health`), endpoint de proyección estocástica (`/api/v1/pronostico`) y motor de clasificación temprana (`/api/v1/clasificar`).
2. **Infraestructura Contenerizada y Orquestada en la Nube:**
   * **Contenedores Multi-Stage con Docker Compose:** 4 contenedores desacoplados (`Dockerfile.ingesta`, `Dockerfile.modelos`, `Dockerfile.tablero`, `Dockerfile.worker`) con usuario sin privilegios `appuser`, capas de cache optimizadas y arranque integral local mediante `docker-compose up -d`.
   * **Orquestación en Kubernetes (`k8s/`):** Manifiestos de `Namespace`, `ConfigMap`, `Secret`, `Deployment`, `Service` y `HorizontalPodAutoscaler` (HPA) con escalado elástico de 2 a 10 réplicas basado en umbrales de CPU ($70\%$) y memoria ($80\%$).
   * **Computación Serverless Event-Driven:** Función AWS Lambda / Cloud Functions (`services/serverless/lambda_function.py`) que procesa de manera reactiva la llegada de archivos a `raw/` en S3 o lotes en SQS, ejecutando limpieza automatizada y canalizando excepciones a *Dead Letter Queue* (DLQ).
   * **Infraestructura como Código (IaC) con Terraform:** Definición declarativa modular en `terraform/` aprovisionando el Data Lake S3 con ciclo de vida, colas SQS con política de redrive, y políticas IAM con principio de mínimo privilegio (*Least Privilege*).
   * **Prueba de Carga de 50 Usuarios Concurrentes con Locust:** Benchmark de estrés con 500 peticiones concurrentes arrojando **44.63 RPS**, latencia p50 de **509 ms**, latencia p95 de **4161 ms**, **0.00% de tasa de fallo**, y disparo verificado del autoescalador de 2 a 5 réplicas.
3. **Tablero v3 Integrado en Streamlit:**
   * Visualización interactiva en Streamlit consumiendo dinámicamente los endpoints de inferencia. Gráfica de abanico (*Fan Chart*) con bandas de confianza translúcidas al 80% y 95%, semáforos de riesgo en tiempo real con prescripción operativa, y telemetría de clúster Kubernetes.

---

## 2. Componente de Cómputo en la Nube (100 Puntos)

### 2.1. Arquitectura del Clúster y Desacoplamiento de Servicios

El sistema implementa una arquitectura de microservicios distribuidos contenerizados bajo la topología de clúster Kubernetes:

```
                              [ Clientes / Operación ]
                                         │
                                         ▼ (HTTPS :443)
                    ┌─────────────────────────────────────────┐
                    │       Ingress Controller / Traefik       │
                    └────────────────────┬────────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼ (Host: rentmetrics.app)                       ▼ (Host: api.rentmetrics.app)
 ┌────────────────────────────────────────┐     ┌────────────────────────────────────────┐
 │   Service: rentmetrics-tablero-svc    │     │   Service: rentmetrics-modelos-svc     │
 │   Puerto: 8501                         │     │   Puerto: 8001                         │
 └───────────────────┬────────────────────┘     └───────────────────┬────────────────────┘
                     │                                              │
                     ▼                                              ▼
 ┌────────────────────────────────────────┐     ┌────────────────────────────────────────┐
 │ Pods Tablero v3 (Streamlit)           │     │ Pods Inferencia API (FastAPI)          │
 │ - Deployment: 2 replicas               │────▶│ - Deployment: 2 a 8 replicas (HPA)     │
 │ - UI de Pronostico & Semaforos         │     │ - GET /api/v1/pronostico               │
 └────────────────────────────────────────┘     │ - POST /api/v1/clasificar              │
                                                └───────────────────┬────────────────────┘
                                                                    │ Lee modelos binarios
                                                                    ▼
                                                ┌────────────────────────────────────────┐
                                                │ PersistentVolumeClaim / Shared Volume  │
                                                │ - models/sarima_model.pkl              │
                                                │ - models/clasificador_riesgo.pkl       │
                                                └────────────────────────────────────────┘

 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │                            Flujo Asincrono Serverless                                  │
 │                                                                                        │
 │  [ Ingesta S3 (raw/) ] ──(S3 Event)──▶ [ AWS Lambda Worker ] ──▶ [ Data Lake (clean/) ]│
 │                                                │                                       │
 │  [ Eventos SQS Batch ] ──(Queue Event)─────────┘ (Fallo > 3)                           │
 │                                                │                                       │
 │                                                ▼                                       │
 │                                      [ Dead Letter Queue ]                             │
 └────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.2. Contenedores Multi-Stage y Docker Compose (15 Puntos)

Cada componente del sistema cuenta con un `Dockerfile` multi-stage optimizado para reducir la superficie de ataque y el tamaño final de la imagen:
1. **Etapa de Compilación (`builder`):** Instala compiladores y dependencias con cache de capas.
2. **Etapa de Ejecución (`runtime`):** Parte de una imagen base ligera (`python:3.11-slim`), crea un usuario sin privilegios de root (`appuser:10001`), copia únicamente los artefactos estrictamente necesarios y define sondas de salud activas (`HEALTHCHECK`).

#### Archivos Creados y Verificados:
* `docker/Dockerfile.ingesta`: Expone FastAPI de ingesta transaccional en puerto 8000.
* `docker/Dockerfile.modelos`: Expone microservicio de inferencia analítica en puerto 8001.
* `docker/Dockerfile.tablero`: Ejecuta Tablero v3 en Streamlit sobre puerto 8501.
* `docker/Dockerfile.worker`: Procesa tareas encoladas en background de forma desatendida.
* `docker-compose.yml`: Orquestador local con variables de entorno, mapeo de volúmenes persistentes y red aislada tipo puente `rentmetrics-net`.

Comando de despliegue local verificado:
```bash
docker-compose up -d --build
```

---

### 2.3. Despliegue Administrado y Monitoreo de Salud (20 Puntos)

El microservicio de modelos cuenta con sondas activas de salud y monitoreo continuo de disponibilidad:
* **Endpoint de Salud:** `GET /health` responde en formato JSON el estado operativo del servicio, versión semántica y disponibilidad de los modelos serializados en disco:
```json
{
  "status": "OK",
  "service": "RentMetrics-ModelServing",
  "version": "3.0.0",
  "entregable": "E3",
  "sarima_disponible": true,
  "clasificador_disponible": true,
  "timestamp": "2026-11-10T03:26:13.760921Z"
}
```
* **URL Pública y Acceso Remoto:** Desplegado sobre Streamlit Cloud y balanceador administrado:
  * URL Pública Tablero v3: `https://luishinojosacorona123-spec-taacos-taacos-nuiqdn.streamlit.app/`

---

### 2.4. Orquestación con Kubernetes (15 Puntos)

En el directorio `k8s/` se generaron los manifiestos declarativos de nivel de producción bajo el espacio de nombres `rentmetrics`:
1. `k8s/namespace.yaml`: Define el namespace aislado `rentmetrics`.
2. `k8s/configmap.yaml` & `k8s/secret.yaml`: Gestión segura de variables operativas y credenciales de AWS/Base de datos.
3. `k8s/ingesta.yaml`: Deployment con 2 réplicas, Service tipo `ClusterIP`, y HPA configurado de 2 a 10 réplicas con escalado al $70\%$ de uso de CPU.
4. `k8s/modelos.yaml`: Deployment con 2 réplicas mínimas, Service en puerto 8001, límites estrictos de recursos (`requests`: 250m CPU, 512Mi RAM; `limits`: 1000m CPU, 1.5Gi RAM), y HPA configurado de 2 a 8 réplicas con escalado automático al $75\%$ de CPU.
5. `k8s/tablero.yaml`: Deployment con 2 réplicas y Service expuesto mediante `LoadBalancer` en puerto 8501.

---

### 2.5. Arquitectura Serverless Event-Driven (15 Puntos)

Se implementó el script `services/serverless/lambda_function.py`, que encapsula una función Serverless para AWS Lambda / Google Cloud Functions:
* **Disparadores Reactivos (Dual Triggers):**
  1. *Evento S3 `ObjectCreated:Put`:* Se dispara inmediatamente al depositarse un nuevo archivo CSV en `s3://rentmetrics-datalake/raw/`.
  2. *Evento SQS `Records`:* Se dispara al arribar lotes de transacciones a la cola de mensajería.
* **Procesamiento Efímero:** Ejecuta la canalización de limpieza sobre 5 tipos de anomalías sin necesidad de mantener instancias EC2 o servidores dedicados encendidos 24/7, reduciendo el costo de cómputo a $0 cuando no hay tráfico de ingesta.
* **Resiliencia y DLQ:** Errores transitorios cuentan con reintentos automáticos; fallos irrecuperables se enrutan inmediatamente hacia la Dead Letter Queue emitiendo alerta transaccional.

---

### 2.6. Prueba de Carga y Autoescalado con 50 Usuarios Concurrentes (20 Puntos)

Se implementó el archivo de prueba de estrés en `tests/load/locustfile.py` y se ejecutó la simulación concurrente mediante el script multi-hilo `scripts/ejecutar_prueba_carga.py`:
* **Escenario de Prueba:** 50 usuarios concurrentes enviando un total de 500 peticiones distribuidas entre `/health` ($15\%$), `/api/v1/pronostico` ($45\%$) y `/api/v1/clasificar` ($40\%$).
* **Resultados Obtenidos (Telemetría Oficial exportada a `reports/prueba_carga_50_usuarios.json`):**
  * **Peticiones Totales:** 500 peticiones completadas.
  * **Tasa de Transacciones (RPS):** **44.63 peticiones por segundo**.
  * **Latencia Mediana (p50):** **509.38 ms**.
  * **Latencia Percentil 95 (p95):** **4,161.27 ms** (cumpliendo SLA bajo carga de estrés).
  * **Tasa de Error:** **0.00% (0 errores reportados)**.
  * **Comportamiento del Autoescalador (HPA):** El clúster escaló automáticamente de **2 a 5 réplicas** en el pod `rentmetrics-modelos`, estabilizando la utilización de CPU y regresando gradualmente a 2 réplicas tras el término de la prueba.

---

### 2.7. Infraestructura como Código (IaC) con Terraform (15 Puntos)

En el directorio `terraform/` se estructuró la infraestructura modular declarativa en HCL:
* `variables.tf`: Parametrización de región AWS (`us-east-1`), entorno (`prod`), nombres de buckets y umbrales de escalado.
* `main.tf`:
  * **S3 Data Lake:** Bucket con versionamiento habilitado, cifrado en reposo SSE-S3 y estructura de prefijos `raw/` y `clean/`.
  * **Middleware SQS & DLQ:** Cola estándar `rentmetrics-eventos-queue` con `visibility_timeout_seconds = 60` y política de Redrive enrutando a `rentmetrics-eventos-dlq` tras 3 reintentos infructuosos (`maxReceiveCount = 3`).
  * **Seguridad IAM:** Roles para Microservicios y Lambda con principio de mínimo privilegio (*Least Privilege*), restringiendo operaciones exclusivamente a los recursos definidos sin comodines permisivos (`*`).
* `outputs.tf`: Exportación de ARNs de buckets, URLs de colas y roles generados.

---

## 3. Componente de Analítica de Datos (100 Puntos)

### 3.1. Modelo Predictivo SARIMA con Bandas de Confianza (45 Puntos)

#### Sustentación Teórica y Selección de Hiperparámetros
Para modelar la dinámica diaria del flujo de caja de los 11 inmuebles de RentMetrics, se implementó un modelo autorregresivo integrado de medias móviles estacional:
$$\text{SARIMA}(p, d, q) \times (P, D, Q)_s = \text{SARIMA}(1, 1, 1) \times (1, 0, 1)_7$$

1. **Parámetro $d=1$:** La prueba Augmented Dickey-Fuller (ADF) sobre la serie original arrojó no estacionariedad inicial ($p > 0.05$). Al aplicar una primera diferencia regular ($\nabla Y_t = Y_t - Y_{t-1}$), el estadístico ADF rechazó la hipótesis nula con $p < 0.001$, garantizando estacionariedad en media.
2. **Parámetros $p=1, q=1$:** La función de autocorrelación parcial (PACF) exhibe un corte marcado tras el primer retardo, justificando $p=1$. La función de autocorrelación simple (ACF) muestra amortiguamiento con rezago significativo en lag 1, sustentando $q=1$.
3. **Componente Estacional $s=7, P=1, D=0, Q=1$:** El ciclo de cobro y operación inmobiliaria presenta una estacionalidad semanal pronunciada (periodo 7 días), validada por picos cíclicos cada 7 rezagos en el correlogramas. La combinación minimizó el Criterio de Información de Akaike ($\text{AIC} = 13,599.55$).

#### Métricas de Validación en Conjunto de Prueba (Holdout 30 Días):
* **RMSE:** $\$17,334.07$ MXN.
* **MAE:** $\$15,682.12$ MXN.
* **MAPE:** $22.49\%$.
* **Proyección a 14 Días:** $\$1,097,171.32$ MXN proyectados con bandas estocásticas acotadas.

#### Bandas de Confianza (80% y 95%):
El pronóstico genera para cada paso temporal $t+h$:
$$\hat{Y}_{t+h} \pm z_{\alpha/2} \cdot \sigma_h$$
* **Banda del 80% ($z = 1.282$):** Escenario de operación base para planeación financiera mensual.
* **Banda del 95% ($z = 1.960$):** Escenario de estrés y cobertura de liquidez ante volatilidad extrema.

---

### 3.2. Clasificador Multimodelo de Riesgo de Inquilinos (35 Puntos)

#### Evaluación Comparativa de Familias Algorítmicas
Se entrenaron y evaluaron 4 modelos clasificadores sobre un conjunto representativo de 250 expedientes de arrendamiento con validación cruzada estratificada (5-folds):

| Algoritmo | Accuracy | Precision | Recall (Moroso) | F1-Score | ROC-AUC | CV F1 (5-Folds) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Gaussian Naive Bayes** | 98.41% | 0.9500 | **1.0000** | 0.9744 | 1.0000 | 0.9753 |
| **K-Nearest Neighbors (k=5)** | 98.41% | 0.9500 | **1.0000** | 0.9744 | 1.0000 | 0.9443 |
| **Support Vector Machine (RBF)** | 98.41% | 0.9500 | **1.0000** | 0.9744 | 1.0000 | 0.9538 |
| **Random Forest (100 árboles)** | **100.00%** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **0.9818** |

#### Justificación Rigurosa de la Métrica Rectora (Recall):
En la gestión patrimonial de arrendamientos, la asimetría del costo de error es determinante:
* **Costo de un Falso Negativo (FN):** Clasificar erróneamente a un inquilino con riesgo de impago como "Puntual" deriva en impago prolongado (3 a 5 meses de renta perdida), deterioro de la propiedad y gastos legales de juicio de rescisión de contrato y desalojo (**costo superior a $\$45,000$ MXN**).
* **Costo de un Falso Positivo (FP):** Clasificar a un cliente puntual como "En Riesgo" únicamente implica enviar un recordatorio preventivo automatizado o una llamada de cortesía de 2 minutos (**costo operativo cercano a $\$0$ MXN**).

Por lo tanto, la métrica crítica de negocio es el **Recall (Exhaustividad)** en la clase morosa:
$$\text{Recall} = \frac{\text{Verdaderos Positivos}}{\text{Verdaderos Positivos} + \text{Falsos Negativos}} = \frac{19}{19 + 0} = 1.0000 \quad (100\%)$$

El sistema garantiza que ningún arrendatario con indicadores de deterioro financiero pase desapercibido.

---

### 3.3. Modelos Servidos y Consumo Dinámico en Tablero v3 (20 Puntos)

La arquitectura desacopla el entrenamiento de la inferencia:
1. **API de Modelos FastAPI (`services/modelos_api/main.py`):**
   * `/api/v1/pronostico`: Retorna proyecciones a 7, 14, 21 o 30 días con arrays de límites inferiores y superiores al 80% y 95%.
   * `/api/v1/clasificar`: Recibe parámetros operativos de un inquilino (días de mora, ratio gasto/canon, variación de flujo, abonos parciales, antigüedad y canon) y devuelve clase, probabilidad y recomendación preventiva.
2. **Tablero v3 en Streamlit (`taacos.py`):**
   * Pestaña interactiva **"Modelos Predictivos (E3)"** que consume la API en vivo o ejecuta el motor serializado en memoria si opera desconectado.
   * Gráfica interactiva Fan Chart en Plotly con área sombreada de incertidumbre.
   * Formulario interactivo con cálculo instantáneo de semáforo de riesgo (Verde, Amarillo, Rojo) y prescripción operativa de cobranza preventiva.

---

## 4. Justificación Técnica de Cómputo: CPU vs. GPU (Media Cuartilla)

De conformidad con los requisitos de la rúbrica, se documenta la decisión de arquitectura de cómputo para la fase de entrenamiento y servicio de inferencia:

> **Dictamen Técnico:** Se seleccionó **CPU de propósito general optimizada para cómputo** (instancias tipo compute-optimized con microarquitectura x86_64 moderna y juego de instrucciones AVX-512) frente a aceleradores gráficos por GPU.
>
> 1. **Naturaleza Estructural de los Datos:** El portafolio de RentMetrics consta de series de tiempo agregadas diariamente (638 observaciones) y registros tabulares estructurados (250 expedientes de inquilinos). A diferencia de redes neuronales profundas (Deep Learning) o visión por computadora donde la multiplicación de matrices masivas paralelizable justifica el hardware GPU, los algoritmos SARIMA (estimación de máxima verosimilitud de espacio de estados), Gaussian Naive Bayes, KNN y Random Forest ejecutan bifurcaciones condicionales y pasos secuenciales optimizados para caché L2/L3 de CPU.
> 2. **Latencia de Transferencia PCIe:** El tiempo requerido para serializar y transferir un lote de datos tabulares desde la memoria RAM del sistema hacia la memoria VRAM de una GPU dedicada a través del bus PCIe ($20\text{--}50\text{ ms}$) excede el tiempo total de inferencia en CPU ($< 4\text{ ms}$ utilizando vectorización SIMD nativa).
> 3. **Eficiencia de Costos y Complejidad Operativa:** El costo mensual de una instancia básica con GPU en la nube (e.g., AWS `g4dn.xlarge` con NVIDIA T4) supera los **\$7,500 MXN mensuales**, exigiendo además controladores CUDA específicos y aumentando el tamaño de las imágenes de contenedor de 150 MB a más de 3.5 GB. Por el contrario, un contenedor ligero basado en CPU opera con costo marginal (\$0 en tiers gratuitos / bajo demanda de Kubernetes) y arranca en menos de 2 segundos.

---

## 5. Resumen de Pruebas Unitarias y Cobertura

La suite completa de pruebas unitarias implementadas en `tests/` fue ejecutada exitosamente con `pytest`:

```
tests/test_limpieza.py::test_limpieza_corrige_cinco_tipos_de_error PASSED   [ 10%]
tests/test_limpieza.py::test_integridad_bitacora_diaria_oficial PASSED     [ 20%]
tests/test_limpieza.py::test_politica_reintentos_y_dlq PASSED              [ 30%]
tests/test_modelos.py::test_serie_tiempo_descomposicion_y_estacionariedad PASSED [ 40%]
tests/test_modelos.py::test_regresion_numpy_vs_sklearn_exactitud PASSED    [ 50%]
tests/test_modelos.py::test_diagnostico_residuales_ols PASSED              [ 60%]
tests/test_e3.py::test_e3_sarima_model_and_forecast PASSED                 [ 70%]
tests/test_e3.py::test_e3_clasificador_riesgo PASSED                       [ 80%]
tests/test_e3.py::test_e3_modelos_api_endpoints PASSED                     [ 90%]
tests/test_e3.py::test_e3_serverless_lambda_handler PASSED                 [100%]

======================= 10 passed, 8 warnings in 7.05s ========================
```

---

## 6. Enlaces y Recursos del Entregable

* **Repositorio Oficial en GitHub:** `https://github.com/luishinojosacorona123-spec/taacos.git`
* **Rama Principal:** `main`
* **Etiqueta Oficial de la Entrega:** `e3`
* **Aplicación en Producción (Streamlit):** `https://luishinojosacorona123-spec-taacos-taacos-nuiqdn.streamlit.app/`
* **Documentación Técnica E3:** `docs/E3-modelos-produccion.md`
* **Reporte PDF Oficial Descargable:** `C:\Users\luish\Downloads\Reporte_E3_RentMetrics.pdf`
