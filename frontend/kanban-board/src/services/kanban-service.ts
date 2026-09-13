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

const now = Date.now();
const members: Member[] = [
  { id: 'm1', name: 'Mara Chen', initials: 'MC', color: '#db805e', role: 'Product lead' },
  { id: 'm2', name: 'Theo Alvarez', initials: 'TA', color: '#5f8f77', role: 'Engineer' },
  { id: 'm3', name: 'Inez Okafor', initials: 'IO', color: '#7a72ad', role: 'Designer' },
  { id: 'm4', name: 'Rowan Bell', initials: 'RB', color: '#c58b42', role: 'Engineer' },
];

let projects: Project[] = [
  {
    id: 'p1',
    name: 'Northstar',
    key: 'NST',
    description: 'A calmer way to see the work that moves the team forward.',
    color: '#5f8f77',
    icon: 'N',
    archived: false,
    updatedAt: new Date(now).toISOString(),
    members,
  },
  {
    id: 'p2',
    name: 'Field notes',
    key: 'FLD',
    description: 'Research threads and customer signals.',
    color: '#c58b42',
    icon: 'F',
    archived: false,
    updatedAt: new Date(now - 86400000 * 3).toISOString(),
    members: members.slice(0, 3),
  },
  {
    id: 'p3',
    name: 'Orbit / archive',
    key: 'ORB',
    description: 'Previous experiments and decisions.',
    color: '#7a72ad',
    icon: 'O',
    archived: true,
    updatedAt: new Date(now - 86400000 * 18).toISOString(),
    members: members.slice(0, 2),
  },
];

let columns: BoardColumn[] = [
  { id: 'c1', projectId: 'p1', name: 'Backlog', color: '#8e96a3', position: 0 },
  { id: 'c2', projectId: 'p1', name: 'In progress', color: '#c58b42', position: 1 },
  { id: 'c3', projectId: 'p1', name: 'Review', color: '#7a72ad', position: 2 },
  { id: 'c4', projectId: 'p1', name: 'Shipped', color: '#5f8f77', position: 3 },
  { id: 'c5', projectId: 'p2', name: 'Inbox', color: '#8e96a3', position: 0 },
  { id: 'c6', projectId: 'p2', name: 'Exploring', color: '#c58b42', position: 1 },
  { id: 'c7', projectId: 'p2', name: 'Captured', color: '#5f8f77', position: 2 },
];

const card = (
  id: string,
  columnId: string,
  title: string,
  description: string,
  priority: CardPriority,
  assigneeId: string | null,
  dueDate: string | null,
  labels: string[],
  blockedBy: string[] = [],
  blocking: string[] = [],
): Card => ({
  id, projectId: 'p1', columnId, title, description, priority, assigneeId, dueDate, labels,
  createdAt: new Date(now - 86400000 * 9).toISOString(),
  updatedAt: new Date(now - 86400000).toISOString(),
  blockedBy, blocking, commentCount: 0,
});

