"""Capa de persistencia y conexion a Base de Datos (PostgreSQL / SQLite).
Soporta conexion a AWS RDS for PostgreSQL o base de datos local embebida con SQLAlchemy.
"""
import os
from datetime import datetime
from typing import Generator
from sqlalchemy import (
    create_engine, Column, Integer, String, Numeric, Date, DateTime, Text, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_SQLITE_PATH = os.path.join(BASE_DIR, "data", "taacos.db")

# Si existe DATABASE_URL (ej. en AWS RDS o contenedor), se usa; de lo contrario, SQLite local
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")

os.makedirs(os.path.dirname(DEFAULT_SQLITE_PATH), exist_ok=True)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ActivoModel(Base):
    __tablename__ = "activos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(50), unique=True, nullable=False, index=True)
    categoria = Column(String(30), nullable=False)
    ubicacion = Column(String(50), nullable=False)
    valor_propiedad = Column(Numeric(12, 2), nullable=False)
    renta_mensual = Column(Numeric(10, 2), nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class OperacionDiariaModel(Base):
    __tablename__ = "operaciones_diarias"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fecha = Column(Date, nullable=False, index=True)
    producto = Column(String(50), nullable=False, index=True)
    categoria = Column(String(30), nullable=False)
    ubicacion = Column(String(50), nullable=False)
    unidades = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(12, 2), nullable=False)
    estado = Column(String(20), nullable=False, default="RAW", index=True)  # RAW, CLEAN, REJECTED
    ingesta_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ConsolidadoMensualModel(Base):
    __tablename__ = "consolidado_mensual"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    propiedad = Column(String(50), nullable=False, index=True)
    categoria = Column(String(30), nullable=False)
    ubicacion = Column(String(50), nullable=False)
    valor_propiedad = Column(Numeric(12, 2), nullable=False)
    renta_mensual = Column(Numeric(10, 2), nullable=False)
    mes = Column(String(20), nullable=False)
    num_mes = Column(Integer, nullable=False, index=True)
    ingreso_renta = Column(Numeric(12, 2), nullable=False)
    gasto_operativo = Column(Numeric(12, 2), nullable=False)
    utilidad_neta = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("propiedad", "num_mes", name="uq_propiedad_num_mes"),
    )


class IngestaLogModel(Base):
    __tablename__ = "ingesta_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    batch_id = Column(String(100), unique=True, nullable=False, index=True)
    origen = Column(String(50), nullable=False)  # API_REST, CSV_UPLOAD
    archivo_raw = Column(String(255), nullable=True)
    total_registros = Column(Integer, nullable=False)
    registros_limpios = Column(Integer, default=0)
    estado = Column(String(30), nullable=False, default="RECEIVED", index=True)  # RECEIVED, QUEUED, PROCESSED, FAILED, DLQ
    reintentos = Column(Integer, default=0)
    error_detalle = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    """Inicializa todas las tablas en la base de datos."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Generador de sesion para inyeccion de dependencias en FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
