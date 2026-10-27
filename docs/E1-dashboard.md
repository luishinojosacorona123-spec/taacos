# E1 · Dashboard Empresarial: Los datos cuentan su historia

**Proyecto:** *PropTech Colima AI (TAACOS)* — Gestión de Portafolio Inmobiliario y Rentas  
**Materias:** Analítica de Datos (Unidad 2, temas 2.1 a 2.8) × Cómputo en la Nube (Tema 2.4: Almacenamiento en nube)  
**Archivo ejecutable del Tablero:** [`taacos.py`](../taacos.py)  
**Módulo de Limpieza:** [`services/worker/limpiar_portafolio.py`](../services/worker/limpiar_portafolio.py)

---

## 1. Limpieza de Datos y Preprocesamiento (`raw/` $\rightarrow$ `clean/`)

El archivo original del negocio aliado (`raw/portafolio_inmuebles_raw.csv`, 79 filas × 23 columnas) fue procesado para detectar y corregir los **5 tipos de errores** vistos en la Unidad 1.2, generando el archivo relacional depurado `clean/portafolio_inmuebles_clean.csv` (110 registros × 10 columnas, correspondientes a los 11 activos durante los 10 meses de Enero a Octubre 2026):

| Tipo de Error (Unidad 1.2) | Celdas / Registros Corregidos | Hallazgo en `raw/portafolio_inmuebles_raw.csv` | Corrección en `clean/portafolio_inmuebles_clean.csv` |
| :--- | :---: | :--- | :--- |
| **1. Valores faltantes (`NaN`)** | **1,412** | Filas divisoras en blanco, columnas `Unnamed` vacías y celda `Total()` sin valor en Terrenos (fila 54). | Eliminación de filas vacías, imputación de `$0` en meses sin gasto operativo y estructuración en 110 filas completas (`0 NaN`). |
| **2. Tipos de dato inválidos** | **218** | Uso de guiones `-------------------------------------` en la columna de renta de los dos vehículos `Versa` y en meses sin gastos. | Limpieza de cadenas no numéricas, conversión estricta a `int64`/`float64` y asignación de `0` en `renta_mensual` para vehículos. |
| **3. Formato y ortografía** | **34** | Espacios y minúsculas (`"Agua dulce "`, `"carretera "`, `"gasera 1"`, `"mayo"`, `"julio"`, `"gasolina"`) y errores (`"Impermiabilizante"`, `"Labadora"`, `"trasmicion"`). | Aplicación de `.str.strip()`, normalización a *Title Case* (`"Agua Dulce"`, `"Carretera"`, `"Gasera 1"`, `"Carlos Chávez"`) y homologación de meses. |
| **4. Duplicados / Ambigüedad** | **20** | Los dos vehículos utilitarios aparecen con el mismo nombre `"Versa"` en las filas 17–18 y columnas 19–22 (10 meses × 2 vehículos). | Desambiguación a `"Versa 1"` y `"Versa 2"` para garantizar llave primaria única `(propiedad, mes)` con 0 duplicados. |
| **5. Errores lógicos y Atípicos** | **14** | La fila 77 (`Ganancias Rentas(Enero-Septimbre) = 858600`) suma 9 meses de renta pero resta 10 meses de gastos (`357269`); choques atípicos en Ene-Feb (`$65k` paneles, `$80k` caseta). | Recálculo programático exacto: $\text{utilidad\_neta} = \text{ingreso\_renta} - \text{gasto\_operativo}$ ($\$954,000 - \$357,269 = \$596,731\text{ MXN}$). |

---

## 2. Encabezado de Indicadores (KPIs Ejecutivos)

Al abrir `taacos.py`, el dueño visualiza en menos de 5 segundos los **4 indicadores clave**:
1. **💵 Ingresos del Periodo (Rentas):** **$\$954,000\text{ MXN}$** acumulados (Enero–Octubre 2026), equivalentes a **$\$95,400\text{ MXN/mes}$** fijos.
2. **📈 Ticket / Renta Promedio y Utilidad Neta:** Renta promedio de **$\$10,600\text{ MXN/mes}$** por propiedad arrendada y **$\$596,731\text{ MXN}$** de utilidad neta libre (margen neto del **$62.5\%$**).
3. **⭐ Activo Estrella:** **Terreno Aguacatera** con **$\$19,000\text{ MXN/mes}$** ($19.9\%$ de la captación mensual) y **Departamento Ceibas Manzanillo** con **$\$16,500\text{ MXN/mes}$** (mayor utilidad neta acumulada: $\$148,800\text{ MXN}$).
4. **🔄 Variación contra el Mes Anterior (Octubre vs. Septiembre):** **$-3.5\%$** en utilidad neta mensual ($\$84,050$ en octubre frente a $\$87,100\text{ MXN}$ en septiembre), explicada por el gasto correctivo de $\$3,050\text{ MXN}$ (arreglo de pantalla en *Versa 2*).

---

## 3. Catálogo de Visualizaciones con Hallazgo en el Título y Fundamento Teórico

