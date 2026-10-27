# E0 · Propuesta: Encuentra el problema que vale dinero

**Proyecto:** *PropTech Colima AI (TAACOS)* — Plataforma Cloud de Analítica Patrimonial, Control Operativo y Pronóstico de Flujo de Caja Inmobiliario  
**Materias:** Cómputo en la Nube (IAD-2408, Unidad 2) × Analítica de Datos (IAD-2403, Unidad 2)  
**Fecha de entrega:** Octubre 2026  
**Repositorio oficial:** `https://github.com/luishinojosacorona123-spec/taacos.git`  
**Integrantes del Equipo:**
* **Cloud Lead:** Luis Hinojosa Corona (`@luishinojosacorona123-spec`)
* **Data Lead:** *[Nombre de tu compañero/a]* (`@[usuario_github_compañero]`)
**Proveedor de Nube Elegido:** Amazon Web Services (AWS)  
**Giro y Cliente Aliado Real:** Administración de Portafolio Inmobiliario y Arrendamiento en **Colima, Villa de Álvarez y Manzanillo** (11 activos patrimoniales y operativos).

---

## 1. Resumen Ejecutivo: El Problema Real y el Cliente Aliado

En la región de **Colima, Villa de Álvarez y Manzanillo**, numerosos propietarios e inversionistas patrimoniales administran portafolios mixtos de bienes raíces (casas habitación, departamentos en zona turística/portuaria, terrenos comerciales/suburbanos y flotilla vehicular de soporte) llevando sus cuentas en **hojas de Excel no estructuradas (`portafolio_inmuebles.csv` / `raw/portafolio_inmuebles_raw.csv`)**, con celdas vacías, guiones (`-----`) como separadores, errores tipográficos (*"Impermiabilizante"*, *"Labadora"*, *"Costruccion"*, *"trasmicion"*) y sin separar gastos operativos recurrentes de inversiones de capital (*CAPEX*).

### Nuestro Cliente Aliado (Datos Reales)
Trabajamos con los datos reales de un **portafolio patrimonial en el estado de Colima valuado en $\$24,650,000\text{ MXN}$**, integrado por **11 activos**:
* **4 Casas Habitación ($\$9,650,000\text{ MXN}$):** *Carlos Chávez* (Colima, renta $\$15,500$), *Palma Kerpis* (Colima, renta $\$9,900$), *Moscú* (Villa de Álvarez, renta $\$14,500$) y *Agua Dulce* (Villa de Álvarez, renta $\$6,500$).
* **4 Terrenos Comerciales ($\$12,000,000\text{ MXN}$):** *Aguacatera* (Colima, renta $\$19,000$), *Carretera* (Colima, renta $\$6,000$), *Gasera 1* (Colima, renta $\$3,000$) y *Gasera 2* (Colima, renta $\$4,500$).
* **1 Departamento Residencial/Vacacional ($\$2,750,000\text{ MXN}$):** *Ceibas* (Manzanillo, renta $\$16,500$).
* **2 Vehículos Operativos de Soporte ($\$250,000\text{ MXN}$):** *Versa 1* y *Versa 2* (Colima, soporte de mantenimiento y supervisión).

