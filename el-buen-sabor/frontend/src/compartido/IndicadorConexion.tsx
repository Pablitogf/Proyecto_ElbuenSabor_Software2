export function IndicadorConexion({ conectado }: { conectado: boolean }) {
  return (
    <span className={`indicador-conexion ${conectado ? "" : "indicador-conexion--caido"}`}>
      <span className="indicador-conexion__punto" aria-hidden="true" />
      {conectado ? "En línea" : "Sin conexión"}
    </span>
  );
}
