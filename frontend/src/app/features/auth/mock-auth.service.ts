import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, of } from 'rxjs';
import { TokenRespuesta, UsuarioPerfil } from './auth.models';
import { AuthService } from './auth.service';

@Injectable({ providedIn: 'root' })
export class MockAuthService extends AuthService {
  private readonly http = inject(HttpClient);

  override login(): Observable<TokenRespuesta> {
    return of({
      access_token: 'mock-jwt-token-demo',
      token_type: 'bearer',
      expires_in: 86400,
    });
  }

  override obtenerPerfil(): Observable<UsuarioPerfil> {
    return this.http.get<UsuarioPerfil>('/mock/auth-me.json');
  }
}