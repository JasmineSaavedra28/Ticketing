from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EstadoTicket(str, Enum):
    ABIERTO = "Abierto"
    EN_PROCESO = "En proceso"
    CERRADO = "Cerrado"


@dataclass
class Usuario:
    id: int | None
    nombre: str
    email: str
    password_hash: str
    rol: str
    especialidad_id: int | None = None


@dataclass
class TipoProducto:
    id: int
    nombre: str


@dataclass
class Producto:
    id: int | None
    nombre: str
    marca: str
    modelo: str
    tipo: TipoProducto
    numero_serie: str


@dataclass
class Mensaje:
    id: int | None
    ticket_id: int
    remitente_id: int
    contenido: str
    fecha_hora: datetime
    leido: bool = False


@dataclass
class Hito:
    id: int | None
    ticket_id: int
    tipo_evento: str
    detalle: str
    fecha_hora: datetime
    estado_resultante: EstadoTicket
    realizado_por: int


@dataclass
class Ticket:
    id: int | None
    cliente_id: int
    tecnico_id: int
    producto_id: int
    descripcion: str
    estado: EstadoTicket = EstadoTicket.ABIERTO
    fecha_creacion: datetime = field(default_factory=datetime.now)
    mensajes: list[Mensaje] = field(default_factory=list)
    hitos: list[Hito] = field(default_factory=list)


@dataclass
class Notificacion:
    id: int | None
    usuario_id: int
    ticket_id: int
    mensaje: str
    fecha_hora: datetime
    leida: bool = False
