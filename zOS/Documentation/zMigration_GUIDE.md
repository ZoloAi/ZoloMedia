# zMigration: Declarative Schema Evolution System

**Version:** 1.0.0  
**Status:** Production Ready  
**Philosophy:** "The schema IS the migration"

---

## 🎯 Overview

zMigration is zOS's **declarative schema evolution system** that automatically tracks, applies, and manages database schema changes across CSV, SQLite, and PostgreSQL backends.

Unlike traditional migration systems (Django, Rails, Alembic) that require manual migration file generation, zMigration uses **schema-as-code**: your YAML schema files ARE the migrations.

### Key Features

- ✅ **Single Source of Truth** - Schema YAML is the only definition
- ✅ **Automatic Discovery** - Finds all schemas via `ZDATA_*_URL` environment variables
- ✅ **Zero Drift** - Schema and database always in sync
- ✅ **Version Tracking** - Semantic versioning with auto-suggestion
- ✅ **History Management** - Every migration tracked with hash, timestamp, changes
- ✅ **Backend Agnostic** - Works on CSV, SQLite, PostgreSQL
- ✅ **Rollback Support** - (Coming soon) Automated rollback SQL generation
- ✅ **Terminal First** - Preview changes before applying

---

## 🏗️ Architecture

### The Problem with Traditional Migrations

**Django:**
```python
# models.py - Source of truth #1
class User(models.Model):
    email = models.EmailField()

# migrations/0002_add_email.py - Source of truth #2
class Migration(migrations.Migration):
    operations = [
        migrations.AddField('user', 'email', models.EmailField()),
    ]
```

**Problem:** Two sources of truth can drift!

---

### The zMigration Solution

**zOS:**
```yaml
# zSchema.users.yaml - ONLY source of truth
Meta:
  zMigration: true
  zMigrationVersion: v1.1.0

users:
  email:
    type: str
    required: true
```

**Result:** Schema IS the migration. No drift possible!

---

## 🚀 Quick Start

### 1. Enable zMigration in Schema

```yaml
# zCloud/models/zSchema.users.yaml
Meta:
  Data_Type: csv
  Data_Source: ZDATA_USERS_URL
  zMigration: true              # Enable migration tracking
  zMigrationVersion: v1.0.0     # Current version

users:
  id: {type: int, pk: true}
  username: {type: str, required: true}
  email: {type: str, required: true}
```

### 2. Add Environment Variable

```bash
# zCloud/.zEnv
ZDATA_USERS_URL=@.Data
```

### 3. Run Migration

```bash
zolo migrate zTest.py
```

**Output:**
```
======================================================================
🔄 zMigration: Schema Evolution System
======================================================================
   App: zTest.py
   Directory: /Users/you/Projects/zCloud
======================================================================

1️⃣ Loading application configuration...
   ✅ Loaded zSpark for: zCloud

2️⃣ Initializing zOS...
   ✅ zOS initialized

3️⃣ Discovering schemas...
📊 Discovered Schemas:
   ✓ zSchema.users
      Data Type: csv
      Version: v1.0.0
      Status: zMigration: enabled

======================================================================
✅ Schema Discovery Complete
======================================================================

📌 1 schema(s) ready for migration

4️⃣ Applying Migrations (Declarative)
Migrating zSchema.users...
   Version: v1.0.0
   ✅ Migration complete (0 operation(s))

======================================================================
📊 Migration Results
======================================================================

   ✅ 1 migration(s) applied successfully

======================================================================
✅ All migrations applied successfully!
======================================================================
```

---

## 📋 Core Concepts

### 1. Schema-as-Code

Your YAML schema is the **single source of truth**. When you change the schema, zMigration automatically detects and applies the changes.

**Example: Adding a Field**

```yaml
# Before (v1.0.0)
users:
  id: {type: int, pk: true}
  username: {type: str}

# After (v1.1.0) - Just add the field!
users:
  id: {type: int, pk: true}
  username: {type: str}
  email: {type: str}  # NEW FIELD
```

