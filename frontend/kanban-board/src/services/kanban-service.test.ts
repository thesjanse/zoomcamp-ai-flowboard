import { describe, expect, it } from 'vitest';

import { kanbanService } from './kanban-service';

const allFilters = {
  search: '',
  priorities: [],
  assigneeId: null,
  due: 'all' as const,
};

describe('kanbanService', () => {
  it('returns active and archived projects through the same service boundary', async () => {
    const projects = await kanbanService.listProjects();

    expect(projects).toHaveLength(3);
    expect(projects.find((project) => project.id === 'p1')?.archived).toBe(false);
    expect(projects.find((project) => project.id === 'p3')?.archived).toBe(true);
  });

  it('filters board cards by search, priority, assignee, and due state', async () => {
    const board = await kanbanService.getBoard('p1', {
      ...allFilters,
      search: 'empty states',
    });
    expect(board.cards.map((card) => card.id)).toEqual(['NST-138']);

    const assigned = await kanbanService.getBoard('p1', {
      ...allFilters,
      assigneeId: 'm2',
      priorities: ['urgent'],
    });
    expect(assigned.cards.map((card) => card.id)).toEqual(['NST-141']);
  });

  it('creates, updates, moves, and deletes a card', async () => {
    const created = await kanbanService.createCard('p2', {
      title: 'Test service persistence',
      description: 'A card created by the service contract test.',
      priority: 'medium',
      assigneeId: 'm1',
      dueDate: null,
      labels: ['Test'],
      columnId: 'c5',
    });

    expect(created.projectId).toBe('p2');
    expect(created.title).toBe('Test service persistence');

    const updated = await kanbanService.updateCard(created.id, {
      priority: 'urgent',
      columnId: 'c6',
    });
    expect(updated.priority).toBe('urgent');
    expect(updated.columnId).toBe('c6');

    const moved = await kanbanService.moveCard(created.id, 'c7');
    expect(moved.columnId).toBe('c7');

    await kanbanService.deleteCard(created.id);
    const board = await kanbanService.getBoard('p2', allFilters);
    expect(board.cards.some((card) => card.id === created.id)).toBe(false);
  });

  it('adds comments and exposes search results without a direct backend call', async () => {
    const comment = await kanbanService.addComment(
      'NST-141',
      'm1',
      'The service contract keeps this local.',
    );
    expect(comment.cardId).toBe('NST-141');
    expect(comment.body).toContain('local');

    const results = await kanbanService.search('Northstar');
    expect(results[0]).toMatchObject({
      type: 'project',
      id: 'p1',
    });
  });
});