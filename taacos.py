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
# 1. ARQUITECTURA DE ALMACENAMIENTO DE OBJETOS EN LA NUBE
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


# ==============================================================================
# 2. CAPA DE BACKEND: CARGA Y LIMPIEZA DE DATOS CON @st.cache_data
# ==============================================================================

@st.cache_data(ttl=600, show_spinner=False)
def load_and_clean_data(cloud_url: str) -> pd.DataFrame:
    """Capa de Backend:

    Descarga los datos directamente desde el almacenamiento de objetos en la
    nube (zona clean/), ejecuta la sanitización, conversión de tipos de datos,
    manejo de valores atípicos y almacena en caché en memoria.
    """
    df = pd.read_csv(cloud_url)

    # 1. Depuración de nombres de columnas
    df = df.drop(columns=[col for col in df.columns if str(col).strip() == ''])

    # 2. Conversión robusta de fechas y generación de semanas
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

    # 3. Filtrado lógico: exclusión de servicios cancelados
    if 'estado_servicio' in df.columns:
        df_clean = df[df['estado_servicio'] != 'Cancelado'].copy()
    else:
        df_clean = df.copy()

    # 4. Saneamiento de columnas numéricas indispensables
    num_cols = [
        'costo_total_mxn',
        'costo_refacciones_mxn',
        'costo_mano_obra_mxn',
        'duracion_horas',
        'kilometraje',
    ]
    for col in num_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(
                df_clean[col], errors='coerce'
            ).fillna(0.0)
        else:
            df_clean[col] = 0.0

    if 'tipo_servicio' not in df_clean.columns:
        df_clean['tipo_servicio'] = 'General'

    if 'marca_vehiculo' not in df_clean.columns:
        df_clean['marca_vehiculo'] = 'Desconocida'

    return df_clean


