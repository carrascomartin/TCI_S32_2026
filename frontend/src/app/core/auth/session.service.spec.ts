import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { AuthService } from '../../features/auth/auth.service';
import { SessionService } from './session.service';

describe('SessionService', () => {
  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        {
          provide: AuthService,
          useValue: {
            login: () => of({ access_token: 'prueba', token_type: 'bearer', expires_in: 60 }),
            obtenerPerfil: () => of({
              id: 1, correo: 'demo@example.invalid', nombre: 'Demo',
              roles: ['encargado_mantenimiento'],
            }),
          },
        },
      ],
    });
  });

  it('actualiza el estado de sesión al iniciar y cerrar sesión', () => {
    const sesion = TestBed.inject(SessionService);
    expect(sesion.estaAutenticado()).toBe(false);
    sesion.iniciarSesion('demo@example.invalid', 'clave').subscribe();
    expect(sesion.estaAutenticado()).toBe(true);
    expect(sesion.roles()).toContain('encargado_mantenimiento');
    sesion.cerrarSesion();
    expect(sesion.estaAutenticado()).toBe(false);
  });

  it('recupera el perfil al iniciar con un token vigente', async () => {
    localStorage.setItem('tci_auth_token', 'prueba');
    localStorage.setItem('tci_auth_expires_at', String(Date.now() + 60000));
    const sesion = TestBed.inject(SessionService);
    await Promise.resolve();
    expect(sesion.estaAutenticado()).toBe(true);
    expect(sesion.roles()).toContain('encargado_mantenimiento');
  });
});
