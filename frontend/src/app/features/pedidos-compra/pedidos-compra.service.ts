import { Observable } from 'rxjs';
import {
  AprobarPedidoCompraDto,
  CancelarPedidoCompraDto,
  PedidoCompraDto,
  RecepcionCompraCreateDto,
  RecepcionCompraDto,
  UbicacionDto,
} from './pedidos-compra.models';

export abstract class PedidosCompraService {
  abstract listar(): Observable<PedidoCompraDto[]>;
  abstract obtenerPorId(id: number): Observable<PedidoCompraDto>;
  abstract listarUbicaciones(): Observable<UbicacionDto[]>;
  abstract aprobar(pedidoId: number, datos?: AprobarPedidoCompraDto): Observable<PedidoCompraDto>;
  abstract cancelar(pedidoId: number, datos: CancelarPedidoCompraDto): Observable<PedidoCompraDto>;
  abstract registrarRecepcion(
    pedidoId: number,
    datos: RecepcionCompraCreateDto,
  ): Observable<RecepcionCompraDto>;
}
