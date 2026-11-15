import { baseEnvironment } from "./environment.base";

export const environment = {
  ...baseEnvironment,
  apiUrl: "http://localhost:8300",
  useMockData: false,
  production: false
};
