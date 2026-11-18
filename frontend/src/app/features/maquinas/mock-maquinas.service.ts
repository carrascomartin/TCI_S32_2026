import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map, throwError } from 'rxjs';
import { DatosMaquina, MaquinaDto, Pagina, TipoMaquinaDto } from './maquinas.models';
import { MaquinasService } from './maquinas.service';

@Injectable({ providedIn: 'root' })
export class MockMaquinasService extends MaquinasService {
  private readonly http = inject(HttpClient);
  private readonly fixture = 'mock/maquinas.json';

  listar(): Observable<MaquinaDto[]> {
    return this.http.get<Pagina<MaquinaDto>>(this.fixture).pipe(map((pagina) => pagina.items));
  }

  obtenerPorId(id: number): Observable<MaquinaDto> {
    return this.http.get<Pagina<MaquinaDto>>(this.fixture).pipe(
      map((pagina) => {
        const maquina = pagina.items.find((item) => item.id === id);
        if (!maquina) throw new Error(`No existe la máquina ${id}`);
        return maquina;
      }),
    );
  }

  listarTipos(): Observable<TipoMaquinaDto[]> {
    return this.listar().pipe(map((maquinas) => Array.from(
      new Map(maquinas.map((maquina) => [maquina.tipo_maquina.id, {
        ...maquina.tipo_maquina, descripcion: null, activo: true,
      }])).values(),
    )));
  }

  crearTipo(_nombre: string): Observable<TipoMaquinaDto> {
    return throwError(() => new Error('La edición no está disponible en modo demostración.'));
  }

  crear(_datos: DatosMaquina): Observable<MaquinaDto> {
    return throwError(() => new Error('La edición no está disponible en modo demostración.'));
  }

  actualizar(_id: number, _datos: Partial<DatosMaquina> & { estado?: string }): Observable<MaquinaDto> {
    return throwError(() => new Error('La edición no está disponible en modo demostración.'));
  }
}
