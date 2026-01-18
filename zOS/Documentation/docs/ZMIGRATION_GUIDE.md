# zMigration: Opt-In Schema Migrations

**Version:** 1.5.13  
**Author:** zOS Team  
**Date:** December 20, 2025

---

## 📖 **Overview**

`zMigration` is zOS's declarative schema migration system with **explicit opt-in**. It provides safe, trackable, and automated database migrations while preventing accidental schema changes.

### **Key Features:**
- ✅ **Opt-in by design** - Requires explicit `zMigration: true` flag
- ✅ **Backend migration support** - Automatically handles CSV → Postgres transitions
- ✅ **Version tracking** - Track schema versions with `zMigrationVersion`
- ✅ **Dry-run mode** - Preview changes before execution
- ✅ **Transaction safety** - Atomic operations with automatic rollback
- ✅ **Migration history** - Audit trail of all schema changes
- ✅ **Data preservation** - Automatic backup before backend changes

---

## 🚀 **Quick Start**

### **1. Enable Migrations in Your Schema**

Add to your schema's `Meta` section:

```yaml
Meta:
  Data_Type: csv
  Data_Label: "My Schema"
  Data_Source: "ZDATA_MYSCHEMA_URL"
  Data_Paradigm: classical
  Schema_Name: "zSchema.myschema"
  
  # Enable migrations (required)
  zMigration: true
  zMigrationVersion: "v1.0.0"
```

### **2. Preview Migration (Dry-Run)**

```bash
# Preview changes without executing
data migrate --model @.models.zSchema.myschema --dry-run
```

### **3. Apply Migration**

```bash
# Execute migration (with confirmation)
data migrate --model @.models.zSchema.myschema
```

### **4. View Migration History**

```bash
# See all past migrations
data history --model @.models.zSchema.myschema
```

---

## ⚙️ **Configuration**

### **Required Meta Fields:**

```yaml
Meta:
  # Standard fields
  Data_Type: csv              # Backend type (csv, sqlite, postgres)
  Data_Label: "Users"         # Human-readable name
  Data_Source: "ZDATA_URL"    # Environment variable reference
  Data_Paradigm: classical
  Schema_Name: "zSchema.users"
  
  # Migration fields (NEW v1.5.13)
  zMigration: true            # Enable migrations (REQUIRED)
  zMigrationVersion: "v1.0.0" # Schema version (REQUIRED)
```

### **Version Format:**

Use semantic versioning or any consistent format:
- `v1.0.0` - Semantic versioning
- `2025-12-20` - Date-based
- `abc123` - Git commit hash
- `Phase-1` - Milestone-based

---

## 🔒 **Why Opt-In?**

### **Production Safety**

Without opt-in, migrations could:
- ❌ Accidentally modify production databases
- ❌ Delete critical data
- ❌ Break running applications
- ❌ Occur without awareness

With opt-in:
- ✅ Explicit consent required
- ✅ Prevents accidental changes
- ✅ Clear intention in code
- ✅ Version tracking enforced

### **Error When zMigration Missing:**

```
❌ Migration Blocked: zMigration not enabled

Schema file: @.models.zSchema.users

To enable migrations, add to Meta section:

  Meta:
    zMigration: true
    zMigrationVersion: "v1.0.0"

This opt-in flag prevents accidental schema changes.
```

---

## 🔄 **Backend Migration**

### **Automatic Backend Changes**

When you change `Data_Type` in your schema, zData automatically:

1. **Exports all data** from current backend (to CSV)
2. **Initializes new backend** (creates tables)
3. **Imports data** to new backend
4. **Creates backup** of exported data

### **Example: CSV → Postgres**

**Before (CSV):**
```yaml
Meta:
  Data_Type: csv
  Data_Source: "ZDATA_USERS_URL"
  zMigration: true
  zMigrationVersion: "v1.0.0"
```

**After (Postgres):**
```yaml
Meta:
  Data_Type: postgres
  Data_Source: "ZDATA_USERS_URL"
  zMigration: true
  zMigrationVersion: "v2.0.0"  # Bump version!
```

**Output:**
```
⚠️  BACKEND MIGRATION DETECTED
================================================================================

  Old Backend: csv
  New Backend: postgres

Migration Steps:
  1. Export all data from current backend
  2. Initialize new backend
  3. Import data to new backend
  4. Backup old data

📦 Exporting data from csv...
  ✓ Exported users (5 rows)
  ✓ Exported roles (3 rows)
  ✓ Exported 2 tables to Data/backups/csv_export_20251220_120000

🔧 Initializing new backend (postgres)...
  ✓ New backend initialized

📥 Importing data to postgres...
  ✓ Imported users (5 rows)
  ✓ Imported roles (3 rows)
  ✓ Imported 2 tables

✅ Backend migration complete!

📦 Backup location: Data/backups/csv_export_20251220_120000
```

### **Backup Location**

Backups are stored in:
```
Data/backups/{backend}_export_{timestamp}/
  ├── users.csv
  ├── roles.csv
  └── ...
```

---

## 📋 **Usage Examples**

### **Python API**

