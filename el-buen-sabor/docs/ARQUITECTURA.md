# Documento de Arquitectura de Software — versión 2 (alineada con el código)

**Proyecto:** Sistema de Gestión de Pedidos y Caja — Restaurante El Buen Sabor
**Alcance de esta versión:** funcionalidades F-01 a F-06 del Plan de Requisitos.

> Esta versión corrige el documento anterior y lo amarra al código del repositorio.
> Cada patrón y componente mencionado aquí existe en una ruta concreta (ver §7 y §12).
> La sección **0** resume qué se cambió y por qué.

---

## 0. Revisión del documento anterior

| # | Qué decía | Problema | Cómo quedó |
|---|---|---|---|
| 1 | §4: el Módulo Cocina es "de solo lectura" y a la vez "permite cambiar el estado a Listo". | Contradicción. Además el Contrato 2 exige que cocina cambie el estado. | La pantalla de cocina es **interactiva**: inicia la preparación, marca cada plato y despacha. |
| 2 | §7: los únicos "patrones" son Cliente-Servidor/API REST y ORM. | Son estilos y mecanismos, no patrones de diseño. No explicaba cómo se organiza el código por dentro. | §7 documenta **arquitectura limpia por capas** + 12 patrones con su archivo: State, Strategy, Adapter, Builder, Factory, Observer, Repository, Unit of Work, Data Mapper, Inyección de dependencias, Facade (gestores) y RBAC por permisos. |
| 3 | §2/§3: tecnologías genéricas ("Framework Backend", "RDBMS", "HTML/CSS/JS"). | No se puede verificar ni desplegar. | Stack concreto: React 18 + TypeScript + Vite, Python 3.11 + FastAPI, SQLAlchemy 2, SQLite (desarrollo) / PostgreSQL (producción). |
| 4 | §10: "cifrado de extremo a extremo mediante HTTPS/TLS 1.3". | TLS cifra **el transporte** (punto a punto), no es cifrado de extremo a extremo. La DIAN además exige **firma digital** del XML. | Se habla de cifrado en tránsito con TLS 1.3 y se agrega la firma XAdES del XML como requisito pendiente de la integración real. |
| 5 | §10: "solo Administrador y Cajero pueden acceder a … cierres de caja". | Contradice RF-10: **solo el administrador** ejecuta el cierre. | Matriz RBAC por permiso (§10): el cajero ve registros de caja; solo el administrador cierra. |
| 6 | §5 y Diagrama 3: "la DIAN … valida y **retorna el CUFE**". | El CUFE lo **calcula el emisor** (SHA-384 con la clave técnica); la DIAN solo lo valida y responde con un acuse. | `calcular_cufe()` en el dominio; el adaptador DIAN recalcula y valida. |
| 7 | Contrato 3: precondición "la comunicación con la DIAN debe estar activa" para registrar la factura. | Si la DIAN cae, el cajero no podría cobrar a un cliente que ya pagó. Choca con la operación real y con CU-06 9a (que asume facturas sin CUFE). | Se agrega el estado **Pagado**: el pago y la factura se registran; la factura queda `PENDIENTE_DIAN`, se reintenta desde caja y **bloquea el cierre** hasta validarse. RD-05 se sigue cumpliendo: el pedido solo pasa a Facturado con la validación. |
| 8 | Diagrama de estados del Pedido: Registrado → … → Entregado → Facturado. | Faltaba el estado intermedio de #7 y no decía desde dónde se puede cancelar. | Registrado → En preparación → Listo → Entregado → **Pagado** → Facturado; **Cancelado solo desde Registrado** (`docs/arquitectura/estados_pedido.puml`). |
| 9 | Contrato 3: IVA 19 %. | Los restaurantes en Colombia normalmente liquidan el **Impuesto Nacional al Consumo (8 %)**, no IVA. Conviene confirmarlo con el docente. | Patrón Strategy: `IVA_19` (por defecto, como dice el documento) e `INC_8`, seleccionable con la variable `IMPUESTO_FACTURA`. El precio del menú incluye el impuesto y la factura lo desglosa. |
| 10 | §3: "el servidor se conecta de forma directa a la base de datos mediante ORM"; el diagrama de componentes dice "CRUD Pedidos [ORM]". | Acopla la lógica a la base de datos y reduce los módulos a CRUD. | El dominio no conoce el ORM. El acceso pasa por **Repository + Unit of Work**, y cada gestor aplica reglas de negocio, no CRUD (§4, §7). |
| 11 | §12 promete "los códigos de los diagramas … en PlantUML", pero solo hay imágenes. | No se pueden mantener ni versionar. | Fuentes `.puml` en `docs/arquitectura/`. |
| 12 | §8: pruebas de estrés en Wi-Fi y certificación del 99,5 %. | No existían. Documentar algo que no se hizo es un riesgo en la sustentación. | §8 describe lo que sí existe (87 pruebas automáticas) y deja la prueba de carga como trabajo siguiente. |
| 13 | §9: "local o en la nube", sin más detalle. | No dice qué limita la escalabilidad. | §9 indica que el bus de eventos y las conexiones WebSocket viven en memoria (un solo proceso); para escalar horizontalmente se reemplazan por Redis Pub/Sub sin tocar los casos de uso. |

