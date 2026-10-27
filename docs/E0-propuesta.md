# E0: Propuesta de Proyecto Integrador - Data Startup

**Nombre de la Startup:** RentMetrics (PropTech Colima AI - TAACOS)  
**Giro:** Plataforma cloud de analítica predictiva, gestión patrimonial y control de cobranza/morosidad para arrendamiento habitacional y comercial a largo plazo  
**Materias:** Cómputo en la Nube (IAD-2408) & Analítica de Datos (IAD-2403)  
**Fecha de Entrega:** Octubre 2026  
**Repositorio Oficial:** [`https://github.com/luishinojosacorona123-spec/taacos`](https://github.com/luishinojosacorona123-spec/taacos)  
**Proveedor Cloud:** Amazon Web Services (AWS)  

**Integrantes del Equipo:**
* **Hernández Chávez Manuel Alexander** — *Data Lead*
* **Hinojosa Corona Luis Antonio** (`@luishinojosacorona123-spec`) — *Cloud Lead*

---

## 1. Lean Canvas (Los 9 Bloques Validados)

| Bloque | Detalle del Negocio (*RentMetrics*) |
| :--- | :--- |
| **1. Problema** | • Los propietarios y administradores de inmuebles en renta tradicional batallan con inquilinos morosos que se atrasan en las mensualidades sin previo aviso.<br>• Dificultad para calcular el precio óptimo del contrato (si cobran de más, la propiedad dura 4 o 6 meses desocupada generando gastos de predial y agua; si cobran de menos, pierden frente a la inflación y el Cap Rate se desploma).<br>• Incertidumbre al renovar contrato: no saben qué inquilinos tienen alta probabilidad de desocupar la casa o caer en impago.<br>• Descontrol contable al registrar ingresos y egresos en hojas de cálculo manuales desestructuradas con celdas vacías y notas informales. |
| **2. Segmento de Clientes** | • Propietarios particulares con 2 a 15 propiedades (casas, locales, departamentos o terrenos) en renta por contrato anual.<br>• Pequeñas agencias inmobiliarias y administradores locales de bienes raíces independientes que gestionan entre 10 y 40 contratos de arrendamiento en Colima, Villa de Álvarez y Manzanillo. |
| **3. Propuesta de Valor Única** | *"Predice el riesgo de morosidad de tus inquilinos y calcula la renta óptima de tus propiedades con datos en la nube, asegurando ingresos constantes sin lidiar con hojas de cálculo desordenadas."* |
| **4. Solución** | • **Panel centralizado en la nube (Streamlit):** Monitoreo en tiempo real del flujo de rentas cobradas, pagos pendientes, gastos operativos y contratos.<br>• **Modelo analítico de series de tiempo (ARIMA/SARIMA):** Proyección del flujo de caja mensual recaudado y gasto operativo esperado considerando estacionalidad.<br>• **Modelo de clasificación supervisada:** Predicción de si un contrato caerá en morosidad el próximo mes basándose en puntualidad histórica y características del inmueble.<br>• **Tubería ETL automatizada:** Limpieza reproducible de sábanas desordenadas de Excel a almacenamiento de objetos en la nube (`raw/` $\rightarrow$ `clean/`). |
| **5. Canales** | • Venta directa y contacto con administradores de propiedades y agentes inmobiliarios locales en Colima y Manzanillo.<br>• Grupos locales de Facebook y redes de profesionistas de bienes raíces y arrendamiento.<br>• Plataforma web pública desplegada en la nube accesible desde navegador móvil o computadora. |
| **6. Estructura de Costos** | • Costo de nube en **$0.00 MXN** durante el desarrollo y validación operando en la Capa Gratuita (AWS Free Tier / GitHub / Streamlit Cloud).<br>• Costos de operación futura a escala: almacenamiento de objetos Data Lake (S3 `raw/` y `clean/`), base de datos relacional (PostgreSQL), colas de mensajería (SQS) y ejecuciones serverless (Lambda).<br>• Dominio web y mantenimiento de software. |
| **7. Fuentes de Ingresos** | • **Suscripción mensual fija (SaaS):** \$99 MXN por contrato o propiedad activa administrada al mes.<br>• **Modelo Freemium:** Panel de control histórico básico sin costo; proyecciones de flujo de efectivo, estimación de Cap Rate y scoring de riesgo de morosidad bajo suscripción de pago (\$499 MXN/mes por portafolio de hasta 15 activos). |
| **8. Métricas Clave (KPIs)** | • Tasa de morosidad (% de mensualidades pagadas fuera de fecha límite).<br>• Días promedio de desocupación entre contratos consecutivos.<br>• Margen neto operativo del portafolio (actualmente $67.1\%$ en el ejercicio anual).<br>• Precisión del pronóstico de ingresos y flujo mensual (MAE, RMSE, $R^2$).<br>• Precisión y Recall del modelo clasificador de riesgo de morosidad (F1-score). |
| **9. Ventaja Injusta** | Enfoque 100% aterrizado a la realidad del arrendamiento habitacional y comercial tradicional en México (contratos a 12 meses, pagarés y depósitos en garantía), integrando una tubería de preprocesamiento de datos reales matriciales de Colima con costo marginal mínimo en la nube frente a ERPs corporativos costosos. |

---

## 2. Entrevista de Validación de Negocio (Entrevista Real)

* **Entrevistado:** Administrador y titular de portafolio de arrendamiento patrimonial en Colima, Villa de Álvarez y Manzanillo
* **Rol:** Administrador de propiedades y contratos de arrendamiento habitacional y comercial
* **Fecha y Duración:** 14 de octubre de 2026 | 18 minutos
* **Modalidad:** Entrevista presencial de validación de problema con revisión de archivo de control en Excel

### Las 5 Preguntas y Respuestas Textuales:

1. **¿Cómo fijas el precio de la renta mensual cuando una casa se queda vacía?**
   > *"Pregunto a otros colegas en la zona o me meto a ver anuncios en Marketplace de casas parecidas en la misma colonia. Muchas veces los dueños quieren pedir de más porque le tienen cariño a la casa, y el resultado es que la propiedad se queda sola 4 o 5 meses. Esos meses sin cobrar renta jamás se recuperan, ni cobrando caro después."*

2. **¿Cuál es el dolor de cabeza o problema más grande al cobrar la renta cada mes?**
   > *"Los inquilinos que empiezan pagando puntual el día 5 y de repente al sexto mes te pagan el 15, luego el 25, y de la nada ya te deben dos meses enteros y los servicios de luz y agua. Detectar a tiempo cuándo un inquilino ya empezó a tener problemas de liquidez antes de que la deuda se vuelva impagable es lo más difícil."*

3. **¿Cómo llevas el control administrativo de los contratos, vencimientos y pagos?**
   > *"Llevo una libreta de notas y un archivo de Excel donde anoto los recibos que entrego y las transferencias que me caen. Pero si ando mostrando casas o con trámites en notarías, se me pasa revisar quién ya se atrasó y me doy cuenta hasta que el dueño me habla para pedir su depósito mensual."*

4. **¿Pagarías por una herramienta que te avise qué inquilinos tienen alta probabilidad de atrasarse y cuánto flujo de rentas vas a cobrar el siguiente mes?**
   > *"Por supuesto. Si una plataforma me cuesta 500 o 600 pesos al mes por mis casas pero me evita un solo juicio de desalojo o me ahorra dos meses de impago, para mí ya es una inversión que se paga sola."*

5. **Si abrieras un sistema en tu celular todas las mañanas, ¿qué información necesitarías ver en 30 segundos?**
   > *"Tres cosas: cuánto dinero de rentas ya cayó este mes, qué contratos vencen en los próximos 60 días para ver renovaciones, y una lista roja con los inquilinos que tienen riesgo alto de no pagar a tiempo."*

### Lo que aprendimos de la entrevista (Hallazgos Clave):

* **La morosidad y la cobranza tardía son el riesgo crítico:** En renta tradicional el problema no es llenar la casa cada fin de semana, sino la estabilidad del pago mes con mes y evitar caer en impagos prolongados o cobranza judicial.
* **Costo de la desocupación y precios descalibrados:** Dejar una casa desocupada por fijar mal la renta genera pérdidas acumuladas mucho mayores que haber ajustado el precio al mercado desde el inicio. El sistema debe correlacionar valor comercial y renta justa.
* **Facilidad de ingesta desde hojas de cálculo existentes:** Los administradores registran pagos mediante transferencias bancarias y recibos en Excel no estructurado; procesar estos datos vía CSV o API y limpiarlos automáticamente en la nube encaja directo con su operación habitual.

---

## 3. La Cadena de Preguntas

Siguiendo la metodología del proyecto para conectar la necesidad del negocio con la formulación analítica y de machine learning:

```
[Pregunta de Negocio (Decisión del Propietario)]
¿Cuánto dinero se va a recaudar por concepto de rentas el próximo mes y qué contratos
tienen mayor riesgo de caer en mora o no renovarse para activar la gestión de cobranza?
                         │
                         ▼
[Pregunta Analítica]
¿Cuál es la tendencia del monto mensual recaudado considerando la estacionalidad de pagos
y cuál es la probabilidad de que un contrato o propiedad presente un atraso o sobrecosto operativo?
                         │
                         ▼
[Variables a Predecir]
1. `monto_recaudado_mensual` / `utilidad_neta` (Variable cuantitativa continua en MXN para pronóstico
   de series de tiempo con ARIMA/SARIMA y regresión lineal por mínimos cuadrados).
2. `estatus_morosidad` / `riesgo_operativo` (Variable cualitativa binaria: 1 = En mora / Alerta de sobrecosto,
   0 = Pago puntual / Operación estable, para el clasificador supervisado Naive Bayes/SVM/Árboles).
```

---

## 4. Inventario de Datos

El proyecto cuenta con dos conjuntos de datos complementarios que garantizan tanto el rigor del caso de negocio real como el volumen estadístico y granularidad temporal exigidos por la rúbrica de evaluación:

### 4.1 Matriz Mensual Real del Portafolio Inmobiliario
* **Fuente:** Archivo real de control operativo y cobranza del administrador (`portafolio_inmuebles.csv` $\rightarrow$ `raw/portafolio_inmuebles_raw.csv` $\rightarrow$ `clean/portafolio_inmuebles_clean.csv`).
* **Periodo:** 12 meses completos (Enero a Diciembre 2026, con 10 meses observados y 2 proyectados).
* **Volumen:** 132 registros tabulares limpios (11 activos × 12 meses) que representan $\$24,650,000\text{ MXN}$ en valor comercial y $\$1,144,800\text{ MXN}$ de ingresos anuales.
* **Columnas:** `propiedad`, `categoria`, `ubicacion`, `valor_propiedad`, `renta_mensual`, `mes`, `num_mes`, `ingreso_renta`, `gasto_operativo`, `utilidad_neta`.

### 4.2 Bitácora Operativa Diaria de Gran Volumen (Adaptación Oficial Págs. 23-24)
Para cumplir con el requisito estricto del proyecto de **mínimo 12 meses diarios o 5,000 registros** y permitir el **Análisis Espectral con Transformada Rápida de Fourier (FFT)**, se implementó el generador oficial del kit adaptado a los 11 activos del portafolio:
* **Fuente:** Script reproducible [`generar_ventas.py`](../generar_ventas.py) (semilla `42`, factores de tendencia, ciclo semanal, efecto quincena y estacionalidad).
* **Periodo:** `2025-01-01` a `2026-09-30` (**21 meses continuos diarios**, 638 días).
* **Volumen:** **7,048 registros en bruto** en `raw/bitacora_diaria_portafolio_raw.csv` depurados a **7,018 registros limpios** en `clean/bitacora_diaria_portafolio_clean.csv`.
* **Columnas:** `fecha`, `producto` (propiedad), `categoria`, `ubicacion`, `unidades`, `precio_unitario`, `total`, `ingreso_diario`, `utilidad_diaria`.

### Diccionario de Columnas de la Bitácora Diaria:

| Columna | Tipo de Dato | Clasificación Estadística | Descripción | Ejemplo |
| :--- | :--- | :--- | :--- | :--- |
| `fecha` | DATE | Temporal | Fecha de la operación diaria (AAAA-MM-DD). | `2025-06-15` |
| `producto` / `propiedad` | VARCHAR(50) | Cualitativa nominal | Nombre del activo o inmueble en gestión. | `Aguacatera` |
| `categoria` | VARCHAR(30) | Cualitativa nominal | Tipo de bien (`Casas`, `Terrenos`, `Departamento`, `Vehículos`). | `Terrenos` |
| `ubicacion` | VARCHAR(30) | Cualitativa nominal | Municipio (`Colima`, `Villa de Álvarez`, `Manzanillo`). | `Colima` |
| `unidades` | INT | Cuantitativa discreta | Frecuencia de cobros/servicios registrados en el día. | `20` |
| `precio_unitario` | DECIMAL(10,2) | Cuantitativa continua | Tarifa unitaria base en MXN. | `635.00` |
| `total` / `ingreso_diario` | DECIMAL(10,2) | Cuantitativa continua | Monto total diario cobrado ($\text{unidades} \times \text{precio\_unitario}$). | `12700.00` |

---

## 5. Arranque Técnico en la Nube y Control FinOps ($0)

### 5.1 Proveedor de Nube Seleccionado: Amazon Web Services (AWS)

Evaluamos los tres proveedores líderes de nube para garantizar cobertura técnica total al costo de **$0.00 MXN** durante el semestre:

| Criterio Técnico / Financiero | Amazon Web Services (AWS) *(Elegido)* | Microsoft Azure | Google Cloud Platform (GCP) |
| :--- | :--- | :--- | :--- |
| **Almacenamiento Data Lake (`raw/` y `clean/`)** | **Amazon S3:** 5 GB Standard gratis (20k GET, 2k PUT/mes). | Azure Blob Storage: 5 GB LRS por 12 meses. | Cloud Storage: 5 GB regional US. |
| **Cola de Mensajería Asíncrona (E2)** | **Amazon SQS:** 1,000,000 peticiones/mes *Always Free*. | Azure Service Bus: requiere créditos. | Cloud Pub/Sub: 10 GB/mes gratis. |
| **Cómputo Serverless (Worker E3)** | **AWS Lambda:** 1,000,000 invocaciones/mes *Always Free*. | Azure Functions: 1,000,000 ejecuciones/mes. | Cloud Run functions: 2,000,000 ejecuciones. |
| **Máquina Virtual e Ingesta (E2)** | **Amazon EC2 (`t3.micro`):** 750 h/mes en Free Tier. | VM `B1s` con crédito limitado. | Compute Engine `e2-micro`. |
| **Base de Datos Relacional (E2)** | **Amazon RDS PostgreSQL:** 750 h/mes en Free Tier. | Azure DB PostgreSQL (consume créditos). | Cloud SQL sin Free Tier (con costo). |
| **Control de Presupuesto FinOps** | **AWS Budgets:** Plantilla *Zero-Spend Budget* ($0.01 USD). | Cost Management Alerts. | Cloud Billing Budgets. |

### 5.2 Control de Presupuesto FinOps Activo
* Se configuró la **Alerta de Presupuesto en \$0.00 MXN / \$1.00 USD** dentro de la consola de **AWS Budgets**.
* Notificaciones automáticas configuradas por correo electrónico para alertar al 50%, 80% y 100% de cualquier posible consumo en la cuenta.
* **Seguridad IAM:** Cuentas individuales de usuario IAM para cada integrante (`Cloud Lead` y `Data Lead`), con permisos mínimos requeridos y sin operar bajo la cuenta raíz (*root account*).

### 5.3 Repositorio en GitHub y Estructura Oficial
* **Repositorio oficial:** [`https://github.com/luishinojosacorona123-spec/taacos`](https://github.com/luishinojosacorona123-spec/taacos)
* Estructura inicializada siguiendo las directrices del Proyecto Integrador:
  ```
  taacos/
  ├── README.md            # Documentación general y acceso público
  ├── docs/                # E0-propuesta.md, E1-dashboard.md, arquitectura
  ├── data/sample/         # Muestra anonimizada
  ├── clean/               # Zona clean/ del Data Lake
  ├── raw/                 # Zona raw/ del Data Lake
  ├── services/
  │   ├── ingesta/         # API FastAPI de ingesta (E2)
  │   └── worker/          # Script de limpieza reproducible (E1/E2)
  ├── scripts/             # subir_a_aws.py para provisión de S3
  ├── taacos.py            # Dashboard empresarial interactivo Streamlit
  └── requirements.txt
  ```

---

## 6. Declaración de Uso de IA Generativa

En apego a los lineamientos éticos del Proyecto Integrador:
* **Herramientas empleadas:** Asistentes de IA generativa (Antigravity / Gemini) para asistencia en la estructuración de documentos markdown, normalización de esquemas y prototipado visual en Streamlit.
* **Dominio conceptual del equipo:** Ambos integrantes (**Manuel Alexander Hernández Chávez** y **Luis Antonio Hinojosa Corona**) dominan y son capaces de defender en el Demo Day la lógica del negocio, las respuestas reales de la entrevista, la formulación matemática de la cadena de preguntas y la arquitectura en la nube desplegada.