let cards: Card[] = [
  card('NST-142', 'c1', 'Decide what “ready” means', 'A small checklist for work entering the flow, so context does not disappear at handoff.', 'high', 'm1', new Date(now + 86400000 * 2).toISOString().slice(0, 10), ['Process']),
  card('NST-138', 'c1', 'Audit the empty states', 'Make the first moment in a new project feel useful rather than blank.', 'medium', 'm3', null, ['UX']),
  card('NST-145', 'c1', 'Name the release ritual', 'A lightweight weekly checkpoint for the team to look back before moving forward.', 'low', null, new Date(now + 86400000 * 6).toISOString().slice(0, 10), ['Team']),
  card('NST-141', 'c2', 'Trim the board to the signal', 'Remove the fields that ask for busywork. Keep just enough shape to hold the story.', 'urgent', 'm2', new Date(now - 86400000).toISOString().slice(0, 10), ['Product'], [], ['NST-147']),
  card('NST-147', 'c2', 'Map the first-run path', 'Walk a new teammate from open question to shipped work in under five minutes.', 'high', 'm3', new Date(now + 86400000 * 3).toISOString().slice(0, 10), ['UX'], ['NST-141']),
  card('NST-136', 'c3', 'Copy pass: project switcher', 'The switcher should make the active project and its state immediately clear.', 'medium', 'm1', new Date(now + 86400000 * 4).toISOString().slice(0, 10), ['Writing']),
  card('NST-129', 'c4', 'Define the team promise', 'A concise statement that keeps the workspace opinionated.', 'low', 'm2', null, ['Strategy']),
];
cards = cards.concat([
  { ...card('FLD-24', 'c5', 'Ask three teams about handoffs', 'Listen for where context drops between conversation and action.', 'high', 'm1', null, ['Research']), projectId: 'p2' },
  { ...card('FLD-19', 'c6', 'Cluster the recurring friction', 'Turn the raw notes into a few patterns we can actually respond to.', 'medium', 'm3', null, ['Research']), projectId: 'p2' },
  { ...card('FLD-11', 'c7', 'Share the first readout', 'A short, honest note with what we know and what we still need to learn.', 'low', 'm1', null, ['Writing']), projectId: 'p2' },
]);

let comments: Comment[] = [
  { id: 'comment-1', cardId: 'NST-141', authorId: 'm1', body: 'The cut feels right. Keep the rationale in the decision log.', createdAt: new Date(now - 86400000 * 2).toISOString() },
  { id: 'comment-2', cardId: 'NST-141', authorId: 'm2', body: 'I can take the first pass after today’s pairing session.', createdAt: new Date(now - 86400000).toISOString() },
];
cards = cards.map((item) => ({ ...item, commentCount: comments.filter((comment) => comment.cardId === item.id).length }));

const wait = <T,>(value: T, delay = 120): Promise<T> =>
  new Promise((resolve) => globalThis.setTimeout(() => resolve(value), delay));

const clone = <T,>(value: T): T => JSON.parse(JSON.stringify(value)) as T;
const projectFor = (id: string) => projects.find((project) => project.id === id) ?? projects[0];

