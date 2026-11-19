import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterLink } from '@angular/router';
import { HlmBadgeImports } from '@shared/ui/badge';
import { HlmButtonImports } from '@shared/ui/button';
import { filter, map, startWith } from 'rxjs';
import { tieneAlgunRol } from '../../core/auth/roles.guard';
import { SessionService } from '../../core/auth/session.service';
import { HEADER_CONFIG } from './HEADER_CONFIG';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [RouterLink, HlmBadgeImports, HlmButtonImports],
  templateUrl: './header.component.html',
  styleUrl: './header.component.css',
})
export class HeaderComponent {
  private readonly sessionService = inject(SessionService);
  private readonly router = inject(Router);

  protected readonly config = HEADER_CONFIG;
  protected readonly isMenuOpen = signal(false);
  protected readonly usuario = this.sessionService.usuario;
  protected readonly nombreMostrar = this.sessionService.nombreMostrar;
  protected readonly esModoMock = this.sessionService.esModoMock;

  /** Solo los módulos que el rol de la persona puede usar. */
  protected readonly navegacion = computed(() =>
    this.config.navigation.filter(
      (item) => !item.roles || tieneAlgunRol(this.sessionService.roles(), item.roles),
    ),
  );

  private readonly urlActual = toSignal(
    this.router.events.pipe(
      filter((event): event is NavigationEnd => event instanceof NavigationEnd),
      map(() => this.router.url),
      startWith(this.router.url),
    ),
    { initialValue: this.router.url },
  );

  protected readonly esPantallaLogin = computed(() => this.urlActual().startsWith('/login'));

  protected readonly mostrarNavegacion = computed(
    () => this.sessionService.estaAutenticado() && !this.esPantallaLogin(),
  );

  protected toggleMenu(): void {
    this.isMenuOpen.update((current) => !current);
  }

  protected closeMenu(): void {
    this.isMenuOpen.set(false);
  }

  protected cerrarSesion(): void {
    this.closeMenu();
    this.sessionService.cerrarSesion();
  }
}
