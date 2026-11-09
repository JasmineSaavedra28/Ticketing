from datetime import datetime
from .database import Database
from dominio.modelos import (Admin, Cliente, EstadoTicket, Hito, Mensaje, Notificacion,
                             Producto, Tecnico, Ticket, TipoProducto)


def _fecha(valor):
    return datetime.fromisoformat(valor) if valor else None


class UsuarioRepository:
    def __init__(self, db: Database): self.db = db

    def crear(self, nombre, email, password_hash, rol, especialidad_id=None, telefono="", direccion=""):
        fecha_alta=datetime.now().isoformat(timespec="seconds")
        with self.db.conectar() as c:
            login=email.strip().lower()
            cur = c.execute("INSERT INTO usuarios(nombre,email,login,password_hash,rol,fecha_alta,especialidad_id,telefono,direccion) VALUES(?,?,?,?,?,?,?,?,?)",
                            (nombre.strip(), login, login, password_hash, rol, fecha_alta, especialidad_id, telefono.strip(), direccion.strip()))
            return cur.lastrowid

    def listar(self, rol=None):
        with self.db.conectar() as c:
            if rol:
                rows=c.execute("SELECT u.*,t.nombre especialidad FROM usuarios u LEFT JOIN tipos_producto t ON t.id=u.especialidad_id WHERE rol=? ORDER BY nombre", (rol,)).fetchall()
            else:
                rows=c.execute("SELECT u.*,t.nombre especialidad FROM usuarios u LEFT JOIN tipos_producto t ON t.id=u.especialidad_id ORDER BY nombre").fetchall()
            return [self._mapear(row) for row in rows]

    @staticmethod
    def _mapear(row):
        base=dict(id=row["id"],nombre=row["nombre"],email=row["email"],login=row["login"] or row["email"],
                  password_hash=row["password_hash"],rol=row["rol"],fecha_alta=_fecha(row["fecha_alta"]))
        if row["rol"]=="Cliente":
            return Cliente(**base,activo=bool(row["activo"]),telefono=row["telefono"],direccion=row["direccion"])
        if row["rol"]=="Tecnico":
            return Tecnico(**base,activo=bool(row["activo"]),disponible=bool(row["disponible"]),
                           especialidad_id=row["especialidad_id"],especialidad_nombre=row["especialidad"] or "")
        return Admin(**base)

    def buscar(self, usuario_id):
        with self.db.conectar() as c:
            row=c.execute("SELECT u.*,t.nombre especialidad FROM usuarios u LEFT JOIN tipos_producto t ON t.id=u.especialidad_id WHERE u.id=?", (usuario_id,)).fetchone()
            return self._mapear(row) if row else None

    def tecnico_para_tipo(self, tipo_id):
        with self.db.conectar() as c:
            row=c.execute("SELECT u.*,t.nombre especialidad FROM usuarios u LEFT JOIN tipos_producto t ON t.id=u.especialidad_id WHERE u.rol='Tecnico' AND u.especialidad_id=? AND u.activo=1 AND u.disponible=1 ORDER BY u.id LIMIT 1", (tipo_id,)).fetchone()
            return self._mapear(row) if row else None

    def autenticar(self, email):
        with self.db.conectar() as c:
            row=c.execute("SELECT u.*,t.nombre especialidad FROM usuarios u LEFT JOIN tipos_producto t ON t.id=u.especialidad_id WHERE u.email=? COLLATE NOCASE", (email.strip(),)).fetchone()
            return self._mapear(row) if row else None


class ProductoRepository:
    def __init__(self, db: Database): self.db = db
    def tipos(self):
        with self.db.conectar() as c:
            return [TipoProducto(row["id"],row["nombre"],row["descripcion"]) for row in c.execute("SELECT * FROM tipos_producto ORDER BY nombre").fetchall()]
    def crear_tipo(self, nombre, descripcion=""):
        with self.db.conectar() as c:
            cur=c.execute("INSERT INTO tipos_producto(nombre,descripcion) VALUES(?,?)",(nombre.strip(),descripcion.strip()))
            return cur.lastrowid
    def crear_producto(self, nombre, marca, modelo, tipo_id, numero_serie, descripcion=""):
        with self.db.conectar() as c:
            cur=c.execute("INSERT INTO productos(nombre,marca,modelo,descripcion,tipo_id,numero_serie) VALUES(?,?,?,?,?,?)", (nombre.strip(),marca.strip(),modelo.strip(),descripcion.strip(),tipo_id,numero_serie.strip()))
            return cur.lastrowid
    def productos(self, tipo_id=None):
        with self.db.conectar() as c:
            sql="SELECT p.*,t.nombre tipo FROM productos p JOIN tipos_producto t ON t.id=p.tipo_id"
            rows=c.execute(sql+" WHERE tipo_id=? ORDER BY p.nombre" if tipo_id else sql+" ORDER BY p.nombre", (tipo_id,) if tipo_id else ()).fetchall()
            return [Producto(row["id"],row["nombre"],row["modelo"],row["marca"],row["descripcion"],row["tipo_id"],row["numero_serie"],row["tipo"]) for row in rows]
    def producto(self, producto_id):
        with self.db.conectar() as c:
            row=c.execute("SELECT p.*,t.nombre tipo FROM productos p LEFT JOIN tipos_producto t ON t.id=p.tipo_id WHERE p.id=?", (producto_id,)).fetchone()
            return Producto(row["id"],row["nombre"],row["modelo"],row["marca"],row["descripcion"],row["tipo_id"],row["numero_serie"],row["tipo"] or "") if row else None