Run `zolo migrate zTest.py` and zMigration:
1. Detects the new `email` field
2. Generates `ALTER TABLE ADD COLUMN` (SQL) or adds column (CSV)
3. Records the change in `__zmigration_users.csv`
4. Updates `zMigrationVersion` to `v1.1.0`

### 2. Automatic Discovery

zMigration finds all schemas by scanning environment variables:

```bash
# .zEnv
ZDATA_USERS_URL=@.Data
ZDATA_POSTS_URL=@.Data
ZDATA_COMMENTS_URL=@.Data
```

When you run `zolo migrate zTest.py`, it discovers **all** schemas with `zMigration: true` and migrates them together.

### 3. Migration History

Every migration is tracked in a special table/file:

**CSV:** `__zmigration_users.csv` (same folder as `users.csv`)
```csv
id,schema_name,from_version,to_version,applied_at,schema_hash,changes_summary,status
1,zSchema.users,v1.0.0,v1.1.0,2024-12-24T10:30:00,abc123...,Added column: email,SUCCESS
```

**SQL:** `__zmigration_users` table (same database as `users` table)

### 4. Semantic Versioning

zMigration uses **semantic versioning** (Major.Minor.Patch):

- **Patch (x.y.Z):** Non-breaking changes (add column, add index)
- **Minor (x.Y.z):** Breaking changes (drop column, change type)
- **Major (X.y.z):** Major refactoring (manual override)

**Auto-Suggestion:**
```
Detected changes:
  - Added column: email (non-breaking)

Suggested version: v1.0.1
Current version: v1.0.0
```

### 5. Schema Hashing

Every migration records a **SHA256 hash** of the schema YAML:

```python
schema_hash = hashlib.sha256(yaml_content.encode()).hexdigest()
# abc123def456... (64 characters)
```

**Why?** Detects manual schema edits and ensures integrity.

---

## 🛠️ Command Reference

### `zolo migrate <app_file>`

**Description:** Apply all pending migrations for an application.

**Arguments:**
- `app_file` - Path to zSpark file (e.g., `zTest.py`, `app.py`)

**Options:**
- `--auto-approve` - Skip confirmation prompt (for CI/CD)
- `--version <version>` - Manually specify target version

**Examples:**

```bash
# Interactive mode (prompts for confirmation)
zolo migrate zTest.py

# Auto-approve (CI/CD)
zolo migrate zTest.py --auto-approve

# Manual version override
zolo migrate zTest.py --version v2.0.0
```

---

## 📖 Schema Configuration

### Meta Section

```yaml
Meta:
  Data_Type: csv               # csv, sqlite, postgresql
  Data_Source: ZDATA_USERS_URL # Environment variable
  zMigration: true             # Enable migration tracking
  zMigrationVersion: v1.0.0    # Current schema version
  
  # Optional: Migration hooks (future)
  zMigrationHooks:
    before_migrate: "@.plugins.migrations.before_users"
    after_migrate: "@.plugins.migrations.after_users"
```

### Field Definitions

```yaml
users:
  # Primary key
  id:
    type: int
    pk: true
    auto_increment: true
  
  # Required field
  username:
    type: str
    required: true
    rules:
      min_length: 3
      max_length: 50
  
  # Optional field with default
  email:
    type: str
    required: false
    default: null
  
  # Timestamp with auto-now
  created_at:
    type: datetime
    default: now
```

---

## 🔄 Migration Workflow

### Step 1: Edit Schema

```yaml
# zCloud/models/zSchema.users.yaml
Meta:
  zMigrationVersion: v1.0.0

users:
  id: {type: int, pk: true}
  username: {type: str}
  # Add new field:
  email: {type: str, required: false}
```

### Step 2: Run Migration

```bash
cd zCloud
zolo migrate zTest.py
```

### Step 3: Review Changes

