## Context

The current settings page uses a tab-based navigation pattern with three tabs: LLM Providers, Database, and External Tools. This creates unnecessary navigation overhead and fragments related configuration. The LLM provider system uses `is_primary` and `is_fallback` boolean flags to manage provider selection, which adds complexity. Additionally, database configuration is exposed in the UI, creating security risks and violating 12-factor app principles.

The system is built with React + TypeScript frontend using Zustand for state management, and FastAPI backend with PostgreSQL database. The LLM factory pattern already supports multiple providers with fallback logic.

## Goals / Non-Goals

**Goals:**
- Simplify settings UX by consolidating all settings into a single scrollable page with collapsible sections
- Reduce cognitive load by replacing primary/fallback model with single default model concept
- Improve security by removing database configuration from UI and moving to environment variables only
- Fix styling bug where form labels are invisible due to missing text color classes
- Maintain backward compatibility through database migration for existing provider configurations

**Non-Goals:**
- Changing the underlying LLM factory fallback/retry logic (keep existing reliability features)
- Adding new settings categories or configuration options
- Redesigning the visual appearance beyond layout structure
- Modifying external tools configuration (remains read-only)

## Decisions

### Decision 1: Single-page collapsible sections over tabs

**Rationale:** Tabs hide content and require navigation clicks. With only 2-3 setting categories (after removing database), a single page with collapsible sections provides better overview and reduces clicks. Users can expand multiple sections simultaneously for comparison.

**Alternatives considered:**
- Keep tabs: Rejected because it fragments the UI unnecessarily for small number of categories
- Sidebar navigation: Rejected as over-engineering for 2-3 sections
- Accordion (only one section open): Rejected because users may want to compare settings across sections

**Implementation:** Use React state to track expanded/collapsed state per section. Store state in localStorage for persistence across reloads. Default to all sections expanded on first visit.

### Decision 2: Replace is_primary/is_fallback with is_default

**Rationale:** The primary/fallback concept is confusing for users. Most users just want "which model should the system use by default?" The backend can still maintain fallback logic internally by treating enabled non-default providers as fallback options.

**Alternatives considered:**
- Keep primary/fallback: Rejected due to user confusion and unnecessary complexity in UI
- Remove fallback entirely: Rejected because fallback provides valuable reliability
- Add priority ordering: Rejected as over-engineering; simple default + enabled is sufficient

**Implementation:**
- Frontend: Replace `is_primary`/`is_fallback` checkboxes with single `is_default` radio button group
- Backend: Update `llm_factory.py` to use `is_default` flag, treat other enabled providers as fallback chain
- Database: Migration to rename columns and set `is_default = is_primary` for existing records

### Decision 3: Remove database config UI entirely

**Rationale:** Database connection strings contain sensitive credentials and should never be exposed in a web UI. Infrastructure configuration belongs in environment variables per 12-factor app methodology. This also simplifies deployment and reduces attack surface.

**Alternatives considered:**
- Keep UI but add encryption: Rejected because it's still wrong layer for infrastructure config
- Make read-only: Rejected because it provides no value if not editable
- Move to separate admin CLI: Rejected as unnecessary; .env is standard practice

**Implementation:**
- Delete `DatabaseConfig.tsx` component
- Remove database-related methods from `settingsStore.ts`
- Remove database config API endpoints from backend
- Document all database environment variables in `.env.example`
- Update `CLAUDE.md` to reflect .env-only approach

### Decision 4: Fix form label styling with text-text-main class

**Rationale:** The modal uses dark background (`bg-bg-surface: #1e293b`) but form labels don't specify text color, causing them to default to dark text on dark background. Adding `text-text-main` class ensures proper contrast.

**Alternatives considered:**
- Change modal background: Rejected because dark theme is intentional design
- Use inline styles: Rejected because Tailwind classes are the project standard
- Create new label component: Rejected as over-engineering for simple fix

**Implementation:** Add `text-text-main` to all `<label>` elements in `LLMProviderForm.tsx` (lines 83, 94, 108, 119, 130).

## Risks / Trade-offs

**[Risk]** Users with existing primary/fallback configurations may be confused by the change
→ **Mitigation:** Migration automatically converts primary to default. Add UI hint showing "默认" badge clearly. Document change in release notes.

**[Risk]** Removing database UI may frustrate users who want to change database config
→ **Mitigation:** This is intentional. Document in `.env.example` and `CLAUDE.md` that database config is environment-only. This is standard practice and improves security.

**[Risk]** Single-page layout may feel cluttered with many settings
→ **Mitigation:** Currently only 2 sections (LLM + Tools), which is manageable. Collapsible sections prevent clutter. If more settings are added later, can revisit layout.

**[Risk]** localStorage for section state may not sync across browser tabs
→ **Mitigation:** Acceptable trade-off. Section state is low-stakes preference, not critical data. Users can easily re-expand sections if needed.

**[Trade-off]** Backend still maintains fallback logic but UI doesn't expose it explicitly
→ **Rationale:** This is intentional simplification. Power users don't need to configure fallback order; system automatically tries enabled providers in order. Reduces cognitive load for 90% of users.

## Migration Plan

**Database Migration:**
1. Create migration script to add `is_default` column to `settings` table
2. Set `is_default = is_primary` for all existing LLM provider records
3. Drop `is_primary` and `is_fallback` columns after data migration
4. Add unique constraint on `is_default = true` per setting type

**Deployment Steps:**
1. Deploy backend changes first (backward compatible - reads both old and new columns)
2. Run database migration
3. Deploy frontend changes
4. Update `.env.example` with database connection variables
5. Update documentation (`CLAUDE.md`)

**Rollback Strategy:**
- If issues arise, revert frontend deployment (backend remains compatible)
- Database migration is one-way; rollback requires manual SQL to restore columns
- Keep backup of `settings` table before migration

## Open Questions

None - design is straightforward and well-scoped.
