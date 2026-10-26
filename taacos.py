import io
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

st.set_page_config(
    page_title='Gestión de Portafolio Inmobiliario y Rentas (Enero a Octubre 2026)',
    layout='wide',
    initial_sidebar_state='expanded',
)

# ==============================================================================
# 1. ARQUITECTURA DE ALMACENAMIENTO DE OBJETOS EN LA NUBE
# - Zona raw/   : Dataset original del portafolio inmobiliario (portafolio_inmuebles_raw.csv)
# - Zona clean/ : Dataset procesado, validado y normalizado (portafolio_inmuebles_clean.csv)
# ==============================================================================

DEFAULT_CLEAN_CLOUD_URL = (
    'https://raw.githubusercontent.com/luishinojosacorona123-spec/taacos/main/clean/portafolio_inmuebles_clean.csv'
)

DEFAULT_RAW_CLOUD_URL = (
    'https://raw.githubusercontent.com/luishinojosacorona123-spec/taacos/main/raw/portafolio_inmuebles_raw.csv'
)

LOCAL_CLEAN_PATH = os.path.join(os.path.dirname(__file__), 'clean', 'portafolio_inmuebles_clean.csv')
LOCAL_RAW_PATH = os.path.join(os.path.dirname(__file__), 'raw', 'portafolio_inmuebles_raw.csv')

MESES_ORDEN = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo',
    'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre'
]

PALETA_CATEGORIAS = {
    'Casas': '#2b6cb0',        # Azul corporativo
    'Terrenos': '#2f855a',     # Verde bosque
    'Departamento': '#805ad5', # Morado elegante
    'Vehículos': '#dd6b20',    # Naranja cálido
}

# ==============================================================================
# 2. CAPA DE BACKEND: CARGA Y LIMPIEZA DE DATOS CON @st.cache_data
# ==============================================================================

@st.cache_data(ttl=600, show_spinner=False)
def load_portfolio_data(clean_url: str = DEFAULT_CLEAN_CLOUD_URL, local_path: str = LOCAL_CLEAN_PATH):
    """Carga los datos depurados del portafolio inmobiliario desde la nube o respaldo local."""
    df = None
    source = 'Local'

    # 1. Intento de carga remota desde GitHub / Cloud Storage
    if clean_url:
        try:
            df = pd.read_csv(clean_url, encoding='utf-8')
            source = 'Cloud (GitHub raw)'
        except Exception:
            df = None

    # 2. Respaldo local
    if df is None:
        if os.path.exists(local_path):
            df = pd.read_csv(local_path, encoding='utf-8')
            source = 'Local Storage (clean/)'
        else:
            raise FileNotFoundError(f"No se encontró el dataset en '{clean_url}' ni en '{local_path}'.")

    # Asegurar tipos de datos numéricos
    cols_num = ['valor_propiedad', 'renta_mensual', 'num_mes', 'ingreso_renta', 'gasto_operativo', 'utilidad_neta']
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    return df, source


# ==============================================================================
# 3. INTERFAZ DE USUARIO: CSS Y CONFIGURACIÓN ESTÉTICA
# ==============================================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1a202c;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4a5568;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 1.1rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    .badge-cloud {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        font-size: 0.8rem;
        font-weight: 600;
        border-radius: 6px;
        background-color: #ebf8ff;
        color: #2b6cb0;
        border: 1px solid #bee3f8;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Carga de datos
try:
    df_raw, data_source = load_portfolio_data()
except Exception as e:
    st.error(f"❌ Error al cargar los datos del portafolio: {e}")
    st.stop()


# ==============================================================================
# 4. BARRA LATERAL: FILTROS DINÁMICOS Y CONTROL DE DATOS
# ==============================================================================

