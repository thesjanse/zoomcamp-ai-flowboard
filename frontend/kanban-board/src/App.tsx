import { useEffect, useMemo, useState, type DragEvent, type FormEvent } from 'react';
import {
  Archive,
  ArrowUp,
  Bell,
  CalendarDays,
  Check,
  ChevronDown,
  CircleHelp,
  CirclePlus,
  Clipboard,
  Clock3,
  FileText,
  Filter,
  FolderKanban,
  GripVertical,
  Layers3,
  LayoutDashboard,
  LoaderCircle,
  LogOut,
  MessageCircle,
  Moon,
  PanelRight,
  Pencil,
  Plus,
  RotateCcw,
  Search,
  Settings2,
  SlidersHorizontal,
  Sparkles,
  Sun,
  Trash2,
  UserRound,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  type BoardColumn,
  type BoardFilters,
  type Card,
  type CardPriority,
  type Comment,
  type Member,
  type Project,
  kanbanService,
} from '@/services/kanban-service';
import { AuthScreen } from '@/components/auth-screen';
import { authService, type AuthUser } from '@/services/auth-service';

const emptyFilters: BoardFilters = { search: '', priorities: [], assigneeId: null, due: 'all' };
const priorityMeta: Record<CardPriority, { label: string; color: string; soft: string }> = {
  urgent: { label: 'Urgent', color: '#c7564b', soft: 'bg-[#c7564b]/10 text-[#a33b32]' },
  high: { label: 'High', color: '#c58b42', soft: 'bg-[#c58b42]/12 text-[#94621d]' },
  medium: { label: 'Medium', color: '#7082a8', soft: 'bg-[#7082a8]/12 text-[#526484]' },
  low: { label: 'Low', color: '#7a8b7e', soft: 'bg-[#7a8b7e]/12 text-[#55705b]' },
};

const formatDue = (value: string | null) => {
  if (!value) return 'No due date';
  const date = new Date(`${value}T12:00:00`);
  return new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric' }).format(date);
};

const isOverdue = (value: string | null) => !!value && new Date(`${value}T12:00:00`) < new Date();

function Avatar({ member, size = 'md' }: { member?: Member; size?: 'sm' | 'md' }) {
  if (!member) {
    return <span className={`${size === 'sm' ? 'h-6 w-6 text-[10px]' : 'h-8 w-8 text-xs'} inline-flex items-center justify-center rounded-full border border-dashed border-border text-muted-foreground`}><UserRound className="h-3.5 w-3.5" /></span>;
  }
  return <span data-testid={`avatar-member-${member.id}`} title={member.name} className={`${size === 'sm' ? 'h-6 w-6 text-[10px]' : 'h-8 w-8 text-xs'} inline-flex shrink-0 items-center justify-center rounded-full font-bold text-white ring-2 ring-card`} style={{ backgroundColor: member.color }}>{member.initials}</span>;
}

function LoadingBoard() {
  return <div data-testid="loading-board" className="flex min-w-[920px] gap-4 p-5">
    {[1, 2, 3, 4].map((column) => <div key={column} className="w-[270px] shrink-0 space-y-3">
      <div className="h-5 w-32 animate-pulse rounded bg-muted" />
      {[1, 2].map((item) => <div key={item} className="h-36 animate-pulse rounded-2xl border border-border/60 bg-card/70" />)}
    </div>)}
  </div>;
}

function CardItem({
  item, member, onOpen, onDragStart, onDelete,
}: { item: Card; member?: Member; onOpen: () => void; onDragStart: (event: DragEvent<HTMLElement>) => void; onDelete: () => void }) {
  const priority = priorityMeta[item.priority];
  return <article
    draggable
    onDragStart={onDragStart}
    data-testid={`card-task-${item.id}`}
    onClick={onOpen}
    className="group relative cursor-grab rounded-2xl border border-card-border bg-card p-4 shadow-[0_2px_0_hsl(var(--border)/.55)] transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-[0_12px_28px_hsl(226_30%_18%/.08)] active:cursor-grabbing"
  >
    <div className="mb-3 flex items-start justify-between gap-2">
      <div className="flex min-w-0 items-center gap-2">
        <span className="font-mono-ui text-[10px] font-medium tracking-[.08em] text-muted-foreground">{item.id}</span>
        {item.blockedBy.length > 0 && <span title="Blocked by another task" className="h-1.5 w-1.5 rounded-full bg-[#c7564b]" />}
      </div>
      <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
        <button data-testid={`button-edit-card-${item.id}`} onClick={(event) => { event.stopPropagation(); onOpen(); }} className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground"><Pencil className="h-3.5 w-3.5" /></button>
        <button data-testid={`button-delete-card-${item.id}`} onClick={(event) => { event.stopPropagation(); onDelete(); }} className="rounded-md p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"><Trash2 className="h-3.5 w-3.5" /></button>
      </div>
    </div>
    <h3 data-testid={`text-card-title-${item.id}`} className="text-[13px] font-bold leading-5 text-card-foreground">{item.title}</h3>
    {item.description && <p className="mt-1.5 line-clamp-2 text-xs leading-5 text-muted-foreground">{item.description}</p>}
    <div className="mt-4 flex items-center gap-1.5">
      <span data-testid={`badge-priority-${item.id}`} className={`rounded-md px-2 py-1 text-[10px] font-bold ${priority.soft}`}>{priority.label}</span>
      {item.labels.slice(0, 1).map((label) => <span key={label} className="max-w-[92px] truncate rounded-md bg-muted px-2 py-1 text-[10px] font-semibold text-muted-foreground">{label}</span>)}
      {item.labels.length > 1 && <span className="font-mono-ui text-[10px] text-muted-foreground">+{item.labels.length - 1}</span>}
    </div>
    <div className="mt-4 flex items-center justify-between border-t border-border/65 pt-3">
      <div className="flex items-center gap-2">
        <Avatar member={member} size="sm" />
        {item.dueDate && <span className={`flex items-center gap-1 text-[10px] font-medium ${isOverdue(item.dueDate) ? 'text-destructive' : 'text-muted-foreground'}`}><CalendarDays className="h-3 w-3" />{formatDue(item.dueDate)}</span>}
      </div>
      <div className="flex items-center gap-2 text-muted-foreground">
        {item.commentCount > 0 && <span className="flex items-center gap-1 text-[10px]"><MessageCircle className="h-3 w-3" />{item.commentCount}</span>}
        <GripVertical className="h-3.5 w-3.5 opacity-40" />
      </div>
    </div>
  </article>;
}