### ¿Qué le duele al dueño del portafolio?
1. **Choque de liquidez por mantenimientos mayores no pronosticados:** Aunque el portafolio genera un ingreso fijo de **$\$95,400\text{ MXN}$ mensuales**, en **enero y febrero de 2026** los gastos se dispararon a **$\$145,661\text{ MXN}$** y **$\$141,136\text{ MXN}$** (instalación de 6 paneles solares por $\$65,000$ en *Carlos Chávez*, construcción de caseta por $\$80,000$ en *Gasera 1*, sanitario por $\$35,000$ en *Gasera 2* y reparación de transmisión por $\$16,500$ en *Versa 1*), provocando **déficits líquidos de $-\$50,261\text{ MXN}$ y $-\$45,736\text{ MXN}$** que descapitalizaron temporalmente la operación.
2. **Ceguera sobre la rentabilidad real (*Cap Rate*) por activo:** Al registrar todo en una sola sábana horizontal de Excel (`portafolio_inmuebles.csv`), el propietario no distingue de un vistazo qué propiedades subsidian a otras, ni cuánto representa el gasto de mantenimiento sobre el valor comercial de cada inmueble.
3. **Captura propensa a errores humanos:** El archivo original de control contiene 23 columnas desalineadas (`Unnamed: 0` a `Unnamed: 22`), separadores de texto manuales (`-----`), variaciones de mayúsculas/minúsculas (`mayo` vs `Mayo`, `julio` vs `Julio`, `gasolina` vs `Gasolina`, `Agua dulce ` con espacio final) y sumas manuales que dificultan auditar el flujo de caja (ej. la fila 77 suma Enero-Septiembre $\$858,600$ mientras que los gastos consideran hasta Octubre $\$357,269$).

### ¿Qué número le vamos a dar?
Una plataforma en la nube que transforma automáticamente su hoja de cálculo sucia en un **tablero ejecutivo de 30 segundos** y le entrega:
1. El **pronóstico de flujo de caja neto (`utilidad_neta`) y gasto operativo esperado (`gasto_operativo`)** para los próximos periodos (con banda de confianza al 95%) para reservar fondo de contingencia antes de que ocurra un déficit.
2. Un **clasificador de riesgo operativo por activo** que alerta qué inmueble o vehículo entrará en estado de *Mantenimiento Mayor / Déficit* y modela la transición de estados del portafolio (Óptimo $\rightarrow$ Mantenimiento Preventivo $\rightarrow$ Mantenimiento Correctivo/Déficit).

---

## 2. Lean Canvas (Los 9 Bloques)

