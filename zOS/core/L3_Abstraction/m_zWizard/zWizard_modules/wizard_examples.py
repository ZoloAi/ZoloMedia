# zCLI/subsystems/zWizard/zWizard_modules/wizard_examples.py

"""
zWizard Usage Examples - Real-World Patterns
============================================

This module provides comprehensive examples of zWizard usage patterns for both
Shell mode and Walker mode, including transactions, RBAC, and advanced features.

Examples included:
------------------
1. **Shell Mode**: Basic wizard workflow
2. **Walker Mode**: Menu navigation
3. **Transactional Wizard**: Multi-step data operations
4. **RBAC-Protected Wizard**: Role-based access control
5. **zHat Interpolation**: Cross-step result references
6. **Error Handling**: Custom navigation callbacks
7. **Advanced Patterns**: Nested wizards, conditional execution

Layer: 2, Position: 2 (zWizard subsystem)
Week: 6.14
Version: v1.5.4 Phase 3 (Polish)
"""

from zOS import Any


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 1: SHELL MODE - BASIC WIZARD WORKFLOW
# ═══════════════════════════════════════════════════════════════════════════

def example_shell_mode_basic(zcli: Any) -> None:
    """
    Example 1: Basic wizard execution in Shell mode.
    
    Use Case: User management workflow (create user, assign role, send email)
    
    Args:
        zcli: zCLI instance
    """
    from zOS.L3_Abstraction.m_zWizard import zWizard
    
    # Initialize wizard with zcli instance
    wizard = zWizard(zcli=zcli)
    
    # Define workflow steps
    workflow_items = {
        "welcome": {
            "type": "zDisplay",
            "event": "text",
            "content": "Welcome to User Creation Wizard",
            "color": "MAIN"
        },
        "get_username": {
            "type": "zDialog",
            "prompt": "Enter username:",
            "validate": "required"
        },
        "get_email": {
            "type": "zDialog",
            "prompt": "Enter email:",
            "validate": "email"
        },
        "confirm": {
            "type": "zDisplay",
            "event": "text",
            "content": "Creating user...",
            "color": "SUCCESS"
        }
    }
    
    # Execute workflow
    result = wizard.execute_loop(workflow_items)
    
    # Result is a WizardHat object with triple-access
    print(f"Workflow completed with {len(result)} steps")
    print(f"Username: {result['get_username']}")  # Key access
    print(f"Email: {result.get_email}")  # Attribute access
    print(f"First result: {result[0]}")  # Numeric access


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 2: WALKER MODE - MENU NAVIGATION
# ═══════════════════════════════════════════════════════════════════════════

def example_walker_mode_menu(walker: Any) -> None:
    """
    Example 2: Menu navigation using zWalker (which inherits from zWizard).
    
    Use Case: Admin dashboard with multiple menu options
    
    Args:
        walker: zWalker instance (inherits from zWizard)
    """
    # zWalker inherits from zWizard, reusing the loop engine
    # Menu items are wizard steps with special handling
    
    menu_items = {
        "users": {
            "label": "User Management",
            "description": "Create, edit, delete users",
            "action": "user_menu",
            "zRBAC": {"require_role": "admin"}  # Protected by RBAC
        },
        "settings": {
            "label": "System Settings",
            "description": "Configure system parameters",
            "action": "settings_menu",
            "zRBAC": {"require_permission": "system.configure"}
        },
        "reports": {
            "label": "View Reports",
            "description": "Analytics and reporting",
            "action": "reports_menu",
            "zRBAC": {"require_auth": True}  # Any authenticated user
        },
        "exit": {
            "label": "Exit",
            "description": "Return to main menu",
            "action": "zBack"  # Navigation signal
        }
    }
    
    # Execute menu loop (walker mode)
    # Navigation signals (zBack, exit, stop) control flow
    result = walker.execute_loop(menu_items)
    
    # Result handling
    if result == "zBack":
        print("Returned to previous menu")
    elif result == "exit":
        print("Exited application")


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 3: TRANSACTIONAL WIZARD - MULTI-STEP DATA OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════

