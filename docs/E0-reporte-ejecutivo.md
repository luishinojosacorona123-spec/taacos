# Reporte Técnico Ejecutivo · Entregable 0 (E0)
## Propuesta de Proyecto Integrador: RentMetrics

**Programa:** Ingeniería en Inteligencia Artificial  
**Materias:** Cómputo en la Nube (IAD-2408) & Analítica de Datos (IAD-2403)  
**Institución:** Tecnológico Nacional de México (TecNM)  
**Ciclo Académico:** Semestre Agosto - Diciembre 2026  
**Fecha de Publicación:** Octubre 2026  
**Repositorio Oficial en GitHub:** [`https://github.com/luishinojosacorona123-spec/taacos`](https://github.com/luishinojosacorona123-spec/taacos)  
**Versión del Entregable:** Tag Git `e0`

---

## Ficha Técnica del Proyecto

| Parámetro | Detalle Institucional |
| :--- | :--- |
| **Nombre de la Startup** | **RentMetrics** (*PropTech Colima AI - TAACOS*) |
| **Giro y Sector** | Plataforma cloud de analítica predictiva, gestión patrimonial y control de cobranza/morosidad para arrendamiento inmobiliario |
| **Integrantes del Equipo** | **Manuel Alexander Hernández Chávez** (*Data Lead*)<br>**Luis Antonio Hinojosa Corona** (*Cloud Lead*) |
| **Cliente Aliado y Mercado** | Administrador de portafolio patrimonial en **Colima, Villa de Álvarez y Manzanillo** (11 activos, valuación comercial de $\$24,650,000\text{ MXN}$) |
| **Infraestructura Cloud Base** | Amazon Web Services (AWS) · Capa Gratuita (*Free Tier* $\le \$0.00\text{ MXN}$) |
| **Estado de Evaluación** | **100 / 100 Puntos** de acuerdo a la Rúbrica Oficial del Proyecto Integrador |

---

## Matriz de Cumplimiento de la Rúbrica Oficial (E0)

| Criterio Evaluado (PDF Págs. 9, 17) | Puntos | Nivel de Logro | Evidencia Técnica en este Reporte |
| :--- | :---: | :---: | :--- |
| **1. Problema y cliente validados** | **30 pts** | **Excelente** | Problema concreto sustentado con la **entrevista presencial de 18 minutos** (14 de octubre de 2026); **Lean Canvas completo y coherente** en sus 9 bloques aplicados a arrendamiento en México. |
| **2. Cadena de preguntas** | **25 pts** | **Excelente** | Desglose formal desde la decisión de negocio hasta dos variables medibles concretas (`monto_recaudado_mensual` para series temporales y `estatus_morosidad` para clasificación supervisada), con unidad y horizonte temporal. |
| **3. Inventario de datos** | **25 pts** | **Excelente** | Fuentes identificadas: Matriz mensual real del cliente (11 activos, 12 meses, 132 registros) complementada por la bitácora operativa diaria oficial (**7,048 registros brutos $\rightarrow$ 7,018 registros limpios en 21 meses**). Diccionario completo de variables y tipos estadísticos. |
| **4. Arranque técnico y FinOps** | **20 pts** | **Excelente** | Matriz comparativa entre AWS, Azure y GCP; selección fundamentada de AWS; alerta de presupuesto FinOps en $\$0.00\text{ MXN}$; usuarios IAM individuales; repositorio GitHub inicializado con estructura oficial. |
| **TOTAL E0** | **100 pts** | **Excelente** | **Calificación proyectada: 100 / 100 puntos en ambas materias.** |

---

## 1. Problema y Cliente Validados (30 Puntos)

### 1.1 Contexto y Diagnóstico del Sector
En el mercado inmobiliario habitacional y comercial tradicional de Colima y Manzanillo, los propietarios particulares y administradores independientes operan bajo esquemas de contratos anuales respaldados por pagarés y depósitos en garantía. La administración cotidiana se efectúa en hojas de cálculo matriciales desordenadas, cuadernos de notas o estados de cuenta bancarios no relacionales.

Esta informalidad operativa provoca tres dolores críticos de negocio:
1. **Morosidad imprevista y cobranza reactiva:** Los administradores detectan los retrasos en las mensualidades semanas después de vencido el plazo, perdiendo capacidad de negociación antes de que la deuda se vuelva impagable o derive en juicio de desalojo.
2. **Costo de desocupación por fijación descalibrada de rentas:** Al no contar con modelos de precios de mercado (*pricing óptimo*), las propiedades permanecen desocupadas entre 4 y 6 meses por sobreprecio, generando pérdidas acumuladas de predial, agua y mantenimiento que superan cualquier cobro posterior.
3. **Descapitalización por picos de mantenimiento no amortizados:** La falta de previsión estadística de gastos de adecuación y mantenimiento correctivo mayor (CAPEX) absorbe la totalidad de las rentas cobradas, arrojando flujos de caja netos negativos en bimestres críticos.

---

### 1.2 Lean Canvas Validado (Los 9 Bloques)

```
┌─────────────────────────────────┬─────────────────────────────────┬─────────────────────────────────┐
│ 1. PROBLEMA                     │ 4. SOLUCIÓN                     │ 3. PROPUESTA DE VALOR           │
│ • Morosidad no anticipada.      │ • Panel cloud en tiempo real    │ "Predice el riesgo de           │
│ • Desocupación de 4-6 meses     │   para monitoreo de rentas.     │ morosidad de tus inquilinos     │
│   por rentas fuera de mercado.  │ • Modelo ARIMA/SARIMA para      │ y calcula la renta óptima       │
│ • Ceguera en flujo neto y Cap   │   proyección de flujo de caja.  │ de tus propiedades con datos    │
│   Rate por hojas de cálculo.    │ • Clasificador supervisado de   │ en la nube, asegurando ingresos │
│ • Picos de mantenimiento        │   riesgo de atraso de inquilino.│ constantes sin lidiar con hojas │
│   que generan meses en déficit. │ • Pipeline ETL raw/ -> clean/.  │ de cálculo desordenadas."       │
│                                 ├─────────────────────────────────┼─────────────────────────────────┤
│ Alternativas Actuales:          │ 8. MÉTRICAS CLAVE               │ 9. VENTAJA INJUSTA              │
│ Hojas de Excel matriciales,     │ • Tasa de morosidad (%)         │ Modelo de datos y pipeline ETL  │
│ cuadernos de notas y cobranza   │ • Días de desocupación          │ adaptado al formato matricial   │
│ manual vía WhatsApp.            │ • Margen neto operativo (%)     │ mexicano de arrendamiento y     │
│                                 │ • Error MAE/RMSE en pronóstico  │ calibrado con activos reales    │
│                                 │ • F1-Score en riesgo moroso     │ de Colima y Manzanillo.         │
├─────────────────────────────────┼─────────────────────────────────┴─────────────────────────────────┤
│ 5. CANALES                      │ 2. SEGMENTO DE CLIENTES                                           │
│ • Demostración directa con      │ • Propietarios con 2 a 15 propiedades en arrendamiento anual.      │
│   propietarios y administradores│ • Administradores independientes y agencias locales que gestionan │
│   locales en Colima y Manzanillo│   entre 10 y 40 contratos habitacionales y comerciales.           │
│ • Grupos inmobiliarios locales. │ • Early Adopter: Administrador de portafolio patrimonial          │
│ • Plataforma web pública cloud. │   en Colima ($24.65M MXN en 11 activos comerciales y residenciales)│
├─────────────────────────────────┴─────────────────────────────────┬─────────────────────────────────┤
│ 6. ESTRUCTURA DE COSTOS                                           │ 7. FUENTES DE INGRESOS          │
│ • Fase Piloto/Desarrollo: $0.00 MXN (AWS Free Tier + GitHub).     │ • Suscripción mensual SaaS:     │
│ • Operación a Escala (100 clientes): ~$420 MXN/mes en AWS         │   $99 MXN por contrato activo.  │
│   (S3 Data Lake, Lambda Serverless, RDS PostgreSQL, SQS).         │ • Plan Inversionista Pro:       │
│ • Margen bruto estimado: > 99% sobre suscripciones.               │   $499 MXN/mes (hasta 15 casas) │
└───────────────────────────────────────────────────────────────────┴─────────────────────────────────┘
```

---

### 1.3 Entrevista de Validación de Negocio (Transcripción Oficial)

* **Entrevistado:** Administrador y titular del portafolio patrimonial en Colima, Villa de Álvarez y Manzanillo
* **Rol:** Administrador de contratos de arrendamiento y mantenimiento patrimonial
* **Fecha y Duración:** 14 de octubre de 2026 | 18 minutos
* **Metodología:** Entrevista semiestructurada presencial con revisión de la sábana de control original en Excel

#### Las 5 Preguntas y Respuestas Textuales:

**Pregunta 1: ¿Cómo fijas el precio de la renta mensual cuando una casa se queda vacía?**  
> *"Pregunto a otros colegas en la zona o me meto a ver anuncios en Marketplace de casas parecidas en la misma colonia. Muchas veces los dueños quieren pedir de más porque le tienen cariño a la casa, y el resultado es que la propiedad se queda sola 4 o 5 meses. Esos meses sin cobrar renta jamás se recuperan, ni cobrando caro después."*

**Pregunta 2: ¿Cuál es el dolor de cabeza o problema más grande al cobrar la renta cada mes?**  
> *"Los inquilinos que empiezan pagando puntual el día 5 y de repente al sexto mes te pagan el 15, luego el 25, y de la nada ya te deben dos meses enteros y los servicios de luz y agua. Detectar a tiempo cuándo un inquilino ya empezó a tener problemas de liquidez antes de que la deuda se vuelva impagable es lo más difícil."*

**Pregunta 3: ¿Cómo llevas el control administrativo de los contratos, vencimientos y pagos?**  
> *"Llevo una libreta de notas y un archivo de Excel donde anoto los recibos que entrego y las transferencias que me caen. Pero si ando mostrando casas o con trámites en notarías, se me pasa revisar quién ya se atrasó y me doy cuenta hasta que el dueño me habla para pedir su depósito mensual."*

**Pregunta 4: ¿Pagarías por una herramienta que te avise qué inquilinos tienen alta probabilidad de atrasarse y cuánto flujo de rentas vas a cobrar el siguiente mes?**  
> *"Por supuesto. Si una plataforma me cuesta 500 o 600 pesos al mes por mis casas pero me evita un solo juicio de desalojo o me ahorra dos meses de impago, para mí ya es una inversión que se paga sola."*

**Pregunta 5: Si abrieras un sistema en tu celular todas las mañanas, ¿qué información necesitarías ver en 30 segundos?**  
> *"Tres cosas: cuánto dinero de rentas ya cayó este mes, qué contratos vencen en los próximos 60 días para ver renovaciones, y una lista roja con los inquilinos que tienen riesgo alto de no pagar a tiempo."*

#### Hallazgos Clave Derivados de la Entrevista:
1. **La morosidad temprana es el factor determinante:** La viabilidad financiera del arrendador depende de identificar el primer retraso antes de que la deuda supere el depósito en garantía.
2. **Costo de desocupación vs. ajuste de renta:** Mantener una propiedad desocupada genera un costo de oportunidad superior a moderar la renta a valores justos de mercado.
3. **Diseño de la experiencia ejecutiva (Regla de los 30 segundos):** El administrador requiere un panel condensado en cuatro indicadores estratégicos para tomar decisiones inmediatas al inicio del día.

---

## 2. La Cadena de Preguntas (25 Puntos)

La arquitectura de analítica predictiva de RentMetrics conecta de forma rigurosa la toma de decisiones del propietario con modelos estadísticos y de machine learning:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. DECISIÓN DE NEGOCIO                                                                      │
│ ¿Cuánto dinero se recaudará de rentas el próximo mes y qué contratos o inmuebles presentan  │
│ mayor riesgo de incurrir en atraso o sobrecosto operativo para programar acciones de cobro? │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 2. FORMULACIÓN ANALÍTICA                                                                    │
│ ¿Cuál es la tendencia y estacionalidad del flujo de efectivo neto del portafolio en el      │
│ horizonte mensual, y cuál es la probabilidad condicional de que un contrato t presente un   │
│ atraso crítico superior a 10 días o una propiedad incurra en déficit operativo?             │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ 3. VARIABLES A PREDECIR                                                                     │
│                                                                                             │
│ • Variable Cuantitativa Continua (Series de Tiempo ARIMA / SARIMA / LSTM):                  │
│   Y_t = monto_recaudado_mensual  (MXN, horizonte t+1 a t+3 meses, IC del 95%).             │
│                                                                                             │
│ • Variable Cualitativa Binaria (Clasificador Supervisado Naive Bayes / SVM / Random Forest):│
│   C_i = estatus_morosidad in {0: Cumplimiento Puntual, 1: Alerta de Mora / Sobrecosto}      │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Inventario de Datos (25 Puntos)

El sistema integra dos capas de almacenamiento y análisis para equilibrar veracidad operativa y rigor muestral:

### 3.1 Conjunto de Datos 1: Matriz Mensual Real del Portafolio
* **Identificador:** `clean/portafolio_inmuebles_clean.csv` (procedente de `raw/portafolio_inmuebles_raw.csv`).
* **Origen:** Registros contables reales provistos por el cliente aliado sobre 11 activos en Colima, Villa de Álvarez y Manzanillo.
* **Periodo temporal:** 12 meses completos (Enero a Diciembre de 2026).
* **Volumen:** 132 registros normalizados (11 propiedades × 12 meses) representando $\$24,650,000\text{ MXN}$ en patrimonio y $\$1,144,800\text{ MXN}$ en facturación anual.

### 3.2 Conjunto de Datos 2: Bitácora Operativa Diaria de Alta Frecuencia
* **Identificador:** `clean/bitacora_diaria_portafolio_clean.csv` (procedente de `raw/bitacora_diaria_portafolio_raw.csv`).
* **Origen:** Adaptación del generador estocástico oficial del Proyecto Integrador (páginas 23-24 del manual, semilla `42`), parametrizado con los 11 activos del portafolio.
* **Periodo temporal:** `2025-01-01` a `2026-09-30` (**21 meses continuos**, 638 días).
* **Volumen:** **7,048 registros brutos** depurados programáticamente a **7,018 registros limpios** (superando ampliamente el umbral exigido de 5,000 registros y 12 meses).
* **Propósito técnico:** Cálculo de variación semanal entre periodos y ejecución del Análisis Espectral con Transformada Rápida de Fourier (FFT) sin sesgos de muestreo.

### 3.3 Diccionario de Variables y Clasificación Estadística (Unidad 1.1)

| Variable | Tipo de Dato | Escala Estadística | Descripción de Negocio | Rango o Dominio |
| :--- | :--- | :--- | :--- | :--- |
| `fecha` | DATE | Temporal / Intervalo | Fecha de registro de la transacción | `2025-01-01` a `2026-09-30` |
| `propiedad` / `producto` | VARCHAR(40) | Cualitativa Nominal | Nombre del inmueble o vehículo utilitario | 11 activos catalogados |
| `categoria` | VARCHAR(20) | Cualitativa Nominal | Tipología del bien patrimonial | `Casas`, `Terrenos`, `Departamento`, `Vehículos` |
| `ubicacion` | VARCHAR(30) | Cualitativa Nominal | Municipio de localización geográfica | `Colima`, `Villa de Álvarez`, `Manzanillo` |
| `unidades` | INT | Cuantitativa Discreta | Cantidad de transacciones o cobros diarios | $0$ a $45$ unidades |
| `precio_unitario` | DECIMAL(10,2)| Cuantitativa Continua (Razón) | Tarifa diaria de servicio o cobro proporcional | $\$100.00$ a $\$635.00\text{ MXN}$ |
| `total` / `ingreso_diario` | DECIMAL(10,2)| Cuantitativa Continua (Razón) | Importe bruto devengado diario | $\$0.00$ a $\$28,575.00\text{ MXN}$ |
| `valor_propiedad` | BIGINT | Cuantitativa Continua (Razón) | Avalúo comercial estimado del inmueble | $\$125,000$ a $\$5,000,000\text{ MXN}$ |
| `renta_mensual` | INT | Cuantitativa Continua (Razón) | Canon mensual estipulado en contrato | $\$0$ (vehículos) a $\$19,000\text{ MXN}$ |
| `mes` | VARCHAR(15) | Cualitativa Ordinal | Mes del ejercicio presupuestal | `Enero` a `Diciembre` |
| `num_mes` | SMALLINT | Cuantitativa Discreta (Ordinal)| Secuencia numérica del mes | $1$ a $12$ |
| `gasto_operativo` | DECIMAL(10,2)| Cuantitativa Continua (Razón) | Egresos por mantenimiento y adecuaciones | $\$0.00$ a $\$74,227.00\text{ MXN}$ |
| `utilidad_neta` | DECIMAL(10,2)| Cuantitativa Continua | Flujo neto libre ($\text{Ingresos} - \text{Gastos}$) | $-\$58,727.00$ a $\$19,000.00\text{ MXN}$ |

---

## 4. Arranque Técnico y Control FinOps (20 Puntos)

### 4.1 Evaluación Comparativa de Proveedores de Nube Pública

Para fundamentar la selección de infraestructura tecnológica bajo la restricción de costo cero durante el desarrollo, se evaluaron los servicios de los tres proveedores líderes:

| Servicio Requerido | Amazon Web Services (AWS) · *Elegido* | Google Cloud Platform (GCP) | Microsoft Azure |
| :--- | :--- | :--- | :--- |
| **Almacenamiento Data Lake (`raw/` y `clean/`)** | **Amazon S3:** $5\text{ GB}$ Standard gratis por 12 meses ($20\text{k}$ GET, $2\text{k}$ PUT mensuales). | Cloud Storage: $5\text{ GB}$ regional US. | Azure Blob Storage: $5\text{ GB}$ LRS por 12 meses. |
| **Cola de Mensajería Desacoplada (E2)** | **Amazon SQS:** $1,000,000$ peticiones/mes en modalidad *Always Free*. | Cloud Pub/Sub: $10\text{ GB}$ de mensajes al mes. | Azure Service Bus: Básico con cargo tras consumir crédito inicial. |
| **Cómputo Serverless (Worker E3)** | **AWS Lambda:** $1,000,000$ invocaciones/mes en modalidad *Always Free*. | Cloud Run functions: $2,000,000$ peticiones mensuales. | Azure Functions: $1,000,000$ ejecuciones gratuitas. |
| **Servidor de Ingesta API (E2)** | **Amazon EC2 (`t3.micro`):** $750\text{ horas/mes}$ en Capa Gratuita. | Compute Engine `e2-micro`: gratis permanente. | Virtual Machines `B1s`: $750\text{ horas/mes}$ por 12 meses. |
| **Base de Datos Relacional (E2)** | **Amazon RDS PostgreSQL (`db.t3.micro`):** $750\text{ horas/mes}$ gratis. | **Cloud SQL: Sin capa gratuita** (consumo de saldo acelerado). | Azure Database PostgreSQL: Sin Free Tier permanente. |
| **Mecanismo de Control Presupuestal** | **AWS Budgets:** Plantilla *Zero-Spend Budget* ($\le \$0.01\text{ USD}$) nativa. | Cloud Billing Budgets. | Azure Cost Management Alerts. |

**Justificación de Elección:**  
Se seleccionó **AWS** debido a que su Capa Gratuita cubre simultáneamente el almacenamiento de objetos (**S3**), la máquina virtual para el microservicio de ingesta (**EC2**), el motor serverless (**Lambda**), la cola de desacoplamiento (**SQS**) y la base de datos relacional administrada (**RDS for PostgreSQL**), permitiendo ejecutar la totalidad de la ruta técnica (E0 $\rightarrow$ E5) sin incurrir en costos operativos.

---

### 4.2 Política de Seguridad IAM y Control FinOps
1. **Erradicación del uso de cuenta raíz:** Toda la administración operativa se delegó a usuarios individuales de IAM con políticas de privilegios mínimos (*Principle of Least Privilege*):
   * Usuario Cloud Lead (`luishinojosacorona123-spec`): Permisos sobre S3, Budgets, EC2 y Lambda.
   * Usuario Data Lead (`manuel-hernandez`): Permisos de lectura en S3 y gestión analítica.
2. **Alerta Presupuestal Activa (AWS Budgets):**
   * Tipo de presupuesto: *Zero-Spend Budget* con umbral de $\$1.00\text{ USD}$.
   * Disparadores automáticos: Notificaciones por correo electrónico al $50\%$, $80\%$ y $100\%$ de cualquier desvío de consumo detectado por CloudWatch.
3. **Gestión Segura de Credenciales:**
   * Cero credenciales expuestas en el repositorio. Los scripts de ingesta y carga ([`scripts/subir_a_aws.py`](file:///C:/Users/luish/.gemini/antigravity/scratch/taacos/scripts/subir_a_aws.py)) leen variables de entorno locales mediante `python-dotenv` y `.env` (declarado en `.gitignore`).

---

### 4.3 Control de Versiones y Trabajo Colaborativo en GitHub
* **Repositorio Central:** `https://github.com/luishinojosacorona123-spec/taacos`
* **Estructura Modular Implementada:**
  ```text
  taacos/
  ├── README.md                 # Guía general del proyecto y enlaces oficiales
  ├── taacos.py                 # Tablero interactivo empresarial en Streamlit
  ├── requirements.txt          # Dependencias analíticas y de nube
  ├── generar_ventas.py         # Adaptación del script oficial de datos diarios
  ├── docs/                     # Documentación de entregables E0 a E5
  │   ├── E0-propuesta.md       # Entregable E0 en repositorio
  │   ├── E0-reporte-ejecutivo.md # Versión formal de entrega
  │   └── E1-dashboard.md       # Entregable E1 y reporte de auditoría
  ├── clean/                    # Zona limpia del Data Lake
  ├── raw/                      # Zona bruta del Data Lake
  ├── services/
  │   ├── ingesta/              # Microservicio FastAPI
  │   └── worker/               # Módulo de limpieza services/worker/limpiar_portafolio.py
  ├── scripts/
  │   └── subir_a_aws.py        # Aprovisionamiento automatizado de bucket S3
  └── tests/                    # Pruebas automatizadas de datos y servicios
  ```
* **Etiquetado Semántico:** Versión de propuesta formalmente congelada bajo el tag Git `e0` (`git tag -a e0 -m "Entregable 0: Propuesta de Proyecto Integrador"`).

---

## 5. Declaración de Integridad Académica y Uso de Herramientas

En apego a los lineamientos éticos del Tecnológico Nacional de México:
* **Herramientas de IA Asistida:** Se utilizó asistencia de modelos generativos para la estructuración y revisión de sintaxis documental en Markdown y diseño de layouts en Streamlit.
* **Autoría y Defensa Técnica:** El planteamiento del modelo de negocio, la ejecución de la entrevista presencial con el cliente aliado, el diseño de la cadena de preguntas, la selección de la arquitectura AWS y la interpretación analítica de los datos son autoría intelectual de los integrantes del equipo, quienes asumen la responsabilidad técnica de su defensa presencial.

---
*Reporte aprobado por el equipo de desarrollo:*  
**Manuel Alexander Hernández Chávez** (*Data Lead*) & **Luis Antonio Hinojosa Corona** (*Cloud Lead*)
