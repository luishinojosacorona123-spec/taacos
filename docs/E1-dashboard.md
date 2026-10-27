# E1 · Dashboard Empresarial: Los datos cuentan su historia

**Proyecto:** *PropTech Colima AI (TAACOS)* — Gestión de Portafolio Inmobiliario y Rentas  
**Materias:** Analítica de Datos (Unidad 2, temas 2.1 a 2.8) × Cómputo en la Nube (Tema 2.4: Almacenamiento en nube)  
**URL Pública del Tablero (Streamlit Cloud):** [`https://luishinojosacorona123-spec-taacos-taacos-nuiqdn.streamlit.app`](https://luishinojosacorona123-spec-taacos-taacos-nuiqdn.streamlit.app)  
**Archivo ejecutable del Tablero:** [`taacos.py`](../taacos.py)  
**Módulo Reproducible de Limpieza:** [`services/worker/limpiar_portafolio.py`](../services/worker/limpiar_portafolio.py)

---

## 1. Limpieza de Datos Reproducible (`raw/` $\rightarrow$ `clean/`)

El proyecto procesa y valida de forma programática (mediante [`services/worker/limpiar_portafolio.py`](../services/worker/limpiar_portafolio.py)) dos niveles de granularidad en las zonas `raw/` y `clean/`:
1. **Matriz Mensual Real del Cliente (`raw/portafolio_inmuebles_raw.csv` $\rightarrow$ `clean/portafolio_inmuebles_clean.csv`):** 86 filas × 23 columnas en bruto transformadas a **132 registros relacionales limpios** (11 activos × 12 meses de Enero a Diciembre 2026; con Enero–Octubre observados y Noviembre–Diciembre identificados como cierre anual proyectado).
2. **Bitácora Operativa Diaria (`raw/bitacora_diaria_portafolio_raw.csv` $\rightarrow$ `clean/bitacora_diaria_portafolio_clean.csv`):** **5,062 registros diarios en bruto** depurados a **5,027 registros diarios limpios** (15 meses: `2025-10-01` a `2026-12-31`), garantizando el requisito de $>12$ meses diarios y $>5,000$ registros para el cálculo de variación semanal, distribución del ticket diario y Análisis Espectral con FFT.

### Conteo Verificado en Código de los 5 Tipos de Error

| Tipo de Error (Unidad 1.2) | Corregidos en Bitácora Diaria (`5,027` reg.) | Corregidos en Matriz Mensual (`132` reg.) | Regla Programática Aplicada en `limpiar_portafolio.py` |
| :--- | :---: | :---: | :--- |
| **1. Valores faltantes (`NaN`)** | **45** | **1,185** | Imputación con mediana por propiedad en bitácora diaria y eliminación de celdas divisorias vacías en matriz mensual (`0 NaN` en `clean/`). |
| **2. Tipos de dato inválidos (`-----`)** | **0** | **266** | Sustitución por expresión regular `r"^-+$" -> 0` en renta de vehículos `Versa` y meses sin gastos; conversión estricta a `int64`/`float64`. |
| **3. Formato, espacios y ortografía** | **30** | **28** | Aplicación de `.str.strip()`, normalización *Title Case* (`"Agua Dulce"`, `"Carretera"`, `"Gasera 1"`, `"Carlos Chávez"`) y corrección ortográfica. |
| **4. Duplicados y llaves ambiguas** | **35** | **26** | `drop_duplicates(subset=['fecha', 'propiedad'])` en bitácora diaria y desambiguación de `"Versa"` en `"Versa 1"` y `"Versa 2"`. |
| **5. Errores lógicos y Atípicos** | **30** *(18 negativos + 12 outliers)* | **9** | Valor absoluto en 18 gastos negativos, reemplazo de 12 outliers (`999,999`) por mediana y recálculo exacto $\text{utilidad\_neta} = \text{ingreso} - \text{gasto}$. |

---

## 2. Encabezado de Indicadores (4 KPIs Sincronizados con los Filtros)

Al abrir `taacos.py`, todos los indicadores se calculan dinámicamente a partir de los datos filtrados:
1. **💵 Ingresos del Periodo:** **$\$1,144,800\text{ MXN}$** en los 12 meses (o **$\$954,000\text{ MXN}$** en los 10 meses observados Enero–Octubre), con **Ticket/Renta promedio de $\$10,600\text{ MXN/mes}$** por activo arrendado.
2. **📈 Utilidad Neta y Variación Semanal / Mensual:** **$\$768,231\text{ MXN}$** de flujo libre anual (**$67.1\%$ de margen neto**; $\$596,731\text{ MXN}$ y $62.5\%$ en Enero–Octubre), mostrando tanto la **variación contra la semana anterior** (calculada sobre la bitácora diaria) como la variación mensual.
3. **⭐ Activo Estrella:** **Terreno Aguacatera** con **$\$19,000\text{ MXN/mes}$** ($19.9\%$ de las rentas mensuales del portafolio).
4. **🏛️ Valor Patrimonial en Gestión:** **$\$24,650,000\text{ MXN}$** en 11 activos (con gastos acumulados de $\$376,569\text{ MXN}$ en 12 meses).

---

## 3. Visualizaciones, Regla de Sturges y Transformada de Fourier (FFT)

1. **Gráfica 1 (Líneas):** Evolución mensual de ingresos, gastos y utilidad neta, destacando el superávit constante de marzo a diciembre ($>\$84,000\text{ MXN/mes}$).
2. **Gráfica 2 (Barras Horizontales):** Ranking de captación mensual por inmueble (*Aguacatera*, *Ceibas* y *Carlos Chávez* concentran el $53.5\%$).
3. **Gráfica 3 (Circular / Pastel):** Composición porcentual sincronizada en tiempo real con las tarjetas KPI ($67.1\%$ utilidad neta vs. $32.9\%$ gastos en 12 meses; $62.5\%$ vs. $37.5\%$ en 10 meses).
4. **Gráfica 4 (Histogramas con Regla de Sturges):**
   * *Panel Izquierdo (Distribución del Ticket de Cobro Diario):* Sobre $n = 4,113$ cobros positivos de la bitácora diaria, la Regla de Sturges define $k = 1 + \lceil\log_2(4113)\rceil = 13\text{ bins}$.
   * *Panel Derecho (Distribución de la Utilidad Mensual):* Sobre $n = 132$ registros mensuales, $k = 1 + \lceil\log_2(132)\rceil = 9\text{ bins}$, donde el $84.8\%$ de los meses-activo opera en superávit.
5. **Gráfica 5 (Boxplot):** Dispersión de gastos operativos por categoría de activo.
6. **Gráfica 6 (Dispersión y Regresión Lineal):** Valor comercial vs. renta mensual ($R = 0.80$), identificando la subvaluación de *Gasera 1* ($1.2\%$ anual).
7. **Gráfica 7 (Mapa de Calor):** Matriz de correlación de Pearson ($r = -0.94$ entre gasto y utilidad) y semáforo cruzado Activo × Mes.
8. **Gráfica 8 (Análisis Espectral con FFT sobre Serie Diaria):**
   * Se aplica `np.fft.rfft` directamente sobre la serie diaria agregada de `clean/bitacora_diaria_portafolio_clean.csv` ($457\text{ días}$, $5,027\text{ registros}$), sin inyectar ondas artificiales en el script de visualización.
   * El periodograma ($T = 1/f$) demuestra los tres ciclos operativos del negocio: **$\sim 7.0\text{ días}$ (semanal)**, **$\sim 15.2\text{ días}$ (quincenal)** y **$\sim 30.4\text{ días}$ (mensual)**.
9. **Gráfica 9 (Dona Patrimonial):** Composición del portafolio de $\$24.65\text{M MXN}$ por categoría.
