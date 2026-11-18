import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { environment } from '../../../environments/environment';
import { SessionService } from './session.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const sessionService = inject(SessionService);

  if (environment.useMockData) {
    return next(req);
  }

  const esLogin = req.url.includes('/auth/token');
  const token = sessionService.obtenerToken();
  const destino = new URL(req.url, window.location.origin);
  const api = new URL(environment.apiUrl || window.location.origin, window.location.origin);
  const esApi = destino.origin === api.origin &&
    (destino.pathname.startsWith('/api/') || destino.pathname.startsWith('/auth/'));

  const authReq =
    token && !esLogin && esApi
      ? req.clone({
          setHeaders: {
            Authorization: `Bearer ${token}`,
          },
        })
      : req;

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 401 && !esLogin && esApi) {
        sessionService.cerrarSesion();
      }
      return throwError(() => error);
    }),
  );
};
