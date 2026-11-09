from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EstadoTicket(str, Enum):
    ABIERTO = "Abierto"
    EN_PROCESO = "En proceso"
    RESUELTO = "Resuelto"
    CERRADO = "Cerrado"


@dataclass
class RegistroDominio:
    """Permite que la interfaz lea entidades con la misma notación que filas SQLite."""
    aliases = {}

    def __getitem__(self, clave):
        atributo = self.aliases.get(clave, clave)
        return getattr(self, atributo)


@dataclass
class Usuario(RegistroDominio):
    """Clase base UML; la contraseña se conserva como hash para protegerla."""
    id: int | None
    nombre: str
    email: str
    login: str
    password_hash: str
    rol: str
    fecha_alta: datetime = field(default_factory=datetime.now)


@dataclass
class Cliente(Usuario):
    activo: bool = True
    telefono: str = ""
    direccion: str = ""


@dataclass
class Tecnico(Usuario):
    activo: bool = True
    disponible: bool = True
    especialidad_id: int | None = None
    especialidad_nombre: str = ""

    aliases = {"especialidad": "especialidad_nombre"}


@dataclass
class Admin(Usuario):
    def gestionar_tipo_producto(self, producto_controller, nombre, descripcion=""):
        return producto_controller.crear_tipo(nombre, descripcion)

    def asignar_ticket(self, ticket_controller, ticket_id, tecnico_id, actor_id):
        return ticket_controller.asignar(ticket_id, tecnico_id, actor_id)

    def configurar_prioridad(self, ticket_controller, ticket_id, prioridad, actor_id):
        return ticket_controller.configurar_prioridad(ticket_id, prioridad, actor_id)


@dataclass
class TipoProducto(RegistroDominio):
    id: int | None
    nombre: str
    descripcion: str = ""


@dataclass
class Producto(RegistroDominio):
    id: int | None
    nombre: str
    modelo: str
    marca: str
    descripcion: str
    tipo_id: int
    numero_serie: str = ""
    tipo_nombre: str = ""

    aliases = {"tipo": "tipo_nombre"}


@dataclass
class Mensaje(RegistroDominio):
    id: int | None
    ticket_id: int
    contenido: str
    fecha_hora: datetime
    leido: bool
    remitente_id: int
    remitente_nombre: str = ""

    aliases = {"remitente": "remitente_nombre"}


@dataclass
class Hito(RegistroDominio):
    id: int | None
    ticket_id: int
    tipo_evento: str
    detalle: str
    fecha_hora: datetime
    estado_resultante: EstadoTicket
    realizado_por: int
    realizado_por_nombre: str = ""

    aliases = {"realizado_por_nombre": "realizado_por_nombre"}


@dataclass
class Notificacion(RegistroDominio):
    id: int | None
    mensaje: str
    fecha_hora: datetime
    leida: bool
    usuario_id: int
    ticket_id: int


@dataclass
class Ticket(RegistroDominio):
    id: int | None
    titulo: str
    descripcion: str
    fecha_creacion: datetime
    fecha_cierre: datetime | None
    prioridad: str
    cliente_id: int
    tecnico_id: int
    producto_id: int
    estado: EstadoTicket = EstadoTicket.ABIERTO
    mensajes: list[Mensaje] = field(default_factory=list)
    hitos: list[Hito] = field(default_factory=list)
    notificaciones: list[Notificacion] = field(default_factory=list)
    cliente: str = ""
    tecnico: str = ""
    producto: str = ""
    numero_serie: str = ""

    def __getitem__(self, clave):
        valor=super().__getitem__(clave)
        return valor.value if clave=="estado" and isinstance(valor,EstadoTicket) else valor

    def validar_estado(self, esperado: EstadoTicket | None = None) -> bool:
        return esperado is None or self.estado == esperado

    def abrir(self):
        self.estado = EstadoTicket.ABIERTO
        self.fecha_cierre = None

    def cerrar(self):
        self.estado = EstadoTicket.CERRADO
        self.fecha_cierre = datetime.now()

    def reabrir(self):
        if not self.validar_estado(EstadoTicket.CERRADO):
            raise ValueError("Solo se pueden reabrir tickets cerrados.")
        self.estado = EstadoTicket.EN_PROCESO
        self.fecha_cierre = None

    def agregar_mensaje(self, mensaje: Mensaje):
        self.mensajes.append(mensaje)

    def agregar_hito(self, hito: Hito):
        self.hitos.append(hito)

    def agregar_notificacion(self, notificacion: Notificacion):
        self.notificaciones.append(notificacion)