with st.sidebar:
    st.title("🏢 Filtros del Portafolio")
    st.markdown(f"<span class='badge-cloud'>Origen: {data_source}</span>", unsafe_allow_html=True)
    st.markdown("---")

    # Filtro 1: Categoría de activo
    todas_categorias = sorted(df_raw['categoria'].unique().tolist())
    sel_todas_cat = st.checkbox("Seleccionar todas las categorías", value=True)
    if sel_todas_cat:
        selected_cats = st.multiselect("Categorías de Activo", todas_categorias, default=todas_categorias)
    else:
        selected_cats = st.multiselect("Categorías de Activo", todas_categorias, default=[todas_categorias[0]])

    if not selected_cats:
        st.warning("⚠️ Selecciona al menos una categoría.")
        st.stop()

    df_filtered_cats = df_raw[df_raw['categoria'].isin(selected_cats)]

    # Filtro 2: Propiedades
    todas_props = sorted(df_filtered_cats['propiedad'].unique().tolist())
    sel_todas_props = st.checkbox("Seleccionar todas las propiedades", value=True)
    if sel_todas_props:
        selected_props = st.multiselect("Propiedades / Activos", todas_props, default=todas_props)
    else:
        selected_props = st.multiselect("Propiedades / Activos", todas_props, default=[todas_props[0]])

    if not selected_props:
        st.warning("⚠️ Selecciona al menos una propiedad.")
        st.stop()

    df_filtered_props = df_filtered_cats[df_filtered_cats['propiedad'].isin(selected_props)]

    # Filtro 3: Rango de meses
    meses_disponibles = [m for m in MESES_ORDEN if m in df_filtered_props['mes'].unique()]
    sel_todos_meses = st.checkbox("Seleccionar todos los meses", value=True)
    if sel_todos_meses:
        selected_meses = st.multiselect("Meses del Periodo (2026)", meses_disponibles, default=meses_disponibles)
    else:
        selected_meses = st.multiselect("Meses del Periodo (2026)", meses_disponibles, default=meses_disponibles[:3])

    if not selected_meses:
        st.warning("⚠️ Selecciona al menos un mes.")
        st.stop()

    # Dataset final filtrado
    df_filtered = df_filtered_props[df_filtered_props['mes'].isin(selected_meses)].copy()

    st.markdown("---")
    st.subheader("📥 Descarga de Datasets")
    csv_clean_bytes = df_raw.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📄 Descargar Dataset Clean (CSV)",
        data=csv_clean_bytes,
        file_name="portafolio_inmuebles_clean.csv",
        mime="text/csv",
        use_container_width=True,
    )

    if os.path.exists(LOCAL_RAW_PATH):
        with open(LOCAL_RAW_PATH, 'rb') as f:
            raw_bytes = f.read()
        st.download_button(
            label="📦 Descargar Dataset Raw (CSV)",
            data=raw_bytes,
            file_name="portafolio_inmuebles_raw.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ==============================================================================
# 5. ENCABEZADO Y KPIS PRINCIPALES DEL PORTAFOLIO
# ==============================================================================

st.markdown("<h1 class='main-title'>Gestión de Portafolio Inmobiliario y Rentas</h1>", unsafe_allow_html=True)
st.markdown(
    "<p class='sub-title'>Monitoreo integral de ingresos por rentas, gastos operativos, flujo de caja neto y valuación patrimonial "
    "de 11 activos en Colima, Villa de Álvarez y Manzanillo (Enero a Octubre 2026).</p>",
    unsafe_allow_html=True,
)

# Cálculos de KPIs
total_ingresos = df_filtered['ingreso_renta'].sum()
total_gastos = df_filtered['gasto_operativo'].sum()
total_utilidad = df_filtered['utilidad_neta'].sum()
margen_neto = (total_utilidad / total_ingresos * 100) if total_ingresos > 0 else 0

# Valor patrimonial único por propiedad seleccionada
df_props_unicas = df_filtered.drop_duplicates('propiedad')
total_patrimonio = df_props_unicas['valor_propiedad'].sum()
num_activos = len(df_props_unicas)

col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

with col_kpi1:
    st.metric(
        label="💵 Ingresos por Rentas",
        value=f"${total_ingresos:,.0f} MXN",
        delta=f"{len(selected_meses)} meses activos",
    )

with col_kpi2:
    st.metric(
        label="📉 Gastos Operativos",
        value=f"${total_gastos:,.0f} MXN",
        delta=f"{(total_gastos/total_ingresos*100 if total_ingresos > 0 else 0):.1f}% de ingresos",
        delta_color="inverse",
    )

with col_kpi3:
    st.metric(
        label="📈 Utilidad Neta",
        value=f"${total_utilidad:,.0f} MXN",
        delta=f"{margen_neto:.1f}% margen neto",
    )

with col_kpi4:
    st.metric(
        label="🏛️ Valor Total de Activos",
        value=f"${total_patrimonio:,.0f} MXN",
        delta=f"{num_activos} activos filtrados",
    )

st.markdown("---")


# ==============================================================================
# 6. PESTAÑAS ANALÍTICAS (3 PESTAÑAS - 6 GRÁFICAS ESTABLECIDAS)
# ==============================================================================

tab_flujo, tab_operativo, tab_patrimonio = st.tabs([
    "📈 Flujo de Caja y Rentas",
    "🔧 Análisis Operativo y Rentabilidad",
    "💳 Composición Patrimonial y Activos"
])

# ------------------------------------------------------------------------------
# PESTAÑA 1: FLUJO DE CAJA MENSUAL Y RANKING DE RENTAS (HERO + BARRAS + PIE)
# ------------------------------------------------------------------------------
with tab_flujo:
    # 1. HERO CHART (Línea temporal a ancho completo)
    st.subheader("¿Cómo evoluciona el flujo de caja mensual (ingresos, gastos y utilidad neta) de enero a octubre?")
    
    # Agrupar por mes ordenado
    df_mes = (
        df_filtered.groupby(['num_mes', 'mes'])[['ingreso_renta', 'gasto_operativo', 'utilidad_neta']]
        .sum()
        .reset_index()
        .sort_values('num_mes')
    )

    if not df_mes.empty:
        fig_hero, ax_hero = plt.subplots(figsize=(10, 4.2))
        ax_hero.plot(
            df_mes['mes'],
            df_mes['ingreso_renta'],
            label='Ingresos por Rentas',
            color='#3182ce',
            lw=2.2,
            linestyle='--',
            marker='s'
        )
        ax_hero.plot(
            df_mes['mes'],
            df_mes['gasto_operativo'],
            label='Gastos Operativos',
            color='#e53e3e',
            lw=2.2,
            marker='^'
        )
        ax_hero.plot(
            df_mes['mes'],
            df_mes['utilidad_neta'],
            label='Utilidad Neta',
            color='#2b6cb0',
            lw=2.8,
            marker='o'
        )

        ax_hero.axhline(0, color='gray', linestyle=':', alpha=0.7)
        ax_hero.fill_between(
            df_mes['mes'],
            df_mes['utilidad_neta'],
            0,
            where=(df_mes['utilidad_neta'] >= 0),
            color='#c6f6d5',
            alpha=0.45,
            label='Superávit Líquido'
        )
        ax_hero.fill_between(
            df_mes['mes'],
            df_mes['utilidad_neta'],
            0,
            where=(df_mes['utilidad_neta'] < 0),
            color='#fed7d7',
            alpha=0.45,
            label='Déficit / Inversión de Capital'
        )

        # Anotaciones numéricas en ganancia neta
        for m, val in zip(df_mes['mes'], df_mes['utilidad_neta']):
            ax_hero.annotate(
                f"${val/1000:,.1f}k",
                (m, val),
                textcoords="offset points",
                xytext=(0, 8 if val >= 0 else -14),
                ha='center',
                fontsize=8,
                fontweight='bold',
                color='#1a365d' if val >= 0 else '#9b2c2c',
            )

        ax_hero.set_ylabel("Monto en MXN")
        ax_hero.yaxis.set_major_formatter('${x:,.0f}')
        ax_hero.grid(True, linestyle='--', alpha=0.5)
        ax_hero.legend(loc='upper right', fontsize=8.5)
        plt.tight_layout()
        st.pyplot(fig_hero)
        st.caption(
            "📊 **Insight clave del Flujo de Caja:** Durante enero y febrero se registraron fuertes inversiones de adecuación "
            "y capital ($145,661 y $141,136 MXN en paneles solares, caseta y mantenimiento mayor), provocando un saldo negativo temporal. "
            "A partir de marzo, el flujo operativo se normalizó con gastos mínimos ($8,100 - $11,350 MXN), estabilizando una **utilidad neta mensual constante superior a $84,000 MXN**."
        )
    else:
        st.info("No hay datos disponibles para los filtros seleccionados.")

    st.markdown("---")

    # Fila de 2 Columnas: Barras de Rentas vs Pie de Rentabilidad
    col_bar, col_pie = st.columns(2)

    with col_bar:
        st.subheader("¿Cuáles son las propiedades que generan mayor ingreso por renta mensual?")
        df_rentas = (
            df_filtered[df_filtered['renta_mensual'] > 0]
            .drop_duplicates('propiedad')
            .sort_values('renta_mensual', ascending=True)
        )

        if not df_rentas.empty:
            fig_bar, ax_bar = plt.subplots(figsize=(8, 4.8))
            bars = ax_bar.barh(
                df_rentas['propiedad'],
                df_rentas['renta_mensual'],
                color='#319795',
                height=0.65,
                edgecolor='black',
                linewidth=0.5
            )
            max_r = df_rentas['renta_mensual'].max()
            for bar in bars:
                w = bar.get_width()
                ax_bar.text(
                    w + max_r * 0.015,
                    bar.get_y() + bar.get_height() / 2,
                    f"${w:,.0f} MXN",
                    va='center',
                    fontsize=8.5,
                    fontweight='bold',
                    color='#234e52'
                )
            ax_bar.set_xlabel("Renta Mensual Fija (MXN)")
            ax_bar.xaxis.set_major_formatter('${x:,.0f}')
            ax_bar.set_xlim(0, max_r * 1.25)
            ax_bar.grid(True, linestyle='--', alpha=0.5, axis='x')
            plt.tight_layout()
            st.pyplot(fig_bar)
            st.caption(
                "🏢 **Insight clave:** El terreno **Aguacatera ($19,000 MXN)**, el departamento **Ceibas Manzanillo ($16,500 MXN)** "
                "y la casa **Carlos Chávez ($15,500 MXN)** representan el 53.5% de la captación mensual por arrendamiento ($51,000 de $95,400 MXN)."
            )
        else:
            st.info("Sin propiedades con renta activa en la selección.")

    with col_pie:
        st.subheader("¿Cómo se distribuyen los ingresos por rentas? (Gastos vs. Ganancia Neta)")
        
        tot_rentas = df_filtered['ingreso_renta'].sum()
        tot_gastos_sel = df_filtered['gasto_operativo'].sum()
        tot_ganancia_sel = df_filtered['utilidad_neta'].sum()

        if tot_rentas > 0:
            fig_pie, ax_pie = plt.subplots(figsize=(8, 4.6))
            pie_vals = [tot_ganancia_sel, tot_gastos_sel]
            pie_labels = ['Ganancia Neta', 'Gastos Operativos']
            pie_colors = ['#2b6cb0', '#e53e3e']

            wedges, texts, autotexts = ax_pie.pie(
                pie_vals,
                labels=None,
                autopct='%1.1f%%',
                pctdistance=0.55,
                startangle=140,
                colors=pie_colors,
                explode=[0.03, 0.03],
                textprops={'fontsize': 10.5, 'weight': 'bold', 'color': 'white'},
                wedgeprops={'edgecolor': 'white', 'linewidth': 2},
            )
            for at in autotexts:
                at.set_color('white')
            ax_pie.axis('equal')
            
            labels_legend = [
                f"{lbl}: ${val:,.0f} MXN ({val/tot_rentas*100:.1f}%)"
                for lbl, val in zip(pie_labels, pie_vals)
            ]
            ax_pie.legend(
                wedges,
                labels_legend,
                title='Destino del Ingreso',
                loc='center left',
                bbox_to_anchor=(1.02, 0.5),
                fontsize=9,
                title_fontsize=10,
            )
            plt.tight_layout()
            st.pyplot(fig_pie)
            st.caption(
                f"⚖️ **Insight clave:** Del total de ingresos captados (${tot_rentas:,.0f} MXN), el **{tot_ganancia_sel/tot_rentas*100:.1f}%** "
                f"(${tot_ganancia_sel:,.0f} MXN) se consolidó como utilidad neta líquida, mientras que el **{tot_gastos_sel/tot_rentas*100:.1f}%** "
                f"(${tot_gastos_sel:,.0f} MXN) fue absorbido por gastos y remodelaciones."
            )
        else:
            st.info("Sin ingresos registrados en el periodo seleccionado.")


# ------------------------------------------------------------------------------
# PESTAÑA 2: ANÁLISIS OPERATIVO Y DISPERSIÓN (BOXPLOT + SCATTER)
# ------------------------------------------------------------------------------
with tab_operativo:
    col_box, col_scatter = st.columns(2)

    with col_box:
        st.subheader("¿Cómo se distribuyen y varían los gastos mensuales según la categoría de activo?")
        
        cats_presentes = [c for c in ['Casas', 'Terrenos', 'Departamento', 'Vehículos'] if c in df_filtered['categoria'].unique()]
        
        if cats_presentes and len(df_filtered) > 0:
            fig_box, ax_box = plt.subplots(figsize=(8, 4.8))
            sns.boxplot(
                data=df_filtered,
                x='gasto_operativo',
                y='categoria',
                hue='categoria',
                order=cats_presentes,
                palette=PALETA_CATEGORIAS,
                legend=False,
                ax=ax_box,
                linewidth=1.2,
                fliersize=3.5,
                boxprops=dict(alpha=0.85),
            )
            ax_box.set_xlabel("Gasto Mensual por Activo (MXN)")
            ax_box.set_ylabel("")
            ax_box.xaxis.set_major_formatter('${x:,.0f}')
            ax_box.grid(True, linestyle='--', alpha=0.5)
            plt.tight_layout()
            st.pyplot(fig_box)
            st.caption(
                "📦 **Insight clave de Dispersión:** Las categorías de **Terrenos** y **Casas** presentan valores atípicos notables "
                "(Gasera 1 con $80,000 en caseta y Carlos Chávez con $74,227 en paneles solares), mientras que **Departamento** y **Vehículos** "
                "mantienen gastos operativos estables y contenidos (promedio de $1,500 MXN mensuales por cuota de coto y combustible)."
            )
        else:
            st.info("Sin registros de gastos para graficar boxplot.")

    with col_scatter:
        st.subheader("¿Existe una relación directa entre el valor comercial del inmueble y su renta mensual?")
        
        df_inm = df_filtered[df_filtered['renta_mensual'] > 0].drop_duplicates('propiedad')

        if len(df_inm) >= 2:
            fig_scat, ax_scat = plt.subplots(figsize=(8, 4.8))
            sns.scatterplot(
                data=df_inm,
                x='valor_propiedad',
                y='renta_mensual',
                hue='categoria',
                palette=PALETA_CATEGORIAS,
                s=95,
                edgecolor='black',
                linewidth=0.6,
                alpha=0.9,
                ax=ax_scat,
            )

            # Regresión lineal
            x_vals = df_inm['valor_propiedad'].values
            y_vals = df_inm['renta_mensual'].values
            if np.std(x_vals) > 0 and np.std(y_vals) > 0:
                m_pend, b_inter = np.polyfit(x_vals, y_vals, 1)
                r_corr = np.corrcoef(x_vals, y_vals)[0, 1]
                x_line = np.linspace(x_vals.min() * 0.9, x_vals.max() * 1.1, 100)
                ax_scat.plot(
                    x_line,
                    m_pend * x_line + b_inter,
                    color='#e53e3e',
                    linestyle='--',
                    lw=1.8,
                    label=f'Tendencia lineal (R = {r_corr:.2f})'
                )

            for _, row in df_inm.iterrows():
                ax_scat.annotate(
                    row['propiedad'],
                    (row['valor_propiedad'], row['renta_mensual']),
                    textcoords="offset points",
                    xytext=(0, 6),
                    ha='center',
                    fontsize=7.5,
                )

            ax_scat.set_xlabel("Valor Comercial Estimado (MXN)")
            ax_scat.set_ylabel("Renta Mensual Fija (MXN)")
            ax_scat.xaxis.set_major_formatter('${x:,.0f}')
            ax_scat.yaxis.set_major_formatter('${x:,.0f}')
            ax_scat.legend(loc='upper left', fontsize=8)
            ax_scat.grid(True, linestyle='--', alpha=0.5)
            plt.tight_layout()
            st.pyplot(fig_scat)
            st.caption(
                f"⏱️ **Insight clave de Rentabilidad (Cap Rate):** Existe una correlación positiva sólida ($R = {r_corr:.2f}$) "
                "entre el valor comercial y el canon de arrendamiento. Las propiedades habitacionales (Ceibas, Carlos Chávez, Moscú) "
                "ofrecen un retorno anualizado (*Cap Rate*) de entre 5.3% y 7.2%, alineado a la tasa óptima del mercado patrimonial."
            )
        else:
            st.info("Se requieren al menos 2 propiedades con renta para generar la dispersión.")


# ------------------------------------------------------------------------------
# PESTAÑA 3: DISTRIBUCIÓN PATRIMONIAL (GRÁFICA DE DONA)
# ------------------------------------------------------------------------------
with tab_patrimonio:
    st.subheader("¿Cómo se distribuye el valor patrimonial total del portafolio según el tipo de activo?")

    df_activos_unicos = df_filtered.drop_duplicates('propiedad')
    val_por_cat = df_activos_unicos.groupby('categoria')['valor_propiedad'].sum().sort_values(ascending=False)
    patrimonio_total_sel = val_por_cat.sum()

    if patrimonio_total_sel > 0:
        etiquetas_dona = val_por_cat.index.tolist()
        valores_dona = val_por_cat.values.tolist()
        colores_dona = [PALETA_CATEGORIAS.get(c, '#718096') for c in etiquetas_dona]

        fig_dona, ax_dona = plt.subplots(figsize=(8.5, 4.8))
        wedges, texts, autotexts = ax_dona.pie(
            valores_dona,
            labels=None,
            autopct='%1.1f%%',
            pctdistance=0.76,
            startangle=140,
            colors=colores_dona,
            wedgeprops=dict(width=0.42, edgecolor='white', linewidth=2),
            textprops=dict(fontsize=9, fontweight='bold', color='white'),
        )

        # Centro de la dona
        ax_dona.text(0, 0.08, 'Valor Patrimonial', ha='center', va='center', fontsize=9, color='#718096')
        ax_dona.text(
            0,
            -0.08,
            f"${patrimonio_total_sel:,.0f}\nMXN",
            ha='center',
            va='center',
            fontsize=11,
            fontweight='bold',
            color='#1a202c',
        )

        legend_labels = [
            f"{cat}: ${val:,.0f} MXN ({val/patrimonio_total_sel*100:.1f}%)"
            for cat, val in zip(etiquetas_dona, valores_dona)
        ]
        ax_dona.legend(
            wedges,
            legend_labels,
            title='Tipo de Activo',
            loc='center left',
            bbox_to_anchor=(1.02, 0.5),
            fontsize=8.5,
            title_fontsize=9.5,
        )
        ax_dona.axis('equal')
        plt.tight_layout()
        st.pyplot(fig_dona)

        # Tarjetas cuantitativas por categoría
        cols_tarjetas = st.columns(len(etiquetas_dona))
        for col_t, (cat_nombre, val_cat_num) in zip(cols_tarjetas, val_por_cat.items()):
            pct = (val_cat_num / patrimonio_total_sel) * 100
            col_t.metric(
                label=cat_nombre,
                value=f"${val_cat_num:,.0f} MXN",
                delta=f"{pct:.1f}% del portafolio",
            )

        st.caption(
            f"🏛️ **Insight clave de Composición Patrimonial:** El portafolio totaliza **${patrimonio_total_sel:,.0f} MXN** "
            "distribuido estratégicamente en 4 terrenos comerciales/suburbanos ($12.0M, 48.7%), 4 casas habitacionales ($9.65M, 39.1%), "
            "un departamento vacacional/residencial en Manzanillo ($2.75M, 11.2%) y activos vehiculares de soporte ($250k, 1.0%)."
        )
    else:
        st.info("Sin activos patrimoniales para graficar dona.")


# ==============================================================================
# 7. TABLA DE DATOS DETALLADA Y AUDITORÍA
# ==============================================================================

with st.expander("🔍 Ver y Explorar Dataset Detallado del Portafolio"):
    st.dataframe(
        df_filtered[['propiedad', 'categoria', 'ubicacion', 'mes', 'ingreso_renta', 'gasto_operativo', 'utilidad_neta', 'valor_propiedad']],
        use_container_width=True,
    )