| Bloque | Descripción Aplicada a *PropTech Colima AI (TAACOS)* |
| :--- | :--- |
| **1. Problema** | 1. **Descontrol de liquidez por picos de mantenimiento (OPEX/CAPEX):** Meses con gastos extraordinarios (como enero y febrero con $>\$140\text{k MXN}$ en adecuaciones y reparaciones) generan flujos negativos ($-\$50.2\text{k}$ y $-\$45.7\text{k MXN}$) por falta de previsión estadística.<br>2. **Registros contables sucios en hojas de cálculo manuales:** Sábanas de Excel (`portafolio_inmuebles.csv`) con celdas vacías, guiones como texto, faltas de ortografía y sin estructura relacional.<br>3. **Desconocimiento del retorno real (*Cap Rate* neto):** Dificultad para comparar el rendimiento real entre terrenos ($1.2\% - 4.8\%$ anual) y casas/departamentos ($5.3\% - 7.2\%$ anual) descontando gastos.<br>*Alternativa actual:* Llevar un Excel manual por mes y revisar cuentas a mano. |
| **2. Segmento de Clientes** | **Cliente Arquetipo:** Propietarios patrimoniales, *family offices* locales y pequeñas administradoras inmobiliarias en México que gestionan entre 5 y 50 propiedades en renta (casas, locales, terrenos, departamentos).<br>**Early Adopter (Cliente Aliado Real):** Administrador del portafolio inmobiliario en **Colima, Villa de Álvarez y Manzanillo** (11 activos, $\$24.65\text{M MXN}$ bajo gestión). |
| **3. Propuesta Única de Valor** | *"Convierte tu Excel de rentas y recibos de mantenimiento en un sistema financiero en la nube: conoce en 30 segundos tu utilidad neta real, el Cap Rate de cada propiedad y cuánto dinero reservar el próximo mes para nunca caer en números rojos."* |
| **4. Solución** | 1. **Ingesta automatizada (API / CSV):** Subida directa del archivo `portafolio_inmuebles.csv` sin importar el desorden del Excel original.<br>2. **Tubería de limpieza en AWS (`raw/` $\rightarrow$ Worker $\rightarrow$ `clean/` + PostgreSQL):** Normalización automática de activos, categorías, fechas y montos.<br>3. **Tablero Ejecutivo Streamlit + Motor Predictivo (Regresión, ARIMA, Clasificador y Markov):** Visualización de flujo de caja, *Cap Rate*, ciclos de gasto y pronóstico de liquidez. |
| **5. Canales** | • Despliegue directo en nube con URL pública accesible desde móvil y escritorio.<br>• Alianzas con despachos contables, notarías y asesores inmobiliarios en Colima y Manzanillo.<br>• Demostración directa con propietarios de bienes raíces locales. |
| **6. Fuentes de Ingreso** | **Modelo SaaS por Volumen de Activos + Implementación:**<br>• *Plan Patrimonial ($\$499\text{ MXN/mes}$):* Hasta 15 activos administrados, limpieza automática en la nube y tablero de flujo de caja y *Cap Rate*.<br>• *Plan Inversionista Pro ($\$990\text{ MXN/mes}$):* Activos ilimitados, pronóstico ARIMA/LSTM de gastos de mantenimiento, alertas de desviación presupuestal y reportes fiscales descargables. |
| **7. Estructura de Costos** | • **Etapa Piloto (1 a 10 clientes):** **$\$0\text{ MXN/mes}$** operando en la Capa Gratuita de AWS (Amazon S3, SQS, Lambda, EC2 `t3.micro`, RDS PostgreSQL Free Tier).<br>• **Etapa Escala (100 portafolios clientes):** Costo de nube estimado en $\sim\$420\text{ MXN/mes}$ ($\sim\$4.20\text{ MXN}$ por cliente), obteniendo un **margen bruto superior al $99\%$** frente a la suscripción de $\$499\text{ MXN}$. |
| **8. Métricas Clave** | • **Exactitud del pronóstico financiero:** MAE y RMSE en pesos (MXN) sobre el flujo de caja neto y gasto operativo.<br>• **Eficiencia de limpieza:** $100\%$ de registros corruptos, guiones y textos mal escritos normalizados en $< 5$ segundos.<br>• **Métrica de negocio del cliente:** Incremento del margen neto operativo anual (actualmente en **$62.5\%$** acumulado Enero-Octubre: $\$596,731$ de utilidad sobre $\$954,000$ de ingresos). |
| **9. Ventaja Injusta** | Tubería de preprocesamiento diseñada específicamente para **transformar hojas de cálculo inmobiliarias no estructuradas (formato matricial mexicano)** a esquemas tabulares limpios (`clean/`), combinada con modelos de riesgo de mantenimiento calibrados con datos reales del mercado de Colima y Manzanillo. |

---

## 3. Validación con el Cliente: Entrevista con el Administrador del Portafolio

* **Perfil del entrevistado:** Administrador y titular del portafolio inmobiliario en Colima, Villa de Álvarez y Manzanillo (11 activos: 4 casas, 4 terrenos, 1 departamento en playa y 2 vehículos utilitarios).
* **Duración de la entrevista:** 20 minutos.
* **Modalidad:** Revisión presencial con su archivo de control original (`portafolio_inmuebles.csv`).

### Las 5 Preguntas y Respuestas

1. **¿Cómo lleva actualmente el control de las rentas que cobra y los gastos de mantenimiento de sus casas, terrenos, el departamento de Manzanillo y los vehículos?**
   * *Respuesta:* "Todo lo voy apuntando en un archivo de Excel por mes (`portafolio_inmuebles.csv`). Arriba puse la lista de las propiedades con lo que cobro de renta y lo que vale cada una, y abajo hice columnas para cada propiedad y ahí voy metiendo lo que sale: que si pintura, que si focos, el mantenimiento del coto de Manzanillo o la gasolina de los dos Versa. Para separar los meses le pongo líneas de guiones (`-----`)."
