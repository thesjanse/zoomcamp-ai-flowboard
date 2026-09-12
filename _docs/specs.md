# Kanban Project Management App — MVP Specification

## 1. Product Overview

A responsive web-based Kanban project-management application for individuals and small teams.

The core experience is:

**Dashboard → My Tasks → Project → Kanban Board → Card**

The MVP intentionally avoids feature bloat and focuses on projects, cards, collaboration, dependencies, search, and rich-text content.

---

## 2. MVP Decisions

### 2.1 Authentication & Users

- An account is required to use the application.
- Authentication uses **email + password** only.
- No social login in the MVP.
- User profile consists of:
  - Name
  - Email
- Users can change their email and password.
- Users can delete their account, but must transfer their projects first.
- No user avatar or bio.
- English only.

### 2.2 Dashboard

The dashboard prioritizes **My Tasks**.

Users can filter their assigned cards by:

- Project
- Status
- Priority
- Due date

Active projects are shown normally.

Archived projects are **not shown in the normal project list** and can be accessed through search.

The dashboard shows project names only; it does not show project descriptions, icons, colors, IDs, or project-level due dates.

### 2.3 Projects

- Users can create an unlimited number of projects.
- Projects are private by default.
- A project has exactly **one Kanban board**.
- Project creation includes:
  - Name
  - Description
  - Members
  - Starting columns
- There are no project templates.
- There are no project IDs.
- There are no project icons or colors.
- There is no project-level due date.

#### Default columns

New projects start with:

1. To Do
2. In Progress
3. Done

Columns can be customized after creation.

Maximum number of columns: **7**.

Admins can:

- Rename columns
- Reorder columns
- Add columns
- Delete columns

### 2.4 Project Membership & Administration

- Members join through an **expiring invite link**.
- There is no fixed project member limit.
- The creator is automatically the first admin.
- There is no separate owner role.
- The creator can transfer admin rights at any time.
- Admins can designate additional admins.
- Only the creator can remove an admin.
- Admins can remove regular members.
- Any member can leave a project.
- If the creator leaves, they must designate another admin first.
- If the creator is the last member, the project is closed and archived.
- Any person with original project access can restore an archived project.
- Archived projects remain indefinitely.
- Admins can permanently delete archived projects manually.

### 2.5 Cards

A card contains:

- Unique card ID
- Title
- Rich-text description
- Creator
- Assignee
- Due date
- Priority
- Comments
- Blocking relationships

#### Card IDs

- IDs are sequential within each project.
- Deleted IDs are never reused.
- Example: `WEB-1`, `WEB-2`, `WEB-3`.
- Moving a card to another project generates a new ID in the destination project.

#### Titles

- Duplicate card titles are allowed.

#### Assignee

- Each card has exactly one assignee.
- The assignee must be a member of the card's current project.

#### Dates

- Cards have an optional due date.
- Due dates are date-only.
- No time component.
- No start date.

#### Priority

Priority values:

1. Critical
2. Major
3. Normal
4. Low

Default priority: **Normal**.

#### Card operations

Cards:

- Can be dragged between columns.
- Can be reordered within a column using drag-and-drop.
- Can also have their status changed through a status dropdown.
- Auto-save every change.
- Cannot be duplicated.
- Cannot be archived.
- Can be moved between projects by any project member.

### 2.6 Kanban Board

- Drag-and-drop is a core interaction.
- Status dropdown is also available.
- Card order is shared across all users.
- Changes save automatically.
- No undo/redo.
- No real-time collaboration.
- Users must refresh to see changes made by others.
- Each column displays a simple card count.
- A soft warning appears when a column contains more than **20 cards**.
- There is no hard card limit.

#### Board filters

Users can filter the board by:

- Assignee
- Priority
- Due date

No automatic sorting is provided.

Card ordering is manual only.

### 2.7 Moving Cards Between Projects

Any member can move a card to another project they belong to.

When moving a card:

- If the destination project contains the same column/status, retain that status.
- If it does not, move the card to **To Do**.
- Generate a new card ID in the destination project.
- Move all comments with the card.
- Preserve the card's other compatible data.

#### Recommended rule for assignees

If the current assignee is not a member of the destination project:

> Require the user to select a valid destination-project member before completing the move.

This prevents cards from having invalid assignees.

### 2.8 Rich Text

Descriptions and comments use the same rich-text capabilities.

