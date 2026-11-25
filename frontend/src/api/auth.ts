import { api } from "./client";
import { ApiError } from "./errors";

export async function login(email: string, password: string): Promise<string> {
  const { data, response } = await api.POST("/api/v1/auth/token", {
    body: { username: email, password, scope: "" },
    bodySerializer: (body) =>
      new URLSearchParams({ username: body.username, password: body.password }),
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  if (response.status === 401) {
    throw new ApiError("Incorrect email or password", 401);
  }
  if (!response.ok || data === undefined) {
    throw new ApiError("Could not log in, please try again", response.status);
  }
  return data.access_token;
}

export async function register(email: string, password: string): Promise<void> {
  const { response } = await api.POST("/api/v1/auth/register", {
    body: { email, password },
  });
  if (response.status === 409) {
    throw new ApiError("This email is already registered", 409);
  }
  if (!response.ok) {
    throw new ApiError("Could not create the account", response.status);
  }
}

export async function getMe() {
  const { data, response } = await api.GET("/api/v1/auth/me");
  if (!response.ok || data === undefined) {
    throw new ApiError("Could not load your account", response.status);
  }
  return data;
}