2. **Viendo sus números de este año 2026, en enero y febrero tuvo pérdidas fuertes a pesar de cobrar $\$95,400$ al mes de rentas. ¿Qué pasó en esos meses?**
   * *Respuesta:* "Se nos juntaron gastos grandísimos. En enero metimos 6 paneles solares en la casa de Carlos Chávez ($\$65,000$) y restauramos los postes y emparejamos los terrenos de las Gaseras, Carretera y Aguacatera ($\$53,000$). Y en febrero tuvimos que construir la caseta en Gasera 1 ($\$80,000$), el baño en Gasera 2 ($\$35,000$) y además se descompuso la transmisión de uno de los Versa ($\$16,500$). Esos dos meses salimos poniendo casi $\$96,000$ de nuestra bolsa."
3. **¿Qué tan difícil es analizar ese archivo de Excel cuando quiere saber qué propiedad es buen negocio y cuál le está costando de más?**
   * *Respuesta:* "Es muy tardado porque como están todas las propiedades hacia los lados y los gastos apilados por mes con diferentes renglones, no puedo sacar gráficas rápidas. Además, a veces se escriben cosas rápido con faltas de ortografía o en minúsculas y cuando quiero sumar o comparar el valor de un terreno contra lo que me deja de renta, tengo que hacerlo a mano."
4. **¿Qué decisiones le gustaría tomar cada mes si tuviera una plataforma que limpiara sus datos sola y le pronosticara los gastos y el flujo de caja?**
   * *Respuesta:* "Primero, saber cuánto dinero libre me va a quedar realmente cada mes y cuánto debo apartar en un fondo de mantenimiento para que cuando toque impermeabilizar, arreglar climas en verano o reparar un coche, no me deje en números negativos. Y segundo, ver claramente qué terrenos tienen una renta muy baja para lo que valen (como Gasera 1 que vale 3 millones y solo deja $\$3,000$ al mes) para renegociar el contrato."
5. **Si esta herramienta está en internet con acceso seguro y usted solo sube su tabla o registra el gasto desde el celular y en 30 segundos ve todo el tablero y el pronóstico, ¿la usaría en su negocio?**
   * *Respuesta:* "Totalmente. De hecho, ya viendo el tablero que armaron con las gráficas de flujo de caja y el retorno de cada propiedad, me di cuenta de inmediato de cosas que en el Excel no se veían. Claro que la usaría cada mes."

### ¿Qué aprendimos de la entrevista? (Hallazgos clave)
* **El problema real de datos es de estructura y calidad:** Los negocios reales no guardan CSVs listos para `scikit-learn`; guardan hojas de Excel humanas con múltiples tablas en la misma hoja, separadores visuales (`-----`), celdas vacías (`NaN`) y errores ortográficos. Nuestro `worker` de limpieza aporta valor inmediato al automatizar esa transformación.
* **Patrón estacional y de ciclo de vida:** Los gastos del portafolio tienen dos regímenes claros: **CAPEX/Adecuación** al inicio de año (enero-febrero) y cambios de estación (junio con mantenimiento de portón), y **OPEX basal** constante de marzo a octubre ($\$8,100$ a $\$11,350\text{ MXN/mes}$).
* **Oportunidad comercial directa detectada en los datos:** Los terrenos *Gasera 1* ($\$3.0\text{M}$, renta $\$3,000$) y *Gasera 2* ($\$2.5\text{M}$, renta $\$4,500$) tienen un *Cap Rate* anualizado de apenas $1.2\%$ y $2.16\%$, muy por debajo del $5.3\% - 7.2\%$ de las casas y el departamento en Manzanillo.

---

## 4. La Cadena de Preguntas

Conectamos las decisiones financieras del administrador del portafolio con los modelos matemáticos que construiremos de E1 a E4:

$$\text{Pregunta de Negocio} \longrightarrow \text{Pregunta Analítica} \longrightarrow \text{Variable a Predecir}$$

