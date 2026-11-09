# Documentación del proyecto

Los diagramas editables y sus exportaciones se encuentran en [`diagramas/`](./diagramas/). Esta página resume los flujos y clases representados, y describe cómo se reflejan en la implementación actual.

## Casos de uso

| Archivo | Flujo representado | Estado en la aplicación |
| --- | --- | --- |
| [`CU01.drawio`](./diagramas/CU01.drawio) · [PNG](./diagramas/CU01.png) | Alta de producto | Implementado: administración de tipos y productos persistidos en SQLite. |
| [`CU02.drawio`](./diagramas/CU02.drawio) · [PNG](./diagramas/CU02.png) | Creación de ticket | Implementado: asociación con cliente y producto, estado inicial, hito y asignación por especialidad. |
| [`CU03.drawio`](./diagramas/CU03.drawio) · [PNG](./diagramas/CU03.png) | Envío de mensaje | Implementado: historial de mensajes y registro de actividad del ticket, con notificación a la otra parte. |
| [`CU04.drawio`](./diagramas/CU04.drawio) · [PNG](./diagramas/CU04.png) | Reapertura de ticket | Implementado: pasa a En proceso, registra la consulta como mensaje e hito y notifica al técnico. |

## Modelo UML

- [`uml.drawio`](./diagramas/uml.drawio): modelo editable de clases y arquitectura.
- [`uml_v0.1.png`](./diagramas/uml_v0.1.png) y [`uml_v1.1.png`](./diagramas/uml_v1.1.png): exportaciones conservadas de distintas versiones del modelo.

Los archivos `.drawio` se mantienen junto a sus exportaciones PNG para facilitar su edición y consulta.

## Correspondencia entre UML e implementación

La aplicación mantiene la separación por capas del modelo: `dominio/` contiene entidades y reglas; `control/` coordina operaciones y validaciones; `persistencia/` implementa repositorios SQLite; y `presentacion/` ofrece la interfaz Tkinter. `Servicio` actúa como fachada para la interfaz y los controladores coordinan el acceso a repositorios. En la interfaz, el historial de actividad reúne eventos como la creación del ticket, mensajes, cambios de estado y reaperturas; en el código y el modelo UML, esta entidad se denomina `Hito`.

### Implementaciones y adaptaciones

- El almacenamiento de los repositorios se realiza en SQLite mediante tablas, claves foráneas, índices y restricciones de unicidad. Las colecciones que aparecen en el modelo se cargan desde la base al consultar las entidades.
- `Cliente`, `Tecnico` y `Admin` están representados como subclases del dominio. En SQLite comparten la tabla `usuarios`; el campo `rol` determina qué subtipo se reconstruye.
- `Ticket` conserva título, descripción, fechas, prioridad, estado y asociaciones con cliente, técnico, producto, mensajes, hitos y notificaciones.
- `Producto` incorpora `numero_serie`, que se usa como dato único para identificar productos registrados.
- El ciclo de vida admite Abierto, En proceso, Resuelto y Cerrado. La reapertura de un ticket cerrado lo devuelve a En proceso.
- La interfaz implementa autenticación y vistas de tickets, productos, usuarios y notificaciones según el rol. Permite buscar tickets y filtrarlos por estado, y buscar productos combinando texto con el filtro por tipo. Las operaciones de productos disponibles son alta, listado y filtro por tipo.
- La numeración de los archivos de casos de uso corresponde a los diagramas: CU01 alta de producto, CU02 creación de ticket, CU03 mensajería y CU04 reapertura.

La inicialización migra bases SQLite existentes para incorporar los campos requeridos por la versión actual y conservar los registros. En tickets previos, el título se completa a partir de la descripción cuando no existía ese dato; las fechas de cierre históricas no disponibles quedan vacías.
