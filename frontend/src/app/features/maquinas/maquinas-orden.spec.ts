import { describe, expect, it } from 'vitest';
import { MaquinaDto } from './maquinas.models';
import { ordenarMaquinas } from './maquinas-orden';

function maquina(codigo: string, tipo: string, estado: string): MaquinaDto {
  return { id: 1, codigo, tipo_maquina_id: 1, tipo_maquina: { id: 1, nombre: tipo }, estado, creado_en: '' };
}

describe('ordenarMaquinas', () => {
  const datos = [
    maquina('M-10', 'Torno', 'operativa'),
    maquina('M-2', 'Fresadora', 'en_mantenimiento'),
    maquina('M-1', 'Torno', 'detenida'),
  ];

  it('ordena por la etiqueta visible del estado sin modificar la lista original', () => {
    expect(ordenarMaquinas(datos, 'estado', 'asc').map((item) => item.codigo)).toEqual(['M-1', 'M-2', 'M-10']);
    expect(datos.map((item) => item.codigo)).toEqual(['M-10', 'M-2', 'M-1']);
  });

  it('ordena por tipo y desempata por código', () => {
    expect(ordenarMaquinas(datos, 'tipo', 'desc').map((item) => item.codigo)).toEqual(['M-1', 'M-10', 'M-2']);
  });

  it('contempla estados no registrados', () => {
    const desconocida = maquina('M-3', 'Torno', 'z_estado');
    expect(ordenarMaquinas([desconocida, datos[0]], 'estado', 'asc').map((item) => item.codigo)).toEqual(['M-10', 'M-3']);
  });
});