```
Detected changes for zSchema.users:
  + Added column: email (type: str, required: false)

Suggested version: v1.0.1 (non-breaking)
Current version: v1.0.0

Apply migration? [y/N]
```

### Step 4: Confirm

```
y
```

### Step 5: Verify

```
Migrating zSchema.users...
   Version: v1.0.0 → v1.0.1
   ✅ Migration complete (1 operation(s))

Migration history recorded:
   File: Data/__zmigration_users.csv
   Hash: abc123def456...
   Changes: Added column: email
```

---

## 📊 Migration Types

### 1. Add Column (Non-Breaking)

**Schema Change:**
```yaml
users:
  email: {type: str, required: false}  # NEW
```

**DDL Generated:**
```sql
ALTER TABLE users ADD COLUMN email VARCHAR(255);
```

**Version:** v1.0.0 → v1.0.1 (patch)

---

### 2. Drop Column (Breaking)

**Schema Change:**
```yaml
users:
  # old_field: {type: str}  # REMOVED
```

**DDL Generated:**
```sql
ALTER TABLE users DROP COLUMN old_field;
```

**Version:** v1.0.0 → v1.1.0 (minor)

---

### 3. Change Column Type (Breaking)

**Schema Change:**
```yaml
users:
  age: {type: int}  # Was: {type: str}
```

**DDL Generated:**
```sql
ALTER TABLE users ALTER COLUMN age TYPE INTEGER USING age::integer;
```

**Version:** v1.0.0 → v1.1.0 (minor)

---

### 4. Add Index (Non-Breaking)

**Schema Change:**
```yaml
users:
  email:
    type: str
    indexed: true  # NEW
```

**DDL Generated:**
```sql
CREATE INDEX idx_users_email ON users(email);
```

**Version:** v1.0.0 → v1.0.1 (patch)

---

### 5. Add Foreign Key (Non-Breaking)

**Schema Change:**
```yaml
posts:
  user_id:
    type: int
    foreign_key: users.id  # NEW
```

**DDL Generated:**
```sql
ALTER TABLE posts ADD CONSTRAINT fk_posts_user_id 
  FOREIGN KEY (user_id) REFERENCES users(id);
```

**Version:** v1.0.0 → v1.0.1 (patch)

---

## 🗂️ Migration History Schema

### System Schema: `zSchema.zMigration.yaml`

Located in: `~/Library/Application Support/zolo-zcli/zSchemas/zSchema.zMigration.yaml`

```yaml
Meta:
  Data_Type: csv
  Data_Source: "ZDATA_ZMIGRATION_URL"
  zMigration: false  # This schema doesn't migrate itself!
  zMigrationVersion: v1.0.0

zdata_migrations:
  id: {type: int, pk: true, auto_increment: true}
  
  schema_name: {type: str, required: true}
  from_version: {type: str, required: false}
  to_version: {type: str, required: true}
  applied_at: {type: datetime, default: now}
  
  schema_hash: {type: str, required: true}
  changes_summary: {type: str, required: false}
  status: {type: str, default: "SUCCESS"}
  
  applied_by: {type: str, required: false, default: "system"}
  app_name: {type: str, required: false}
  app_version: {type: str, required: false}
  zcli_version: {type: str, required: false}
  
  execution_time_ms: {type: int, required: false}
  rollback_sql: {type: str, required: false}
  forward_sql: {type: str, required: false}
  diff_json: {type: json, required: false}
  meta_data: {type: json, required: false}
  notes: {type: str, required: false}
```

### Fields Explained

- **schema_name** - Which schema was migrated (e.g., `zSchema.users`)
- **from_version** - Version before migration (e.g., `v1.0.0`)
- **to_version** - Version after migration (e.g., `v1.1.0`)
- **applied_at** - When the migration was applied
- **schema_hash** - SHA256 hash of schema YAML (integrity check)
- **changes_summary** - Human-readable summary (e.g., "Added column: email")
- **status** - SUCCESS, FAILED, or ROLLBACK
- **applied_by** - User or system that applied migration
- **execution_time_ms** - How long the migration took
- **diff_json** - Full JSON diff of schema changes

