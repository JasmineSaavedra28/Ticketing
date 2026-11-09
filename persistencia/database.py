import sqlite3
from contextlib import contextmanager
from pathlib import Path


ESQUEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS tipos_producto (
 id INTEGER PRIMARY KEY, nombre TEXT NOT NULL UNIQUE COLLATE NOCASE,
 descripcion TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS usuarios (
 id INTEGER PRIMARY KEY, nombre TEXT NOT NULL, email TEXT NOT NULL UNIQUE COLLATE NOCASE,
 login TEXT NOT NULL DEFAULT '', password_hash TEXT NOT NULL,
 rol TEXT NOT NULL CHECK(rol IN ('Cliente','Tecnico','Admin')),
 fecha_alta TEXT NOT NULL DEFAULT '', activo INTEGER NOT NULL DEFAULT 1,
 telefono TEXT NOT NULL DEFAULT '', direccion TEXT NOT NULL DEFAULT '',
 disponible INTEGER NOT NULL DEFAULT 1,
 especialidad_id INTEGER REFERENCES tipos_producto(id)
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_usuarios_login ON usuarios(login COLLATE NOCASE);
CREATE TABLE IF NOT EXISTS productos (
 id INTEGER PRIMARY KEY, nombre TEXT NOT NULL, marca TEXT NOT NULL, modelo TEXT NOT NULL,
 descripcion TEXT NOT NULL DEFAULT '', tipo_id INTEGER NOT NULL REFERENCES tipos_producto(id),
 numero_serie TEXT NOT NULL UNIQUE COLLATE NOCASE
);
CREATE TABLE IF NOT EXISTS tickets (
 id INTEGER PRIMARY KEY, titulo TEXT NOT NULL DEFAULT '', descripcion TEXT NOT NULL,
 fecha_creacion TEXT NOT NULL, fecha_cierre TEXT, prioridad TEXT NOT NULL DEFAULT 'Media',
 cliente_id INTEGER NOT NULL REFERENCES usuarios(id), tecnico_id INTEGER NOT NULL REFERENCES usuarios(id),
 producto_id INTEGER NOT NULL REFERENCES productos(id),
 estado TEXT NOT NULL CHECK(estado IN ('Abierto','En proceso','Resuelto','Cerrado'))
);
CREATE TABLE IF NOT EXISTS mensajes (
 id INTEGER PRIMARY KEY, ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
 contenido TEXT NOT NULL, fecha_hora TEXT NOT NULL, leido INTEGER NOT NULL DEFAULT 0,
 remitente_id INTEGER NOT NULL REFERENCES usuarios(id)
);
CREATE TABLE IF NOT EXISTS hitos (
 id INTEGER PRIMARY KEY, ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
 tipo_evento TEXT NOT NULL, detalle TEXT NOT NULL, fecha_hora TEXT NOT NULL,
 estado_resultante TEXT NOT NULL, realizado_por INTEGER NOT NULL REFERENCES usuarios(id)
);
CREATE TABLE IF NOT EXISTS notificaciones (
 id INTEGER PRIMARY KEY, mensaje TEXT NOT NULL, fecha_hora TEXT NOT NULL,
 leida INTEGER NOT NULL DEFAULT 0, usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
 ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_tickets_cliente ON tickets(cliente_id);
CREATE INDEX IF NOT EXISTS idx_tickets_tecnico ON tickets(tecnico_id);
CREATE INDEX IF NOT EXISTS idx_mensajes_ticket ON mensajes(ticket_id, fecha_hora);
CREATE INDEX IF NOT EXISTS idx_hitos_ticket ON hitos(ticket_id, fecha_hora);
"""


class Database:
    def __init__(self, ruta: str | Path = "hitos.db"):
        self.ruta = str(ruta)
        self.inicializar()

    @contextmanager
    def conectar(self):
        conexion = sqlite3.connect(self.ruta, timeout=10)
        conexion.row_factory = sqlite3.Row
        conexion.execute("PRAGMA foreign_keys = ON")
        try:
            yield conexion
            conexion.commit()
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    @staticmethod
    def _columnas(conexion, tabla):
        return {fila["name"] for fila in conexion.execute(f"PRAGMA table_info({tabla})")}

    def _migrar_esquema_anterior(self):
        """Agrega los campos UML faltantes y conserva los registros existentes."""
        conexion = sqlite3.connect(self.ruta)
        conexion.row_factory = sqlite3.Row
        try:
            conexion.execute("PRAGMA foreign_keys = OFF")
            if not conexion.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='tickets'").fetchone():
                return
            cambios = {
                "tipos_producto": [("descripcion", "TEXT NOT NULL DEFAULT ''")],
                "usuarios": [("login", "TEXT NOT NULL DEFAULT ''"), ("fecha_alta", "TEXT NOT NULL DEFAULT ''"),
                    ("activo", "INTEGER NOT NULL DEFAULT 1"), ("telefono", "TEXT NOT NULL DEFAULT ''"),
                    ("direccion", "TEXT NOT NULL DEFAULT ''"), ("disponible", "INTEGER NOT NULL DEFAULT 1")],
                "productos": [("descripcion", "TEXT NOT NULL DEFAULT ''")],
                "tickets": [("titulo", "TEXT NOT NULL DEFAULT ''"), ("fecha_cierre", "TEXT"), ("prioridad", "TEXT NOT NULL DEFAULT 'Media'")],
            }
            for tabla, columnas in cambios.items():
                presentes = self._columnas(conexion, tabla)
                for nombre, definicion in columnas:
                    if nombre not in presentes:
                        conexion.execute(f"ALTER TABLE {tabla} ADD COLUMN {nombre} {definicion}")
            conexion.execute("UPDATE usuarios SET login=email WHERE login='' OR login IS NULL")
            conexion.execute("UPDATE usuarios SET fecha_alta=datetime('now') WHERE fecha_alta='' OR fecha_alta IS NULL")
            sql = conexion.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='tickets'").fetchone()[0]
            if "Resuelto" not in sql:
                conexion.execute("""CREATE TABLE tickets_nueva (
                    id INTEGER PRIMARY KEY, titulo TEXT NOT NULL DEFAULT '', descripcion TEXT NOT NULL,
                    fecha_creacion TEXT NOT NULL, fecha_cierre TEXT, prioridad TEXT NOT NULL DEFAULT 'Media',
                    cliente_id INTEGER NOT NULL REFERENCES usuarios(id), tecnico_id INTEGER NOT NULL REFERENCES usuarios(id),
                    producto_id INTEGER NOT NULL REFERENCES productos(id),
                    estado TEXT NOT NULL CHECK(estado IN ('Abierto','En proceso','Resuelto','Cerrado'))
                )""")
                conexion.execute("INSERT INTO tickets_nueva SELECT id,titulo,descripcion,fecha_creacion,fecha_cierre,prioridad,cliente_id,tecnico_id,producto_id,estado FROM tickets")
                conexion.execute("DROP TABLE tickets")
                conexion.execute("ALTER TABLE tickets_nueva RENAME TO tickets")
            conexion.execute("UPDATE tickets SET titulo=substr(descripcion,1,80) WHERE titulo='' OR titulo IS NULL")
            conexion.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_usuarios_login ON usuarios(login COLLATE NOCASE)")
            conexion.commit()
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    def inicializar(self):
        self._migrar_esquema_anterior()
        with self.conectar() as db:
            db.executescript(ESQUEMA)
            for nombre in ("Línea blanca", "Cocina", "Electrónica", "Pequeños electrodomésticos"):
                db.execute("INSERT OR IGNORE INTO tipos_producto(nombre) VALUES (?)", (nombre,))
