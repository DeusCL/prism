import enum

from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Integer, Boolean, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship



class Base(DeclarativeBase):
    pass


# Enums para campos con valores específicos
class EstadoEnum(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class EstadoConversacionEnum(enum.Enum):
    IA_RESPONDIENDO = "ia_respondiendo"
    ESPERANDO_HUMANO = "esperando_humano"
    FINALIZADA = "finalizada"


class TipoMensajeEnum(enum.Enum):
    CLIENTE = "cliente"
    IA = "ia"
    HUMANO = "humano"
    SISTEMA = "sistema"


class ConfiguracionIA(Base):
    """Configuración global de la IA - Singleton"""
    __tablename__ = "configuracion_ia"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    temperatura: Mapped[float] = mapped_column(nullable=False, default=0.7)
    min_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    model: Mapped[str] = mapped_column(String(100), nullable=False, default="gpt-4")
    auto_derivacion_activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<ConfiguracionIA(id={self.id}, model='{self.model}', temperatura={self.temperatura})>"


class Area(Base):
    """Áreas de especialización de Biplan"""
    __tablename__ = "areas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    instrucciones: Mapped[str] = mapped_column(Text, nullable=False)
    estado: Mapped[EstadoEnum] = mapped_column(Enum(EstadoEnum), nullable=False, default=EstadoEnum.ACTIVE)
    tiempo_respuesta: Mapped[Optional[int]] = mapped_column(Integer)  # en minutos
    especialista_asignado: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relaciones
    conversaciones: Mapped[List["Conversacion"]] = relationship(
        "Conversacion",
        back_populates="area_derivada",
        foreign_keys="Conversacion.id_area_derivada"
    )
    clientes: Mapped[List["Cliente"]] = relationship(
        "Cliente",
        back_populates="area_asignada",
        foreign_keys="Cliente.id_area_asignada"
    )

    def __repr__(self) -> str:
        return f"<Area(id={self.id}, nombre='{self.nombre}', estado='{self.estado.value}')>"


class Cliente(Base):
    """Clientes que interactúan con Prism"""
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    telefono: Mapped[Optional[str]] = mapped_column(String(50))  # Para simular WhatsApp
    estado: Mapped[str] = mapped_column(String(50), nullable=False, default="nuevo")  # nuevo/activo/derivado
    id_area_asignada: Mapped[Optional[int]] = mapped_column(ForeignKey("areas.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relaciones
    area_asignada: Mapped[Optional["Area"]] = relationship(
        "Area",
        back_populates="clientes",
        foreign_keys=[id_area_asignada]
    )
    conversaciones: Mapped[List["Conversacion"]] = relationship(
        "Conversacion",
        back_populates="cliente",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Cliente(id={self.id}, nombre='{self.nombre}', estado='{self.estado}')>"


class Conversacion(Base):
    """Conversaciones individuales con cada cliente"""
    __tablename__ = "conversaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_cliente: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)
    id_area_derivada: Mapped[Optional[int]] = mapped_column(ForeignKey("areas.id"))
    estado: Mapped[EstadoConversacionEnum] = mapped_column(
        Enum(EstadoConversacionEnum),
        nullable=False,
        default=EstadoConversacionEnum.IA_RESPONDIENDO
    )
    fecha_derivacion: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    cliente: Mapped["Cliente"] = relationship(
        "Cliente",
        back_populates="conversaciones",
        foreign_keys=[id_cliente]
    )
    area_derivada: Mapped[Optional["Area"]] = relationship(
        "Area",
        back_populates="conversaciones",
        foreign_keys=[id_area_derivada]
    )
    mensajes: Mapped[List["Mensaje"]] = relationship(
        "Mensaje",
        back_populates="conversacion",
        cascade="all, delete-orphan",
        order_by="Mensaje.timestamp"
    )

    def __repr__(self) -> str:
        return f"<Conversacion(id={self.id}, cliente_id={self.id_cliente}, estado='{self.estado.value}')>"


class Mensaje(Base):
    """Mensajes individuales dentro de cada conversación"""
    __tablename__ = "mensajes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_conversacion: Mapped[int] = mapped_column(ForeignKey("conversaciones.id"), nullable=False)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[TipoMensajeEnum] = mapped_column(Enum(TipoMensajeEnum), nullable=False)
    remitente: Mapped[str] = mapped_column(String(255), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    es_derivacion: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relaciones
    conversacion: Mapped["Conversacion"] = relationship(
        "Conversacion",
        back_populates="mensajes",
        foreign_keys=[id_conversacion]
    )

    def __repr__(self) -> str:
        return f"<Mensaje(id={self.id}, tipo='{self.tipo.value}', remitente='{self.remitente}', es_derivacion={self.es_derivacion})>"

