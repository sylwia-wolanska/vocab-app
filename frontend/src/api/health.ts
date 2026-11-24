import { api } from "./client";

export async function fetchHealth(): Promise<Record<string, string>> {
  const { data, response } = await api.GET("/api/v1/health");
  if (!response.ok || data === undefined) {
    throw new Error(`Health check failed with status ${response.status}`);
  }
  return data;
}
