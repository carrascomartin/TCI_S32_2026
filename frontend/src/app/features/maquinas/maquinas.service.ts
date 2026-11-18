import { Observable } from 'rxjs';
import { DatosMaquina, MaquinaDto, TipoMaquinaDto } from './maquinas.models';

export abstract class MaquinasService {
  abstract listar(): Observable<MaquinaDto[]>;
  abstract obtenerPorId(id: number): Observable<MaquinaDto>;
  abstract listarTipos(): Observable<TipoMaquinaDto[]>;
  abstract crearTipo(nombre: string): Observable<TipoMaquinaDto>;
  abstract crear(datos: DatosMaquina): Observable<MaquinaDto>;
  abstract actualizar(id: number, datos: Partial<DatosMaquina> & { estado?: string }): Observable<MaquinaDto>;
}
