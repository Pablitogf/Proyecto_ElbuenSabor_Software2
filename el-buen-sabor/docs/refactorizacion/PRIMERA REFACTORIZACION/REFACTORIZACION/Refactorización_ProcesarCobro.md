# Diagnóstico Técnico y Refactorización — Funcionalidad F-02: Procesar Cobro

**Universidad del Quindío** · Ingeniería de Software II  
**Restaurante El Buen Sabor**  
**Autores:** Jean Pierre León · Santiago Ramírez · Pablo González  
**Fecha:** Armenia, Quindío · 2026  

---

## 1. Contexto

* **Equipo de trabajo:** Jean Pierre León, Santiago Ramírez, Pablo González.
* **Repositorio:** Proyecto Restaurante El Buen Sabor (Módulo Backend).
* **Funcionalidad analizada:** `F-02 · Procesar cobro`.
* **Requisitos relacionados:**
  * Transacción de negocio que involucra 5 entidades: `Jornada` (verifica caja abierta), `Pedido` (pasa a pagado), `Mesa` (se libera), `Factura` (se crea con reglas DIAN) y `Pago` (se registra el cobro).
  * Integración con dos sistemas externos: pasarela bancaria (cobro de tarjetas) y la DIAN (facturación electrónica).
  * Operación crítica del negocio que involucra movimiento de dinero y cumplimiento legal.

---

## 2. Arquitectura real

El recorrido de una petición de cobro en el sistema actual se estructura en el siguiente flujo a través de las capas de la aplicación:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ Flujo del cobro (POST /api/caja/cobros)                                          │
│                                                                                  │
│ Pantalla de caja ──► rutas/caja.py · cobrar_cuenta()               [Presentación]│
│                           ▼                                                      │
│                      GestorCobros.cobrar()                          [Aplicación] │
│                        1. Jornada.exigir_abierta()                               │
│                        2. Pedido.registrar_pago()                                │
│                        3. validar_desglose()                                     │
│                        4. Mesa.liberar()                                         │
│                        5. EmisorDeFacturas.emitir(...)                           │
│                        6. Estrategia de pago (efectivo / tarjeta ──► Banco)      │
│                        7. Guardar Pago y confirmar la transacción                │
│                        8. Publicar eventos (pantallas en tiempo real)            │
│                        9. GestorFacturacion.enviar_a_dian()                      │
│                           ▼                                                      │
│                      UnidadDeTrabajoSQL ──► Repositorios ──► BD [Infraestructura]│
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Hallazgos

### Ficha de Hallazgo H-01
* **ID:** H-01
* **Tipo:** Deuda técnica
* **Ubicación:** `backend/app/presentacion/rutas/caja.py`, función `cobrar_cuenta()` (Líneas 34-40) y `reenviar_a_dian()` (Líneas 49-53).
* **Evidencia:**
  ```python
  resultado = await contenedor.cobros().cobrar(solicitud.pedido_id, ..., cajero)
  detalle = contenedor.facturacion().detalle(resultado.factura.id)
  return CobroRespuesta.desde(resultado, detalle.pedido.numero_mesa)
  ```
* **Observación:** El controlador llama primero al caso de uso de cobro y luego a un caso de uso de facturación (`detalle()`) para consultar únicamente el número de mesa, dato que `GestorCobros` ya tenía en memoria.
* **Criterio afectado:** Separación de capas y cohesión.
* **Impacto y riesgo:**
  * Genera una transacción extra con 3 consultas redundantes (`factura`, `pedido`, `pago`).
  * Falta de atomicidad en la lectura: si otro proceso modifica la factura entre ambas llamadas, la respuesta HTTP mezcla dos estados temporales distintos.
* **Acción propuesta:** Que el caso de uso `GestorCobros` incluya el número de mesa en `ResultadoCobro`, dejando al controlador únicamente la tarea de traducir la respuesta a JSON.
* **Verificación:** Ejecución de `test_respuesta_completa_del_cobro`.
* **Estado:** Pendiente (Deuda planificada).

