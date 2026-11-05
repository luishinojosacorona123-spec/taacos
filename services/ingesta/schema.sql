-- Esquema Relacional de Base de Datos para RentMetrics / PropTech Colima
-- Compatible con PostgreSQL y SQLite
-- Modelo transaccional ACID en Tercera Forma Normal (3NF)

CREATE TABLE IF NOT EXISTS activos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE NOT NULL,
    categoria VARCHAR(30) NOT NULL,
    ubicacion VARCHAR(50) NOT NULL,
    valor_propiedad NUMERIC(12, 2) NOT NULL,
    renta_mensual NUMERIC(10, 2) NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS operaciones_diarias (
    id SERIAL PRIMARY KEY,
    fecha DATE NOT NULL,
    producto VARCHAR(50) NOT NULL,
    categoria VARCHAR(30) NOT NULL,
    ubicacion VARCHAR(50) NOT NULL,
    unidades INT NOT NULL,
    precio_unitario NUMERIC(10, 2) NOT NULL,
    total NUMERIC(12, 2) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'RAW', -- 'RAW', 'CLEAN', 'REJECTED'
    ingesta_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS consolidado_mensual (
    id SERIAL PRIMARY KEY,
    propiedad VARCHAR(50) NOT NULL,
    categoria VARCHAR(30) NOT NULL,
    ubicacion VARCHAR(50) NOT NULL,
    valor_propiedad NUMERIC(12, 2) NOT NULL,
    renta_mensual NUMERIC(10, 2) NOT NULL,
    mes VARCHAR(20) NOT NULL,
    num_mes INT NOT NULL,
    ingreso_renta NUMERIC(12, 2) NOT NULL,
    gasto_operativo NUMERIC(12, 2) NOT NULL,
    utilidad_neta NUMERIC(12, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_propiedad_mes UNIQUE (propiedad, num_mes)
);

CREATE TABLE IF NOT EXISTS ingesta_logs (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(100) UNIQUE NOT NULL,
    origen VARCHAR(50) NOT NULL, -- 'API_REST', 'CSV_UPLOAD'
    archivo_raw VARCHAR(255),
    total_registros INT NOT NULL,
    registros_limpios INT DEFAULT 0,
    estado VARCHAR(30) NOT NULL, -- 'RECEIVED', 'QUEUED', 'PROCESSED', 'FAILED', 'DLQ'
    reintentos INT DEFAULT 0,
    error_detalle TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices de alto rendimiento para consultas analiticas y particionado logico
CREATE INDEX IF NOT EXISTS idx_operaciones_fecha ON operaciones_diarias (fecha);
CREATE INDEX IF NOT EXISTS idx_operaciones_producto ON operaciones_diarias (producto);
CREATE INDEX IF NOT EXISTS idx_operaciones_estado ON operaciones_diarias (estado);
CREATE INDEX IF NOT EXISTS idx_consolidado_mes ON consolidado_mensual (num_mes);
CREATE INDEX IF NOT EXISTS idx_ingesta_estado ON ingesta_logs (estado);
