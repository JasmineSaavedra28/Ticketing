import tempfile
import unittest
from pathlib import Path

from control.servicios import Servicio
from dominio.modelos import EstadoTicket
from persistencia.database import Database


class ServicioTicketTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp_dir.name) / "test_hitos.db")
        self.servicio = Servicio(self.db)
        self.tipos = self.servicio.catalogo.tipos()
        self.admin = self.servicio.usuarios.autenticar("admin@hitos.local")
        self.cliente = self.servicio.usuarios.autenticar("cliente@hitos.local")
        self.tecnico = self.servicio.usuarios.autenticar("tecnico@hitos.local")
        self.producto_id = self.servicio.crear_producto(
            "Notebook de prueba", "Marca", "Modelo", self.tecnico["especialidad_id"], "SERIE-001"
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def crear_ticket(self):
        return self.servicio.crear_ticket(self.cliente["id"], self.producto_id, "No enciende")

    def test_crear_ticket_asigna_tecnico_especializado_y_registra_hito(self):
        ticket_id = self.crear_ticket()
        ticket = self.servicio.tickets.buscar(ticket_id)
        detalle = self.servicio.tickets.detalle(ticket_id)

        self.assertEqual(ticket["estado"], EstadoTicket.ABIERTO.value)
        self.assertEqual(ticket["titulo"], "No enciende")
        self.assertEqual(ticket["prioridad"], "Media")
        self.assertIsNone(ticket["fecha_cierre"])
        self.assertEqual(ticket["tecnico_id"], self.tecnico["id"])
        self.assertEqual(len(detalle[2]), 1)
        self.assertEqual(detalle[2][0]["detalle"], "Ticket creado")

    def test_crear_ticket_sin_descripcion_falla(self):
        with self.assertRaisesRegex(ValueError, "descripción"):
            self.servicio.crear_ticket(self.cliente["id"], self.producto_id, "  ")

    def test_enviar_mensaje_guarda_hito_y_notifica_a_la_otra_parte(self):
        ticket_id = self.crear_ticket()

        self.servicio.enviar_mensaje(ticket_id, self.cliente, "¿Cuándo podrían revisarlo?")

        _, mensajes, hitos = self.servicio.tickets.detalle(ticket_id)
        notificaciones = self.servicio.notificaciones.listar(self.tecnico["id"])
        self.assertEqual(mensajes[-1]["contenido"], "¿Cuándo podrían revisarlo?")
        self.assertEqual(hitos[-1]["tipo_evento"], "Mensaje")
        self.assertEqual(len(notificaciones), 1)

    def test_enviar_mensaje_vacio_falla(self):
        ticket_id = self.crear_ticket()

        with self.assertRaisesRegex(ValueError, "vacío"):
            self.servicio.enviar_mensaje(ticket_id, self.cliente, "  ")

    def test_reabrir_ticket_cerrado_registra_consulta_hito_y_notificacion(self):
        ticket_id = self.crear_ticket()
        self.servicio.cambiar_estado(ticket_id, EstadoTicket.CERRADO, self.tecnico)

        self.servicio.reabrir_ticket(ticket_id, self.cliente, "El problema continúa")

        ticket, mensajes, hitos = self.servicio.tickets.detalle(ticket_id)
        notificaciones = self.servicio.notificaciones.listar(self.tecnico["id"])
        self.assertEqual(ticket["estado"], EstadoTicket.EN_PROCESO.value)
        self.assertIsNone(ticket["fecha_cierre"])
        self.assertEqual(mensajes[-1]["contenido"], "El problema continúa")
        self.assertEqual(hitos[-1]["tipo_evento"], "Reapertura")
        self.assertTrue(any("reabierto" in n["mensaje"] for n in notificaciones))

    def test_admin_asigna_tecnico_y_configura_prioridad(self):
        ticket_id = self.crear_ticket()

        self.servicio.asignar_ticket(ticket_id, self.tecnico["id"], self.admin)
        self.servicio.configurar_prioridad(ticket_id, "Alta", self.admin)

        ticket, _, hitos = self.servicio.tickets.detalle(ticket_id)
        self.assertEqual(ticket["tecnico_id"], self.tecnico["id"])
        self.assertEqual(ticket["prioridad"], "Alta")
        self.assertEqual(hitos[-1]["tipo_evento"], "Prioridad")

    def test_no_se_puede_enviar_mensaje_a_ticket_cerrado(self):
        ticket_id = self.crear_ticket()
        self.servicio.cambiar_estado(ticket_id, EstadoTicket.CERRADO, self.tecnico)

        with self.assertRaisesRegex(ValueError, "ticket cerrado"):
            self.servicio.enviar_mensaje(ticket_id, self.cliente, "Mensaje tardío")

    def test_solo_cliente_titular_puede_reabrir(self):
        ticket_id = self.crear_ticket()
        self.servicio.cambiar_estado(ticket_id, EstadoTicket.CERRADO, self.tecnico)

        with self.assertRaises(PermissionError):
            self.servicio.reabrir_ticket(ticket_id, self.tecnico, "Consulta")

    def test_correo_de_usuario_duplicado_es_rechazado(self):
        with self.assertRaisesRegex(Exception, "UNIQUE constraint failed"):
            self.servicio.crear_usuario("Otra persona", "cliente@hitos.local", "clave123", "Cliente")


if __name__ == "__main__":
    unittest.main()
