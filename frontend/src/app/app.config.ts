import { ApplicationConfig, inject, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { provideIcons } from '@ng-icons/core';

import { environment } from '../environments/environment';
import { routes } from './app.routes';
import { authInterceptor } from './core/auth/auth.interceptor';
import { AuthHttpService } from './features/auth/auth.http.service';
import { AuthService } from './features/auth/auth.service';
import { MockAuthService } from './features/auth/mock-auth.service';
import { UI_ICON_SET } from './shared/ui/icon';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(withInterceptors([authInterceptor])),
    provideIcons(UI_ICON_SET),
    {
      provide: AuthService,
      useFactory: () =>
        environment.useMockData ? inject(MockAuthService) : inject(AuthHttpService),
    },
  ],
};