Supported features:

- Bold
- Italic
- Lists
- Links
- Headings
- Code blocks

No tables, embedded images, or attachments in the MVP.

### 2.9 Comments

- Comments are flat; no threads/replies.
- @mentions are supported.
- Typing `@` provides member autocomplete.
- Mentions do not generate notifications.
- Users can edit their own comments.
- Edited comments display an **edited** indicator.
- Comments cannot be deleted.
- Comments show exact date + time timestamps.

#### Recommended behavior for deleted users

If a user is removed from a project or deletes their account, existing comments should remain as historical content. The author's display name should be preserved where possible rather than deleting the comment.

### 2.10 Dependencies / Relationships

Cards support a **blocking** relationship.

A card can block multiple cards.

A card can be blocked by multiple cards.

Card details display:

- **Blocked by**
- **Blocks**

There is intentionally **no special visual "Blocked" state** on cards.

#### Deleting a card with relationships

If a card has relationships, deletion requires the user to choose:

1. Remove all relationships, or
2. Reconnect the relationships to another card.

Recommended UX:

- Show the affected relationships clearly.
- Do not silently destroy relationships.
- Require explicit confirmation.

### 2.11 Search

Search covers:

- Projects
- Cards

Search is also the primary way to find archived projects.

Recommended search behavior:

- Search card titles, card IDs, and project names.
- Also search project descriptions and card descriptions.
- Do not search comments in the MVP.
- Results should respect the user's access permissions.

### 2.12 Notifications

There are **no notifications in the MVP**.

Excluded:

- Assignment notifications
- Mention notifications
- Due-date reminders
- Activity notifications
- Email notifications

### 2.13 Activity / History

There is no project activity feed.

No user-facing change history is required in the MVP.

### 2.14 Attachments

No attachments are supported.

This includes:

- Files
- Images
- Documents

### 2.15 Checklists / Subtasks

No checklists or nested subtasks.

### 2.16 Project Lifecycle

Active projects can be closed by the creator leaving as the last member.

Closed projects become **Archived**.

Archived projects:

- Are preserved indefinitely.
- Do not appear in the normal project list.
- Can be found through search.
- Can be restored by users with original project access.
- Can be permanently deleted manually by an admin.

#### Recommended archive semantics

Archive should preserve the entire project state, including:

- Columns
- Cards
- Card order
- Comments
- Relationships
- Membership/access metadata

Restoring should return the project to its previous state.

### 2.17 Project Deletion

Admins can delete projects.

Deletion moves the project to Archived rather than immediately destroying it.

Archived projects can be permanently deleted manually by admins.

There is no automatic deletion after 30/90/365 days.

#### Recommended permanent-delete warning

Permanent deletion should require an explicit confirmation and clearly state that the project and all associated data will be permanently destroyed.

### 2.18 Responsive UI & Theme

- Responsive web application.
- Desktop and mobile web supported.
- User-selectable light/dark theme.
- No keyboard shortcuts.
- No online presence indicator.

---

# 3. Permission Model

## Regular Member

Can:

- View project
- Create cards
- Edit cards
- Move cards
- Assign cards to project members
- Comment
- Edit their own comments
- Move cards between projects they belong to
- Leave project

Cannot:

- Edit project settings
- Manage admins
- Remove other members
- Permanently delete archived projects

## Admin

Everything a regular member can do, plus:

- Edit project name
- Edit project description
- Add/remove members
- Modify columns
- Designate admins
- Remove regular members
- Delete/archive the project
- Permanently delete archived projects

## Creator

The creator starts as an admin and additionally:

- Can transfer admin rights.
- Is the only user who can remove another admin.
- Must designate another admin before leaving if other members remain.

If the creator is the last member, the project is archived.

---

# 4. Recommended Clarifications for Blurry Areas

The following decisions were not explicitly specified but should be fixed before implementation.

## 4.1 Invite Link Expiration

**Recommendation: 7 days.**

Admins can generate a new link after expiration.

Generating a new link should invalidate the previous link.

## 4.2 Column Deletion

**Recommendation: require reassignment of cards.**

An admin cannot delete a column containing cards until all cards are moved to another column.

The UI should provide a destination-column selector as part of deletion.

## 4.3 Maximum Columns

The maximum is **7 columns total**.

The UI should prevent creation of an eighth column.

## 4.4 Minimum Columns

**Recommendation: require at least 1 column.**

