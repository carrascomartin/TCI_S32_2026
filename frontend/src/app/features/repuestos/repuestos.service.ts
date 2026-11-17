import { Observable } from 'rxjs';
import {
  RepuestoCreateDto,
  RepuestoDto,
  RepuestoUpdateDto,
  UbicacionCreateDto,
  UbicacionDto,
} from './repuestos.models';

/**
 * Contrato de datos de las vistas de repuestos (T12).
 * Lo cumplen RepuestosHttpService (API real) y MockRepuestosService (fixtures).
 * Es una clase abstracta y no una interface porque Angular la usa como token de inyección.
 */
export abstract class RepuestosService {
  abstract listar(): Observable<RepuestoDto[]>;
  abstract obtener(id: number): Observable<RepuestoDto>;
  abstract crear(datos: RepuestoCreateDto): Observable<RepuestoDto>;
  abstract actualizar(id: number, cambios: RepuestoUpdateDto): Observable<RepuestoDto>;
  abstract listarUbicaciones(): Observable<UbicacionDto[]>;
  abstract crearUbicacion(datos: UbicacionCreateDto): Observable<UbicacionDto>;
}
