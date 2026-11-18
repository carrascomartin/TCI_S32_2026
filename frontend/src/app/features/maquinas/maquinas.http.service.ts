import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import { DatosMaquina, MaquinaDto, Pagina, TipoMaquinaDto } from './maquinas.models';
import { MaquinasService } from './maquinas.service';

@Injectable({ providedIn: 'root' })
export class MaquinasHttpService extends MaquinasService {
  private readonly http = inject(HttpClient);
  private readonly url = `${environment.apiUrl}/api/v0/maquinas`;

  listar(): Observable<MaquinaDto[]> {
    const params = new HttpParams().set('limit', 100);
    return this.http
      .get<Pagina<MaquinaDto>>(this.url, { params })
      .pipe(map((pagina) => pagina.items));
  }

  obtenerPorId(id: number): Observable<MaquinaDto> {
    return this.http.get<MaquinaDto>(`${this.url}/${id}`);
  }

  listarTipos(): Observable<TipoMaquinaDto[]> {
    return this.http.get<Pagina<TipoMaquinaDto>>(`${environment.apiUrl}/api/v0/tipos-maquina?limit=100`).pipe(map((pagina) => pagina.items));
  }

  crearTipo(nombre: string): Observable<TipoMaquinaDto> {
    return this.http.post<TipoMaquinaDto>(`${environment.apiUrl}/api/v0/tipos-maquina`, { nombre });
  }

  crear(datos: DatosMaquina): Observable<MaquinaDto> {
    return this.http.post<MaquinaDto>(this.url, datos);
  }

  actualizar(id: number, datos: Partial<DatosMaquina> & { estado?: string }): Observable<MaquinaDto> {
    return this.http.patch<MaquinaDto>(`${this.url}/${id}`, datos);
  }
}
