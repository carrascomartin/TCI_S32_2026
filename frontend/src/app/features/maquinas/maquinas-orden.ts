import { ESTADOS_MAQUINA } from './maquinas.config';
import { MaquinaDto } from './maquinas.models';

export type CampoOrden = 'tipo' | 'estado';
export type DireccionOrden = 'asc' | 'desc';

export function ordenarMaquinas(maquinas: MaquinaDto[], campo: CampoOrden, direccion: DireccionOrden): MaquinaDto[] {
  const valor = (maquina: MaquinaDto): string => campo === 'tipo'
    ? maquina.tipo_maquina.nombre
    : ESTADOS_MAQUINA[maquina.estado]?.etiqueta ?? maquina.estado;
  const sentido = direccion === 'asc' ? 1 : -1;
  return [...maquinas].sort((a, b) =>
    sentido * valor(a).localeCompare(valor(b), 'es', { sensitivity: 'base', numeric: true })
      || a.codigo.localeCompare(b.codigo, 'es', { sensitivity: 'base', numeric: true }),
  );
}
