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

DEFAULT_CLEAN_CLOUD_URL = (
    'https://raw.githubusercontent.com/luishinojosacorona123-spec/taacos/main/clean/taller_mecanico_clean.csv'
)

DEFAULT_RAW_CLOUD_URL = (
    'https://raw.githubusercontent.com/luishinojosacorona123-spec/taacos/main/raw/taller_mecanico_raw.csv'
)


def etl_clean_pipeline(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Pipeline ETL: Transforma datos de la zona raw/ a la zona clean/.

    Elimina registros cancelados, limpia columnas vacías, formatea tipos de
    datos y genera variables temporales.
    """
    df = df_raw.copy()
    df = df.drop(columns=[col for col in df.columns if str(col).strip() == ''])

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

    if 'estado_servicio' in df.columns:
        df_clean = df[df['estado_servicio'] != 'Cancelado'].copy()
    else:
        df_clean = df.copy()

    num_cols = [
        'costo_total_mxn',
        'costo_refacciones_mxn',
        'costo_mano_obra_mxn',
        'duracion_horas',
        'kilometraje',
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

    if 'marca_vehiculo' not in df_clean.columns:
        df_clean['marca_vehiculo'] = 'Desconocida'

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

with st.expander(
    '📂 Ingesta de datos a la zona `raw/` (Cargar archivo CSV)', expanded=False
):
    st.write(
        'Carga cualquier archivo CSV en bruto. El sistema lo recibirá en la zona'
        ' **raw/**, ejecutará la depuración automática y lo presentará en la'
        ' zona **clean/**.'
    )
    uploaded_main_file = st.file_uploader(
        'Selecciona el archivo para ingesta raw/:',
        type=['csv'],
        key='main_raw_uploader',
    )

active_upload = uploaded_main_file or uploaded_raw_file

if active_upload is not None:
    st.info(
        f'📥 **Zona `raw/`:** Archivo `{active_upload.name}` ingresado tal como'
        ' llegó.'
    )
    df_raw = pd.read_csv(active_upload)
    df = etl_clean_pipeline(df_raw)
    st.success(
        f'✨ **Zona `clean/`:** Depuración completada. '
        f'{len(df_raw)} registros en raw/ ➔ {len(df)} registros válidos en'
        ' clean/.'
    )
else:
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
marca_top = (
    df['marca_vehiculo'].value_counts().index[0]
    if 'marca_vehiculo' in df.columns and not df['marca_vehiculo'].empty
    else 'N/A'
)
marca_top_cant = (
    df['marca_vehiculo'].value_counts().iloc[0]
    if 'marca_vehiculo' in df.columns and not df['marca_vehiculo'].empty
    else 0
)

servicio_top = (
    df['tipo_servicio'].value_counts().index[0]
    if 'tipo_servicio' in df.columns and not df['tipo_servicio'].empty
    else 'N/A'
)
servicio_top_cant = (
    df['tipo_servicio'].value_counts().iloc[0]
    if 'tipo_servicio' in df.columns and not df['tipo_servicio'].empty
    else 0
)

km_promedio = (
    df['kilometraje'].mean()
    if 'kilometraje' in df.columns and len(df['kilometraje']) > 0
    else 0.0
)

k1, k2, k3, k4 = st.columns(4)
k1.metric('Ventas Totales del Periodo', f'${ventas_totales:,.2f} MXN')
k2.metric(
    'Marca Más Atendida',
    str(marca_top),
    f'{marca_top_cant:,} servicios realizados',
)
k3.metric(
    'Servicio Más Solicitado',
    str(servicio_top),
    f'{servicio_top_cant:,} solicitudes',
)
k4.metric('Kilometraje Promedio', f'{km_promedio:,.0f} km')

st.markdown('---')

# ----------------- VISUALIZACIONES EN FORMATO RETICULAR (6 PREGUNTAS) -----------------
c1, c2 = st.columns(2)

# Gráfica 1: ¿Qué marca de auto es el que ha ocupado más servicio?
with c1:
    st.subheader('¿Qué marca de auto es la que ha ocupado más servicio?')
    fig, ax = plt.subplots(figsize=(8, 4))
    if 'marca_vehiculo' in df.columns and not df['marca_vehiculo'].empty:
        marcas_count = df['marca_vehiculo'].value_counts()
        marcas_count.plot(kind='bar', ax=ax, color='#1f77b4')
        ax.set_ylabel('Cantidad de Servicios')
        ax.set_xlabel('Marca de Vehículo')
        ax.grid(True, linestyle='--', alpha=0.5)
        plt.xticks(rotation=45, ha='right')
        for p in ax.patches:
            height = p.get_height()
            if height > 0:
                ax.annotate(
                    f'{int(height)}',
                    (p.get_x() + p.get_width() / 2.0, height),
                    ha='center',
                    va='bottom',
                    fontsize=8,
                    xytext=(0, 2),
                    textcoords='offset points',
                )
    st.pyplot(fig)

# Gráfica 2: ¿Cuáles han sido las ganancias promedio de un día, 15 días, 30 días, 1 año?
with c2:
    st.subheader(
        '¿Cuáles han sido las ganancias promedio de 1 día, 15 días, 30 días y 1'
        ' año?'
    )
    fig, ax = plt.subplots(figsize=(8, 4))
    valid_dates = df.dropna(subset=['fecha_servicio'])
    if len(valid_dates) > 0:
        daily_earnings = valid_dates.groupby('fecha_servicio')[
            'costo_total_mxn'
        ].sum()
        avg_day = daily_earnings.mean()
    else:
        avg_day = df['costo_total_mxn'].mean() if len(df) > 0 else 0.0

    periodos = ['1 Día', '15 Días', '30 Días', '1 Año']
    valores = [avg_day, avg_day * 15, avg_day * 30, avg_day * 365]
    colores = ['#2ca02c', '#1f77b4', '#ff7f0e', '#9467bd']

    bars = ax.bar(periodos, valores, color=colores)
    ax.set_ylabel('Ganancia Promedio (MXN)')
    ax.set_xlabel('Periodo de Tiempo')
    ax.grid(True, linestyle='--', alpha=0.5)
    for bar in bars:
        yval = bar.get_height()
        ax.annotate(
            f'${yval:,.0f}',
            (bar.get_x() + bar.get_width() / 2.0, yval),
            ha='center',
            va='bottom',
            fontsize=8,
            xytext=(0, 3),
            textcoords='offset points',
        )
    st.pyplot(fig)

c3, c4 = st.columns(2)

# Gráfica 3: Mayor a menor servicio solicitado
with c3:
    st.subheader(
        '¿Cuáles son los servicios más solicitados? (De mayor a menor)'
    )
    fig, ax = plt.subplots(figsize=(8, 4))
    if 'tipo_servicio' in df.columns and not df['tipo_servicio'].empty:
        servicios_ordenados = df['tipo_servicio'].value_counts(ascending=True)
        servicios_ordenados.plot(kind='barh', ax=ax, color='#ff7f0e')
        ax.set_xlabel('Cantidad de Servicios Solicitados')
        ax.set_ylabel('')
        ax.grid(True, linestyle='--', alpha=0.5)
        for p in ax.patches:
            width = p.get_width()
            if width > 0:
                ax.annotate(
                    f'{int(width)}',
                    (width, p.get_y() + p.get_height() / 2.0),
                    ha='left',
                    va='center',
                    fontsize=8,
                    xytext=(3, 0),
                    textcoords='offset points',
                )
    st.pyplot(fig)

# Gráfica 4: Comparación del costo de refacciones al costo total
with c4:
    st.subheader(
        '¿Cómo se compara el costo de refacciones respecto al costo total?'
    )
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.scatterplot(
        data=df,
        x='costo_refacciones_mxn',
        y='costo_total_mxn',
        alpha=0.6,
        color='#2ca02c',
        ax=ax,
    )
    max_ref = (
        df['costo_refacciones_mxn'].max()
        if len(df['costo_refacciones_mxn']) > 0
        else 0
    )
    ax.plot(
        [0, max_ref],
        [0, max_ref],
        color='red',
        linestyle='--',
        label='Costo Refacciones Base (sin MO)',
    )
    ax.set_xlabel('Costo de Refacciones (MXN)')
    ax.set_ylabel('Costo Total con Mano de Obra (MXN)')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend()
    st.pyplot(fig)

c5, c6 = st.columns(2)

# Gráfica 5: Duración de los servicios
with c5:
    st.subheader('¿Cuál es la duración de los servicios mecánicos?')
    fig, ax = plt.subplots(figsize=(8, 4))
    if 'duracion_horas' in df.columns and len(df['duracion_horas']) > 0:
        duracion_prom = df['duracion_horas'].mean()
        sns.histplot(
            df['duracion_horas'], bins=25, kde=True, ax=ax, color='#9467bd'
        )
        ax.axvline(
            duracion_prom,
            color='red',
            linestyle='--',
            label=f'Promedio: {duracion_prom:.1f} hrs',
        )
        ax.legend()
    ax.set_xlabel('Duración del Servicio (Horas)')
    ax.set_ylabel('Cantidad de Servicios')
    ax.grid(True, linestyle='--', alpha=0.5)
    st.pyplot(fig)

# Gráfica 6: Kilometrajes
with c6:
    st.subheader(
        '¿Cuál es la distribución de kilometrajes en los vehículos atendidos?'
    )
    fig, ax = plt.subplots(figsize=(8, 4))
    if 'kilometraje' in df.columns and len(df['kilometraje']) > 0:
        km_media = df['kilometraje'].mean()
        sns.histplot(
            df['kilometraje'], bins=30, kde=True, ax=ax, color='#d62728'
        )
        ax.axvline(
            km_media,
            color='blue',
            linestyle='--',
            label=f'Promedio: {km_media:,.0f} km',
        )
        ax.legend()
    ax.set_xlabel('Kilometraje del Vehículo (km)')
    ax.set_ylabel('Cantidad de Vehículos')
    ax.grid(True, linestyle='--', alpha=0.5)
    st.pyplot(fig)