**Observaciones al Student Book** (fuera del documento de arquitectura, pero afectan la trazabilidad):

- **CU-03 "Gestionar Menú"** repite la tabla de CU-02 (error de copiado).
- **CU-04** referencia RF-01, RF-04 y RF-13; por contenido deberían ser RF-05, RF-14 y RF-17. **CU-05** referencia RF-14; debería ser RF-15 y RF-16.
- **RF-04** dice "cuando el plato esté marcado como **servido**"; por el flujo es "**listo**".
- **RF-15** dice "los roles de rol y administrador"; probablemente quería decir "mesero y administrador".
- En **1.2**, la fila "Una solución exitosa debería" repite el texto de "El impacto es".

---

## 1. Introducción

**Descripción del sistema:** aplicación web multi-rol que digitaliza la operación del restaurante. Un pedido sigue este recorrido: mesero → cocina → mesero → caja → DIAN → cierre diario. El inventario y las reservas lo alimentan.

**Objetivo del informe:** definir la estructura del sistema (capas, componentes, patrones, tecnologías, flujos y decisiones) de forma verificable contra el código.

## 2. Contexto del sistema

**Dominio:** el restaurante opera con comandas en papel, cuentas con calculadora y cuaderno de caja, y no cumple la facturación electrónica.

**Restricciones que guían la arquitectura:**

| Requisito | Decisión que lo atiende |
|---|---|
| RNF-02: comanda a cocina en < 2 s | Eventos de dominio publicados después del commit y difundidos por WebSocket |
| RNF-03: botones táctiles ≥ 44×44 px | Sistema de componentes con `min-height: 44px` |
| RNF-04: RBAC | Permisos por endpoint (`requiere(Permiso.X)`) y por pantalla |
| RNF-06: Chrome y Safari, responsive | SPA en React con diseño adaptable a celular, tablet y escritorio |
| RNF-07: arquitectura limpia y API documentada | Capas con dependencias hacia adentro; OpenAPI automático en `/docs` |
| RF-02: sin conexión no se envía la comanda | El botón "Confirmar pedido" se bloquea si el WebSocket está caído |

**Tecnologías:**

| Capa | Tecnología |
|---|---|
| Interfaz | React 18, TypeScript (modo estricto), Vite |
| API | Python 3.11, FastAPI, Uvicorn, Pydantic 2 |
| Persistencia | SQLAlchemy 2 (ORM); SQLite en desarrollo, PostgreSQL en producción (solo cambia `URL_BASE_DATOS`) |
| Tiempo real | WebSockets (`/ws/eventos`) |
| Integraciones | DIAN (SOAP/TLS 1.3) y banco (REST/TLS 1.3) **simulados** con adaptadores intercambiables |
| Pruebas | pytest (backend) y Vitest (frontend) |