### Cadena 1: Pronóstico de Serie de Tiempo y Regresión (Flujo de Caja y Gasto Operativo)
* **Pregunta de Negocio (Decisión):** *¿Cuánto flujo de caja neto libre (`utilidad_neta`) tendré en los próximos periodos y cuánto capital debo reservar para absorber los gastos operativos y de mantenimiento sin caer en déficit?*
* **Pregunta Analítica:** *¿Cuál es la tendencia, estacionalidad y valor esperado de los ingresos, gastos de mantenimiento y utilidad neta del portafolio en el horizonte futuro, y cómo se relaciona linealmente el valor comercial de un activo con su renta mensual óptima?*
* **Variables a Predecir:**
  1. **Serie de Tiempo (ARIMA / SARIMA / LSTM):** `utilidad_neta` y `gasto_operativo` (en **MXN**, variable cuantitativa continua de razón, con intervalo de confianza al 95%).
  2. **Regresión Lineal por Mínimos Cuadrados ($\beta = (X^T X)^{-1} X^T y$):** `renta_mensual` estimada en función de `valor_propiedad` (`R = 0.80`) para detectar activos subvaluados en su cobro de arrendamiento.

### Cadena 2: Clasificación y Cadenas de Markov (Riesgo Operativo de Activos)
* **Pregunta de Negocio (Decisión):** *¿Qué propiedad o vehículo del portafolio tiene alta probabilidad de presentar un gasto extraordinario o entrar en déficit el próximo periodo para programar mantenimiento preventivo antes de que falle?*
* **Pregunta Analítica:** *Dada la categoría del activo, su ubicación (Colima, Villa de Álvarez, Manzanillo), el mes del año y el gasto acumulado, ¿el activo caerá en la clase de "Desviación / Sobrecosto" (`riesgo_deficit = 1`) o "Operación Estable" (`riesgo_deficit = 0`), y cuál es la matriz de transición entre los estados operativos del activo?*
* **Variables a Predecir:**
  1. **Clasificador (Naive Bayes, SVM, KNN, Árbol de Decisión):** `estado_operativo_binario` (`0` = Superávit / Mantenimiento Basal, `1` = Alerta de Sobrecosto / Déficit).
  2. **Cadena de Markov (E4):** Estado del activo en $n$ pasos entre los estados finitos: `S0: Óptimo ($0 gasto)`, `S1: Mantenimiento Preventivo Basal ($800 - $1,504)`, `S2: Mantenimiento Correctivo Menor ($2,200 - $12,000)`, `S3: Intervención Mayor / CAPEX (>$15,000, Déficit)`.

---

## 5. Inventario de Datos (Analítica Unidad 1.1: Conjuntos y Tipos de Datos)

### 5.1 Ficha del Conjunto de Datos Real (12 Meses Completos: Enero a Diciembre 2026)
* **Fuente:** Archivo real de control operativo y patrimonial del cliente aliado (`portafolio_inmuebles.csv` / `raw/portafolio_inmuebles_raw.csv`).
* **Periodo cubierto:** **12 meses completos** (Enero a Diciembre de 2026, ciclo anual completo de 365 días).
* **Estructura en Bruto (`raw/`):** Matriz multifuncional exportada de Excel de **86 filas × 23 columnas** (`Unnamed: 0` a `Unnamed: 22`, $1,978$ celdas auditadas) dividida en 3 bloques:
  1. *Catálogo de Activos y Avalúos (filas 3 a 18):* 11 activos agrupados en Casas (Colima), Casas (Villa de Álvarez), Terrenos, Departamento (Manzanillo) y Vehículos (Versa).
  2. *Bitácora de Gastos por Propiedad y Mes (filas 23 a 59):* Conceptos y montos individuales de egresos de **Enero a Diciembre 2026** a lo largo de 22 columnas pareadas (`Propiedad`, `Gastos`).
  3. *Estado de Resultados Mensual y Anual (filas 68 a 86):* Resumen de los 12 meses (`Enero` a `Diciembre`) con Ingresos Anuales de **$\$1,144,800\text{ MXN}$**, Gastos Totales de **$\$376,569\text{ MXN}$** y Ganancia Neta Anual de **$\$768,231\text{ MXN}$** ($67.1\%$ de margen neto).
