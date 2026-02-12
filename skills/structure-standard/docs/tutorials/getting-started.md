# Getting Started with structure-standard

> **Type:** Tutorial (learning-oriented)
> **Time:** ~10 minutes
> **Prerequisites:** Bash shell, access to OpenClaw workspace

This tutorial walks you through validating and scaffolding projects using the structure-standard skill.

---

## What You'll Build

By the end, you'll have a properly structured project validated against OpenClaw standards.

---

## Step 1: Validate an Existing Project

Run the validation script against any project directory:

```bash
bash skills/structure-standard/scripts/validate-structure.sh ./my-project skill
```

This checks for required files like `SKILL.md`, `_meta.json`, and proper directory layout.

**Checkpoint:** You should see a list of ✓ passes and ✗ errors.

---

## Step 2: Scaffold a New Project

Create a new skill project from scratch:

```bash
bash skills/structure-standard/scripts/scaffold.sh skill my-new-skill .
```

This generates the standard directory structure:

```
my-new-skill/
├── SKILL.md
├── _meta.json
├── scripts/
└── references/
```

**Checkpoint:** The directory `./my-new-skill` exists with all template files.

---

## Step 3: Audit Your Filesystem

Run the full filesystem audit to check permissions and hygiene:

```bash
bash skills/structure-standard/scripts/audit-filesystem.sh --quiet
```

To auto-fix safe issues (permissions, stale backups):

```bash
bash skills/structure-standard/scripts/audit-filesystem.sh --fix
```

**Checkpoint:** You see a score and list of any remaining issues.

---

## What You Learned

- How to validate project structure against standards
- How to scaffold new projects with correct layout
- How to audit and fix filesystem hygiene issues

## Next Steps

- Explore `enforce-permissions.sh` for permission management
- Use `cleanup-stale.sh` to remove old backups and logs
- Read the [SKILL.md](../../SKILL.md) for full reference
