# El Buen Sabor · Vertical Slice F-01: Registrar pedido

Prototipo funcional de la **primera entrega** del proyecto de Ingeniería de Software
(Universidad del Quindío, 2026). Implementa de punta a punta, **sin saltos**, la
funcionalidad **F-01 · Registrar pedido** desde la tablet del mesero (IU-01) hasta la
pantalla de cocina (IU-02): interfaz, API, lógica de negocio y base de datos.

---

## 1. Tecnologías y por qué

| Capa | Tecnología | Justificación (trazable al SyRS) |
|---|---|---|
| Frontend | **React 18 + TypeScript + Vite** | Aplicación web táctil accesible desde el navegador de la tablet, sin instalar nada (Sección 3.5). |
| Backend | **Python 3.11+ + FastAPI** | Expone la API REST interna y los **WebSockets** para eventos en tiempo real (IS-04, Sección 3.4). |
| Persistencia | **SQLite + SQLAlchemy 2 (ORM)** | Base de datos relacional local, conectada por ORM (IS-03). No requiere instalar un servidor de BD. |
| Pruebas | **pytest** (backend) y **Vitest** (frontend) | Verificación automática del flujo y de las reglas de negocio. |

> Para producción bastaría con cambiar la variable `URL_BASE_DATOS` a PostgreSQL o MySQL;
> el código no cambia porque todo pasa por el ORM y los repositorios.

---

## 2. Cómo ejecutarlo

**Requisitos:** Python 3.11 o superior y Node.js 18 o superior.

Abrir **dos terminales** en la carpeta del proyecto:

| | Windows | macOS / Linux |
|---|---|---|
| Terminal 1 (API) | `iniciar-backend.bat` | `./iniciar-backend.sh` |
| Terminal 2 (interfaz) | `iniciar-frontend.bat` | `./iniciar-frontend.sh` |

Luego abrir en el navegador:

- **Tablet del mesero (IU-01):** http://localhost:5173
- **Pantalla de cocina (IU-02):** http://localhost:5173/cocina (también desde el ícono ⚙ de la tablet)
- **Documentación interactiva de la API:** http://localhost:8000/docs

La base de datos `backend/el_buen_sabor.db` se crea sola la primera vez, con mesas, menú,
recetas e inventario de ejemplo.

<details>
<summary>Ejecución manual (sin scripts)</summary>

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows  (en macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000

# Frontend (otra terminal)
cd frontend
npm install
npm run dev
```
</details>

**Probar con una tablet real:** con el PC y la tablet en la misma red Wi-Fi, abrir en la
tablet la dirección *Network* que muestra Vite (por ejemplo `http://192.168.1.20:5173`).

---

## 3. Pruebas

```bash
cd backend && python -m pytest         # 14 pruebas: dominio + flujo completo por API
cd frontend && npm test                # 6 pruebas: lógica del pedido en curso
cd frontend && npm run typecheck       # Verificación de tipos
```

---

## 4. Trazabilidad

| Requisito | Dónde se implementa |
| **F-01 / RF-01** Registrar pedido asociado a una mesa, por categorías | `RegistrarPedido`, `PaginaMesero`, `MenuCategorias` |
| **SWR-01 / RF-03** Menú con disponibilidad según ingredientes | `Inventario.porciones_disponibles`, `ConsultarMenuDisponible`, `GET /api/menu` |
| **SWR-02** Asociar platos a la mesa | `Pedido`, `DetallePedido`, tablas `pedidos` y `detalles_pedido` |
| **SWR-03 / RF-02** Enviar comanda a cocina en tiempo real | `NotificadorWebSocket`, `/ws/eventos`, `PaginaCocina` |
| **RF-05** Descontar ingredientes al confirmar | `Inventario.consumir` |
| **RF-06** Cálculo automático del total | `Pedido.total` (backend), `calcularTotal` (frontend) |
| **RD-01** Mesa ocupada no admite nuevo pedido | `Mesa.ocupar` → `MesaNoDisponibleError` |
| **RD-02** Pedido con al menos un plato activo | `Pedido.registrar`, `ProductoInactivoError` |
| **Contrato 1** `crearPedido(numeroMesa, listaItems)` | `RegistrarPedido.ejecutar(numero_mesa, items)` |
| **CU-01 curso alterno 3a** Editar antes de confirmar | Botones − / + del resumen |
| **CU-01 curso alterno 4a** Ingrediente agotado al confirmar | Respuesta 409 + recarga del menú |


---

**Equipo:** Jean Pierre Leon, Santiago Ramirez, Pablo Gonzalez.
