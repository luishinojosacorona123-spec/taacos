# Dashboard de Gestión de Portafolio Inmobiliario y Rentas 🏢📈 (DATA STARTUP — TAACOS)

Dashboard interactivo, plataforma en la nube y motor predictivo desarrollado en Streamlit y AWS para el monitoreo financiero, control de flujo de caja, gastos operativos y valuación patrimonial de **11 activos inmobiliarios y operativos reales** en **Colima, Villa de Álvarez y Manzanillo** (Valuación: **$24,650,000 MXN**).

**Materias:** Cómputo en la Nube (IAD-2408) × Analítica de Datos (IAD-2403) · Ingeniería en Inteligencia Artificial  
**Documento de Propuesta (E0):** [`docs/E0-propuesta.md`](docs/E0-propuesta.md)

---

## 🚀 Requisitos e Instalación

1. Clona el repositorio:
   ```bash
   git clone https://github.com/luishinojosacorona123-spec/taacos.git
   cd taacos
   ```

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Ejecuta la aplicación del Dashboard (E1):
   ```bash
   streamlit run taacos.py
   ```

---

## 📂 Estructura del Repositorio (Arquitectura DATA STARTUP)

```text
taacos/
├── README.md                        # Descripción general, cómo se levanta y arquitectura
├── taacos.py                        # Aplicación principal del Tablero Empresarial en Streamlit
├── portafolio_inmuebles.csv         # Dataset original del portafolio inmobiliario (Enero-Octubre 2026)
├── requirements.txt                 # Dependencias de Python
├── docs/                            # Documentación técnica y entregables E0..E5
│   └── E0-propuesta.md              # Entregable E0: Lean Canvas, entrevista, cadena de preguntas e inventario
├── raw/                             # Zona raw/ del Data Lake (portafolio_inmuebles_raw.csv)
├── clean/                           # Zona clean/ del Data Lake (portafolio_inmuebles_clean.csv)
├── data/sample/                     # Muestra anonimizada del portafolio
├── notebooks/                       # Exploración, FFT, pruebas ADF/ACF/PACF y entrenamiento de modelos
├── services/
│   ├── ingesta/                     # Microservicio API FastAPI + Dockerfile (E2 -> E3)
│   ├── worker/                      # Módulo de limpieza automatizada / AWS Lambda (E2 -> E3)
│   ├── modelos/                     # Servicio de modelos /pronostico y /clasificar (E3)
│   └── tablero/                     # Contenedor de Streamlit (E3)
├── infra/terraform/                 # Infraestructura como código en AWS (S3, SQS, IAM) (E3)
├── k8s/                             # Manifiestos de Kubernetes (Deployment, Service, HPA) (E3)
└── tests/                           # Pruebas unitarias de limpieza y scripts de carga en Locust (E2 -> E3)
```

---

## 📊 Arquitectura y Preguntas Analíticas Adaptadas

El dashboard implementa la arquitectura de almacenamiento de datos (`raw/` y `clean/`) y da respuesta a las preguntas analíticas del negocio mediante visualizaciones ejecutivas:

1. **📈 Flujo de Caja y Rentas (Hero Chart)**: *¿Cómo evoluciona el flujo de caja mensual (ingresos, gastos y utilidad neta) de enero a octubre?*
2. **🏢 Ranking de Captación (Gráfica de Barras Horizontales)**: *¿Cuáles son las propiedades que generan mayor ingreso por renta mensual?*
3. **⚖️ Destino de Ingresos (Gráfica de Pastel / Pie Chart)**: *¿Cómo se distribuyen los ingresos por rentas? (Gastos Operativos vs. Ganancia Neta)*
4. **📦 Dispersión Operativa (Boxplot)**: *¿Cómo se distribuyen y varían los gastos mensuales según la categoría de activo?*
5. **⏱️ Rentabilidad y Retorno (Diagrama de Dispersión / Scatter Plot)**: *¿Existe una relación directa entre el valor comercial del inmueble y su renta mensual?*
6. **💳 Composición Patrimonial (Gráfica de Dona / Donut Chart)**: *¿Cómo se distribuye el valor patrimonial total del portafolio según el tipo de activo?*