## 3. Arquitectura de alto nivel

Cliente-servidor con API REST + WebSocket. **Dentro del servidor** se usa una **arquitectura limpia (hexagonal)** de cuatro capas. Las dependencias apuntan siempre hacia el dominio:

```
 ┌──────────────────────────────────────────────────────────────┐
 │ PRESENTACIÓN   rutas REST, RBAC, esquemas JSON, WebSocket    │  adaptadores de entrada
 │  ┌────────────────────────────────────────────────────────┐  │
 │  │ APLICACIÓN   Gestores (casos de uso) + PUERTOS         │  │
 │  │  ┌──────────────────────────────────────────────────┐  │  │
 │  │  │ DOMINIO   entidades, reglas, State, Strategy     │  │  │
 │  │  └──────────────────────────────────────────────────┘  │  │
 │  └────────────────────────────────────────────────────────┘  │
 └──────────────────────────────────────────────────────────────┘
   INFRAESTRUCTURA  implementa los puertos: SQLAlchemy, DIAN, banco, bus de eventos, seguridad
   contenedor.py    raíz de composición: decide qué adaptador recibe cada puerto
```

Regla verificable: `app/dominio/` no importa nada de FastAPI, SQLAlchemy ni de la red, y sus 39 pruebas corren sin base de datos.

## 4. Componentes y módulos

### 4.1 Interfaces de usuario (frontend)

| Pantalla | Ruta | Rol | Funcionalidades |
|---|---|---|---|
| Ingreso | `/ingreso` | Todos | RF-01 autenticación (usuario + PIN) |
| IU-01 Tablet del mesero | `/mesero` | Mesero | F-01 tomar pedido · F-05 avisos de "listo" y servir · F-06 confirmar llegada · cancelar pedido |
| IU-02 Pantalla de cocina | `/cocina` | Cocinero | F-05 iniciar, marcar platos, despachar; semáforo de tiempos |
| IU-03 Módulo de caja | `/caja` | Cajero | F-02 cobro efectivo/tarjeta/mixto · F-03 factura, reintento DIAN, XML |
| IU-04 Administración | `/admin` | Administrador | Resumen y alertas, cierre/apertura de caja, F-04 inventario, F-06 reservas, simulador |
| Reservas | `/reservas` | Mesero, administrador | F-06 agenda del día |

### 4.2 Componentes del servidor

| Componente (diagrama de secuencia) | Archivo | Responsabilidad y reglas que aplica |
|---|---|---|
| **GestorPedidos** | `aplicacion/casos_de_uso/pedidos/gestor_pedidos.py` | Registrar (Contrato 1): caja abierta, mesa libre y no apartada por reserva, platos activos, stock re-consultado, kardex. Entregar (RF-04). Cancelar (devuelve ingredientes, libera la mesa) |
| **GestorCocina** | `…/cocina/gestor_cocina.py` | Contrato 2; marcar platos; despachar solo si todos están preparados |
| **GestorCobros** | `…/caja/gestor_cobros.py` | Solo pedidos entregados; el pago debe sumar exacto; tarjeta al final; libera la mesa; emite la factura |
| **GestorFacturacion** | `…/facturacion/gestor_facturacion.py` | Envío y reenvío a la DIAN; Pagado → Facturado solo con validación (RD-05) |
| **GestorJornada** | `…/caja/gestor_jornada.py` | Resumen del día; cierre con bloqueos e inconsistencias (RF-10, RF-11, CU-06 9a); apertura |
| **GestorInventario** | `…/inventario/gestor_inventario.py` | Entradas con proveedor, pérdidas con causa, mínimos con alerta, sugerencia de compra (RF-12) |
| **GestorReservas** | `…/reservas/gestor_reservas.py` | Políticas de horario, sin solapes, asignación de mesa, llegada, no-show |
| **GestorSesion** | `…/autenticacion/gestor_sesion.py` | Credenciales y token |
| **Base de datos (IS-03)** | `infraestructura/base_de_datos/` | 13 tablas; acceso solo por repositorios |

