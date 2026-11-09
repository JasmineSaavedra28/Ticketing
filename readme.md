# Sistema de Ticketing

Aplicación de escritorio en Python para registrar productos, crear y administrar tickets de soporte y mantener el historial de conversación (mensajes e hitos). Los datos persisten en SQLite.

## Requisitos y ejecución

- Python 3.10 o posterior.
- No requiere paquetes externos: utiliza Tkinter y SQLite de la biblioteca estándar.

Desde la carpeta del proyecto:

```bash
py main.py
```

## Pruebas automatizadas

Ejecutá la suite desde la carpeta del proyecto:

```bash
py -m unittest discover -v
```

Las pruebas usan una base SQLite temporal, separada de `hitos.db`.

La base `hitos.db` se crea automáticamente en esa carpeta en el primer inicio. También se inicializan los tipos de producto definidos en el modelo.

## Usuarios de demostración

| Rol | Correo | Contraseña |
| --- | --- | --- |
| Administrador | `admin@hitos.local` | `admin123` |
| Cliente | `cliente@hitos.local` | `cliente123` |
| Técnico | `tecnico@hitos.local` | `tecnico123` |

El técnico de demostración se crea con la primera especialidad disponible. El administrador puede crear productos, administrar usuarios y asignar una especialidad a los técnicos. Para probar la creación automática de tickets, registrá un producto de un tipo que tenga un técnico asignado.

## Funcionalidad

- Inicio de sesión con contraseñas almacenadas como PBKDF2-HMAC-SHA256 con salt.
- Administración de usuarios con roles Cliente, Técnico y Admin; el correo es único.
- Catálogo de tipos y productos; el número de serie es único y se puede buscar por texto y filtrar por tipo.
- Creación de tickets por clientes, con selección automática de un técnico de la especialidad correspondiente.
- Listados de tickets según el rol, búsqueda por texto y filtro por estado; acceso a la conversación e historial de actividad.
- Envío de mensajes, registro de hitos y notificación a la otra parte.
- Estados del ticket: Abierto, En proceso, Resuelto y Cerrado.
- Reapertura por el cliente titular: cambia el ticket cerrado a En proceso, registra la consulta como mensaje y hito, y notifica al técnico.
- Los mensajes solo se envían cuando el ticket está Abierto o En proceso.
- Bandeja de notificaciones y opción para marcarlas como leídas.

## Organización

- `dominio/`: estados y entidades del dominio.
- `persistencia/`: esquema SQLite y repositorios.
- `control/`: servicios de aplicación y reglas de autorización.
- `presentacion/`: interfaz de escritorio Tkinter.
- `main.py`: punto de entrada.
- `tests/`: pruebas automatizadas.
- [`docs/`](./docs/README.md): índice de casos de uso y modelos UML editables/exportados.

## Implementación actual

La aplicación usa Python, SQLite y una interfaz Tkinter organizada en capas. SQLite almacena usuarios, productos, tickets, mensajes, hitos y notificaciones; las claves foráneas y restricciones mantienen la integridad de las relaciones y evitan correos o números de serie duplicados. Los casos de uso y modelos UML relacionados con esta versión están documentados en [`docs/`](./docs/README.md).

La suite contiene pruebas automatizadas de regresión para los principales flujos. La interfaz ejecuta las operaciones de SQLite localmente, ya que el almacenamiento es local y las operaciones actuales no requieren procesamiento en segundo plano.
