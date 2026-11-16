import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  AprobarPedidoCompraDto,
  CancelarPedidoCompraDto,
  Pagina,
  PedidoCompraDto,
  RecepcionCompraCreateDto,
  RecepcionCompraDto,
  UbicacionDto,
} from './pedidos-compra.models';
import { PedidosCompraService } from './pedidos-compra.service';

@Injectable({ providedIn: 'root' })
export class PedidosCompraHttpService extends PedidosCompraService {
  private readonly http = inject(HttpClient);
  private readonly url = `${environment.apiUrl}/api/v0/pedidos-compra`;
  private readonly urlUbicaciones = `${environment.apiUrl}/api/v0/ubicaciones`;

  listar(): Observable<PedidoCompraDto[]> {
    return this.http.get<Pagina<PedidoCompraDto>>(this.url).pipe(map((pagina) => pagina.items));
  }

  obtenerPorId(id: number): Observable<PedidoCompraDto> {
    return this.http.get<PedidoCompraDto>(`${this.url}/${id}`);
  }

  listarUbicaciones(): Observable<UbicacionDto[]> {
    return this.http
      .get<Pagina<UbicacionDto>>(this.urlUbicaciones)
      .pipe(map((pagina) => pagina.items));
  }

  aprobar(pedidoId: number, datos: AprobarPedidoCompraDto = {}): Observable<PedidoCompraDto> {
    return this.http.post<PedidoCompraDto>(`${this.url}/${pedidoId}/aprobacion`, datos);
  }

  cancelar(pedidoId: number, datos: CancelarPedidoCompraDto): Observable<PedidoCompraDto> {
    return this.http.post<PedidoCompraDto>(`${this.url}/${pedidoId}/cancelacion`, datos);
  }

  registrarRecepcion(
    pedidoId: number,
    datos: RecepcionCompraCreateDto,
  ): Observable<RecepcionCompraDto> {
    return this.http.post<RecepcionCompraDto>(`${this.url}/${pedidoId}/recepciones`, datos);
  }
}
