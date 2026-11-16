export interface TokenRespuesta {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface UsuarioPerfil {
  usuario_id: number;
  correo: string;
  nombre?: string;
  apellido?: string;
  roles: string[];
  esDemo?: boolean;
}