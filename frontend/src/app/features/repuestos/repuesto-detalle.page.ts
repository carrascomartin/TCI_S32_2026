import { Component, DestroyRef, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { HlmBadgeImports } from '@shared/ui/badge';
import { HlmButtonImports } from '@shared/ui/button';
import { HlmCardImports } from '@shared/ui/card';
import { DataTableComponent } from '@shared/ui/table';
import { environment } from '../../../environments/environment';
import { SessionService } from '../../core/auth/session.service';
import { ESTADOS_STOCK, REPUESTOS_CONFIG } from './repuestos.config';
import { ROLES_ESCRITURA, RepuestoDto, estadoDe } from './repuestos.models';
import { RepuestosService } from './repuestos.service';

type Carga = 'cargando' | 'listo' | 'error';

@Component({
  selector: 'app-repuesto-detalle-page',
  standalone: true,
  imports: [RouterLink, HlmBadgeImports, HlmButtonImports, HlmCardImports, DataTableComponent],
  templateUrl: './repuesto-detalle.page.html',
})
export class RepuestoDetallePage {
  // Mock o real: lo decide la ruta (app.routes.ts) según environment.useMockData.
  private readonly servicio = inject(RepuestosService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly ruta = inject(ActivatedRoute);

  protected readonly config = REPUESTOS_CONFIG;
  protected readonly esDemo = environment.useMockData;
  private readonly sesion = inject(SessionService);
  protected readonly puedeEditar = computed(() =>
    this.sesion.roles().some((rol) => ROLES_ESCRITURA.includes(rol.toLowerCase())),
  );

  protected readonly repuesto = signal<RepuestoDto | null>(null);
  protected readonly carga = signal<Carga>('cargando');

  constructor() {
    this.cargar();
  }

  protected cargar(): void {
    const id = Number(this.ruta.snapshot.paramMap.get('id'));
    if (!Number.isInteger(id) || id <= 0) {
      this.carga.set('error');
      return;
    }
    this.carga.set('cargando');
    this.servicio
      .obtener(id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (repuesto) => {
          this.repuesto.set(repuesto);
          this.carga.set('listo');
        },
        error: () => this.carga.set('error'),
      });
  }

  protected info(repuesto: RepuestoDto) {
    return ESTADOS_STOCK[estadoDe(repuesto)];
  }
}
