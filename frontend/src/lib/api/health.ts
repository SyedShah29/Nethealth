import { apiGet } from "./client";

export type ApiHealth = {
  status: "healthy";
  service: string;
};

export function getApiHealth(signal?: AbortSignal): Promise<ApiHealth> {
  return apiGet<ApiHealth>("/health", signal);
}
