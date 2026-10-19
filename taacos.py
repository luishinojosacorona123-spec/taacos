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
    initial_sidebar_state='collapsed',
)


# Carga desde nube (S3/GCS o zona clean)
@st.cache_data
def load_data():
  # Simula lectura de zona 'clean/' (o bucket S3: 's3://taller-data/clean/data.parquet')
  df = pd.read_csv('taller_mecanico_gdl.csv')
  df = df.drop(columns=[col for col in df.columns if col.strip() == ''])
  df['fecha_servicio'] = pd.to_datetime(df['fecha_servicio'], format='%d/%m/%Y')
  # Depuración lógica
  df_clean = df[df['estado_servicio'] != 'Cancelado'].copy()
  df_clean['semana'] = df_clean['fecha_servicio'].dt.isocalendar().week
  return df_clean


df = load_data()

# ----------------- KPI HEADER -----------------
st.title('Métricas Clave del Taller Mecánico GDL')

ventas_totales = df['costo_total_mxn'].sum()
servicios_facturados = df[df['costo_total_mxn'] > 0]
ticket_promedio = servicios_facturados['costo_total_mxn'].mean()
estrella_vol = df['tipo_servicio'].value_counts().index[0]
estrella_rev = (
    df.groupby('tipo_servicio')['costo_total_mxn'].sum().idxmax()
)

ventas_sem = df.groupby('semana')['costo_total_mxn'].sum()
var_sem = (
    (ventas_sem.iloc[-1] - ventas_sem.iloc[-2]) / ventas_sem.iloc[-2]
) * 100

k1, k2, k3, k4 = st.columns(4)
k1.metric('Ventas del Periodo', f'${ventas_totales:,.2f} MXN')
k2.metric('Ticket Promedio', f'${ticket_promedio:,.2f} MXN')
k3.metric('Servicio Estrella', estrella_vol, f'Líder en ingresos: {estrella_rev}')
k4.metric('Variación Semanal', f'{var_sem:.1f}%', delta=f'{var_sem:.1f}%')

st.markdown('---')

# ----------------- VISUALIZACIONES -----------------
c1, c2 = st.columns(2)

with c1:
  st.subheader('¿Cómo evoluciona la facturación semana a semana?')
  fig, ax = plt.subplots(figsize=(8, 4))
  ventas_sem.plot(kind='line', marker='o', ax=ax, color='#1f77b4')
  ax.set_ylabel('MXN')
  ax.set_xlabel('Semana del Año')
  ax.grid(True, linestyle='--', alpha=0.5)
  st.pyplot(fig)

with c2:
  st.subheader('¿Cuál es la concentración de importes por ticket?')
  fig, ax = plt.subplots(figsize=(8, 4))
  sns.histplot(
      df['costo_total_mxn'], bins=30, kde=True, ax=ax, color='#2ca02c'
  )
  ax.axvline(
      ticket_promedio,
      color='red',
      linestyle='--',
      label=f'Promedio: ${ticket_promedio:,.0f}',
  )
  ax.set_xlabel('Costo Total (MXN)')
  ax.legend()
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

with c6:
  st.subheader('¿Qué líneas de servicio generan mayor volumen de facturación?')
  ingresos_cat = (
      df.groupby('tipo_servicio')['costo_total_mxn']
      .sum()
      .sort_values(ascending=True)
  )
  fig, ax = plt.subplots(figsize=(8, 4))
  ingresos_cat.plot(kind='barh', ax=ax, color='#d62728')
  ax.set_xlabel('Total Facturado (MXN)')
  ax.set_ylabel('')
  st.pyplot(fig)