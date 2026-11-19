import { Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { SessionService } from '../../core/auth/session.service';
import { HlmBadgeImports } from '@shared/ui/badge';
import { HlmButtonImports } from '@shared/ui/button';
import { HlmCardImports } from '@shared/ui/card';
import { environment } from '../../../environments/environment';
import { ESTADOS_MAQUINA, MAQUINAS_CONFIG } from './maquinas.config';
import { MaquinaDto, TipoMaquinaDto } from './maquinas.models';
import { MaquinasService } from './maquinas.service';

type Carga = 'cargando' | 'listo' | 'error';

@Component({
  selector: 'app-maquina-detalle-page',
  standalone: true,
  imports: [RouterLink, FormsModule, HlmBadgeImports, HlmButtonImports, HlmCardImports],
  templateUrl: './maquina-detalle.page.html',
})
export class MaquinaDetallePage {
  private readonly servicio = inject(MaquinasService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly ruta = inject(ActivatedRoute);
  private readonly sesion = inject(SessionService);

  protected readonly config = MAQUINAS_CONFIG;
  protected readonly esDemo = environment.useMockData;
  protected readonly maquina = signal<MaquinaDto | null>(null);
  protected readonly carga = signal<Carga>('cargando');
  protected readonly guardando = signal(false);
  protected readonly mensajeEdicion = signal('');
  protected readonly tipos = signal<TipoMaquinaDto[]>([]);
  protected codigoEdicion = '';
  protected serieEdicion = '';
  protected estadoEdicion = '';
  protected tipoEdicion = 0;
  protected fechaEdicion = '';

  protected get puedeEditar(): boolean {
    return !this.esDemo && this.sesion.roles().includes('encargado_mantenimiento');
  }

  constructor() {
    this.cargar();
    if (this.puedeEditar) {
      this.servicio.listarTipos().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
        next: (tipos) => this.tipos.set(tipos),
        error: () => this.mensajeEdicion.set('No se pudieron cargar los tipos.'),
      });
    }
  }

  protected cargar(): void {
    const id = Number(this.ruta.snapshot.paramMap.get('id'));
    this.carga.set('cargando');
    this.servicio
      .obtenerPorId(id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (maquina) => {
          this.maquina.set(maquina);
          this.codigoEdicion = maquina.codigo;
          this.serieEdicion = maquina.numero_serie ?? '';
          this.estadoEdicion = maquina.estado;
          this.tipoEdicion = maquina.tipo_maquina_id;
          if (maquina.fecha_instalacion) {
            const fecha = new Date(maquina.fecha_instalacion);
            this.fechaEdicion = new Date(fecha.getTime() - fecha.getTimezoneOffset() * 60_000)
              .toISOString().slice(0, 16);
          } else {
            this.fechaEdicion = '';
          }
          this.carga.set('listo');
        },
        error: () => this.carga.set('error'),
      });
  }

  protected guardar(): void {
    const actual = this.maquina();
    if (!actual || !this.codigoEdicion.trim() || !this.estadoEdicion.trim() || this.guardando()) return;
    this.guardando.set(true);
    this.servicio.actualizar(actual.id, {
      codigo: this.codigoEdicion.trim(),
      numero_serie: this.serieEdicion.trim() || null,
      estado: this.estadoEdicion.trim(),
      tipo_maquina_id: Number(this.tipoEdicion),
      fecha_instalacion: this.fechaEdicion ? new Date(this.fechaEdicion).toISOString() : null,
    }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (maquina) => {
        this.maquina.set(maquina);
        this.mensajeEdicion.set('Máquina actualizada.');
        this.guardando.set(false);
      },
      error: () => {
        this.mensajeEdicion.set('No se pudo actualizar la máquina.');
        this.guardando.set(false);
      },
    });
  }

  protected estado(valor: string) {
    return ESTADOS_MAQUINA[valor] ?? { etiqueta: valor, variante: 'outline' as const };
  }

  protected fecha(valor: string | null | undefined): string {
    return valor ? new Date(valor).toLocaleString('es-AR') : this.config.detalle.noInformado;
  }
}
