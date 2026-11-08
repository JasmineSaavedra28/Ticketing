# Sistema de Ticketing Hitos

Aplicación de escritorio en Python para registrar productos, crear y administrar tickets de soporte y mantener el historial de conversación (mensajes e hitos). Los datos persisten en SQLite.

## Requisitos y ejecución

- Python 3.10 o posterior.
- No requiere paquetes externos: utiliza Tkinter y SQLite de la biblioteca estándar.

Desde la carpeta del proyecto:

```bash
py main.py
```

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
- Catálogo de tipos y productos; el número de serie es único y se puede filtrar por tipo.
- Creación de tickets por clientes, con selección automática de un técnico de la especialidad correspondiente.
- Listados de tickets según el rol y acceso a la conversación y la línea de hitos.
- Envío de mensajes, registro de hitos y notificación a la otra parte.
- Estados del ticket: Abierto, En proceso y Cerrado.
- Reapertura por el cliente titular: cambia el ticket cerrado a En proceso, registra la consulta como mensaje y hito, y notifica al técnico.
- Los mensajes solo se envían cuando el ticket está Abierto o En proceso.
- Bandeja de notificaciones y opción para marcarlas como leídas.

## Organización

- `dominio/`: estados y entidades del dominio.
- `persistencia/`: esquema SQLite y repositorios.
- `control/`: servicios de aplicación y reglas de autorización.
- `presentacion/`: interfaz de escritorio Tkinter.
- `main.py`: punto de entrada.

## Alcance y criterios aplicados

La consigna actual solicita Python y persistencia SQLite, por lo que SQLite reemplaza la persistencia en memoria mencionada en la documentación anterior. Los casos de uso CU01–CU04 guían los flujos implementados. Las tablas tienen claves foráneas y restricciones de unicidad para correo y número de serie.

El requisito original también mencionaba procesamiento asíncrono y TDD. La consigna actual compartida pide explícitamente Python y SQLite; no especifica procesamiento asíncrono. La interfaz ejecuta las operaciones SQLite localmente. El requisito TDD y las pruebas automatizadas todavía deben completarse.

