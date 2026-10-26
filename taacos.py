import io
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

st.set_page_config(
    page_title='Análisis de Homicidios en México 2026 - SESNSP',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ==============================================================================
# 1. ARQUITECTURA DE ALMACENAMIENTO DE OBJETOS EN LA NUBE
# - Zona raw/   : Datos de homicidios del SESNSP (homicidios_2026_raw.csv)
# - Zona clean/ : Datos depurados y validados para el tablero (homicidios_2026_clean.csv)
# EL DASHBOARD SE ENFOCA EXCLUSIVAMENTE EN EL ANÁLISIS DE HOMICIDIOS.
# ==============================================================================

DEFAULT_CLEAN_CLOUD_URL = (
    'https://raw.githubusercontent.com/luishinojosacorona123-spec/taacos/main/clean/homicidios_2026_clean.csv'
)

DEFAULT_RAW_CLOUD_URL = (
    'https://raw.githubusercontent.com/luishinojosacorona123-spec/taacos/main/raw/homicidios_2026_raw.csv'
)

LOCAL_CLEAN_PATH = os.path.join(os.path.dirname(__file__), 'clean', 'homicidios_2026_clean.csv')
LOCAL_RAW_PATH = os.path.join(os.path.dirname(__file__), 'raw', 'homicidios_2026_raw.csv')
BACKUP_CLEAN_PATH = os.path.join(os.path.dirname(__file__), 'clean', 'incidencia_delictiva_2026_clean.csv')

MESES_OFICIALES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio']

# ==============================================================================
# 2. CAPA DE BACKEND: CARGA Y LIMPIEZA DE DATOS CON @st.cache_data
# ==============================================================================

def sanitize_and_filter_homicidios(df: pd.DataFrame) -> pd.DataFrame:
    """Estandariza los nombres de columnas y filtra exclusivamente registros de Homicidio."""
    new_cols = []
    for c in df.columns:
        c_str = str(c).strip()
        if 'Bien' in c_str or 'jur' in c_str.lower():
            new_cols.append('bien_juridico_afectado')
        elif 'Clave' in c_str or 'clave' in c_str.lower():
            new_cols.append('clave_ent')
        elif 'Entidad' in c_str or 'entidad' in c_str.lower():
            new_cols.append('entidad')
        elif 'Subtipo' in c_str or 'subtipo' in c_str.lower():
            new_cols.append('subtipo_delito')
        elif 'Tipo' in c_str or 'tipo' in c_str.lower():
            new_cols.append('tipo_delito')
        elif 'Modalidad' in c_str or 'modalidad' in c_str.lower():
            new_cols.append('modalidad')
        elif 'Añ' in c_str or 'Ano' in c_str or 'año' in c_str.lower():
            new_cols.append('anio')
        else:
            new_cols.append(c_str)
    df.columns = new_cols

    # Saneamiento de cadenas de texto
    for col in ['entidad', 'bien_juridico_afectado', 'tipo_delito', 'subtipo_delito', 'modalidad']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Saneamiento de meses numéricos
    for m in MESES_OFICIALES:
        if m in df.columns:
            df[m] = pd.to_numeric(df[m], errors='coerce').fillna(0).astype(int)
        else:
            df[m] = 0

    # FILTRO ESTRICTO: ENFOCADO EXCLUSIVAMENTE EN HOMICIDIOS
    if 'tipo_delito' in df.columns:
        df = df[df['tipo_delito'] == 'Homicidio'].copy()

    df['total_delitos'] = df[MESES_OFICIALES].sum(axis=1)
    return df


@st.cache_data(ttl=600, show_spinner=False)
def load_and_clean_data(cloud_url: str) -> pd.DataFrame:
    """Descarga los datos de homicidios directamente desde la nube o lee la copia local de respaldo."""
    df = None
    try:
        df = pd.read_csv(cloud_url, encoding='utf-8-sig')
    except Exception:
        if os.path.exists(LOCAL_CLEAN_PATH):
            df = pd.read_csv(LOCAL_CLEAN_PATH, encoding='utf-8-sig')
        elif os.path.exists(LOCAL_RAW_PATH):
            df = pd.read_csv(LOCAL_RAW_PATH, encoding='utf-8-sig')
        elif os.path.exists(BACKUP_CLEAN_PATH):
            df = pd.read_csv(BACKUP_CLEAN_PATH, encoding='utf-8-sig')

    if df is None:
        raise FileNotFoundError("No se encontró el archivo de datos de homicidios.")

    return sanitize_and_filter_homicidios(df)


@st.cache_data(show_spinner=False)
def etl_clean_pipeline(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Pipeline ETL para procesar archivos recién ingestados en la zona raw/."""
    return sanitize_and_filter_homicidios(df_raw.copy())


# ==============================================================================
# 3. CAPA DE FRONTEND: CONFIGURACIÓN, INGESTA Y WIDGETS DE FILTRADO
# ==============================================================================

with st.sidebar:
    st.header('☁️ Almacenamiento en la Nube')
    st.markdown("""
    **Zonas de Almacenamiento (Data Lakehouse):**
    - 📁 `raw/`: Datos del SESNSP tal como llegaron.
    - 📁 `clean/`: Datos depurados y filtrados de homicidios.
    """)

    cloud_storage_url = st.text_input(
        '🌐 Endpoint de la Nube (Zona `clean/`):',
        value=DEFAULT_CLEAN_CLOUD_URL,
        help='URL pública para el dataset de homicidios en la zona clean/',
    )

    uploaded_raw_file = st.file_uploader(
        '📥 Ingesta a Zona `raw/` (CSV o Excel):',
        type=['csv', 'xlsx'],
        key='sidebar_raw_uploader',
        help='Carga un archivo de datos para su procesamiento dinámico.',
    )


# ----------------- EJECUCIÓN DEL BACKEND (CARGA) -----------------
if uploaded_raw_file is not None:
    try:
        if uploaded_raw_file.name.endswith('.xlsx'):
            df_uploaded = pd.read_excel(uploaded_raw_file)
        else:
            df_uploaded = pd.read_csv(uploaded_raw_file)
        df_base = etl_clean_pipeline(df_uploaded)
        st.sidebar.success(
            f'✅ Archivo `{uploaded_raw_file.name}` procesado: {len(df_base):,} registros de homicidios.'
        )
    except Exception as e:
        st.sidebar.error(f'Error al procesar archivo: {e}')
        df_base = load_and_clean_data(DEFAULT_CLEAN_CLOUD_URL)
else:
    try:
        df_base = load_and_clean_data(cloud_storage_url)
    except Exception as e:
        st.sidebar.error(f'Error al conectar: {e}. Usando respaldo local...')
        df_base = load_and_clean_data(LOCAL_CLEAN_PATH)


# ----------------- WIDGETS DE FILTRADO INTERACTIVO (FRONTEND) -----------------
with st.sidebar:
    st.markdown('---')
    st.header('🎯 Filtros Especializados de Homicidios')

    # Widget 1: Entidades Federativas
    entidades_disponibles = sorted(df_base['entidad'].dropna().unique().tolist())
    filtro_entidades = st.multiselect(
        '📍 Entidad Federativa (Estado):',
        options=entidades_disponibles,
        default=entidades_disponibles,
        help='Selecciona una o más entidades para analizar.',
    )

    # Widget 2: Subtipo de Homicidio
    subtipos_disponibles = sorted(df_base['subtipo_delito'].dropna().unique().tolist())
    filtro_subtipos = st.multiselect(
        '⚖️ Subtipo Jurídico de Homicidio:',
        options=subtipos_disponibles,
        default=subtipos_disponibles,
        help='Filtra por homicidio doloso, culposo o tentativa.',
    )

    # Widget 3: Modalidad de Comisión
    modalidades_disponibles = sorted(
        df_base[df_base['subtipo_delito'].isin(filtro_subtipos)]['modalidad'].dropna().unique().tolist()
    ) if filtro_subtipos else sorted(df_base['modalidad'].dropna().unique().tolist())

    filtro_modalidades = st.multiselect(
        '🔫 Medio o Modalidad de Comisión:',
        options=modalidades_disponibles,
        default=modalidades_disponibles,
        help='Arma de fuego, arma blanca, accidente de tránsito, etc.',
    )

    # Widget 4: Meses a Analizar
    filtro_meses = st.multiselect(
        '📅 Meses Analizados (2026):',
        options=MESES_OFICIALES,
        default=MESES_OFICIALES,
        help='Selecciona los meses considerados en el cálculo.',
    )

    # Botón de Restablecimiento
    if st.button('🔄 Restablecer Filtros'):
        st.rerun()


# ----------------- APLICACIÓN DE FILTROS AL CONJUNTO DE DATOS -----------------
df_filtered = df_base.copy()

if filtro_entidades:
    df_filtered = df_filtered[df_filtered['entidad'].isin(filtro_entidades)]
else:
    df_filtered = df_filtered.iloc[0:0]

if filtro_subtipos:
    df_filtered = df_filtered[df_filtered['subtipo_delito'].isin(filtro_subtipos)]
else:
    df_filtered = df_filtered.iloc[0:0]

if filtro_modalidades:
    df_filtered = df_filtered[df_filtered['modalidad'].isin(filtro_modalidades)]
else:
    df_filtered = df_filtered.iloc[0:0]

meses_activos = filtro_meses if filtro_meses else MESES_OFICIALES
df_filtered['total_delitos'] = df_filtered[meses_activos].sum(axis=1)


# ==============================================================================
# ÁREA PRINCIPAL: KPIs Y GRÁFICOS INTERACTIVOS (FRONTEND)
# ==============================================================================

st.title('Tablero Especializado: Análisis de Homicidios en México 2026')
st.caption(
    'Secretariado Ejecutivo del Sistema Nacional de Seguridad Pública (SESNSP) | '
    f'Corte Enero - Julio 2026 ({len(df_filtered):,} registros filtrados de {len(df_base):,} totales)'
)

# Control de caso borde: Sin registros seleccionados
if df_filtered.empty or df_filtered['total_delitos'].sum() == 0:
    st.warning(
        '⚠️ No se encontraron registros de homicidios que coincidan con los filtros seleccionados. '
        'Por favor selecciona al menos una entidad, subtipo, modalidad y mes en la barra lateral.'
    )
    st.stop()


# ----------------- KPI HEADER DINÁMICO -----------------
total_homicidios = df_filtered['total_delitos'].sum()
num_meses_sel = len(meses_activos)
promedio_mensual = (total_homicidios / num_meses_sel) if num_meses_sel > 0 else 0

subtipo_serie = df_filtered.groupby('subtipo_delito')['total_delitos'].sum().sort_values(ascending=False)
if not subtipo_serie.empty:
    subtipo_top_nombre = subtipo_serie.index[0]
    subtipo_top_casos = subtipo_serie.iloc[0]
    subtipo_top_pct = (subtipo_top_casos / total_homicidios) * 100 if total_homicidios > 0 else 0
else:
    subtipo_top_nombre = 'N/A'
    subtipo_top_casos = 0
    subtipo_top_pct = 0

# Variación del último mes activo vs mes penúltimo
sum_meses = df_filtered[meses_activos].sum()
if len(sum_meses) >= 2 and sum_meses.iloc[-2] > 0:
    ultimo_mes_nombre = sum_meses.index[-1]
    penultimo_mes_nombre = sum_meses.index[-2]
    ultimo_mes_casos = sum_meses.iloc[-1]
    penultimo_mes_casos = sum_meses.iloc[-2]
    var_ultimo_mes = ((ultimo_mes_casos - penultimo_mes_casos) / penultimo_mes_casos) * 100
    delta_str = f"{var_ultimo_mes:+.1f}% vs {penultimo_mes_nombre}"
    ultimo_mes_label = f"Homicidios {ultimo_mes_nombre}"
    ultimo_mes_valor = f"{ultimo_mes_casos:,.0f} casos"
elif len(sum_meses) == 1:
    ultimo_mes_nombre = sum_meses.index[0]
    ultimo_mes_label = f"Homicidios {ultimo_mes_nombre}"
    ultimo_mes_valor = f"{sum_meses.iloc[0]:,.0f} casos"
    delta_str = "Mes único"
else:
    ultimo_mes_label = "Homicidios Último Mes"
    ultimo_mes_valor = "0 casos"
    delta_str = "0.0%"

k1, k2, k3, k4 = st.columns(4)
k1.metric('Total Homicidios Registrados', f'{total_homicidios:,.0f} casos')
k2.metric('Promedio Mensual', f'{promedio_mensual:,.0f} casos/mes')
k3.metric('Subtipo Prevalente', str(subtipo_top_nombre), f'{subtipo_top_casos:,.0f} casos ({subtipo_top_pct:.1f}%)')
k4.metric(ultimo_mes_label, ultimo_mes_valor, delta=delta_str)

st.markdown('---')


# ==============================================================================
# 4. PALETA DE COLOR UNIFICADA POR MODALIDAD Y SUBTIPO
# ==============================================================================
PALETA_SUBTIPOS = {
    'Homicidio culposo': '#2b6cb0',                 # Azul corporativo
    'Homicidio doloso': '#e53e3e',                  # Rojo
    'Tentativa de homicidio doloso': '#dd6b20',     # Naranja
}

PALETA_MODALIDADES = {
    'Con arma de fuego': '#e53e3e',                 # Rojo
    'En accidente de tránsito': '#2b6cb0',         # Azul
    'Con otro elemento': '#dd6b20',                 # Naranja
    'No especificado': '#718096',                   # Gris
    'Tentativa de homicidio doloso': '#319795',     # Teal
    'Con arma blanca': '#805ad5',                   # Morado
}


# ==============================================================================
# 5. JERARQUÍA VISUAL CON st.tabs Y st.columns CON TEXTOS DE APOYO (INSIGHTS)
# ==============================================================================
tab_tendencias, tab_entidades, tab_modalidades = st.tabs([
    '📈 Tendencias y Estados Críticos',
    '🔧 Análisis por Modalidad y Dispersión Estatal',
    '💳 Distribución por Medio y Modalidad (Dona)',
])

# ------------------------------------------------------------------------------
# PESTAÑA 1: TENDENCIAS Y ESTADOS CRÍTICOS (HERO CHART + BARRAS + PASTEL)
# ------------------------------------------------------------------------------
with tab_tendencias:
    # Gráfico Principal de Mayor Jerarquía Visual (Arriba y a ancho completo)
    st.subheader('¿Cómo evoluciona la cifra de homicidios mes a mes en México durante 2026?')
    fig, ax = plt.subplots(figsize=(10, 4))
    
    mensual_totales = df_filtered[meses_activos].sum()
    ax.plot(
        mensual_totales.index,
        mensual_totales.values,
        marker='o',
        color='#c53030',
        linewidth=2.5,
        markersize=7,
        label='Homicidios Registrados',
    )
    ax.fill_between(mensual_totales.index, mensual_totales.values, color='#feb2b2', alpha=0.35)
    
    for m, val in zip(mensual_totales.index, mensual_totales.values):
        ax.annotate(
            f"{val:,.0f}",
            (m, val),
            textcoords="offset points",
            xytext=(0, 8),
            ha='center',
            fontsize=8.5,
            fontweight='bold',
            color='#742a2a',
        )

    ax.set_ylabel('Número de Homicidios')
    ax.yaxis.set_major_formatter('{x:,.0f}')
    ax.grid(True, linestyle='--', alpha=0.5)
    if not mensual_totales.empty and max(mensual_totales.values) > 0:
        ax.set_ylim(min(mensual_totales.values) * 0.90, max(mensual_totales.values) * 1.08)
    
    st.pyplot(fig)
    st.caption(
        '📈 **Insight clave de Temporalidad:** Los homicidios registraron su mayor punto de tensión en marzo con 3,061 carpetas,'
        ' mostrando una desaceleración gradual hacia junio (2,634) y julio (2,650), lo que representa una reducción de 13.4% respecto al pico del primer trimestre.'
    )

    st.markdown('---')

    # Fila secundaria en 2 columnas para Estados Críticos y Naturaleza Jurídica
    col_barras, col_pie = st.columns(2)

    with col_barras:
        st.subheader('¿Cuáles son las entidades federativas con mayor número de homicidios registrados?')
        fig, ax = plt.subplots(figsize=(8, 4.6))
        
        top10_estados = df_filtered.groupby('entidad')['total_delitos'].sum().sort_values(ascending=True).tail(10)
        bars = ax.barh(top10_estados.index, top10_estados.values, color='#e53e3e', height=0.65, edgecolor='black', linewidth=0.5)
        
        max_val = max(top10_estados.values) if len(top10_estados) > 0 else 1
        for bar in bars:
            w = bar.get_width()
            ax.text(
                w + max_val * 0.015,
                bar.get_y() + bar.get_height() / 2,
                f"{w:,.0f}",
                va='center',
                fontsize=8.5,
                fontweight='bold',
                color='#742a2a',
            )
            
        ax.set_xlabel('Carpetas de Homicidio')
        ax.xaxis.set_major_formatter('{x:,.0f}')
        ax.set_xlim(0, max_val * 1.15)
        ax.grid(True, linestyle='--', alpha=0.5, axis='x')
        st.pyplot(fig)
        st.caption(
            '🚨 **Insight clave:** Guanajuato (1,663), Estado de México (1,473) y Michoacán (1,343) encabezan la cifra absoluta de homicidios,'
            ' concentrando en conjunto el 22.6% del total nacional en los primeros siete meses de 2026.'
        )

    with col_pie:
        st.subheader('¿Cómo se clasifican los homicidios según su naturaleza jurídica? (Doloso vs. Culposo)')
        fig, ax = plt.subplots(figsize=(8, 4.6))
        
        sub_resumen = df_filtered.groupby('subtipo_delito')['total_delitos'].sum()
        
        if not sub_resumen.empty and sub_resumen.sum() > 0:
            colores = [PALETA_SUBTIPOS.get(s, '#718096') for s in sub_resumen.index]
            wedges, texts, autotexts = ax.pie(
                sub_resumen.values,
                labels=sub_resumen.index,
                autopct='%1.1f%%',
                startangle=140,
                colors=colores,
                explode=[0.03] * len(sub_resumen),
                textprops={'fontsize': 9, 'weight': 'bold'},
                wedgeprops={'edgecolor': 'white', 'linewidth': 1.5},
            )
            for at in autotexts:
                at.set_color('white')
            ax.axis('equal')
            ax.legend(
                wedges,
                [f"{lbl}: {val:,.0f} casos" for lbl, val in zip(sub_resumen.index, sub_resumen.values)],
                title='Subtipo',
                loc='upper right',
                bbox_to_anchor=(1.35, 1),
                fontsize=8,
            )
        else:
            ax.text(0.5, 0.5, 'Sin registros para los filtros seleccionados', ha='center', va='center')
            
        st.pyplot(fig)
        st.caption(
            '⚖️ **Insight clave:** Prácticamente 1 de cada 2 homicidios es culposo (47.4%, impulsado principalmente por siniestros viales),'
            ' mientras que el homicidio doloso representa el 45.3%, visibilizando dos frentes de acción urgentes: pacificación territorial y seguridad vial.'
        )

# ------------------------------------------------------------------------------
# PESTAÑA 2: ANÁLISIS POR MODALIDAD Y DISPERSIÓN ESTATAL (BOXPLOT + SCATTER)
# ------------------------------------------------------------------------------
with tab_entidades:
    col_box, col_scatter = st.columns(2)

    with col_box:
        st.subheader('¿Cómo se distribuye y varía la tasa de homicidios por estado según la modalidad?')
        fig, ax = plt.subplots(figsize=(8, 4.8))
        
        modalidades_analisis = [
            'Con arma de fuego',
            'En accidente de tránsito',
            'Con otro elemento',
            'No especificado',
            'Con arma blanca',
        ]
        modalidades_presentes = [m for m in modalidades_analisis if m in df_filtered['modalidad'].unique()]
        
        if modalidades_presentes:
            ent_mod = (
                df_filtered[df_filtered['modalidad'].isin(modalidades_presentes)]
                .groupby(['entidad', 'modalidad'])['total_delitos']
                .sum()
                .reset_index()
            )
            palette_mod = dict(zip(modalidades_presentes, sns.color_palette('Reds_r', n_colors=len(modalidades_presentes))))
            
            sns.boxplot(
                data=ent_mod,
                x='total_delitos',
                y='modalidad',
                hue='modalidad',
                order=modalidades_presentes,
                palette=palette_mod,
                legend=False,
                ax=ax,
                linewidth=1.2,
                fliersize=3.5,
                boxprops=dict(alpha=0.85),
            )
            ax.set_xlabel('Homicidios por Estado')
            ax.set_ylabel('')
            ax.xaxis.set_major_formatter('{x:,.0f}')
            ax.grid(True, linestyle='--', alpha=0.5)
        else:
            ax.text(0.5, 0.5, 'Sin modalidades seleccionadas para boxplot', ha='center', va='center')
            
        st.pyplot(fig)
        st.caption(
            '📦 **Insight clave:** El *homicidio con arma de fuego* exhibe la mayor variabilidad y valores atípicos severos'
            ' (Guanajuato con 660+ y Baja California con 500+ homicidios dolosos armados), mientras que el homicidio con arma blanca es homogéneamente bajo en el país.'
        )

    with col_scatter:
        st.subheader('¿Existe relación entre homicidios dolosos y culposos por entidad?')
        fig, ax = plt.subplots(figsize=(8, 4.8))
        
        pivot_sub = df_filtered.pivot_table(
            index='entidad',
            columns='subtipo_delito',
            values='total_delitos',
            aggfunc='sum',
            fill_value=0,
        ).reset_index()

        x_col = 'Homicidio doloso'
        y_col = 'Homicidio culposo'

        if x_col in pivot_sub.columns and y_col in pivot_sub.columns and len(pivot_sub) > 1:
            sns.scatterplot(
                data=pivot_sub,
                x=x_col,
                y=y_col,
                s=70,
                color='#e53e3e',
                edgecolor='black',
                linewidth=0.6,
                alpha=0.85,
                ax=ax,
            )

            # Ajuste lineal de tendencia
            x_vals = pivot_sub[x_col].values
            y_vals = pivot_sub[y_col].values
            if np.std(x_vals) > 0 and np.std(y_vals) > 0:
                m, b = np.polyfit(x_vals, y_vals, 1)
                r_corr = np.corrcoef(x_vals, y_vals)[0, 1]
                x_line = np.linspace(x_vals.min(), x_vals.max(), 100)
                ax.plot(x_line, m * x_line + b, color='#2b6cb0', linestyle='--', lw=1.8, label=f'Tendencia lineal (R = {r_corr:.2f})')

            ax.set_xlabel('Homicidios Dolosos por Estado')
            ax.set_ylabel('Homicidios Culposos por Estado')
            ax.xaxis.set_major_formatter('{x:,.0f}')
            ax.yaxis.set_major_formatter('{x:,.0f}')
            ax.legend(loc='upper left', fontsize=8.5)
            ax.grid(True, linestyle='--', alpha=0.5)
        else:
            ax.text(0.5, 0.5, 'Se requieren datos de ambos subtipos para correlacionar', ha='center', va='center')
            
        st.pyplot(fig)
        st.caption(
            '⏱️ **Insight clave:** La relación entre homicidios dolosos y culposos ($R = 0.54$) revela que estados de alta violencia criminal'
            ' (como Guanajuato y Michoacán) presentan una clara desproporción hacia el dolo, mientras que entidades metropolitanas reportan mayor peso culposo vial.'
        )

# ------------------------------------------------------------------------------
# PESTAÑA 3: DISTRIBUCIÓN POR MEDIO Y MODALIDAD (GRÁFICA DE DONA)
# ------------------------------------------------------------------------------
with tab_modalidades:
    st.subheader('¿Cómo se distribuyen los homicidios según el medio o modalidad de comisión?')
    
    mod_summary = (
        df_filtered.groupby('modalidad')['total_delitos']
        .sum()
        .sort_values(ascending=False)
    )
    total_global = mod_summary.sum()

    if total_global > 0:
        etiquetas = mod_summary.index.tolist()
        valores = mod_summary.values.tolist()
        colores = [PALETA_MODALIDADES.get(m, '#718096') for m in etiquetas]

        # Gráfica de Dona (Donut Chart)
        fig, ax = plt.subplots(figsize=(8.5, 4.8))
        wedges, texts, autotexts = ax.pie(
            valores,
            labels=None,
            autopct='%1.1f%%',
            pctdistance=0.76,
            startangle=140,
            colors=colores,
            wedgeprops=dict(width=0.42, edgecolor='white', linewidth=2),
            textprops=dict(fontsize=8.5, fontweight='bold', color='white'),
        )

        # Texto en el centro de la dona
        ax.text(0, 0.08, 'Total Homicidios', ha='center', va='center', fontsize=9.5, color='#718096')
        ax.text(
            0,
            -0.08,
            f"{total_global:,.0f}\nCasos",
            ha='center',
            va='center',
            fontsize=11,
            fontweight='bold',
            color='#1a202c',
        )

        # Leyenda descriptiva a la derecha
        legend_labels = [
            f"{etiqueta}: {val:,.0f} ({val/total_global*100:.1f}%)"
            for etiqueta, val in zip(etiquetas, valores)
        ]
        ax.legend(
            wedges,
            legend_labels,
            title='Modalidad o Medio',
            loc='center left',
            bbox_to_anchor=(1.02, 0.5),
            fontsize=8.5,
            title_fontsize=9.5,
        )
        ax.axis('equal')
        plt.tight_layout()
        st.pyplot(fig)

        # Tarjetas de diagnóstico cuantitativo (Top 4 Modalidades)
        top4_mods = mod_summary.head(4)
        cols = st.columns(len(top4_mods))
        for col, (modalidad_nombre, valor_mod) in zip(cols, top4_mods.items()):
            pct = (valor_mod / total_global) * 100
            nombre_corto = modalidad_nombre if len(modalidad_nombre) <= 22 else modalidad_nombre[:20] + ".."
            col.metric(
                label=nombre_corto,
                value=f"{valor_mod:,.0f} casos",
                delta=f"{pct:.1f}% del total",
            )

        # Resumen e insights ejecutivos de política de seguridad
        fuego_total = mod_summary.get('Con arma de fuego', 0)
        fuego_pct = (fuego_total / total_global) * 100 if total_global > 0 else 0
        transito_total = mod_summary.get('En accidente de tránsito', 0)
        transito_pct = (transito_total / total_global) * 100 if total_global > 0 else 0

        st.caption(
            f"🛡️ **Insight clave de Política de Seguridad:** El **{fuego_pct:.1f}%** de los homicidios en México se cometieron con "
            f"**arma de fuego** ({fuego_total:,.0f} casos), siendo el vector letal determinante en la violencia organizada. "
            f"Asimismo, los accidentes de tránsito ocupan el segundo lugar (**{transito_pct:.1f}%**, {transito_total:,.0f} casos), "
            f"confirmando la necesidad crítica de operativos de desarme y rigurosidad en normatividad vial."
        )
    else:
        st.info('No hay registros de homicidios para los filtros seleccionados.')