## 5. Interacciones y flujos de datos

1. **Pedido (F-01):** la tablet envía `POST /api/pedidos`. En **una transacción** se valida, se descuenta el inventario, se registra el kardex y se ocupa la mesa. Tras el commit se publica `PedidoRegistrado` y la cocina lo recibe por WebSocket.
2. **Preparación (F-05):** cocina inicia, marca los platos y despacha. `PedidoListoParaServir` llega a la tablet como aviso, que solo desaparece cuando el mesero marca "Servido".
3. **Cobro (F-02/F-03):** caja cobra (la tarjeta va por la pasarela y es lo último que se procesa). En una transacción se guardan el pago y la factura con su CUFE y se libera la mesa. Después se envía el XML a la DIAN; si no responde, la factura queda pendiente para reintento.
4. **Inventario (F-04):** cada consumo, devolución, entrada o pérdida queda en `movimientos_inventario`. Al cruzar el mínimo se publica `StockBajoMinimo`, que muestra la alerta en administración.
5. **Reservas (F-06):** la mesa se ve "Reservada" desde 30 minutos antes de la hora. La tablet no deja tomarle pedido hasta confirmar la llegada.
6. **Cierre (RF-10/11):** el administrador cuenta el efectivo. El sistema arma el reporte, muestra bloqueos e inconsistencias, envía el consolidado a la DIAN y cierra la jornada (E-08). Sin jornada abierta no se aceptan pedidos ni cobros (M-02).

Secuencia detallada del flujo 3: `docs/arquitectura/secuencia_cobrar_y_facturar.puml`.

## 6. Decisiones de diseño y justificaciones

| Decisión | Por qué | Alternativa descartada |
|---|---|---|
| Arquitectura limpia por capas | RNF-07; probar reglas sin base de datos; cambiar DIAN simulada por real sin tocar casos de uso | MVC con lógica en controladores |
| WebSockets para eventos | RNF-02 (< 2 s) sin sondeo constante | *Polling* cada N segundos |
| Eventos publicados **después** del commit | Las pantallas nunca ven un pedido que luego se revierte | Notificar dentro de la transacción |
| Estado **Pagado** antes de Facturado | Separar "el cliente pagó" de "la DIAN validó"; contingencia sin doble cobro | Bloquear el cobro si la DIAN cae |
| Tarjeta procesada al final del cobro | Si algo falla antes (efectivo insuficiente, numeración agotada), no se toca la tarjeta | Cobrar primero y validar después |
| `RESERVADA` **calculado**, no guardado | Depende de la hora; guardarlo exigiría un proceso programado que lo actualice | Columna de estado con tarea programada |
| RBAC por **permiso**, no por rol | Cambiar quién hace qué es editar una tabla (`PERMISOS_POR_ROL`) | `if rol == "ADMIN"` en cada endpoint |
| Token firmado con HMAC (sin sesión en memoria) | Sobrevive reinicios; cada pestaña tiene su sesión | Sesiones guardadas en el servidor |
| Precios con impuesto incluido; la factura desglosa | En Colombia el precio exhibido al consumidor incluye impuestos | Sumar el impuesto al cobrar |
| Aplicación web en lugar de nativa | Sin licencias ni instalación (sección 3.5 del SyRS) | Apps Android/iOS |

## 7. Patrones de diseño utilizados

