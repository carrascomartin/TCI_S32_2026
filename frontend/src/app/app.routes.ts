import { inject } from '@angular/core';
import { Routes } from '@angular/router';
import { environment } from '../environments/environment';
import { authGuard } from './core/auth/auth.guard';
import { InicioHttpService } from './features/inicio/inicio.http.service';
import { InicioService } from './features/inicio/inicio.service';
import { MockInicioService } from './features/inicio/mock-inicio.service';
import { MockRepuestosService } from './features/repuestos/mock-repuestos.service';
import { RepuestosHttpService } from './features/repuestos/repuestos.http.service';
import { RepuestosService } from './features/repuestos/repuestos.service';
import { MaquinasHttpService } from './features/maquinas/maquinas.http.service';
import { MockMaquinasService } from './features/maquinas/mock-maquinas.service';
import { MaquinasService } from './features/maquinas/maquinas.service';

export const routes: Routes = [
  {
    path: 'login',
    title: 'Iniciar sesión · TCI',
    loadComponent: () => import('./features/auth/login.page').then((page) => page.LoginPage),
  },

  {
    path: '',
    canActivate: [authGuard],
    children: [
      {
        path: '',
        pathMatch: 'full',
        redirectTo: 'inicio',
      },

      {
        path: 'inicio',
        title: 'Inicio · TCI',
        providers: [
          {
            provide: InicioService,
            useFactory: () =>
              environment.useMockData ? inject(MockInicioService) : inject(InicioHttpService),
          },
        ],
        loadComponent: () =>
          import('./features/inicio/inicio.page').then((page) => page.InicioPage),
      },

      {
        path: 'stock',
        providers: [
          {
            provide: RepuestosService,
            useFactory: () =>
              environment.useMockData
                ? inject(MockRepuestosService)
                : inject(RepuestosHttpService),
          },
        ],
        children: [
          {
            path: '',
            title: 'Repuestos · TCI',
            loadComponent: () =>
              import('./features/repuestos/repuestos.page').then((page) => page.RepuestosPage),
          },
          {
            path: 'nuevo',
            title: 'Nuevo repuesto · TCI',
            loadComponent: () =>
              import('./features/repuestos/repuesto-form.page').then((page) => page.RepuestoFormPage),
          },
          {
            path: ':id/editar',
            title: 'Editar repuesto · TCI',
            loadComponent: () =>
              import('./features/repuestos/repuesto-form.page').then((page) => page.RepuestoFormPage),
          },
          {
            path: ':id',
            title: 'Detalle de repuesto · TCI',
            loadComponent: () =>
              import('./features/repuestos/repuesto-detalle.page').then(
                (page) => page.RepuestoDetallePage,
              ),
          },
        ],
      },

      {
        path: 'ubicaciones',
        title: 'Ubicaciones · TCI',
        providers: [
          {
            provide: RepuestosService,
            useFactory: () =>
              environment.useMockData
                ? inject(MockRepuestosService)
                : inject(RepuestosHttpService),
          },
        ],
        loadComponent: () =>
          import('./features/repuestos/ubicaciones.page').then((page) => page.UbicacionesPage),
      },

      {
        path: 'reposicion',
        providers: [
          {
            provide: RepuestosService,
            useFactory: () =>
              environment.useMockData
                ? inject(MockRepuestosService)
                : inject(RepuestosHttpService),
          },
        ],
        loadComponent: () =>
          import('./features/reposicion-repuestos/reposicion-repuestos.page').then(
            (page) => page.ReposicionRepuestosPage,
          ),
      },

      {
        path: 'compras',
        providers: [
          {
            provide: RepuestosService,
            useFactory: () =>
              environment.useMockData
                ? inject(MockRepuestosService)
                : inject(RepuestosHttpService),
          },
        ],
        loadComponent: () =>
          import('./features/compras/compras.page').then((page) => page.ComprasPage),
      },

      {
        path: 'maquinas',
        providers: [
          {
            provide: MaquinasService,
            useFactory: () =>
              environment.useMockData
                ? inject(MockMaquinasService)
                : inject(MaquinasHttpService),
          },
        ],
        children: [
          {
            path: '',
            title: 'Máquinas · TCI',
            loadComponent: () =>
              import('./features/maquinas/maquinas.page').then((page) => page.MaquinasPage),
          },
          {
            path: ':id',
            title: 'Detalle de máquina · TCI',
            loadComponent: () =>
              import('./features/maquinas/maquina-detalle.page').then(
                (page) => page.MaquinaDetallePage,
              ),
          },
        ],
      },
    ],
  },

  {
    path: '**',
    title: 'Pantalla en desarrollo · TCI',
    loadComponent: () =>
      import('./features/en-desarrollo/en-desarrollo.page').then(
        (page) => page.EnDesarrolloPage,
      ),
  },
];