import { customFetch, setAuthTokenGetter } from '@/lib/api-client';

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  createdAt: string;
  updatedAt: string;
}

export interface AuthSession {
  token: string;
  user: AuthUser;
}

const TOKEN_KEY = 'northstar-token';

function readStoredToken(): string | null {
  return globalThis.localStorage?.getItem(TOKEN_KEY) ?? null;
}

setAuthTokenGetter(() => readStoredToken());

function persistSession({ token, user }: AuthSession): AuthUser {
  globalThis.localStorage?.setItem(TOKEN_KEY, token);
  return user;
}

function clearSession(): void {
  globalThis.localStorage?.removeItem(TOKEN_KEY);
}

export const authService = {
  async login(email: string, password: string): Promise<AuthUser> {
    const session = await customFetch<AuthSession>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    return persistSession(session);
  },

  async register(name: string, email: string, password: string): Promise<AuthUser> {
    const session = await customFetch<AuthSession>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    });
    return persistSession(session);
  },

  async restore(): Promise<AuthUser | null> {
    if (!readStoredToken()) return null;
    try {
      return await customFetch<AuthUser>('/api/me');
    } catch {
      clearSession();
      return null;
    }
  },

  async logout(): Promise<void> {
    try {
      await customFetch<void>('/api/auth/logout', { method: 'POST', responseType: 'text' });
    } catch {
      // Local logout still proceeds if the server call fails.
    }
    clearSession();
  },
};