# Taxonomy System

This directory contains the tag taxonomy system for portfolio projects.

## Files

### `master_tags.json`
**Master list of approved tags.** This is the source of truth for all project tags.

- Organized by category (medium, technology, gaming, etc.)
- Includes hierarchical relationships (e.g., `audio` → `audio/spatial`)
- Maps tags to work.html filters
- Defines semantic relationships for similarity scoring

### `tag_descriptions.json`
**Detailed descriptions for LLM tagging.** Helps AI understand when to apply each tag.

- Natural language explanation of each tag
- Examples of correct usage
- Selection strategy guidelines

### `new_tags_pending.json`
**Queue for new tag proposals.** When build script encounters concepts not in master list.

- Holds new tags for review
- Track rejected tags to avoid re-suggesting
- Approved tags get moved to master_tags.json

## Workflow

### 1. Tagging a New Project

```bash
# LLM suggests tags based on master_tags.json
python build_smart.py --tag-project "New Project.md"

# If new tag proposed:
# → Adds to new_tags_pending.json
# → You review and approve/reject
```

### 2. Approving New Tags

```bash
# Review pending tags
python build_smart.py --review-tags

# Approve a tag
python build_smart.py --approve-tag "#VR"

# Tag moves to master_tags.json
# Script offers to check all existing projects for relevance
```

### 3. Propagating Tags

When a new tag is approved, optionally check if it applies to existing projects:

```bash
python build_smart.py --propagate-tag "#VR"

# Output:
# Checking 31 projects...
# ✓ Project A (85% match) - Add tag? [y/N]
# ✗ Project B (30% match) - skipped
```

## Tag Guidelines

### Hierarchical Tags
Use `/` for specific subtypes:
- `audio` → `audio/spatial`
- `3d` → `3d/print`, `3d/modeling`
- `game` → `game/map`, `game/cosmetics`

### Tag Count
- **3-7 tags per project** for optimal balance
- Too few: Poor discoverability
- Too many: Diluted relevance

### Naming Convention
- **Lowercase** for consistency
- **No spaces** - use `/` or `-` for compound terms
- **Descriptive** - clear meaning without context

### When to Create New Tags
✅ **Create new tag when:**
- New technology/medium emerges (e.g., VR, AR)
- Recurring theme not covered by existing tags
- Specific game/tool becomes focus of multiple projects

❌ **Don't create new tag for:**
- One-off concepts (use existing approximate tag)
- Overly specific details (use description field)
- Redundant terms (check if existing tag works)

## Related Projects System

Tags power the "Related Projects" section on project pages:

1. **Manual curation** (preferred): Use `related-projects::` field in markdown
2. **Auto-similarity**: Calculate tag overlap + semantic relationships
3. **Display**: Show 2-4 most related projects with matching tags visible

### Similarity Algorithm

```
Score = (matching_tags / total_tags) × weights
- Exact match: 1.0
- Hierarchical parent/child: 0.7
- Same cluster: 0.5
- Bonus for specific tags (game names, etc.): +0.3
```

## Version History

- **1.0** (2025-10-29): Initial taxonomy system
  - Standardized narrative tags (spoken/written/interactive)
  - Standardized 3D tags (3d/print, 3d/modeling)
  - Changed `gamer` → `player`
  - Removed `oneday` (use date metadata)
  - Added `collaboration` tag

## Maintenance

### Regular Tasks
- **Monthly**: Review new_tags_pending.json
- **Per project**: Tag new work immediately
- **Annually**: Audit tag usage, consolidate rarely-used tags

### Quality Checks
```bash
# List unused tags
python build_smart.py --audit-tags --show-unused

# Find projects with too few/many tags
python build_smart.py --audit-tags --check-counts

# Check for deprecated tags still in use
python build_smart.py --audit-tags --check-deprecated
```

