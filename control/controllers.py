"""Controladores que traducen los casos de uso a operaciones de repositorio SQLite."""


class ProductoController:
    def __init__(self, repository):
        self.repository = repository

    def crear(self, nombre, marca, modelo, tipo_id, serie, descripcion=""):
        return self.repository.crear_producto(nombre, marca, modelo, tipo_id, serie, descripcion)

    def crear_tipo(self, nombre, descripcion=""):
        return self.repository.crear_tipo(nombre, descripcion)

    def listar(self, tipo_id=None):
        return self.repository.productos(tipo_id)

    def tipos(self):
        return self.repository.tipos()

    def buscar(self, producto_id):
        return self.repository.producto(producto_id)


class NotificacionController:
    def __init__(self, notificacion_repo):
        self.notificacionRepo = notificacion_repo

    def listar(self, usuario_id):
        return self.notificacionRepo.listar(usuario_id)

    def marcar_leida(self, notificacion_id, usuario_id):
        return self.notificacionRepo.marcar_leida(notificacion_id, usuario_id)


class TicketController:
    def __init__(self, ticket_repo, usuario_repo, producto_repo, notificacion_ctrl):
        self.ticketRepo = ticket_repo
        self.usuarioRepo = usuario_repo
        self.productoRepo = producto_repo
        self.notificacionCtrl = notificacion_ctrl

    def crear(self, cliente_id, tecnico_id, producto_id, descripcion, actor_id, titulo=None, prioridad="Media"):
        return self.ticketRepo.crear(cliente_id, tecnico_id, producto_id, descripcion, actor_id, titulo, prioridad)

    def buscar(self, ticket_id):
        return self.ticketRepo.buscar(ticket_id)

    def listar(self, usuario_id=None, rol=None):
        return self.ticketRepo.listar(usuario_id, rol)

    def detalle(self, ticket_id):
        return self.ticketRepo.detalle(ticket_id)

    def enviar_mensaje(self, ticket_id, remitente_id, contenido, destinatario_id):
        return self.ticketRepo.enviar_mensaje(ticket_id, remitente_id, contenido, destinatario_id)

    def reabrir(self, ticket_id, cliente_id, contenido, tecnico_id):
        return self.ticketRepo.reabrir(ticket_id, cliente_id, contenido, tecnico_id)

    def cambiar_estado(self, ticket_id, estado, actor_id):
        return self.ticketRepo.cambiar_estado(ticket_id, estado, actor_id)

    def asignar(self, ticket_id, tecnico_id, actor_id):
        return self.ticketRepo.asignar_tecnico(ticket_id, tecnico_id, actor_id)

    def configurar_prioridad(self, ticket_id, prioridad, actor_id):
        return self.ticketRepo.configurar_prioridad(ticket_id, prioridad, actor_id)
