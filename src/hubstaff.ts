import { promises as fs } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

/**
 * Minimal Hubstaff REST API v2 client.
 *
 * Authentication uses Hubstaff's OAuth2 refresh-token flow. You generate a
 * "Personal Access Token" (which is a long-lived refresh token) from
 * https://developer.hubstaff.com/personal_access_tokens and provide it via the
 * HUBSTAFF_REFRESH_TOKEN environment variable.
 *
 * The refresh token rotates on every exchange, so the newest one is persisted
 * to disk (default: ~/.hubstify-mcp/token.json) and reused on subsequent runs.
 */

const ACCOUNTS_BASE = "https://account.hubstaff.com";
const API_BASE = "https://api.hubstaff.com/v2";

interface TokenState {
  refreshToken: string;
  accessToken?: string;
  /** epoch ms when the access token expires */
  expiresAt?: number;
}

export interface HubstaffClientOptions {
  refreshToken: string;
  tokenStorePath?: string;
}

export class HubstaffError extends Error {
  status: number;
  body: unknown;
  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.name = "HubstaffError";
    this.status = status;
    this.body = body;
  }
}

export class HubstaffClient {
  private state: TokenState;
  private storePath: string;
  private loaded = false;

  constructor(opts: HubstaffClientOptions) {
    this.state = { refreshToken: opts.refreshToken };
    this.storePath =
      opts.tokenStorePath ??
      join(homedir(), ".hubstify-mcp", "token.json");
  }

  /** Load any previously persisted (rotated) refresh token from disk. */
  private async loadState(): Promise<void> {
    if (this.loaded) return;
    this.loaded = true;
    try {
      const raw = await fs.readFile(this.storePath, "utf8");
      const saved = JSON.parse(raw) as TokenState;
      // Only trust the persisted token; keep using it across restarts.
      if (saved.refreshToken) {
        this.state = { ...this.state, ...saved };
      }
    } catch {
      // No persisted state yet — fall back to the env-provided token.
    }
  }

  private async persistState(): Promise<void> {
    try {
      await fs.mkdir(join(this.storePath, ".."), { recursive: true });
      await fs.writeFile(this.storePath, JSON.stringify(this.state, null, 2), {
        mode: 0o600,
      });
    } catch {
      // Persistence is best-effort; the server still works for this session.
    }
  }

  /** Exchange the current refresh token for a fresh access token. */
  private async refreshAccessToken(): Promise<void> {
    const params = new URLSearchParams({
      grant_type: "refresh_token",
      refresh_token: this.state.refreshToken,
    });

    const res = await fetch(`${ACCOUNTS_BASE}/access_tokens`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: params.toString(),
    });

    const data = (await res.json().catch(() => ({}))) as Record<string, any>;
    if (!res.ok) {
      throw new HubstaffError(
        `Failed to refresh Hubstaff access token: ${
          data.error_description || data.error || res.statusText
        }`,
        res.status,
        data
      );
    }

    this.state.accessToken = data.access_token;
    // Hubstaff rotates the refresh token on each exchange.
    if (data.refresh_token) this.state.refreshToken = data.refresh_token;
    const expiresIn = Number(data.expires_in ?? 86400);
    // Refresh a minute early to avoid edge-of-expiry races.
    this.state.expiresAt = Date.now() + (expiresIn - 60) * 1000;
    await this.persistState();
  }

  private async ensureAccessToken(): Promise<string> {
    await this.loadState();
    if (
      !this.state.accessToken ||
      !this.state.expiresAt ||
      Date.now() >= this.state.expiresAt
    ) {
      await this.refreshAccessToken();
    }
    return this.state.accessToken!;
  }

  /** Perform an authenticated request against the Hubstaff v2 API. */
  async request<T = any>(
    path: string,
    init: { method?: string; query?: Record<string, unknown>; body?: unknown } = {}
  ): Promise<T> {
    const url = new URL(`${API_BASE}${path.startsWith("/") ? path : `/${path}`}`);
    if (init.query) {
      for (const [key, value] of Object.entries(init.query)) {
        if (value === undefined || value === null || value === "") continue;
        if (Array.isArray(value)) {
          for (const v of value) url.searchParams.append(key, String(v));
        } else {
          url.searchParams.set(key, String(value));
        }
      }
    }

    const doFetch = async (token: string) =>
      fetch(url.toString(), {
        method: init.method ?? "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "application/json",
          ...(init.body ? { "Content-Type": "application/json" } : {}),
        },
        body: init.body ? JSON.stringify(init.body) : undefined,
      });

    let token = await this.ensureAccessToken();
    let res = await doFetch(token);

    // Access token may have been revoked/expired server-side — retry once.
    if (res.status === 401) {
      await this.refreshAccessToken();
      token = this.state.accessToken!;
      res = await doFetch(token);
    }

    const text = await res.text();
    const data = text ? safeJson(text) : null;
    if (!res.ok) {
      throw new HubstaffError(
        `Hubstaff API ${res.status} on ${init.method ?? "GET"} ${path}`,
        res.status,
        data ?? text
      );
    }
    return data as T;
  }
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}