El tablero incluye **9 visualizaciones interactivas** (superando el mínimo de 6 y cubriendo todos los tipos obligatorios de la rúbrica):

1. **Líneas (Tendencia de Flujo de Caja):**
   * *Título con hallazgo:* `¿Cómo evoluciona el flujo de caja mensual? — Hallazgo: Desde marzo la utilidad se estabiliza sobre $84,000 MXN/mes tras absorber $286,797 de CAPEX en ene-feb`
2. **Barras Horizontales (Comparación / Ranking):**
   * *Título con hallazgo:* `¿Qué propiedades generan más renta? — Hallazgo: Aguacatera, Ceibas y Carlos Chávez aportan el 53.5% del ingreso`
3. **Circular / Pastel (Composición de Ingresos):**
   * *Título con hallazgo:* `¿Cómo se dividen los ingresos? — Hallazgo: El 62.5% ($596.7k) queda como ganancia neta libre`
4. **Histograma con Regla de Sturges (Distribución y Sesgo):**
   * *Título con hallazgo:* `¿Cómo se distribuye la utilidad neta mensual por activo? — Hallazgo: El 81.8% de los meses-activo genera superávit entre $3,000 y $19,000 MXN (sesgo izquierdo por 4 eventos de CAPEX)`
   * *Sustento matemático (Regla de Sturges):* Para $n = 110$ observaciones (meses-activo), el número óptimo de intervalos (*bins*) se calcula como:
     $$k = 1 + \lceil \log_2(110) \rceil = 1 + \lceil 6.78 \rceil = 8\text{ bins}$$
     La distribución presenta **sesgo negativo ($g_1 = -4.18$)** porque la mediana ($\$4,500\text{ MXN}$) es mayor que la media ($\$5,425\text{ MXN}$ con cola izquierda hasta $-\$77,000\text{ MXN}$ en *Gasera 1*).
5. **Boxplot / Diagrama de Caja (Dispersión por Categoría):**
   * *Título con hallazgo:* `¿Cómo varían los gastos por categoría? — Hallazgo: Casas y Terrenos concentran los picos atípicos; Depto y Vehículos son fijos ($1.5k)`
6. **Dispersión / Scatter Plot con Regresión (Relación Bivariada):**
   * *Título con hallazgo:* `¿Relación valor comercial vs. renta? — Hallazgo: Correlación fuerte (R = 0.80), pero Gasera 1 rinde solo 1.2% anual`
7. **Mapa de Calor: Matriz de Correlación de Pearson y Tabla Cruzada:**
   * *Título con hallazgo:* `¿Cómo se correlacionan las variables y qué activo/mes concentra el déficit? — Hallazgo: Correlación de r = -0.94 entre gasto y utilidad; el 100% del déficit ocurre en Ene-Feb`
8. **Análisis Espectral con Transformada Rápida de Fourier (FFT):**
   * *Título con hallazgo:* `¿Qué ciclos dominan el flujo de caja y los gastos del portafolio? — Hallazgo: La FFT detecta el ciclo anual de CAPEX, el ciclo mensual de cobro de rentas (30 días) y el ciclo quincenal de mantenimiento (15 días)`
   * *Sustento matemático (FFT):* Aplicamos la Transformada Discreta de Fourier sobre la serie centrada $\tilde{x}[n] = x[n] - \bar{x}$:
     $$X[k] = \sum_{n=0}^{N-1} \tilde{x}[n] \, e^{-i 2\pi k n / N}, \quad T = \frac{1}{f}$$
     Identificamos tres picos espectrales dominantes:
     * **$T_1 = 30.0\text{ días}$ ($f_1 = 0.033\text{ ciclos/día}$):** Ciclo mensual de facturación y cobro de los 9 contratos de arrendamiento.
     * **$T_2 = 15.0\text{ días}$ ($f_2 = 0.067\text{ ciclos/día}$):** Efecto quincena en México (pago quincenal de mano de obra de mantenimiento, jardinería, cuota de coto en Manzanillo y servicios).
     * **$T_3 = 7.0\text{ días}$ ($f_3 = 0.143\text{ ciclos/día}$):** Ciclo semanal de dotación de gasolina ($\$1,500/\text{mes}$ por vehículo) y rondas de supervisión en *Versa 1* y *Versa 2*.
9. **Gráfica de Dona (Composición Patrimonial):**
   * *Título con hallazgo:* `¿Cómo se distribuye el patrimonio de $24.65M MXN? — Hallazgo: Terrenos (48.7%) y Casas (39.1%) concentran el 87.8% del valor patrimonial`

---

## 4. Tres Recomendaciones de Negocio para el Dueño