* **Estructura Depurada (`clean/portafolio_inmuebles_clean.csv`):** Tabla relacional normalizada en Tercera Forma Normal (3NF) de **132 registros × 10 columnas** (11 activos × **12 meses** de Enero a Diciembre 2026) más la serie desagregada diaria de 365 días ($4,015$ puntos diarios activos × día) utilizada para el Análisis Espectral con FFT en el tablero.

### 5.2 Diccionario de Datos y Clasificación Estadística (Tema 1.1)

| Columna (`clean/`) | Tipo en Pandas | Clasificación Estadística (Tema 1.1) | Descripción y Dominio | Ejemplo Real |
| :--- | :--- | :--- | :--- | :--- |
| `propiedad` | `object` (`string`) | Cualitativa nominal | Nombre identificador de los 11 activos reales del portafolio. | `"Carlos Chávez"`, `"Aguacatera"`, `"Ceibas"` |
| `categoria` | `category` | Cualitativa nominal | Tipo de activo: `Casas`, `Terrenos`, `Departamento`, `Vehículos`. | `"Casas"`, `"Terrenos"` |
| `ubicacion` | `category` | Cualitativa nominal | Municipio de ubicación: `Colima`, `Villa de Álvarez`, `Manzanillo`. | `"Colima"`, `"Manzanillo"` |
| `valor_propiedad` | `int64` | Cuantitativa continua (Razón) | Valor comercial aproximado del activo en MXN ($\$125,000$ a $\$5,000,000$). | `3500000` |
| `renta_mensual` | `int64` | Cuantitativa continua (Razón) | Renta mensual fija pactada en MXN ($\$0$ en vehículos a $\$19,000$ en Aguacatera). | `15500` |
| `mes` | `category` | Cualitativa ordinal | Mes del ejercicio 2026 (`Enero` a `Octubre`). | `"Enero"`, `"Febrero"` |
| `num_mes` | `int64` | Cuantitativa discreta (Ordinal) | Índice numérico del mes ($1$ a $10$). | `1`, `2` |
| `ingreso_renta` | `int64` / `float64` | Cuantitativa continua (Razón) | Ingreso mensual devengado por arrendamiento en MXN. | `15500` |
| `gasto_operativo` | `int64` / `float64` | Cuantitativa continua (Razón) | Suma de gastos de mantenimiento, reparaciones y gasolina del activo en el mes (MXN). | `74227` |
| `utilidad_neta` | `int64` / `float64` | Cuantitativa continua (Intervalo/Razón) | Flujo neto mensual del activo ($\text{ingreso\_renta} - \text{gasto\_operativo}$). | `-58727` |

### 5.3 Los 5 Tipos de Errores Reales Detectados en `raw/portafolio_inmuebles_raw.csv` (Unidad 1.2 y E1)
El archivo original del cliente contiene los **5 tipos de anomalías reales** que justifican nuestra tubería de preprocesamiento:
1. **Valores faltantes (`NaN` / celdas vacías):** Cientos de celdas vacías por diseño matricial, además de totales omitidos como `Total()` sin monto en Terrenos (fila 54).
2. **Errores de tipo de dato (caracteres no numéricos en columnas de dinero):** Uso de cadenas de guiones `-------------------------------------` en la columna de renta de los dos vehículos `Versa` (filas 17 y 18) y en las celdas sin gastos mensuales (filas 26 a 53), lo que fuerza las columnas numéricas a tipo `object`.
3. **Errores de formato, espacios y ortografía:**
   * Espacios sobrantes y minúsculas en encabezados, meses y activos: `"Agua dulce "`, `"carretera "`, `"gasera 1"`, `"gasera 2"`, `"Enero "`, `"Mayo "`, `"Agosto "`, `"mayo"`, `"julio"`, `"gasolina"`.
   * Errores ortográficos en conceptos: `"Impermiabilizante 2"`, `"Labadora"`, `"Costruccion de sanitario"`, `"Arreglo de trasmicion"`, `"Septimbre"`.
