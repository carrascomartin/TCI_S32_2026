import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';

import { App } from './app';
import { AuthService } from './features/auth/auth.service';

describe('Aplicación', () => {
  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [
        provideHttpClient(),
        provideRouter([]),
        {
          provide: AuthService,
          useValue: {
            login: () => of({ access_token: 'token', token_type: 'bearer', expires_in: 60 }),
            obtenerPerfil: () => of({ id: 1, correo: 'demo@example.invalid', nombre: 'Demo', roles: [] }),
          },
        },
      ],
    }).compileComponents();
  });

  it('crea la aplicación y muestra el pie del sistema', async () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    await fixture.whenStable();
    expect(fixture.componentInstance).toBeTruthy();
    expect(fixture.nativeElement.textContent).toContain('TCI');
  });
});
