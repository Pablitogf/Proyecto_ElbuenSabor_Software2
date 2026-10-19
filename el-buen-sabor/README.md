# El Buen Sabor · Sistema de pedidos, cocina y caja

Prototipo funcional del proyecto de Ingeniería de Software (Universidad del Quindío, 2026).
Implementa de punta a punta (interfaz, API, reglas de negocio y base de datos) las **6 funcionalidades**
del Plan de Requisitos:

| ID | Funcionalidad | Dónde se ve | Reglas de negocio principales |
|---|---|---|---|
| **F-01** | Registrar pedido | Tablet del mesero | Mesa libre y no apartada por reserva (RD-01), platos activos (RD-02), stock re-consultado y descontado (RF-03, RF-05), caja abierta (M-02) |
| **F-02** | Procesar cobro | Módulo de caja | Solo se cobra lo servido (Contrato 3), el pago debe sumar exacto, efectivo + tarjeta (CU-02 4a), tarjeta rechazada sin registrar nada (5a), libera la mesa |
| **F-03** | Factura electrónica | Módulo de caja | Numeración autorizada, desglose de impuesto, CUFE SHA-384, XML UBL 2.1, contingencia si la DIAN cae y reintento (RD-05) |
| **F-04** | Gestionar inventario | Administración | Kardex de cada movimiento, entradas con proveedor, pérdidas con causa (RF-17), alerta de mínimo (RF-14), sugerencia de compra (RF-12) |
| **F-05** | Notificar preparación | Cocina + tablet | Flujo de estados sin saltos (RD-03, patrón State), despacho solo con todos los platos listos, aviso al mesero que solo desaparece al servir (RF-04) |
| **F-06** | Gestionar reservas | Tablet y administración | Horario 11:00–20:00, sin cruces en la misma mesa (RF-16), mejor mesa automática, mesa apartada 30 min antes, llegada y no-show con tolerancia |

Además: **inicio de sesión por rol** (RF-01, RNF-04) y **cierre de caja** con cuadre e inconsistencias (RF-10, RF-11).