---

### Ficha de Hallazgo H-02
* **ID:** H-02
* **Tipo:** Riesgo arquitectónico
* **Ubicación:** 
  * `aplicacion/casos_de_uso/facturacion/emisor_facturas.py` (`EmisorDeFacturas.emitir()`, L17-20).
  * `aplicacion/casos_de_uso/caja/gestor_cobros.py` (L10, L30, L53, L73).
  * `contenedor.py` (L55, L79-81).
* **Evidencia:**
  ```python
  # emisor_facturas.py (Antes)
  def emitir(self, unidad_de_trabajo: UnidadDeTrabajo, pedido: Pedido, ahora) -> Factura:
      consecutivo = max(unidad_de_trabajo.facturas.ultimo_consecutivo() + 1, self._resolucion.desde)
      factura = Factura.emitir(pedido, consecutivo, self._resolucion, self._impuesto, ahora)
      return unidad_de_trabajo.facturas.agregar(factura)
  ```
* **Observación:** 
  1. `EmisorDeFacturas` requiere que el llamador le pase una transacción/UoW abierta.
  2. Viola SRP: la clase calcula consecutivo/arma objeto (regla de negocio) y además lo persiste en base de datos.
  3. Acoplamiento fuerte: `GestorCobros` depende de la clase concreta `GestorFacturacion` en lugar de una abstracción.
  4. Falso positivo comprobado en `evidencias/demostrar_h02.py`: Si se invoca fuera de una UoW activa con BD basada en archivo, `emitir()` retorna un objeto `Factura` con ID y consecutivo, pero **no guarda nada en la BD (0 registros agregados)**.
* **Criterio afectado:** SRP (Responsabilidad Única), DIP (Inversión de Dependencias), Bajo Acoplamiento Temporal.
* **Impacto y riesgo:** Alto. Cualquier refactorización futura que mueva la llamada de emisión fuera del bloque `with self._uow:` generará facturas impresas para el cliente y enviadas a la DIAN sin respaldo real en la base de datos contable.
* **Acción propuesta:** Convertir el emisor en una fábrica pura de dominio; mover la responsabilidad de persistencia a la transacción del cobro; desacoplar el envío a la DIAN mediante un puerto (interfaz).
* **Verificación:** Pruebas de caracterización + pruebas aisladas de dominio sin base de datos (`TestEmisorDeFacturas`).
* **Estado:** **Implementado y verificado**.

---

### Ficha de Hallazgo H-03
* **ID:** H-03
* **Tipo:** Deuda técnica
* **Ubicación:** 
  * Formato de moneda: `dominio/pago.py` (L53), `estrategias_pago.py` (L24), `dominio/jornada.py` (L159-160).
  * Búsqueda de pedido: `gestor_cobros.py` (L76-80), `gestor_pedidos.py` (L168-172), `gestor_cocina.py` (L39-41).
* **Evidencia:**
  ```python
  # Duplicación de formato en 3 archivos
  f"${valor:,}".replace(",", ".")

  # Búsqueda repetida con lanzamiento de excepción
  pedido = self._uow.pedidos.obtener(pedido_id)
  if pedido is None:
      raise PedidoNoEncontradoError(pedido_id)
  ```