1. **Renegociar el arrendamiento de los terrenos *Gasera 1* y *Gasera 2* tras las mejoras de capital (+$\$9,000$ a +$\$12,500\text{ MXN/mes}$):**
   * *Explicación para el dueño:* Este año usted invirtió $\$107,000\text{ MXN}$ en *Gasera 1* (caseta de $\$80\text{k}$, postes y emparejado) y $\$41,000\text{ MXN}$ en *Gasera 2* (sanitario de $\$35\text{k}$ y postes), pero sigue cobrando solo $\$3,000$ y $\$4,500\text{ MXN}$ de renta mensual ($1.2\%$ y $2.1\%$ anual sobre su valor). Al renovar contrato, ajuste la renta hacia el $4\%$ anual promedio de sus otros terrenos ($\$10,000\text{ MXN/mes}$ en *Gasera 1* y $\$8,300\text{ MXN/mes}$ en *Gasera 2*).
2. **Constituir un "Fondo Quincenal de Mantenimiento" reteniendo $\$5,750\text{ MXN}$ por quincena de Marzo a Diciembre:**
   * *Explicación para el dueño:* De marzo a octubre su portafolio le deja libres más de $\$84,000\text{ MXN}$ cada mes, pero en enero y febrero tuvo que poner $\$95,997\text{ MXN}$ de su bolsa por juntar todas las obras. Si aparta $\$5,750\text{ MXN}$ cada quincena ($\$11,500/\text{mes}$) en los 10 meses estables, juntará **$\$115,000\text{ MXN}$** de reserva y ningún mes volverá a cerrar en números rojos.
3. **Escalonar obras mayores (máximo 1 por trimestre) y aplicar mantenimiento preventivo semestral a los dos *Versa*:**
   * *Explicación para el dueño:* Hacer los paneles solares de *Carlos Chávez* ($\$65\text{k}$) al mismo tiempo que la caseta de *Gasera 1* ($\$80\text{k}$) y la transmisión del *Versa 1* ($\$16.5\text{k}$) descapitalizó el inicio de año. Programe una sola mejora grande por trimestre y haga servicio preventivo a los vehículos cada 6 meses para evitar reparaciones de caja/transmisión de más de $\$15,000\text{ MXN}$.

---

## 5. Arquitectura de Almacenamiento en la Nube (Nube Tema 2.4)

### 5.1 Almacenamiento de Objetos vs. Bloques vs. Archivos
* **Almacenamiento de Objetos (Amazon S3):** Elegido para nuestro **Data Lake** porque almacena archivos completos (`CSV`, `Parquet`, modelos `.pkl`) como objetos inmutables con metadatos y acceso vía API HTTP/REST (`GET`/`PUT`), escalando sin límite y costando $\$0.00\text{ USD}$ en la Capa Gratuita hasta $5\text{ GB}$.
* **Almacenamiento de Bloques (Amazon EBS):** Discos virtuales acoplados a una instancia EC2 (se usará en E2 para el sistema operativo de la VM y el volumen de datos de PostgreSQL).
* **Almacenamiento de Archivos (Amazon EFS):** Sistema de archivos compartido por red (NFS) para múltiples instancias; no se requiere en E1 dado que Streamlit consulta objetos directamente desde `clean/`.

### 5.2 Convención de Nombres del Data Lake y Prefijos (`raw/` y `clean/`)
* **Nombre del Bucket S3:** `taacos-datalake-colima-2026`
* **Estructura de Zonas (Prefijos):**
  * `s3://taacos-datalake-colima-2026/raw/portafolio_inmuebles_raw.csv` $\rightarrow$ Datos tal como llegan del Excel del cliente (inmutables, zona de aterrizaje).
  * `s3://taacos-datalake-colima-2026/clean/portafolio_inmuebles_clean.csv` $\rightarrow$ Datos validados, sin `NaN`, sin guiones y en formato tabular 3NF consumidos directamente por `taacos.py`.
  * `s3://taacos-datalake-colima-2026/models/` $\rightarrow$ Zona reservada para artefactos de modelos entrenados en E3 y E4.

### 5.3 Data Lake vs. Data Warehouse
* **Data Lake (Amazon S3):** Almacena datos en su formato nativo (`raw/` semi-estructurado y `clean/` estructurado) bajo esquema de lectura (*schema-on-read*), ideal para ciencia de datos y entrenamiento de modelos ML.
* **Data Warehouse / Base Relacional de Consultas (PostgreSQL en E2):** Almacena datos bajo esquema de escritura estricto (*schema-on-write*) optimizado para consultas SQL transaccionales y agregaciones rápidas.

### 5.4 Seguridad y Credenciales de Acceso Programático
* **Cero credenciales en el código:** `taacos.py` utiliza `os.getenv('AWS_ACCESS_KEY_ID')` y `os.getenv('AWS_SECRET_ACCESS_KEY')` cargadas desde variables de entorno (`.env` ignorado en `.gitignore` o `st.secrets` en Streamlit Cloud). Subir llaves IAM a un repositorio público compromete la cuenta en minutos mediante bots de escaneo automatizado.
* **Usuarios IAM individuales y Presupuesto $0:** Se opera exclusivamente con usuarios IAM con permisos acotados (`AmazonS3ReadOnlyAccess` para el tablero) y MFA activo en la cuenta raíz.
