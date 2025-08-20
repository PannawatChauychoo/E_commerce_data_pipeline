/** Assumptions
 * - Django runs at http://localhost:8000 with routes under /api/
 * - Endpoints:
 *    /api/simulate/  (POST)
 *    /api/transactions/?since=<ISO>&limit=<int>  (GET)
 *    /api/cust1/     (GET)
 *    /api/cust2/     (GET)
 *    /api/products/  (GET)
 * - If you use session auth, CSRF cookie name is "csrftoken"
 */

type JsonValue = string | number | boolean | null | JsonValue[] | { [k: string]: JsonValue };
type JsonBody = Record<string, JsonValue>;

// Getting the full API request 
const joinUrl = (base: string, path: string) =>
  `${base.replace(/\/+$/, "")}/${path.replace(/^\/+/, "")}`;

const API_ORIGIN = process.env.NEXT_PUBLIC_API_ORIGIN ?? "http://localhost:8000";
const API_PREFIX = process.env.NEXT_PUBLIC_API_PREFIX ?? "/api";
const API_BASE = joinUrl(API_ORIGIN, API_PREFIX);


// Include defined values and safely stringify them
function toQuery(params?: Record<string, string | number | undefined>) {
  const u = new URLSearchParams();
  Object.entries(params ?? {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && `${v}` !== "") u.set(k, String(v));
  });
  const s = u.toString();
  return s ? `?${s}` : "";
}

// If cookies are used, we check for CSRF token header for unsafe methods (POST/DELETE/PUT)
function getCSRFCookie(name = "csrftoken") {
  if (typeof document === "undefined") return undefined;
  const m = document.cookie.match(`(?:^|; )${name}=([^;]*)`);
  return m ? decodeURIComponent(m[1]) : undefined;
}


// Make errors readable
async function parseError(res: Response) {
  const ct = res.headers.get("content-type") || "";
  const body = ct.includes("application/json") ? await res.json().catch(() => ({})) : await res.text();
  const detail = typeof body === "string" ? body : body.detail ?? JSON.stringify(body);
  const err = new Error(`HTTP ${res.status} ${res.statusText}: ${detail}`);
  // @ts-expect-error attach for debugging
  err.status = res.status;
  // @ts-expect-error attach for debugging
  err.payload = body;
  throw err;
}

// Setting types for body and headers
type RequestOpts = Omit<RequestInit, "body" | "headers"> & {
  body?: BodyInit | JsonBody;
  headers?: HeadersInit;
};
async function apiRequest<T = unknown>(endpoint: string, opts: RequestOpts = {}): Promise<T> {

  //Setting up the headers
  const url = joinUrl(API_BASE, endpoint);
  const headers = new Headers(opts.headers);

  //Setting up the body
  let body = opts.body as BodyInit | JsonBody | undefined;
  const isJsonLike =
    body != null &&
    typeof body === "object" &&
    !(body instanceof FormData) &&
    !(body instanceof Blob) &&
    !(body instanceof URLSearchParams) &&
    !(body instanceof ArrayBuffer);  // CSRF for same-origin/session (safe to include; backend can ignore if not needed)

  if (isJsonLike) {
    if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");
    body = JSON.stringify(body as JsonBody);
  }

  const csrf = getCSRFCookie();
  if (csrf && !headers.has("X-CSRFToken")) headers.set("X-CSRFToken", csrf);

  const res = await fetch(url, {
    method: opts.method ?? (body ? "POST" : "GET"),
    credentials: opts.credentials ?? "include",
    ...opts,
    headers,
    body: body as BodyInit | undefined,
  });

  if (!res.ok) {
    await parseError(res); // throws
  }
  if (res.status === 204) return undefined as T;

  const ct = res.headers.get("content-type") || "";
  return (ct.includes("application/json") ? res.json() : res.text()) as Promise<T>;
}

/** Types to keep the callsites readable */
export type RunSimulationParams = {
  start_date: string;              // "YYYY-MM-DD" or "YYYYMMDD"
  max_steps: number;
  n_customers1: number;
  n_customers2: number;
  n_products_per_category: number;
};

const normalizeDateForAPI = (d: string) => d.replaceAll("-", ""); // DRF accepts both; we send digits.

export const simulationAPI = {
  /** GET /api/transactions/?since=&limit= */
  getTransactions: (opts?: { since?: string; limit?: number }) =>
    apiRequest(`/transactions/${toQuery(opts)}`),

  /** POST /api/simulate/ */
  runSimulation: (p: RunSimulationParams) =>
    apiRequest("/simulate/", {
      method: "POST",
      body: {
        ...p,
        start_date: normalizeDateForAPI(p.start_date),
      },
    }),

  /** GET /api/cust1/ */
  getCust1Data: () => apiRequest("/cust1/"),

  /** GET /api/cust2/ */
  getCust2Data: () => apiRequest("/cust2/"),

  /** GET /api/products/ */
  getProducts: () => apiRequest("/products/"),
};

