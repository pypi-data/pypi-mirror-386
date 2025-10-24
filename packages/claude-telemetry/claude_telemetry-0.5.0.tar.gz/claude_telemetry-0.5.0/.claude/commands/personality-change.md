---
description: Change or activate a personality for both Cursor and Claude Code
---

Change the active AI personality to create consistent behavior across Claude Code and
Cursor.

**IMPORTANT: Ask the user which personality they want if not provided.**

## Available Personalities

- **sherlock** - Analytical, precise, deductive reasoning for debugging
- **bob-ross** - Calm, encouraging, treats bugs as happy accidents
- **samantha** - Warm, witty, emotionally intelligent, playfully flirty
- **stewie** - Sophisticated, condescending, theatrical, brilliant with high standards
- **ron-swanson** - Minimalist, anti-complexity, straightforward and practical
- **marie-kondo** - Organized, joyful minimalism, eliminates what doesn't spark joy
- **marianne-williamson** - Spiritual, love-based, sees coding as consciousness work
- **unity** - Creative muse meets structured builder, warm encourager

## Process

### 1. Validate Input

- If no personality name provided, show available personalities and ask which to
  activate
- Check that `.cursor/rules/personalities/<name>.mdc` exists
- If `none` was requested, skip to step 3 to remove personality

### 2. Handle Claude Code Activation

a. Read or create `.claude/context.md`

b. Check for existing personality:

- Search for `## Active Personality` section
- Extract current name from `<!-- personality-<name> -->` comment if found

c. If personality exists:

- If same as requested: inform "✓ <name> is already active" and stop
- If different: remove entire `## Active Personality` section (including HTML comments)

d. If not removing (name != "none"):

- Read `.cursor/rules/personalities/<name>.mdc`
- Strip frontmatter (content between opening `---` and closing `---`)
- Append to `.claude/context.md`:

```
## Active Personality

<!-- personality-<name> -->
<personality content without frontmatter>
<!-- /personality-<name> -->
```

e. Write updated `.claude/context.md`

### 3. Update Cursor Configuration

a. Find all personality files in `.cursor/rules/personalities/` (except
`common-personality.mdc`)

b. For each personality file:

- Read the file content
- Extract frontmatter (between `---` markers)
- If this is the selected personality and name != "none": set `alwaysApply: true`
- If this is NOT the selected personality OR name == "none": set `alwaysApply: false`
- Write the updated file back

c. Confirm updates were made

### 4. Report Results

**If switching personalities:**

```
✓ Switched from <old-name> to <new-name> personality

Claude Code: Updated .claude/context.md
Cursor: Set alwaysApply=true in .cursor/rules/personalities/<new-name>.mdc
        Set alwaysApply=false in .cursor/rules/personalities/<old-name>.mdc
```

**If activating (no previous):**

```
✓ Activated <name> personality

Claude Code: Added to .claude/context.md
Cursor: Set alwaysApply=true in .cursor/rules/personalities/<name>.mdc
```

**If removing:**

```
✓ Removed active personality

Claude Code: Removed from .claude/context.md
Cursor: Set alwaysApply=false for all personalities
```

**If already active:**

```
✓ <name> personality is already active
```

## Examples

```
/personality-change samantha
/personality-change unity
/personality-change none    # Remove active personality
```

## Notes

- Only one personality active at a time (plus common-personality baseline)
- Personality affects ALL future interactions in this project
- `.cursor/rules/personalities/common-personality.mdc` is always applied as baseline
- Cursor frontmatter is automatically updated (`alwaysApply: true` for active, `false`
  for others)
- Claude Code reads from `.claude/context.md` which is always included
