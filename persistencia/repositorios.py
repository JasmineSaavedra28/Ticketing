from datetime import datetime
from .database import Database
from dominio.modelos import EstadoTicket


class UsuarioRepository:
    def __init__(self, db: Database): self.db = db

    def crear(self, nombre, email, password_hash, rol, especialidad_id=None):
        with self.db.conectar() as c:
            cur = c.execute("INSERT INTO usuarios(nombre,email,password_hash,rol,especialidad_id) VALUES(?,?,?,?,?)",
                            (nombre.strip(), email.strip().lower(), password_hash, rol, especialidad_id))
            return cur.lastrowid

    def listar(self, rol=None):
        with self.db.conectar() as c:
            if rol:
                return c.execute("SELECT u.*,t.nombre especialidad FROM usuarios u LEFT JOIN tipos_producto t ON t.id=u.especialidad_id WHERE rol=? ORDER BY nombre", (rol,)).fetchall()
            return c.execute("SELECT u.*,t.nombre especialidad FROM usuarios u LEFT JOIN tipos_producto t ON t.id=u.especialidad_id ORDER BY nombre").fetchall()

    def buscar(self, usuario_id):
        with self.db.conectar() as c: return c.execute("SELECT * FROM usuarios WHERE id=?", (usuario_id,)).fetchone()

    def tecnico_para_tipo(self, tipo_id):
        with self.db.conectar() as c:
            return c.execute("SELECT * FROM usuarios WHERE rol='Tecnico' AND especialidad_id=? ORDER BY id LIMIT 1", (tipo_id,)).fetchone()

    def autenticar(self, email):
        with self.db.conectar() as c: return c.execute("SELECT * FROM usuarios WHERE email=? COLLATE NOCASE", (email.strip(),)).fetchone()


class CatalogoRepository:
    def __init__(self, db: Database): self.db = db
    def tipos(self):
        with self.db.conectar() as c: return c.execute("SELECT * FROM tipos_producto ORDER BY nombre").fetchall()
    def crear_producto(self, nombre, marca, modelo, tipo_id, numero_serie):
        with self.db.conectar() as c:
            cur=c.execute("INSERT INTO productos(nombre,marca,modelo,tipo_id,numero_serie) VALUES(?,?,?,?,?)", (nombre.strip(),marca.strip(),modelo.strip(),tipo_id,numero_serie.strip()))
            return cur.lastrowid
    def productos(self, tipo_id=None):
        with self.db.conectar() as c:
            sql="SELECT p.*,t.nombre tipo FROM productos p JOIN tipos_producto t ON t.id=p.tipo_id"
            return c.execute(sql+" WHERE tipo_id=? ORDER BY p.nombre" if tipo_id else sql+" ORDER BY p.nombre", (tipo_id,) if tipo_id else ()).fetchall()
    def producto(self, producto_id):
        with self.db.conectar() as c: return c.execute("SELECT * FROM productos WHERE id=?", (producto_id,)).fetchone()


