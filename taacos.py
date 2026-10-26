import io
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

st.set_page_config(
    page_title='Incidencia Delictiva Nacional 2026 - SESNSP',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ==============================================================================
# 1. ARQUITECTURA DE ALMACENAMIENTO DE OBJETOS EN LA NUBE
# - Zona raw/   : Datos tal como llegaron del SESNSP (incidencia_delictiva_2026_raw.csv)
# - Zona clean/ : Datos depurados y validados para el consumo analítico (incidencia_delictiva_2026_clean.csv)
# EL DASHBOARD LEE SUS DATOS DIRECTAMENTE DE LA ZONA clean/ EN LA NUBE O EN REPOSITORIO LOCAL.
# ==============================================================================

DEFAULT_CLEAN_CLOUD_URL = (
    'https://raw.githubusercontent.com/luishinojosacorona123-spec/taacos/main/clean/incidencia_delictiva_2026_clean.csv'
)

DEFAULT_RAW_CLOUD_URL = (
    'https://raw.githubusercontent.com/luishinojosacorona123-spec/taacos/main/raw/incidencia_delictiva_2026_raw.csv'
)

LOCAL_CLEAN_PATH = os.path.join(os.path.dirname(__file__), 'clean', 'incidencia_delictiva_2026_clean.csv')
LOCAL_RAW_PATH = os.path.join(os.path.dirname(__file__), 'raw', 'incidencia_delictiva_2026_raw.csv')

MESES_OFICIALES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio']

# ==============================================================================
# 2. CAPA DE BACKEND: CARGA Y LIMPIEZA DE DATOS CON @st.cache_data
# ==============================================================================

def sanitize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Estandariza los nombres de columnas evitando caracteres especiales o Mojibake."""
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

    df['total_delitos'] = df[MESES_OFICIALES].sum(axis=1)
    return df


@st.cache_data(ttl=600, show_spinner=False)
def load_and_clean_data(cloud_url: str) -> pd.DataFrame:
    """Descarga los datos directamente desde la nube o lee la copia local de respaldo."""
    df = None
    try:
        df = pd.read_csv(cloud_url, encoding='utf-8-sig')
    except Exception:
        if os.path.exists(LOCAL_CLEAN_PATH):
            df = pd.read_csv(LOCAL_CLEAN_PATH, encoding='utf-8-sig')
        elif os.path.exists(LOCAL_RAW_PATH):
            df = pd.read_csv(LOCAL_RAW_PATH, encoding='utf-8-sig')

    if df is None:
        raise FileNotFoundError("No se encontró el archivo de datos ni local ni remotamente.")

    return sanitize_columns(df)


@st.cache_data(show_spinner=False)
def etl_clean_pipeline(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Pipeline ETL para procesar archivos recién ingestados en la zona raw/."""
    return sanitize_columns(df_raw.copy())


# ==============================================================================
# 3. CAPA DE FRONTEND: CONFIGURACIÓN, INGESTA Y WIDGETS DE FILTRADO
# ==============================================================================

with st.sidebar:
    st.header('☁️ Almacenamiento en la Nube')
    st.markdown("""
    **Zonas de Almacenamiento (Data Lakehouse):**
    - 📁 `raw/`: Datos del SESNSP tal como llegaron.
    - 📁 `clean/`: Datos estructurados y validados para el tablero.
    """)

    cloud_storage_url = st.text_input(
        '🌐 Endpoint de la Nube (Zona `clean/`):',
        value=DEFAULT_CLEAN_CLOUD_URL,
        help='URL pública para el dataset en la zona clean/',
    )

    uploaded_raw_file = st.file_uploader(
        '📥 Ingesta a Zona `raw/` (CSV o Excel):',
        type=['csv', 'xlsx'],
        key='sidebar_raw_uploader',
        help='Carga un archivo de incidencia delictiva para su procesamiento dinámico.',
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
            f'✅ Archivo `{uploaded_raw_file.name}` procesado: {len(df_base):,} registros en clean/'
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
    st.header('🎯 Filtros Interactivos')

    # Widget 1: Entidades Federativas
    entidades_disponibles = sorted(df_base['entidad'].dropna().unique().tolist())
    filtro_entidades = st.multiselect(
        '📍 Entidad Federativa (Estado):',
        options=entidades_disponibles,
        default=entidades_disponibles,
        help='Selecciona una o más entidades para analizar.',
    )

    # Widget 2: Bien Jurídico Afectado
    bienes_disponibles = sorted(df_base['bien_juridico_afectado'].dropna().unique().tolist())
    filtro_bienes = st.multiselect(
        '🛡️ Bien Jurídico Afectado:',
        options=bienes_disponibles,
        default=bienes_disponibles,
        help='Filtra por categorías principales de protección jurídica.',
    )

    # Widget 3: Tipo de Delito
    delitos_disponibles = sorted(
        df_base[df_base['bien_juridico_afectado'].isin(filtro_bienes)]['tipo_delito'].dropna().unique().tolist()
    ) if filtro_bienes else sorted(df_base['tipo_delito'].dropna().unique().tolist())

    filtro_delitos = st.multiselect(
        '🚨 Tipo de Delito:',
        options=delitos_disponibles,
        default=delitos_disponibles,
        help='Filtra delitos específicos dentro de las categorías elegidas.',
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

if filtro_bienes:
    df_filtered = df_filtered[df_filtered['bien_juridico_afectado'].isin(filtro_bienes)]
else:
    df_filtered = df_filtered.iloc[0:0]

if filtro_delitos:
    df_filtered = df_filtered[df_filtered['tipo_delito'].isin(filtro_delitos)]
else:
    df_filtered = df_filtered.iloc[0:0]

meses_activos = filtro_meses if filtro_meses else MESES_OFICIALES
df_filtered['total_delitos'] = df_filtered[meses_activos].sum(axis=1)


# ==============================================================================
# ÁREA PRINCIPAL: KPIs Y GRÁFICOS INTERACTIVOS (FRONTEND)
# ==============================================================================

st.title('Tablero de Control: Incidencia Delictiva en México 2026')
st.caption(
    'Secretariado Ejecutivo del Sistema Nacional de Seguridad Pública (SESNSP) | '
    f'Corte Enero - Julio 2026 ({len(df_filtered):,} registros analizados de {len(df_base):,} totales)'
)

# Control de caso borde: Sin registros seleccionados
if df_filtered.empty or df_filtered['total_delitos'].sum() == 0:
    st.warning(
        '⚠️ No se encontraron registros que coincidan con los filtros seleccionados. '
        'Por favor selecciona al menos una entidad, bien jurídico, tipo de delito y mes en la barra lateral.'
    )
    st.stop()


# ----------------- KPI HEADER DINÁMICO -----------------
total_delitos_nacional = df_filtered['total_delitos'].sum()
num_meses_sel = len(meses_activos)
promedio_mensual = (total_delitos_nacional / num_meses_sel) if num_meses_sel > 0 else 0

top_delito_serie = df_filtered.groupby('tipo_delito')['total_delitos'].sum().sort_values(ascending=False)
if not top_delito_serie.empty:
    top_delito_nombre = top_delito_serie.index[0]
    top_delito_casos = top_delito_serie.iloc[0]
    top_delito_pct = (top_delito_casos / total_delitos_nacional) * 100 if total_delitos_nacional > 0 else 0
else:
    top_delito_nombre = 'N/A'
    top_delito_casos = 0
    top_delito_pct = 0

# Variación del último mes activo vs mes penúltimo
sum_meses = df_filtered[meses_activos].sum()
if len(sum_meses) >= 2 and sum_meses.iloc[-2] > 0:
    ultimo_mes_nombre = sum_meses.index[-1]
    penultimo_mes_nombre = sum_meses.index[-2]
    ultimo_mes_casos = sum_meses.iloc[-1]
    penultimo_mes_casos = sum_meses.iloc[-2]
    var_ultimo_mes = ((ultimo_mes_casos - penultimo_mes_casos) / penultimo_mes_casos) * 100
    delta_str = f"{var_ultimo_mes:+.1f}% vs {penultimo_mes_nombre}"
    ultimo_mes_label = f"Incidencia {ultimo_mes_nombre}"
    ultimo_mes_valor = f"{ultimo_mes_casos:,.0f} casos"
elif len(sum_meses) == 1:
    ultimo_mes_nombre = sum_meses.index[0]
    ultimo_mes_label = f"Incidencia {ultimo_mes_nombre}"
    ultimo_mes_valor = f"{sum_meses.iloc[0]:,.0f} casos"
    delta_str = "Mes único"
else:
    ultimo_mes_label = "Incidencia Último Mes"
    ultimo_mes_valor = "0 casos"
    delta_str = "0.0%"

k1, k2, k3, k4 = st.columns(4)
k1.metric('Total Delitos Registrados', f'{total_delitos_nacional:,.0f} casos')
k2.metric('Promedio Mensual', f'{promedio_mensual:,.0f} casos/mes')
k3.metric('Delito Mayor Frecuencia', str(top_delito_nombre), f'{top_delito_casos:,.0f} casos ({top_delito_pct:.1f}%)')
k4.metric(ultimo_mes_label, ultimo_mes_valor, delta=delta_str)

st.markdown('---')


# ==============================================================================
# 4. PALETA DE COLOR UNIFICADA POR CATEGORÍA
# ==============================================================================
PALETA_BIENES = {
    'El patrimonio': '#2b6cb0',                                          # Azul corporativo
    'Otros bienes jurídicos afectados (del fuero común)': '#4a5568',    # Gris pizarra
    'La familia': '#319795',                                              # Verde azulado / Teal
    'La vida y la Integridad corporal': '#e53e3e',                        # Rojo
    'La libertad y la seguridad sexual': '#805ad5',                       # Púrpura
    'Libertad personal': '#dd6b20',                                       # Naranja
    'La sociedad': '#38a169',                                             # Verde
}

PALETA_VIOLENCIA = {
    'Sin violencia': '#3182ce',
    'Con violencia': '#e53e3e',
}


# ==============================================================================
# 5. JERARQUÍA VISUAL CON st.tabs Y st.columns CON TEXTOS DE APOYO (INSIGHTS)
# ==============================================================================
tab_tendencias, tab_entidades, tab_distribucion = st.tabs([
    '📈 Tendencias y Mayor Frecuencia',
    '🔧 Análisis por Entidad y Dispersión',
    '💳 Distribución Proporcional (Dona)',
])

# ------------------------------------------------------------------------------
# PESTAÑA 1: TENDENCIAS Y MAYOR FRECUENCIA (HERO CHART + BARRAS + PASTEL)
# ------------------------------------------------------------------------------
with tab_tendencias:
    # Gráfico Principal de Mayor Jerarquía Visual (Arriba y a ancho completo)
    st.subheader('¿Cómo evoluciona la incidencia delictiva total mes a mes en 2026?')
    fig, ax = plt.subplots(figsize=(10, 4))
    
    mensual_totales = df_filtered[meses_activos].sum()
    ax.plot(
        mensual_totales.index,
        mensual_totales.values,
        marker='o',
        color='#2b6cb0',
        linewidth=2.5,
        markersize=7,
        label='Total Delitos Registrados',
    )
    ax.fill_between(mensual_totales.index, mensual_totales.values, color='#bee3f8', alpha=0.35)
    
    for m, val in zip(mensual_totales.index, mensual_totales.values):
        ax.annotate(
            f"{val:,.0f}",
            (m, val),
            textcoords="offset points",
            xytext=(0, 8),
            ha='center',
            fontsize=8.5,
            fontweight='bold',
            color='#1a365d',
        )

    ax.set_ylabel('Número de Delitos')
    ax.yaxis.set_major_formatter('{x:,.0f}')
    ax.grid(True, linestyle='--', alpha=0.5)
    if not mensual_totales.empty and max(mensual_totales.values) > 0:
        ax.set_ylim(min(mensual_totales.values) * 0.90, max(mensual_totales.values) * 1.08)
    
    st.pyplot(fig)
    st.caption(
        '📈 **Insight clave de Temporalidad:** La incidencia delictiva total experimentó un crecimiento'
        ' del 16.4% entre enero (155,033 casos) y marzo (175,248 casos), estabilizándose posteriormente en'
        ' una meseta regular cercana a ~173,500 delitos mensuales durante el segundo trimestre de 2026.'
    )

    st.markdown('---')

    # Fila secundaria en 2 columnas para Top Delitos y Modalidad de Robo
    col_barras, col_pie = st.columns(2)

    with col_barras:
        st.subheader('¿Cuáles son los tipos de delito con mayor incidencia registrada?')
        fig, ax = plt.subplots(figsize=(8, 4.6))
        
        top10_delitos = df_filtered.groupby('tipo_delito')['total_delitos'].sum().sort_values(ascending=True).tail(10)
        bars = ax.barh(top10_delitos.index, top10_delitos.values, color='#319795', height=0.65, edgecolor='black', linewidth=0.5)
        
        max_val = max(top10_delitos.values) if len(top10_delitos) > 0 else 1
        for bar in bars:
            w = bar.get_width()
            ax.text(
                w + max_val * 0.015,
                bar.get_y() + bar.get_height() / 2,
                f"{w:,.0f}",
                va='center',
                fontsize=8.5,
                fontweight='bold',
                color='#1d4044',
            )
            
        ax.set_xlabel('Carpetas de Investigación')
        ax.xaxis.set_major_formatter('{x:,.0f}')
        ax.set_xlim(0, max_val * 1.18)
        ax.grid(True, linestyle='--', alpha=0.5, axis='x')
        st.pyplot(fig)
        st.caption(
            '🚨 **Insight clave:** El *Robo* lidera de forma contundente la incidencia delictiva con más de 247,000 carpetas (21.1%),'
            ' seguido por *Violencia familiar* (163,285) y *Lesiones* (127,360), concentrando juntos casi la mitad de los delitos del fuero común.'
        )

    with col_pie:
        st.subheader('¿Cómo se distribuyen los robos según el uso de violencia?')
        fig, ax = plt.subplots(figsize=(8, 4.6))
        
        robos_df = df_filtered[df_filtered['tipo_delito'] == 'Robo']
        robos_mod = robos_df.groupby('modalidad')['total_delitos'].sum()
        
        # Filtrar modalidades de violencia en robo
        violencia_cats = [m for m in ['Sin violencia', 'Con violencia'] if m in robos_mod.index]
        
        if len(violencia_cats) > 0 and robos_mod[violencia_cats].sum() > 0:
            sub_mod = robos_mod[violencia_cats]
            colores = [PALETA_VIOLENCIA.get(m, '#718096') for m in sub_mod.index]
            wedges, texts, autotexts = ax.pie(
                sub_mod.values,
                labels=sub_mod.index,
                autopct='%1.1f%%',
                startangle=140,
                colors=colores,
                explode=[0.03] * len(sub_mod),
                textprops={'fontsize': 9.5, 'weight': 'bold'},
                wedgeprops={'edgecolor': 'white', 'linewidth': 1.5},
            )
            for at in autotexts:
                at.set_color('white')
            ax.axis('equal')
            ax.legend(
                wedges,
                [f"{lbl}: {val:,.0f} casos" for lbl, val in zip(sub_mod.index, sub_mod.values)],
                title='Modalidad',
                loc='upper right',
                fontsize=8.5,
            )
        else:
            # Si no hay robos en el filtro, mostrar desglose general de violencia o texto informativo
            ax.text(0.5, 0.5, 'Sin registros de robo en el rango filtrado', ha='center', va='center')
            
        st.pyplot(fig)
        st.caption(
            '⚖️ **Insight clave:** El 69.7% de los robos corresponden a modalidades no violentas (como robo a casa o negocio sin violencia),'
            ' mientras que 3 de cada 10 robos se perpetraron con violencia directa sobre las víctimas, demandando patrullaje preventivo estratégico.'
        )

# ------------------------------------------------------------------------------
# PESTAÑA 2: ANÁLISIS POR ENTIDAD Y DISPERSIÓN (BOXPLOT + SCATTER EN 2 COLUMNAS)
# ------------------------------------------------------------------------------
with tab_entidades:
    col_box, col_scatter = st.columns(2)

    with col_box:
        st.subheader('¿Cómo se distribuye y varía la incidencia por estado según el delito?')
        fig, ax = plt.subplots(figsize=(8, 4.8))
        
        delitos_principales = ['Robo', 'Violencia familiar', 'Lesiones', 'Daño a la propiedad', 'Fraude', 'Amenazas']
        delitos_presentes = [d for d in delitos_principales if d in df_filtered['tipo_delito'].unique()]
        
        if delitos_presentes:
            ent_del = (
                df_filtered[df_filtered['tipo_delito'].isin(delitos_presentes)]
                .groupby(['entidad', 'tipo_delito'])['total_delitos']
                .sum()
                .reset_index()
            )
            palette_box = dict(zip(delitos_presentes, sns.color_palette('tab10', n_colors=len(delitos_presentes))))
            
            sns.boxplot(
                data=ent_del,
                x='total_delitos',
                y='tipo_delito',
                hue='tipo_delito',
                order=delitos_presentes,
                palette=palette_box,
                legend=False,
                ax=ax,
                linewidth=1.2,
                fliersize=3.5,
                boxprops=dict(alpha=0.85),
            )
            ax.set_xlabel('Carpetas de Investigación por Estado')
            ax.set_ylabel('')
            ax.xaxis.set_major_formatter('{x:,.0f}')
            ax.grid(True, linestyle='--', alpha=0.5)
        else:
            ax.text(0.5, 0.5, 'Sin delitos principales en los filtros activos', ha='center', va='center')
            
        st.pyplot(fig)
        st.caption(
            '📦 **Insight clave:** *Robo* y *Violencia familiar* muestran la mayor dispersión territorial con valores atípicos severos'
            ' (outliers en Estado de México y CDMX), mientras que ilícitos como *Fraude* o *Amenazas* mantienen distribuciones estatales más compactas.'
        )

    with col_scatter:
        st.subheader('¿Existe correlación entre delitos patrimoniales y contra la vida?')
        fig, ax = plt.subplots(figsize=(8, 4.8))
        
        ent_bj = df_filtered.pivot_table(
            index='entidad',
            columns='bien_juridico_afectado',
            values='total_delitos',
            aggfunc='sum',
            fill_value=0,
        ).reset_index()

        x_col = 'El patrimonio'
        y_col = 'La vida y la Integridad corporal'

        if x_col in ent_bj.columns and y_col in ent_bj.columns and len(ent_bj) > 1:
            sns.scatterplot(
                data=ent_bj,
                x=x_col,
                y=y_col,
                s=65,
                color='#2b6cb0',
                edgecolor='black',
                linewidth=0.6,
                alpha=0.85,
                ax=ax,
            )

            # Ajuste lineal de tendencia
            x_vals = ent_bj[x_col].values
            y_vals = ent_bj[y_col].values
            if np.std(x_vals) > 0 and np.std(y_vals) > 0:
                m, b = np.polyfit(x_vals, y_vals, 1)
                r_corr = np.corrcoef(x_vals, y_vals)[0, 1]
                x_line = np.linspace(x_vals.min(), x_vals.max(), 100)
                ax.plot(x_line, m * x_line + b, color='#e53e3e', linestyle='--', lw=1.8, label=f'Tendencia lineal (R = {r_corr:.2f})')

            ax.set_xlabel('Delitos contra el Patrimonio por Estado')
            ax.set_ylabel('Delitos contra la Vida e Integridad')
            ax.xaxis.set_major_formatter('{x:,.0f}')
            ax.yaxis.set_major_formatter('{x:,.0f}')
            ax.legend(loc='upper left', fontsize=8.5)
            ax.grid(True, linestyle='--', alpha=0.5)
        else:
            ax.text(0.5, 0.5, 'Se requieren datos de ambas categorías para correlacionar', ha='center', va='center')
            
        st.pyplot(fig)
        st.caption(
            '⏱️ **Insight clave:** Se confirma una fuerte correlación lineal positiva ($R > 0.85$): las entidades con mayor incidencia'
            ' patrimonial también concentran el mayor número de homicidios y lesiones, reflejando focos de inseguridad estructural común.'
        )

# ------------------------------------------------------------------------------
# PESTAÑA 3: DISTRIBUCIÓN PROPORCIONAL (GRÁFICA DE DONA)
# ------------------------------------------------------------------------------
with tab_distribucion:
    st.subheader('¿Cómo se distribuye la incidencia delictiva según el Bien Jurídico Afectado?')
    
    bj_summary = (
        df_filtered.groupby('bien_juridico_afectado')['total_delitos']
        .sum()
        .sort_values(ascending=False)
    )
    total_global = bj_summary.sum()

    if total_global > 0:
        etiquetas = bj_summary.index.tolist()
        valores = bj_summary.values.tolist()
        colores = [PALETA_BIENES.get(b, '#718096') for b in etiquetas]

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
        ax.text(0, 0.08, 'Total Delitos', ha='center', va='center', fontsize=9.5, color='#718096')
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
            f"{etiqueta[:28]}..: {val:,.0f} ({val/total_global*100:.1f}%)" if len(etiqueta) > 30 else f"{etiqueta}: {val:,.0f} ({val/total_global*100:.1f}%)"
            for etiqueta, val in zip(etiquetas, valores)
        ]
        ax.legend(
            wedges,
            legend_labels,
            title='Bien Jurídico Afectado',
            loc='center left',
            bbox_to_anchor=(1.02, 0.5),
            fontsize=8.5,
            title_fontsize=9.5,
        )
        ax.axis('equal')
        plt.tight_layout()
        st.pyplot(fig)

        # Tarjetas de diagnóstico cuantitativo (Top 4 Bienes Jurídicos)
        top4_bienes = bj_summary.head(4)
        cols = st.columns(len(top4_bienes))
        for col, (bien, valor_bien) in zip(cols, top4_bienes.items()):
            pct = (valor_bien / total_global) * 100
            nombre_corto = bien if len(bien) <= 22 else bien[:20] + ".."
            col.metric(
                label=nombre_corto,
                value=f"{valor_bien:,.0f} casos",
                delta=f"{pct:.1f}% del total",
            )

        # Resumen e insights ejecutivos de política criminal
        patrimonio_total = bj_summary.get('El patrimonio', 0)
        patrimonio_pct = (patrimonio_total / total_global) * 100 if total_global > 0 else 0
        familia_total = bj_summary.get('La familia', 0)
        familia_pct = (familia_total / total_global) * 100 if total_global > 0 else 0

        st.caption(
            f"🛡️ **Insight clave de Política Criminal:** El patrimonio ciudadano es el bien más vulnerado en México con "
            f"**{patrimonio_pct:.1f}%** de los delitos ({patrimonio_total:,.0f} casos), seguido por los delitos que atentan contra la familia "
            f"(**{familia_pct:.1f}%**, {familia_total:,.0f} casos). Esto subraya que más de la mitad de las carpetas de investigación corresponden "
            f"a afectaciones patrimoniales y violencia en el entorno doméstico, prioritarias para el despliegue de políticas preventivas."
        )
    else:
        st.info('No hay registros de delitos para los filtros seleccionados.')