| Patrón | Tipo | Dónde (ruta) | Qué resuelve |
|---|---|---|---|
| **Arquitectura limpia / Hexagonal (Puertos y Adaptadores)** | Arquitectónico | `aplicacion/puertos.py` + `infraestructura/` | El negocio no depende de frameworks ni de sistemas externos |
| **State** | Comportamiento | `dominio/estados_pedido.py` | RD-03: cada estado del pedido define sus transiciones válidas; no hay saltos ni retrocesos |
| **Strategy** | Comportamiento | `caja/estrategias_pago.py` (efectivo, tarjeta) | Agregar Nequi/Daviplata sin tocar el cobro |
| **Strategy** | Comportamiento | `dominio/impuestos.py` (IVA 19 %, INC 8 %) | Cambiar la tarifa por configuración |
| **Strategy** | Comportamiento | `dominio/agenda_mesas.py` (`MejorAjuste`) | Política de asignación de mesa intercambiable |
| **Strategy** | Comportamiento | `dominio/reabastecimiento.py` (`CoberturaPorConsumoPromedio`) | RF-12: otra fórmula de compra sin tocar el gestor |
| **Factory Method** | Creacional | `Pedido.registrar`, `Factura.emitir`, `Reserva.crear`, `Jornada.abrir`, `MovimientoInventario.entrada/merma` | Un objeto nace válido o no nace |
| **Factory** | Creacional | `FabricaEstrategiasPago`, `EmisorDeFacturas` | Elegir la estrategia; numeración DIAN y desglose al emitir |
| **Builder** | Creacional | `integraciones/dian/constructor_xml_factura.py` | XML UBL 2.1 por secciones encadenables |
| **Adapter** | Estructural | `integraciones/pasarela_simulada.py`, `integraciones/dian/servicio_dian_simulado.py` | Traducen los puertos a cada sistema externo; se reemplazan por los reales |
| **Facade** | Estructural | Los `Gestor*` | Una operación de negocio coordina varios objetos, igual que en los diagramas de secuencia |
| **Observer (Publicar/Suscribir)** | Comportamiento | `dominio/eventos.py`, `infraestructura/eventos/bus_en_memoria.py`, `presentacion/tiempo_real/difusor_eventos.py` | Los casos de uso publican sin saber quién escucha |
| **Repository** | Persistencia | `infraestructura/base_de_datos/repositorios.py` | Colecciones de entidades sin SQL en el negocio |
| **Unit of Work** | Persistencia | `infraestructura/base_de_datos/unidad_de_trabajo.py` | Todo o nada: pedido + inventario + mesa + kardex |
| **Data Mapper (ORM)** | Persistencia | `infraestructura/base_de_datos/mapeadores.py` | Entidades puras ↔ tablas |
| **Inyección de dependencias / Composition Root** | Arquitectónico | `app/contenedor.py`, `presentacion/dependencias.py` | Un único lugar conecta puertos con adaptadores |
| **RBAC** | Seguridad | `dominio/usuario.py` (`PERMISOS_POR_ROL`) | RNF-04 declarativo |

En el frontend: separación en `dominio/` (funciones puras probadas: `pedidoEnCurso.ts`, `cobro.ts`), `api/` (un solo cliente HTTP con sesión), `compartido/` (hooks reutilizables; `useEventosTiempoReal` es el lado cliente del Observer) y `paginas/` por rol.

## 8. Gestión de la calidad y pruebas

| Nivel | Cantidad | Qué cubre |
|---|---|---|
| Unitarias de dominio (pytest) | 39 | State del pedido, desglose de pago, impuestos, CUFE, numeración, cuadre de caja, inventario, sugerencia, reservas y agenda |
| Integración por API (pytest + SQLite en memoria + reloj fijo) | 37 | Un archivo por funcionalidad (F-01…F-06 y cierre), incluidos WebSocket, RBAC (401/403) y cursos alternos (tarjeta rechazada, DIAN caída, faltante de efectivo) |
| Unitarias de frontend (Vitest) | 11 | Pedido en curso y plan de cobro |
| Tipado estático | — | TypeScript estricto (`npm run typecheck`) |

El reloj se inyecta (`puertos.Reloj`), así que las reglas de horario se prueban de forma determinista.
**Siguiente paso:** prueba de carga de WebSocket (por ejemplo con Locust) en la red del restaurante para medir RNF-02 y RNF-05.

## 9. Despliegue y configuración