```python
from zOS import zOS

z = zOS({'zMode': 'Terminal'})

# Load current schema
z.data.load_schema('@.models.zSchema.users')

# Preview migration
result = z.data.migrate('@.models.zSchema.users_v2', dry_run=True)
print(result)

# Execute migration
result = z.data.migrate('@.models.zSchema.users_v2')

# View history
history = z.data.get_migration_history(limit=10)
for record in history:
    print(f"{record['applied_at']}: {record['schema_version']}")
```

### **Command Line (zShell)**

```bash
# Start zShell
python3 -c "from zOS import zOS; z = zOS(); z.shell.run()"

# In zShell:
> data load --model @.models.zSchema.users
> data migrate --model @.models.zSchema.users_v2 --dry-run
> data migrate --model @.models.zSchema.users_v2
> data history --model @.models.zSchema.users
```

---

## 🧪 **Testing**

### **Test Script (test_phase0_migration.py)**

```bash
cd zCloud
python3 test_phase0_migration.py
```

**Expected Output:**
```
🚀 Phase 0: zMigration System Test Suite
================================================================================

TEST 1: Migration should be BLOCKED without zMigration flag
================================================================================
✅ TEST PASSED: Migration correctly blocked!

TEST 2: Migration should SUCCEED with zMigration flag
================================================================================
✅ TEST PASSED: Migration correctly allowed!

TEST 3: Version tracking should work
================================================================================
✅ TEST PASSED: Version correctly tracked: v1.0.0

📊 TEST SUMMARY
================================================================================
  ✅ PASS: Migration Blocked
  ✅ PASS: Migration Allowed
  ✅ PASS: Version Tracking

  Total: 3/3 tests passed

🎉 All tests passed! Phase 0 implementation is complete.
```

---

## 🛠️ **Migration Workflow**

### **Standard Pattern**

1. **Create new schema YAML** with changes
2. **Add zMigration flags** to Meta
3. **Preview with dry-run** to validate
4. **Execute migration** after review
5. **Verify in both modes** (Terminal + Bifrost)
6. **Check migration history** for audit trail

### **Example Workflow**

```bash
# 1. Edit schema file
vim zCloud/models/zSchema.users.yaml
# - Add new field: avatar_url
# - Bump version: v1.1.0

# 2. Preview changes
python3 -c "
from zOS import zOS
z = zOS({'zMode': 'Terminal'})
z.data.load_schema('@.models.zSchema.users')
result = z.data.migrate('@.models.zSchema.users', dry_run=True)
"

# 3. Apply migration
python3 -c "
from zOS import zOS
z = zOS({'zMode': 'Terminal'})
z.data.load_schema('@.models.zSchema.users')
result = z.data.migrate('@.models.zSchema.users')
"

# 4. Test Terminal mode
python3 app.py  # Terminal
# Login and verify

# 5. Test Bifrost mode
python3 app.py  # (zMode: zBifrost)
# Open browser and verify
```

---

## 📚 **Related Documentation**

- [zData Guide](./ZDATA_GUIDE.md) - Complete zData subsystem documentation
- [Schema Design](./SCHEMA_DESIGN.md) - How to design schemas
- [Migration Plan](../../local_planning/ZCLOUD_SCHEMA_MIGRATION_PLAN.md) - Production migration guide

---

## 🔍 **Troubleshooting**

### **"zMigration not enabled in schema"**

**Problem:** Trying to migrate schema without opt-in flag.

**Solution:** Add to Meta section:
```yaml
Meta:
  zMigration: true
  zMigrationVersion: "v1.0.0"
```

### **"No schema loaded"**

**Problem:** Calling migrate() before load_schema().

**Solution:** Load current schema first:
```python
z.data.load_schema('@.models.zSchema.current')
z.data.migrate('@.models.zSchema.new')
```

### **Backend migration fails**

**Problem:** Error during CSV → Postgres migration.

**Solution:**
1. Check backup location (printed in error)
2. Verify new backend credentials in `.zEnv`
3. Restore from backup if needed:
   ```bash
   cp Data/backups/csv_export_*/users.csv Data/users.csv
   ```

---

## 🎯 **Best Practices**

### **Version Management**
- ✅ Bump version on every schema change
- ✅ Use consistent versioning format
- ✅ Document breaking changes in commit messages

### **Testing**
- ✅ Always dry-run first
- ✅ Test in Terminal mode before Bifrost
- ✅ Verify data integrity after migration

### **Backup**
- ✅ Commit schema files before migration
- ✅ Keep backups of data files
- ✅ Test rollback procedures

### **Production**
- ✅ Schedule migrations during maintenance windows
- ✅ Notify users before schema changes
- ✅ Have rollback plan ready

---

## 📝 **Changelog**

### **v1.5.13 (2025-12-20)**
- ✨ Added `zMigration` opt-in flag
- ✨ Added `zMigrationVersion` tracking
- ✨ Added backend migration support
- ✨ Added automatic data export/import
- ✨ Added validation and error messages

---

**For more information, see the [zData Guide](./ZDATA_GUIDE.md) or open an issue on GitHub.**

