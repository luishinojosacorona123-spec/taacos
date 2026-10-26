# Dashboard de Gestión de Portafolio Inmobiliario y Rentas 🏢📈

Dashboard interactivo y analítico desarrollado en Streamlit para el monitoreo financiero, control de flujo de caja, gastos operativos y valuación patrimonial de activos inmobiliarios en Colima, Villa de Álvarez y Manzanillo (Enero a Octubre 2026).

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

3. Ejecuta la aplicación:
   ```bash
   streamlit run taacos.py
   ```

## 📊 Arquitectura y Preguntas Analíticas Adaptadas

El dashboard implementa la arquitectura de almacenamiento de datos (`raw/` y `clean/`) y da respuesta a 6 preguntas analíticas mediante visualizaciones establecidas:

1. **📈 Flujo de Caja y Rentas (Hero Chart)**: *¿Cómo evoluciona el flujo de caja mensual (ingresos, gastos y utilidad neta) de enero a octubre?*
2. **🏢 Ranking de Captación (Gráfica de Barras Horizontales)**: *¿Cuáles son las propiedades que generan mayor ingreso por renta mensual?*
3. **⚖️ Destino de Ingresos (Gráfica de Pastel / Pie Chart)**: *¿Cómo se distribuyen los ingresos por rentas? (Gastos Operativos vs. Ganancia Neta)*
4. **📦 Dispersión Operativa (Boxplot)**: *¿Cómo se distribuyen y varían los gastos mensuales según la categoría de activo?*
5. **⏱️ Rentabilidad y Retorno (Diagrama de Dispersión / Scatter Plot)**: *¿Existe una relación directa entre el valor comercial del inmueble y su renta mensual?*
6. **💳 Composición Patrimonial (Gráfica de Dona / Donut Chart)**: *¿Cómo se distribuye el valor patrimonial total del portafolio según el tipo de activo?*
