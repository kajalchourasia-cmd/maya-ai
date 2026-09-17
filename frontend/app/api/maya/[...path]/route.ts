import { bridgeAccess, bridgeSessionCookie } from "@/lib/local-api-bridge";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

async function proxy(request: Request, context: {params: Promise<{path: string[]}>}) {
  const {path} = await context.params;
  const token = process.env.MAYA_OPERATOR_TOKEN;
  const access = bridgeAccess(request, path, {
    mode: process.env.MAYA_RUNTIME_MODE, origin: process.env.MAYA_LOCAL_UI_ORIGIN, token,
  });
  const headers = {"Cache-Control":"no-store", "Vary":"Cookie", "X-Content-Type-Options":"nosniff"};
  if (!access.allowed) return Response.json({code:"local_access_required", detail:"This connection is available only in the explicitly started private local UI."}, {status:403, headers});
  let body: string | undefined;
  if (request.method === "POST") {
    if (!request.headers.get("content-type")?.startsWith("application/json")) return Response.json({detail:"JSON required"},{status:415,headers});
    body = await request.text();
    if (new TextEncoder().encode(body).length > 65536) return Response.json({detail:"Request too large"},{status:413,headers});
  }
  try {
    // Fixed loopback target: no arbitrary host/path forwarding or client token.
    const upstream = await fetch(`http://127.0.0.1:8000${access.upstreamPath}`, {
      method: request.method, body, cache:"no-store", redirect:"error",
      headers: {"Content-Type":"application/json", "X-Maya-Operator":token!,
        "Cookie":request.headers.get("cookie") || "", "Origin":process.env.MAYA_LOCAL_UI_ORIGIN!},
      signal: AbortSignal.timeout(180000),
    });
    const response = new Response(upstream.body, {status:upstream.status, headers:{...headers,"Content-Type":"application/json"}});
    for (const cookie of upstream.headers.getSetCookie()) {
      const scoped = bridgeSessionCookie(cookie);
      if (scoped) response.headers.append("Set-Cookie",scoped);
    }
    return response;
  } catch {
    return Response.json({code:"local_backend_unavailable",detail:"Maya could not reach the local backend or the request timed out. Check the local services and retry; no sample answer was substituted."},{status:502,headers});
  }
}

export const GET = proxy;
export const POST = proxy;
