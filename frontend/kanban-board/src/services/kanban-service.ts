import { customFetch } from '@/lib/api-client';

export type ThemeMode = 'light' | 'dark';
export type CardPriority = 'urgent' | 'high' | 'medium' | 'low';

export interface Member {
  id: string;
  name: string;
  initials: string;
  color: string;
  role: string;
}

export interface Comment {
  id: string;
  cardId: string;
  authorId: string;
  body: string;
  createdAt: string;
}

export interface Card {
  id: string;
  projectId: string;
  columnId: string;
  title: string;
  description: string;
  priority: CardPriority;
  assigneeId: string | null;
  dueDate: string | null;
  labels: string[];
  createdAt: string;
  updatedAt: string;
  blockedBy: string[];
  blocking: string[];
  commentCount: number;
}

export interface BoardColumn {
  id: string;
  projectId: string;
  name: string;
  color: string;
  position: number;
}

export interface Project {
  id: string;
  name: string;
  key: string;
  description: string;
  color: string;
  icon: string;
  archived: boolean;
  updatedAt: string;
  members: Member[];
}

export interface BoardFilters {
  search: string;
  priorities: CardPriority[];
  assigneeId: string | null;
  due: 'all' | 'overdue' | 'this-week' | 'no-date';
}

export interface CardInput {
  title: string;
  description: string;
  priority: CardPriority;
  assigneeId: string | null;
  dueDate: string | null;
  labels: string[];
  columnId: string;
}

export interface BoardSnapshot {
  project: Project;
  columns: BoardColumn[];
  cards: Card[];
  comments: Comment[];
  members: Member[];
}

export interface SearchResult {
  type: 'project' | 'card';
  id: string;
  title: string;
  subtitle: string;
}

const encodeFilters = (projectId: string, filters: BoardFilters) => {
  const params = new URLSearchParams();
  const term = filters.search.trim();
  if (term) params.append('search', term);
  filters.priorities.forEach((priority) => params.append('priorities', priority));
  if (filters.assigneeId) params.append('assigneeId', filters.assigneeId);
  if (filters.due !== 'all') params.append('due', filters.due);
  const query = params.toString();
  return `projects/${encodeURIComponent(projectId)}/board${query ? `?${query}` : ''}`;
};

export const kanbanService = {
  async listProjects(includeArchived = true): Promise<Project[]> {
    const query = includeArchived ? '?includeArchived=true' : '?includeArchived=false';
    return customFetch<Project[]>(`/api/projects${query}`);
  },
  async getBoard(projectId: string, filters: BoardFilters): Promise<BoardSnapshot> {
    return customFetch<BoardSnapshot>(`/api/${encodeFilters(projectId, filters)}`);
  },
  async createCard(projectId: string, input: CardInput): Promise<Card> {
    return customFetch<Card>(`/api/projects/${encodeURIComponent(projectId)}/cards`, {
      method: 'POST',
      body: JSON.stringify(input),
    });
  },
  async updateCard(cardId: string, input: Partial<CardInput>): Promise<Card> {
    const { columnId, ...fields } = input;
    const url = `/api/cards/${encodeURIComponent(cardId)}`;
    const updated = await customFetch<Card>(url, {
      method: 'PATCH',
      body: JSON.stringify(fields),
    });
    if (columnId !== undefined && columnId !== updated.columnId) {
      return this.moveCard(cardId, columnId);
    }
    return updated;
  },
  async moveCard(cardId: string, columnId: string): Promise<Card> {
    return customFetch<Card>(`/api/cards/${encodeURIComponent(cardId)}/move`, {
      method: 'POST',
      body: JSON.stringify({ columnId }),
    });
  },
  async deleteCard(cardId: string): Promise<boolean> {
    await customFetch<void>(`/api/cards/${encodeURIComponent(cardId)}`, {
      method: 'DELETE',
      body: JSON.stringify({ resolveRelationships: 'delete' }),
      responseType: 'text',
    });
    return true;
  },
  async addComment(cardId: string, _authorId: string, body: string): Promise<Comment> {
    return customFetch<Comment>(`/api/cards/${encodeURIComponent(cardId)}/comments`, {
      method: 'POST',
      body: JSON.stringify({ body }),
    });
  },
  async deleteComment(commentId: string): Promise<boolean> {
    await customFetch<void>(`/api/comments/${encodeURIComponent(commentId)}`, {
      method: 'DELETE',
      responseType: 'text',
    });
    return true;
  },
  async search(query: string): Promise<SearchResult[]> {
    return customFetch<SearchResult[]>(`/api/search?q=${encodeURIComponent(query)}`);
  },
  async updateProject(projectId: string, input: Partial<Pick<Project, 'name' | 'description' | 'color'>>): Promise<Project> {
    return customFetch<Project>(`/api/projects/${encodeURIComponent(projectId)}`, {
      method: 'PATCH',
      body: JSON.stringify(input),
    });
  },
  async archiveProject(projectId: string): Promise<Project> {
    return this.updateProjectStatus(projectId, true);
  },
  async restoreProject(projectId: string): Promise<Project> {
    return this.updateProjectStatus(projectId, false);
  },
  async updateProjectStatus(projectId: string, archived: boolean): Promise<Project> {
    const action = archived ? 'archive' : 'restore';
    return customFetch<Project>(`/api/projects/${encodeURIComponent(projectId)}/${action}`, {
      method: 'POST',
    });
  },
  async createProject(input: Pick<Project, 'name' | 'description' | 'color'>): Promise<Project> {
    return customFetch<Project>('/api/projects', {
      method: 'POST',
      body: JSON.stringify(input),
    });
  },
};