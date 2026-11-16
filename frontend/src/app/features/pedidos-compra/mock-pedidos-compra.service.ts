import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map, of } from 'rxjs';
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
export class MockPedidosCompraService extends PedidosCompraService {
  private readonly http = inject(HttpClient);
  private readonly fixture = 'mock/pedidos-compra.json';
  private readonly fixtureUbicaciones = 'mock/ubicaciones.json';
  private siguienteRecepcionId = 9000;
  /** Resoluciones de demostración: viven solo en memoria, hasta recargar la página. */
  private readonly resueltos = new Map<number, PedidoCompraDto>();

  listar(): Observable<PedidoCompraDto[]> {
    return this.http
      .get<Pagina<PedidoCompraDto>>(this.fixture)
      .pipe(map((pagina) => pagina.items.map((item) => this.resueltos.get(item.id) ?? item)));
  }

  obtenerPorId(id: number): Observable<PedidoCompraDto> {
    return this.http.get<Pagina<PedidoCompraDto>>(this.fixture).pipe(
      map((pagina) => {
        const pedido = this.resueltos.get(id) ?? pagina.items.find((item) => item.id === id);
        if (!pedido) throw new Error(`No existe el pedido ${id}`);
        return pedido;
      }),
    );
  }

  listarUbicaciones(): Observable<UbicacionDto[]> {
    return this.http
      .get<Pagina<UbicacionDto>>(this.fixtureUbicaciones)
      .pipe(map((pagina) => pagina.items));
  }

  aprobar(pedidoId: number, _datos: AprobarPedidoCompraDto = {}): Observable<PedidoCompraDto> {
    return this.resolver(pedidoId, { estado: 'confirmado' });
  }

  cancelar(pedidoId: number, datos: CancelarPedidoCompraDto): Observable<PedidoCompraDto> {
    return this.resolver(pedidoId, { estado: 'cancelado', motivo_cancelacion: datos.motivo });
  }

  private resolver(
    pedidoId: number,
    cambios: Pick<PedidoCompraDto, 'estado'> & Partial<PedidoCompraDto>,
  ): Observable<PedidoCompraDto> {
    return this.obtenerPorId(pedidoId).pipe(
      map((pedido) => {
        if (pedido.estado !== 'pendiente_aprobacion') {
          throw new Error(`El pedido ${pedidoId} no está pendiente de aprobación`);
        }
        const resuelto: PedidoCompraDto = {
          ...pedido,
          ...cambios,
          revision_resuelta_por_usuario_id: 0,
          revision_resuelta_en: new Date().toISOString(),
        };
        this.resueltos.set(pedidoId, resuelto);
        return resuelto;
      }),
    );
  }

  /** Demostración: no persiste nada, solo simula la respuesta del servicio real. */
  registrarRecepcion(
    pedidoId: number,
    datos: RecepcionCompraCreateDto,
  ): Observable<RecepcionCompraDto> {
    const recepcion: RecepcionCompraDto = {
      id: this.siguienteRecepcionId++,
      pedido_compra_id: pedidoId,
      recibida_por_usuario_id: 0,
      delegada_a_usuario_id: datos.delegada_a_usuario_id ?? null,
      recibida_en: new Date().toISOString(),
      notas: datos.notas ?? null,
    };
    return of(recepcion);
  }
}
