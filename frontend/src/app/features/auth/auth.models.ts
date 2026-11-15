export type RolUsuario =
  | 'OPERARIO'
  | 'EMPLEADO_MANTENIMIENTO'
  | 'ENCARGADO_MANTENIMIENTO'
  | 'GERENCIA_ADMINISTRACION';

export interface UsuarioPerfil {
  id: number | string;
  correo: string;
  nombre: string;
  roles: string[];
  esDemo?: boolean;
}

export interface TokenRespuesta {
  access_token: string;
  token_type: string;
  expires_in: number;
}