---

## 🎯 Best Practices

### 1. Always Use Semantic Versioning

```yaml
# Non-breaking (add field, add index)
v1.0.0 → v1.0.1

# Breaking (drop field, change type)
v1.0.0 → v1.1.0

# Major refactor (manual override)
v1.0.0 → v2.0.0
```

### 2. Test Migrations in Development

```bash
# 1. Make schema changes
# 2. Run migration on CSV (fast)
zolo migrate zTest.py

# 3. Test your app
python zTest.py

# 4. Verify data
# 5. Commit changes
```

### 3. Use Migration Hooks for Data Migration

```yaml
Meta:
  zMigrationHooks:
    after_migrate: "@.plugins.migrations.populate_email"
```

```python
# zCloud/plugins/migrations.py
def populate_email(zcli, **kwargs):
    """Populate email field with username@example.com for existing users."""
    users = zcli.data.users.select(where={"email": None})
    
    for user in users:
        zcli.data.users.update(
            where={"id": user['id']},
            set={"email": f"{user['username']}@example.com"}
        )
```

### 4. Keep Schema Changes Small

❌ **Bad:**
```yaml
# Changed 10 fields in one migration
Meta:
  zMigrationVersion: v1.5.0  # Jumped from v1.0.0!
```

✅ **Good:**
```yaml
# Changed 1-2 fields per migration
Meta:
  zMigrationVersion: v1.0.1  # Incremental
```

### 5. Document Breaking Changes

```yaml
Meta:
  zMigrationVersion: v1.1.0
  zMigrationNotes: |
    BREAKING CHANGE: Renamed 'name' to 'full_name'
    Migration hook migrates existing data automatically.
  zMigrationHooks:
    after_migrate: "@.plugins.migrations.rename_name_to_full_name"
```

---

## 🆚 Comparison with Other Frameworks

### Django Migrations

**Django:**
```bash
# 1. Edit models.py
# 2. Generate migration
python manage.py makemigrations

# 3. Review auto-generated migration file
# 4. Apply migration
python manage.py migrate
```

**Problems:**
- ✗ Two sources of truth (models.py + migration files)
- ✗ Manual migration generation required
- ✗ Migration files can drift from models
- ✗ Must track migration files in version control

**zOS:**
```bash
# 1. Edit zSchema.users.yaml
# 2. Apply migration
zolo migrate zTest.py
```

**Benefits:**
- ✓ One source of truth (schema YAML)
- ✓ Automatic migration detection
- ✓ Zero drift possible
- ✓ No migration files to track

---

### Rails Migrations

**Rails:**
```bash
# 1. Generate migration
rails generate migration AddEmailToUsers email:string

# 2. Edit generated migration file
# 3. Run migration
rails db:migrate
```

**Problems:**
- ✗ Manual migration generation
- ✗ Migration files separate from schema
- ✗ Can't easily see current schema state

**zOS:**
- ✓ Schema IS the migration
- ✓ Current state always visible in YAML
- ✓ No separate migration files

---

### Alembic (SQLAlchemy)

**Alembic:**
```bash
# 1. Edit models.py
# 2. Auto-generate migration
alembic revision --autogenerate -m "add email"

# 3. Review generated migration
# 4. Apply
alembic upgrade head
```

**Problems:**
- ✗ Complex migration files (upgrade/downgrade functions)
- ✗ Auto-detection not always accurate
- ✗ Steep learning curve

**zOS:**
- ✓ Simple YAML schema
- ✓ Accurate auto-detection (compares schema YAML to database)
- ✓ Minimal learning curve

---

## 🔬 Advanced Features

### 1. Multi-Backend Support

**Same Schema, Different Backends:**

