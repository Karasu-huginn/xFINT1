import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, requestEmpty, requestJson } from "./client";

function stubFetch(response: Response): void {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("requestJson", () => {
  it("returns the parsed body on success", async () => {
    stubFetch(
      new Response(JSON.stringify({ id: 1 }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(requestJson<{ id: number }>("/api/thing")).resolves.toEqual({
      id: 1,
    });
  });

  it("sends cookies so the httpOnly session travels with the call", async () => {
    const fetchSpy = vi.fn().mockResolvedValue(new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", fetchSpy);

    await requestJson("/api/thing");

    expect(fetchSpy.mock.calls[0][1]).toMatchObject({ credentials: "include" });
  });

  it("raises an ApiError carrying the envelope detail and code", async () => {
    stubFetch(
      new Response(JSON.stringify({ detail: "Déjà pris", code: "conflict" }), {
        status: 409,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(requestJson("/api/thing")).rejects.toMatchObject({
      status: 409,
      code: "conflict",
      message: "Déjà pris",
    });
  });

  it("still raises an ApiError when the body is not the envelope", async () => {
    stubFetch(new Response("<html>502</html>", { status: 502 }));

    const failure: unknown = await requestJson("/api/thing").catch(
      (error: unknown) => error,
    );

    expect(failure).toBeInstanceOf(ApiError);
    // Narrowing rather than casting, so the test fails loudly if the rejection
    // stops being an ApiError instead of silently reading undefined properties.
    if (!(failure instanceof ApiError)) {
      throw new Error("expected the rejection to be an ApiError");
    }
    expect(failure.status).toBe(502);
    expect(failure.message.length).toBeGreaterThan(0);
  });
});

describe("requestEmpty", () => {
  it("resolves on a 204 with no body to parse", async () => {
    stubFetch(new Response(null, { status: 204 }));

    await expect(
      requestEmpty("/api/auth/logout", { method: "POST" }),
    ).resolves.toBeUndefined();
  });
});
