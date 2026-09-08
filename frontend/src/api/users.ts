import type { InvitedUser, Role } from "../types/api";
import { jsonBody, requestJson } from "./client";

export async function createUser(email: string, role: Role): Promise<InvitedUser> {
  return requestJson<InvitedUser>("/api/users", {
    method: "POST",
    ...jsonBody({ email, role }),
  });
}

export function buildActivationUrl(token: string): string {
  // The API returns the raw token and not a link, because it has no idea what
  // origin the frontend is served from. The frontend does, so it builds the URL.
  return `${window.location.origin}/activate?token=${encodeURIComponent(token)}`;
}