A project should never have zero columns.

## 4.5 Required Project Name

**Recommendation: project name is required and must not be blank.**

Description remains optional.

## 4.6 Required Card Title

**Recommendation: card title is required and must not be blank.**

Description remains optional.

## 4.7 Card Creator Changes

The creator is recorded automatically but can be changed.

**Recommendation: only admins should be able to change the creator field.**

This preserves useful provenance while honoring the chosen ability to change it.

## 4.8 Card Deletion

Earlier we established that cards are deleted immediately, but relationship-bearing cards require a relationship decision.

**Recommendation:**

- Card with no relationships → delete immediately.
- Card with relationships → show relationship-resolution dialog, then delete after the user chooses how to handle them.

There should be no card trash/recycle bin.

## 4.9 Destination Project Assignee

When moving a card between projects:

- If the assignee belongs to the destination project → preserve assignee.
- If not → require selecting a destination-project member.
- Do not allow an invalid assignee.

## 4.10 Card Priority When Moving Projects

**Recommendation: preserve priority.**

Priority is card-level data and does not depend on the project.

## 4.11 Due Date When Moving Projects

**Recommendation: preserve due date.**

If a due date is already set, moving the card should not remove it.

## 4.12 Blocking Relationships Across Projects

**Recommendation: allow only same-project blocking relationships.**

When a card moves to another project, its blocking relationships should be resolved during the move.

Recommended move dialog:

- Show relationships that cannot remain.
- Allow the user to remove them or reconnect them to cards in the destination project.
- Do not silently create cross-project dependencies.

This keeps the data model simple for the MVP.

## 4.13 Moving Cards Into Archived Projects

**Recommendation: do not allow it.**

Archived projects are read/restore targets, not active destinations.

A card may only be moved into an active project.

## 4.14 Restoring Archived Projects

**Recommendation: restoration should require the user to still have valid access to the project.**

If the user's original membership was removed or their account no longer exists, they should not be able to restore the project solely because they once had access.

For practical MVP implementation, preserve former membership records as historical access metadata and define restoration eligibility explicitly.

## 4.15 Archived Project Search

Search results should clearly distinguish:

- Active project
- Archived project

Opening an archived project should present a read-only state until restored.

## 4.16 Project Admin Rules

Recommended consistent permission rules:

- Creator can designate admins.
- Any admin can designate another admin.
- Only creator can remove an admin.
- Admins cannot remove the creator.
- Creator can transfer admin rights.
- A project must always have at least one admin while it has members.

## 4.17 Leaving Projects

For a regular member:

> Leave immediately.

For an admin who is not the creator:

> Leave immediately if another admin remains.

For the creator:

> If other members remain, designate another admin first.

If creator is the last member:

> Archive the project.

## 4.18 Account Deletion

Before deleting an account:

- User must transfer any projects they administer.
- After transfer, their account can be deleted.
- Their comments should remain as historical content.
- Cards they created should retain their creator information where possible; if the user record is removed, display a neutral deleted-user representation.

## 4.19 Rich Text Security

**Recommendation: sanitize all rich text on the server.**

Do not trust HTML generated by the browser/editor.

Allow only the explicitly supported formatting elements.

Links should be sanitized to prevent unsafe protocols and scripts.

## 4.20 Search Permissions

**Recommendation: enforce authorization at the backend.**

Search must never return projects/cards a user does not have access to.

This applies especially to archived projects.

## 4.21 Date & Time Handling

Due dates are date-only.

Comment timestamps are date + time.

**Recommendation: store comment timestamps in UTC and render them in the user's local timezone.**

Due dates should be stored as calendar dates without timezone conversion.

## 4.22 Card Order

The board has one shared order.

**Recommendation: store an explicit ordering value per card within its column.**

Do not derive order from creation date.

When a card is moved/reordered, update the ordering value automatically.

## 4.23 Concurrent Editing

Because there is no real-time collaboration:

**Recommendation: use last-write-wins for normal edits**, while avoiding unnecessary destructive overwrites.

For example, board movement can simply persist the latest state. Rich-text edits should save when submitted/blurred rather than on every keystroke.

## 4.24 Mobile Kanban UX

Drag-and-drop can be awkward on touch devices.

**Recommendation:**

- Keep drag-and-drop where practical.
- Always provide the status dropdown as the reliable mobile alternative.
- Card reordering on mobile may use explicit move controls if touch drag-and-drop proves unreliable.