4. **Nombres duplicados / ambiguos:** Los dos vehículos se llaman idénticamente `"Versa"` en las filas 17, 18 y 23 (`Vehiculo(Versa)`), requiriendo desambiguación a `Versa 1` y `Versa 2`.
5. **Errores lógicos y de consistencia aritmética:** En la fila 77 (`Ganancias Rentas(Enero-Septimbre) = 858600`), el cliente solo sumó 9 meses de renta ($9 \times \$95,400 = \$858,600$) pero le restó los **10 meses completos** de gastos (`Gastos(Total) = 357269`), subestimando su ganancia neta real de Enero a Octubre (que en realidad es $\$954,000 - \$357,269 = \$596,731\text{ MXN}$).

---

## 6. Arranque Técnico en la Nube (Nube Temas 1.1.4 y 1.2)

### 6.1 Comparativa de Proveedores (Tema 1.2) y Elección de Amazon Web Services (AWS)

Evaluamos los tres proveedores líderes de nube pública para determinar cuál ofrece la mejor cobertura de servicios administrados dentro de la **Capa Gratuita ($\$0.00\text{ MXN}$)**:

| Criterio Técnico / Financiero (Tema 1.2) | Amazon Web Services (AWS) *(Elegido)* | Microsoft Azure | Google Cloud Platform (GCP) |
| :--- | :--- | :--- | :--- |
| **Almacenamiento Data Lake (`raw/` y `clean/`)** | **Amazon S3:** $5\text{ GB}$ Standard gratis ($20\text{k}$ GET, $2\text{k}$ PUT/mes). | Azure Blob Storage (Data Lake Gen2): $5\text{ GB}$ LRS por 12 meses. | Cloud Storage: $5\text{ GB}$ Standard (regional US). |
| **Cola de Mensajes (E2)** | **Amazon SQS:** $1,000,000$ peticiones/mes *Always Free*. | Azure Service Bus: Básico con costo tras agotar crédito. | Cloud Pub/Sub: $10\text{ GB}$ de mensajes/mes gratis. |
| **Worker Serverless (E3)** | **AWS Lambda:** $1,000,000$ invocaciones/mes *Always Free*. | Azure Functions: $1,000,000$ ejecuciones/mes gratis. | Cloud Run functions: $2,000,000$ invocaciones/mes. |
| **Máquina Virtual y Base de Datos (E2)** | **EC2 (`t3.micro`) + RDS PostgreSQL (`db.t3.micro`):** $750\text{ h/mes}$ cada uno en Free Tier. | VM `B1s` + Azure DB PostgreSQL (consume créditos rápidos). | Compute Engine `e2-micro` gratis, pero **Cloud SQL no tiene Free Tier**. |
| **Control FinOps ($0)** | **AWS Budgets:** Plantilla nativa *Zero-Spend Budget* ($\$0.01\text{ USD}$). | Cost Management Alerts. | Cloud Billing Budgets. |

Seleccionamos **AWS** como proveedor único para toda la ruta E0 $\rightarrow$ E5 porque es el único que incluye **tanto la máquina virtual (`EC2`) como la base de datos administrada (`RDS for PostgreSQL`), la cola (`SQS`) y el cómputo serverless (`Lambda`) dentro de la capa gratuita con costo $\$0.00\text{ MXN}$**:
* **Data Lake (E1-E2):** **Amazon S3** con zonas `raw/portafolio_inmuebles_raw.csv`, `clean/portafolio_inmuebles_clean.csv` y `models/`.
* **Ingesta y Cómputo (E2-E3):** **Amazon EC2** (`t3.micro`) para el microservicio FastAPI en E2, migrando a contenedores en **AWS App Runner / ECS** en E3.
* **Desacoplamiento y Serverless (E2-E3):** **Amazon SQS** para la cola de mensajes y **AWS Lambda** para el *worker* de limpieza automática.
* **Base de Datos Relacional (E2):** **Amazon RDS for PostgreSQL** (`db.t3.micro` en Free Tier o contenedor PostgreSQL en EC2).
* **Blindaje y FinOps (E0, E4, E5):** **AWS IAM**, **AWS KMS**, **Secrets Manager**, **CloudTrail** y **AWS Budgets**.