@st.cache_data(show_spinner=False)
def etl_clean_pipeline(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Capa de Backend (Pipeline ETL):

    Transforma datos recién ingresados en la zona raw/ hacia la zona clean/.
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
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(
                df_clean[col], errors='coerce'
            ).fillna(0.0)
        else:
            df_clean[col] = 0.0

    if 'tipo_servicio' not in df_clean.columns:
        df_clean['tipo_servicio'] = 'General'

    if 'marca_vehiculo' not in df_clean.columns:
        df_clean['marca_vehiculo'] = 'Desconocida'

    return df_clean


# ==============================================================================
# 3. CAPA DE FRONTEND: CONFIGURACIÓN, INGESTA Y WIDGETS DE FILTRADO
# ==============================================================================

with st.sidebar:
    st.header('☁️ Almacenamiento en la Nube')
    st.markdown("""
    **Zonas de Almacenamiento (Data Lake):**
    - 📁 `raw/`: Datos tal como llegaron.
    - 📁 `clean/`: Datos depurados leídos por el dashboard.
    """)

    cloud_storage_url = st.text_input(
        '🌐 Endpoint de la Nube (Zona `clean/`):',
        value=DEFAULT_CLEAN_CLOUD_URL,
        help='URL pública o PAR de Oracle Cloud Object Storage / S3 para el archivo en la zona clean/',
    )

    uploaded_raw_file = st.file_uploader(
        '📥 Ingesta a Zona `raw/` (Nuevo CSV):',
        type=['csv'],
        key='sidebar_raw_uploader',
        help='El archivo se ingesta en la zona raw/, pasa por el pipeline backend y se carga a la zona clean/.',
    )


# ----------------- EJECUCIÓN DEL BACKEND (CARGA) -----------------
active_upload = uploaded_raw_file

if active_upload is not None:
    try:
        df_raw = pd.read_csv(active_upload)
        df_base = etl_clean_pipeline(df_raw)
        st.sidebar.success(
            f'✅ Archivo `{active_upload.name}` procesado: {len(df_base)}'
            ' registros en clean/'
        )
    except Exception as e:
        st.sidebar.error(f'Error al procesar archivo: {e}')
        df_base = load_and_clean_data(DEFAULT_CLEAN_CLOUD_URL)
else:
    try:
        df_base = load_and_clean_data(cloud_storage_url)
    except Exception as e:
        st.sidebar.error(
            f'Error al conectar con la nube: {e}. Usando endpoint de respaldo...'
        )
        df_base = load_and_clean_data(DEFAULT_CLEAN_CLOUD_URL)


# ----------------- WIDGETS DE FILTRADO INTERACTIVO (FRONTEND) -----------------
with st.sidebar:
    st.markdown('---')
    st.header('🎯 Filtros Interactivos')

    # Widget 1: Rango de Fechas
    fechas_validas = df_base['fecha_servicio'].dropna()
    if not fechas_validas.empty:
        min_date = fechas_validas.min().date()
        max_date = fechas_validas.max().date()
    else:
        min_date = pd.to_datetime('2024-01-01').date()
        max_date = pd.to_datetime('2024-12-31').date()

    filtro_fechas = st.date_input(
        '📅 Rango de Fechas:',
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        help='Selecciona la fecha inicial y final para acotar el análisis.',
    )

    # Widget 2: Tipo de Servicio (Multiselect)
    servicios_disponibles = sorted(df_base['tipo_servicio'].dropna().unique())
    filtro_servicios = st.multiselect(
        '🔧 Tipo de Servicio:',
        options=servicios_disponibles,
        default=servicios_disponibles,
        help='Filtra uno o varios tipos de servicio específicos.',
    )

    # Widget 3: Marca de Vehículo (Multiselect)
    marcas_disponibles = sorted(df_base['marca_vehiculo'].dropna().unique())
    filtro_marcas = st.multiselect(
        '🚗 Marca de Vehículo:',
        options=marcas_disponibles,
        default=marcas_disponibles,
        help='Filtra por marcas de automóviles.',
    )

    # Botón de Restablecimiento
    if st.button('🔄 Restablecer Filtros'):
        st.rerun()


# ----------------- APLICACIÓN DE FILTROS AL CONJUNTO DE DATOS -----------------
df_filtered = df_base.copy()

# 1. Aplicar filtro de fechas
if isinstance(filtro_fechas, tuple) and len(filtro_fechas) == 2:
    f_inicio, f_fin = filtro_fechas
    df_filtered = df_filtered[
        (df_filtered['fecha_servicio'].dt.date >= f_inicio)
        & (df_filtered['fecha_servicio'].dt.date <= f_fin)
    ]
elif isinstance(filtro_fechas, tuple) and len(filtro_fechas) == 1:
    df_filtered = df_filtered[
        df_filtered['fecha_servicio'].dt.date == filtro_fechas[0]
    ]

# 2. Aplicar filtro de tipos de servicio
if filtro_servicios:
    df_filtered = df_filtered[
        df_filtered['tipo_servicio'].isin(filtro_servicios)
    ]
else:
    df_filtered = df_filtered.iloc[0:0]  # Vacío si deselecciona todo

# 3. Aplicar filtro de marcas
if filtro_marcas:
    df_filtered = df_filtered[df_filtered['marca_vehiculo'].isin(filtro_marcas)]
else:
    df_filtered = df_filtered.iloc[0:0]


# ==============================================================================
# ÁREA PRINCIPAL: KPIs Y GRÁFICOS INTERACTIVOS (FRONTEND)
# ==============================================================================

# Determinar el período global del dataset (formato: Año(Mes)-Año(Mes))
MESES_ES = {
    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
    5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
}
fechas_dataset = df_base['fecha_servicio'].dropna()
if not fechas_dataset.empty:
    min_f = fechas_dataset.min()
    max_f = fechas_dataset.max()
    periodo_dataset = f"{min_f.year}({MESES_ES.get(min_f.month, '')})-{max_f.year}({MESES_ES.get(max_f.month, '')})"
else:
    periodo_dataset = "2024(enero)-2024(diciembre)"

st.title(f'Métricas Clave del Taller Mecánico GDL {periodo_dataset}')
st.caption(
    'Cloud Data Lakehouse: Ingesta `raw/` ➔ Backend ETL `@st.cache_data` ➔'
    f' Visualización Dinámica ({len(df_filtered):,} de {len(df_base):,} registros'
    ' mostrados)'
)

# Control de caso borde: Sin registros seleccionados
if df_filtered.empty:
    st.warning(
        '⚠️ No se encontraron registros que coincidan con los filtros'
        ' seleccionados. Por favor selecciona al menos un tipo de servicio,'
        ' marca o amplía el rango de fechas en la barra lateral.'
    )
    st.stop()

# ----------------- KPI HEADER DINÁMICO -----------------
ventas_totales = df_filtered['costo_total_mxn'].sum()
servicios_facturados = df_filtered[df_filtered['costo_total_mxn'] > 0]
ticket_promedio = (
    servicios_facturados['costo_total_mxn'].mean()
    if len(servicios_facturados) > 0
    else 0.0
)

if (
    not df_filtered['tipo_servicio'].empty
    and len(df_filtered['tipo_servicio'].value_counts()) > 0
):
    estrella_vol = df_filtered['tipo_servicio'].value_counts().index[0]
    estrella_rev = (
        df_filtered.groupby('tipo_servicio')['costo_total_mxn'].sum().idxmax()
    )
else:
    estrella_vol = 'N/A'
    estrella_rev = 'N/A'

ventas_sem = df_filtered.groupby('semana')['costo_total_mxn'].sum()
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

# ----------------- VISUALIZACIONES (SEABORN / MATPLOTLIB CON st.pyplot) -----------------
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
    if len(df_filtered['costo_total_mxn']) > 0:
        sns.histplot(
            df_filtered['costo_total_mxn'],
            bins=30,
            kde=True,
            ax=ax,
            color='#2ca02c',
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
    # Comprobar que haya suficientes columnas con varianza para correlación
    valid_corr_cols = [
        c
        for c in corr_cols
        if c in df_filtered.columns and df_filtered[c].std() > 0
    ]
    if len(valid_corr_cols) >= 2:
        sns.heatmap(
            df_filtered[valid_corr_cols].corr(),
            annot=True,
            cmap='Blues',
            fmt='.2f',
            ax=ax,
        )
    else:
        ax.text(
            0.5,
            0.5,
            'Datos insuficientes para correlación con los filtros aplicados',
            ha='center',
            va='center',
        )
    st.pyplot(fig)

with c4:
    st.subheader('¿La mano de obra cobrada es lineal respecto al tiempo?')
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.scatterplot(
        data=df_filtered,
        x='duracion_horas',
        y='costo_mano_obra_mxn',
        hue='tipo_servicio',
        legend=False,
        ax=ax,
    )
    ax.set_xlabel('Duración (Horas)')
    ax.set_ylabel('Mano de Obra (MXN)')
    ax.grid(True, linestyle='--', alpha=0.5)
    st.pyplot(fig)

c5, c6 = st.columns(2)

with c5:
    st.subheader(
        '¿Qué periodicidad domina los ingresos? (Análisis Espectral FFT)'
    )
    valid_dates = df_filtered.dropna(subset=['fecha_servicio'])
    if len(valid_dates) > 5 and valid_dates['fecha_servicio'].nunique() > 2:
        daily_series = (
            df_filtered.groupby('fecha_servicio')['costo_total_mxn']
            .sum()
            .reindex(
                pd.date_range(
                    df_filtered['fecha_servicio'].min(),
                    df_filtered['fecha_servicio'].max(),
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
            ' análisis FFT en este rango filtrado.'
        )

with c6:
    st.subheader(
        '¿Qué líneas de servicio generan mayor volumen de facturación?'
    )
    fig, ax = plt.subplots(figsize=(8, 4))
    if not df_filtered['tipo_servicio'].empty:
        ingresos_cat = (
            df_filtered.groupby('tipo_servicio')['costo_total_mxn']
            .sum()
            .sort_values(ascending=True)
        )
        ingresos_cat.plot(kind='barh', ax=ax, color='#d62728')
    ax.set_xlabel('Total Facturado (MXN)')
    ax.set_ylabel('')
    ax.grid(True, linestyle='--', alpha=0.5)
    st.pyplot(fig)