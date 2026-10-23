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

def parse_dates_robust(series: pd.Series) -> pd.Series:
    """Parsea fechas de forma precisa dando prioridad al formato día/mes/año (DD/MM/YYYY)."""
    parsed = pd.to_datetime(series, format='%d/%m/%Y', errors='coerce')
    if parsed.isna().all() or parsed.isna().sum() > len(series) * 0.2:
        parsed = pd.to_datetime(series, errors='coerce')
    return parsed


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
        df['fecha_servicio'] = parse_dates_robust(df['fecha_servicio'])
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
        df['fecha_servicio'] = parse_dates_robust(df['fecha_servicio'])
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

# Cálculo de variación mensual
MESES_ABREV = {
    1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr',
    5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Ago',
    9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
}
if not df_filtered.empty and df_filtered['fecha_servicio'].notna().any():
    df_temp_kpi = df_filtered.dropna(subset=['fecha_servicio'])
    ventas_mes_kpi = df_temp_kpi.groupby(df_temp_kpi['fecha_servicio'].dt.to_period('M'))['costo_total_mxn'].sum()
    if len(ventas_mes_kpi) >= 2 and ventas_mes_kpi.iloc[-2] != 0:
        var_mes = ((ventas_mes_kpi.iloc[-1] - ventas_mes_kpi.iloc[-2]) / ventas_mes_kpi.iloc[-2]) * 100
    else:
        var_mes = 0.0
else:
    var_mes = 0.0

k1, k2, k3, k4 = st.columns(4)
k1.metric('Ventas del Periodo', f'${ventas_totales:,.2f} MXN')
k2.metric('Ticket Promedio', f'${ticket_promedio:,.2f} MXN')
k3.metric(
    'Servicio Estrella', str(estrella_vol), f'Líder en ingresos: {estrella_rev}'
)
k4.metric('Variación Mensual', f'{var_mes:.1f}%', delta=f'{var_mes:.1f}%')

st.markdown('---')

# ----------------- VISUALIZACIONES (SEABORN / MATPLOTLIB CON st.pyplot) -----------------
c1, c2 = st.columns(2)

with c1:
    st.subheader('¿Cómo evoluciona la facturación mes a mes?')
    fig, ax = plt.subplots(figsize=(8, 4))
    if not df_filtered.empty and df_filtered['fecha_servicio'].notna().any():
        df_temp = df_filtered.dropna(subset=['fecha_servicio'])
        periodos_mes = df_temp['fecha_servicio'].dt.to_period('M')
        ventas_mes = df_temp.groupby(periodos_mes)['costo_total_mxn'].sum()

        multi_year = df_temp['fecha_servicio'].dt.year.nunique() > 1
        nombres_eje = [
            f"{MESES_ABREV[p.month]} {p.year}" if multi_year else MESES_ABREV[p.month]
            for p in ventas_mes.index
        ]

        ax.plot(nombres_eje, ventas_mes.values, marker='o', color='#1f77b4', linewidth=2)
        ax.set_ylabel('MXN')
        ax.set_xlabel('Mes')
        ax.grid(True, linestyle='--', alpha=0.5)
        plt.xticks(rotation=45 if len(nombres_eje) > 8 else 0)
    st.pyplot(fig)

with c2:
    st.subheader('¿Cómo se distribuye y varía el costo según el tipo de servicio?')
    fig, ax = plt.subplots(figsize=(8, 4))
    if not df_filtered.empty and 'tipo_servicio' in df_filtered.columns and len(df_filtered) > 0:
        orden_servicios = (
            df_filtered.groupby('tipo_servicio')['costo_total_mxn']
            .median()
            .sort_values(ascending=False)
            .index
        )
        sns.boxplot(
            data=df_filtered,
            x='costo_total_mxn',
            y='tipo_servicio',
            order=orden_servicios,
            color='#3182bd',
            boxprops=dict(alpha=0.75),
            ax=ax,
            fliersize=3,
            linewidth=1.2,
        )
        ax.set_xlabel('Costo Total (MXN)')
        ax.set_ylabel('')
        ax.xaxis.set_major_formatter('${x:,.0f}')
        ax.grid(True, linestyle='--', alpha=0.5)
    st.pyplot(fig)

c3, c4 = st.columns(2)

with c3:
    st.subheader('¿Cómo se distribuye el costo total? (Refacciones vs. Mano de Obra)')
    fig, ax = plt.subplots(figsize=(8, 4))
    costo_ref = df_filtered['costo_refacciones_mxn'].sum()
    costo_mo = df_filtered['costo_mano_obra_mxn'].sum()
    total_costos = costo_ref + costo_mo

    if total_costos > 0:
        etiquetas = ['Refacciones', 'Mano de Obra']
        valores = [costo_ref, costo_mo]
        colores = ['#1f77b4', '#ff7f0e']
        explode = (0.05, 0)

        wedges, texts, autotexts = ax.pie(
            valores,
            labels=etiquetas,
            autopct='%1.1f%%',
            startangle=90,
            colors=colores,
            explode=explode,
            textprops={'fontsize': 10},
            wedgeprops={'edgecolor': 'white', 'linewidth': 1.5},
        )
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_weight('bold')
        ax.axis('equal')
        ax.legend(
            labels=[
                f'{etiquetas[0]}: ${costo_ref:,.2f} MXN',
                f'{etiquetas[1]}: ${costo_mo:,.2f} MXN',
            ],
            loc='upper right',
            fontsize=8,
        )
    else:
        ax.text(
            0.5,
            0.5,
            'Sin datos de costos para los filtros seleccionados',
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
    st.subheader('¿Cada cuántos días se repiten los picos de mayor facturación?')
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
        ax.axvline(30, color='red', linestyle=':', label='Ciclo Mensual (~30d)')
        ax.grid(True, linestyle='--', alpha=0.5)
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