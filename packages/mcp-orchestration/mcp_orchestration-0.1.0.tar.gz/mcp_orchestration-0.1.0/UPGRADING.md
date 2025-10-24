# Upgrading mcp-orchestration

**Project**: mcp-orchestration
**Generated with**: chora-base 942644b0feb0bb4e0497e100125c98704e0f31af
**Package**: mcp_orchestration

---

## Quick Reference

### Check for Updates

```bash
# See what version you're currently on
cat .copier-answers.yml | grep _commit

# Check latest chora-base version
# Visit: https://github.com/liminalcommons/chora-base/releases

# Update to specific version
copier update --vcs-ref vX.Y.Z --trust

# Update to latest
copier update --trust
```

### Before Upgrading

**Always create backup before upgrading:**

```bash
# 1. Commit all changes
git add -A
git commit -m "Pre-upgrade snapshot: $(date +%Y-%m-%d)"

# 2. Create backup branch
git branch backup-pre-upgrade-$(date +%Y%m%d)

# 3. Create backup tag
git tag backup-$(cat .copier-answers.yml | grep _commit | awk '{print $2}')

# 4. Verify clean state
git status
# Should show: "nothing to commit, working tree clean"
```

### Upgrade Resources

- **Upgrade Philosophy**: https://github.com/liminalcommons/chora-base/blob/main/docs/upgrades/PHILOSOPHY.md
- **Version-specific guides**: https://github.com/liminalcommons/chora-base/tree/main/docs/upgrades
- **CHANGELOG**: https://github.com/liminalcommons/chora-base/blob/main/CHANGELOG.md

---

## Customization Tracking

**Purpose**: Document customizations for easier merging during upgrades

### Customized Files

Track which template files you've modified and why:

#### Scripts

- [ ] `scripts/setup.sh` - Customization: [describe]
- [ ] `scripts/check-env.sh` - Customization: [describe]
- [ ] `scripts/smoke-test.sh` - Customization: [describe]
- [ ] `scripts/integration-test.sh` - Customization: [describe]
- [ ] `scripts/diagnose.sh` - Customization: [describe]
- [ ] `scripts/handoff.sh` - Customization: [describe]
- [ ] `scripts/mcp-tool.sh` - Customization: [describe]
- [ ] Other: [file] - Customization: [describe]

#### Documentation

- [ ] `README.md` - Customization: [describe sections added/modified]
- [ ] `AGENTS.md` - Customization: [describe sections added/modified]
- [ ] `CONTRIBUTING.md` - Customization: [describe]
- [ ] Other: [file] - Customization: [describe]

#### Task Automation

- [ ] `justfile` - Custom tasks: [list task names]
  - `task-name`: [purpose]
  - `another-task`: [purpose]

#### Configuration

- [ ] `pyproject.toml` - Customization: [dependencies added, config changed]
- [ ] `.pre-commit-config.yaml` - Customization: [hooks added/modified]
- [ ] `.env.example` - Customization: [variables added]
- [ ] Other: [file] - Customization: [describe]

#### Source Code

Note: Source code is yours to customize freely. This section tracks template-generated code that you've modified.

- [ ] `src/mcp_orchestration/__init__.py` - Customization: [describe]
- [ ] `src/mcp_orchestration/memory/__init__.py` - Customization: [describe]
- [ ] `src/mcp_orchestration/memory/trace.py` - Customization: [describe]
- [ ] Other: [file] - Customization: [describe]

---

## Upgrade History

### Template Version History

Track your upgrade path for reference:

| Date | From Version | To Version | Notes |
|------|--------------|------------|-------|
| 2025-10-24 | - | 942644b0feb0bb4e0497e100125c98704e0f31af | Initial generation |

**Example entries** (fill in as you upgrade):
```
| 2025-10-20 | v1.3.1 | v1.4.0 | Adopted just --list, configured PyPI (token method) |
| 2025-11-15 | v1.4.0 | v1.5.0 | [describe major changes] |
```

### Major Customization Changes

Track significant customization work:

| Date | File(s) | Change | Reason |
|------|---------|--------|--------|
| 2025-10-24 | [file] | [change] | [reason] |

**Example entries**:
```
| 2025-10-21 | scripts/diagnose.sh | Added API key validation | Project needs ANTHROPIC_API_KEY |
| 2025-10-22 | AGENTS.md | Added custom task section | Document project-specific workflows |
```