```yaml
# Development: CSV
Meta:
  Data_Type: csv
  zMigration: true

# Production: PostgreSQL (change ONE line!)
Meta:
  Data_Type: postgresql
  zMigration: true
```

zMigration generates appropriate DDL for each backend!

---

### 2. Migration Hooks (Coming Soon)

```yaml
Meta:
  zMigrationHooks:
    before_migrate: "@.plugins.migrations.backup_data"
    after_migrate: "@.plugins.migrations.reindex_search"
    on_rollback: "@.plugins.migrations.restore_backup"
```

---

### 3. Rollback Support (Coming Soon)

```bash
# Apply migration
zolo migrate zTest.py

# Rollback last migration
zolo migrate zTest.py --rollback

# Rollback to specific version
zolo migrate zTest.py --rollback-to v1.0.0
```

---

### 4. Migration Preview

```bash
# Preview changes without applying
zolo migrate zTest.py --dry-run
```

**Output:**
```
Detected changes for zSchema.users:
  + Add column: email (VARCHAR(255))
  + Add index: idx_users_email

DDL Preview:
  ALTER TABLE users ADD COLUMN email VARCHAR(255);
  CREATE INDEX idx_users_email ON users(email);

No changes will be applied (dry-run mode).
```

---

## 🔧 Troubleshooting

### Issue: "No schemas found with zMigration enabled"

**Cause:** No `ZDATA_*_URL` environment variables or `zMigration: false`

**Solution:**
1. Check `.zEnv` file has `ZDATA_USERS_URL=@.Data`
2. Check schema has `zMigration: true` in Meta section

---

### Issue: "Schema drift detected"

**Cause:** Schema hash doesn't match last migration

**Solution:**
1. Review uncommitted schema changes
2. Run `zolo migrate` to sync
3. Commit schema changes

---

### Issue: "Migration failed: Column already exists"

**Cause:** Database out of sync with migration history

**Solution:**
```bash
# Option 1: Force sync (dangerous!)
zolo migrate zTest.py --force-sync

# Option 2: Manually fix database
# Drop the column, then re-run migration
```

---

## 📚 Reference

### Environment Variables

- `ZDATA_<TABLE>_URL` - Data source path (e.g., `@.Data`)
- `ZDATA_ZMIGRATION_URL` - Migration history path (auto-set)

### CLI Flags

- `--auto-approve` - Skip confirmation
- `--version <version>` - Manual version override
- `--dry-run` - Preview changes (coming soon)
- `--rollback` - Rollback last migration (coming soon)
- `--force-sync` - Force sync (dangerous, coming soon)

### Schema Meta Fields

- `zMigration` - Enable/disable migration tracking (default: true)
- `zMigrationVersion` - Current schema version (required)
- `zMigrationHooks` - Before/after migration hooks (optional)
- `zMigrationNotes` - Human-readable migration notes (optional)

---

## 🎓 Summary

### What Makes zMigration Special?

1. **Schema-as-Code** - YAML schema is the only source of truth
2. **Zero Configuration** - Auto-discovers schemas via env vars
3. **Terminal First** - Preview and apply from command line
4. **Backend Agnostic** - CSV, SQLite, PostgreSQL with same workflow
5. **Semantic Versioning** - Auto-suggests version bumps
6. **History Tracking** - Every migration recorded with hash and timestamp
7. **Declarative** - No manual migration file writing

### The zOS Way

> **"The schema IS the migration. If you're writing migration files, you're doing it wrong."**

Instead of:
1. Edit model → Generate migration → Review migration → Apply migration

You do:
1. Edit schema → Apply migration

**That's it. 2 steps instead of 4.**

---

## 🚀 Next Steps

1. **Enable zMigration** in your schemas
2. **Run your first migration** with `zolo migrate`
3. **Check migration history** in `__zmigration_*.csv` files
4. **Read the battle plan** for production deployment

---

**Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Last Updated:** December 24, 2024

*"Migration should be declarative, not imperative. The framework knows how."* 🎯

