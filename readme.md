# ️ Sistema de Ticketing "Hitos"

**Instituto Superior de Formación Técnica Nº 151**  
**Carrera:** Analista en Sistemas  
**Materia:** Algoritmos y Estructuras de Datos III (3er Año)  
**Trabajo Práctico Final Integrador - 2026**  
**Modalidad:** Semi-Presencial | **Estrategia:** Trabajo Individual  

---

## 📖 Descripción del Proyecto
El **Sistema de Ticketing "Hitos"** es una aplicación de escritorio diseñada para la gestión de atención al cliente y soporte técnico. El sistema permite documentar solicitudes, administrar el ciclo de vida de los casos (tickets) y facilitar la comunicación continua entre clientes y representantes técnicos a través de un hilo de interacciones denominado **"Hitos"**.

El sistema garantiza la asignación inteligente de técnicos basada en la especialización por rubro (tipo de producto) y asegura una experiencia fluida mediante notificaciones en tiempo real y una interfaz gráfica asíncrona.

---

## 🎯 Objetivos
1. Modelar e implementar un sistema de gestión de tickets robusto.
2. Aplicar la metodología de Desarrollo Guiado por Pruebas (**TDD**).
3. Implementar una arquitectura **MVC** que separe la lógica de negocio de la interfaz gráfica.
4. Garantizar la responsividad de la UI mediante **procesamiento asíncrono**.
5. Implementar persistencia en memoria mediante repositorios y colecciones.

---

## 📋 Requerimientos del Sistema

### ✅ Requerimientos Funcionales
1. **Gestión de Usuarios:** Listado y administración de usuarios (Clientes, Técnicos, Administradores).
2. **Gestión de Productos y Tipos:** 
   - Administración de tipos de productos (Línea blanca, cocina, electrónica, pequeños electrodomésticos).
   - Listado de productos (general y filtrado por tipo).
3. **Gestión de Hitos:** Listado y registro de interacciones/mensajes dentro de un ticket.
4. **Notificaciones:** Alertas a las partes ante nuevas interacciones, cambios de estado o reaperturas.
5. **Gestión de Estados:** Ciclo de vida del ticket (`Abierto`, `En proceso`, `Resuelto`, `Cerrado`).
6. **Gestión de Tickets:**
   - Vinculación de Clientes, Técnicos, Productos e Hitos.
   - Actualización de estados y registro de mensajes.
   - Asignación automática/manual de técnicos según especialidad (tipo de producto).
   - Reapertura de tickets cerrados con registro de hitos.

### ️ Requerimientos No Funcionales
- **Metodología:** Codificación bajo **TDD** (Test-Driven Development).
- **Seguridad:** Módulo de autenticación (Login).
- **Integridad:** El sistema no permitirá la duplicidad de usuarios ni productos.
- **UI/UX:** Interfaz gráfica con **procesamiento asíncrono** (hilos/tasks) para evitar bloqueos (freeze) en operaciones de I/O o cálculos largos.
- **Arquitectura:** Separación estricta de responsabilidades mediante **MVC** (Presentación, Control, Persistencia, Dominio).

---


###  Diagrama de Arquitectura MVC
El sistema está organizado en cuatro capas principales:

