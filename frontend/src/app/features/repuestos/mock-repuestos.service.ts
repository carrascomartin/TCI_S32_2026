import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map, of } from 'rxjs';
import {
  Pagina,
  RepuestoCreateDto,
  RepuestoDto,
  RepuestoUpdateDto,
  UbicacionCreateDto,
  UbicacionDto,
} from './repuestos.models';
import { RepuestosService } from './repuestos.service';

/** Demostración: los cambios viven en memoria hasta recargar la página. */
@Injectable({ providedIn: 'root' })
export class MockRepuestosService extends RepuestosService {
  private readonly http = inject(HttpClient);
  private repuestos: RepuestoDto[] | null = null;
  private ubicaciones: UbicacionDto[] | null = null;

  listar(): Observable<RepuestoDto[]> {
    if (this.repuestos) return of(this.repuestos);
    return this.http.get<Pagina<RepuestoDto>>('mock/repuestos.json').pipe(
      map((pagina) => (this.repuestos = pagina.items)),
    );
  }

  obtener(id: number): Observable<RepuestoDto> {
    return this.listar().pipe(
      map((items) => {
        const repuesto = items.find((item) => item.id === id);
        if (!repuesto) throw new Error(`Repuesto ${id} inexistente`);
        return repuesto;
      }),
    );
  }

  crear(datos: RepuestoCreateDto): Observable<RepuestoDto> {
    return this.listar().pipe(
      map((items) => {
        if (items.some((item) => item.codigo === datos.codigo)) throw duplicado('Ya existe un repuesto con ese código.');
        const repuesto: RepuestoDto = {
          id: Math.max(0, ...items.map((item) => item.id)) + 1,
          ...datos,
          activo: true,
          stock: [],
          stock_fisico_total: 0,
          stock_reservado_total: 0,
          stock_disponible_total: 0,
        };
        this.repuestos = [...items, repuesto];
        return repuesto;
      }),
    );
  }

  actualizar(id: number, cambios: RepuestoUpdateDto): Observable<RepuestoDto> {
    return this.listar().pipe(
      map((items) => {
        if (items.some((item) => item.codigo === cambios.codigo && item.id !== id)) {
          throw duplicado('Ya existe un repuesto con ese código.');
        }
        const actual = items.find((item) => item.id === id);
        if (!actual) throw new Error(`Repuesto ${id} inexistente`);
        const repuesto = { ...actual, ...cambios };
        this.repuestos = items.map((item) => (item.id === id ? repuesto : item));
        return repuesto;
      }),
    );
  }

  listarUbicaciones(): Observable<UbicacionDto[]> {
    if (this.ubicaciones) return of(this.ubicaciones);
    return this.http.get<Pagina<UbicacionDto>>('mock/ubicaciones.json').pipe(
      map((pagina) => (this.ubicaciones = pagina.items.map((item) => ({ ...item, activo: item.activo ?? true })))),
    );
  }

  crearUbicacion(datos: UbicacionCreateDto): Observable<UbicacionDto> {
    return this.listarUbicaciones().pipe(
      map((items) => {
        if (items.some((item) => item.codigo === datos.codigo)) throw duplicado('Ya existe una ubicación con ese código.');
        const ubicacion: UbicacionDto = {
          id: Math.max(0, ...items.map((item) => item.id)) + 1,
          ...datos,
          activo: true,
        };
        this.ubicaciones = [...items, ubicacion];
        return ubicacion;
      }),
    );
  }
}

function duplicado(mensaje: string): HttpErrorResponse {
  return new HttpErrorResponse({ status: 409, error: { codigo: 'duplicado', mensaje } });
}