function CardEditor({
  card, projectId, columnId, members, columnsList, onSaved, onCancel,
}: {
  card?: Card;
  projectId: string;
  columnId: string;
  members: Member[];
  columnsList: BoardColumn[];
  onSaved: (card: Card) => void;
  onCancel: () => void;
}) {
  const [form, setForm] = useState({
    title: card?.title ?? '',
    description: card?.description ?? '',
    priority: card?.priority ?? 'medium' as CardPriority,
    assigneeId: card?.assigneeId ?? '',
    dueDate: card?.dueDate ?? '',
    labels: card?.labels.join(', ') ?? '',
    columnId: card?.columnId ?? columnId,
  });
  const [saving, setSaving] = useState(false);
  const save = async (event: FormEvent) => {
    event.preventDefault();
    if (!form.title.trim()) return;
    setSaving(true);
    const payload = { ...form, title: form.title.trim(), assigneeId: form.assigneeId || null, dueDate: form.dueDate || null, labels: form.labels.split(',').map((label) => label.trim()).filter(Boolean) };
    const result = card ? await kanbanService.updateCard(card.id, payload) : await kanbanService.createCard(projectId, payload);
    setSaving(false);
    onSaved(result);
  };
  return <form onSubmit={save} className="space-y-4" data-testid="form-card-editor">
    <label className="block"><span className="mb-1.5 block text-[11px] font-bold uppercase tracking-[.12em] text-muted-foreground">Title</span><input data-testid="input-card-title" autoFocus required value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} placeholder="Give this work a clear name" className="w-full rounded-xl border border-input bg-background px-3.5 py-3 text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/15" /></label>
    <label className="block"><span className="mb-1.5 block text-[11px] font-bold uppercase tracking-[.12em] text-muted-foreground">Context</span><textarea data-testid="input-card-description" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} placeholder="What should the next person know?" rows={4} className="w-full resize-none rounded-xl border border-input bg-background px-3.5 py-3 text-sm leading-5 outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/15" /></label>
    <div className="grid grid-cols-2 gap-3">
      <label className="block"><span className="mb-1.5 block text-[11px] font-bold uppercase tracking-[.12em] text-muted-foreground">Priority</span><select data-testid="select-card-priority" value={form.priority} onChange={(event) => setForm({ ...form, priority: event.target.value as CardPriority })} className="h-10 w-full rounded-xl border border-input bg-background px-3 text-sm outline-none focus:border-primary">{Object.entries(priorityMeta).map(([value, meta]) => <option key={value} value={value}>{meta.label}</option>)}</select></label>
      <label className="block"><span className="mb-1.5 block text-[11px] font-bold uppercase tracking-[.12em] text-muted-foreground">Status</span><select data-testid="select-card-status" value={form.columnId} onChange={(event) => setForm({ ...form, columnId: event.target.value })} className="h-10 w-full rounded-xl border border-input bg-background px-3 text-sm outline-none focus:border-primary">{columnsList.map((column) => <option key={column.id} value={column.id}>{column.name}</option>)}</select></label>
    </div>
    <div className="grid grid-cols-2 gap-3">
      <label className="block"><span className="mb-1.5 block text-[11px] font-bold uppercase tracking-[.12em] text-muted-foreground">Assignee</span><select data-testid="select-card-assignee" value={form.assigneeId} onChange={(event) => setForm({ ...form, assigneeId: event.target.value })} className="h-10 w-full rounded-xl border border-input bg-background px-3 text-sm outline-none focus:border-primary"><option value="">Unassigned</option>{members.map((member) => <option key={member.id} value={member.id}>{member.name}</option>)}</select></label>
      <label className="block"><span className="mb-1.5 block text-[11px] font-bold uppercase tracking-[.12em] text-muted-foreground">Due date</span><input data-testid="input-card-due-date" type="date" value={form.dueDate} onChange={(event) => setForm({ ...form, dueDate: event.target.value })} className="h-10 w-full rounded-xl border border-input bg-background px-3 text-sm outline-none focus:border-primary" /></label>
    </div>
    <label className="block"><span className="mb-1.5 block text-[11px] font-bold uppercase tracking-[.12em] text-muted-foreground">Labels</span><input data-testid="input-card-labels" value={form.labels} onChange={(event) => setForm({ ...form, labels: event.target.value })} placeholder="Design, Product" className="h-10 w-full rounded-xl border border-input bg-background px-3 text-sm outline-none focus:border-primary" /></label>
    <div className="flex justify-end gap-2 border-t border-border pt-4"><Button type="button" variant="ghost" onClick={onCancel} data-testid="button-cancel-card">Cancel</Button><Button type="submit" disabled={saving} data-testid="button-save-card">{saving ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}{card ? 'Save changes' : 'Add task'}</Button></div>
  </form>;
}

