// Server-only route helper. Never import this from a Client Component.
export function bridgeAccess(request: Request, path: string[], config: {
  mode?: string; origin?: string; token?: string;
}): { allowed: boolean; upstreamPath?: string } {
  if (config.mode !== "private_development" || !config.origin || (config.token?.length || 0) < 32) return {allowed:false};
  let expected: URL;
  try { expected = new URL(config.origin); } catch { return {allowed:false}; }
  if (expected.protocol !== "http:" || expected.hostname !== "127.0.0.1" || !expected.port) return {allowed:false};
  if (request.headers.get("host") !== expected.host) return {allowed:false};
  const origin = request.headers.get("origin");
  if ((origin && origin !== expected.origin) || (request.method === "POST" && origin !== expected.origin)) return {allowed:false};
  const fetchSite = request.headers.get("sec-fetch-site");
  if (fetchSite && !["same-origin", "none"].includes(fetchSite)) return {allowed:false};
  const route = path.join("/");
  const uuid = "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}";
  const permitted = request.method === "POST"
    ? /^v1\/(session|timeline|onboarding|chat|plan)$/.test(route)
    : request.method === "GET" && new RegExp(`^v1/(session|home|plans)/${uuid}$`).test(route);
  return permitted ? {allowed:true, upstreamPath:`/${route}`} : {allowed:false};
}
/** Keep the private session cookie scoped to the browser-facing API path. */
export function bridgeSessionCookie(cookie: string): string | null {
  if (!cookie.startsWith("maya_session=")) return null;
  return cookie.replace(/;\s*Path=\/v1(?=;|$)/i, "; Path=/api/maya/v1");
}
