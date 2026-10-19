import io
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.fft import rfft, rfftfreq
import seaborn as sns
import streamlit as st

st.set_page_config(
    page_title='Dashboard Taller Mecánico GDL - Cloud Data Lakehouse',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ==============================================================================
# ARQUITECTURA DE ALMACENAMIENTO DE OBJETOS EN LA NUBE
# - Zona raw/   : Datos tal como llegaron (en bruto / sin procesar)
# - Zona clean/ : Datos depurados y validados para el consumo analítico
# EL DASHBOARD LEE SUS DATOS DIRECTAMENTE DE LA ZONA clean/ EN LA NUBE.
# ==============================================================================

# Endpoint en la nube de la zona clean/ (Object Storage)
DEFAULT_CLEAN_CLOUD_URL = (
    'https://raw.githubusercontent.com/luishinojosacorona123-spec/taacos/main/clean/taller_mecanico_clean.csv'
)

# Endpoint en la nube de la zona raw/ (Object Storage)
DEFAULT_RAW_CLOUD_URL = (
    'https://raw.githubusercontent.com/luishinojosacorona123-spec/taacos/main/raw/taller_mecanico_raw.csv'
)


def etl_clean_pipeline(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Pipeline ETL: Transforma datos de la zona raw/ a la zona clean/.

    Elimina registros cancelados, limpia columnas vacías, formatea tipos de
    datos y genera variables temporales.
    """
    df = df_raw.copy()
    # Eliminar columnas sin nombre o vacías
    df = df.drop(columns=[col for col in df.columns if str(col).strip() == ''])

    # Depuración de fechas y asignación de semana del año
    if 'fecha_servicio' in df.columns:
        df['fecha_servicio'] = pd.to_datetime(
            df['fecha_servicio'], dayfirst=True, errors='coerce'
        )
        if df['fecha_servicio'].notna().any():
            df['semana'] = df['fecha_servicio'].dt.isocalendar().week
        else:
            df['semana'] = 1
    else:
        df['fecha_servicio'] = pd.to_datetime('today')
        df['semana'] = 1

    # Regla de negocio zona clean/: Excluir servicios cancelados
    if 'estado_servicio' in df.columns:
        df_clean = df[df['estado_servicio'] != 'Cancelado'].copy()
    else:
        df_clean = df.copy()

    # Sanitización de columnas numéricas indispensables
    num_cols = [
        'costo_total_mxn',
        'costo_refacciones_mxn',
        'costo_mano_obra_mxn',
        'duracion_horas',
    ]
    for col in num_cols:
        if col not in df_clean.columns:
            df_clean[col] = 0.0
        else:
            df_clean[col] = pd.to_numeric(
                df_clean[col], errors='coerce'
            ).fillna(0.0)

    if 'tipo_servicio' not in df_clean.columns:
        df_clean['tipo_servicio'] = 'General'

    return df_clean


@st.cache_data(ttl=300)
def load_from_cloud_storage(cloud_url: str) -> pd.DataFrame:
    """Descarga y lee los datos directamente desde el almacenamiento de objetos en la nube (zona clean/).

    No lee ningún archivo local en la computadora.
    """
    df = pd.read_csv(cloud_url)
    if 'fecha_servicio' in df.columns:
        df['fecha_servicio'] = pd.to_datetime(
            df['fecha_servicio'], errors='coerce'
        )
    return df


# ----------------- PANEL LATERAL / ALMACENAMIENTO DE OBJETOS -----------------
with st.sidebar:
    st.header('☁️ Almacenamiento de Objetos')
    st.markdown("""
    **Estructura del Data Lake en la Nube:**
    - 📁 `raw/`: Datos tal como llegaron (en bruto).
    - 📁 `clean/`: Datos depurados leídos por el dashboard.
    """)

    st.markdown('---')
    st.subheader('🌐 Endpoint de la Nube (Zona `clean/`)')
    cloud_storage_url = st.text_input(
        'URL del Objeto en la Nube:',
        value=DEFAULT_CLEAN_CLOUD_URL,
        help='URL pública o PAR de Oracle Cloud Object Storage / S3 / Cloud Storage para el archivo en la zona clean/',
    )

    st.markdown('---')
    st.subheader('📥 Ingesta a Zona `raw/`')
    uploaded_raw_file = st.file_uploader(
        'Subir nuevo archivo a la zona raw/:',
        type=['csv'],
        key='sidebar_raw_uploader',
        help='El archivo se ingesta en la zona raw/, pasa por el pipeline de depuración y se carga a la zona clean/.',
    )


# ----------------- ÁREA PRINCIPAL -----------------
st.title('Métricas Clave del Taller Mecánico GDL')
st.caption(
    'Arquitectura de Almacenamiento en la Nube: Ingestión `raw/` ➔'
    ' Procesamiento ETL ➔ Consumo `clean/`'
)

# Sección opcional de ingesta en la pantalla principal
with st.expander(
    '📂 Ingesta de datos a la zona `raw/` (Cargar archivo CSV)', expanded=False
):
    st.write(
        'Carga cualquier archivo CSV en bruto. El sistema lo recibirá en la zona'
        ' **raw/**, ejecutará la depuración automática (remoción de'
        ' cancelados, formato de fechas, validación de tipos) y lo presentará'
        ' en la zona **clean/**.'
    )
    uploaded_main_file = st.file_uploader(
        'Selecciona el archivo para ingesta raw/:',
        type=['csv'],
        key='main_raw_uploader',
    )

# Determinar fuente activa: Ingesta reciente a raw/ o lectura directa de clean/ en la nube
active_upload = uploaded_main_file or uploaded_raw_file

if active_upload is not None:
    # 1. Ingesta a zona raw/
    st.info(
        f'📥 **Zona `raw/`:** Archivo `{active_upload.name}` ingresado tal como'
        ' llegó.'
    )
    df_raw = pd.read_csv(active_upload)
    # 2. Pipeline a zona clean/
    df = etl_clean_pipeline(df_raw)
    st.success(
        f'✨ **Zona `clean/`:** Depuración completada. '
        f'{len(df_raw)} registros en raw/ ➔ {len(df)} registros válidos en'
        ' clean/.'
    )
else:
    # Lectura directa desde el almacenamiento de objetos en la nube (zona clean/)
    try:
        with st.spinner(
            'Conectando al almacenamiento de objetos en la nube (zona'
            ' clean/)...'
        ):
            df = load_from_cloud_storage(cloud_storage_url)
        st.success(
            '☁️ **Conectado a la nube:** Datos leídos exitosamente desde la zona'
            f' `clean/` ({len(df)} registros).'
        )
    except Exception as e:
        st.error(
            f'Error al conectar con el almacenamiento de objetos: {e}.'
            ' Intentando con endpoint de respaldo en la nube...'
        )
        df = load_from_cloud_storage(DEFAULT_CLEAN_CLOUD_URL)

# ----------------- KPI HEADER -----------------
ventas_totales = df['costo_total_mxn'].sum()
servicios_facturados = df[df['costo_total_mxn'] > 0]
ticket_promedio = (
    servicios_facturados['costo_total_mxn'].mean()
    if len(servicios_facturados) > 0
    else 0.0
)

if not df['tipo_servicio'].empty and len(df['tipo_servicio'].value_counts()) > 0:
    estrella_vol = df['tipo_servicio'].value_counts().index[0]
    estrella_rev = df.groupby('tipo_servicio')['costo_total_mxn'].sum().idxmax()
else:
    estrella_vol = 'N/A'
    estrella_rev = 'N/A'

ventas_sem = df.groupby('semana')['costo_total_mxn'].sum()
if len(ventas_sem) >= 2 and ventas_sem.iloc[-2] != 0:
    var_sem = (
        (ventas_sem.iloc[-1] - ventas_sem.iloc[-2]) / ventas_sem.iloc[-2]
    ) * 100
else:
    var_sem = 0.0

k1, k2, k3, k4 = st.columns(4)
k1.metric('Ventas del Periodo', f'${ventas_totales:,.2f} MXN')
k2.metric('Ticket Promedio', f'${ticket_promedio:,.2f} MXN')
k3.metric(
    'Servicio Estrella', str(estrella_vol), f'Líder en ingresos: {estrella_rev}'
)
k4.metric('Variación Semanal', f'{var_sem:.1f}%', delta=f'{var_sem:.1f}%')

st.markdown('---')

# ----------------- VISUALIZACIONES -----------------
c1, c2 = st.columns(2)

with c1:
    st.subheader('¿Cómo evoluciona la facturación semana a semana?')
    fig, ax = plt.subplots(figsize=(8, 4))
    if len(ventas_sem) > 0:
        ventas_sem.plot(kind='line', marker='o', ax=ax, color='#1f77b4')
    ax.set_ylabel('MXN')
    ax.set_xlabel('Semana del Año')
    ax.grid(True, linestyle='--', alpha=0.5)
    st.pyplot(fig)

with c2:
    st.subheader('¿Cuál es la concentración de importes por ticket?')
    fig, ax = plt.subplots(figsize=(8, 4))
    if len(df['costo_total_mxn']) > 0:
        sns.histplot(
            df['costo_total_mxn'], bins=30, kde=True, ax=ax, color='#2ca02c'
        )
        ax.axvline(
            ticket_promedio,
            color='red',
            linestyle='--',
            label=f'Promedio: ${ticket_promedio:,.0f}',
        )
        ax.legend()
    ax.set_xlabel('Costo Total (MXN)')
    st.pyplot(fig)

c3, c4 = st.columns(2)

with c3:
    st.subheader('¿Qué variables explican el costo de las reparaciones?')
    fig, ax = plt.subplots(figsize=(8, 4))
    corr_cols = [
        'costo_refacciones_mxn',
        'costo_mano_obra_mxn',
        'costo_total_mxn',
        'duracion_horas',
    ]
    sns.heatmap(
        df[corr_cols].corr(), annot=True, cmap='Blues', fmt='.2f', ax=ax
    )
    st.pyplot(fig)

with c4:
    st.subheader('¿La mano de obra cobrada es lineal respecto al tiempo?')
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.scatterplot(
        data=df,
        x='duracion_horas',
        y='costo_mano_obra_mxn',
        hue='tipo_servicio',
        legend=False,
        ax=ax,
    )
    ax.set_xlabel('Duración (Horas)')
    ax.set_ylabel('Mano de Obra (MXN)')
    st.pyplot(fig)

c5, c6 = st.columns(2)

with c5:
    st.subheader(
        '¿Qué periodicidad domina los ingresos? (Análisis Espectral FFT)'
    )
    valid_dates = df.dropna(subset=['fecha_servicio'])
    if len(valid_dates) > 5 and valid_dates['fecha_servicio'].nunique() > 2:
        daily_series = (
            df.groupby('fecha_servicio')['costo_total_mxn']
            .sum()
            .reindex(
                pd.date_range(
                    df['fecha_servicio'].min(), df['fecha_servicio'].max()
                ),
                fill_value=0,
            )
        )
        N = len(daily_series)
        yf = rfft(daily_series.values - daily_series.values.mean())
        xf = rfftfreq(N, 1.0)
        periods = 1 / xf[1:]
        amplitudes = np.abs(yf[1:])

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(periods, amplitudes, color='#9467bd', lw=1.5)
        ax.set_xlim(1, 35)
        ax.set_xlabel('Ciclo (Días)')
        ax.set_ylabel('Amplitud')
        ax.axvline(7, color='orange', linestyle=':', label='Ciclo Semanal (7d)')
        ax.axvline(15, color='green', linestyle=':', label='Ciclo Quincenal (~15d)')
        ax.legend()
        st.pyplot(fig)
    else:
        st.info(
            'Se requieren más registros con fechas continuas para calcular el'
            ' análisis FFT.'
        )

with c6:
    st.subheader(
        '¿Qué líneas de servicio generan mayor volumen de facturación?'
    )
    fig, ax = plt.subplots(figsize=(8, 4))
    if not df['tipo_servicio'].empty:
        ingresos_cat = (
            df.groupby('tipo_servicio')['costo_total_mxn']
            .sum()
            .sort_values(ascending=True)
        )
        ingresos_cat.plot(kind='barh', ax=ax, color='#d62728')
    ax.set_xlabel('Total Facturado (MXN)')
    ax.set_ylabel('')
    st.pyplot(fig)