import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  AlertaStockDto,
  IncidenciaDto,
  LIMITE_RESUMEN,
  Pagina,
  masRecientes,
} from './inicio.models';
import { RepuestoDto } from '../repuestos/repuestos.models';
import { InicioService } from './inicio.service';

@Injectable({ providedIn: 'root' })
export class InicioHttpService extends InicioService {
  private readonly http = inject(HttpClient);

  incidenciasRecientes(): Observable<IncidenciaDto[]> {
    return this.http
      .get<Pagina<IncidenciaDto>>(`${environment.apiUrl}/api/v0/incidencias`)
      .pipe(map((pagina) => masRecientes(pagina.items)));
  }

  /** Repuestos con disponible igual o menor al mínimo (RN-02), los más críticos primero. */
  alertasStock(): Observable<AlertaStockDto[]> {
    const params = new HttpParams().set('limit', 100);
    return this.http
      .get<Pagina<RepuestoDto>>(`${environment.apiUrl}/api/v0/repuestos`, { params })
      .pipe(
        map((pagina) =>
          pagina.items
            .filter((r) => r.activo && r.stock_disponible_total <= r.stock_minimo)
            .sort(
              (a, b) =>
                a.stock_disponible_total - a.stock_minimo - (b.stock_disponible_total - b.stock_minimo),
            )
            .slice(0, LIMITE_RESUMEN)
            .map((r) => ({
              repuesto: { id: r.id, codigo: r.codigo, nombre: r.nombre },
              stock_disponible: r.stock_disponible_total,
              stock_minimo: r.stock_minimo,
            })),
        ),
      );
  }
}