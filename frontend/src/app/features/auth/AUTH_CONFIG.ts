export const AUTH_CONFIG = {
  eyebrow: 'ACCESO AL SISTEMA · TCI',
  title: 'Iniciar sesión',
  subtitle: 'Ingresá tus credenciales para acceder a la gestión de mantenimiento.',
  fields: {
    email: {
      label: 'Correo electrónico',
      placeholder: 'usuario@planta.local',
      requiredError: 'El correo electrónico es obligatorio.',
      invalidError: 'Ingresá un correo electrónico válido.',
    },
    password: {
      label: 'Contraseña',
      placeholder: '••••••••',
      requiredError: 'La contraseña es obligatoria.',
    },
  },
  actions: {
    submit: 'Ingresar',
    submitting: 'Verificando...',
  },
  errors: {
    invalidCredentials: 'Correo o contraseña incorrectos.',
    serverError: 'No se pudo conectar con el servidor. Intentá nuevamente.',
  },
  mockNotice: 'Modo demostración activo: navegás sin backend con un usuario de prueba.',
} as const;