def example_transactional_wizard(zcli: Any) -> None:
    """
    Example 3: Multi-step wizard with database transactions.
    
    Use Case: Create team and assign members atomically
    
    Args:
        zcli: zCLI instance
    
    YAML equivalent:
    ----------------
    ```yaml
    _transaction: true  # Enable transaction mode
    
    create_team:
      zData:
        model: "$teams"      # $ prefix starts transaction
        operation: create
        data:
          name: "Engineering"
          description: "Development team"
    
    assign_lead:
      zData:
        model: "$teams"      # Same alias = same transaction
        operation: update
        where: {id: "{{ zHat.create_team.id }}"}
        data: {lead_id: 42}
    
    add_members:
      zData:
        model: "$users"
        operation: update
        where: {team_id: null}
        data: {team_id: "{{ zHat.create_team.id }}"}
    
    # All operations committed together or rolled back on error
    ```
    """
    from zOS.L3_Abstraction.m_zWizard import zWizard
    
    wizard = zWizard(zcli=zcli)
    
    # Workflow with transaction support
    workflow = {
        "_transaction": True,  # Enable transaction mode
        
        "create_team": {
            "zData": {
                "model": "$teams",  # Transaction starts here
                "operation": "create",
                "data": {
                    "name": "Engineering",
                    "description": "Development team"
                }
            }
        },
        
        "assign_lead": {
            "zData": {
                "model": "$teams",  # Uses same transaction
                "operation": "update",
                "where": {"id": "{{ zHat.create_team.id }}"},  # Interpolation!
                "data": {"lead_id": 42}
            }
        },
        
        "add_members": {
            "zData": {
                "model": "$users",
                "operation": "update",
                "where": {"team_id": None},
                "data": {"team_id": "{{ zHat.create_team.id }}"}
            }
        }
    }
    
    try:
        # Execute with automatic transaction management
        result = wizard.handle(workflow)
        print("Transaction completed successfully")
        print(f"Team ID: {result.create_team['id']}")  # Access results
    except Exception as e:
        print(f"Transaction rolled back due to error: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 4: RBAC-PROTECTED WIZARD - ROLE-BASED ACCESS CONTROL
# ═══════════════════════════════════════════════════════════════════════════

def examplezRBAC_protected_wizard(zcli: Any) -> None:
    """
    Example 4: Wizard with role-based access control on specific steps.
    
    Use Case: Admin workflow with some public and some protected steps
    
    Args:
        zcli: zCLI instance
    
    YAML equivalent:
    ----------------
    ```yaml
    view_dashboard:
      zRBAC:
        require_auth: true  # Any logged-in user
      zDisplay:
        event: text
        content: "Welcome to dashboard"
    
    manage_users:
      zRBAC:
        require_role: "admin"  # Admin only
      zDisplay:
        event: text
        content: "User management panel"
    
    delete_data:
      zRBAC:
        require_permission: "data.delete"  # Specific permission
      zData:
        model: "users"
        operation: delete
        where: {id: 123}
    ```
    """
    from zOS.L3_Abstraction.m_zWizard import zWizard
    
    wizard = zWizard(zcli=zcli)
    
    workflow_items = {
        "view_dashboard": {
            "zRBAC": {
                "require_auth": True  # Any authenticated user
            },
            "type": "zDisplay",
            "content": "Welcome to dashboard"
        },
        
        "manage_users": {
            "zRBAC": {
                "require_role": "admin"  # Admin role required
            },
            "type": "zDisplay",
            "content": "User management panel"
        },
        
        "delete_data": {
            "zRBAC": {
                "require_permission": "data.delete"  # Specific permission
            },
            "type": "zData",
            "model": "users",
            "operation": "delete",
            "where": {"id": 123}
        }
    }
    
    # Execute workflow
    # RBAC checks happen automatically before each step
    # Denied steps are skipped and logged
    result = wizard.execute_loop(workflow_items)
    
    print(f"Workflow completed ({len(result)} steps executed)")


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 5: zHAT INTERPOLATION - CROSS-STEP RESULT REFERENCES
# ═══════════════════════════════════════════════════════════════════════════

def example_zhat_interpolation(zcli: Any) -> None:
    """
    Example 5: Using zHat to reference previous step results.
    
    Use Case: Multi-step workflow where later steps use earlier results
    
    Args:
        zcli: zCLI instance
    
    Interpolation Patterns:
    -----------------------
    - zHat[0], zHat[1]                      # Numeric (backward compatible)
    - zHat["step_name"], zHat['step_name']  # Key-based (semantic)
    - zHat[step_name]                       # Without quotes (YAML)
    - zHat.step_name                        # Attribute access (Python)
    
    YAML equivalent:
    ----------------
    ```yaml
    get_user_id:
      zFunc:
        function: fetch_user_id
        args: ["alice"]
    
    get_user_details:
      zFunc:
        function: fetch_user_details
        args: ["{{ zHat.get_user_id }}"]  # Uses previous result
    
    display_info:
      zDisplay:
        event: text
        content: "User {{ zHat.get_user_id }} has email {{ zHat.get_user_details.email }}"
    ```
    """
    from zOS.L3_Abstraction.m_zWizard import zWizard
    
    wizard = zWizard(zcli=zcli)
    
    workflow = {
        "get_user_id": {
            "type": "zFunc",
            "function": "fetch_user_id",
            "args": ["alice"]
        },
        
        "get_user_details": {
            "type": "zFunc",
            "function": "fetch_user_details",
            "args": ["{{ zHat.get_user_id }}"]  # Interpolation!
        },
        
        "display_info": {
            "type": "zDisplay",
            "event": "text",
            "content": "User {{ zHat[0] }} has email {{ zHat.get_user_details.email }}"
        }
    }
    
    result = wizard.handle(workflow)
    
    # Access results using triple-access pattern
    print(f"User ID (numeric): {result[0]}")
    print(f"User ID (key): {result['get_user_id']}")
    print(f"User ID (attribute): {result.get_user_id}")


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 6: ERROR HANDLING - CUSTOM NAVIGATION CALLBACKS
# ═══════════════════════════════════════════════════════════════════════════

def example_error_handling_callbacks(zcli: Any) -> None:
    """
    Example 6: Custom error handling with navigation callbacks.
    
    Use Case: Graceful error recovery with user feedback
    
    Args:
        zcli: zCLI instance
    """
    from zOS.L3_Abstraction.m_zWizard import zWizard
    
    wizard = zWizard(zcli=zcli)
    
    # Define custom navigation callbacks
    def handle_error(error: Exception, key: str) -> str:
        """Custom error handler."""
        print(f"ERROR in step '{key}': {error}")
        print("Rolling back changes...")
        # Custom recovery logic here
        return "error"  # Signal to stop execution
    
    def handle_back(_signal: str) -> str:
        """Custom back handler."""
        print("User requested to go back")
        # Custom logic for handling zBack
        return "zBack"
    
    def handle_exit(_signal: str) -> str:
        """Custom exit handler."""
        print("User requested to exit wizard")
        # Cleanup logic here
        return "exit"
    
    navigation_callbacks = {
        "on_error": handle_error,
        "on_back": handle_back,
        "on_exit": handle_exit,
        "on_stop": lambda sig: print(f"Wizard stopped: {sig}")
    }
    
    workflow_items = {
        "step1": {"type": "zDisplay", "content": "Step 1"},
        "step2": {"type": "zDisplay", "content": "Step 2"},
        "step3": {"type": "zDisplay", "content": "Step 3"}
    }
    
    # Execute with custom callbacks
    result = wizard.execute_loop(
        workflow_items,
        navigation_callbacks=navigation_callbacks
    )
    
    # Handle navigation signals
    if result == "error":
        print("Workflow stopped due to error")
    elif result == "zBack":
        print("Workflow went back")
    elif result == "exit":
        print("Workflow exited")
    else:
        print("Workflow completed successfully")


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 7: ADVANCED PATTERN - START FROM SPECIFIC KEY
# ═══════════════════════════════════════════════════════════════════════════

def example_start_from_key(zcli: Any) -> None:
    """
    Example 7: Start wizard execution from a specific step.
    
    Use Case: Resume wizard from a saved checkpoint
    
    Args:
        zcli: zCLI instance
    """
    from zOS.L3_Abstraction.m_zWizard import zWizard
    
    wizard = zWizard(zcli=zcli)
    
    workflow_items = {
        "step1": {"type": "zDisplay", "content": "Step 1"},
        "step2": {"type": "zDisplay", "content": "Step 2"},
        "step3": {"type": "zDisplay", "content": "Step 3"},
        "step4": {"type": "zDisplay", "content": "Step 4"}
    }
    
    # Start from step3 (skip step1 and step2)
    result = wizard.execute_loop(
        workflow_items,
        start_key="step3"  # Resume from here
    )
    
    print(f"Executed {len(result)} steps (step3 and step4 only)")


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 8: CUSTOM DISPATCH FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

def example_custom_dispatch(zcli: Any) -> None:
    """
    Example 8: Provide custom dispatch function for specialized handling.
    
    Use Case: Custom step execution logic
    
    Args:
        zcli: zCLI instance
    """
    from zOS.L3_Abstraction.m_zWizard import zWizard
    
    wizard = zWizard(zcli=zcli)
    
    # Custom dispatch function
    def custom_dispatch(key: str, value: Any) -> str:
        """Custom step dispatcher."""
        print(f"Custom dispatch for key: {key}")
        
        # Custom logic based on step type
        if isinstance(value, dict) and "custom_action" in value:
            # Handle custom action
            print(f"Executing custom action: {value['custom_action']}")
            return f"Result from {key}"
        else:
            # Fall back to default dispatch
            return zcli.dispatch.handle(key, value)
    
    workflow_items = {
        "step1": {"custom_action": "special_operation"},
        "step2": {"type": "zDisplay", "content": "Normal step"}
    }
    
    # Execute with custom dispatch
    result = wizard.execute_loop(
        workflow_items,
        dispatch_fn=custom_dispatch
    )
    
    print(f"Workflow completed with custom dispatch: {len(result)} steps")


# ═══════════════════════════════════════════════════════════════════════════
# USAGE NOTES
# ═══════════════════════════════════════════════════════════════════════════

# Best Practices:
# ---------------
# 1. **Use Transactions**: Enable `_transaction: true` for multi-step data operations
# 2. **RBAC Everything**: Protect sensitive steps with `zRBAC` metadata
# 3. **zHat Interpolation**: Reference previous results for dynamic workflows
# 4. **Error Callbacks**: Provide custom error handlers for graceful recovery
# 5. **WizardHat Access**: Use attribute access (zHat.step_name) for cleaner code
#
# Common Patterns:
# ----------------
# - **Data Pipeline**: fetch → transform → store (with transactions)
# - **User Input**: prompt → validate → confirm → execute
# - **Menu System**: display → select → execute → return (with RBAC)
# - **Batch Operations**: loop over items → execute → accumulate results
#
# Performance Tips:
# -----------------
# - Transaction mode reduces database round trips
# - Schema cache connection reuse improves performance
# - RBAC checks are cached per session
# - WizardHat uses efficient dual-storage (list + dict)
#
# See Also:
# ---------
# - wizard_hat.py: WizardHat triple-access container
# - wizard_interpolation.py: Template variable interpolation
# - wizard_transactions.py: Transaction management
# - wizard_rbac.py: Role-based access control
# - wizard_exceptions.py: Custom exception types

