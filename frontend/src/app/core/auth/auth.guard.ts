import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { SessionService } from './session.service';

export const authGuard: CanActivateFn = () => {
  const sessionService = inject(SessionService);
  const router = inject(Router);

  if (sessionService.estaAutenticado()) {
    return true;
  }

  sessionService.cerrarSesion();
  return router.createUrlTree(['/login']);
};

export const guestGuard: CanActivateFn = () => {
  const sessionService = inject(SessionService);
  const router = inject(Router);

  if (sessionService.estaAutenticado()) {
    return router.createUrlTree(['/inicio']);
  }

  return true;
};