La arquitectura y los patrones de diseño están documentados y justificados en
**[`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md)**, junto con la revisión del documento anterior.

---

## 1. Tecnologías

| Capa | Tecnología |
|---|---|
| Frontend | React 18 + TypeScript + Vite |
| Backend | Python 3.11+ + FastAPI (API REST + WebSockets) |
| Base de datos | SQLite local con SQLAlchemy 2 (ORM). Para PostgreSQL solo se cambia `URL_BASE_DATOS` |
| Pruebas | pytest (76 pruebas) y Vitest (11 pruebas) |

## 2. Cómo ejecutarlo

**Requisitos:** Python 3.11 o superior y Node.js 18 o superior.

Abrir **dos terminales** en la carpeta del proyecto:

| | Windows | macOS / Linux |
|---|---|---|
| Terminal 1 (API) | `iniciar-backend.bat` | `./iniciar-backend.sh` |
| Terminal 2 (interfaz) | `iniciar-frontend.bat` | `./iniciar-frontend.sh` |

Luego abrir **http://localhost:5173** y elegir quién ingresa:

| Usuario | Rol | PIN | Pantalla |
|---|---|---|---|
| Laura Gómez | Mesero | `1111` | Tablet (IU-01) |
| Carlos Muñoz | Cocina | `2222` | Pantalla de cocina (IU-02) |
| Diana Restrepo | Caja | `3333` | Módulo de caja (IU-03) |
| Sofía Arango | Administración | `0000` | Panel de administración (IU-04) — puede abrir todas las pantallas |

Cada **pestaña** del navegador tiene su propia sesión, así que se pueden tener las cuatro pantallas abiertas lado a lado.
Documentación interactiva de la API: **http://localhost:8000/docs**.

> Si vienen de la primera entrega, la base de datos cambió: el sistema crea `backend/el_buen_sabor_v2.db` nueva.
> Si `pip` ya estaba instalado antes, ejecuten de nuevo `pip install -r requirements.txt`, que incluye `uvicorn[standard]` para los WebSockets.

## 3. Guion de la demostración

Los datos iniciales ya traen cada caso listo: la **mesa 2** tiene un pedido listo para servir, la **mesa 3** está en cocina,
la **mesa 6** ya fue servida y está por cobrar, y la **mesa 7** está apartada por una reserva que llega en 20 minutos.

1. **F-01 · Mesero:** tocar la mesa 5, agregar platos (la mojarra sale "Sin stock") y confirmar. La mesa pasa a rojo y la comanda aparece en cocina.
2. **F-05 · Cocina:** "Empezar preparación", tocar cada plato y "Marcar como listo". En la tablet aparece la barra "Mesa 5 lista"; si nadie la atiende en 5 minutos, empieza a parpadear.
3. **F-05 · Mesero:** "Marcar servido". La notificación desaparece y la mesa queda "Servido · por cobrar".
4. **F-02 / F-03 · Caja:** elegir la mesa 6, efectivo, $100.000 recibidos: cambio de $20.000, factura `FEBS1001` validada, mesa libre. Botón **XML** para ver el documento enviado a la DIAN.
5. **Cursos alternos (Administración → Simulador):**
   - "Rechazar la próxima tarjeta" y cobrar con tarjeta: rechazo, no se registra nada y se cobra con otro medio (CU-02 5a).
   - Apagar la DIAN y cobrar: el pago se registra y la factura queda **Pendiente**. Volver a encender la DIAN y usar "Reintentar envío".
6. **F-04 · Administración → Inventario:** alertas de mínimo, entrada de mercancía, registro de pérdidas, sugerencia de compra y kardex.
7. **F-06 · Reservas:** la mesa 7 aparece "Reservada". En la tablet, "Confirmar llegada" la libera para tomar el pedido. En Reservas se registra una nueva y el sistema asigna la mesa más pequeña donde cabe el grupo.
8. **Cierre de caja (Administración → Resumen):** con mesas sin cobrar o facturas pendientes, el cierre se **bloquea**. Si el efectivo contado no cuadra, exige observación y confirmación. Después del cierre, la tablet muestra "Caja cerrada" y no deja tomar pedidos.

"Reiniciar datos de demostración" (en Simulador) deja todo como al inicio. Las capturas de cada paso están en `docs/capturas/`.

## 4. Estructura

```
el-buen-sabor/
├── backend/app/
│   ├── dominio/                  Entidades y reglas puras (sin frameworks)
│   │   ├── estados_pedido.py     Patrón State (RD-03)
│   │   ├── pedido.py · mesa.py · producto.py
│   │   ├── inventario.py · reabastecimiento.py (Strategy RF-12)
│   │   ├── pago.py · impuestos.py (Strategy) · factura.py (CUFE) · jornada.py (cuadre)
│   │   ├── reserva.py · agenda_mesas.py (Strategy de asignación)
│   │   ├── usuario.py (RBAC) · eventos.py (Observer) · excepciones.py
│   ├── aplicacion/
│   │   ├── puertos.py            Interfaces que el negocio necesita (repositorios, DIAN, banco, reloj…)
│   │   └── casos_de_uso/         Un "Gestor" por módulo: pedidos, cocina, caja, facturación, inventario, reservas
│   ├── infraestructura/          Adaptadores: SQLAlchemy, DIAN y banco simulados, bus de eventos, seguridad
│   ├── presentacion/             Rutas REST con RBAC, esquemas JSON, WebSocket, manejo de errores
│   ├── contenedor.py             Inyección de dependencias (raíz de composición)
│   └── main.py
├── backend/tests/                Unitarias de dominio + integración por funcionalidad
├── frontend/src/
│   ├── dominio/                  Tipos y lógica pura (pedido en curso, plan de cobro) con pruebas
│   ├── api/ · sesion/ · compartido/
│   └── paginas/                  ingreso · mesero · cocina · caja · admin · reservas
└── docs/
    ├── ARQUITECTURA.md           Documento de arquitectura corregido y alineado al código
    ├── arquitectura/*.puml       Diagramas C4 y de secuencia en PlantUML
    └── capturas/
```

## 5. Clean Code aplicado

- **Nombres del dominio** en español, iguales a los del SyRS (`registrar_pago`, `marcar_listo`, `exigir_abierta`), en el backend y en el frontend.
- **Una responsabilidad por archivo**: un gestor por módulo, un componente por archivo y un hook por preocupación.
- **Reglas en el dominio**, no en los controladores ni en la interfaz. La interfaz repite algunas validaciones solo para dar retroalimentación inmediata; el backend siempre tiene la última palabra.
- **Errores con nombre** (`MesaReservadaError`, `PagoRechazadoError`, `CierreBloqueadoError`…), traducidos a HTTP en un solo lugar.
- **Sin números mágicos**: `TOLERANCIA_LLEGADA`, `BLOQUEO_PREVIO`, `MINUTOS_PARA_INSISTIR`, `CUPO_MAXIMO_POR_TRANSACCION`…
- **Transacciones atómicas** (Unit of Work) y **eventos publicados después del commit**.
- **Dependencias hacia adentro**: el dominio no importa FastAPI ni SQLAlchemy.
- **Comentarios solo para el porqué** o para enlazar con el requisito (RF, RD, CU).

## 6. Pruebas

```bash
cd backend  && python -m pytest       # 76 pruebas: 39 de dominio + 37 de integración (F-01…F-06 y cierre)
cd frontend && npm test               # 11 pruebas: pedido en curso y plan de cobro
cd frontend && npm run typecheck      # TypeScript estricto
```

## 7. Pendiente para las siguientes entregas

- Integración real con la DIAN (SOAP, firma XAdES) y con el banco: hoy están simuladas con adaptadores intercambiables.
- Gestión del menú (RF-13), usuarios y reportes por período (CU-06 completo).
- Modo sin conexión de cocina (M-03): guardar comandas localmente y reenviarlas.
- Prueba de carga de WebSocket en la red del restaurante (RNF-02, RNF-05).
