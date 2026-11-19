export interface Pagina<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
}

export interface IncidenciaDto {
  id: number;
  maquina_id: number;
  descripcion: string;
  estado: string;
  turno: string;
  reportada_en: string;
  resuelta_en: string | null;
  reportada_por_usuario_id: number;
  maquina: {
    id: number;
    codigo: string;
  } | null;
  fotos: {
    id: number;
    nombre_archivo: string | null;
    tipo_mime: string;
    capturada_en: string | null;
    contenido_base64: string;
  }[];
}

export interface AlertaStockDto {
  repuesto: { id: number; codigo: string; nombre: string };
  stock_disponible: number;
  stock_minimo: number;
}

export const LIMITE_RESUMEN = 3;

export function masRecientes(items: IncidenciaDto[]): IncidenciaDto[] {
  return [...items]
    .sort((a, b) => Date.parse(b.reportada_en) - Date.parse(a.reportada_en))
    .slice(0, LIMITE_RESUMEN);
}