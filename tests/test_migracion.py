import sqlite3
import tempfile
import unittest
from pathlib import Path

from persistencia.database import Database


class MigracionSqliteTests(unittest.TestCase):
    def test_migra_esquema_anterior_sin_perder_registros(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "hitos.db"
            conexion = sqlite3.connect(ruta)
            conexion.executescript("""
                PRAGMA foreign_keys=ON;
                CREATE TABLE tipos_producto(id INTEGER PRIMARY KEY, nombre TEXT NOT NULL UNIQUE);
                CREATE TABLE usuarios(id INTEGER PRIMARY KEY, nombre TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL, rol TEXT NOT NULL, especialidad_id INTEGER REFERENCES tipos_producto(id));
                CREATE TABLE productos(id INTEGER PRIMARY KEY, nombre TEXT NOT NULL, marca TEXT NOT NULL,
                    modelo TEXT NOT NULL, tipo_id INTEGER NOT NULL REFERENCES tipos_producto(id), numero_serie TEXT NOT NULL UNIQUE);
                CREATE TABLE tickets(id INTEGER PRIMARY KEY, cliente_id INTEGER NOT NULL REFERENCES usuarios(id), tecnico_id INTEGER NOT NULL REFERENCES usuarios(id),
                    producto_id INTEGER NOT NULL REFERENCES productos(id), descripcion TEXT NOT NULL,
                    estado TEXT NOT NULL CHECK(estado IN ('Abierto','En proceso','Cerrado')), fecha_creacion TEXT NOT NULL);
                CREATE TABLE mensajes(id INTEGER PRIMARY KEY, ticket_id INTEGER NOT NULL REFERENCES tickets(id), remitente_id INTEGER NOT NULL REFERENCES usuarios(id),
                    contenido TEXT NOT NULL, fecha_hora TEXT NOT NULL, leido INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE hitos(id INTEGER PRIMARY KEY, ticket_id INTEGER NOT NULL REFERENCES tickets(id), tipo_evento TEXT NOT NULL,
                    detalle TEXT NOT NULL, fecha_hora TEXT NOT NULL, estado_resultante TEXT NOT NULL, realizado_por INTEGER NOT NULL REFERENCES usuarios(id));
                CREATE TABLE notificaciones(id INTEGER PRIMARY KEY, usuario_id INTEGER NOT NULL REFERENCES usuarios(id), ticket_id INTEGER NOT NULL REFERENCES tickets(id),
                    mensaje TEXT NOT NULL, fecha_hora TEXT NOT NULL, leida INTEGER NOT NULL DEFAULT 0);
                INSERT INTO tipos_producto VALUES (1,'Electrónica');
                INSERT INTO usuarios VALUES (1,'Cliente','cliente@test.local','hash','Cliente',NULL);
                INSERT INTO usuarios VALUES (2,'Técnico','tecnico@test.local','hash','Tecnico',1);
                INSERT INTO productos VALUES (1,'Notebook','Marca','Modelo',1,'SERIE-1');
                INSERT INTO tickets VALUES (1,1,2,1,'No enciende','Cerrado','2026-01-01T10:00:00');
                INSERT INTO mensajes VALUES (1,1,1,'Sigue fallando','2026-01-01T10:01:00',0);
                INSERT INTO hitos VALUES (1,1,'Creación','Ticket creado','2026-01-01T10:00:00','Abierto',1);
                INSERT INTO notificaciones VALUES (1,2,1,'Nuevo ticket','2026-01-01T10:00:00',0);
            """)
            conexion.commit()
            conexion.close()

            Database(ruta)

            db = sqlite3.connect(ruta)
            try:
                db.row_factory = sqlite3.Row
                ticket = db.execute("SELECT * FROM tickets WHERE id=1").fetchone()
                usuario = db.execute("SELECT * FROM usuarios WHERE id=1").fetchone()
                producto = db.execute("SELECT * FROM productos WHERE id=1").fetchone()
                self.assertEqual(ticket["descripcion"], "No enciende")
                self.assertEqual(ticket["estado"], "Cerrado")
                self.assertEqual(ticket["titulo"], "No enciende")
                self.assertEqual(usuario["login"], "cliente@test.local")
                self.assertEqual(producto["numero_serie"], "SERIE-1")
                self.assertEqual(db.execute("SELECT COUNT(*) FROM mensajes").fetchone()[0], 1)
                self.assertEqual(db.execute("SELECT COUNT(*) FROM hitos").fetchone()[0], 1)
                self.assertEqual(db.execute("SELECT COUNT(*) FROM notificaciones").fetchone()[0], 1)
                db.execute("UPDATE tickets SET estado='Resuelto' WHERE id=1")
                self.assertEqual(db.execute("SELECT estado FROM tickets WHERE id=1").fetchone()[0], "Resuelto")
                self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()
