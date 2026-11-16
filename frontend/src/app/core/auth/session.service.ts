import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, catchError, switchMap, tap, throwError } from 'rxjs';
import { environment } from '../../../environments/environment';
import { TokenRespuesta, UsuarioPerfil } from '../../features/auth/auth.models';
import { AuthService } from '../../features/auth/auth.service';

@Injectable({ providedIn: 'root' })
export class SessionService {
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  private readonly TOKEN_KEY = 'tci_auth_token';
  private readonly EXPIRES_KEY = 'tci_auth_expires_at';

  private readonly _usuario = signal<UsuarioPerfil | null>(null);
  private readonly _cargandoPerfil = signal(false);
  private readonly versionSesion = signal(0);

  readonly usuario = this._usuario.asReadonly();
  readonly roles = computed(() => this._usuario()?.roles ?? []);
  readonly esModoMock = computed(() => environment.useMockData);
  readonly cargandoPerfil = this._cargandoPerfil.asReadonly();

  readonly nombreMostrar = computed(() => {
    const user = this._usuario();
    if (!user) {
      return '';
    }
    const completo = [user.nombre, user.apellido].filter(Boolean).join(' ').trim();
    return completo || user.correo;
  });

  readonly estaAutenticado = computed(() => {
    this.versionSesion();
    if (environment.useMockData) {
      return true;
    }
    return Boolean(this.obtenerToken()) && !this.tokenVencido();
  });

  constructor() {
    queueMicrotask(() => this.inicializarSesion());
  }

  private inicializarSesion(): void {
    if (environment.useMockData) {
      this._cargandoPerfil.set(true);
      this.authService.obtenerPerfil().subscribe({
        next: (perfil) => {
          this._usuario.set({ ...perfil, esDemo: true });
          this._cargandoPerfil.set(false);
        },
        error: () => {
          this._usuario.set({
            usuario_id: 0,
            correo: 'demo@tci.local',
            nombre: 'Usuario',
            apellido: 'Demostración',
            roles: ['encargado_mantenimiento'],
            esDemo: true,
          });
          this._cargandoPerfil.set(false);
        },
      });
      return;
    }

    if (this.obtenerToken() && !this.tokenVencido()) {
      this.cargarPerfil().subscribe({
        error: () => this.cerrarSesion(),
      });
    } else {
      this.limpiarStorage();
    }
  }

  iniciarSesion(correo: string, password: string): Observable<UsuarioPerfil> {
    return this.authService.login(correo, password).pipe(
      tap((respuesta) => this.guardarToken(respuesta)),
      switchMap(() => this.cargarPerfil()),
      catchError((err) => {
        this.limpiarStorage();
        return throwError(() => err);
      }),
    );
  }

  cargarPerfil(): Observable<UsuarioPerfil> {
    this._cargandoPerfil.set(true);
    return this.authService.obtenerPerfil().pipe(
      tap({
        next: (perfil) => {
          this._usuario.set(perfil);
          this._cargandoPerfil.set(false);
        },
        error: () => {
          this._cargandoPerfil.set(false);
        },
      }),
    );
  }

  cerrarSesion(): void {
    this.limpiarStorage();
    this._usuario.set(null);
    this.router.navigate(['/login']);
  }

  obtenerToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  tokenVencido(): boolean {
    const expiraEn = localStorage.getItem(this.EXPIRES_KEY);
    if (!expiraEn) {
      return true;
    }
    return Date.now() >= Number(expiraEn);
  }

  private guardarToken(respuesta: TokenRespuesta): void {
    const expiraEn = Date.now() + respuesta.expires_in * 1000;
    localStorage.setItem(this.TOKEN_KEY, respuesta.access_token);
    localStorage.setItem(this.EXPIRES_KEY, expiraEn.toString());
    this.versionSesion.update((version) => version + 1);
  }

  private limpiarStorage(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.EXPIRES_KEY);
    this.versionSesion.update((version) => version + 1);
  }
}