class TicketRepository:
    def __init__(self, db: Database): self.db = db
    def crear(self, cliente_id, tecnico_id, producto_id, descripcion, realizado_por):
        ahora=datetime.now().isoformat(timespec="seconds")
        with self.db.conectar() as c:
            cur=c.execute("INSERT INTO tickets(cliente_id,tecnico_id,producto_id,descripcion,estado,fecha_creacion) VALUES(?,?,?,?,?,?)", (cliente_id,tecnico_id,producto_id,descripcion.strip(),EstadoTicket.ABIERTO.value,ahora))
            ticket_id=cur.lastrowid
            c.execute("INSERT INTO hitos(ticket_id,tipo_evento,detalle,fecha_hora,estado_resultante,realizado_por) VALUES(?,?,?,?,?,?)", (ticket_id,"Creación","Ticket creado",ahora,EstadoTicket.ABIERTO.value,realizado_por))
            return ticket_id
    def listar(self, usuario=None, rol=None):
        sql="SELECT t.*,c.nombre cliente,te.nombre tecnico,p.nombre producto,p.numero_serie FROM tickets t JOIN usuarios c ON c.id=t.cliente_id JOIN usuarios te ON te.id=t.tecnico_id JOIN productos p ON p.id=t.producto_id"
        args=()
        if rol=="Cliente": sql+=" WHERE cliente_id=?"; args=(usuario,)
        elif rol=="Tecnico": sql+=" WHERE tecnico_id=?"; args=(usuario,)
        with self.db.conectar() as c: return c.execute(sql+" ORDER BY t.fecha_creacion DESC",args).fetchall()
    def buscar(self, ticket_id):
        with self.db.conectar() as c: return c.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()
    def detalle(self, ticket_id):
        with self.db.conectar() as c:
            t=c.execute("SELECT t.*,c.nombre cliente,te.nombre tecnico,p.nombre producto,p.numero_serie FROM tickets t JOIN usuarios c ON c.id=t.cliente_id JOIN usuarios te ON te.id=t.tecnico_id JOIN productos p ON p.id=t.producto_id WHERE t.id=?", (ticket_id,)).fetchone()
            if not t: return None
            return t, c.execute("SELECT m.*,u.nombre remitente FROM mensajes m JOIN usuarios u ON u.id=m.remitente_id WHERE ticket_id=? ORDER BY m.fecha_hora",(ticket_id,)).fetchall(), c.execute("SELECT h.*,u.nombre realizado_por_nombre FROM hitos h JOIN usuarios u ON u.id=h.realizado_por WHERE ticket_id=? ORDER BY h.fecha_hora",(ticket_id,)).fetchall()
    def enviar_mensaje(self, ticket_id, remitente_id, contenido, destinatario_id):
        ahora=datetime.now().isoformat(timespec="seconds")
        with self.db.conectar() as c:
            c.execute("INSERT INTO mensajes(ticket_id,remitente_id,contenido,fecha_hora) VALUES(?,?,?,?)", (ticket_id,remitente_id,contenido.strip(),ahora))
            t=c.execute("SELECT estado FROM tickets WHERE id=?",(ticket_id,)).fetchone()
            c.execute("INSERT INTO hitos(ticket_id,tipo_evento,detalle,fecha_hora,estado_resultante,realizado_por) VALUES(?,?,?,?,?,?)",(ticket_id,"Mensaje","Mensaje enviado",ahora,t["estado"],remitente_id))
            c.execute("INSERT INTO notificaciones(usuario_id,ticket_id,mensaje,fecha_hora) VALUES(?,?,?,?)",(destinatario_id,ticket_id,"Nuevo mensaje en el ticket #"+str(ticket_id),ahora))

    def reabrir(self, ticket_id, cliente_id, contenido, tecnico_id):
        ahora=datetime.now().isoformat(timespec="seconds")
        with self.db.conectar() as c:
            c.execute("UPDATE tickets SET estado=? WHERE id=?", (EstadoTicket.EN_PROCESO.value,ticket_id))
            c.execute("INSERT INTO mensajes(ticket_id,remitente_id,contenido,fecha_hora) VALUES(?,?,?,?)",(ticket_id,cliente_id,contenido.strip(),ahora))
            c.execute("INSERT INTO hitos(ticket_id,tipo_evento,detalle,fecha_hora,estado_resultante,realizado_por) VALUES(?,?,?,?,?,?)",(ticket_id,"Reapertura","Ticket reabierto por el cliente",ahora,EstadoTicket.EN_PROCESO.value,cliente_id))
            c.execute("INSERT INTO notificaciones(usuario_id,ticket_id,mensaje,fecha_hora) VALUES(?,?,?,?)",(tecnico_id,ticket_id,"El ticket #"+str(ticket_id)+" fue reabierto",ahora))
    def cambiar_estado(self, ticket_id, nuevo_estado, actor_id):
        ahora=datetime.now().isoformat(timespec="seconds")
        with self.db.conectar() as c:
            c.execute("UPDATE tickets SET estado=? WHERE id=?",(nuevo_estado.value,ticket_id))
            c.execute("INSERT INTO hitos(ticket_id,tipo_evento,detalle,fecha_hora,estado_resultante,realizado_por) VALUES(?,?,?,?,?,?)",(ticket_id,"Cambio de estado",f"Estado actualizado a {nuevo_estado.value}",ahora,nuevo_estado.value,actor_id))
            row=c.execute("SELECT cliente_id,tecnico_id FROM tickets WHERE id=?",(ticket_id,)).fetchone()
            for uid in {row['cliente_id'],row['tecnico_id']}-{actor_id}:
                c.execute("INSERT INTO notificaciones(usuario_id,ticket_id,mensaje,fecha_hora) VALUES(?,?,?,?)",(uid,ticket_id,f"El ticket #{ticket_id} cambió a {nuevo_estado.value}",ahora))


class NotificacionRepository:
    def __init__(self, db: Database): self.db=db
    def listar(self, usuario_id):
        with self.db.conectar() as c: return c.execute("SELECT * FROM notificaciones WHERE usuario_id=? ORDER BY fecha_hora DESC",(usuario_id,)).fetchall()
    def marcar_leida(self, notificacion_id, usuario_id):
        with self.db.conectar() as c: c.execute("UPDATE notificaciones SET leida=1 WHERE id=? AND usuario_id=?",(notificacion_id,usuario_id))
