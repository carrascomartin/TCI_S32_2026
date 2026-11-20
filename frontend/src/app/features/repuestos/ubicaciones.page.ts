import { HttpErrorResponse } from '@angular/common/http';
import { Clipboard } from '@angular/cdk/clipboard';
import { Component, DestroyRef, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { HlmBadgeImports } from '@shared/ui/badge';
import { HlmButtonImports } from '@shared/ui/button';
import { HlmCardImports } from '@shared/ui/card';
import { HlmInputImports } from '@shared/ui/input';
import { HlmLabelImports } from '@shared/ui/label';
import { IconComponent } from '@shared/ui/icon';
import { DataTableComponent } from '@shared/ui/table';
import { environment } from '../../../environments/environment';
import { SessionService } from '../../core/auth/session.service';
import { ToastService } from '../../core/services/toast.service';
import { REPUESTOS_CONFIG } from './repuestos.config';
import { ROLES_ESCRITURA, UbicacionDto } from './repuestos.models';
import { RepuestosService } from './repuestos.service';

type Carga = 'cargando' | 'listo' | 'error';

/** Listado y alta de las ubicaciones del almacén. */
@Component({
  selector: 'app-ubicaciones-page',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    HlmBadgeImports,
    HlmButtonImports,
    HlmCardImports,
    HlmInputImports,
    HlmLabelImports,
    IconComponent,
    DataTableComponent,
  ],
  templateUrl: './ubicaciones.page.html',
})
export class UbicacionesPage {
  private readonly servicio = inject(RepuestosService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly toast = inject(ToastService);
  private readonly sesion = inject(SessionService);
  private readonly clipboard = inject(Clipboard);

  protected readonly config = REPUESTOS_CONFIG.ubicaciones;
  protected readonly demo = REPUESTOS_CONFIG.demo;
  protected readonly reintentar = REPUESTOS_CONFIG.reintentar;
  protected readonly esDemo = environment.useMockData;
  protected readonly puedeEditar = computed(() =>
    this.sesion.roles().some((rol) => ROLES_ESCRITURA.includes(rol.toLowerCase())),
  );

  protected readonly ubicaciones = signal<UbicacionDto[]>([]);
  protected readonly carga = signal<Carga>('cargando');
  protected readonly creando = signal(false);
  protected readonly error = signal<string | null>(null);

  protected readonly form = inject(FormBuilder).nonNullable.group({
    codigo: ['', [Validators.required, Validators.maxLength(50)]],
    descripcion: ['', Validators.maxLength(255)],
  });

  constructor() {
    this.cargar();
  }

  protected cargar(): void {
    this.carga.set('cargando');
    this.servicio
      .listarUbicaciones()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (items) => {
          this.ubicaciones.set(items);
          this.carga.set('listo');
        },
        error: () => this.carga.set('error'),
      });
  }

  protected codigoInvalido(): boolean {
    const control = this.form.controls.codigo;
    return control.invalid && (control.touched || control.dirty);
  }

  protected descripcionCorta(descripcion: string | null | undefined): string {
    const caracteres = Array.from(descripcion ?? '');
    return caracteres.length > 50 ? `${caracteres.slice(0, 50).join('')}…` : caracteres.join('');
  }

  protected copiarCodigo(codigo: string): void {
    const copiado = this.clipboard.copy(codigo);
    this.toast.show({
      variant: copiado ? 'success' : 'error',
      message: copiado ? 'Código copiado.' : 'No se pudo copiar el código.',
    });
  }

  protected crear(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const { codigo, descripcion } = this.form.getRawValue();
    this.creando.set(true);
    this.error.set(null);
    this.servicio
      .crearUbicacion({ codigo: codigo.trim(), descripcion: descripcion.trim() || null })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (ubicacion) => {
          this.creando.set(false);
          this.ubicaciones.update((items) =>
            [...items, ubicacion].sort((a, b) => a.codigo.localeCompare(b.codigo)),
          );
          this.form.reset();
          this.toast.show({ variant: 'success', message: this.config.creada });
        },
        error: (respuesta: HttpErrorResponse) => {
          this.creando.set(false);
          this.error.set(
            respuesta.status === 409
              ? this.config.duplicado
              : respuesta.status === 403
                ? this.config.sinPermiso
                : this.config.errorCrear,
          );
        },
      });
  }
}
