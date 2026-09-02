export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

const GENERIC_FAILURE_MESSAGE = "Une erreur est survenue, merci de réessayer.";

async function readErrorEnvelope(response: Response): Promise<ApiError> {
  // A 502 from a proxy or a crash outside the handler chain returns HTML, not the
  // envelope, so parsing has to be allowed to fail without masking the real status.
  try {
    const body = await response.json();
    return new ApiError(
      response.status,
      typeof body.code === "string" ? body.code : "error",
      typeof body.detail === "string" ? body.detail : GENERIC_FAILURE_MESSAGE,
    );
  } catch {
    return new ApiError(response.status, "error", GENERIC_FAILURE_MESSAGE);
  }
}

async function send(path: string, options: RequestInit = {}): Promise<Response> {
  // The session lives in an httpOnly cookie, so it only travels when credentials
  // are included; script cannot attach it by hand.
  const response = await fetch(path, { credentials: "include", ...options });
  if (!response.ok) {
    throw await readErrorEnvelope(response);
  }
  return response;
}

export async function requestJson<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await send(path, options);
  return (await response.json()) as T;
}

export async function requestEmpty(
  path: string,
  options: RequestInit = {},
): Promise<void> {
  await send(path, options);
}

export function jsonBody(payload: unknown): RequestInit {
  return {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  };
}