```
┌─────────────────────────────────────────────────────────────┐
│  PRESENTACIÓN                                                │
│  • GUITicket                                                 │
│  • GUIProducto                                               │
─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  CONTROL                                                     │
│  • TicketController                                          │
│  • ProductoController                                        │
│  • NotificacionController                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  PERSISTENCIA                                                │
│  • TicketRepository → ColeccionTickets                       │
│  • ProductoRepository → ColeccionProductos                   │
│  • UsuarioRepository → ColeccionUsuarios                     │
│  • NotificacionRepository → ColeccionNotificaciones          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  DOMINIO                                                     │
│  • Usuario (Cliente, Tecnico, Admin)                         │
│  • Ticket, Producto, TipoProducto                            │
│  • Mensaje, Hito, Notificacion                               │
│  • EstadoTicket (Enumeración)                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Arquitectura y Metodología

### 🏗️ Patrón de Diseño: MVC con Capas
El sistema implementa una arquitectura de **4 capas** bien definidas:

1. **Presentación (GUI):**
   - `GUITicket`: Interfaz para gestión de tickets
   - `GUIProducto`: Interfaz para gestión de productos
   - Solo se encarga de renderizar y capturar eventos de usuario

2. **Control (Controllers):**
   - `TicketController`: Orquesta operaciones de tickets
   - `ProductoController`: Orquesta operaciones de productos
   - `NotificacionController`: Gestiona notificaciones
   - Actúan como intermediarios entre UI y lógica de negocio

3. **Persistencia (Repositories):**
   - `TicketRepository`, `ProductoRepository`, `UsuarioRepository`, `NotificacionRepository`
   - Gestionan el acceso a datos mediante colecciones en memoria
   - Implementan patrón Repository para abstraer la persistencia

4. **Dominio (Model):**
   - Entidades de negocio: `Usuario`, `Ticket`, `Producto`, `Mensaje`, `Hito`, `Notificacion`
   - Contienen la lógica de negocio y reglas de dominio
   - `EstadoTicket` como enumeración para el ciclo de vida

### 🔄 Procesamiento Asíncrono
Para cumplir con el requerimiento de no bloquear la interfaz, las operaciones de:
- Búsqueda en repositorios
- Creación de notificaciones
- Actualización de colecciones

Se ejecutarán en **hilos secundarios / tareas asíncronas**, utilizando callbacks o promesas/futures para actualizar la UI una vez finalizadas.

### 🧪 Metodología TDD (Test-Driven Development)
El ciclo de vida del código seguirá la regla de las 3R:
1. **Red:** Escribir una prueba unitaria que falle
2. **Green:** Escribir el código mínimo para que la prueba pase
3. **Refactor:** Limpiar y optimizar el código manteniendo las pruebas en verde

**Ejemplo de tests a implementar:**
- `test_crear_ticket_asigna_tecnico_correcto()`
- `test_reabrir_ticket_cerrado_crea_hito()`
- `test_enviar_mensaje_genera_notificacion()`
- `test_crear_producto_duplicado_falla()`

---

## 🚧 Estado del Proyecto (Hitos)

- [x] **Hito 1:** Definición de Requerimientos y Marco Teórico.
- [x] **Hito 2:** Modelado UML (Casos de Uso, Clases y Secuencia).
- [x] **Hito 3:** Diagramas de Secuencia detallados (Creación, Mensaje, Reapertura, Producto).
- [ ] **Hito 4:** Configuración del entorno y pruebas unitarias iniciales (TDD).
- [ ] **Hito 5:** Desarrollo de la Lógica de Negocio (Modelo y Controladores).
- [ ] **Hito 6:** Desarrollo de la Interfaz Gráfica y conciliación Asíncrona.
- [ ] **Hito 7:** Integración, pruebas finales y entrega.

---

## 📁 Posible Estructura del Proyecto a modificar

```
SistemaTicketing/
├── presentacion/
│   ├── GUITicket.py
│   └── GUIProducto.py
├── control/
│   ├── TicketController.py
│   ├── ProductoController.py
│   └── NotificacionController.py
├── persistencia/
│   ├── TicketRepository.py
│   ├── ProductoRepository.py
│   ├── UsuarioRepository.py
│   ├── NotificacionRepository.py
│   ── colecciones/
│       ├── ColeccionTickets.py
│       ├── ColeccionProductos.py
│       ├── ColeccionUsuarios.py
│       └── ColeccionNotificaciones.py
├── dominio/
│   ├── Usuario.py
│   ├── Cliente.py
│   ├── Tecnico.py
│   ├── Admin.py
│   ├── Ticket.py
│   ├── Producto.py
│   ├── TipoProducto.py
│   ├── Mensaje.py
│   ├── Hito.py
│   ├── Notificacion.py
│   └── EstadoTicket.py
├── tests/
│   ├── test_ticket.py
│   ├── test_producto.py
│   └── test_notificacion.py
└── README.md
```

---




