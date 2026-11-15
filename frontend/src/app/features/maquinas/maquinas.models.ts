export interface Pagina<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
}

export interface TipoMaquinaResumenDto {
  id: number;
  nombre: string;
}

export interface TipoMaquinaDto extends TipoMaquinaResumenDto {
  descripcion: string | null;
  activo: boolean;
}

export interface DatosMaquina {
  codigo: string;
  tipo_maquina_id: number;
  numero_serie?: string | null;
  fecha_instalacion?: string | null;
}

export interface MaquinaDto {
  id: number;
  codigo: string;
  tipo_maquina_id: number;
  tipo_maquina: TipoMaquinaResumenDto;
  numero_serie?: string | null;
  estado: string;
  fecha_instalacion?: string | null;
  creado_en: string;
  actualizado_en?: string | null;
}