---

## Upgrade Workflow

### Standard Upgrade Process

**1. Preparation** (5 minutes):
```bash
# Commit current state
git add -A
git commit -m "Pre-upgrade snapshot"

# Create backup
git branch backup-pre-upgrade-$(date +%Y%m%d)
git tag backup-$(cat .copier-answers.yml | grep _commit | awk '{print $2}')

# Review customizations (update this file if needed)
cat UPGRADING.md
```

**2. Research** (10-30 minutes):
```bash
# Check target version
TARGET_VERSION="v1.X.Y"

# Read upgrade guide
# Visit: https://github.com/liminalcommons/chora-base/blob/main/docs/upgrades/vOLD-to-vNEW.md

# Read CHANGELOG
# Visit: https://github.com/liminalcommons/chora-base/blob/main/CHANGELOG.md#XY

# Evaluate:
# - Does this upgrade fix critical issues? (required)
# - Do new features benefit this project? (value)
# - What files will conflict with customizations? (cost)
# - What workflow changes are advocated? (displacement)
```

**3. Execution** (15-60 minutes):
```bash
# Run upgrade
copier update --vcs-ref $TARGET_VERSION --trust

# Answer any new prompts
# [copier will prompt for new variables]

# Review changes
git status
git diff

# Resolve conflicts (if any)
# See upgrade guide for merge strategies
```

**4. Validation** (10-30 minutes):
```bash
# Check environment
just check  # or: ./scripts/check-env.sh

# Run tests
just test   # or: pytest

# Run full validation
just pre-merge  # or: ./scripts/pre-merge.sh
# Verify customizations preserved
# Check files listed in "Customized Files" section above
# Ensure your changes are still present
```

**5. Documentation** (5-10 minutes):
```bash
# Update UPGRADING.md
# Add entry to "Template Version History" table
# Document any new customizations

# Commit upgrade
git add .
git commit -m "chore: Upgrade to chora-base $TARGET_VERSION

- Updated from vOLD to $TARGET_VERSION
- [List major changes]
- Preserved customizations: [list]
- All tests passing

See docs/upgrades/vOLD-to-vNEW.md for details"
```

---

## Merge Conflict Resolution

### When Conflicts Occur

**Copier may show conflicts when both you and the template changed the same file.**

**General Strategy**:
1. **Understand the conflict**: What did template change? What did you customize?
2. **Choose approach**:
   - **Accept template**: If template fix is critical and you can re-apply customization
   - **Keep local**: If customization is essential and template change is optional
   - **Merge both**: Combine template improvement with local customization (preferred)
3. **Document decision**: Add entry to "Major Customization Changes" table
4. **Validate**: Run tests/scripts to ensure both changes work together

### Common Conflicts

#### Conflict: README.md (Documentation)

**Template likely changed**: Development section, features list
**You likely changed**: Project description, usage examples

**Strategy**: Keep both
- Accept template structural improvements
- Re-add your custom content in appropriate sections
- Use subsections to separate template vs custom content

#### Conflict: AGENTS.md (AI Instructions)

**Template likely changed**: Added new sections (Task Discovery, memory troubleshooting)
**You likely changed**: Added project-specific tasks

**Strategy**: Merge sections
- Accept template's new sections
- Keep your custom task sections
- Use clear section headers to separate

#### Conflict: justfile (Task Automation)

**Template likely changed**: Improved existing tasks, added new common tasks
**You likely changed**: Added project-specific tasks

**Strategy**: Combine
```bash
# 1. Accept template version
git checkout --theirs justfile

# 2. Re-add your custom tasks at bottom
cat >> justfile <<'EOF'

# === Project-Specific Tasks ===

your-custom-task:
    @echo "Running custom task..."
    [your logic]
EOF

# 3. Verify
just --list
# Should show both template AND custom tasks
```

#### Conflict: scripts/* (Automation)

**Template likely changed**: Bug fixes, improved error handling
**You likely changed**: Added project-specific checks

**Strategy**: Merge improvements
1. Review template changes: `git diff --theirs scripts/file.sh`
2. Review your changes: `git diff --ours scripts/file.sh`
3. Manually merge: Apply template fixes, preserve your customizations
4. Test: `./scripts/file.sh` should work

