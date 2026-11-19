import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  LIMITE_LISTADO,
  Pagina,
  RepuestoCreateDto,
  RepuestoDto,
  RepuestoUpdateDto,
  UbicacionCreateDto,
  UbicacionDto,
} from './repuestos.models';
import { RepuestosService } from './repuestos.service';

@Injectable({ providedIn: 'root' })
export class RepuestosHttpService extends RepuestosService {
  private readonly http = inject(HttpClient);
  private readonly url = `${environment.apiUrl}/api/v0`;

  listar(): Observable<RepuestoDto[]> {
    const params = new HttpParams().set('limit', LIMITE_LISTADO);
    return this.http
      .get<Pagina<RepuestoDto>>(`${this.url}/repuestos`, { params })
      .pipe(map((pagina) => pagina.items));
  }

  obtener(id: number): Observable<RepuestoDto> {
    return this.http.get<RepuestoDto>(`${this.url}/repuestos/${id}`);
  }

  crear(datos: RepuestoCreateDto): Observable<RepuestoDto> {
    return this.http.post<RepuestoDto>(`${this.url}/repuestos`, datos);
  }

  actualizar(id: number, cambios: RepuestoUpdateDto): Observable<RepuestoDto> {
    return this.http.patch<RepuestoDto>(`${this.url}/repuestos/${id}`, cambios);
  }

  listarUbicaciones(): Observable<UbicacionDto[]> {
    const params = new HttpParams().set('limit', LIMITE_LISTADO);
    return this.http
      .get<Pagina<UbicacionDto>>(`${this.url}/ubicaciones`, { params })
      .pipe(map((pagina) => pagina.items));
  }

  crearUbicacion(datos: UbicacionCreateDto): Observable<UbicacionDto> {
    return this.http.post<UbicacionDto>(`${this.url}/ubicaciones`, datos);
  }
}
