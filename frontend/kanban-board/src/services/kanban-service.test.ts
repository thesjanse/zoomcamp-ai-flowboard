import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  kanbanService,
  type BoardSnapshot,
  type Card,
  type Comment,
  type Member,
  type Project,
} from './kanban-service';

const allFilters = {
  search: '',
  priorities: [],
  assigneeId: null,
  due: 'all' as const,
};

const members: Member[] = [
  { id: 'u1', name: 'Demo User', initials: 'DU', color: '#5f8f77', role: 'admin' },
  { id: 'u2', name: 'Mara Chen', initials: 'MC', color: '#db805e', role: 'admin' },
];

const project = (id: string, name: string, key: string, archived: boolean): Project => ({
  id, name, key, description: `${name} description`, color: '#5f8f77', icon: key[0],
  archived, updatedAt: '2026-01-01T00:00:00Z', members,
});

const card = (id: string, columnId: string, title: string, priority: Card['priority'], assigneeId: string | null): Card => ({
  id, projectId: 'p1', columnId, title, description: `${title} context`, priority,
  assigneeId, dueDate: null, labels: ['Test'], createdAt: '2026-01-01T00:00:00Z',
  updatedAt: '2026-01-02T00:00:00Z', blockedBy: [], blocking: [], commentCount: 0,
});

interface CapturedRequest {
  url: string;
  method: string;
  headers: Record<string, string>;
  body: unknown;
}

type Route = {
  method: string;
  match: (url: string, body?: unknown) => boolean;
  json?: unknown;
  status?: number;
};

const jsonResponse = (data: unknown, status = 200): Response =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

let routes: Route[];
let requests: CapturedRequest[];

function route(method: string, match: (url: string, body?: unknown) => boolean, response: { json?: unknown; status?: number } = {}) {
  routes.push({ method, match, ...response });
}

function respond(url: string, method: string, body?: unknown): Response {
  const hit = routes.find((item) => item.method === method && item.match(url, body));
  if (!hit) return jsonResponse({ detail: 'Unmocked request' }, 404);
  if (hit.status === 204) return new Response(null, { status: 204 });
  return jsonResponse(hit.json, hit.status ?? 200);
}

