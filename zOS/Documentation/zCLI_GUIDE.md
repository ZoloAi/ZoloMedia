# Building Applications with zOS

**A Comprehensive Guide to zOS Architecture, Patterns, and Application Development**

**Version**: 1.5.0  
**Audience**: Developers, Architects, LLMs building zOS-based applications  
**Purpose**: Conceptual understanding and application design patterns

---

## Table of Contents

1. [What is zOS?](#what-is-zcli)
2. [Core Philosophy](#core-philosophy)
3. [Architecture Overview](#architecture-overview)
4. [Building Your First Application](#building-your-first-application)
5. [Application Patterns](#application-patterns)
6. [Integration Strategies](#integration-strategies)
7. [Advanced Concepts](#advanced-concepts)
8. [Real-World Examples](#real-world-examples)
9. [Best Practices](#best-practices)
10. [Troubleshooting & Debugging](#troubleshooting--debugging)

---

## What is zOS?

**zOS** (Zolo Command Line Interface) is a **declarative application framework** that enables developers to build sophisticated command-line applications using YAML configuration files instead of imperative code.

### Key Differentiators

| Traditional CLI | zOS |
|----------------|------|
| Write Python/JS code | Write YAML configs |
| Hard-coded menus | Dynamic UI from files |
| Manual data handling | Built-in CRUD operations |
| Custom auth logic | Integrated authentication |
| Roll your own plugins | Standard plugin system |

### What Can You Build?

- **Data Management Tools**: Database frontends, CSV processors, data migration utilities
- **Interactive Wizards**: Multi-step workflows, configuration generators, installers
- **Admin Dashboards**: System monitoring, user management, deployment tools
- **Educational Tools**: Interactive tutorials, quizzes, learning management
- **Business Applications**: Inventory systems, CRM tools, reporting dashboards
- **DevOps Utilities**: Deployment pipelines, log analyzers, environment managers

---

## Core Philosophy

### 1. **Declarative Over Imperative**

Instead of writing:
```python
# Traditional approach
print("Main Menu")
print("1. View Users")
print("2. Add User")
choice = input("Select: ")
if choice == "1":
    view_users()
elif choice == "2":
    add_user()
```

You declare:
```yaml
# zOS approach (zUI file)
Main Menu:
  label: "Main Menu"
  options:
    - label: "View Users"
      zLink: "@.Users.View"
    - label: "Add User"
      zLink: "@.Users.Add"
```

### 2. **Separation of Concerns**

- **UI Layer** (`zUI.*.yaml`): What users see and interact with
- **Data Layer** (`zSchema.*.yaml`): How data is structured and stored
- **Logic Layer** (Plugins): Custom business logic when needed
- **Configuration Layer** (`zConfig`): Environment, paths, settings

### 3. **Convention Over Configuration**

- File naming: `zUI.app_name.yaml`, `zSchema.db_name.yaml`
- Path resolution: `@.` (workspace), `~.` (home), `zMachine.` (data dir)
- Command structure: `subsystem action target --flags`

### 4. **Progressive Enhancement**

Start simple, add complexity as needed:

1. **Level 1**: Basic menus and navigation
2. **Level 2**: Data operations (CRUD)
3. **Level 3**: Wizards and workflows
4. **Level 4**: Custom plugins and integrations
5. **Level 5**: Multi-user, authentication, remote services

---

## Architecture Overview

### The 3-Layer Model

```
┌─────────────────────────────────────────────────────────┐
│ Layer 3: ORCHESTRATION                                  │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ zWalker: UI/Menu Navigation & Flow Control          │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ Layer 2: SERVICES                                       │
│ ┌──────────┬──────────┬──────────┬──────────┐          │
│ │ zShell   │ zWizard  │ zUtils   │ zData    │          │
│ │ Commands │ Workflows│ Plugins  │ CRUD Ops │          │
│ └──────────┴──────────┴──────────┴──────────┘          │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ Layer 1: CORE                                           │
│ ┌────────┬────────┬─────────┬─────────┬────────┐       │
│ │zDisplay│ zAuth  │zDispatch│zParser  │zLoader │       │
│ │ Output │ Access │ Routing │ Syntax  │ Cache  │       │
│ └────────┴────────┴─────────┴─────────┴────────┘       │
│ ┌────────┬────────┬─────────┬─────────┐               │
│ │ zFunc  │zDialog │ zOpen   │zNavigate│               │
│ │Evaluate│ Forms  │ Files   │ Menus   │               │
│ └────────┴────────┴─────────┴─────────┘               │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ Layer 0: FOUNDATION                                     │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ zConfig: Paths, Session, Logger, Machine Config    │ │
│ │ zComm: WebSocket & Service Communication           │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Subsystem Responsibilities

#### Layer 0: Foundation (No zDisplay Available)
- **zConfig**: Environment detection, path resolution, session management, logging
- **zComm**: WebSocket server (zBifrost), service communication

#### Layer 1: Core (zDisplay Available)
- **zDisplay**: All output rendering (text, tables, menus, dialogs)
- **zAuth**: Authentication and authorization
- **zDispatch**: Command routing and execution
- **zParser**: Path resolution (`@.`, `~.`, `zMachine.`), plugin invocation (`&`)
- **zLoader**: 4-tier caching (pinned, schema, file, plugin)
- **zFunc**: Expression evaluation and function calls
- **zDialog**: Interactive forms and user input
- **zOpen**: File operations and content display
- **zNavigation**: Menu rendering and breadcrumb management

#### Layer 2: Services
- **zShell**: Command-line interface and built-in commands
- **zWizard**: Multi-step transactional workflows
- **zUtils**: Plugin system and utilities
- **zData**: Database operations (SQLite, CSV, PostgreSQL)

#### Layer 3: Orchestration
- **zWalker**: UI navigation, menu orchestration, session flow

---

## Building Your First Application

### Example: Student Grade Tracker

Let's build a complete application step-by-step.

#### Step 1: Define Your Data (Schema)

**File**: `zSchema.grades.yaml`

```yaml
# Data structure definition
metadata:
  paradigm: sqlite
  database: zMachine.grades/student_grades.db
  version: "1.0"

tables:
  students:
    columns:
      - name: id
        type: INTEGER
        constraints: [PRIMARY KEY, AUTOINCREMENT]
      - name: name
        type: TEXT
        constraints: [NOT NULL]
      - name: email
        type: TEXT
        constraints: [UNIQUE]
      - name: grade_level
        type: INTEGER
        
  assignments:
    columns:
      - name: id
        type: INTEGER
        constraints: [PRIMARY KEY, AUTOINCREMENT]
      - name: title
        type: TEXT
        constraints: [NOT NULL]
      - name: max_points
        type: INTEGER
        constraints: [NOT NULL]
      - name: due_date
        type: TEXT
        
  grades:
    columns:
      - name: id
        type: INTEGER
        constraints: [PRIMARY KEY, AUTOINCREMENT]
      - name: student_id
        type: INTEGER
        constraints: [NOT NULL, "FOREIGN KEY REFERENCES students(id)"]
      - name: assignment_id
        type: INTEGER
        constraints: [NOT NULL, "FOREIGN KEY REFERENCES assignments(id)"]
      - name: score
        type: INTEGER
      - name: submitted_date
        type: TEXT
```

#### Step 2: Create Your UI (Menus)

**File**: `zUI.grades.yaml`

```yaml
# Main menu
Main Menu:
  label: "📚 Student Grade Tracker"
  options:
    - label: "👥 Manage Students"
      zLink: "@.Students Menu"
    - label: "📝 Manage Assignments"
      zLink: "@.Assignments Menu"
    - label: "📊 View Grades"
      zLink: "@.Grades Menu"
    - label: "📈 Reports"
      zLink: "@.Reports Menu"
    - label: "⚙️ Settings"
      zLink: "@.Settings Menu"

# Student management
Students Menu:
  label: "👥 Student Management"
  options:
    - label: "View All Students"
      zAction:
        - action: read
          table: students
          model: $grades
          fields: "*"
          order_by: "name ASC"
    - label: "Add New Student"
      zLink: "@.Add Student"
    - label: "Search Students"
      zLink: "@.Search Students"
    - label: "← Back"
      zLink: "$back"

# Add student form
Add Student:
  label: "Add New Student"
  zDialog:
    fields:
      - name: name
        label: "Student Name"
        type: text
        required: true
      - name: email
        label: "Email Address"
        type: text
        required: true
      - name: grade_level
        label: "Grade Level (9-12)"
        type: number
        min: 9
        max: 12
        required: true
    submit:
      zAction:
        - action: insert
          table: students
          model: $grades
          fields: "name,email,grade_level"
          values: "${name},${email},${grade_level}"
      zLink: "@.Students Menu"

# Assignments menu
Assignments Menu:
  label: "📝 Assignment Management"
  options:
    - label: "View All Assignments"
      zAction:
        - action: read
          table: assignments
          model: $grades
          fields: "*"
          order_by: "due_date DESC"
    - label: "Create Assignment"
      zLink: "@.Create Assignment"
    - label: "← Back"
      zLink: "$back"

# Grades menu with filtering
Grades Menu:
  label: "📊 Grade Management"
  options:
    - label: "View All Grades"
      zAction:
        - action: read
          table: grades
          model: $grades
          fields: "*"
          join: "students ON grades.student_id = students.id"
          join: "assignments ON grades.assignment_id = assignments.id"
    - label: "Enter Grade"
      zLink: "@.Enter Grade"
    - label: "Grade by Student"
      zLink: "@.Grade by Student"
    - label: "Grade by Assignment"
      zLink: "@.Grade by Assignment"
    - label: "← Back"
      zLink: "$back"

# Reports menu
Reports Menu:
  label: "📈 Reports & Analytics"
  options:
    - label: "Student Averages"
      zAction:
        - action: read
          table: grades
          model: $grades
          fields: "students.name, AVG(grades.score) as average"
          join: "students ON grades.student_id = students.id"
          group_by: "students.name"
          order_by: "average DESC"
    - label: "Assignment Statistics"
      zAction:
        - action: read
          table: grades
          model: $grades
          fields: "assignments.title, AVG(score) as avg, MIN(score) as min, MAX(score) as max"
          join: "assignments ON grades.assignment_id = assignments.id"
          group_by: "assignments.title"
    - label: "Class Performance"
      zFunc: "&GradeReports.class_performance()"
    - label: "← Back"
      zLink: "$back"

# Settings
Settings Menu:
  label: "⚙️ Settings"
  options:
    - label: "Export Data (CSV)"
      zFunc: "&DataExport.export_to_csv('$grades', 'grades')"
    - label: "Import Data (CSV)"
      zFunc: "&DataImport.import_from_csv('$grades')"
    - label: "Reset Database"
      zLink: "@.Confirm Reset"
    - label: "← Back"
      zLink: "$back"
```

#### Step 3: Initialize Your Application

**File**: `grade_tracker.py`

```python
#!/usr/bin/env python3
"""Student Grade Tracker - Built with zOS"""

from zOS import zOS
from pathlib import Path

def main():
    # Get the directory where this script lives
    app_dir = Path(__file__).parent.absolute()
    
    # Configure zOS
    zspark_config = {
        "zSpark": "Grade Tracker v1.0",
        "zWorkspace": str(app_dir),
        "zVaFilename": "@.zUI.grades",  # UI file
        "zBlock": "Main Menu",          # Starting menu
        "zMode": "Terminal",
        "logger": "info",
        "plugins": [
            # Optional: Load custom plugins
            # "grade_tracker.plugins.reports",
            # "grade_tracker.plugins.export",
        ]
    }
    
    # Initialize zOS
    zcli = zOS(zspark_config)
    
    # Load the schema
    zcli.loader.handle("@.zSchema.grades", {"cache_as": "grades"})
    
    # Run the application
    zcli.run()

if __name__ == "__main__":
    main()
```

#### Step 4: Run Your Application

```bash
# Make executable
chmod +x grade_tracker.py

# Run
./grade_tracker.py

# Or via Python
python grade_tracker.py
```

**That's it!** You now have a fully functional grade tracking application with:
- ✅ Database storage (SQLite)
- ✅ CRUD operations
- ✅ Interactive menus
- ✅ Data validation
- ✅ Reporting capabilities

---

## Application Patterns

### Pattern 1: Simple Data Browser

**Use Case**: View and search data from a database or CSV file.

**Components**:
- Schema file defining data structure
- UI file with read-only views
- Optional search/filter dialogs

**Example**: Employee directory, product catalog, log viewer

```yaml
# zUI.browser.yaml
Main:
  label: "Data Browser"
  options:
    - label: "View All Records"
      zAction:
        - action: read
          table: records
          model: $data
    - label: "Search"
      zLink: "@.Search"

Search:
  label: "Search Records"
  zDialog:
    fields:
      - name: query
        label: "Search term"
        type: text
    submit:
      zAction:
        - action: read
          table: records
          model: $data
          where: "name LIKE '%${query}%'"
```

### Pattern 2: CRUD Application

**Use Case**: Full create, read, update, delete operations.

**Components**:
- Schema with all tables
- UI with separate menus for each operation
- Dialogs for data entry
- Confirmation prompts for deletions

**Example**: Contact manager, inventory system, task tracker

```yaml
# zUI.crud.yaml
Main:
  options:
    - label: "View Items"
      zAction: [...]
    - label: "Add Item"
      zLink: "@.Add"
    - label: "Edit Item"
      zLink: "@.Edit"
    - label: "Delete Item"
      zLink: "@.Delete"

Add:
  zDialog:
    fields: [...]
    submit:
      zAction:
        - action: insert
          table: items
          model: $data
          fields: "name,description,quantity"
          values: "${name},${description},${quantity}"

Edit:
  zDialog:
    fields: [...]
    submit:
      zAction:
        - action: update
          table: items
          model: $data
          set: "name='${name}', quantity=${quantity}"
          where: "id = ${item_id}"

Delete:
  label: "⚠️ Confirm Deletion"
  options:
    - label: "Yes, Delete"
      zAction:
        - action: delete
          table: items
          model: $data
          where: "id = ${item_id}"
    - label: "Cancel"
      zLink: "$back"
```

### Pattern 3: Multi-Step Wizard

**Use Case**: Complex workflows requiring multiple steps.

**Components**:
- Wizard schema defining steps
- UI with step-by-step navigation
- Transaction support (all-or-nothing)

**Example**: User onboarding, order processing, system setup

```yaml
# zUI.wizard.yaml
Start Wizard:
  label: "Setup Wizard"
  zWizard:
    schema: $wizard_schema
    steps:
      - name: "Step 1: Basic Info"
        zDialog:
          fields:
            - name: username
              type: text
        zAction:
          - action: insert
            table: users
            model: $data
            fields: "username"
            values: "${username}"
            
      - name: "Step 2: Preferences"
        zDialog:
          fields:
            - name: theme
              type: select
              options: ["light", "dark"]
        zAction:
          - action: insert
            table: preferences
            model: $data
            fields: "user_id,theme"
            values: "${user_id},${theme}"
            
      - name: "Step 3: Confirmation"
        zAction:
          - action: read
            table: users
            model: $data
            where: "id = ${user_id}"
```

### Pattern 4: Dashboard Application

**Use Case**: Display aggregated data and metrics.

**Components**:
- Schema with analytical queries
- UI with report views
- Optional plugins for custom calculations

**Example**: Sales dashboard, system monitor, analytics tool

```yaml
# zUI.dashboard.yaml
Dashboard:
  label: "📊 Dashboard"
  options:
    - label: "Key Metrics"
      zAction:
        - action: read
          table: sales
          model: $data
          fields: "COUNT(*) as total, SUM(amount) as revenue, AVG(amount) as avg_sale"
    - label: "Top Products"
      zAction:
        - action: read
          table: sales
          model: $data
          fields: "product, COUNT(*) as sales"
          group_by: "product"
          order_by: "sales DESC"
          limit: 10
    - label: "Recent Activity"
      zAction:
        - action: read
          table: sales
          model: $data
          fields: "*"
          order_by: "date DESC"
          limit: 20
    - label: "Custom Report"
      zFunc: "&Reports.generate_custom()"
```

### Pattern 5: Plugin-Extended Application

**Use Case**: Core functionality in YAML, custom logic in Python.

**Components**:
- Schema and UI for standard operations
- Python plugins for complex logic
- Plugin invocation via `&` syntax

**Example**: Data processor, API client, automation tool

**Plugin File**: `plugins/custom_logic.py`

```python
"""Custom business logic plugin"""

def calculate_discount(zcli, customer_id, order_total):
    """Calculate customer-specific discount"""
    # Access zOS subsystems
    result = zcli.data.handle({
        "action": "read",
        "table": "customers",
        "model": "$data",
        "where": f"id = {customer_id}",
        "fields": "loyalty_tier"
    })
    
    tier = result[0]["loyalty_tier"]
    
    # Business logic
    discounts = {"bronze": 0.05, "silver": 0.10, "gold": 0.15}
    discount = discounts.get(tier, 0)
    
    final_price = order_total * (1 - discount)
    
    zcli.display.success(f"Discount applied: {discount*100}%")
    zcli.display.text(f"Final price: ${final_price:.2f}")
    
    return final_price

def export_report(zcli, format="pdf"):
    """Generate and export report"""
    # Custom export logic
    pass
```

**UI File**: `zUI.app.yaml`

```yaml
Process Order:
  label: "Process Order"
  zDialog:
    fields:
      - name: customer_id
        type: number
      - name: order_total
        type: number
    submit:
      zFunc: "&custom_logic.calculate_discount(${customer_id}, ${order_total})"
      zLink: "@.Confirm Order"
```

---

## Integration Strategies

### Strategy 1: Embed zOS in Existing Python Applications

```python
# your_app.py
from zOS import zOS

class YourApplication:
    def __init__(self):
        self.zcli = zOS({
            "zWorkspace": "/path/to/configs",
            "logger": "info"
        })
        
    def run_admin_panel(self):
        """Launch zOS-based admin interface"""
        self.zcli.loader.handle("@.zUI.admin", {})
        self.zcli.walker.run()
        
    def run_data_import(self, csv_file):
        """Use zOS for data operations"""
        self.zcli.loader.handle("@.zSchema.mydb", {"cache_as": "db"})
        # Import logic using zcli.data
```

### Strategy 2: Use zOS as a Microservice

```python
# api_server.py
from flask import Flask, request
from zOS import zOS

app = Flask(__name__)
zcli = zOS({"zWorkspace": "/app/configs"})

@app.route("/execute", methods=["POST"])
def execute_command():
    command = request.json.get("command")
    result = zcli.run_command(command)
    return {"result": result}

@app.route("/data/<table>", methods=["GET"])
def get_data(table):
    result = zcli.data.handle({
        "action": "read",
        "table": table,
        "model": "$db"
    })
    return {"data": result}
```

### Strategy 3: Extend zOS with Custom Subsystems

```python
# custom_subsystem.py
class MyCustomSubsystem:
    def __init__(self, zcli):
        self.zcli = zcli
        self.logger = zcli.logger
        
    def handle(self, request):
        """Custom subsystem logic"""
        self.logger.info("Custom subsystem called")
        # Your logic here
        return {"status": "success"}

# In your app initialization
from zOS import zOS
zcli = zOS()
zcli.custom = MyCustomSubsystem(zcli)

# Now available throughout zOS
# zcli.custom.handle(...)
```

### Strategy 4: Multi-Tenant Applications

```python
# multi_tenant.py
from zOS import zOS

class TenantManager:
    def __init__(self):
        self.tenants = {}
        
    def get_tenant_cli(self, tenant_id):
        """Get or create zOS instance for tenant"""
        if tenant_id not in self.tenants:
            self.tenants[tenant_id] = zOS({
                "zWorkspace": f"/data/tenants/{tenant_id}",
                "logger": "info"
            })
        return self.tenants[tenant_id]
        
    def execute_for_tenant(self, tenant_id, command):
        """Execute command in tenant context"""
        zcli = self.get_tenant_cli(tenant_id)
        return zcli.run_command(command)
```

---

## Advanced Concepts

### Concept 1: Session State Management

The `zcli.session` dictionary persists data across menu navigations:

```python
# In a plugin
def save_context(zcli, user_id):
    zcli.session["current_user"] = user_id
    zcli.session["last_action"] = "login"
    
def get_context(zcli):
    user_id = zcli.session.get("current_user")
    return user_id
```

```yaml
# In UI file - access session variables
User Profile:
  label: "Profile for ${current_user}"
  zAction:
    - action: read
      table: users
      model: $data
      where: "id = ${current_user}"
```

### Concept 2: Dynamic Menu Generation

```python
# Plugin: menu_builder.py
def build_menu(zcli):
    """Generate menu options dynamically"""
    # Query database
    categories = zcli.data.handle({
        "action": "read",
        "table": "categories",
        "model": "$data",
        "fields": "id,name"
    })
    
    # Build menu structure
    menu = {
        "label": "Dynamic Menu",
        "options": []
    }
    
    for cat in categories:
        menu["options"].append({
            "label": cat["name"],
            "zLink": f"@.Category_{cat['id']}"
        })
    
    # Store in session for zWalker
    zcli.session["dynamic_menu"] = menu
    
    return menu
```

### Concept 3: Cross-Schema Operations

```yaml
# Load multiple schemas
Init:
  zAction:
    - action: load
      schema: "@.zSchema.users"
      cache_as: "users_db"
    - action: load
      schema: "@.zSchema.orders"
      cache_as: "orders_db"

# Use in operations
View User Orders:
  zAction:
    - action: read
      table: users
      model: $users_db
      where: "id = ${user_id}"
    - action: read
      table: orders
      model: $orders_db
      where: "user_id = ${user_id}"
```

### Concept 4: Event-Driven Workflows

```python
# Plugin: events.py
class EventHandler:
    def __init__(self, zcli):
        self.zcli = zcli
        self.listeners = {}
        
    def on(self, event_name, callback):
        """Register event listener"""
        if event_name not in self.listeners:
            self.listeners[event_name] = []
        self.listeners[event_name].append(callback)
        
    def emit(self, event_name, data):
        """Trigger event"""
        if event_name in self.listeners:
            for callback in self.listeners[event_name]:
                callback(self.zcli, data)

# Usage
events = EventHandler(zcli)

events.on("user_created", lambda zcli, user: 
    zcli.display.success(f"Welcome {user['name']}!"))

events.on("user_created", lambda zcli, user:
    zcli.data.handle({
        "action": "insert",
        "table": "audit_log",
        "model": "$data",
        "fields": "event,user_id",
        "values": f"'user_created',{user['id']}"
    }))

# Trigger
events.emit("user_created", {"id": 123, "name": "Alice"})
```

### Concept 5: Caching Strategies

zOS provides 4-tier caching:

```python
# Tier 1: Pinned Cache (persistent across sessions)
zcli.loader.handle("@.zSchema.config", {
    "cache_as": "config",
    "pin": True  # Never evicted
})

# Tier 2: Schema Cache (schema definitions)
zcli.loader.handle("@.zSchema.users", {
    "cache_as": "users"
})

# Tier 3: File Cache (general files)
zcli.loader.handle("@.data.large_file.json", {
    "cache_as": "data"
})

# Tier 4: Plugin Cache (Python modules)
zcli.utils.load_plugins(["my_plugin"])

# Access cached items
schema = zcli.loader.cache.schema_cache.get("users")
data = zcli.loader.cache.file_cache.get("data")
```

---

## Real-World Examples

### Example 1: E-Commerce Order Management

**Scenario**: Small business needs to track orders, inventory, and customers.

**Architecture**:
```
ecommerce/
├── main.py                          # Entry point
├── zSchema.ecommerce.yaml           # Database schema
├── zUI.ecommerce.yaml               # Main UI
├── plugins/
│   ├── inventory.py                 # Stock management
│   ├── reports.py                   # Sales reports
│   └── notifications.py             # Email/SMS alerts
└── data/
    └── ecommerce.db                 # SQLite database
```

**Key Features**:
- Customer database with purchase history
- Product catalog with inventory tracking
- Order processing workflow (wizard)
- Sales reports and analytics
- Low stock alerts (plugin)
- Email confirmations (plugin)

**Implementation Highlights**:

```yaml
# zUI.ecommerce.yaml (excerpt)
Process Order:
  label: "New Order"
  zWizard:
    steps:
      - name: "Select Customer"
        zDialog:
          fields:
            - name: customer_id
              label: "Customer"
              type: select
              options: "&inventory.get_customers()"
              
      - name: "Add Products"
        zDialog:
          fields:
            - name: products
              label: "Products"
              type: multi-select
              options: "&inventory.get_available_products()"
              
      - name: "Calculate Total"
        zFunc: "&inventory.calculate_order_total(${products})"
        
      - name: "Confirm & Process"
        zAction:
          - action: insert
            table: orders
            model: $ecommerce
            fields: "customer_id,total,status"
            values: "${customer_id},${order_total},'pending'"
          - action: update
            table: inventory
            model: $ecommerce
            set: "quantity = quantity - ${quantity}"
            where: "product_id IN (${product_ids})"
        zFunc: "&notifications.send_order_confirmation(${order_id})"
```

### Example 2: Student Information System

**Scenario**: School needs to manage students, courses, grades, and attendance.

**Architecture**:
```
school_system/
├── main.py
├── zSchema.school.yaml              # Students, courses, grades, attendance
├── zUI.admin.yaml                   # Admin interface
├── zUI.teacher.yaml                 # Teacher interface
├── zUI.student.yaml                 # Student portal
├── plugins/
│   ├── grading.py                   # GPA calculations
│   ├── attendance.py                # Attendance tracking
│   └── reports.py                   # Report cards
└── data/
    └── school.db
```

**Key Features**:
- Multi-role access (admin, teacher, student)
- Course enrollment management
- Grade entry and GPA calculation
- Attendance tracking
- Report card generation
- Parent notifications

### Example 3: DevOps Deployment Tool

**Scenario**: Deploy applications across multiple environments.

**Architecture**:
```
deploy_tool/
├── main.py
├── zSchema.deployments.yaml         # Deployment history
├── zUI.deploy.yaml                  # Deployment wizard
├── plugins/
│   ├── docker.py                    # Docker operations
│   ├── kubernetes.py                # K8s deployments
│   ├── aws.py                       # AWS integration
│   └── notifications.py             # Slack/email alerts
└── configs/
    ├── dev.yaml                     # Dev environment
    ├── staging.yaml                 # Staging environment
    └── prod.yaml                    # Production environment
```

**Key Features**:
- Environment-specific configurations
- Pre-deployment checks (plugin)
- Rollback capabilities
- Deployment history tracking
- Automated testing integration
- Notification on success/failure

### Example 4: Research Data Collector

**Scenario**: Researchers need to collect, validate, and analyze survey data.

**Architecture**:
```
research_tool/
├── main.py
├── zSchema.survey.yaml              # Survey responses
├── zUI.collector.yaml               # Data collection interface
├── zUI.analysis.yaml                # Analysis dashboard
├── plugins/
│   ├── validation.py                # Data validation rules
│   ├── statistics.py                # Statistical analysis
│   └── export.py                    # Export to SPSS/R
└── data/
    ├── responses.db
    └── exports/
```

**Key Features**:
- Dynamic survey forms (zDialog)
- Real-time validation (plugins)
- Data export (CSV, SPSS, R)
- Statistical analysis (plugins)
- Visualization generation
- Progress tracking

---

## Best Practices

### 1. Project Structure

**Recommended Layout**:
```
my_zcli_app/
├── main.py                          # Entry point
├── README.md                        # Documentation
├── requirements.txt                 # Dependencies
├── configs/
│   ├── zSchema.*.yaml               # Data schemas
│   └── zUI.*.yaml                   # UI definitions
├── plugins/
│   ├── __init__.py
│   ├── business_logic.py
│   └── integrations.py
├── data/                            # Runtime data (gitignored)
│   └── .gitkeep
├── tests/
│   ├── test_plugins.py
│   └── test_workflows.py
└── docs/
    ├── USER_GUIDE.md
    └── API_REFERENCE.md
```

### 2. Naming Conventions

**Files**:
- Schemas: `zSchema.{domain}.yaml` (e.g., `zSchema.users.yaml`)
- UI files: `zUI.{app_name}.yaml` (e.g., `zUI.admin.yaml`)
- Plugins: `{feature}.py` (e.g., `authentication.py`)

**YAML Keys**:
- Menu blocks: PascalCase (e.g., `Main Menu`, `User Settings`)
- Fields: snake_case (e.g., `user_id`, `created_at`)
- Cache aliases: lowercase (e.g., `$users`, `$config`)

**Variables**:
- Session: `${variable_name}`
- Environment: `$ENV_VAR`
- Cache: `$cache_alias`

### 3. Error Handling

**In Plugins**:
```python
def safe_operation(zcli, data):
    try:
        # Your logic
        result = process_data(data)
        zcli.display.success("Operation completed")
        return result
    except ValueError as e:
        zcli.logger.error(f"Validation error: {e}")
        zcli.display.error(f"Invalid data: {e}")
        return None
    except Exception as e:
        zcli.logger.error(f"Unexpected error: {e}", exc_info=True)
        zcli.display.error("An error occurred. Check logs.")
        return None
```

**In UI Files**:
```yaml
Risky Operation:
  label: "⚠️ Warning: This cannot be undone"
  options:
    - label: "Proceed"
      zAction:
        - action: delete
          table: records
          model: $data
          where: "id = ${record_id}"
      zLink: "@.Success Message"
    - label: "Cancel"
      zLink: "$back"
```

### 4. Security Considerations

**Authentication**:
```python
# Plugin: auth.py
def require_auth(zcli):
    """Ensure user is authenticated"""
    if not zcli.session.get("authenticated"):
        zcli.display.error("Authentication required")
        zcli.walker.navigate("@.Login")
        return False
    return True

def check_permission(zcli, required_role):
    """Check user has required role"""
    user_role = zcli.session.get("user_role")
    if user_role != required_role:
        zcli.display.error("Insufficient permissions")
        return False
    return True
```

```yaml
Admin Panel:
  label: "Admin Panel"
  zFunc: "&auth.require_auth() and &auth.check_permission('admin')"
  options:
    - label: "Manage Users"
      zLink: "@.User Management"
```

**Input Sanitization**:
```python
def sanitize_input(zcli, user_input):
    """Sanitize user input to prevent SQL injection"""
    import re
    # Remove dangerous characters
    sanitized = re.sub(r'[;\'"\\]', '', user_input)
    return sanitized
```

**Sensitive Data**:
```python
# Never log sensitive data
zcli.logger.info(f"User {user_id} logged in")  # ✅ Good
zcli.logger.info(f"Password: {password}")      # ❌ Bad

# Use environment variables for secrets
import os
api_key = os.getenv("API_KEY")
```

### 5. Performance Optimization

**Caching**:
```python
# Cache expensive operations
def get_report_data(zcli):
    cache_key = "monthly_report"
    
    # Check cache first
    if cache_key in zcli.session:
        return zcli.session[cache_key]
    
    # Generate report
    data = expensive_calculation()
    
    # Cache for session
    zcli.session[cache_key] = data
    return data
```

**Lazy Loading**:
```yaml
# Load data only when needed
View Large Dataset:
  label: "View Data"
  options:
    - label: "First 100 rows"
      zAction:
        - action: read
          table: large_table
          model: $data
          limit: 100
    - label: "Search specific records"
      zLink: "@.Search"
```

**Batch Operations**:
```python
# Process in batches
def bulk_insert(zcli, records):
    batch_size = 100
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        zcli.data.handle({
            "action": "insert",
            "table": "records",
            "model": "$data",
            "fields": "name,value",
            "values": batch
        })
```

### 6. Testing Strategies

**Unit Tests for Plugins**:
```python
# tests/test_plugins.py
import unittest
from unittest.mock import Mock
from plugins.business_logic import calculate_total

class TestBusinessLogic(unittest.TestCase):
    def setUp(self):
        self.mock_zcli = Mock()
        
    def test_calculate_total(self):
        result = calculate_total(self.mock_zcli, [10, 20, 30])
        self.assertEqual(result, 60)
```

**Integration Tests**:
```python
# tests/test_workflows.py
from zOS import zOS

def test_order_workflow():
    zcli = zOS({"zWorkspace": "test_data"})
    zcli.loader.handle("@.zSchema.test", {"cache_as": "test"})
    
    # Execute workflow
    result = zcli.run_command("data insert orders --model $test --fields 'customer_id,total' --values '1,100'")
    
    # Verify
    assert result["status"] == "success"
```

### 7. Documentation

**Document Your Schemas**:
```yaml
# zSchema.users.yaml
metadata:
  paradigm: sqlite
  database: zMachine.app/users.db
  version: "1.0"
  description: "User management database"
  author: "Your Name"
  created: "2025-01-01"

tables:
  users:
    description: "Application users"
    columns:
      - name: id
        type: INTEGER
        constraints: [PRIMARY KEY, AUTOINCREMENT]
        description: "Unique user identifier"
      - name: email
        type: TEXT
        constraints: [UNIQUE, NOT NULL]
        description: "User email address (used for login)"
```

**Document Your UI**:
```yaml
# zUI.app.yaml
# Main application interface
# Version: 1.0
# Last updated: 2025-01-01

Main Menu:
  # Primary navigation hub
  label: "Main Menu"
  options:
    - label: "Users"
      # Navigate to user management
      zLink: "@.User Management"
```

**Document Your Plugins**:
```python
"""
Business Logic Plugin

This plugin provides core business logic for the application.

Functions:
    calculate_discount(zcli, customer_id, total): Calculate customer discount
    validate_order(zcli, order_data): Validate order before processing
    send_notification(zcli, user_id, message): Send user notification

Author: Your Name
Version: 1.0
"""

def calculate_discount(zcli, customer_id, total):
    """
    Calculate customer-specific discount.
    
    Args:
        zcli: zOS instance
        customer_id (int): Customer ID
        total (float): Order total
        
    Returns:
        float: Discounted total
        
    Example:
        >>> calculate_discount(zcli, 123, 100.0)
        90.0
    """
    pass
```

---

## Troubleshooting & Debugging

### Common Issues

#### Issue 1: "Schema not found"

**Symptom**: `Error: Schema 'myschema' not found in cache`

**Causes**:
- Schema not loaded before use
- Incorrect cache alias
- Schema file path wrong

**Solutions**:
```python
# Load schema first
zcli.loader.handle("@.zSchema.myschema", {"cache_as": "myschema"})

# Then use it
zcli.data.handle({
    "action": "read",
    "table": "users",
    "model": "$myschema"  # Must match cache_as
})
```

#### Issue 2: "zDisplay not available"

**Symptom**: `AttributeError: 'NoneType' object has no attribute 'display'`

**Cause**: Trying to use `zDisplay` in Layer 0 (zConfig)

**Solution**: Use `print()` in Layer 0, `zcli.display` in Layer 1+

```python
# In zConfig (Layer 0)
print(f"{Colors.INFO}Message{Colors.RESET}")

# In other subsystems (Layer 1+)
zcli.display.text("Message")
```

#### Issue 3: "Plugin function not found"

**Symptom**: `Error: Function 'my_function' not found in plugin`

**Causes**:
- Plugin not loaded
- Function name typo
- Wrong plugin name

**Solutions**:
```python
# Load plugin
zcli.utils.load_plugins(["my_plugin"])

# Verify it's loaded
print(zcli.utils.plugin_manager.plugins)

# Use correct syntax
"&my_plugin.my_function()"  # Correct
"&MyPlugin.my_function()"   # Wrong (case-sensitive)
```

#### Issue 4: "Path not resolved"

**Symptom**: `Error: Could not resolve path '@.configs.schema'`

**Causes**:
- Workspace not set correctly
- File doesn't exist
- Wrong path syntax

**Solutions**:
```python
# Check workspace
print(zcli.session["zWorkspace"])

# Use correct syntax
"@.configs.schema"           # Workspace-relative
"~.configs.schema"           # Home-relative
"zMachine.configs.schema"    # Data directory
"/absolute/path/to/schema"   # Absolute path
```

### Debugging Techniques

#### Enable Debug Logging

```python
# In your main.py
zspark_config = {
    "logger": "debug",  # Show all debug messages
    # ...
}

zcli = zOS(zspark_config)
```

#### Inspect Session State

```python
# In a plugin
def debug_session(zcli):
    """Print current session state"""
    import json
    print(json.dumps(dict(zcli.session), indent=2, default=str))
```

#### Test Individual Components

```python
# Test schema loading
zcli.loader.handle("@.zSchema.test", {"cache_as": "test"})
print(zcli.loader.cache.schema_cache.get("test"))

# Test data operation
result = zcli.data.handle({
    "action": "read",
    "table": "users",
    "model": "$test"
})
print(result)

# Test plugin
zcli.utils.load_plugins(["my_plugin"])
result = zcli.utils.plugin_manager.call_plugin_function(
    "my_plugin", "my_function", zcli, arg1, arg2
)
print(result)
```

#### Use Interactive Shell

```bash
# Start shell
zolo-zcli shell

# Test commands interactively
> load @.zSchema.test --as test
> data read users --model $test
> plugin load @.plugins.my_plugin
> plugin call my_plugin.my_function arg1 arg2
```

---

## Conclusion

zOS provides a powerful, declarative framework for building command-line applications. By separating concerns (UI, data, logic) and providing a rich set of subsystems, it enables rapid development of sophisticated tools.

### Key Takeaways

1. **Start Simple**: Begin with basic menus and data operations
2. **Use Patterns**: Follow established patterns for common use cases
3. **Extend Gradually**: Add plugins only when YAML isn't enough
4. **Test Thoroughly**: Write tests for plugins and workflows
5. **Document Everything**: Future you (and others) will thank you

### Next Steps

1. **Read the Guides**: Start with [zUI_GUIDE.md](zUI_GUIDE.md) and [zSchema_GUIDE.md](zSchema_GUIDE.md)
2. **Run the Demos**: Explore `zTestSuite/demos/` for working examples
3. **Build Something**: Start with a simple CRUD app
4. **Join the Community**: Share your creations and get help

### Resources

- **Documentation**: `Documentation/` folder
- **Test Suite**: `zTestSuite/` for examples
- **Source Code**: `zOS/subsystems/` for reference
- **AGENT.md**: LLM-optimized technical reference

---

**Version**: 1.5.0  
**Last Updated**: 2025-10-19  
**Maintained By**: Zolo AI

For questions, issues, or contributions, visit the [GitHub repository](https://github.com/ZoloAi/zolo-zcli).

