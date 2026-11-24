import createClient, { type Middleware } from "openapi-fetch";

import type { paths } from "./schema";

const TOKEN_KEY = "vocab.token";

export const tokenStorage = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

let handleUnauthorized = () => {};

export function setUnauthorizedHandler(handler: () => void) {
  handleUnauthorized = handler;
}

const authMiddleware: Middleware = {
  onRequest({ request }) {
    const token = tokenStorage.get();
    if (token) {
      request.headers.set("Authorization", `Bearer ${token}`);
    }
    return request;
  },
  onResponse({ request, response }) {
    if (response.status === 401 && request.headers.has("Authorization")) {
      handleUnauthorized();
    }
    return response;
  },
};

export const api = createClient<paths>({
  baseUrl: import.meta.env.VITE_API_URL,
});

api.use(authMiddleware);