function DetailPanel({
  card, project, columnsList, members, currentUserId, onClose, onChanged, onDelete,
}: {
  card: Card;
  project: Project;
  columnsList: BoardColumn[];
  members: Member[];
  currentUserId: string;
  onClose: () => void;
  onChanged: (card: Card) => void;
  onDelete: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [commentText, setCommentText] = useState('');
  const [comments, setComments] = useState<Comment[]>([]);
  const [savingComment, setSavingComment] = useState(false);
  const memberById = useMemo(() => new Map(members.map((member) => [member.id, member])), [members]);
  const column = columnsList.find((item) => item.id === card.columnId);
  useEffect(() => {
    let active = true;
    kanbanService.getBoard(project.id, emptyFilters).then((board) => { if (active) setComments(board.comments.filter((item) => item.cardId === card.id)); });
    return () => { active = false; };
  }, [card.id, project.id]);
  const addComment = async () => {
    if (!commentText.trim()) return;
    setSavingComment(true);
    const created = await kanbanService.addComment(card.id, currentUserId, commentText.trim());
    setComments([...comments, created]);
    setCommentText('');
    setSavingComment(false);
    onChanged({ ...card, commentCount: card.commentCount + 1 });
  };
  return <div className="fixed inset-0 z-40 flex justify-end bg-foreground/20 backdrop-blur-[2px]" data-testid="task-detail-surface">
    <aside className="h-full w-full max-w-[440px] overflow-y-auto border-l border-border bg-background shadow-2xl animate-in slide-in-from-right duration-300">
      <div className="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-background/90 px-6 py-4 backdrop-blur">
        <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground"><PanelRight className="h-4 w-4" />Task detail</div>
        <div className="flex items-center gap-1"><button data-testid="button-edit-detail" onClick={() => setEditing(!editing)} className="rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground"><Pencil className="h-4 w-4" /></button><button data-testid="button-close-detail" onClick={onClose} className="rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground"><X className="h-4 w-4" /></button></div>
      </div>
      <div className="p-6">
        {editing ? <CardEditor card={card} projectId={project.id} columnId={card.columnId} members={members} columnsList={columnsList} onSaved={(updated) => { onChanged(updated); setEditing(false); }} onCancel={() => setEditing(false)} /> : <>
          <div className="mb-5 flex items-center gap-2"><span className="font-mono-ui text-[11px] text-muted-foreground">{card.id}</span><span className="h-1 w-1 rounded-full bg-border" /><span className="text-[11px] font-semibold text-muted-foreground">{column?.name}</span></div>
          <h1 data-testid="text-detail-title" className="text-2xl font-extrabold leading-tight tracking-[-.04em]">{card.title}</h1>
          <div className="mt-5 flex flex-wrap gap-2"><span className={`rounded-lg px-2.5 py-1.5 text-xs font-bold ${priorityMeta[card.priority].soft}`}>{priorityMeta[card.priority].label} priority</span>{card.labels.map((label) => <span key={label} className="rounded-lg bg-muted px-2.5 py-1.5 text-xs font-semibold text-muted-foreground">{label}</span>)}</div>
          <div className="my-6 grid grid-cols-2 gap-3">
            <div className="rounded-xl border border-border bg-card p-3"><span className="block text-[10px] font-bold uppercase tracking-[.12em] text-muted-foreground">Assignee</span><div className="mt-2 flex items-center gap-2 text-xs font-semibold"><Avatar member={memberById.get(card.assigneeId ?? '')} size="sm" />{memberById.get(card.assigneeId ?? '')?.name ?? 'Unassigned'}</div></div>
            <div className="rounded-xl border border-border bg-card p-3"><span className="block text-[10px] font-bold uppercase tracking-[.12em] text-muted-foreground">Due date</span><div className={`mt-2 flex items-center gap-2 text-xs font-semibold ${isOverdue(card.dueDate) ? 'text-destructive' : ''}`}><CalendarDays className="h-3.5 w-3.5" />{formatDue(card.dueDate)}</div></div>
          </div>
          <section><h2 className="mb-2 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[.12em] text-muted-foreground"><FileText className="h-3.5 w-3.5" />Context</h2><p className="whitespace-pre-wrap text-sm leading-6 text-foreground/80">{card.description || 'No context added yet.'}</p></section>
          {(card.blockedBy.length > 0 || card.blocking.length > 0) && <section className="mt-6 border-t border-border pt-5"><h2 className="mb-3 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[.12em] text-muted-foreground"><Layers3 className="h-3.5 w-3.5" />Dependencies</h2><div className="space-y-2">{card.blockedBy.length > 0 && <p className="text-xs text-destructive">Blocked by <span className="font-mono-ui">{card.blockedBy.join(', ')}</span></p>}{card.blocking.length > 0 && <p className="text-xs text-muted-foreground">Unblocks <span className="font-mono-ui">{card.blocking.join(', ')}</span></p>}</div></section>}
          <section className="mt-7 border-t border-border pt-5"><h2 className="mb-4 flex items-center gap-2 text-[11px] font-bold uppercase tracking-[.12em] text-muted-foreground"><MessageCircle className="h-3.5 w-3.5" />Conversation <span className="font-mono-ui text-[10px]">{comments.length}</span></h2><div className="space-y-4">{comments.map((comment) => <div key={comment.id} className="flex gap-3"><Avatar member={memberById.get(comment.authorId)} size="sm" /><div className="min-w-0"><div className="flex items-center gap-2"><span className="text-xs font-bold">{memberById.get(comment.authorId)?.name}</span><span className="text-[10px] text-muted-foreground">{formatDue(comment.createdAt.slice(0, 10))}</span></div><p className="mt-1 text-xs leading-5 text-foreground/75">{comment.body}</p></div></div>)}</div><div className="mt-5 flex gap-2"><Avatar member={memberById.get(currentUserId)} size="sm" /><div className="flex min-w-0 flex-1 gap-2"><input data-testid="input-comment" value={commentText} onChange={(event) => setCommentText(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); void addComment(); } }} placeholder="Leave a note…" className="min-w-0 flex-1 rounded-lg border border-input bg-card px-3 py-2 text-xs outline-none focus:border-primary" /><button data-testid="button-add-comment" disabled={savingComment} onClick={() => void addComment()} className="rounded-lg bg-primary px-3 text-primary-foreground transition hover:brightness-95">{savingComment ? <LoaderCircle className="h-3.5 w-3.5 animate-spin" /> : <ArrowUp className="h-3.5 w-3.5" />}</button></div></div></section>
          <div className="mt-8 flex items-center justify-between border-t border-border pt-5"><button data-testid="button-delete-detail" onClick={onDelete} className="flex items-center gap-2 text-xs font-bold text-destructive hover:underline"><Trash2 className="h-3.5 w-3.5" />Delete task</button><span className="text-[10px] text-muted-foreground">Updated just now</span></div>
        </>}
      </div>
    </aside>
  </div>;
}

