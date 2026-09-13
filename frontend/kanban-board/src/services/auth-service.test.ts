import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { customFetch } from '@/lib/api-client';
import { authService, type AuthUser } from './auth-service';

const TOKEN_KEY = 'northstar-token';
const token = 'jwt-token';

const user: AuthUser = {
  id: 'u1',
  name: 'Demo User',
  email: 'demo@demo.dev',
  createdAt: '2026-01-01T00:00:00Z',
  updatedAt: '2026-01-01T00:00:00Z',
};

interface CapturedRequest {
  url: string;
  method: string;
  headers: Record<string, string>;
  body: unknown;
}

function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });
}

let storage: Storage;
let requests: CapturedRequest[];

beforeEach(() => {
  const map = new Map<string, string>();
  storage = {
    getItem: (key) => map.get(key) ?? null,
    setItem: (key, value) => { map.set(key, String(value)); },
    removeItem: (key) => { map.delete(key); },
    clear: () => { map.clear(); },
    key: (index) => Array.from(map.keys())[index] ?? null,
    get length() { return map.size; },
  } as Storage;
  Object.defineProperty(globalThis, 'localStorage', { value: storage, configurable: true, writable: true });

  requests = [];
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === 'string' ? input : input.url;
    const method = init?.method ?? 'GET';
    const headers = Object.fromEntries(new Headers(init?.headers).entries());
    let body: unknown;
    if (typeof init?.body === 'string' && init.body) {
      try { body = JSON.parse(init.body); } catch { body = init.body; }
    }
    requests.push({ url, method, headers, body });
    return respond(url, method);
  });
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

type Route = {
  method: string;
  url: string;
  json?: unknown;
  status?: number;
};

let routes: Route[];

function route(method: string, url: string, response: { json?: unknown; status?: number } = {}) {
  routes.push({ method, url, ...response });
}

function respond(url: string, method: string): Response {
  const hit = routes.find((item) => item.method === method && item.url === url);
  if (!hit) return jsonResponse({ detail: 'Unmocked request' }, 404);
  if (hit.status === 204) return new Response(null, { status: 204 });
  return jsonResponse(hit.json, hit.status ?? 200);
}

describe('authService', () => {
  it('logs in, persists the token, and attaches it to later requests', async () => {
    routes = [
      { method: 'POST', url: '/api/auth/login', json: { token, user } },
      { method: 'GET', url: '/api/me', json: user },
    ];

    const loggedIn = await authService.login('demo@demo.dev', 'password123');

    expect(loggedIn).toEqual(user);
    expect(requests[0].body).toEqual({ email: 'demo@demo.dev', password: 'password123' });
    expect(storage.getItem(TOKEN_KEY)).toBe(token);

    await customFetch<AuthUser>('/api/me');
    expect(requests[1].headers.authorization).toBe(`Bearer ${token}`);
  });

  it('registers a new account and stores the returned session', async () => {
    routes = [{ method: 'POST', url: '/api/auth/register', json: { token, user } }];

    const registered = await authService.register('Demo User', 'demo@demo.dev', 'password123');

    expect(registered).toEqual(user);
    expect(requests[0].body).toEqual({ name: 'Demo User', email: 'demo@demo.dev', password: 'password123' });
    expect(storage.getItem(TOKEN_KEY)).toBe(token);
  });

  it('restores the session when a stored token is still valid', async () => {
    routes = [
      { method: 'GET', url: '/api/me', json: user },
    ];
    storage.setItem(TOKEN_KEY, token);

    await expect(authService.restore()).resolves.toEqual(user);
    expect(requests[0].headers.authorization).toBe(`Bearer ${token}`);
  });

  it('clears an invalid stored token when the session cannot be restored', async () => {
    routes = [{ method: 'GET', url: '/api/me', status: 401, json: { detail: 'Invalid token' } }];
    storage.setItem(TOKEN_KEY, token);

    await expect(authService.restore()).resolves.toBeNull();
    expect(storage.getItem(TOKEN_KEY)).toBeNull();
  });

  it('logs out on the server and clears the local token', async () => {
    routes = [{ method: 'POST', url: '/api/auth/logout', status: 204 }];
    storage.setItem(TOKEN_KEY, token);

    await authService.logout();
    expect(requests[0].url).toBe('/api/auth/logout');
    expect(storage.getItem(TOKEN_KEY)).toBeNull();
  });
});