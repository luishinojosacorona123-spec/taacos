# RentMetrics · Plataforma de Analítica Patrimonial y Gestión de Rentas

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40%2B-red.svg)](https://streamlit.io/)
[![AWS](https://img.shields.io/badge/AWS-S3%20%7C%20SQS%20%7C%20IAM-orange.svg)](https://aws.amazon.com/)
[![Status](https://img.shields.io/badge/Status-E0%20%26%20E1%20Completed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-Academic%20Integrator-lightgrey.svg)]()

**Proyecto Integrador:** Data Startup  
**Materias:** Cómputo en la Nube (IAD-2408) & Analítica de Datos (IAD-2403)  
**Institución:** Tecnológico Nacional de México (TecNM)  
**Demostración Pública en Producción:** [https://luishinojosacorona123-spec-taacos-taacos-nuiqdn.streamlit.app/](https://luishinojosacorona123-spec-taacos-taacos-nuiqdn.streamlit.app/)

---

## Integrantes del Equipo

* **Manuel Alexander Hernández Chávez** — *Data Lead*
* **Luis Antonio Hinojosa Corona** (`@luishinojosacorona123-spec`) — *Cloud Lead*

---

## Descripción del Proyecto

**RentMetrics** es una plataforma en la nube orientada a la gestión de cobranza, control de flujo de caja y analítica predictiva de portafolios patrimoniales de arrendamiento habitacional y comercial en el estado de Colima (Colima, Villa de Álvarez y Manzanillo).

El sistema procesa y normaliza datos operativos reales de **11 activos** valorados en **$24,650,000 MXN** y una bitácora temporal de alta frecuencia (**7,018 registros limpios en 21 meses**), permitiendo a propietarios y administradores supervisar en tiempo real el flujo neto, detectar desviaciones de capital (CAPEX) y anticipar ciclos de mantenimiento mediante análisis espectral con Transformada Rápida de Fourier (FFT).

---

## Arquitectura del Sistema

```text
[ Fuentes de Datos ]
  ├── raw/portafolio_inmuebles_raw.csv (Matriz de control mensual, 11 activos)
  └── raw/bitacora_diaria_portafolio_raw.csv (7,048 registros, script oficial pags. 23-24)
           │
           ▼
[ Pipeline ETL · services/worker/limpiar_portafolio.py ]
  ├── 1. Imputacion de valores faltantes (NaN) via total / precio_unitario
  ├── 2. Eliminacion de duplicados exactos (subset fecha + producto)
  ├── 3. Normalizacion de formato y nombres canonicos Title Case
  ├── 4. Correccion de inconsistencias logicas y valores negativos (.abs())
  └── 5. Remocion y reconstruccion de valores atipicos (outliers = 999)
           │
           ▼
[ Zona Limpia · Data Lake / Almacenamiento de Objetos ]
  ├── clean/portafolio_inmuebles_clean.csv (132 registros normalizados, Ene-Dic)
  ├── clean/bitacora_diaria_portafolio_clean.csv (7,018 registros limpios, 21 meses)
  └── AWS S3: s3://taacos-datalake-colima-2026/clean/
           │
           ▼
[ Capa de Presentación y Analítica · taacos.py ]
  ├── 4 KPIs Dinamicos (Ingresos, Margen Neto, Activo Estrella, Variacion Semanal)
  ├── 9 Visualizaciones Ejecutivas (Regla de Sturges, Correlacion de Pearson)
  ├── Analisis Espectral con FFT (Ciclos dominantes a 7, 15 y 30 dias)
  └── 3 Recomendaciones Estratégicas y Auditoria Programatica
```

---

## Estructura del Repositorio

```text
taacos/
├── README.md                            # Documentación técnica principal y arquitectura
├── taacos.py                            # Aplicación interactiva del Tablero Streamlit
├── requirements.txt                     # Dependencias de producción
├── .env.example                         # Plantilla de variables de entorno (sin credenciales)
├── generar_ventas.py                    # Generador de datos sintéticos diarios (kit págs. 23-24)
├── docs/                                # Entregables y reportes técnicos
│   ├── E0-propuesta.md                  # Entregable 0: Lean Canvas, entrevista, cadena e inventario
│   └── E1-dashboard.md                  # Entregable 1: Reporte de tablero, auditoría y FFT
├── raw/                                 # Zona raw/ del Data Lake
│   ├── portafolio_inmuebles_raw.csv     # Matriz mensual original no estructurada
│   └── bitacora_diaria_portafolio_raw.csv# Bitácora diaria en bruto (7,048 registros)
├── clean/                               # Zona clean/ del Data Lake
│   ├── portafolio_inmuebles_clean.csv   # Consolidado mensual limpio (132 registros)
│   └── bitacora_diaria_portafolio_clean.csv # Bitácora limpia de 21 meses (7,018 registros)
├── data/sample/                         # Muestra anonimizada del portafolio
├── services/
│   ├── ingesta/                         # Microservicio API FastAPI (E2 -> E3)
│   └── worker/                          # Módulo de limpieza de datos (services/worker/limpiar_portafolio.py)
├── scripts/
│   └── subir_a_aws.py                   # Aprovisionamiento automatizado de bucket S3 y carga
└── tests/                               # Pruebas unitarias y de validación
```

---

## Resumen de Entregables

### Entregable 0 (E0) · Propuesta de Negocio
* **Documento:** [`docs/E0-propuesta.md`](docs/E0-propuesta.md) (Tag: `e0`)
* **Lean Canvas:** 9 bloques de negocio detallados para el sector inmobiliario y de rentas.
* **Validación con Cliente:** Entrevista presencial de 18 minutos efectuada el 14 de octubre de 2026.
* **Cadena de Preguntas:** Formulación matemática desde la necesidad del negocio hasta la variable predictiva (`monto_recaudado_mensual` y `estatus_morosidad`).
* **Arranque Técnico:** Matriz comparativa de proveedores cloud (AWS vs. GCP vs. Azure) y control presupuestal FinOps configurado en $0.00 MXN.

### Entregable 1 (E1) · Tablero Empresarial
* **Documento:** [`docs/E1-dashboard.md`](docs/E1-dashboard.md) (Tag: `e1`)
* **URL Pública:** [Streamlit Cloud](https://luishinojosacorona123-spec-taacos-taacos-nuiqdn.streamlit.app/)
* **Indicadores:** 4 KPIs dinámicos interactivos con cálculo de variación semanal y mensual.
* **Visualizaciones con Hallazgo:** 9 gráficas que responden a preguntas concretas (Líneas, Ranking en Barras, Proporción Circular, Histograma con Regla de Sturges $k = 1 + \lceil\log_2(n)\rceil$, Boxplot de gastos, Dispersión y Regresión lineal $R = 0.80$, Mapa de Calor de Pearson $r = -0.94$, Análisis Espectral con FFT y Dona patrimonial).
* **Análisis Espectral:** FFT directa sobre 638 días (`np.fft.rfft`) identificando periodicidades en 7 días (semanal), 15.2 días (quincenal) y 30.4 días (mensual).
* **Limpieza Reproducible:** Reporte cuantitativo de correcciones (40 faltantes, 30 duplicados, 25 formato, 16 lógicos, 10 atípicos).

---

## Instalación y Ejecución Local

### 1. Clonación del Repositorio
```bash
git clone https://github.com/luishinojosacorona123-spec/taacos.git
cd taacos
```

### 2. Creación del Entorno Virtual y Dependencias
```bash
python -m venv venv
# En Windows:
.\venv\Scripts\activate
# En Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Ejecución del Tablero
```bash
streamlit run taacos.py
```
El tablero estará disponible en `http://localhost:8501`.

---

## Configuración de Almacenamiento en la Nube (AWS S3)

Para sincronizar las zonas `raw/` y `clean/` con Amazon Web Services:

1. Cree su archivo `.env` a partir de la plantilla:
   ```bash
   cp .env.example .env
   ```
2. Configure sus credenciales IAM:
   ```ini
   AWS_DEFAULT_REGION=us-east-1
   AWS_S3_BUCKET=taacos-datalake-colima-2026
   AWS_ACCESS_KEY_ID=AKIA...
   AWS_SECRET_ACCESS_KEY=...
   ```
3. Ejecute el script de aprovisionamiento:
   ```bash
   python scripts/subir_a_aws.py
   ```