beforeEach(() => {
  routes = [];
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
    return respond(url, method, body);
  });
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('kanbanService', () => {
  it('lists projects through the API, including archived ones', async () => {
    route('GET', (url) => url === '/api/projects?includeArchived=true', {
      json: [project('p1', 'Northstar', 'NST', false), project('p3', 'Orbit / archive', 'ORB', true)],
    });

    const projects = await kanbanService.listProjects();

    expect(requests[0].method).toBe('GET');
    expect(requests[0].url).toBe('/api/projects?includeArchived=true');
    expect(projects).toHaveLength(2);
    expect(projects.find((item) => item.id === 'p1')?.archived).toBe(false);
    expect(projects.find((item) => item.id === 'p3')?.archived).toBe(true);
  });

  it('filters the board via query parameters and decodes the snapshot', async () => {
    const snapshotFor = (cards: Card[]): BoardSnapshot => ({
      project: project('p1', 'Northstar', 'NST', false),
      columns: [
        { id: 'column-1', projectId: 'p1', name: 'Backlog', color: '#8e96a3', position: 0 },
        { id: 'column-2', projectId: 'p1', name: 'In progress', color: '#8e96a3', position: 1 },
      ],
      cards, comments: [], members,
    });
    route('GET', (url) => url.includes('/api/projects/p1/board') && url.includes('search'), { json: snapshotFor([card('NST-138', 'column-1', 'Audit the empty states', 'medium', 'u4')]) });
    route('GET', (url) => url.includes('/api/projects/p1/board') && url.includes('assigneeId'), { json: snapshotFor([card('NST-141', 'column-2', 'Trim the board', 'urgent', 'u3')]) });

    const searched = await kanbanService.getBoard('p1', {
      ...allFilters,
      search: 'empty states',
    });
    expect(requests[0].url).toBe('/api/projects/p1/board?search=empty+states');
    expect(searched.cards.map((item) => item.id)).toEqual(['NST-138']);

    const assigned = await kanbanService.getBoard('p1', {
      ...allFilters,
      assigneeId: 'u3',
      priorities: ['urgent'],
    });
    expect(requests[1].url).toBe('/api/projects/p1/board?priorities=urgent&assigneeId=u3');
    expect(assigned.cards.map((item) => item.id)).toEqual(['NST-141']);
  });

  it('creates, updates, moves across columns, and deletes a card', async () => {
    route('POST', (url) => url === '/api/projects/p2/cards', {
      json: card('FLD-25', 'column-5', 'Test service persistence', 'medium', null),
    });
    route('PATCH', (url) => url === '/api/cards/FLD-25', {
      json: { ...card('FLD-25', 'column-5', 'Test service persistence', 'urgent', null), updatedAt: '2026-01-03T00:00:00Z' },
    });
    route('POST', (url, body) => url === '/api/cards/FLD-25/move' && (body as { columnId?: string })?.columnId === 'column-6', {
      json: { ...card('FLD-25', 'column-6', 'Test service persistence', 'urgent', null), updatedAt: '2026-01-03T00:00:00Z' },
    });
    route('POST', (url, body) => url === '/api/cards/FLD-25/move' && (body as { columnId?: string })?.columnId === 'column-7', {
      json: { ...card('FLD-25', 'column-7', 'Test service persistence', 'urgent', null), updatedAt: '2026-01-03T00:00:00Z' },
    });
    route('DELETE', (url) => url === '/api/cards/FLD-25', { status: 204 });

    const created = await kanbanService.createCard('p2', {
      title: 'Test service persistence',
      description: 'A card created by the service contract test.',
      priority: 'medium',
      assigneeId: null,
      dueDate: null,
      labels: ['Test'],
      columnId: 'column-5',
    });
    expect(requests[0].url).toBe('/api/projects/p2/cards');
    expect(requests[0].body).toMatchObject({
      title: 'Test service persistence',
      description: 'A card created by the service contract test.',
      priority: 'medium',
      columnId: 'column-5',
    });
    expect(created.projectId).toBe('p1');
    expect(created.title).toBe('Test service persistence');

    const updated = await kanbanService.updateCard(created.id, { priority: 'urgent' });
    expect(requests[1].url).toBe('/api/cards/FLD-25');
    expect(requests[1].body).toEqual({ priority: 'urgent' });
    expect(updated.priority).toBe('urgent');

    const reordered = await kanbanService.updateCard(created.id, { columnId: 'column-6' });
    expect(requests[2].url).toBe('/api/cards/FLD-25');
    expect(requests[2].body).toEqual({});
    expect(requests[3].url).toBe('/api/cards/FLD-25/move');
    expect(requests[3].body).toEqual({ columnId: 'column-6' });
    expect(reordered.columnId).toBe('column-6');

    const moved = await kanbanService.moveCard(created.id, 'column-7');
    expect(requests[4].url).toBe('/api/cards/FLD-25/move');
    expect(requests[4].body).toEqual({ columnId: 'column-7' });
    expect(moved.columnId).toBe('column-7');
    expect(moved.title).toBe('Test service persistence');

    await expect(kanbanService.deleteCard(created.id)).resolves.toBe(true);
    expect(requests[5].method).toBe('DELETE');
    expect(requests[5].body).toEqual({ resolveRelationships: 'delete' });
  });

  it('adds comments and runs search through the API', async () => {
    const comment: Comment = {
      id: 'comment-3', cardId: 'NST-141', authorId: 'u1', body: 'The service contract keeps this local.',
      createdAt: '2026-01-03T00:00:00Z',
    };
    route('POST', (url) => url === '/api/cards/NST-141/comments', { json: comment });
    route('GET', (url) => url.startsWith('/api/search'), {
      json: [{ type: 'project', id: 'p1', title: 'Northstar', subtitle: 'NST project' }],
    });

    const added = await kanbanService.addComment('NST-141', 'u1', 'The service contract keeps this local.');
    expect(requests[0].url).toBe('/api/cards/NST-141/comments');
    expect(requests[0].body).toEqual({ body: 'The service contract keeps this local.' });
    expect(added.cardId).toBe('NST-141');
    expect(added.body).toContain('local');

    const results = await kanbanService.search('Northstar');
    expect(requests[1].url).toBe('/api/search?q=Northstar');
    expect(results[0]).toMatchObject({ type: 'project', id: 'p1' });
  });
});