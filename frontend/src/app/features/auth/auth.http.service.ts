import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import { TokenRespuesta, UsuarioPerfil } from './auth.models';
import { AuthService } from './auth.service';

@Injectable({ providedIn: 'root' })
export class AuthHttpService extends AuthService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  override login(correo: string, password: string): Observable<TokenRespuesta> {
    const body = new HttpParams()
      .set('username', correo)
      .set('password', password)
      .set('grant_type', 'password');

    const headers = new HttpHeaders({
      'Content-Type': 'application/x-www-form-urlencoded',
    });

    return this.http.post<TokenRespuesta>(`${this.baseUrl}/auth/token`, body.toString(), {
      headers,
    });
  }

  override obtenerPerfil(): Observable<UsuarioPerfil> {
    return this.http.get<UsuarioPerfil & { usuario_id: number }>(`${this.baseUrl}/auth/me`).pipe(
      map((perfil) => ({ ...perfil, id: perfil.usuario_id })),
    );
  }
}