- **Desarrollo:** `uvicorn app.main:app` (puerto 8000) + `vite` (puerto 5173, con proxy de `/api` y `/ws`). Base SQLite que se crea con datos de demostración.
- **Producción sugerida:** `npm run build` servido por Nginx con TLS 1.3, que hace de proxy inverso hacia Uvicorn; PostgreSQL. Variables de entorno: `URL_BASE_DATOS`, `CLAVE_SECRETA`, `ORIGENES_PERMITIDOS`, `IMPUESTO_FACTURA`, `NIT_EMISOR`, `CLAVE_TECNICA_DIAN`, `MODO_DEMOSTRACION=0`.
- **Hardware:** tablets (IH-01), TV de cocina (IH-02) y computador de caja (IH-03) en la red Wi-Fi del router (IH-04).
- **Límite conocido:** el bus de eventos y las conexiones WebSocket viven en un solo proceso. Para varias réplicas se cambia `BusDeEventosEnMemoria` por un adaptador de Redis Pub/Sub (mismo puerto `PublicadorEventos`).

## 10. Consideraciones de seguridad

- **Autenticación (RF-01):** usuario + PIN con hash PBKDF2-SHA256 (120 000 iteraciones, sal por usuario). Token firmado con HMAC-SHA256 que vence en 12 h. El WebSocket también exige token.
- **Autorización (RNF-04):** permisos por endpoint y por pantalla:

| Permiso | Mesero | Cocinero | Cajero | Administrador |
|---|:-:|:-:|:-:|:-:|
| Ver salón y menú | ✓ | | ✓ | ✓ |
| Registrar / entregar / cancelar pedidos | ✓ | | | ✓ |
| Ver y preparar comandas | | ✓ | | ✓ |
| Cobrar, ver registros de caja, reenviar facturas (RF-09) | | | ✓ | ✓ |
| **Ejecutar cierre de caja (RF-10)** | | | | ✓ |
| Inventario | | | | ✓ |
| Reservas | ✓ | | | ✓ |

- **Cifrado en tránsito:** TLS 1.3 entre navegador, servidor, DIAN y banco. **Pendiente para la integración real:** firma digital XAdES del XML con el certificado del facturador.
- **Datos de tarjeta:** el sistema nunca recibe el número de la tarjeta; solo guarda el código de autorización del banco.

## 11. Referencias

- DIAN, Anexo Técnico de Factura Electrónica de Venta vigente (Resolución 000042 de 2020 y sus actualizaciones): cálculo del CUFE y estructura UBL 2.1.
- ISO/IEC/IEEE 29148:2018 — Requirements engineering.
- Student Book y Plan de Requisitos 2026 — El Buen Sabor.
- Brown, S. *The C4 model for visualising software architecture*.
- Gamma, Helm, Johnson, Vlissides. *Design Patterns* (State, Strategy, Adapter, Builder, Factory, Observer, Facade).
- Fowler, M. *Patterns of Enterprise Application Architecture* (Repository, Unit of Work, Data Mapper).
- Martin, R. *Clean Architecture*.

## 12. Diagramas (C4 y C4+1) en PlantUML

| Archivo | Nivel |
|---|---|
| `docs/arquitectura/c4_1_contexto.puml` | Nivel 1 · Contexto |
| `docs/arquitectura/c4_2_contenedores.puml` | Nivel 2 · Contenedores (con tecnologías reales) |
| `docs/arquitectura/c4_3_componentes.puml` | Nivel 3 · Componentes (gestores, dominio, adaptadores) |
| `docs/arquitectura/secuencia_cobrar_y_facturar.puml` | C4+1 · Diagrama 3 corregido |
| `docs/arquitectura/estados_pedido.puml` | Estados del Pedido con Pagado y Cancelado |

Para verlos: pegar el contenido en <https://www.plantuml.com/plantuml> o usar la extensión *PlantUML* de VS Code.
Los diagramas 1 y 2 de secuencia del Student Book siguen siendo válidos: corresponden a `GestorPedidos.registrar` y `GestorCocina.iniciar_preparacion`.
