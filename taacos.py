import io
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.fft import rfft, rfftfreq
import seaborn as sns
import streamlit as st

st.set_page_config(
    page_title='Dashboard Taller Mecánico GDL',
    layout='wide',
    initial_sidebar_state='expanded',
)


# Carga de datos flexible (soporta archivo subido o dataset local por defecto)
@st.cache_data
def load_data(file_source=None):
    if file_source is not None:
        df = pd.read_csv(file_source)
    else:
        df = pd.read_csv('taller_mecanico_gdl.csv')

    # Limpiar columnas vacías
    df = df.drop(columns=[col for col in df.columns if col.strip() == ''])

    # Procesar fecha de forma flexible
    if 'fecha_servicio' in df.columns:
        df['fecha_servicio'] = pd.to_datetime(df['fecha_servicio'], dayfirst=True, errors='coerce')
        if df['fecha_servicio'].notna().any():
            df['semana'] = df['fecha_servicio'].dt.isocalendar().week
        else:
            df['semana'] = 1
    else:
        df['fecha_servicio'] = pd.to_datetime('today')
        df['semana'] = 1

    # Filtrar registros cancelados si existe la columna
    if 'estado_servicio' in df.columns:
        df_clean = df[df['estado_servicio'] != 'Cancelado'].copy()
    else:
        df_clean = df.copy()

    # Asegurar que existan las columnas numéricas necesarias
    num_cols = ['costo_total_mxn', 'costo_refacciones_mxn', 'costo_mano_obra_mxn', 'duracion_horas']
    for col in num_cols:
        if col not in df_clean.columns:
            df_clean[col] = 0.0
        else:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0.0)

    if 'tipo_servicio' not in df_clean.columns:
        df_clean['tipo_servicio'] = 'General'

    return df_clean


# ----------------- PANEL LATERAL / SUBIDA DE ARCHIVOS -----------------
with st.sidebar:
    st.header('📂 Cargar Datos')
    uploaded_file_sidebar = st.file_uploader(
        'Sube tu archivo CSV:',
        type=['csv'],
        key='sidebar_csv',
        help='Sube un archivo CSV con las columnas de tu taller para actualizar las métricas.'
    )
    if uploaded_file_sidebar is not None:
        st.success(f'✅ Usando: {uploaded_file_sidebar.name}')
    else:
        st.info('ℹ️ Usando archivo por defecto (`taller_mecanico_gdl.csv`)')

    st.markdown('---')
    st.markdown('**Columnas esperadas en el CSV:**')
    st.caption('`fecha_servicio`, `costo_total_mxn`, `tipo_servicio`, `costo_refacciones_mxn`, `costo_mano_obra_mxn`, `duracion_horas`, `estado_servicio`')


# ----------------- ÁREA PRINCIPAL -----------------
st.title('Métricas Clave del Taller Mecánico GDL')

# Sección desplegable en la página principal para subir CSV
with st.expander('📁 ¿Deseas subir tu propio archivo CSV? Haz clic aquí', expanded=False):
    uploaded_file_main = st.file_uploader(
        'Arrastra o selecciona tu archivo CSV:',
        type=['csv'],
        key='main_csv',
        help='El archivo se procesará automáticamente para calcular todas las métricas.'
    )

# Determinar qué archivo usar (prioridad al que se haya subido)
active_file = uploaded_file_main or uploaded_file_sidebar

try:
    df = load_data(active_file)
    if active_file is not None:
        st.success(f'📊 Mostrando datos del archivo: **{active_file.name}** ({len(df)} registros procesados)')
except Exception as e:
    st.error(f'Error al procesar el archivo CSV: {e}. Mostrando datos predeterminados.')
    df = load_data(None)

# ----------------- KPI HEADER -----------------
ventas_totales = df['costo_total_mxn'].sum()
servicios_facturados = df[df['costo_total_mxn'] > 0]
ticket_promedio = servicios_facturados['costo_total_mxn'].mean() if len(servicios_facturados) > 0 else 0.0

if not df['tipo_servicio'].empty and len(df['tipo_servicio'].value_counts()) > 0:
    estrella_vol = df['tipo_servicio'].value_counts().index[0]
    estrella_rev = df.groupby('tipo_servicio')['costo_total_mxn'].sum().idxmax()
else:
    estrella_vol = 'N/A'
    estrella_rev = 'N/A'

ventas_sem = df.groupby('semana')['costo_total_mxn'].sum()
if len(ventas_sem) >= 2 and ventas_sem.iloc[-2] != 0:
    var_sem = ((ventas_sem.iloc[-1] - ventas_sem.iloc[-2]) / ventas_sem.iloc[-2]) * 100
else:
    var_sem = 0.0

k1, k2, k3, k4 = st.columns(4)
k1.metric('Ventas del Periodo', f'${ventas_totales:,.2f} MXN')
k2.metric('Ticket Promedio', f'${ticket_promedio:,.2f} MXN')
k3.metric('Servicio Estrella', str(estrella_vol), f'Líder en ingresos: {estrella_rev}')
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
        st.info('Se requieren más registros con fechas continuas para calcular el análisis FFT.')

with c6:
    st.subheader('¿Qué líneas de servicio generan mayor volumen de facturación?')
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