import sqlite3
from contextlib import contextmanager
from pathlib import Path


ESQUEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS tipos_producto (
 id INTEGER PRIMARY KEY, nombre TEXT NOT NULL UNIQUE COLLATE NOCASE
);
CREATE TABLE IF NOT EXISTS usuarios (
 id INTEGER PRIMARY KEY, nombre TEXT NOT NULL, email TEXT NOT NULL UNIQUE COLLATE NOCASE,
 password_hash TEXT NOT NULL, rol TEXT NOT NULL CHECK(rol IN ('Cliente','Tecnico','Admin')),
 especialidad_id INTEGER REFERENCES tipos_producto(id)
);
CREATE TABLE IF NOT EXISTS productos (
 id INTEGER PRIMARY KEY, nombre TEXT NOT NULL, marca TEXT NOT NULL, modelo TEXT NOT NULL,
 tipo_id INTEGER NOT NULL REFERENCES tipos_producto(id), numero_serie TEXT NOT NULL UNIQUE COLLATE NOCASE
);
CREATE TABLE IF NOT EXISTS tickets (
 id INTEGER PRIMARY KEY, cliente_id INTEGER NOT NULL REFERENCES usuarios(id),
 tecnico_id INTEGER NOT NULL REFERENCES usuarios(id), producto_id INTEGER NOT NULL REFERENCES productos(id),
 descripcion TEXT NOT NULL, estado TEXT NOT NULL CHECK(estado IN ('Abierto','En proceso','Cerrado')),
 fecha_creacion TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS mensajes (
 id INTEGER PRIMARY KEY, ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
 remitente_id INTEGER NOT NULL REFERENCES usuarios(id), contenido TEXT NOT NULL,
 fecha_hora TEXT NOT NULL, leido INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS hitos (
 id INTEGER PRIMARY KEY, ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
 tipo_evento TEXT NOT NULL, detalle TEXT NOT NULL, fecha_hora TEXT NOT NULL,
 estado_resultante TEXT NOT NULL, realizado_por INTEGER NOT NULL REFERENCES usuarios(id)
);
CREATE TABLE IF NOT EXISTS notificaciones (
 id INTEGER PRIMARY KEY, usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
 ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE, mensaje TEXT NOT NULL,
 fecha_hora TEXT NOT NULL, leida INTEGER NOT NULL DEFAULT 0
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

    def inicializar(self):
        with self.conectar() as db:
            db.executescript(ESQUEMA)
            for nombre in ("Línea blanca", "Cocina", "Electrónica", "Pequeños electrodomésticos"):
                db.execute("INSERT OR IGNORE INTO tipos_producto(nombre) VALUES (?)", (nombre,))