# Conserva el nombre usado por la interfaz; en el UML la clase se llama ProductoRepository.
CatalogoRepository = ProductoRepository


class TicketRepository:
    def __init__(self, db: Database): self.db = db
    def crear(self, cliente_id, tecnico_id, producto_id, descripcion, realizado_por, titulo=None, prioridad="Media"):
        ahora=datetime.now().isoformat(timespec="seconds")
        titulo=(titulo or descripcion.strip().splitlines()[0][:80]).strip()
        with self.db.conectar() as c:
            cur=c.execute("INSERT INTO tickets(titulo,descripcion,fecha_creacion,prioridad,cliente_id,tecnico_id,producto_id,estado) VALUES(?,?,?,?,?,?,?,?)", (titulo,descripcion.strip(),ahora,prioridad,cliente_id,tecnico_id,producto_id,EstadoTicket.ABIERTO.value))
            ticket_id=cur.lastrowid
            c.execute("INSERT INTO hitos(ticket_id,tipo_evento,detalle,fecha_hora,estado_resultante,realizado_por) VALUES(?,?,?,?,?,?)", (ticket_id,"Creación","Ticket creado",ahora,EstadoTicket.ABIERTO.value,realizado_por))
            return ticket_id
    def listar(self, usuario=None, rol=None):
        sql="SELECT t.*,c.nombre cliente,te.nombre tecnico,p.nombre producto,p.numero_serie FROM tickets t JOIN usuarios c ON c.id=t.cliente_id JOIN usuarios te ON te.id=t.tecnico_id JOIN productos p ON p.id=t.producto_id"
        args=()
        if rol=="Cliente": sql+=" WHERE cliente_id=?"; args=(usuario,)
        elif rol=="Tecnico": sql+=" WHERE tecnico_id=?"; args=(usuario,)
        with self.db.conectar() as c:
            return [self._mapear(row) for row in c.execute(sql+" ORDER BY t.fecha_creacion DESC",args).fetchall()]

    @staticmethod
    def _mapear(row):
        return Ticket(id=row["id"],titulo=row["titulo"],descripcion=row["descripcion"],
            fecha_creacion=_fecha(row["fecha_creacion"]),fecha_cierre=_fecha(row["fecha_cierre"]),
            prioridad=row["prioridad"],cliente_id=row["cliente_id"],tecnico_id=row["tecnico_id"],
            producto_id=row["producto_id"],estado=EstadoTicket(row["estado"]),
            cliente=row["cliente"] if "cliente" in row.keys() else "",
            tecnico=row["tecnico"] if "tecnico" in row.keys() else "",
            producto=row["producto"] if "producto" in row.keys() else "",
            numero_serie=row["numero_serie"] if "numero_serie" in row.keys() else "")

    def buscar(self, ticket_id):
        with self.db.conectar() as c:
            row=c.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()
            return self._mapear(row) if row else None
    def detalle(self, ticket_id):
        with self.db.conectar() as c:
            t=c.execute("SELECT t.*,c.nombre cliente,te.nombre tecnico,p.nombre producto,p.numero_serie FROM tickets t JOIN usuarios c ON c.id=t.cliente_id JOIN usuarios te ON te.id=t.tecnico_id JOIN productos p ON p.id=t.producto_id WHERE t.id=?", (ticket_id,)).fetchone()
            if not t: return None
            mensajes=[Mensaje(row["id"],row["ticket_id"],row["contenido"],_fecha(row["fecha_hora"]),bool(row["leido"]),row["remitente_id"],row["remitente"]) for row in c.execute("SELECT m.*,u.nombre remitente FROM mensajes m JOIN usuarios u ON u.id=m.remitente_id WHERE ticket_id=? ORDER BY m.fecha_hora",(ticket_id,)).fetchall()]
            hitos=[Hito(row["id"],row["ticket_id"],row["tipo_evento"],row["detalle"],_fecha(row["fecha_hora"]),EstadoTicket(row["estado_resultante"]),row["realizado_por"],row["realizado_por_nombre"]) for row in c.execute("SELECT h.*,u.nombre realizado_por_nombre FROM hitos h JOIN usuarios u ON u.id=h.realizado_por WHERE ticket_id=? ORDER BY h.fecha_hora",(ticket_id,)).fetchall()]
            notificaciones=[Notificacion(row["id"],row["mensaje"],_fecha(row["fecha_hora"]),bool(row["leida"]),row["usuario_id"],row["ticket_id"]) for row in c.execute("SELECT * FROM notificaciones WHERE ticket_id=? ORDER BY fecha_hora",(ticket_id,)).fetchall()]
            ticket=self._mapear(t)
            ticket.mensajes=mensajes
            ticket.hitos=hitos
            ticket.notificaciones=notificaciones
            return ticket, mensajes, hitos
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
            c.execute("UPDATE tickets SET estado=?,fecha_cierre=NULL WHERE id=?", (EstadoTicket.EN_PROCESO.value,ticket_id))
            c.execute("INSERT INTO mensajes(ticket_id,remitente_id,contenido,fecha_hora) VALUES(?,?,?,?)",(ticket_id,cliente_id,contenido.strip(),ahora))
            c.execute("INSERT INTO hitos(ticket_id,tipo_evento,detalle,fecha_hora,estado_resultante,realizado_por) VALUES(?,?,?,?,?,?)",(ticket_id,"Reapertura","Ticket reabierto por el cliente",ahora,EstadoTicket.EN_PROCESO.value,cliente_id))
            c.execute("INSERT INTO notificaciones(usuario_id,ticket_id,mensaje,fecha_hora) VALUES(?,?,?,?)",(tecnico_id,ticket_id,"El ticket #"+str(ticket_id)+" fue reabierto",ahora))
    def cambiar_estado(self, ticket_id, nuevo_estado, actor_id):
        ahora=datetime.now().isoformat(timespec="seconds")
        with self.db.conectar() as c:
            fecha_cierre=datetime.now().isoformat(timespec="seconds") if nuevo_estado==EstadoTicket.CERRADO else None
            c.execute("UPDATE tickets SET estado=?,fecha_cierre=? WHERE id=?",(nuevo_estado.value,fecha_cierre,ticket_id))
            c.execute("INSERT INTO hitos(ticket_id,tipo_evento,detalle,fecha_hora,estado_resultante,realizado_por) VALUES(?,?,?,?,?,?)",(ticket_id,"Cambio de estado",f"Estado actualizado a {nuevo_estado.value}",ahora,nuevo_estado.value,actor_id))
            row=c.execute("SELECT cliente_id,tecnico_id FROM tickets WHERE id=?",(ticket_id,)).fetchone()
            for uid in {row['cliente_id'],row['tecnico_id']}-{actor_id}:
                c.execute("INSERT INTO notificaciones(usuario_id,ticket_id,mensaje,fecha_hora) VALUES(?,?,?,?)",(uid,ticket_id,f"El ticket #{ticket_id} cambió a {nuevo_estado.value}",ahora))

    def configurar_prioridad(self, ticket_id, prioridad, actor_id):
        ahora=datetime.now().isoformat(timespec="seconds")
        with self.db.conectar() as c:
            c.execute("UPDATE tickets SET prioridad=? WHERE id=?",(prioridad,ticket_id))
            c.execute("INSERT INTO hitos(ticket_id,tipo_evento,detalle,fecha_hora,estado_resultante,realizado_por) SELECT id,'Prioridad',?, ?,estado,? FROM tickets WHERE id=?",(f"Prioridad configurada: {prioridad}",ahora,actor_id,ticket_id))

    def asignar_tecnico(self, ticket_id, tecnico_id, actor_id):
        ahora=datetime.now().isoformat(timespec="seconds")
        with self.db.conectar() as c:
            c.execute("UPDATE tickets SET tecnico_id=? WHERE id=?",(tecnico_id,ticket_id))
            c.execute("INSERT INTO hitos(ticket_id,tipo_evento,detalle,fecha_hora,estado_resultante,realizado_por) SELECT id,'Asignación',?, ?,estado,? FROM tickets WHERE id=?",(f"Ticket asignado al técnico #{tecnico_id}",ahora,actor_id,ticket_id))
            c.execute("INSERT INTO notificaciones(usuario_id,ticket_id,mensaje,fecha_hora) VALUES(?,?,?,?)",(tecnico_id,ticket_id,f"Se te asignó el ticket #{ticket_id}",ahora))


class NotificacionRepository:
    def __init__(self, db: Database): self.db=db
    def listar(self, usuario_id):
        with self.db.conectar() as c:
            return [Notificacion(row["id"],row["mensaje"],_fecha(row["fecha_hora"]),bool(row["leida"]),row["usuario_id"],row["ticket_id"]) for row in c.execute("SELECT * FROM notificaciones WHERE usuario_id=? ORDER BY fecha_hora DESC",(usuario_id,)).fetchall()]
    def marcar_leida(self, notificacion_id, usuario_id):
        with self.db.conectar() as c: c.execute("UPDATE notificaciones SET leida=1 WHERE id=? AND usuario_id=?",(notificacion_id,usuario_id))
