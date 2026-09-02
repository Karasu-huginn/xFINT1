import type { CurrentUser } from "../types/api";
import { jsonBody, requestEmpty, requestJson } from "./client";

export async function logIn(email: string, password: string): Promise<void> {
  await requestEmpty("/api/auth/login", {
    method: "POST",
    ...jsonBody({ email, password }),
  });
}

export async function logOut(): Promise<void> {
  await requestEmpty("/api/auth/logout", { method: "POST" });
}

export async function fetchCurrentUser(): Promise<CurrentUser> {
  return requestJson<CurrentUser>("/api/auth/me");
}

export async function probeActivation(token: string): Promise<{ email: string }> {
  return requestJson<{ email: string }>(
    `/api/auth/activation/${encodeURIComponent(token)}`,
  );
}

export async function activateAccount(
  token: string,
  password: string,
): Promise<void> {
  await requestEmpty("/api/auth/activate", {
    method: "POST",
    ...jsonBody({ token, password }),
  });
}