---

# 5. Core Data Model

Recommended entities:

## User

- id
- name
- email
- password_hash
- created_at
- updated_at

## Project

- id
- name
- description
- status (`active`, `archived`)
- creator_id
- created_at
- updated_at
- archived_at
- archived_by

## ProjectMember

- project_id
- user_id
- role (`admin`, `member`)
- joined_at
- left_at

## ProjectInvite

- id
- project_id
- token_hash
- created_by
- expires_at
- revoked_at
- created_at

## Column

- id
- project_id
- name
- position
- created_at
- updated_at

## Card

- id
- project_id
- card_number
- title
- description_rich_text
- creator_id
- assignee_id
- due_date
- priority
- column_id
- position
- created_at
- updated_at

Card ID can be rendered from the project's prefix plus `card_number`.

## Comment

- id
- card_id
- author_id
- body_rich_text
- created_at
- updated_at
- edited_at

Comments are immutable with respect to deletion, but authors can edit their own comments.

## CardRelationship

- id
- source_card_id
- target_card_id
- relationship_type

For the MVP, the relationship type is effectively:

`blocks`

A source card blocks a target card.

---

# 6. Important Database Constraints

Recommended constraints:

- Project member `(project_id, user_id)` must be unique.
- Card number must be unique within a project.
- Deleted card numbers must not be reused.
- Card position must be unique enough to maintain deterministic ordering.
- A card's assignee must belong to its project.
- A card relationship cannot point to itself.
- Duplicate identical relationships should be prevented.
- Column count per project cannot exceed 7.
- Project must contain at least one column.
- Project name cannot be blank.
- Card title cannot be blank.
- Invite tokens should be stored hashed, not plaintext.
- Search queries must be authorization-filtered.

---

# 7. MVP Screen Map

## Authentication

- Sign up
- Log in
- Change password
- Change email
- Delete account

## Dashboard

- My Tasks
- Filters:
  - Project
  - Status
  - Priority
  - Due date
- Project list
- Search

## Project

- Project header
- Kanban board
- Column management
- Project settings
- Members/admin management
- Invite link
- Search

## Card

- Card title
- Card ID
- Description
- Priority
- Assignee
- Due date
- Creator
- Status
- Blocked by
- Blocks
- Comments
- Edit/delete controls

## Archived

- Search-accessible archived project
- Restore
- Permanent delete for admins

---

# 8. MVP Non-Goals

Do not implement unless requirements change:

- Real-time collaboration
- WebSockets/live presence
- Notifications
- Email notifications
- Activity feeds
- Attachments
- Images/files
- Checklists
- Subtasks
- Threads
- Card duplication
- Card archiving
- Undo/redo
- Keyboard shortcuts
- Favorites
- Templates
- Social login
- Localization
- Multiple boards per project
- Project colors/icons
- Project IDs
- Project due dates
- Card start dates
- Card time-based due dates

---

# 9. Product Principles

1. **Fast board interaction** — creating and moving cards should be lightweight.
2. **Simple collaboration** — shared projects without complex permission hierarchies.
3. **Predictable data ownership** — project access controls all project content.
4. **Minimal notifications** — intentionally none in MVP.
5. **Simple dependencies** — blocking relationships without a complex dependency engine.
6. **Strong data preservation** — archives are durable and restorable.
7. **Mobile accessibility** — every drag-and-drop action should have a non-drag alternative.
8. **Security by default** — private projects and backend authorization.
9. **No unnecessary feature expansion** — preserve the focused MVP.

---

# 10. Final MVP Definition

The MVP is complete when a user can:

1. Create an account and log in.
2. Create a private project.
3. Invite members using an expiring link.
4. Configure up to 7 Kanban columns.
5. Create and manage cards.
6. Assign cards to members.
7. Set priority and due dates.
8. Move and reorder cards.
9. Filter their tasks and board cards.
10. Search projects and cards.
11. Write rich-text descriptions and comments.
12. Mention members in comments.
13. Create and manage blocking relationships.
14. Move cards between projects.
15. Manage project admins and members according to the permission model.
16. Archive and restore projects.
17. Permanently delete archived projects as an admin.
18. Use the application responsively on desktop and mobile.
19. Choose light or dark theme.

This specification represents the agreed MVP scope plus recommended resolutions for previously ambiguous behavior.
