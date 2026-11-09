# Documentación del proyecto

Los diagramas editables y sus exportaciones están organizados en [`diagramas/`](./diagramas/).

## Casos de uso

| Archivo | Flujo representado |
| --- | --- |
| [`CU01.drawio`](./diagramas/CU01.drawio) · [PNG](./diagramas/CU01.png) | Alta de producto |
| [`CU02.drawio`](./diagramas/CU02.drawio) · [PNG](./diagramas/CU02.png) | Creación de ticket |
| [`CU03.drawio`](./diagramas/CU03.drawio) · [PNG](./diagramas/CU03.png) | Envío de mensaje |
| [`CU04.drawio`](./diagramas/CU04.drawio) · [PNG](./diagramas/CU04.png) | Reapertura de ticket |

## Modelo UML

- [`uml.drawio`](./diagramas/uml.drawio): modelo editable de clases y arquitectura.
- [`uml_v0.1.png`](./diagramas/uml_v0.1.png) y [`uml_v1.1.png`](./diagramas/uml_v1.1.png): exportaciones/versiones conservadas del modelo.

Los archivos fuente `.drawio` se mantienen junto a sus exportaciones PNG para poder editar los diagramas y consultar una vista rápida.

## Correspondencia con el código

Los flujos de alta de producto, creación de ticket, mensajería y reapertura están implementados en presentación, control y persistencia SQLite. El dominio incluye las entidades del UML, y los repositorios reconstruyen los objetos y relaciones al leer los datos.

### Adaptaciones del UML a SQLite

- Los repositorios persisten en SQLite; las colecciones en memoria del diagrama se reemplazan por tablas y relaciones.
- `Cliente`, `Tecnico` y `Admin` son subclases del dominio. En SQLite comparten la tabla `usuarios`, y `rol` funciona como discriminador; cada subclase se reconstruye al leer.
- `TicketController`, `ProductoController` y `NotificacionController` coordinan la presentación con repositorios SQLite. `Servicio` funciona como fachada de la interfaz y valida las reglas de los casos de uso.
- `Ticket` incluye título, descripción, fechas de creación/cierre, prioridad, estado y relaciones con cliente, técnico, producto, mensajes, hitos y notificaciones.
- `Producto` incluye los atributos del UML y también `numero_serie`, usado como criterio de unicidad porque los requisitos prohíben duplicados, pero no indican la clave.
- La numeración de los archivos CU difiere de la del documento textual: en los archivos, CU01 es alta de producto, CU02 creación de ticket, CU03 mensajería y CU04 reapertura.
- El UML define `RESUELTO`, mientras que el requerimiento funcional escrito enumera solo Abierto, En proceso y Cerrado. Al alinear el código al UML se incorporó Resuelto.

La base SQLite existente se migra para agregar los campos faltantes, conservar los registros y ampliar la restricción de estados. Los tickets antiguos reciben como título inicial los primeros 80 caracteres de su descripción. La fecha histórica de cierre no puede deducirse de los datos anteriores, por lo que permanece vacía hasta el próximo cierre.