function App() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProjectId, setActiveProjectId] = useState('p1');
  const [board, setBoard] = useState<{ project: Project; columns: BoardColumn[]; cards: Card[]; members: Member[] } | null>(null);
  const [filters, setFilters] = useState<BoardFilters>(emptyFilters);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedCardId, setSelectedCardId] = useState<string | null>(null);
  const [composer, setComposer] = useState<{ open: boolean; columnId: string }>({ open: false, columnId: '' });
  const [editingProject, setEditingProject] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [projectMenuOpen, setProjectMenuOpen] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem('northstar-theme') === 'dark');
  const [toast, setToast] = useState('');
  const [dragOverColumn, setDragOverColumn] = useState<string | null>(null);
  const [showArchived, setShowArchived] = useState(false);
  const [mobileSearchOpen, setMobileSearchOpen] = useState(false);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [authLoading, setAuthLoading] = useState(true);

  const reloadProjects = async () => setProjects(await kanbanService.listProjects(true));
  const reloadBoard = async (showLoading = false) => {
    if (showLoading) setLoading(true); else setRefreshing(true);
    const next = await kanbanService.getBoard(activeProjectId, filters);
    setBoard(next);
    setLoading(false);
    setRefreshing(false);
  };
  useEffect(() => { void authService.restore().then(setUser).catch(() => setUser(null)).finally(() => setAuthLoading(false)); }, []);
  useEffect(() => { if (user) void reloadProjects(); }, [user]);
  useEffect(() => { if (user) void reloadBoard(true); }, [user, activeProjectId, filters.search, filters.assigneeId, filters.due, filters.priorities.join(',')]);
  useEffect(() => { document.documentElement.classList.toggle('dark', darkMode); localStorage.setItem('northstar-theme', darkMode ? 'dark' : 'light'); }, [darkMode]);
  useEffect(() => {
    if (!toast) return undefined;
    const timeout = window.setTimeout(() => setToast(''), 2800);
    return () => window.clearTimeout(timeout);
  }, [toast]);

  const selectedCard = board?.cards.find((item) => item.id === selectedCardId) ?? null;
  const activeProjects = projects.filter((project) => !project.archived);
  const visibleProjects = showArchived ? projects : activeProjects;
  const workspaceMembers = board?.members ?? [];
  const currentMember = workspaceMembers.find((member) => member.id === user?.id) ?? workspaceMembers[0];
  const memberRole = currentMember?.role === 'admin' ? 'Admin' : 'Member';
  const logout = async () => { await authService.logout(); setUser(null); };
  const cardsByColumn = useMemo(() => {
    const map = new Map<string, Card[]>();
    board?.columns.forEach((column) => map.set(column.id, board.cards.filter((item) => item.columnId === column.id)));
    return map;
  }, [board]);
  const change = async (message: string) => { await reloadProjects(); await reloadBoard(); setToast(message); };
  const deleteCard = async (cardId: string) => {
    if (!window.confirm('Delete this task? This cannot be undone.')) return;
    await kanbanService.deleteCard(cardId);
    if (selectedCardId === cardId) setSelectedCardId(null);
    await reloadBoard();
    setToast('Task deleted');
  };
  const moveCard = async (cardId: string, columnId: string) => {
    await kanbanService.moveCard(cardId, columnId);
    await reloadBoard();
    setToast('Task moved');
  };
  const drop = (event: DragEvent<HTMLElement>, columnId: string) => {
    event.preventDefault();
    const cardId = event.dataTransfer.getData('text/plain');
    setDragOverColumn(null);
    if (cardId) void moveCard(cardId, columnId);
  };
  const archived = board?.project.archived ?? false;
  if (authLoading) {
    return <div className="flex min-h-[100dvh] items-center justify-center bg-background text-foreground"><LoaderCircle className="h-5 w-5 animate-spin text-muted-foreground" /></div>;
  }
  if (!user) {
    return <AuthScreen onAuthed={setUser} />;
  }
  return <div className="grain min-h-[100dvh] bg-background text-foreground">
    <div className="flex min-h-[100dvh]">
      <aside className="hidden w-[238px] shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground lg:flex">
        <div className="flex items-center gap-3 px-5 py-6"><div className="flex h-9 w-9 items-center justify-center rounded-xl bg-sidebar-primary font-mono-ui text-sm font-bold text-sidebar-primary-foreground">N</div><div><p className="text-sm font-extrabold tracking-[-.03em]">Northstar</p><p className="font-mono-ui text-[9px] uppercase tracking-[.18em] text-sidebar-foreground/45">Ship with context</p></div></div>
        <nav className="space-y-1 px-3" aria-label="Main navigation"><button data-testid="nav-board" className="flex w-full items-center gap-3 rounded-xl bg-sidebar-accent px-3 py-2.5 text-left text-xs font-bold text-sidebar-accent-foreground"><LayoutDashboard className="h-4 w-4 text-sidebar-primary" />Board<span className="ml-auto rounded bg-sidebar-foreground/10 px-1.5 py-0.5 font-mono-ui text-[9px]">⌘1</span></button><button data-testid="nav-my-work" onClick={() => setFilters({ ...emptyFilters, assigneeId: user.id })} className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-xs font-semibold text-sidebar-foreground/65 transition hover:bg-sidebar-accent hover:text-sidebar-foreground"><Clipboard className="h-4 w-4" />My work</button><button data-testid="nav-activity" onClick={() => setToast('Activity is quiet. That is usually a good sign.')} className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-xs font-semibold text-sidebar-foreground/65 transition hover:bg-sidebar-accent hover:text-sidebar-foreground"><Clock3 className="h-4 w-4" />Activity<span className="ml-auto h-1.5 w-1.5 rounded-full bg-sidebar-primary" /></button></nav>
        <div className="mt-8 px-5"><div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-[.16em] text-sidebar-foreground/35"><span>Projects</span><button data-testid="button-new-project-sidebar" onClick={() => setEditingProject(true)} className="rounded p-1 hover:bg-sidebar-accent hover:text-sidebar-foreground"><Plus className="h-3.5 w-3.5" /></button></div><div className="mt-3 space-y-1">{activeProjects.map((project) => <button key={project.id} data-testid={`nav-project-${project.id}`} onClick={() => setActiveProjectId(project.id)} className={`flex w-full items-center gap-2.5 rounded-xl px-2.5 py-2 text-left text-xs transition ${project.id === activeProjectId ? 'bg-sidebar-primary/12 font-bold text-sidebar-foreground' : 'font-medium text-sidebar-foreground/60 hover:bg-sidebar-accent hover:text-sidebar-foreground'}`}><span className="flex h-6 w-6 items-center justify-center rounded-lg text-[10px] font-extrabold text-white" style={{ backgroundColor: project.color }}>{project.icon}</span><span className="truncate">{project.name}</span>{project.id === activeProjectId && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-sidebar-primary" />}</button>)}</div></div>
        <div className="mt-auto space-y-1 border-t border-sidebar-border px-3 py-4"><button data-testid="button-help" onClick={() => setToast('Need a hand? Ask the team in Activity.')} className="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-xs font-semibold text-sidebar-foreground/55 hover:bg-sidebar-accent hover:text-sidebar-foreground"><CircleHelp className="h-4 w-4" />Help & shortcuts</button><button data-testid="button-sidebar-settings" onClick={() => setSettingsOpen(true)} className="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-xs font-semibold text-sidebar-foreground/55 hover:bg-sidebar-accent hover:text-sidebar-foreground"><Settings2 className="h-4 w-4" />Workspace settings</button><div className="mt-3 flex items-center gap-2 rounded-xl bg-sidebar-accent/60 p-2.5"><Avatar member={currentMember} size="sm" /><div className="min-w-0"><p className="truncate text-[11px] font-bold">{user.name}</p><p className="truncate text-[10px] text-sidebar-foreground/45">{memberRole}</p></div><button data-testid="button-profile-menu" onClick={() => void logout()} title="Sign out" className="ml-auto text-sidebar-foreground/45 transition hover:text-sidebar-foreground"><LogOut className="h-4 w-4" /></button></div></div>
      </aside>
      <main className="min-w-0 flex-1">
        <header className="sticky top-0 z-20 border-b border-border/70 bg-background/85 backdrop-blur-xl">
          <div className="flex h-[68px] items-center gap-3 px-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-3 lg:hidden"><div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary font-mono-ui text-sm font-bold text-primary-foreground">N</div><span className="text-sm font-extrabold">Northstar</span></div>
            <div className="relative min-w-0"><button data-testid="button-project-switcher" onClick={() => setProjectMenuOpen(!projectMenuOpen)} className="flex items-center gap-2 rounded-xl px-2 py-1.5 text-left transition hover:bg-muted"><span className="flex h-7 w-7 items-center justify-center rounded-lg text-[10px] font-extrabold text-white" style={{ backgroundColor: board?.project.color ?? '#5f8f77' }}>{board?.project.icon ?? 'N'}</span><span className="hidden max-w-[140px] truncate text-sm font-extrabold sm:block">{board?.project.name ?? 'Loading'}</span><ChevronDown className="h-4 w-4 text-muted-foreground" /></button>{projectMenuOpen && <div className="absolute left-0 top-12 z-30 w-64 rounded-2xl border border-border bg-popover p-2 shadow-xl"><div className="flex items-center justify-between px-3 py-2"><span className="text-[10px] font-bold uppercase tracking-[.14em] text-muted-foreground">Switch project</span><button data-testid="button-close-project-menu" onClick={() => setProjectMenuOpen(false)}><X className="h-3.5 w-3.5 text-muted-foreground" /></button></div>{visibleProjects.map((project) => <button key={project.id} data-testid={`switch-project-${project.id}`} onClick={() => { setActiveProjectId(project.id); setProjectMenuOpen(false); }} className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-xs hover:bg-muted"><span className="flex h-6 w-6 items-center justify-center rounded-lg text-[10px] font-bold text-white" style={{ backgroundColor: project.color }}>{project.icon}</span><span className="font-semibold">{project.name}</span>{project.archived && <Archive className="ml-auto h-3.5 w-3.5 text-muted-foreground" />}</button>)}<button data-testid="button-toggle-archived-projects" onClick={() => setShowArchived(!showArchived)} className="flex w-full items-center gap-2 border-t border-border px-3 py-2.5 text-xs font-semibold text-muted-foreground hover:text-foreground"><Archive className="h-3.5 w-3.5" />{showArchived ? 'Hide archived' : 'Show archived'}</button><button data-testid="button-create-project-menu" onClick={() => { setEditingProject(true); setProjectMenuOpen(false); }} className="mt-1 flex w-full items-center gap-2 border-t border-border px-3 py-3 text-xs font-bold text-primary"><Plus className="h-4 w-4" />New project</button></div>}</div>
            <div className="hidden h-5 w-px bg-border sm:block" /><div className="hidden items-center gap-2 text-xs text-muted-foreground sm:flex"><span className="font-mono-ui text-[10px]">{board?.project.key ?? '—'}</span><span>/</span><span>Board</span></div>
            <div className="ml-auto flex items-center gap-1.5 sm:gap-2"><label className="group hidden items-center gap-2 rounded-xl border border-transparent bg-muted/70 px-3 py-2 transition focus-within:border-primary/40 focus-within:bg-card sm:flex"><Search className="h-4 w-4 text-muted-foreground" /><input data-testid="input-search" value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} placeholder="Search tasks" className="w-32 bg-transparent text-xs outline-none placeholder:text-muted-foreground/70 lg:w-44" /><kbd className="hidden rounded bg-background px-1.5 py-0.5 font-mono-ui text-[9px] text-muted-foreground lg:block">⌘ K</kbd></label><button data-testid="button-mobile-search" onClick={() => setMobileSearchOpen(!mobileSearchOpen)} className="rounded-xl p-2.5 text-muted-foreground hover:bg-muted sm:hidden"><Search className="h-4 w-4" /></button><button data-testid="button-notifications" onClick={() => setToast('You are all caught up')} className="relative rounded-xl p-2.5 text-muted-foreground hover:bg-muted"><Bell className="h-4 w-4" /><span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-primary" /></button><button data-testid="button-theme-toggle" onClick={() => setDarkMode(!darkMode)} className="rounded-xl p-2.5 text-muted-foreground hover:bg-muted">{darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}</button><button data-testid="button-header-settings" onClick={() => setSettingsOpen(true)} className="hidden rounded-xl p-2.5 text-muted-foreground hover:bg-muted sm:block"><Settings2 className="h-4 w-4" /></button><Avatar member={currentMember} size="sm" /></div>
          </div>
          {mobileSearchOpen && <label className="flex items-center gap-2 border-t border-border/70 px-4 py-3 sm:hidden"><Search className="h-4 w-4 text-muted-foreground" /><input data-testid="input-mobile-search" autoFocus value={filters.search} onChange={(event) => setFilters({ ...filters, search: event.target.value })} placeholder="Search tasks by title, label, or context" className="min-w-0 flex-1 bg-transparent text-xs outline-none" /></label>}
        </header>
        <div className="flex min-h-[calc(100dvh-68px)] flex-col">
          <section className="border-b border-border/70 px-4 pb-5 pt-7 sm:px-6 lg:px-8"><div className="flex flex-wrap items-end justify-between gap-4"><div><div className="mb-2 flex items-center gap-2 text-[10px] font-bold uppercase tracking-[.18em] text-primary"><Sparkles className="h-3.5 w-3.5" />The work in motion</div><h1 data-testid="text-board-title" className="text-3xl font-extrabold tracking-[-.055em] sm:text-4xl">{board?.project.name ?? 'Your board'}</h1><p className="mt-2 max-w-xl text-sm text-muted-foreground">{board?.project.description}</p></div><div className="flex items-center gap-2"><Button variant="outline" onClick={() => setSettingsOpen(true)} data-testid="button-project-settings"><SlidersHorizontal className="h-4 w-4" /><span className="hidden sm:inline">Project settings</span></Button><Button onClick={() => setComposer({ open: true, columnId: board?.columns[0]?.id ?? '' })} data-testid="button-add-task"><Plus className="h-4 w-4" />Add task</Button></div></div></section>
          <section className="flex flex-wrap items-center gap-2 border-b border-border/70 px-4 py-3 sm:px-6 lg:px-8"><div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[.14em] text-muted-foreground"><span className="h-1.5 w-1.5 rounded-full bg-primary" />{board?.cards.length ?? 0} tasks</div><div className="h-4 w-px bg-border" /><button data-testid="button-filter-menu" onClick={() => setFiltersOpen(!filtersOpen)} className={`flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-xs font-bold transition ${filters.priorities.length || filters.assigneeId || filters.due !== 'all' ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted hover:text-foreground'}`}><Filter className="h-3.5 w-3.5" />Filter{(filters.priorities.length || filters.assigneeId || filters.due !== 'all') ? ` · ${filters.priorities.length + (filters.assigneeId ? 1 : 0) + (filters.due !== 'all' ? 1 : 0)}` : ''}</button>{filters.search && <button data-testid="button-clear-search" onClick={() => setFilters({ ...filters, search: '' })} className="flex items-center gap-1.5 rounded-lg bg-muted px-2.5 py-1.5 text-xs font-semibold">“{filters.search}”<X className="h-3 w-3" /></button>}<div className="ml-auto flex items-center gap-2"><button data-testid="button-refresh-board" onClick={() => void reloadBoard()} className={`rounded-lg p-1.5 text-muted-foreground hover:bg-muted ${refreshing ? 'animate-spin' : ''}`}><RotateCcw className="h-3.5 w-3.5" /></button><span className="hidden text-[10px] font-semibold text-muted-foreground sm:block">Last synced just now</span></div>{filtersOpen && <div className="relative basis-full"><div className="absolute left-0 top-1 z-10 w-full max-w-[360px] rounded-2xl border border-border bg-popover p-4 shadow-xl"><div className="flex items-center justify-between"><span className="text-xs font-extrabold">Tune the view</span><button data-testid="button-close-filters" onClick={() => setFiltersOpen(false)}><X className="h-3.5 w-3.5 text-muted-foreground" /></button></div><div className="mt-4"><p className="mb-2 text-[10px] font-bold uppercase tracking-[.12em] text-muted-foreground">Priority</p><div className="flex flex-wrap gap-1.5">{Object.entries(priorityMeta).map(([value, meta]) => <button key={value} data-testid={`filter-priority-${value}`} onClick={() => setFilters({ ...filters, priorities: filters.priorities.includes(value as CardPriority) ? filters.priorities.filter((priority) => priority !== value) : [...filters.priorities, value as CardPriority] })} className={`rounded-lg px-2.5 py-1.5 text-[11px] font-bold ${filters.priorities.includes(value as CardPriority) ? meta.soft + ' ring-1 ring-current' : 'bg-muted text-muted-foreground'}`}>{meta.label}</button>)}</div></div><label className="mt-4 block"><span className="mb-2 block text-[10px] font-bold uppercase tracking-[.12em] text-muted-foreground">Assignee</span><select data-testid="filter-assignee" value={filters.assigneeId ?? ''} onChange={(event) => setFilters({ ...filters, assigneeId: event.target.value || null })} className="h-9 w-full rounded-lg border border-input bg-background px-2 text-xs outline-none"><option value="">Everyone</option>{board?.members.map((member) => <option key={member.id} value={member.id}>{member.name}</option>)}</select></label><label className="mt-3 block"><span className="mb-2 block text-[10px] font-bold uppercase tracking-[.12em] text-muted-foreground">Due date</span><select data-testid="filter-due" value={filters.due} onChange={(event) => setFilters({ ...filters, due: event.target.value as BoardFilters['due'] })} className="h-9 w-full rounded-lg border border-input bg-background px-2 text-xs outline-none"><option value="all">Any date</option><option value="overdue">Overdue</option><option value="this-week">Due this week</option><option value="no-date">No due date</option></select></label><button data-testid="button-reset-filters" onClick={() => setFilters({ ...emptyFilters })} className="mt-4 w-full rounded-lg border border-border py-2 text-xs font-bold text-muted-foreground hover:bg-muted">Clear all filters</button></div></div>}</section>
          {archived && <div className="mx-4 mt-5 flex items-center justify-between gap-3 rounded-2xl border border-[#c58b42]/35 bg-[#c58b42]/10 px-4 py-3 sm:mx-6 lg:mx-8"><div className="flex items-center gap-3"><Archive className="h-4 w-4 text-[#94621d]" /><p className="text-xs font-semibold text-[#80561b]">This project is archived. Restore it to keep shipping.</p></div><button data-testid="button-restore-project" onClick={async () => { await kanbanService.restoreProject(activeProjectId); await reloadProjects(); await reloadBoard(); setToast('Project restored'); }} className="rounded-lg bg-[#c58b42] px-3 py-1.5 text-xs font-bold text-white">Restore</button></div>}
          <div className="relative flex-1 overflow-x-auto overflow-y-hidden">{loading ? <LoadingBoard /> : board?.columns.length ? <div className="flex min-w-max items-start gap-4 p-4 sm:p-6 lg:p-8">{board.columns.map((column) => { const columnCards = cardsByColumn.get(column.id) ?? []; return <section key={column.id} data-testid={`column-${column.id}`} onDragOver={(event) => { event.preventDefault(); setDragOverColumn(column.id); }} onDragLeave={() => setDragOverColumn(null)} onDrop={(event) => drop(event, column.id)} className={`w-[276px] shrink-0 rounded-2xl transition ${dragOverColumn === column.id ? 'bg-primary/8 ring-2 ring-primary/25' : ''}`}><div className="mb-3 flex items-center justify-between px-1"><div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full" style={{ backgroundColor: column.color }} /><h2 className="text-xs font-extrabold">{column.name}</h2><span data-testid={`count-column-${column.id}`} className="font-mono-ui text-[10px] text-muted-foreground">{columnCards.length}</span></div><button data-testid={`button-add-task-${column.id}`} onClick={() => setComposer({ open: true, columnId: column.id })} className="rounded-lg p-1 text-muted-foreground hover:bg-muted hover:text-foreground"><Plus className="h-4 w-4" /></button></div><div className="space-y-3">{columnCards.map((item) => <CardItem key={item.id} item={item} member={board.members.find((member) => member.id === item.assigneeId)} onOpen={() => setSelectedCardId(item.id)} onDragStart={(event) => { event.dataTransfer.setData('text/plain', item.id); event.dataTransfer.effectAllowed = 'move'; }} onDelete={() => void deleteCard(item.id)} />)}{columnCards.length === 0 && <button data-testid={`button-empty-column-${column.id}`} onClick={() => setComposer({ open: true, columnId: column.id })} className="flex min-h-[130px] w-full flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-card/40 text-center transition hover:border-primary/40 hover:bg-card"><CirclePlus className="mb-2 h-5 w-5 text-muted-foreground/60" /><span className="text-xs font-semibold text-muted-foreground">Drop work here</span><span className="mt-1 text-[10px] text-muted-foreground/65">or add a task</span></button>}</div></section>; })}<button data-testid="button-add-column" onClick={() => setToast('Column editing is ready for the next board pass')} className="mt-8 flex w-[180px] shrink-0 items-center justify-center gap-2 rounded-xl border border-dashed border-border py-3 text-xs font-bold text-muted-foreground hover:border-primary/40 hover:text-primary"><Plus className="h-4 w-4" />Add column</button></div> : <div data-testid="empty-board" className="flex min-h-[420px] flex-col items-center justify-center px-6 text-center"><div className="flex h-16 w-16 items-center justify-center rounded-3xl bg-primary/10 text-primary"><FolderKanban className="h-7 w-7" /></div><h2 className="mt-5 text-xl font-extrabold tracking-[-.03em]">A clear surface for the next idea</h2><p className="mt-2 max-w-sm text-sm leading-6 text-muted-foreground">Start with one task. The board will grow around the work, not the other way around.</p><Button className="mt-5" onClick={() => setComposer({ open: true, columnId: board?.columns[0]?.id ?? '' })} data-testid="button-empty-add-task"><Plus className="h-4 w-4" />Add first task</Button></div>}</div>
        </div>
      </main>
    </div>
    {selectedCard && board && <DetailPanel card={selectedCard} project={board.project} columnsList={board.columns} members={board.members} currentUserId={user.id} onClose={() => setSelectedCardId(null)} onChanged={(updated) => { setBoard({ ...board, cards: board.cards.map((item) => item.id === updated.id ? updated : item) }); void reloadBoard(); }} onDelete={() => void deleteCard(selectedCard.id)} />}
    {composer.open && board && <div className="fixed inset-0 z-40 flex items-center justify-center bg-foreground/25 p-4 backdrop-blur-sm" data-testid="card-composer-dialog"><div className="w-full max-w-xl rounded-3xl border border-border bg-background p-6 shadow-2xl"><div className="mb-6 flex items-start justify-between"><div><p className="mb-1 text-[10px] font-bold uppercase tracking-[.16em] text-primary">New piece of work</p><h2 className="text-xl font-extrabold tracking-[-.03em]">Add a task</h2><p className="mt-1 text-xs text-muted-foreground">Make the next action obvious.</p></div><button data-testid="button-close-composer" onClick={() => setComposer({ ...composer, open: false })} className="rounded-lg p-2 text-muted-foreground hover:bg-muted"><X className="h-4 w-4" /></button></div><CardEditor projectId={board.project.id} columnId={composer.columnId} members={board.members} columnsList={board.columns} onSaved={(created) => { setComposer({ ...composer, open: false }); void reloadBoard(); setToast(`Added ${created.id}`); }} onCancel={() => setComposer({ ...composer, open: false })} /></div></div>}
    {settingsOpen && board && <div className="fixed inset-0 z-40 flex justify-end bg-foreground/20 backdrop-blur-sm"><aside className="h-full w-full max-w-[440px] overflow-y-auto border-l border-border bg-background p-6 shadow-2xl"><div className="flex items-center justify-between"><div><p className="text-[10px] font-bold uppercase tracking-[.16em] text-primary">Workspace / project</p><h2 className="mt-1 text-xl font-extrabold">Settings</h2></div><button data-testid="button-close-settings" onClick={() => setSettingsOpen(false)} className="rounded-lg p-2 text-muted-foreground hover:bg-muted"><X className="h-4 w-4" /></button></div><div className="mt-8 space-y-7"><section><h3 className="text-xs font-extrabold">Project identity</h3><p className="mt-1 text-xs text-muted-foreground">A small amount of framing helps the work stay legible.</p><div className="mt-4 space-y-3"><label className="block text-xs font-bold">Name<input data-testid="input-project-name" defaultValue={board.project.name} id="project-name" className="mt-1.5 h-10 w-full rounded-xl border border-input bg-background px-3 text-sm outline-none focus:border-primary" /></label><label className="block text-xs font-bold">Description<textarea data-testid="input-project-description" defaultValue={board.project.description} id="project-description" rows={3} className="mt-1.5 w-full resize-none rounded-xl border border-input bg-background px-3 py-2 text-sm outline-none focus:border-primary" /></label><Button data-testid="button-save-project-settings" onClick={async () => { const name = (document.getElementById('project-name') as HTMLInputElement).value; const description = (document.getElementById('project-description') as HTMLTextAreaElement).value; await kanbanService.updateProject(board.project.id, { name, description }); await reloadProjects(); await reloadBoard(); setSettingsOpen(false); setToast('Project settings saved'); }}>Save changes</Button></div></section><section className="border-t border-border pt-6"><h3 className="text-xs font-extrabold">People on this project</h3><div className="mt-3 space-y-2">{board.members.map((member) => <div key={member.id} className="flex items-center gap-3 rounded-xl bg-card p-2.5"><Avatar member={member} size="sm" /><div><p className="text-xs font-bold">{member.name}</p><p className="text-[10px] text-muted-foreground">{member.role}</p></div></div>)}</div></section><section className="border-t border-border pt-6"><h3 className="text-xs font-extrabold">Archive project</h3><p className="mt-1 text-xs leading-5 text-muted-foreground">{archived ? 'This project is archived and hidden from the active project list.' : 'Archive this project when the work is complete. It can be restored later.'}</p><button data-testid={archived ? 'button-restore-project-settings' : 'button-archive-project'} onClick={async () => { if (!archived && !window.confirm('Archive this project?')) return; if (archived) await kanbanService.restoreProject(board.project.id); else await kanbanService.archiveProject(board.project.id); await reloadProjects(); await reloadBoard(); setSettingsOpen(false); setToast(archived ? 'Project restored' : 'Project archived'); }} className={`mt-4 flex items-center gap-2 rounded-xl border px-3 py-2 text-xs font-bold ${archived ? 'border-primary/30 text-primary' : 'border-destructive/25 text-destructive'}`}>{archived ? <RotateCcw className="h-3.5 w-3.5" /> : <Archive className="h-3.5 w-3.5" />}{archived ? 'Restore project' : 'Archive project'}</button></section></div></aside></div>}
    {editingProject && <div className="fixed inset-0 z-40 flex items-center justify-center bg-foreground/25 p-4 backdrop-blur-sm"><div className="w-full max-w-md rounded-3xl border border-border bg-background p-6 shadow-2xl"><div className="flex items-start justify-between"><div><p className="text-[10px] font-bold uppercase tracking-[.16em] text-primary">A new orbit</p><h2 className="mt-1 text-xl font-extrabold">Create a project</h2></div><button data-testid="button-close-new-project" onClick={() => setEditingProject(false)} className="rounded-lg p-2 text-muted-foreground hover:bg-muted"><X className="h-4 w-4" /></button></div><ProjectForm onCancel={() => setEditingProject(false)} onCreated={async (project) => { await reloadProjects(); setActiveProjectId(project.id); setEditingProject(false); setToast(`${project.name} is ready`); }} /></div></div>}
    {toast && <div data-testid="toast-message" className="fixed bottom-5 left-1/2 z-50 flex -translate-x-1/2 items-center gap-2 rounded-xl bg-sidebar px-4 py-3 text-xs font-bold text-sidebar-foreground shadow-xl"><Check className="h-4 w-4 text-sidebar-primary" />{toast}</div>}
  </div>;
}

function ProjectForm({ onCancel, onCreated }: { onCancel: () => void; onCreated: (project: Project) => Promise<void> }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [color, setColor] = useState('#5f8f77');
  const [saving, setSaving] = useState(false);
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!name.trim()) return;
    setSaving(true);
    const project = await kanbanService.createProject({ name: name.trim(), description: description.trim() || 'A focused place for the work ahead.', color });
    setSaving(false);
    await onCreated(project);
  };
  return <form onSubmit={submit} className="mt-6 space-y-4" data-testid="form-project"><label className="block text-xs font-bold">Project name<input data-testid="input-new-project-name" autoFocus required value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Launch planning" className="mt-1.5 h-11 w-full rounded-xl border border-input bg-background px-3 text-sm outline-none focus:border-primary" /></label><label className="block text-xs font-bold">What is this for?<textarea data-testid="input-new-project-description" value={description} onChange={(event) => setDescription(event.target.value)} rows={3} placeholder="The context that helps the team choose what matters." className="mt-1.5 w-full resize-none rounded-xl border border-input bg-background px-3 py-2 text-sm outline-none focus:border-primary" /></label><div><span className="text-xs font-bold">Signal color</span><div className="mt-2 flex gap-2">{['#5f8f77', '#c58b42', '#7a72ad', '#c7564b'].map((value) => <button type="button" key={value} data-testid={`button-project-color-${value.slice(1)}`} onClick={() => setColor(value)} className={`h-8 w-8 rounded-full ${color === value ? 'ring-2 ring-foreground ring-offset-2 ring-offset-background' : ''}`} style={{ backgroundColor: value }} />)}</div></div><div className="flex justify-end gap-2 border-t border-border pt-4"><Button type="button" variant="ghost" onClick={onCancel} data-testid="button-cancel-project">Cancel</Button><Button type="submit" disabled={saving} data-testid="button-create-project">{saving ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}Create project</Button></div></form>;
}

export default App;