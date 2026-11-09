import hashlib
import hmac
import secrets
import sqlite3
from dominio.modelos import EstadoTicket
from persistencia.repositorios import CatalogoRepository, NotificacionRepository, TicketRepository, UsuarioRepository
from control.controllers import NotificacionController, ProductoController, TicketController


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 240_000)
    return salt.hex() + "$" + digest.hex()


def verificar_password(password: str, guardado: str) -> bool:
    try:
        salt_hex, digest_hex = guardado.split("$", 1)
        return hmac.compare_digest(hash_password(password, bytes.fromhex(salt_hex)), salt_hex + "$" + digest_hex)
    except (ValueError, TypeError):
        return False


class Servicio:
    def __init__(self, db):
        self.db=db
        self.usuarios=UsuarioRepository(db)
        self.catalogo=CatalogoRepository(db)
        self.tickets=TicketRepository(db)
        self.notificaciones=NotificacionRepository(db)
        self.producto_controller=ProductoController(self.catalogo)
        self.notificacion_controller=NotificacionController(self.notificaciones)
        self.ticket_controller=TicketController(self.tickets,self.usuarios,self.catalogo,self.notificacion_controller)
        self._crear_datos_iniciales()

    def _crear_datos_iniciales(self):
        if self.usuarios.listar(): return
        tipos=self.catalogo.tipos()
        self.usuarios.crear("Administración","admin@hitos.local",hash_password("admin123"),"Admin")
        self.usuarios.crear("Cliente Demo","cliente@hitos.local",hash_password("cliente123"),"Cliente")
        self.usuarios.crear("Técnico Electrónica","tecnico@hitos.local",hash_password("tecnico123"),"Tecnico",tipos[0]["id"])

    def login(self,email,password):
        usuario=self.usuarios.autenticar(email)
        return usuario if usuario and verificar_password(password,usuario["password_hash"]) else None

    def crear_usuario(self,nombre,email,password,rol,especialidad_id=None):
        if len(password)<6: raise ValueError("La contraseña debe tener al menos 6 caracteres.")
        if rol=="Tecnico" and not especialidad_id: raise ValueError("Seleccioná una especialidad para el técnico.")
        return self.usuarios.crear(nombre,email,hash_password(password),rol,especialidad_id)

    def crear_producto(self,nombre,marca,modelo,tipo_id,serie,descripcion=""):
        if not all(x.strip() for x in (nombre,marca,modelo,serie)): raise ValueError("Completá todos los datos del producto.")
        return self.producto_controller.crear(nombre,marca,modelo,tipo_id,serie,descripcion)

    def crear_tipo_producto(self,nombre,descripcion,usuario):
        if usuario["rol"]!="Admin": raise PermissionError("Solo un administrador puede gestionar tipos de producto.")
        if not nombre.strip(): raise ValueError("El nombre del tipo es obligatorio.")
        return self.producto_controller.crear_tipo(nombre,descripcion)

    def crear_ticket(self,cliente_id,producto_id,descripcion,titulo=None,prioridad="Media"):
        producto=self.catalogo.producto(producto_id)
        if not producto: raise ValueError("El producto seleccionado ya no existe.")
        tecnico=self.usuarios.tecnico_para_tipo(producto["tipo_id"])
        if not tecnico: raise ValueError("No hay técnicos asignados al tipo de producto seleccionado.")
        if not descripcion.strip(): raise ValueError("Ingresá una descripción del problema.")
        if prioridad not in ("Baja", "Media", "Alta", "Urgente"): raise ValueError("La prioridad seleccionada no es válida.")
        return self.ticket_controller.crear(cliente_id,tecnico["id"],producto_id,descripcion,cliente_id,titulo,prioridad)

    def enviar_mensaje(self,ticket_id,usuario,contenido):
        ticket=self.tickets.buscar(ticket_id)
        if not ticket: raise ValueError("No se encontró el ticket.")
        if usuario["id"] not in (ticket["cliente_id"],ticket["tecnico_id"]) and usuario["rol"]!="Admin": raise PermissionError("No tenés acceso a este ticket.")
        if ticket["estado"]==EstadoTicket.CERRADO.value: raise ValueError("No se pueden enviar mensajes en un ticket cerrado. Reabrilo primero.")
        if not contenido.strip(): raise ValueError("El mensaje no puede estar vacío.")
        destinatario=ticket["tecnico_id"] if usuario["id"]==ticket["cliente_id"] else ticket["cliente_id"]
        self.ticket_controller.enviar_mensaje(ticket_id,usuario["id"],contenido,destinatario)

    def reabrir_ticket(self,ticket_id,usuario,contenido):
        ticket=self.tickets.buscar(ticket_id)
        if not ticket: raise ValueError("No se encontró el ticket.")
        if usuario["rol"]!="Cliente" or usuario["id"]!=ticket["cliente_id"]: raise PermissionError("Solo el cliente titular puede reabrir el ticket.")
        if ticket["estado"]!=EstadoTicket.CERRADO.value: raise ValueError("Solo se pueden reabrir tickets cerrados.")
        if not contenido.strip(): raise ValueError("Ingresá una consulta para justificar la reapertura.")
        self.ticket_controller.reabrir(ticket_id,usuario["id"],contenido,ticket["tecnico_id"])

    def asignar_ticket(self,ticket_id,tecnico_id,usuario):
        if usuario["rol"]!="Admin": raise PermissionError("Solo un administrador puede asignar tickets.")
        ticket=self.tickets.buscar(ticket_id)
        tecnico=self.usuarios.buscar(tecnico_id)
        if not ticket or not tecnico: raise ValueError("No se encontró el ticket o el técnico.")
        if tecnico["rol"]!="Tecnico" or not tecnico["activo"] or not tecnico["disponible"]: raise ValueError("El usuario seleccionado no es un técnico activo y disponible.")
        producto=self.catalogo.producto(ticket["producto_id"])
        if tecnico["especialidad_id"]!=producto["tipo_id"]: raise ValueError("El técnico no tiene la especialidad requerida por el producto.")
        self.ticket_controller.asignar(ticket_id,tecnico_id,usuario["id"])

    def configurar_prioridad(self,ticket_id,prioridad,usuario):
        if usuario["rol"]!="Admin": raise PermissionError("Solo un administrador puede configurar prioridades.")
        if prioridad not in ("Baja","Media","Alta","Urgente"): raise ValueError("La prioridad seleccionada no es válida.")
        if not self.tickets.buscar(ticket_id): raise ValueError("No se encontró el ticket.")
        self.ticket_controller.configurar_prioridad(ticket_id,prioridad,usuario["id"])

    def cambiar_estado(self,ticket_id,estado,usuario):
        ticket=self.tickets.buscar(ticket_id)
        if not ticket: raise ValueError("No se encontró el ticket.")
        if usuario["rol"]!="Admin" and usuario["id"] not in (ticket["cliente_id"],ticket["tecnico_id"]): raise PermissionError("No tenés acceso a este ticket.")
        if usuario["rol"]=="Cliente" and estado!=EstadoTicket.CERRADO: raise PermissionError("El cliente solo puede cerrar el ticket; para reabrirlo debe enviar una consulta.")
        if estado==EstadoTicket.ABIERTO: raise ValueError("La reapertura requiere una consulta y solo la puede solicitar el cliente titular.")
        if ticket["estado"]==EstadoTicket.CERRADO.value and estado!=EstadoTicket.CERRADO: raise ValueError("La reapertura debe solicitarla el cliente titular con una nueva consulta.")
        if estado==EstadoTicket.CERRADO and ticket["estado"]==EstadoTicket.CERRADO.value: raise ValueError("El ticket ya está cerrado.")
        self.ticket_controller.cambiar_estado(ticket_id,estado,usuario["id"])

    def manejar_error(self,error):
        if isinstance(error,sqlite3.IntegrityError):
            if "productos.numero_serie" in str(error): return "Ya existe un producto con ese número de serie."
            if "usuarios.email" in str(error): return "Ya existe un usuario con ese correo electrónico."
            return "No se pudo guardar: los datos no cumplen las reglas de integridad."
        return str(error)
