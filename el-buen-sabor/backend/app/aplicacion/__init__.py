"""Capa de aplicación: casos de uso que orquestan el dominio a través de puertos.

Cada "Gestor" corresponde al objeto controlador de los diagramas de secuencia
(GestorPedidos, GestorCocina, GestorFacturacion…). No contiene reglas de negocio:
las delega en el dominio y coordina transacción, integraciones y eventos.
"""
