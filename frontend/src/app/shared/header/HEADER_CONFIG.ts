import { ROLES_LECTURA_PLANTA } from '../../core/auth/roles.guard';

/** Cada módulo indica qué roles lo ven; sin `roles`, lo ven todos. */
export const HEADER_CONFIG = {
  brand: {
    name: 'TCI · Mantenimiento de planta',
    homeUrl: '/',
  },
  navigation: [
    { label: 'Inicio', href: '/inicio' },
    { label: 'Máquinas', href: '/maquinas', roles: ROLES_LECTURA_PLANTA },
    { label: 'Repuestos', href: '/stock', roles: ROLES_LECTURA_PLANTA },
    { label: 'Ubicaciones', href: '/ubicaciones', roles: ROLES_LECTURA_PLANTA },
    { label: 'Reposición', href: '/reposicion', roles: ROLES_LECTURA_PLANTA },
    { label: 'Compras', href: '/compras', roles: ROLES_LECTURA_PLANTA },
  ] as { label: string; href: string; roles?: string[] }[],
};