---

## Rollback Procedure

**If upgrade fails or causes issues:**

### Quick Rollback (Uncommitted Changes)

```bash
# If you haven't committed the upgrade yet
git reset --hard HEAD

# Verify
cat .copier-answers.yml | grep _commit
# Should show previous version
```

### Committed Rollback

```bash
# Option 1: Undo last commit
git reset --hard HEAD~1

# Option 2: Restore from backup branch
git checkout main
git reset --hard backup-pre-upgrade-$(date +%Y%m%d)

# Option 3: Restore from tag
git checkout main
git tag  # Find your backup tag
git reset --hard backup-vX.Y

# Verify rollback
cat .copier-answers.yml | grep _commit
./scripts/check-env.sh
pytest
```

### Report Issues

If upgrade consistently fails, report it:

**GitHub Issue**: https://github.com/liminalcommons/chora-base/issues/new

**Include**:
- Your project's chora-base version (before upgrade)
- Target version (attempted upgrade)
- Error messages / conflict descriptions
- Customizations involved (from "Customized Files" section)
- Steps to reproduce

---

## For AI Agents

### Upgrade Decision Framework

**When to upgrade:**

```
IF release contains CRITICAL fixes
  THEN: Upgrade required (correctness issue)
ELSE IF new features align with project needs
  THEN: Evaluate benefits vs costs
ELSE IF working across multiple chora-base projects
  THEN: Consider ecosystem consistency benefits
ELSE
  THEN: Defer until needed
```

### Customization Preservation

**Before upgrade:**
1. Review "Customized Files" section in this document
2. Note which files will be affected by template changes
3. Plan merge strategy for each file

**During upgrade:**
1. Accept template improvements where possible
2. Preserve local customizations
3. Merge both when conflicts arise (preferred)

**After upgrade:**
1. Validate all customizations still work
2. Update "Customized Files" if new customizations added
3. Document upgrade in "Template Version History"

### Knowledge Storage

**Create knowledge note for each upgrade:**

```json
{
  "id": "mcp-orchestration-upgrade-vOLD-to-vNEW",
  "created": "YYYY-MM-DD",
  "tags": ["mcp-orchestration", "chora-base", "upgrade"],

  "upgrade": {
    "from": "vOLD",
    "to": "vNEW",
    "decision": "adopted/deferred",
    "reasoning": "[why]"
  },

  "customizations_preserved": [
    "file: [what was preserved]"
  ],

  "workflow_changes": [
    {
      "from": "[old pattern]",
      "to": "[new pattern]",
      "benefit": "[why changed]"
    }
  ],

  "validation": {
    "tests": "passing/failing",
    "coverage": "maintained/improved/degraded"
  }
}
```

---

## Resources

### chora-base Documentation

- **Main README**: https://github.com/liminalcommons/chora-base/blob/main/README.md
- **CHANGELOG**: https://github.com/liminalcommons/chora-base/blob/main/CHANGELOG.md
- **Upgrade Philosophy**: https://github.com/liminalcommons/chora-base/blob/main/docs/upgrades/PHILOSOPHY.md
- **Upgrade Guides**: https://github.com/liminalcommons/chora-base/tree/main/docs/upgrades

### Version-Specific Guides

- [v1.0 → v1.1](https://github.com/liminalcommons/chora-base/blob/main/docs/upgrades/v1.0-to-v1.1.md)
- [v1.1 → v1.2](https://github.com/liminalcommons/chora-base/blob/main/docs/upgrades/v1.1-to-v1.2.md)
- [v1.2 → v1.3](https://github.com/liminalcommons/chora-base/blob/main/docs/upgrades/v1.2-to-v1.3.md)
- [v1.3 → v1.4](https://github.com/liminalcommons/chora-base/blob/main/docs/upgrades/v1.3-to-v1.4.md)

### Cumulative Guides

- [v1.0 → v1.4 (Multi-version jump)](https://github.com/liminalcommons/chora-base/blob/main/docs/upgrades/CUMULATIVE_v1.0-to-v1.4.md)

---

**This document is part of your project**. Update it as you customize and upgrade!

**Template generated**: 2025-10-24
**Template version**: 942644b0feb0bb4e0497e100125c98704e0f31af
