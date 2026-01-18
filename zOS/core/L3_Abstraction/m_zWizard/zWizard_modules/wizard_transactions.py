# zCLI/subsystems/zWizard/zWizard_modules/wizard_transactions.py

"""
Wizard Transactions - Database Transaction Management for Multi-Step Workflows
==============================================================================

Manages database transactions during wizard execution via zLoader's schema_cache.
Provides automatic transaction detection, commit, and rollback functionality to
ensure data consistency across multi-step wizard operations.

Core Responsibilities
--------------------
1. **Auto-Detection**: Identify transaction-enabled steps from zData model refs
2. **Lifecycle Management**: Start, commit, and rollback transactions
3. **Error Handling**: Automatic rollback on step failures
4. **Schema Cache Integration**: Direct integration with zLoader's schema cache

Transaction Lifecycle
--------------------
### Phase 1: Detection (check_transaction_start)
- Scans step values for zData operations with `$alias` model references
- Example: `zData: {model: "$users"}` → Transaction alias = "users"
- Returns alias if transaction should start, None otherwise

### Phase 2: Execution
- All subsequent wizard steps execute within transaction context
- Database operations are buffered in schema cache
- Changes are not committed until explicit commit call

### Phase 3: Completion
**Success Path** (commit_transaction):
- All steps completed successfully
- Transaction committed to database
- Changes become permanent

**Error Path** (rollback_transaction):
- Any step failed with exception
- Transaction rolled back
- Database returns to pre-wizard state

Transaction Detection Rules
---------------------------
### Triggering Conditions (ALL must be true)
1. `use_transaction=True` (wizard enabled transactions via `_transaction: true`)
2. `transaction_alias=None` (no active transaction yet)
3. `schema_cache` exists (zLoader cache available)
4. Step contains `zData` key with `model` starting with `$`

### Model Syntax
- **`$alias`**: Transaction-enabled model reference
- **Regular model**: No transaction (immediate commit per operation)

Example:
```yaml
_transaction: true  # Enable transaction mode

step1:
  zData:
    model: "$users"    # Starts transaction with alias "users"
    operation: create
    data: {name: "Alice"}

step2:
  zData:
    model: "$users"    # Uses existing "users" transaction
    operation: create
    data: {name: "Bob"}

# Both operations committed together or rolled back together
```

Usage Examples
-------------
### Basic Transaction Workflow
```python
# Step 1: Check if transaction should start
transaction_alias = check_transaction_start(
    use_transaction=True,
    transaction_alias=None,
    step_value={"zData": {"model": "$users"}},
    schema_cache=loader.cache.schema_cache,
    logger=logger
)
# Returns: "users"

# Step 2: Execute wizard steps (within transaction)
# ... wizard steps execute using transaction context ...

# Step 3a: On success - Commit
commit_transaction(True, "users", schema_cache, logger)

# OR Step 3b: On error - Rollback
rollback_transaction(True, "users", schema_cache, logger, error)
```

### Multi-Step Wizard with Transactions
```yaml
wizard_create_team:
  _transaction: true  # Enable transactions
  
  create_team:
    zData:
      model: "$teams"
      operation: create
      data: {name: "Engineering"}
  
  add_members:
    zData:
      model: "$users"
      operation: update
      where: {team_id: null}
      data: {team_id: "{{ zHat.create_team.id }}"}

  # If ANY step fails, ALL changes are rolled back
```

Error Handling
-------------
- **Missing schema_cache**: Transaction silently skipped (graceful degradation)
- **Invalid model format**: Transaction not started (no $ prefix)
- **Commit failure**: Logged as error, exception propagated
- **Rollback failure**: Logged as error, database may be in inconsistent state

Constants Reference
-------------------
- LOG_TXN_ENABLED: Transaction start log message
- LOG_TXN_COMMITTED: Transaction commit success message
- LOG_TXN_ROLLBACK: Transaction rollback error message
- KEY_ZDATA: Dict key for zData operations
- KEY_MODEL: Dict key for model reference
- PREFIX_TXN_MODEL: Model prefix indicating transaction ($)
- PREFIX_INDEX: Index to strip $ prefix (1)

Dependencies
-----------
- **zLoader.schema_cache**: Transaction management via cache layer
- **zData**: Database operations that support transactions
- **Logger**: Transaction lifecycle logging

Best Practices
-------------
1. **Explicit Opt-In**: Use `_transaction: true` only for multi-step data operations
2. **Model Consistency**: Use same `$alias` across related steps
3. **Error Boundaries**: Let exceptions propagate for automatic rollback
4. **Logging**: Monitor transaction logs for debugging

Layer: 2, Position: 2 (zWizard subsystem)
Week: 6.14
Version: v1.5.4 Phase 1 (Industry-Grade)
"""

from zOS import Any, Optional

# Import constants from centralized file
from .wizard_constants import (
    _LOG_TXN_ENABLED,
    _LOG_TXN_COMMITTED,
    _LOG_TXN_ROLLBACK,
    _KEY_ZDATA,
    _KEY_MODEL,
    _PREFIX_TXN_MODEL,
    _PREFIX_INDEX,
)

__all__ = ["check_transaction_start", "commit_transaction", "rollback_transaction"]


def check_transaction_start(
    use_transaction: bool,
    transaction_alias: Optional[str],
    step_value: Any,
    schema_cache: Any,
    logger: Any
) -> Optional[str]:
    """
    Check if transaction should start for this step.
    
    Args:
        use_transaction: Whether transactions are enabled
        transaction_alias: Current transaction alias (None if not started)
        step_value: Current wizard step value
        schema_cache: zLoader schema cache for transactions
        logger: Logger instance
        
    Returns:
        Transaction alias (str) if started, None otherwise
    """
    if not (use_transaction and transaction_alias is None and schema_cache):
        return None

    if isinstance(step_value, dict) and _KEY_ZDATA in step_value:
        model = step_value[_KEY_ZDATA].get(_KEY_MODEL)
        if model and model.startswith(_PREFIX_TXN_MODEL):
            alias = model[_PREFIX_INDEX:]  # Remove $ prefix
            logger.info(_LOG_TXN_ENABLED, alias)
            return alias
    return None


def commit_transaction(
    use_transaction: bool,
    transaction_alias: Optional[str],
    schema_cache: Any,
    logger: Any
) -> None:
    """
    Commit transaction if active.
    
    Args:
        use_transaction: Whether transactions are enabled
        transaction_alias: Current transaction alias
        schema_cache: zLoader schema cache for transactions
        logger: Logger instance
    """
    if use_transaction and transaction_alias and schema_cache:
        schema_cache.commit_transaction(transaction_alias)
        logger.info(_LOG_TXN_COMMITTED, transaction_alias)


def rollback_transaction(
    use_transaction: bool,
    transaction_alias: Optional[str],
    schema_cache: Any,
    logger: Any,
    error: Exception
) -> None:
    """
    Rollback transaction on error.
    
    Args:
        use_transaction: Whether transactions are enabled
        transaction_alias: Current transaction alias
        schema_cache: zLoader schema cache for transactions
        logger: Logger instance
        error: The exception that triggered the rollback
    """
    if use_transaction and transaction_alias and schema_cache:
        logger.error(_LOG_TXN_ROLLBACK, transaction_alias, error)
        schema_cache.rollback_transaction(transaction_alias)


