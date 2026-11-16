import { Observable } from 'rxjs';
import { TokenRespuesta, UsuarioPerfil } from './auth.models';

export abstract class AuthService {
  abstract login(correo: string, password: string): Observable<TokenRespuesta>;
  abstract obtenerPerfil(): Observable<UsuarioPerfil>;
}