export const kanbanService = {
  async listProjects(includeArchived = true) {
    return wait(clone(includeArchived ? projects : projects.filter((project) => !project.archived)));
  },
  async getBoard(projectId: string, filters: BoardFilters): Promise<BoardSnapshot> {
    const project = projectFor(projectId);
    const projectColumns = columns.filter((column) => column.projectId === project.id).sort((a, b) => a.position - b.position);
    const projectCards = cards.filter((item) => item.projectId === project.id).filter((item) => {
      const term = filters.search.trim().toLowerCase();
      const matchesSearch = !term || `${item.title} ${item.description} ${item.labels.join(' ')}`.toLowerCase().includes(term);
      const matchesPriority = filters.priorities.length === 0 || filters.priorities.includes(item.priority);
      const matchesAssignee = !filters.assigneeId || item.assigneeId === filters.assigneeId;
      const date = item.dueDate ? new Date(`${item.dueDate}T12:00:00`) : null;
      const today = new Date();
      const weekEnd = new Date(today);
      weekEnd.setDate(today.getDate() + 7);
      const matchesDue = filters.due === 'all'
        || (filters.due === 'no-date' && !date)
        || (filters.due === 'overdue' && !!date && date < today)
        || (filters.due === 'this-week' && !!date && date >= today && date <= weekEnd);
      return matchesSearch && matchesPriority && matchesAssignee && matchesDue;
    });
    return wait(clone({ project, columns: projectColumns, cards: projectCards, comments, members: project.members }));
  },
  async createCard(projectId: string, input: CardInput) {
    const index = cards.filter((item) => item.projectId === projectId).length + 1;
    const newCard: Card = {
      id: `${projectFor(projectId).key}-${String(150 + index)}`,
      projectId, ...input, blockedBy: [], blocking: [], commentCount: 0,
      createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(),
    };
    cards = [...cards, newCard];
    return wait(clone(newCard));
  },
  async updateCard(cardId: string, input: Partial<CardInput>) {
    const target = cards.find((item) => item.id === cardId);
    if (!target) throw new Error('Card not found');
    cards = cards.map((item) => item.id === cardId ? { ...item, ...input, updatedAt: new Date().toISOString() } : item);
    return wait(clone(cards.find((item) => item.id === cardId)!));
  },
  async moveCard(cardId: string, columnId: string) {
    return this.updateCard(cardId, { columnId });
  },
  async deleteCard(cardId: string) {
    cards = cards.filter((item) => item.id !== cardId);
    comments = comments.filter((comment) => comment.cardId !== cardId);
    return wait(true);
  },
  async addComment(cardId: string, authorId: string, body: string) {
    const created: Comment = { id: `comment-${Date.now()}`, cardId, authorId, body, createdAt: new Date().toISOString() };
    comments = [...comments, created];
    cards = cards.map((item) => item.id === cardId ? { ...item, commentCount: item.commentCount + 1 } : item);
    return wait(clone(created));
  },
  async search(query: string) {
    const term = query.trim().toLowerCase();
    if (!term) return wait([]);

    const projectResults = projects
      .filter((project) => `${project.name} ${project.description} ${project.key}`.toLowerCase().includes(term))
      .map((project) => ({
        type: 'project' as const,
        id: project.id,
        title: project.name,
        subtitle: project.archived ? 'Archived project' : `${project.key} project`,
      }));
    const cardResults = cards
      .filter((item) => `${item.id} ${item.title} ${item.description} ${item.labels.join(' ')}`.toLowerCase().includes(term))
      .map((item) => ({
        type: 'card' as const,
        id: item.id,
        title: item.title,
        subtitle: `${item.id} · ${projectFor(item.projectId).name}`,
      }));

    return wait(clone([...projectResults, ...cardResults].slice(0, 8)));
  },
  async deleteComment(commentId: string) {
    const target = comments.find((comment) => comment.id === commentId);
    comments = comments.filter((comment) => comment.id !== commentId);
    if (target) cards = cards.map((item) => item.id === target.cardId ? { ...item, commentCount: Math.max(0, item.commentCount - 1) } : item);
    return wait(true);
  },
  async updateProject(projectId: string, input: Partial<Pick<Project, 'name' | 'description' | 'color'>>) {
    projects = projects.map((project) => project.id === projectId ? { ...project, ...input, updatedAt: new Date().toISOString() } : project);
    return wait(clone(projectFor(projectId)));
  },
  async archiveProject(projectId: string) {
    return this.updateProjectStatus(projectId, true);
  },
  async restoreProject(projectId: string) {
    return this.updateProjectStatus(projectId, false);
  },
  async updateProjectStatus(projectId: string, archived: boolean) {
    projects = projects.map((project) => project.id === projectId ? { ...project, archived, updatedAt: new Date().toISOString() } : project);
    return wait(clone(projectFor(projectId)));
  },
  async createProject(input: Pick<Project, 'name' | 'description' | 'color'>) {
    const key = input.name.split(/\s+/).map((part) => part[0]).join('').toUpperCase().slice(0, 3);
    const project: Project = { ...input, id: `p-${Date.now()}`, key, icon: key[0] ?? 'P', archived: false, updatedAt: new Date().toISOString(), members };
    projects = [...projects, project];
    const projectColumns = ['Backlog', 'In progress', 'Review', 'Shipped'].map((name, position) => ({ id: `col-${project.id}-${position}`, projectId: project.id, name, color: ['#8e96a3', '#c58b42', '#7a72ad', '#5f8f77'][position], position }));
    columns = [...columns, ...projectColumns];
    return wait(clone(project));
  },
};
