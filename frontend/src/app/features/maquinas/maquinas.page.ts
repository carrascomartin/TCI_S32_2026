import { Component, DestroyRef, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { SessionService } from '../../core/auth/session.service';
import { HlmBadgeImports } from '@shared/ui/badge';
import { HlmButtonImports } from '@shared/ui/button';
import { HlmCardImports } from '@shared/ui/card';
import { HlmInputImports } from '@shared/ui/input';
import { DataTableComponent } from '@shared/ui/table';
import { environment } from '../../../environments/environment';
import { ESTADOS_MAQUINA, MAQUINAS_CONFIG } from './maquinas.config';
import { MaquinaDto, TipoMaquinaDto } from './maquinas.models';
import { MaquinasService } from './maquinas.service';
import { CampoOrden, DireccionOrden, ordenarMaquinas } from './maquinas-orden';

type Carga = 'cargando' | 'listo' | 'error';

@Component({
  selector: 'app-maquinas-page',
  standalone: true,
  imports: [
    RouterLink,
    FormsModule,
    HlmBadgeImports,
    HlmButtonImports,
    HlmCardImports,
    HlmInputImports,
    DataTableComponent,
  ],
  templateUrl: './maquinas.page.html',
})
export class MaquinasPage {
  private readonly servicio = inject(MaquinasService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly sesion = inject(SessionService);

  protected readonly config = MAQUINAS_CONFIG;
  protected readonly esDemo = environment.useMockData;
  protected readonly maquinas = signal<MaquinaDto[]>([]);
  protected readonly carga = signal<Carga>('cargando');
  protected readonly busqueda = signal('');
  protected readonly tipoSeleccionado = signal('');
  protected readonly estadoSeleccionado = signal('');
  protected readonly campoOrden = signal<CampoOrden>('estado');
  protected readonly direccionOrden = signal<DireccionOrden>('asc');
  protected readonly tiposDisponibles = signal<TipoMaquinaDto[]>([]);
  protected readonly mensajeFormulario = signal('');
  protected readonly guardando = signal(false);
  protected readonly puedeEditar = computed(() => !this.esDemo && this.sesion.roles().includes('encargado_mantenimiento'));
  protected codigoNuevo = '';
  protected tipoNuevo = '';
  protected idTipoNuevo = 0;
  protected serieNueva = '';
  protected fechaNueva = '';

  protected readonly tipos = computed(() => {
    const tipos = new Map<number, string>();
    for (const maquina of this.maquinas()) {
      tipos.set(maquina.tipo_maquina_id, maquina.tipo_maquina.nombre);
    }
    return Array.from(tipos, ([id, nombre]) => ({ id, nombre })).sort((a, b) =>
      a.nombre.localeCompare(b.nombre, 'es'),
    );
  });

  protected readonly estados = computed(() =>
    [...new Set(this.maquinas().map((maquina) => maquina.estado))].sort((a, b) =>
      a.localeCompare(b, 'es'),
    ),
  );

  protected readonly maquinasVisibles = computed(() => {
    const termino = this.busqueda().trim().toLocaleLowerCase('es');
    const tipo = this.tipoSeleccionado();
    const estado = this.estadoSeleccionado();

    const filtradas = this.maquinas().filter((maquina) => {
      const coincideTipo = !tipo || String(maquina.tipo_maquina_id) === tipo;
      const coincideEstado = !estado || maquina.estado === estado;
      const coincideBusqueda =
        !termino ||
        [
          maquina.codigo,
          maquina.numero_serie ?? '',
          maquina.tipo_maquina.nombre,
          maquina.estado,
        ].some((valor) => valor.toLocaleLowerCase('es').includes(termino));

      return coincideTipo && coincideEstado && coincideBusqueda;
    });
    return ordenarMaquinas(filtradas, this.campoOrden(), this.direccionOrden());
  });

  protected ordenar(campo: CampoOrden): void {
    if (this.campoOrden() === campo) {
      this.direccionOrden.update((direccion) => direccion === 'asc' ? 'desc' : 'asc');
    } else {
      this.campoOrden.set(campo);
      this.direccionOrden.set('asc');
    }
  }

  constructor() {
    this.cargar();
    if (!this.esDemo) this.cargarTipos();
  }

  protected cargarTipos(): void {
    this.servicio.listarTipos().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (tipos) => this.tiposDisponibles.set(tipos),
      error: () => this.mensajeFormulario.set('No se pudieron cargar los tipos de máquina.'),
    });
  }

  protected crearTipo(): void {
    const nombre = this.tipoNuevo.trim();
    if (!nombre || this.guardando()) return;
    this.guardando.set(true);
    this.servicio.crearTipo(nombre).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (tipo) => {
        this.tipoNuevo = '';
        this.idTipoNuevo = tipo.id;
        this.mensajeFormulario.set('Tipo creado correctamente.');
        this.guardando.set(false);
        this.cargarTipos();
      },
      error: () => {
        this.mensajeFormulario.set('No se pudo crear el tipo. Revisá si el nombre ya existe.');
        this.guardando.set(false);
      },
    });
  }

  protected crearMaquina(): void {
    if (!this.codigoNuevo.trim() || !this.idTipoNuevo || this.guardando()) return;
    this.guardando.set(true);
    this.servicio.crear({
      codigo: this.codigoNuevo.trim(),
      tipo_maquina_id: Number(this.idTipoNuevo),
      numero_serie: this.serieNueva.trim() || null,
      fecha_instalacion: this.fechaNueva ? new Date(this.fechaNueva).toISOString() : null,
    }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.codigoNuevo = '';
        this.serieNueva = '';
        this.fechaNueva = '';
        this.mensajeFormulario.set('Máquina creada correctamente.');
        this.guardando.set(false);
        this.cargar();
      },
      error: () => {
        this.mensajeFormulario.set('No se pudo crear la máquina. Revisá el código y el número de serie.');
        this.guardando.set(false);
      },
    });
  }

  protected cargar(): void {
    this.carga.set('cargando');
    this.servicio
      .listar()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (maquinas) => {
          this.maquinas.set(maquinas);
          this.carga.set('listo');
        },
        error: () => this.carga.set('error'),
      });
  }

  protected cambiarBusqueda(event: Event): void {
    this.busqueda.set((event.target as HTMLInputElement).value);
  }

  protected cambiarTipo(event: Event): void {
    this.tipoSeleccionado.set((event.target as HTMLSelectElement).value);
  }

  protected cambiarEstado(event: Event): void {
    this.estadoSeleccionado.set((event.target as HTMLSelectElement).value);
  }

  protected limpiarFiltros(): void {
    this.busqueda.set('');
    this.tipoSeleccionado.set('');
    this.estadoSeleccionado.set('');
  }

  protected estado(valor: string) {
    return ESTADOS_MAQUINA[valor] ?? { etiqueta: valor, variante: 'outline' as const };
  }

  protected fecha(valor: string | null | undefined): string {
    return valor ? new Date(valor).toLocaleDateString('es-AR') : this.config.detalle.noInformado;
  }
}