* **Observación:** Violación del principio DRY. La regla de formateo de moneda se encuentra duplicada en tres puntos del backend, generando inconsistencias visuales con el frontend (`"$80.000"` vs `"$ 80.000"`).
* **Criterio afectado:** DRY (Don't Repeat Yourself).
* **Impacto y riesgo:** Bajo. Afecta la mantenibilidad y consistencia de textos descriptivos de error.
* **Acción propuesta:** Crear una función helper `formatear_pesos()` en el dominio y un método `obtener_o_error()` en el repositorio de pedidos.
* **Verificación:** Pruebas unitarias de excepciones e interfaz.
* **Estado:** Pendiente (Deuda planificada).

---

## 4. Priorización

### Criterios de Evaluación (Escala 1 a 3)

| Criterio | 1 · Bajo | 2 · Medio | 3 · Alto |
| :--- | :--- | :--- | :--- |
| **Impacto** | Mejora cosmética o estilística | Mejora la mantenibilidad de un módulo | Mejora la estructura de una operación crítica (dinero, legal) |
| **Riesgo** | Imposible generar resultados incorrectos | Puede causar errores visibles o lentitud | Un cambio razonable produce información falsa sin aviso |
| **Esfuerzo** | 1 archivo, sin cambios de dependencias | Varios archivos con pruebas que lo cubren | Rediseño amplio sin cobertura previa de pruebas |

### Matriz de Priorización

| ID | Hallazgo | Categoría | Impacto | Riesgo | Esfuerzo | Prioridad | Selección |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **H-02** | Emisor depende de UoW prestada y acoplamiento con GestorFacturacion | Riesgo arquitectónico | **3** | **3** | **2** | **1** | **SELECCIONADO** |
| **H-01** | Controlador de caja coordina dos casos de uso | Deuda técnica | 2 | 1 | 1 | 2 | Pendiente |
| **H-03** | Formato de moneda y búsqueda de pedido duplicados | Deuda técnica | 1 | 1 | 1 | 3 | Pendiente |

**Razón de selección:**  
Se eligió **H-02** porque impacta la transacción financiera y legal más delicada del sistema. Presenta un riesgo crítico comprobado mediante ejecución de código y corrige una desviación de la arquitectura documentada (`docs/ARQUITECTURA.md`). Los hallazgos H-01 y H-03 presentan un riesgo bajo y permanecen registrados como deuda técnica planificada.

---

## 5. Intervención

### Cambio Elegido
Transformar `EmisorDeFacturas` en un objeto de dominio puro (fábrica) que solo aplique reglas de negocio y cálculo de consecutivos. Mover la responsabilidad de persistencia al `GestorCobros` (dentro de su propia UoW) e introducir el puerto `EnvioFacturaElectronica` para invertir la dependencia con la DIAN.

### Diseño Antes y Después

```
ANTES:
  GestorCobros ──usa──► EmisorDeFacturas ──pasa UoW──► RepositorioFacturas
       │                  (arma + numera + GUARDA)
       └──depende de──► GestorFacturacion (clase concreta)

DESPUÉS:
  GestorCobros ──1. Obtener consecutivo ──► RepositorioFacturas
       │       ──2. Armar factura ───────► EmisorDeFacturas (Dominio puro)
       │       ──3. Guardar factura ─────► RepositorioFacturas (Misma UoW)
       └──depende de──► EnvioFacturaElectronica (Puerto Protocol) ◄── GestorFacturacion
```

### Archivos Afectados
1. `backend/app/dominio/factura.py`:
   * Adición del método `ResolucionDIAN.siguiente_consecutivo()`.
   * Traslado y simplificación de `EmisorDeFacturas` como clase pura de dominio.
2. `backend/app/aplicacion/casos_de_uso/facturacion/emisor_facturas.py`: **Eliminado**.
3. `backend/app/aplicacion/puertos.py`: Creación del puerto `EnvioFacturaElectronica`.
4. `backend/app/aplicacion/casos_de_uso/caja/gestor_cobros.py`:
   * Inyección del puerto `EnvioFacturaElectronica`.
   * Adición de método interno `_emitir_factura()` respetando la UoW del cobro.
5. `backend/app/contenedor.py`: Ajuste de importaciones y cableado de dependencias desde el dominio.
6. `docs/ARQUITECTURA.md` y `docs/diagramas/secuencia_cobrar_y_facturar.puml`: Actualización de diagramas y documentación técnica.

---

## 6. Verificación

### Estrategia de Pruebas
1. **Pruebas de Caracterización (Previas):** Creación del archivo `backend/tests/test_caracterizacion_cobro.py` con 4 casos críticos (consecutivos sucesivos, reversión por fallo en tarjeta, respuesta de cobro y contingencia DIAN).
2. **Pruebas Unitarias de Dominio (Nuevas):** Creación de `TestEmisorDeFacturas` para validar el emisor de facturas en memoria sin requerir base de datos ni infraestructura.

### Resultados de Ejecución

| Estado | Pruebas Aprobadas | Pruebas Fallidas | Cobertura / Archivo de Evidencia |
| :--- | :---: | :---: | :--- |
| **Antes de refactorizar** | 80 | 0 | `evidencias/pruebas_antes.txt` |
| **Después de refactorizar** | **85** | **0** | `evidencias/pruebas_despues.txt` |
| **Diferencia de fallos** | — | **0** | `evidencias/comparacion_antes_despues.txt` |

### Demostración de Eliminación del Riesgo (`demostrar_h02_despues.py`)
```
Firma: emitir(self, pedido: Pedido, ultimo_consecutivo: int, ahora: datetime) -> Factura
Prueba sin BD: Consecutivo FEBS1001, Total: $52.000, ID=None
Resultado: El emisor no asigna ID ni interactúa con la BD. La persistencia es responsabilidad exclusiva del repositorio dentro de la transacción del cobro.
```

### Limitaciones
Las pruebas automatizadas se ejecutaron utilizando SQLite en memoria. No se realizaron pruebas de estrés con concurrencia masiva simultánea entre múltiples cajas registradoras operando en paralelo.

---

## 7. Cierre

### Lecciones Aprendidas
* **Separación de Responsabilidades:** Mezclar la lógica de creación de dominio con operaciones de persistencia en una sola clase dificulta la creación de pruebas unitarias aisladas.
* **Acoplamiento Temporal:** Depender de un estado externo implícito (como una transacción abierta en otra capa) genera vulnerabilidades de software difíciles de detectar en revisiones superficiales.

### Deuda Técnica Pendiente
* **H-01:** Retornar número de mesa en `ResultadoCobro` para simplificar la ruta HTTP en la capa de presentación.
* **H-03:** Unificar formateador de moneda en el dominio y método de consulta en el repositorio de pedidos.

### Pregunta de Cierre
**¿Qué práctica del proceso de desarrollo habría permitido detectar estos problemas antes de entregar la aplicación?**

La práctica del proceso de desarrollo que habría permitido detectar estos problemas antes de entregar la aplicación es la **Revisión de Código por Pares (Code Review) guiada por Listas de Comprobación de Arquitectura**, combinada con **Pruebas Unitarias Aisladas de la Capa de Dominio**. 

Si al momento de implementar el emisor de facturas se hubiera exigido escribir una prueba unitaria pura sin base de datos, los desarrolladores habrían notado de inmediato que era imposible instanciar o probar el emisor sin crear una `UnidadDeTrabajoSQL` mockeada o real. Esto habría evidenciado la violación del principio de Inversión de Dependencias (DIP) y la responsabilidad mezclada antes de integrar el código a la rama principal.

---

## 8. Análisis de la Refactorización (Evaluación de Sprint)

Con base en la actividad de revisión de la funcionalidad F-02, a continuación se da respuesta a las preguntas clave de evaluación del cambio aplicado al sistema:

### ¿Cuál era el problema identificado y dónde estaba localizado?
El problema principal (identificado como **H-02**) consistía en que el `EmisorDeFacturas` dependía de una transacción de base de datos "prestada" para poder funcionar, y a su vez, el `GestorCobros` dependía de un caso de uso concreto en lugar de una abstracción. 

**Localización del problema:**
*   `aplicacion/casos_de_uso/facturacion/emisor_facturas.py` (líneas 17-20, método `emitir()`).
*   `aplicacion/casos_de_uso/caja/gestor_cobros.py` (líneas 10, 30, 53 y 73).
*   `contenedor.py` (líneas 55 y 79-81).

### ¿Qué principio de diseño o atributo de calidad estaba comprometido?
Estaban comprometidos directamente tres principios de diseño SOLID y reglas de arquitectura limpia:
*   **SRP (Principio de Responsabilidad Única):** El emisor de facturas tenía dos responsabilidades mezcladas (armar/numerar la factura según reglas de negocio y, además, guardarla en la base de datos).
*   **DIP (Principio de Inversión de Dependencias):** El `GestorCobros` dependía de una implementación concreta (`GestorFacturacion`) en lugar de depender de una interfaz o abstracción.
*   **Bajo Acoplamiento (Acoplamiento temporal):** El emisor dependía de que la clase que lo llamara tuviera abierta previamente una transacción (`UnidadDeTrabajo`), un detalle interno altamente frágil.

### ¿Qué modificación realizaron y cómo cambiaron las responsabilidades o dependencias?
La modificación principal consistió en transformar el emisor en una "fábrica pura" de dominio e introducir un puerto (interfaz) para la comunicación con agentes externos.

**Cambio en responsabilidades:**
*   **Antes:** `EmisorDeFacturas` armaba, numeraba y guardaba la factura en la base de datos.
*   **Después:** `EmisorDeFacturas` (ahora en la capa de dominio) **solo arma y numera** la factura. La responsabilidad de **guardarla** se trasladó al `GestorCobros`, quien ya era el dueño nativo de la transacción. La regla de buscar el siguiente número de factura se delegó a `ResolucionDIAN`.

**Cambio en dependencias:**
*   **Antes:** `GestorCobros` dependía de la clase concreta `GestorFacturacion`.
*   **Después:** Se creó un puerto (interfaz) llamado `EnvioFacturaElectronica`. Ahora `GestorCobros` depende de esta abstracción, y `GestorFacturacion` simplemente cumple con el contrato implementándola.

### ¿Qué consecuencias tiene el cambio sobre la arquitectura de la aplicación?
El cambio alinea el código con la arquitectura documentada y elimina un riesgo arquitectónico grave:
*   **Protección de datos (Consistencia):** Ahora es imposible emitir un número de factura sin que esta se guarde obligatoriamente en la base de datos dentro de la transacción del cobro. Se elimina el riesgo de "perder" facturas.
*   **Separación de capas purificada:** El `EmisorDeFacturas` se liberó de dependencias técnicas y se movió a la capa de Dominio, ya que no necesita conocer nada sobre infraestructura o bases de datos. 
*   **Inversión de dependencias lograda:** Al usar el puerto `EnvioFacturaElectronica`, la capa de aplicación (Cobros) ya no está acoplada al detalle técnico de cómo se envía una factura a la DIAN.
*   **Alta Testabilidad:** La arquitectura ahora permite probar el dominio (`EmisorDeFacturas`) de forma aislada, sin necesidad de levantar una base de datos en memoria o simular transacciones complejas.

### ¿Qué evidencias demuestran que la funcionalidad conserva su comportamiento?
Se recolectaron cuatro evidencias principales que garantizan que el usuario y el sistema no sufrieron alteraciones funcionales:
1.  **Suite de pruebas original intacta:** Las 80 pruebas de integración existentes pasaron exitosamente (0 fallos) antes y después del cambio, demostrando que la API, las respuestas y los estados del sistema no se alteraron.
2.  **Pruebas de caracterización:** Se escribieron 4 pruebas específicas antes de tocar el código para fijar el comportamiento crítico (consecutivos, rechazos de tarjeta, datos de respuesta y contingencia DIAN). Todas siguieron pasando igual.
3.  **Nuevas pruebas habilitadas:** Gracias al desacoplamiento, se lograron escribir 5 pruebas nuevas (4 para el emisor sin base de datos y 1 del gestor aislado) que con el diseño acoplado anterior eran imposibles de implementar.
4.  **Comprobación del riesgo neutralizado:** Se ejecutó el script de demostración (`demostrar_h02_despues.py`), el cual evidenció que si se emite una factura aislada, el objeto devuelto no tiene un ID de persistencia asignado, lo que demuestra que ya no se asume un guardado automático silencioso por parte del emisor.