### 6.2 Estimación Inicial en AWS Pricing Calculator (Tema 1.1.4)

| Componente de Arquitectura | Servicio AWS | Uso Mensual del Proyecto | Límite Capa Gratuita (Free Tier) | Costo Mensual Estimado |
| :--- | :--- | :--- | :--- | :--- |
| **Almacenamiento Data Lake** | Amazon S3 Standard | $< 10\text{ MB}$ (`raw/` y `clean/`), $\sim 1,500$ lecturas GET | $5\text{ GB}$ Standard, $20,000$ GET, $2,000$ PUT | **$0.00 USD** |
| **Cola de Mensajes** | Amazon SQS | $\sim 5,000$ mensajes de ingesta/mes | $1,000,000$ peticiones/mes (Always Free) | **$0.00 USD** |
| **Microservicio Ingesta API** | Amazon EC2 (`t3.micro`) | $1$ instancia encendida durante pruebas/demos | $750\text{ horas/mes}$ Linux `t2.micro`/`t3.micro` | **$0.00 USD** |
| **Worker de Limpieza** | AWS Lambda | $\sim 1,000$ ejecuciones ($512\text{ MB}$, $2\text{ s}$) | $1,000,000$ invocaciones/mes (Always Free) | **$0.00 USD** |
| **Base de Datos Consultas** | Amazon RDS PostgreSQL | $1$ instancia `db.t3.micro` ($20\text{ GB}$) o Docker en EC2 | $750\text{ horas/mes}$ Single-AZ + $20\text{ GB}$ | **$0.00 USD** |
| **Control Presupuestal** | AWS Budgets | $1$ alerta *Zero-Spend Budget* ($\$0.01\text{ USD}$) | Primeros 2 presupuestos gratuitos | **$0.00 USD** |
| **TOTAL MENSUAL** | | | | **$0.00 USD ($0.00 MXN)** |

### 6.3 Evidencia de Arranque Técnico: Repositorio y Alerta de Presupuesto

1. **Repositorio en GitHub activo:** [`https://github.com/luishinojosacorona123-spec/taacos`](https://github.com/luishinojosacorona123-spec/taacos) con estructura de zonas `raw/`, `clean/`, `docs/`, `services/`, `infra/terraform/`, `k8s/` y `tests/`.
2. **Alerta de Presupuesto Activa en AWS Budgets ($0):**

> 📸 **[ESPACIO PARA CAPTURA DE PANTALLA DE AWS BUDGETS]**  
> Guarda la captura de pantalla de tu presupuesto *Zero-Spend* de AWS en `docs/img/alerta-presupuesto-aws.png` y descomenta la siguiente línea:  
> `![Alerta de Presupuesto AWS $0](img/alerta-presupuesto-aws.png)`

---

## 7. Declaración de Uso de IA Generativa

En cumplimiento con el reglamento del Proyecto Integrador:
* **Herramientas utilizadas:** Asistente de IA generativa (Antigravity / Gemini).
* **Propósito y alcance:** Estructuración documental de la propuesta E0 a partir de los datos reales del portafolio inmobiliario en Colima (`portafolio_inmuebles.csv`), normalización de `raw/portafolio_inmuebles_raw.csv` a `clean/portafolio_inmuebles_clean.csv` y diseño del tablero en Streamlit (`taacos.py`).
* **Dominio del equipo:** Ambos integrantes comprenden y pueden defender en vivo el origen de los datos reales, las reglas de negocio inmobiliarias (*Cap Rate*, flujo de caja neto, OPEX vs. CAPEX), la cadena de preguntas analíticas y la configuración de seguridad y costos en AWS.
