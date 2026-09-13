import { useState, type FormEvent } from 'react';
import { Check, LoaderCircle } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { authService, type AuthUser } from '@/services/auth-service';

type Mode = 'login' | 'register';

const demoHint = 'Demo account: demo@demo.dev · password123';

export function AuthScreen({ onAuthed }: { onAuthed: (user: AuthUser) => void }) {
  const [mode, setMode] = useState<Mode>('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (submitting || !email.trim() || !password) return;
    setError('');
    setSubmitting(true);
    try {
      const user = mode === 'login'
        ? await authService.login(email.trim(), password)
        : await authService.register(name.trim(), email.trim(), password);
      onAuthed(user);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Something went wrong.');
    } finally {
      setSubmitting(false);
    }
  };

  return <div className="grain flex min-h-[100dvh] items-center justify-center bg-background p-4 text-foreground">
    <div className="w-full max-w-[400px]">
      <div className="mb-8 flex flex-col items-center gap-3 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-sidebar-primary font-mono-ui text-lg font-bold text-sidebar-primary-foreground">N</div>
        <div>
          <p className="text-xl font-extrabold tracking-[-.03em]">Northstar</p>
          <p className="font-mono-ui text-[10px] uppercase tracking-[.18em] text-muted-foreground">Ship with context</p>
        </div>
      </div>
      <div className="rounded-3xl border border-border bg-card p-6 shadow-[0_2px_0_hsl(var(--border)/.55)]">
        <div className="mb-6 grid grid-cols-2 gap-1 rounded-xl bg-muted p-1">
          {(['login', 'register'] as const).map((value) => (
            <button key={value} type="button" data-testid={`auth-tab-${value}`} onClick={() => { setMode(value); setError(''); }} className={`rounded-lg px-3 py-2 text-xs font-bold transition ${mode === value ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground'}`}>{value === 'login' ? 'Sign in' : 'Create account'}</button>
          ))}
        </div>
        <form onSubmit={submit} className="space-y-4" data-testid="auth-form">
          {mode === 'register' && (
            <label className="block">
              <span className="mb-1.5 block text-[11px] font-bold uppercase tracking-[.12em] text-muted-foreground">Name</span>
              <input data-testid="input-auth-name" autoFocus required value={name} onChange={(event) => setName(event.target.value)} placeholder="Your name" className="h-11 w-full rounded-xl border border-input bg-background px-3.5 text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/15" />
            </label>
          )}
          <label className="block">
            <span className="mb-1.5 block text-[11px] font-bold uppercase tracking-[.12em] text-muted-foreground">Email</span>
            <input data-testid="input-auth-email" autoFocus type="email" required value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" className="h-11 w-full rounded-xl border border-input bg-background px-3.5 text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/15" />
          </label>
          <label className="block">
            <span className="mb-1.5 block text-[11px] font-bold uppercase tracking-[.12em] text-muted-foreground">Password</span>
            <input data-testid="input-auth-password" type="password" required minLength={mode === 'register' ? 8 : undefined} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="••••••••" className="h-11 w-full rounded-xl border border-input bg-background px-3.5 text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/15" />
          </label>
          {error && <p data-testid="auth-error" className="rounded-xl border border-destructive/25 bg-destructive/5 px-3 py-2 text-xs font-semibold text-destructive">{error}</p>}
          <Button type="submit" disabled={submitting} className="w-full" data-testid="button-auth-submit">
            {submitting ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
            {mode === 'login' ? 'Sign in' : 'Create account'}
          </Button>
        </form>
        <p className="mt-5 text-center text-[11px] text-muted-foreground">{demoHint}</p>
      </div>
    </div>
  </div>;
}