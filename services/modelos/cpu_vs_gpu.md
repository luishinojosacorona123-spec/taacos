# Justificación Técnica de Cómputo para Entrenamiento: CPU vs. GPU

**Proyecto:** DATA STARTUP · RentMetrics  
**Entregable:** E3 · Inteligencia en Producción  
**Autor:** Manuel Alexander Hernández Chávez (*Data Lead*)  

---

### 1. Dimensionamiento del Dataset y Carga Computacional
En RentMetrics, el volumen de datos operado en el Entregable E3 comprende:
* **Serie Temporal:** 7,018 registros de bitácora diaria consolidados en 638 puntos de datos continuos (21 meses) para el modelo SARIMA$(1, 1, 1) \times (1, 0, 1)_7$.
* **Clasificador Tabular de Morosidad:** Matriz estructurada de $250 \times 6$ variables operativas para la comparativa de 4 familias de modelos (Gaussian Naive Bayes, KNN, SVM y Random Forest).

### 2. Análisis Comparativo: Arquitectura CPU vs. GPU

| Dimensión Técnica | Procesador Central (CPU - AMD/Intel x86_64 o ARM Graviton) | Procesador Gráfico (GPU - NVIDIA Tensor Core / CUDA) |
| :--- | :--- | :--- |
| **Tiempo de Entrenamiento** | **6.8 segundos** (entrenamiento completo de SARIMA y 4 clasificadores con validación cruzada). | **Estimado 18–35 segundos** (la sobrecarga de inicialización del runtime CUDA y la copia de tensores superan el cómputo útil). |
| **Cuello de Botella E/S** | Cero latencia de bus. Los datos residen en memoria RAM unificada y aprovechan registros vectoriales SIMD (AVX2/AVX-512). | Latencia de transferencia Host-to-Device a través del bus PCIe (Gen 3/4) para datasets pequeños (&lt; 50 MB). |
| **Soporte Algorítmico** | Nativo y altamente optimizado en `statsmodels` y `scikit-learn` (solvers LAPACK/BLAS multihilo en C/Fortran). | Parcial. Modelos clásicos como SARIMA (filtro de Kalman recursivo) no son masivamente paralelizables por su naturaleza secuencial $t-1 \rightarrow t$. |
| **Consumo de Memoria** | &lt; 280 MB de memoria de trabajo, ejecutable en instancias básicas de 1 vCPU / 1 GB RAM. | Asignación mínima de VRAM de 2 a 4 GB solo para el contexto de CUDA, desperdiciando el 95% de la capacidad. |
| **Costo en Nube** | **$0.00 MXN / mes** (Elegible 100% dentro de la capa gratuita de AWS, Google Cloud Run o Azure Container Apps). | **$7,500 – $11,000 MXN / mes** (Instancias mínimas tipo `g4dn.xlarge` en AWS con costo de ~$0.526 USD/hora). |

### 3. Conclusión y Decisión de Ingeniería
Para la escala y naturaleza matemática de los modelos de RentMetrics (filtros recursivos de series de tiempo y clasificadores tabulares basados en particionamiento de hiperplanos y árboles), **la CPU es la opción técnica superior en velocidad, eficiencia energética y viabilidad financiera**. La GPU se reservará exclusivamente para la Unidad 4 (Entregable E4), donde se incorporarán redes neuronales recurrentes profundas (LSTM / GRU) que sí se benefician del paralelismo masivo de operaciones matriciales tensoriales.
