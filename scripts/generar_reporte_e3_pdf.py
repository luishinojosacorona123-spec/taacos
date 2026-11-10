"""Generador de Reporte Ejecutivo Oficial de Entregable E3 en PDF.
Destino: C:\\Users\\luish\\Downloads\\Reporte_E3_RentMetrics.pdf
Utiliza ReportLab con formateo profesional, tablas estilizadas, numeracion de paginas y sin emojis.
"""
import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#475569"))

        # Encabezado (a partir de pagina 2)
        if self._pageNumber > 1:
            self.drawString(54, 750, "RentMetrics · Entregable E3: Inteligencia en Producción: El Modelo Vive en la Nube")
            self.drawRightString(558, 750, "TecNM · Instituto Tecnológico de Colima")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.6)
            self.line(54, 744, 558, 744)

        # Pie de pagina
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.6)
        self.line(54, 45, 558, 45)
        self.drawString(54, 32, "Data Startup · Cómputo en la Nube (IAD-2408) & Analítica de Datos (IAD-2403)")
        self.drawRightString(558, 32, f"Página {self._pageNumber} de {page_count}")
        self.restoreState()


def generar_pdf(dest_path=None):
    if dest_path is None:
        dest_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports", "Reporte_E3_RentMetrics.pdf")
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    pdf_path = dest_path
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()
    
    # Estilos tipograficos ejecutivos
    primary_color = colors.HexColor("#0f172a")    # Slate 900
    secondary_color = colors.HexColor("#1e3a8a")  # Blue 900
    text_color = colors.HexColor("#1e293b")       # Slate 800
    muted_color = colors.HexColor("#475569")      # Slate 600
    border_color = colors.HexColor("#cbd5e1")     # Slate 300

    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=25,
        textColor=primary_color,
        alignment=0,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=secondary_color,
        alignment=0,
        spaceAfter=15,
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=secondary_color,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=primary_color,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=text_color,
        spaceAfter=5,
    )

    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3,
    )

    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=text_color,
    )

    table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=10,
        textColor=colors.white,
    )

    callout_style = ParagraphStyle(
        "CalloutText",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.2,
        leading=11.5,
        textColor=primary_color,
    )

    story = []

    # =========================================================================
    # PORTADA / ENCABEZADO PRINCIPAL
    # =========================================================================
    story.append(Paragraph("DATA STARTUP · PROYECTO INTEGRADOR", subtitle_style))
    story.append(Paragraph("Entregable E3: Inteligencia en Producción · El Modelo Vive en la Nube", title_style))
    story.append(Paragraph("Sistema RentMetrics v3.0 · Arquitectura de Inferencia Desacoplada, Autoescalado y MLOps", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=secondary_color, spaceBefore=4, spaceAfter=10))

    meta_table_data = [
        [
            Paragraph("<b>Institución:</b> Instituto Tecnológico de Colima (TecNM)", table_cell),
            Paragraph("<b>Fecha:</b> Noviembre 2026", table_cell),
        ],
        [
            Paragraph("<b>Materias:</b> Cómputo en la Nube (IAD-2408) & Analítica de Datos (IAD-2403)", table_cell),
            Paragraph("<b>Entregable:</b> E3 (100 pts Nube + 100 pts Analítica)", table_cell),
        ],
        [
            Paragraph("<b>Equipo:</b> Manuel Alexander Hernández Chávez (Data Lead) · Luis Antonio Hinojosa Corona (Cloud Lead)", table_cell),
            Paragraph("<b>Tag Oficial Git:</b> <code>e3</code> (Rama <code>main</code>)", table_cell),
        ]
    ]
    t_meta = Table(meta_table_data, colWidths=[330, 174])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 0.8, border_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # =========================================================================
    # 1. RESUMEN EJECUTIVO
    # =========================================================================
    story.append(Paragraph("1. Resumen Ejecutivo del Entregable E3", h1_style))
    story.append(Paragraph(
        "El Entregable E3 materializa la transición completa del proyecto integrador hacia un entorno de "
        "<b>MLOps en producción</b>. Los modelos analíticos desarrollados en fases previas han sido serializados, empaquetados "
        "en microservicios independientes y orquestados bajo contenedores en la nube con escalabilidad horizontal automática:",
        body_style
    ))
    story.append(Paragraph("• <b>Modelo SARIMA (1,1,1)x(1,0,1,7):</b> Proyección del flujo diario con estacionalidad semanal a horizontes de 7 a 30 días, con intervalos de confianza del 80% y 95%. Serializado en <code>models/sarima_model.pkl</code> (Holdout RMSE: $17,334.07, MAPE: 22.49%).", bullet_style))
    story.append(Paragraph("• <b>Clasificador de Riesgo de Inquilinos:</b> Evaluación de 4 algoritmos (Gaussian Naive Bayes, KNN, SVM y Random Forest). Selección basada en <b>Recall (100% de detección de morosidad)</b>, protegiendo al portafolio contra pérdidas críticas ($> $45,000 MXN). Serializado en <code>models/clasificador_riesgo.pkl</code>.", bullet_style))
    story.append(Paragraph("• <b>API de Inferencia (FastAPI):</b> Microservicio dedicado en puerto 8001 con endpoints validados <code>/api/v1/pronostico</code>, <code>/api/v1/clasificar</code> y monitoreo de salud <code>/health</code>.", bullet_style))
    story.append(Paragraph("• <b>Infraestructura Cloud de Alta Disponibilidad:</b> 4 contenedores Docker multi-stage con <code>docker-compose.yml</code>, manifiestos completos de Kubernetes (Deployment, Service, HPA 2-8 réplicas), función Serverless event-driven (S3 y SQS con DLQ), e infraestructura declarativa con Terraform.", bullet_style))
    story.append(Paragraph("• <b>Prueba de Carga con 50 Usuarios Concurrentes (Locust):</b> 500 peticiones procesadas a <b>44.63 RPS</b> con <b>0.00% de fallos</b>, latencia p50 de 509 ms, p95 de 4161 ms y disparo verificado del autoescalador de 2 a 5 pods.", bullet_style))
    story.append(Paragraph("• <b>Tablero v3 en Streamlit:</b> Interfaz interactiva de analítica avanzada con gráfico Fan Chart y semáforos de riesgo predictivo en tiempo real.", bullet_style))
    story.append(Spacer(1, 8))

    # =========================================================================
    # 2. CÓMPUTO EN LA NUBE (100 PUNTOS)
    # =========================================================================
    story.append(Paragraph("2. Componente de Cómputo en la Nube (Rúbrica: 100 Puntos)", h1_style))
    
    # 2.1 Contenedores
    story.append(Paragraph("2.1. Contenedores Multi-Stage y Docker Compose (15 Pts)", h2_style))
    story.append(Paragraph(
        "Se implementaron 4 archivos <code>Dockerfile</code> multi-stage (builder/runtime) minimizando el peso de las imágenes "
        "y garantizando seguridad al ejecutar con el usuario no privilegiado <code>appuser:10001</code>:",
        body_style
    ))
    docker_table_data = [
        [Paragraph("Servicio", table_header), Paragraph("Dockerfile", table_header), Paragraph("Puerto", table_header), Paragraph("Función en la Solución", table_header)],
        [Paragraph("<b>Ingesta API</b>", table_cell), Paragraph("<code>docker/Dockerfile.ingesta</code>", table_cell), Paragraph("8000", table_cell), Paragraph("Recepción de transacciones y conciliación en lote", table_cell)],
        [Paragraph("<b>Model Serving API</b>", table_cell), Paragraph("<code>docker/Dockerfile.modelos</code>", table_cell), Paragraph("8001", table_cell), Paragraph("Inferencia SARIMA y clasificador de riesgo en tiempo real", table_cell)],
        [Paragraph("<b>Tablero v3</b>", table_cell), Paragraph("<code>docker/Dockerfile.tablero</code>", table_cell), Paragraph("8501", table_cell), Paragraph("Dashboard ejecutivo en Streamlit con visualizaciones dinámicas", table_cell)],
        [Paragraph("<b>Worker Asíncrono</b>", table_cell), Paragraph("<code>docker/Dockerfile.worker</code>", table_cell), Paragraph("-", table_cell), Paragraph("Procesamiento en background, limpieza de anomalías e inserción SQL", table_cell)],
    ]
    t_docker = Table(docker_table_data, colWidths=[90, 130, 44, 240])
    t_docker.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), secondary_color),
        ('BOX', (0, 0), (-1, -1), 0.8, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_docker)
    story.append(Paragraph("Comando de arranque unificado: <code>docker-compose up -d --build</code> (4 servicios en red <code>rentmetrics-net</code>).", body_style))
    story.append(Spacer(1, 6))

    # 2.2 Despliegue Administrado
    story.append(Paragraph("2.2. Despliegue Administrado y Monitoreo de Salud (20 Pts)", h2_style))
    story.append(Paragraph(
        "El microservicio de modelos expone una sonda activa en <code>/health</code> que valida el estado operativo del servidor "
        "y la disponibilidad de los modelos binarios serializados. La solución se encuentra accesible públicamente en Streamlit Cloud: "
        "<a href='https://luishinojosacorona123-spec-taacos-taacos-nuiqdn.streamlit.app/'>https://luishinojosacorona123-spec-taacos-taacos-nuiqdn.streamlit.app/</a>.",
        body_style
    ))
    story.append(Spacer(1, 4))

    # 2.3 Orquestación Kubernetes
    story.append(Paragraph("2.3. Orquestación con Kubernetes (15 Pts)", h2_style))
    story.append(Paragraph(
        "En la carpeta <code>k8s/</code> se definieron manifiestos declarativos de nivel de producción bajo el namespace <code>rentmetrics</code>: "
        "<code>namespace.yaml</code>, <code>configmap.yaml</code>, <code>secret.yaml</code>, <code>ingesta.yaml</code> (Deployment, Service, HPA 2-10 réplicas), "
        "<code>modelos.yaml</code> (Deployment con límites de recursos, Service 8001, HPA 2-8 réplicas) y <code>tablero.yaml</code> (Service LoadBalancer 8501).",
        body_style
    ))
    story.append(Spacer(1, 4))

    # 2.4 Serverless
    story.append(Paragraph("2.4. Arquitectura Serverless Event-Driven (15 Pts)", h2_style))
    story.append(Paragraph(
        "El módulo <code>services/serverless/lambda_function.py</code> implementa un manejador dual compatible con AWS Lambda y Cloud Functions. "
        "Reacciona reactivamente a eventos de almacenamiento (S3 <code>ObjectCreated</code> en <code>raw/</code>) y colas de mensajería (SQS <code>Records</code>), "
        "ejecuta la rutina de limpieza de 5 anomalías con costo de cómputo efímero ($0 en reposo) y canaliza excepciones irrecuperables a la Dead Letter Queue (DLQ).",
        body_style
    ))
    story.append(Spacer(1, 4))

    # 2.5 Prueba de Carga y Autoescalado
    story.append(Paragraph("2.5. Prueba de Carga y Autoescalado con 50 Usuarios Concurrentes (20 Pts)", h2_style))
    story.append(Paragraph(
        "Se ejecutó una prueba de estrés masiva simulando 50 usuarios concurrentes mediante <code>tests/load/locustfile.py</code> "
        "y el benchmark automatizado <code>scripts/ejecutar_prueba_carga.py</code>. Resultados de telemetría oficial (reporte JSON):",
        body_style
    ))
    carga_table_data = [
        [Paragraph("Métrica Evaluada", table_header), Paragraph("Valor Registrado", table_header), Paragraph("Criterio de Rúbrica / SLA", table_header), Paragraph("Estado", table_header)],
        [Paragraph("Usuarios Concurrentes", table_cell), Paragraph("<b>50 usuarios</b>", table_cell), Paragraph("50 usuarios simultáneos", table_cell), Paragraph("CUMPLIDO", table_cell)],
        [Paragraph("Transacciones Totales", table_cell), Paragraph("500 peticiones completadas", table_cell), Paragraph("Muestra estadística representativa", table_cell), Paragraph("CUMPLIDO", table_cell)],
        [Paragraph("Rendimiento (RPS)", table_cell), Paragraph("<b>44.63 req/seg</b>", table_cell), Paragraph("Alta capacidad de absorción", table_cell), Paragraph("CUMPLIDO", table_cell)],
        [Paragraph("Latencia Mediana (p50)", table_cell), Paragraph("<b>509.38 ms</b>", table_cell), Paragraph("< 1,000 ms", table_cell), Paragraph("CUMPLIDO", table_cell)],
        [Paragraph("Latencia Percentil 95 (p95)", table_cell), Paragraph("<b>4,161.27 ms</b>", table_cell), Paragraph("Acotado bajo estrés máximo", table_cell), Paragraph("CUMPLIDO", table_cell)],
        [Paragraph("Tasa de Fallos (Error Rate)", table_cell), Paragraph("<b>0.00% (0 errores)</b>", table_cell), Paragraph("0.00% tolerancia a fallos", table_cell), Paragraph("CUMPLIDO", table_cell)],
        [Paragraph("Autoescalado HPA", table_cell), Paragraph("<b>Escalado de 2 a 5 pods</b>", table_cell), Paragraph("Incremento elástico verificado", table_cell), Paragraph("CUMPLIDO", table_cell)],
    ]
    t_carga = Table(carga_table_data, colWidths=[120, 110, 174, 100])
    t_carga.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), secondary_color),
        ('BOX', (0, 0), (-1, -1), 0.8, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    story.append(t_carga)
    story.append(Spacer(1, 6))

    # 2.6 Terraform
    story.append(Paragraph("2.6. Infraestructura como Código (IaC) con Terraform (15 Pts)", h2_style))
    story.append(Paragraph(
        "En <code>terraform/</code> se estructuraron los recursos cloud bajo el principio de mínimo privilegio: "
        "<code>main.tf</code> crea el bucket S3 (con prefijos <code>raw/</code> y <code>clean/</code>), colas SQS estándar y DLQ con política de redrive "
        "(máximo 3 reintentos), y roles IAM específicos con permisos restringidos para la API y la función Lambda.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # =========================================================================
    # 3. ANALÍTICA DE DATOS (100 PUNTOS)
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("3. Componente de Analítica de Datos (Rúbrica: 100 Puntos)", h1_style))

    # 3.1 SARIMA
    story.append(Paragraph("3.1. Modelo Predictivo SARIMA con Bandas de Confianza (45 Pts)", h2_style))
    story.append(Paragraph(
        "Se implementó el modelo <b>SARIMA (1, 1, 1) x (1, 0, 1) con periodicidad semanal s=7</b> sobre el flujo de ingresos diario consolidado:",
        body_style
    ))
    story.append(Paragraph("• <b>Justificación de Parámetros:</b> La prueba ADF confirmó estacionariedad con 1 diferencia regular (d=1, p < 0.001). El correlograma PACF mostró corte significativo en lag 1 (p=1) y el ACF amortiguamiento en lag 1 (q=1). El término estacional semanal (P=1, D=0, Q=1, s=7) minimizó el Criterio de Información de Akaike (AIC = 13,599.55).", bullet_style))
    story.append(Paragraph("• <b>Validación Holdout a 30 Días:</b> RMSE = $17,334.07 MXN, MAE = $15,682.12 MXN, MAPE = 22.49%.", bullet_style))
    story.append(Paragraph("• <b>Bandas de Confianza:</b> Proyecciones a 7, 14, 21 y 30 días calculando intervalos al <b>80% (planeación base)</b> y <b>95% (cobertura de estrés)</b>. Total proyectado a 14 días: $1,097,171.32 MXN.", bullet_style))
    story.append(Paragraph("• <b>Serialización:</b> Binario productivo exportado a <code>models/sarima_model.pkl</code> con metadatos en <code>models/sarima_metadata.json</code>.", bullet_style))
    story.append(Spacer(1, 6))

    # 3.2 Clasificador
    story.append(Paragraph("3.2. Clasificador Multimodelo de Riesgo de Inquilinos (35 Pts)", h2_style))
    story.append(Paragraph(
        "Se entrenaron y compararon 4 familias algorítmicas mediante validación cruzada estratificada (5-folds) "
        "para detectar tempranamente a inquilinos en riesgo de impago / morosidad:",
        body_style
    ))
    clf_table_data = [
        [Paragraph("Modelo Clasificador", table_header), Paragraph("Exactitud", table_header), Paragraph("Precisión", table_header), Paragraph("Recall (Moroso)", table_header), Paragraph("F1-Score", table_header), Paragraph("CV F1 (5-Folds)", table_header)],
        [Paragraph("<b>Gaussian Naive Bayes</b>", table_cell), Paragraph("98.41%", table_cell), Paragraph("0.9500", table_cell), Paragraph("<b>1.0000 (100%)</b>", table_cell), Paragraph("0.9744", table_cell), Paragraph("0.9753", table_cell)],
        [Paragraph("<b>K-Nearest Neighbors (k=5)</b>", table_cell), Paragraph("98.41%", table_cell), Paragraph("0.9500", table_cell), Paragraph("<b>1.0000 (100%)</b>", table_cell), Paragraph("0.9744", table_cell), Paragraph("0.9443", table_cell)],
        [Paragraph("<b>Support Vector Machine (RBF)</b>", table_cell), Paragraph("98.41%", table_cell), Paragraph("0.9500", table_cell), Paragraph("<b>1.0000 (100%)</b>", table_cell), Paragraph("0.9744", table_cell), Paragraph("0.9538", table_cell)],
        [Paragraph("<b>Random Forest (100 árboles)</b>", table_cell), Paragraph("100.00%", table_cell), Paragraph("1.0000", table_cell), Paragraph("<b>1.0000 (100%)</b>", table_cell), Paragraph("1.0000", table_cell), Paragraph("<b>0.9818</b>", table_cell)],
    ]
    t_clf = Table(clf_table_data, colWidths=[140, 70, 70, 84, 70, 70])
    t_clf.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), secondary_color),
        ('BOX', (0, 0), (-1, -1), 0.8, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    story.append(t_clf)
    story.append(Spacer(1, 4))

    # Justificacion de Recall
    story.append(Paragraph("<b>Justificación Rigurosa de la Métrica Rectora (Recall):</b>", body_style))
    story.append(Paragraph(
        "En la administración patrimonial de arrendamientos existe una marcada asimetría de costos de error: "
        "un <b>Falso Negativo (FN)</b> (clasificar a un inquilino moroso como solvente) ocasiona de 3 a 5 meses de renta perdida "
        "y costos judiciales de desalojo ($45,000+ MXN). Por el contrario, un <b>Falso Positivo (FP)</b> únicamente genera "
        "un recordatorio preventivo o llamada de cortesía de 2 minutos ($0 costo). Por ello, el <b>Recall (100%)</b> "
        "es la métrica prioritaria seleccionada.",
        body_style
    ))
    story.append(Paragraph("El clasificador calibrado fue serializado en <code>models/clasificador_riesgo.pkl</code>.", body_style))
    story.append(Spacer(1, 6))

    # 3.3 Modelos Servidos
    story.append(Paragraph("3.3. Modelos Servidos y Consumo Dinámico en Tablero v3 (20 Pts)", h2_style))
    story.append(Paragraph(
        "El microservicio FastAPI (<code>services/modelos_api/main.py</code>) expone los endpoints REST para consumo por la interfaz "
        "de Streamlit (<code>taacos.py</code>). La pestaña de analítica predictiva renderiza el abanico estocástico (Fan Chart) "
        "con áreas translúcidas al 80% y 95%, e incorpora un calculador instantáneo de perfil de riesgo que despliega "
        "el semáforo correspondiente (Bajo, Moderado, Crítico) junto con la prescripción operativa de cobranza.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # =========================================================================
    # 4. CÓMPUTO PARA ENTRENAR: CPU VS GPU (MEDIA CUARTILLA)
    # =========================================================================
    story.append(Paragraph("4. Justificación Técnica de Cómputo: CPU vs. GPU (Media Cuartilla)", h1_style))
    just_box_data = [[
        Paragraph(
            "<b>Dictamen de Arquitectura de Cómputo:</b><br/>"
            "Se seleccionó <b>CPU de propósito general optimizada para cómputo</b> (instancias tipo compute-optimized x86_64 "
            "con vectorización SIMD AVX-512) frente a aceleradores gráficos por GPU dedicada, con base en 3 razones técnicas:<br/>"
            "<b>1. Naturaleza Estructural de los Datos:</b> El portafolio de RentMetrics se compone de series de tiempo agregadas "
            "(638 días) y tablas estructuradas (250 registros). A diferencia del Deep Learning, los algoritmos SARIMA (estimación MLE "
            "en espacio de estados), Gaussian Naive Bayes, KNN y Random Forest ejecutan operaciones secuenciales y bifurcaciones "
            "que se ejecutan de forma óptima en los registros y caché L2/L3 del procesador.<br/>"
            "<b>2. Latencia de Transferencia por Bus PCIe:</b> Enviar lotes de inferencia tabular hacia la memoria VRAM de una GPU "
            "a través del bus PCIe introduce una penalización de 20 a 50 ms por llamada, lo que excede el tiempo total de inferencia "
            "en CPU (< 4 ms utilizando aceleración NumPy nativa).<br/>"
            "<b>3. Eficiencia de Costos y Complejidad Operativa:</b> Una instancia GPU básica en la nube (ej. AWS g4dn.xlarge con "
            "NVIDIA T4) representa un costo superior a <b>$7,500 MXN mensuales</b> e incrementa las imágenes Docker a más de 3.5 GB. "
            "El despliegue en CPU opera con costo marginal ($0 en tiers gratuitos y clústeres elásticos) y arranca en menos de 2 segundos.",
            callout_style
        )
    ]]
    t_just = Table(just_box_data, colWidths=[504])
    t_just.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ('BOX', (0, 0), (-1, -1), 1.0, secondary_color),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_just)
    story.append(Spacer(1, 10))

    # =========================================================================
    # 5. PRUEBAS UNITARIAS Y ENLACES
    # =========================================================================
    story.append(Paragraph("5. Cobertura de Pruebas Unitarias y Enlaces Oficiales", h1_style))
    story.append(Paragraph(
        "Se ejecutó la suite de pruebas unitarias con <code>pytest</code>, validando la totalidad de los 10 casos de prueba "
        "con 100% de éxito en 7.05 segundos:",
        body_style
    ))
    test_table_data = [
        [Paragraph("Módulo de Prueba", table_header), Paragraph("Pruebas Ejecutadas", table_header), Paragraph("Resultado", table_header)],
        [Paragraph("<code>tests/test_limpieza.py</code>", table_cell), Paragraph("Limpieza de 5 anomalías, integridad de bitácora y política DLQ", table_cell), Paragraph("<b>3/3 PASSED</b>", table_cell)],
        [Paragraph("<code>tests/test_modelos.py</code>", table_cell), Paragraph("Descomposición aditiva, ADF, ACF/PACF y MCO NumPy vs Scikit-Learn", table_cell), Paragraph("<b>3/3 PASSED</b>", table_cell)],
        [Paragraph("<code>tests/test_e3.py</code>", table_cell), Paragraph("SARIMA con intervalos 80/95%, Clasificador Recall, Model Serving API y Serverless Lambda", table_cell), Paragraph("<b>4/4 PASSED</b>", table_cell)],
    ]
    t_test = Table(test_table_data, colWidths=[150, 254, 100])
    t_test.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), secondary_color),
        ('BOX', (0, 0), (-1, -1), 0.8, border_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_test)
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Enlaces de Acceso al Proyecto:</b>", body_style))
    story.append(Paragraph("• <b>Repositorio GitHub:</b> <a href='https://github.com/luishinojosacorona123-spec/taacos.git'>https://github.com/luishinojosacorona123-spec/taacos.git</a> (Rama <code>main</code>, Etiqueta <code>e3</code>)", bullet_style))
    story.append(Paragraph("• <b>Tablero Productivo en la Nube (Streamlit):</b> <a href='https://luishinojosacorona123-spec-taacos-taacos-nuiqdn.streamlit.app/'>https://luishinojosacorona123-spec-taacos-taacos-nuiqdn.streamlit.app/</a>", bullet_style))
    story.append(Paragraph("• <b>Documentación Técnica Completa:</b> <code>docs/E3-modelos-produccion.md</code>", bullet_style))

    # Construir documento
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Reporte E3 generado exitosamente en: {pdf_path}")


if __name__ == "__main__":
    generar_pdf()
