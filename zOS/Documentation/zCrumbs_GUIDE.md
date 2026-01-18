# zCrumbs: Breadcrumb Navigation System

**Version**: 2.0 (Enhanced Arrays with Phase 0.5)  
**Subsystem**: zNavigation  
**Status**: Production-Grade (30+ depth tested)

---

## Table of Contents

1. [Overview](#overview)
2. [Core Concepts](#core-concepts)
3. [Architecture: Enhanced Arrays](#architecture-enhanced-arrays)
4. [Operations](#operations)    
5. [Navigation Patterns](#navigation-patterns)
6. [Display Integration](#display-integration)
7. [Usage Examples](#usage-examples)
8. [Best Practices](#best-practices)
9. [API Reference](#api-reference)
10. [Testing & Validation](#testing--validation)

---

## Overview

**zCrumbs** is zOS's breadcrumb navigation system that tracks user navigation paths through hierarchical UI structures. It provides intelligent back-navigation, context preservation, and visual orientation across Terminal and Bifrost modes.

### Key Features

- **Self-Aware**: Reads session state directly for path determination
- **Multi-Trail**: Tracks multiple concurrent navigation contexts
- **Enhanced Arrays**: Metadata-enriched trails with `_context` and `_depth_map`
- **Smart Navigation**: POP semantics for parent/child relationships
- **Production-Tested**: Validated up to 30+ depth in complex scenarios
- **Dual-Mode**: Works seamlessly in Terminal and Bifrost (GUI)

### Why Breadcrumbs Matter

```
Without zCrumbs:                    With zCrumbs:
User: "Where am I?"                 zCrumbs: Dashboard > Settings > Network
User: "How did I get here?"         [Visual trail with back navigation]
User: "How do I go back?"           [Smart POP to parent context]
```

---

## Core Concepts

### Trails

A **trail** is an ordered list of navigation keys representing a user's path through a specific file and block:

```python
trail = ['Dashboard', 'Settings', 'Network', 'Wi-Fi']
```

### Scopes

A **scope** is a unique identifier for a trail, formatted as:

```
{path}.{filename}.{BlockName}
```

Example:
```
@.zUI.main.MainMenu
```

### Enhanced Structure (v2.0)

Since Phase 0.5, zCrumbs uses an enhanced format:

```python
session[SESSION_KEY_ZCRUMBS] = {
    'trails': {
        '@.zUI.FileA.zBlock_1': ['Header', 'Menu', 'Option1'],
        '@.zUI.FileB.zBlock_1': ['Dashboard', 'Settings']
    },
    '_context': {
        'last_operation': 'APPEND',
        'last_nav_type': 'sequential',
        'current_file': '@.zUI.FileA',
        'timestamp': 1234567890.12345
    },
    '_depth_map': {
        '@.zUI.FileA.zBlock_1': {
            'Menu': {'depth': 1, 'type': 'menu'},
            'Option1': {'depth': 2, 'type': 'menu_child'}
        }
    }
}
```

**Benefits**:
- Metadata hidden from user display
- Context tracking for debugging
- Depth-aware back navigation
- Hierarchical parent/child relationships

---

## Architecture: Enhanced Arrays

### Design Philosophy

Enhanced Arrays provide **80% of graph benefits with 10% of the complexity**:

| Feature | Flat Arrays | Enhanced Arrays | Full Graph |
|---------|-------------|-----------------|------------|
| Trail Storage | ✅ | ✅ | ✅ |
| Context Tracking | ❌ | ✅ | ✅ |
| Depth Hierarchy | ❌ | ✅ | ✅ |
| Smart POP | ❌ | ✅ | ✅ |
| Time Travel | ❌ | ❌ | ✅ |
| Analytics | ❌ | ❌ | ✅ |
| Memory Overhead | Low | Low | High |
| Complexity | Low | Low | High |

### Three Components

#### 1. Trails Dictionary

```python
'trails': {
    'file-block-key': ['step1', 'step2', 'step3']
}
```

**Purpose**: User-facing breadcrumb paths

#### 2. Context Metadata

```python
'_context': {
    'last_operation': 'APPEND',      # Last crumb operation
    'last_nav_type': 'sequential',   # Navigation type
    'current_file': '@.zUI.FileA',   # Active file
    'timestamp': 1234567890.12345    # Last update time
}
```

**Purpose**: Debugging, logging, operation tracking

#### 3. Depth Map

```python
'_depth_map': {
    'file-block-key': {
        'Menu': {'depth': 1, 'type': 'menu'},
        'SubMenu': {'depth': 2, 'type': 'menu_child'}
    }
}
```

**Purpose**: Parent/child relationships for smart POP

---

## Operations

### APPEND

Adds a new key to the end of a trail.

```python
# Before
trail = ['Dashboard', 'Settings']

# After APPEND('Network')
trail = ['Dashboard', 'Settings', 'Network']
```

**Use Cases**:
- Sequential navigation
- Child menu selection
- Forward movement

### POP

Removes the last key from a trail.

```python
# Before
trail = ['Dashboard', 'Settings', 'Network']

# After POP
trail = ['Dashboard', 'Settings']
```

**Use Cases**:
- zBack command
- "Done" in menus
- Parent menu return

**Smart POP**: Uses `_depth_map` to determine if POPing to a parent menu (removes all children) or a sibling (removes one level).

### RESET

Clears all trails and context, starting fresh.

```python
# Before
trails = {
    'FileA': ['Menu', 'Option1', 'SubOption'],
    'FileB': ['Dashboard', 'Settings']
}

# After RESET
trails = {}
_context = {}
_depth_map = {}
```

**Use Cases**:
- zNavBar navigation (always RESET)
- Session restart
- Context switch

### CREATE

Creates a new trail key for a different file or block.

```python
# Before
trails = {'FileA': ['Menu']}

# After CREATE('FileB')
trails = {
    'FileA': ['Menu'],
    'FileB': []  # New trail
}
```

**Use Cases**:
- zLink navigation (`@` prefix)
- Delta links (`$` prefix)
- Dashboard panel switches

### DELETE

Removes an entire trail key.

```python
# Before
trails = {
    'FileA': ['Menu'],
    'FileB': ['Dashboard']
}

# After DELETE('FileB')
trails = {'FileA': ['Menu']}
```

**Use Cases**:
- zBack from cross-file navigation
- Dashboard panel cleanup
- Session pruning

---

## Navigation Patterns

### Complete Navigation Flow

The following Mermaid diagram shows all navigation patterns and their breadcrumb operations:

```mermaid
flowchart TB
    %% =========================
    %% NODES + FLOW
    %% =========================
    Start(["zSpark"]) --> EntryPoint{"Entry Point"}
    UserStart(["User Action"]) --> EntryPoint
    
    %% ============ NEW: zNavBar RESET Path ============
    EntryPoint == "zNavBar Click" ==> NavBarCheck{"NavBar Source?"}
    NavBarCheck -- "Local Override<br/>(in zUI meta)" --> NavBarLocal["🔧 PRIORITY: Local navbar<br/>meta.zNavBar: [list]<br/>Overrides global .zEnv"]
    NavBarCheck -- "Global .zEnv<br/>(meta.zNavBar: true)" --> NavBarGlobal["🔧 Global navbar<br/>ZNAVBAR=FileA,FileB,FileC<br/>Inherits from .zEnv"]
    NavBarLocal --> NavBarReset["🔴 OP_RESET OPERATION"]
    NavBarGlobal --> NavBarReset
    
    NavBarReset --> NavBarClear["🗑️ CLEAR ALL TRAILS<br/>trails = {}<br/>_context = {}<br/>_depth_map = {}"]
    NavBarClear --> NavBarNew["🔑 CREATE destination file key<br/>APPEND destination block<br/>_context: last_operation='RESET'<br/>         last_nav_type='navbar'"]
    NavBarNew --> NavBarComplete["Fresh slate - No trail accumulation<br/>Self-aware breadcrumbs start new"]
    NavBarComplete --> FileType{"File Type?"}
    %% ============ END NEW: zNavBar RESET Path ============
    
    EntryPoint -- "Internal Nav<br/>(no navbar)" --> FileType

    EntryPoint -- "Direct Load" --> DirectLoad["PATH 0: Direct File Load<br/>No NavBar - Context Preserved"]
    DirectLoad --> CheckExisting{"Crumbs exist?"}
    CheckExisting -- YES --> PreserveContext["PRESERVE existing context<br/>Self-aware breadcrumbs read session"]
    CheckExisting -- NO --> CreateNew["CREATE new file key<br/>trails[file-block] = []"]
    PreserveContext --> AddToExisting["APPEND to existing file trail"]
    CreateNew --> AddToNew["START new file trail"]
    AddToExisting --> FileType
    AddToNew --> FileType

    FileType -- "Simple UI" --> Simple["PATH 1: Simple zUI - Single zBlock<br/>Sequential execution"]
    Simple --> SimpleCrumb["Self-aware crumb:<br/>session[zBlock] → file-block"]
    SimpleCrumb --> SimpleKeys["APPEND each key sequentially"]
    SimpleKeys --> SimpleEnd(["Block complete"])

    FileType -- "Multi-Block" --> Multi["PATH 2: Multi-Block zUI<br/>🔄 Sequential block execution"]
    Multi --> MultiCrumb["Start: file-root-block"]
    MultiCrumb --> MultiKeys["APPEND keys from block"]
    MultiKeys --> MultiLoop{"More Blocks?"}
    MultiLoop -- YES --> MultiSwitch["🔄 UPDATE session[zBlock]<br/>CREATE new block trail"]
    MultiSwitch --> MultiAppend["APPEND block keys"]
    MultiAppend --> MultiLoop
    MultiLoop -- NO --> MultiEnd(["All blocks executed<br/>unless interrupted"])

    %% =========================
    %% PATH 3 (Menu)
    %% =========================
    FileType -- "Has Menu" --> Menu["PATH 3: zMenu Navigation<br/>POP semantics + depth tracking"]
    Menu --> MenuCrumb["Start: file-root<br/>Self-aware: reads session state"]
    MenuCrumb --> ShowMenu["Display Menu - APPEND menu name<br/>_depth_map tracks semantic depth"]
    ShowMenu --> MenuState["file-root-menu<br/>_context: last_nav_type=menu"]
    MenuState --> MenuChoice{"User Choice?"}
    MenuChoice == "Select Option" ==> AppendChoice["APPEND selection<br/>Child menu = APPEND"]
    AppendChoice --> MenuChoice2["file-root-menu-selection"]
    MenuChoice2 --> MenuBack{"User Action?"}
    MenuBack == zBack ==> PopChoice["POP last item<br/>Parent menu = POP children"]
    PopChoice --> MenuState
    MenuBack == done ==> PopMenu["POP to root"]
    PopMenu --> MenuCrumb
    MenuChoice -- "zBack/done" --> MenuExit(["Exit to parent"])

    %% PATH 3 DELTA LINK BRANCH
    MenuChoice2 == "Delta Link $" ==> MenuDelta["Navigate to different block<br/>SAME file - self-aware resolution<br/>session[zVaFile] unchanged"]
    MenuDelta ==> MenuDeltaCreate["CREATE new block trail key<br/>PRESERVE menu context"]
    MenuDeltaCreate ==> MenuDeltaState["Two trails active:<br/>file-menu AND file-block2"]
    MenuDeltaState ==> MenuDeltaBoth["Both contexts tracked in _context"]
    MenuDeltaBoth ==> MenuDeltaReturn{"Return?"}
    MenuDeltaReturn -- "zBack to menu" --> MenuChoice2
    MenuDeltaReturn -- "Continue block2" --> MenuDeltaState

    %% PATH 3 ZLINK BRANCH
    MenuChoice2 == "zLink @" ==> MenuZLink["Navigate to different file<br/>Walker required - passed via zcli.walker"]
    MenuZLink ==> MenuZLinkCreate["CREATE new file key<br/>PRESERVE menu context in original"]
    MenuZLinkCreate ==> MenuZLinkState["Two file trails active:<br/>fileA-menu AND fileB-block"]
    MenuZLinkState ==> MenuZLinkBoth["_context tracks both files<br/>current_file updated"]
    MenuZLinkBoth ==> MenuZLinkReturn{"Return?"}
    MenuZLinkReturn -- zBack --> MenuZLinkPop["DELETE fileB key"]
    MenuZLinkPop --> MenuChoice2
    MenuZLinkReturn -- "Continue fileB" --> MenuZLinkState

    %% =========================
    %% PATH 4 (Dashboard - APPROACH 2: Separate Panel Keys)
    %% =========================
    FileType -- Dashboard --> Dash["PATH 4: zDashboard<br/>Approach 2: Separate Panel Keys"]
    Dash --> DashCrumb["APPEND Dashboard key<br/>Self-aware from session state"]
    DashCrumb --> DashRoot["file-Dashboard<br/>_context: nav_type=dashboard"]
    DashRoot --> DashChoice{"Select Panel?"}

    DashChoice -- "Panel A" --> DashCreateA["🔑 CREATE panel key: file-Dashboard.PanelA<br/>🗑️ CLEAR other panel keys<br/>🔄 UPDATE session: zVaFile=PanelA"]
    DashCreateA --> DashStateA["Active trails:<br/>1. file-Dashboard: [Dashboard]<br/>2. file-Dashboard.PanelA: []"]
    DashStateA --> DashContentA["APPEND internal panel keys<br/>_depth_map tracks panel depth"]
    DashContentA --> DashTrailA["PanelA: [Panel_Header, Panel_Content]"]
    DashTrailA --> DashChoice2{"Next Action?"}

    DashChoice2 -- "Switch to Panel B" --> DashCreateB["🗑️ DELETE PanelA key<br/>🔑 CREATE PanelB key<br/>🔄 UPDATE session: zVaFile=PanelB"]
    DashCreateB --> DashStateB["Active trails:<br/>1. file-Dashboard: [Dashboard]<br/>2. file-Dashboard.PanelB: []"]
    DashStateB --> DashChoice2

    DashChoice2 -- done --> DashRestore["🔄 RESTORE session: zVaFile=Dashboard<br/>🗑️ CLEAR all panel keys"]
    DashRestore --> DashExit(["Exit Dashboard"])
    DashChoice -- done --> DashRestore

    %% =========================
    %% PATH 5 (Dashboard + Menu + Delta + zLink + Internal Dash)
    %% CRITICAL: Session context switching + Walker propagation
    %% =========================
    FileType -- "Dash + Menu" --> Nested["PATH 5: Dashboard with Nested Navigation<br/>CRITICAL: Context + Walker Propagation"]
    Nested --> NestedCrumb["APPEND Dashboard key<br/>Self-aware from session"]
    NestedCrumb --> NestedDashRoot["file-Dashboard<br/>session: zVaFile=dash, zVaFolder=@"]
    NestedDashRoot --> NestedPanelChoice{"Select Panel?"}

    %% Panel Selection (Approach 2) - SESSION CONTEXT SWITCH!
    NestedPanelChoice -- "Panel (e.g. zMGMT)" --> NestedCreatePanel["🔑 CREATE panel key: file-Dashboard.Panel1<br/>🗑️ CLEAR other panel keys<br/>🔄 UPDATE session context:<br/>  zVaFile=Panel1<br/>  zVaFolder=@ (preserved)<br/>📍 Walker context available via zcli.walker"]
    NestedCreatePanel --> NestedContextNote["⚠️ CRITICAL ARCHITECTURE:<br/>• Session points to panel file<br/>• Delta links resolve relative to panel<br/>• zLinks need walker from zcli.walker<br/>• Self-aware breadcrumbs read session"]
    NestedContextNote --> NestedPanelState["Active trails:<br/>1. file-Dashboard: [Dashboard]<br/>2. file-Dashboard.Panel1: []<br/>session: zVaFile=Panel1"]
    NestedPanelState --> NestedPanelInternal["APPEND internal panel keys<br/>Sequential execution within panel"]
    NestedPanelInternal --> NestedHasContent{"Panel Type?"}

    %% SIMPLE PANEL (No Menu)
    NestedHasContent -- "Simple Content" --> NestedSimple["Sequential keys: Panel_Header, Panel_Content<br/>APPEND each to panel trail"]
    NestedSimple --> NestedSimpleTrail["Panel1: [Panel_Header, Panel_Content]<br/>_depth_map tracks depth"]
    NestedSimpleTrail --> NestedSimpleAction{"Action?"}
    NestedSimpleAction -- "Switch Panel" --> NestedPanelChoice
    NestedSimpleAction -- done --> NestedRestoreSimple["🔄 RESTORE session: zVaFile=Dashboard<br/>🗑️ CLEAR panel keys"]
    NestedRestoreSimple --> NestedExitSimple(["Exit Dashboard"])

    %% MENU PANEL (Has Menu) - WALKER CONTEXT CRITICAL!
    NestedHasContent -- "Has Menu" --> NestedMenu["🔧 APPEND menu name to panel trail<br/>📍 Walker passed: dispatch.handle(walker=zcli.walker)<br/>POP semantics active"]
    NestedMenu --> NestedMenuState["Panel1: [Panel_Header, Admin_Actions*]<br/>_depth_map: Admin_Actions depth=1"]
    NestedMenuState --> NestedMenuChoice{"Menu Selection?<br/>Walker available for delta/zLinks"}

    %% Regular Menu Option
    NestedMenuChoice -- "Regular Option" --> NestedAppendOption["APPEND selection<br/>Child menu = APPEND<br/>Parent menu = POP children"]
    NestedAppendOption --> NestedOptionState["Panel1: [header, menu, View_All_Users]<br/>_depth_map depth incremented"]
    NestedOptionState --> NestedOptionAction{"Action?"}
    NestedOptionAction -- zBack --> NestedPopOption["POP selection<br/>Smart POP via _depth_map"]
    NestedPopOption --> NestedMenuState
    NestedOptionAction -- done --> NestedPopToPanel["POP to panel root"]
    NestedPopToPanel --> NestedPanelState

    %% DELTA LINK from Panel Menu - BUG #3 FIX!
    NestedMenuChoice == "Delta Link $" ==> NestedDelta["🔧 FIX: Walker propagated<br/>Navigate to different block<br/>Uses session[zVaFile]=Panel1<br/>Self-aware: $zBlock_2 → @.Panel1.zBlock_2"]
    NestedDelta ==> NestedDeltaCreate["🔑 CREATE new block trail key<br/>PRESERVE panel+menu contexts<br/>_context: nav_type=delta"]
    NestedDeltaCreate ==> NestedDeltaMulti["Multiple trails active:"]
    NestedDeltaMulti ==> NestedDeltaTrail1["Panel1.zBlock_1: [header, menu]"]
    NestedDeltaMulti ==> NestedDeltaTrail2["Panel1.zBlock_2: [Details]<br/>_depth_map tracks separately"]
    NestedDeltaTrail2 ==> NestedDeltaAction{"Action?"}
    NestedDeltaAction -- zBack --> NestedDeltaPop["🗑️ DELETE Panel1.zBlock_2 key"]
    NestedDeltaPop --> NestedMenuState
    NestedDeltaAction -- Continue --> NestedDeltaTrail2

    %% ZLINK from Panel Menu - BUG #3 FIX!
    NestedMenuChoice == "zLink @" ==> NestedZLink["🔧 FIX: Walker + Session Update<br/>Navigate to DIFFERENT file<br/>Walker: zcli.walker required<br/>Session: zVaFile updated to target"]
    NestedZLink ==> NestedZLinkUpdate["🔄 UPDATE session:<br/>  zVaFile=FileB (target file)<br/>  zVaFolder updated if needed<br/>Walker context maintained"]
    NestedZLinkUpdate ==> NestedZLinkCreate["🔑 CREATE new file trail key<br/>PRESERVE panel+menu contexts<br/>_context: nav_type=zlink"]
    NestedZLinkCreate ==> NestedZLinkMulti["Multiple file trails active:"]
    NestedZLinkMulti ==> NestedZLinkTrail1["Panel1: [header, menu]"]
    NestedZLinkMulti ==> NestedZLinkTrail2["FileB-Editor: [Form, Validation]<br/>_depth_map independent"]
    NestedZLinkTrail2 ==> NestedZLinkAction{"Action?"}
    NestedZLinkAction -- zBack --> NestedZLinkRestore["🗑️ DELETE FileB key<br/>🔄 RESTORE session: zVaFile=Panel1"]
    NestedZLinkRestore --> NestedMenuState
    NestedZLinkAction -- Continue --> NestedZLinkTrail2

    %% INTERNAL DASHBOARD (Dashboard within Panel) - Recursive Context
    NestedHasContent == "Internal Dashboard" ==> NestedInternalDash["Panel contains nested Dashboard<br/>Recursive session context<br/>Self-aware at each level"]
    NestedInternalDash ==> NestedInternalCreate["🔑 CREATE nested dashboard key<br/>session: zVaFile=InternalDash"]
    NestedInternalCreate ==> NestedInternalMulti["Multiple dashboard contexts:"]
    NestedInternalMulti ==> NestedInternalOuter["file-Dashboard: [root]"]
    NestedInternalMulti ==> NestedInternalInner["file-Dashboard.Settings.SubDash.SubPanelA: []<br/>_depth_map hierarchical"]
    NestedInternalInner ==> NestedInternalAction{"Action?"}
    NestedInternalAction -- "Exit Sub-Dashboard" --> NestedInternalExit["🗑️ POP nested dashboard<br/>🔄 RESTORE parent session"]
    NestedInternalExit --> NestedPanelState
    NestedInternalAction -- "Navigate Sub-Panels" --> NestedInternalSwitch["Same Approach 2 logic<br/>Delete old sub-panel, create new"]
    NestedInternalSwitch --> NestedInternalInner

    %% Exit from Menu Level
    NestedMenuChoice -- done --> NestedMenuExit["POP to panel"]
    NestedMenuExit --> NestedPanelState

    %% Exit from Panel Level - RESTORE SESSION!
    NestedPanelChoice -- done --> NestedRestoreDash["🔄 RESTORE session: zVaFile=dash<br/>🗑️ CLEAR all panel keys"]
    NestedRestoreDash --> NestedExitDash(["Exit Dashboard"])

    %% =========================
    %% LEGEND & KEY INSIGHTS
    %% =========================
    Legend["🔑 KEY ARCHITECTURAL DECISIONS:<br/>1. Self-Aware Breadcrumbs: Read session state directly<br/>2. Sequential Block Execution: Blocks run automatically<br/>3. Enhanced Arrays: trails + _context + _depth_map<br/>4. Dashboard Approach 2: Separate panel keys (memory efficient)<br/>5. Walker Propagation: zcli.walker for nested contexts<br/>6. Session Context Updates: Critical for delta/zLinks<br/>7. POP Semantics: Child APPEND, Parent POP<br/>8. Depth Tracking: _depth_map for hierarchical navigation<br/>9. OP_RESET (NEW): NavBar clears ALL trails/context<br/>10. NavBar Priority: Local override > Global .zEnv<br/><br/>✅ PROVEN: 30+ depth (Ultra Monster Final)<br/>✅ TESTED: OP_RESET (Phase 0 Complete)<br/>🎯 READY: Production-grade navigation"]

    %% =========================
    %% STYLING
    %% =========================
    classDef entryNode stroke-width:4px, stroke:#2f9e44, fill:#C8E6C9, color:#000
    classDef entryPointNode stroke-width:4px, stroke:#2f9e44, fill:#FFF9C4, color:#000
    classDef hubNode stroke-width:3px, stroke:#666, fill:#F5F5F5, color:#000
    classDef decisionNode stroke-width:2px, stroke:#555, fill:#FFFFFF, color:#000
    classDef stateNode stroke-width:2px, stroke:#607D8B, fill:#ECEFF1, color:#000
    classDef endNode stroke-width:2px, stroke:#2f9e44, fill:#E8F5E9, color:#000
    classDef exitNode stroke-width:2px, stroke:#8D6E63, fill:#EFEBE9, color:#000

    classDef path3Active stroke-width:4px, stroke:#EF6C00, fill:#FFE0B2, color:#000, font-weight:bold
    classDef stateNodeActive stroke-width:3px, stroke:#EF6C00, fill:#FFF3E0, color:#000, font-weight:bold
    classDef decisionNodeActive stroke-width:3px, stroke:#EF6C00, fill:#FFECB3, color:#000, font-weight:bold

    classDef appendAction fill:#51cf66,stroke:#2f9e44,color:#fff
    classDef popAction fill:#748ffc,stroke:#5c7cfa,color:#fff
    classDef replaceAction fill:#ffd43b,stroke:#fab005,color:#000
    classDef createAction fill:#40c057,stroke:#2b8a3e,color:#fff
    classDef deleteAction fill:#ff8787,stroke:#fa5252,color:#fff
    classDef resetAction fill:#ff6b6b,stroke:#c92a2a,color:#fff,font-weight:bold
    classDef restoreAction fill:#4dabf7,stroke:#1971c2,color:#fff
    classDef updateAction fill:#ffd43b,stroke:#f59f00,color:#000
    classDef specialPath fill:#FFEBEE,stroke:#FA5252,color:#000
    classDef bugFixNode fill:#FFE082,stroke:#F57F17,stroke-width:3px,color:#000,font-weight:bold
    classDef contextNode fill:#B2DFDB,stroke:#00796B,stroke-width:3px,color:#000,font-style:italic,font-weight:bold
    classDef legendNode fill:#E3F2FD,stroke:#1565C0,stroke-width:3px,color:#000,font-weight:bold
    
    classDef path5Node fill:#FFF3E0,stroke:#F57C00,stroke-width:3px,color:#000,font-weight:bold
    classDef path5State fill:#FFECB3,stroke:#FB8C00,stroke-width:2px,color:#000
    classDef path5Multi fill:#FFF9C4,stroke:#FBC02D,stroke-width:2px,color:#000,font-style:italic
    classDef internalDash fill:#E1F5FE,stroke:#0288D1,stroke-width:3px,color:#000,font-weight:bold
    classDef navbarNode fill:#FFCDD2,stroke:#C62828,stroke-width:4px,color:#000,font-weight:bold

    Start:::entryNode
    UserStart:::entryNode
    EntryPoint:::entryPointNode
    NavBarCheck:::navbarNode
    NavBarLocal:::navbarNode
    NavBarGlobal:::navbarNode
    NavBarReset:::resetAction
    NavBarClear:::deleteAction
    NavBarNew:::createAction
    NavBarComplete:::navbarNode
    PreserveContext:::stateNode
    CreateNew:::createAction

    MultiSwitch:::updateAction

    Menu:::path3Active
    MenuCrumb:::stateNodeActive
    ShowMenu:::path3Active
    MenuState:::stateNodeActive
    MenuChoice:::decisionNodeActive
    MenuChoice2:::stateNodeActive
    MenuBack:::decisionNodeActive

    AppendChoice:::appendAction
    PopChoice:::popAction
    PopMenu:::popAction

    MenuDelta:::specialPath
    MenuDeltaCreate:::createAction
    MenuDeltaState:::specialPath
    MenuDeltaBoth:::specialPath
    MenuDeltaReturn:::decisionNodeActive
    MenuZLinkPop:::deleteAction

    MenuZLink:::specialPath
    MenuZLinkCreate:::createAction
    MenuZLinkState:::specialPath
    MenuZLinkBoth:::specialPath
    MenuZLinkReturn:::decisionNodeActive

    DashCreateA:::createAction
    DashCreateB:::createAction
    DashRestore:::restoreAction
    DashExit:::exitNode

    Nested:::path5Node
    NestedContextNote:::contextNode
    NestedCreatePanel:::createAction
    NestedRestoreSimple:::restoreAction
    NestedRestoreDash:::restoreAction
    NestedDelta:::bugFixNode
    NestedDeltaCreate:::createAction
    NestedDeltaMulti:::path5Multi
    NestedDeltaPop:::deleteAction
    NestedZLink:::bugFixNode
    NestedZLinkUpdate:::updateAction
    NestedZLinkCreate:::createAction
    NestedZLinkMulti:::path5Multi
    NestedZLinkRestore:::restoreAction
    NestedInternalDash:::internalDash
    NestedInternalCreate:::createAction
    NestedInternalMulti:::path5Multi
    NestedInternalSwitch:::updateAction
    NestedInternalExit:::restoreAction
    NestedPopOption:::popAction
    NestedPopToPanel:::popAction
    NestedMenuExit:::popAction
    NestedExitSimple:::exitNode
    NestedExitDash:::exitNode

    Legend:::legendNode
```

### Path Summaries

| Path | Description | Operation | Use Case |
|------|-------------|-----------|----------|
| **PATH 0** | Direct File Load | PRESERVE or CREATE | Programmatic navigation, deep linking |
| **PATH 1** | Simple zUI | APPEND | Single block, sequential keys |
| **PATH 2** | Multi-Block | APPEND + CREATE | Multiple blocks, sequential execution |
| **PATH 3** | zMenu | APPEND + POP | Interactive menus, hierarchical |
| **PATH 3a** | Delta Links ($) | CREATE + PRESERVE | Same-file block navigation |
| **PATH 3b** | zLinks (@) | CREATE + DELETE | Cross-file navigation |
| **PATH 4** | zDashboard | CREATE + DELETE | Panel switching, memory efficient |
| **PATH 5** | Nested Complex | ALL OPERATIONS | Dashboard + Menu + Links + Internal |
| **zNavBar** | Navigation Bar | RESET | Top-level nav, full context reset |

---

## Display Integration

### Terminal Mode

Breadcrumbs display automatically before menus:

```
zCrumbs:
  @.zUI.main.MainMenu[Dashboard > Settings > Network]

  [0] Wi-Fi
  [1] Ethernet
  [2] VPN
```

### Bifrost Mode

Breadcrumbs render as a visual trail with clickable segments:

```json
{
  "event": "zCrumbs",
  "trails": {
    "@.zUI.main.MainMenu": ["Dashboard", "Settings", "Network"]
  }
}
```

### Display Architecture

```python
# zDisplay calls zCrumbs
zcli.display.zCrumbs(zcli.session)

# zDisplay.zCrumbs() uses centralized banner method
crumbs_display = zcli.navigation.breadcrumbs.zCrumbs_banner()

# Returns ONLY trails (no _context or _depth_map)
{
    '@.zUI.FileA.zBlock_1': 'Header > Menu > Option1'
}
```

**Key Design**: Metadata (`_context`, `_depth_map`) is **hidden from user display** via the `zCrumbs_banner()` method, ensuring clean UX.

---

## Usage Examples

### Example 1: Simple Sequential Navigation

```yaml
# zUI.simple.yaml
zBlock_1:
  Header:
    - zDisplay:
        event: header
        label: "Welcome"
  
  Menu*: ["Option1", "Option2"]
  
  Option1:
    - zDisplay:
        event: text
        content: "You selected Option 1"
```

**Breadcrumb Trail**:
```
@.zUI.simple.zBlock_1[Header > Menu > Option1]
```

### Example 2: Delta Link Navigation

```yaml
# zUI.delta.yaml
zBlock_1:
  Root_Menu*: ["Action1", "Jump_Block2"]
  
  Action1:
    - zDisplay:
        event: text
        content: "Action 1"
  
  Jump_Block2:
    - zLink: "$zBlock_2"

zBlock_2:
  Block2_Content:
    - zDisplay:
        event: text
        content: "Block 2"
```

**Breadcrumb Trails** (two active):
```
@.zUI.delta.zBlock_1[Root_Menu > Jump_Block2]
@.zUI.delta.zBlock_2[Block2_Content]
```

### Example 3: zNavBar with Global Config

```bash
# .zEnv
ZNAVBAR=Dashboard,Settings,Profile
```

```yaml
# zUI.dashboard.yaml
meta:
  zNavBar: true  # Inherit from .zEnv
```

**Behavior**: Clicking navbar **RESETS** all breadcrumbs, starting fresh.

### Example 4: Dashboard Panel Switching

```yaml
# zUI.dash.yaml
zBlock_1:
  Dashboard:
    - zDash:
        folder: "@.UI.panels"
        sidebar: ["Overview", "Settings", "Help"]
        default: "Overview"
```

**Breadcrumb Trails**:
```
# Initially
@.zUI.dash.zBlock_1[Dashboard]

# After selecting "Settings"
@.zUI.dash.zBlock_1[Dashboard]
@.zUI.dash.zBlock_1.Settings[Panel_Header, Panel_Content]

# After switching to "Help" (Settings trail deleted)
@.zUI.dash.zBlock_1[Dashboard]
@.zUI.dash.zBlock_1.Help[Help_Header, FAQ]
```

---

## Best Practices

### 1. Use Self-Aware Breadcrumbs

**Don't** compute paths manually:

```python
# ❌ BAD
zBlock = f"{zVaFolder}.{zVaFile}.{block_name}"
zcli.navigation.breadcrumbs.handle_zCrumbs(zBlock, zKey, walker)
```

**Do** let breadcrumbs read session:

```python
# ✅ GOOD
zcli.navigation.breadcrumbs.handle_zCrumbs(zKey, walker=walker)
# Breadcrumbs auto-read session state for zBlock path
```

### 2. Always Use Walker Context

For delta links and zLinks to work in nested contexts:

```python
# ✅ CORRECT
dispatch.handle(key, value, walker=zcli.walker)
```

### 3. Display Clean Trails

Always use `zCrumbs_banner()` for display:

```python
# ✅ CORRECT (filters metadata)
crumbs_display = zcli.navigation.breadcrumbs.zCrumbs_banner()

# ❌ WRONG (exposes _context, _depth_map)
crumbs_raw = zcli.session[SESSION_KEY_ZCRUMBS]
```

### 4. NavBar Always Resets

If you implement custom navbar logic:

```python
# NavBar clicks MUST reset
zcli.navigation.breadcrumbs.handle_zCrumbs(
    destination_key,
    walker=walker,
    operation="RESET"
)
```

### 5. Test Deep Navigation

Test your UI with 10+ depth navigation to ensure:
- No memory leaks
- Correct back navigation
- Context preservation

---

## API Reference

### Core Methods

#### `handle_zCrumbs(zKey, walker=None, operation="APPEND")`

Add or modify breadcrumb trail.

**Parameters**:
- `zKey` (str): Navigation key to add/process
- `walker` (Walker, optional): Walker instance for context
- `operation` (str): Operation type (`APPEND`, `POP`, `RESET`)

**Returns**: None

**Example**:
```python
zcli.navigation.breadcrumbs.handle_zCrumbs("Settings", walker=walker)
```

#### `handle_zBack(show_banner=True, walker=None)`

Navigate backward through breadcrumb trail.

**Parameters**:
- `show_banner` (bool): Show breadcrumb banner after pop
- `walker` (Walker, optional): Walker instance for file reload

**Returns**: Tuple[Dict, List, Optional[str]]
- block_dict: Loaded block dictionary
- block_keys: List of keys in block
- start_key: Current position in trail

**Example**:
```python
block_dict, keys, start_key = zcli.navigation.breadcrumbs.handle_zBack(walker=walker)
```

#### `zCrumbs_banner()`

Format breadcrumbs for display (filters metadata).

**Returns**: Dict[str, str]
- Mapping of scope to formatted trail string

**Example**:
```python
display_trails = zcli.navigation.breadcrumbs.zCrumbs_banner()
# {'@.zUI.main.Menu': 'Dashboard > Settings'}
```

### Session Structure

```python
SESSION_KEY_ZCRUMBS = "zCrumbs"

# Enhanced Format (v2.0)
session[SESSION_KEY_ZCRUMBS] = {
    'trails': {
        'scope-key': ['step1', 'step2']
    },
    '_context': {
        'last_operation': str,
        'last_nav_type': str,
        'current_file': str,
        'timestamp': float
    },
    '_depth_map': {
        'scope-key': {
            'step-key': {
                'depth': int,
                'type': str
            }
        }
    }
}
```

---

## Testing & Validation

### Unit Tests

Located in: `local_planning/zCrumb_investigation/testing/`

**Test Files**:
- `simple_ui.py` - PATH 1: Simple sequential navigation
- `multi_block.py` - PATH 2: Multi-block execution
- `menu_simple.py` - PATH 3: Menu navigation with POP
- `menu_delta.py` - PATH 3a: Delta link navigation
- `menu_zlink.py` - PATH 3b: zLink cross-file navigation
- `dash_test.py` - PATH 4: Dashboard panel switching
- `path5_*.py` - PATH 5: Complex nested scenarios
- `ultra_monster_final.py` - 30+ depth stress test

### Stress Tests

**Monster Test** (20+ depth):
```bash
cd local_planning/zCrumb_investigation/testing/path5/6_monster
python3 v3_monster.py
```

**Ultra Monster Test** (30+ depth):
```bash
cd local_planning/zCrumb_investigation/testing/path5/ultra_monster_final
python3 ultra_monster_final.py
```

### Phase 0: OP_RESET Testing

```bash
cd local_planning/zCrumb_investigation/testing/phase0_reset
python3 test_navbar_reset.py
```

**Validates**:
- Global navbar from `.zEnv`
- Local navbar overrides
- Complete trail cleanup on RESET
- Context metadata tracking

---

## Key Architectural Decisions

### 1. Self-Aware Breadcrumbs

**Decision**: Breadcrumbs read `session[zBlock]` directly instead of receiving computed paths.

**Rationale**:
- Single source of truth
- Eliminates path computation bugs
- Automatic context detection

### 2. Sequential Block Execution

**Decision**: Blocks execute automatically unless interrupted by menus/dialogs/navigation.

**Rationale**:
- Natural flow-based UX
- Reduced explicit navigation code
- Consistent with terminal-first philosophy

### 3. Enhanced Arrays (Not Full Graph)

**Decision**: Use metadata-enriched arrays instead of full graph database.

**Rationale**:
- 80% of benefits, 10% of complexity
- Low memory overhead
- Production-tested to 30+ depth

### 4. Dashboard Separate Panel Keys

**Decision**: Each panel gets its own trail key, old panels are deleted on switch.

**Rationale**:
- Memory efficient (no accumulation)
- Clear hierarchical structure
- Supports internal panel navigation

### 5. Walker Propagation

**Decision**: Pass `walker` instance explicitly through nested contexts.

**Rationale**:
- Delta/zLinks need walker for resolution
- Session context must be maintained
- Enables nested dashboard + menu + links

### 6. POP Semantics

**Decision**: Child menus APPEND, parent menus POP children.

**Rationale**:
- Intuitive hierarchical navigation
- Depth-aware via `_depth_map`
- Smart back navigation

### 7. NavBar Priority Chain

**Decision**: Local override > Global .zEnv > Route fallback.

**Rationale**:
- Flexibility per-file
- Global defaults
- Semantic consistency

### 8. OP_RESET for NavBar

**Decision**: All navbar clicks perform full RESET.

**Rationale**:
- Clear mental model
- No trail accumulation
- Fresh start semantics

### 9. Metadata Hidden from Display

**Decision**: `_context` and `_depth_map` never shown to users.

**Rationale**:
- Clean UX
- Internal debugging only
- Centralized banner method

### 10. Session Context Updates

**Decision**: Update `zVaFile`/`zVaFolder` when navigating to panels/links.

**Rationale**:
- Delta links resolve correctly
- Self-aware breadcrumbs work
- Maintains consistency

---

## Production Status

### Proven Capabilities

✅ **30+ Depth**: Validated with Ultra Monster Test  
✅ **5 Navigation Patterns**: All paths tested and verified  
✅ **Nested Contexts**: Dashboard + Menu + Delta + zLinks working  
✅ **Dual-Mode**: Terminal and Bifrost display correctly  
✅ **RESET Operation**: NavBar cleanup tested (Phase 0)  
✅ **Memory Efficient**: No leaks, proper cleanup  
✅ **Bug-Free**: BUG #3 (walker propagation) and BUG #4 (panel zLinks) fixed  

### Performance

- **Memory**: O(d) where d = depth (linear, not exponential)
- **Lookup**: O(1) for trail access (dictionary key)
- **Display**: O(n) where n = number of trails (typically 1-3)
- **Max Depth Tested**: 30+ entries in single trail
- **Max Trails Tested**: 6 concurrent trails

### Known Limitations

1. **No Time Travel**: Cannot jump to arbitrary past state (use zHistory for this)
2. **No Analytics**: No built-in navigation pattern tracking (future: graph opt-in)
3. **Terminal-First**: Bifrost rendering is basic (future: rich interactive crumbs)

---

## Migration Guide

### From Flat Arrays (v1.0) to Enhanced Arrays (v2.0)

**Automatic Migration**: zCrumbs auto-migrates on first access.

**Old Format**:
```python
{
    '@.zUI.FileA.zBlock_1': ['Header', 'Menu']
}
```

**New Format**:
```python
{
    'trails': {
        '@.zUI.FileA.zBlock_1': ['Header', 'Menu']
    },
    '_context': {},
    '_depth_map': {}
}
```

**No Code Changes Required**: All existing code works unchanged.

---

## Troubleshooting

### Issue: Breadcrumbs Not Displaying

**Symptom**: Menu appears without breadcrumb trail above it.

**Cause**: `display.zCrumbs()` missing or failing.

**Fix**:
```python
# Ensure breadcrumbs display before menu
display.zCrumbs(zcli.session)
display.zMenu(menu_pairs)
```

### Issue: `AttributeError: 'zSystem' object has no attribute 'zcli'`

**Symptom**: Error when displaying breadcrumbs.

**Cause**: Incorrect access pattern in `display_event_system.py`.

**Fix**:
```python
# ❌ WRONG
if hasattr(self.zcli, 'navigation'):

# ✅ CORRECT
if hasattr(self.display, 'zcli') and hasattr(self.display.zcli, 'navigation'):
```

### Issue: Metadata Shown in Display

**Symptom**: User sees `_context[...]` or `_depth_map[...]` in terminal.

**Cause**: Raw session access instead of `zCrumbs_banner()`.

**Fix**:
```python
# ❌ WRONG
crumbs = session[SESSION_KEY_ZCRUMBS]

# ✅ CORRECT
crumbs = zcli.navigation.breadcrumbs.zCrumbs_banner()
```

### Issue: Delta Links Fail in Nested Context

**Symptom**: `KeyError` or "Block not found" when using delta links from dashboard panels.

**Cause**: Walker not propagated through nested contexts.

**Fix**:
```python
# Ensure walker is passed in nested contexts
dispatch.handle(key, value, walker=zcli.walker)
```

---

## Related Documentation

- **zNavigation_GUIDE.md**: Overall navigation system architecture
- **zWalker_GUIDE.md**: Orchestration and UI flow engine
- **zDisplay_GUIDE.md**: Display system and zCrumbs rendering
- **zConfig_GUIDE.md**: Session keys and configuration
- **zServer_GUIDE.md**: Bifrost integration and WebSocket events

---

## Credits

**Original Design**: Gal Nachshon (zOS Creator)  
**Phase 0.5 (Enhanced Arrays)**: December 2022  
**Phase 0 (OP_RESET)**: December 2022  
**Testing**: Monster Test (20+ depth), Ultra Monster Test (30+ depth)  
**Status**: Production-Grade ✅

---

**Last Updated**: December 22, 2025  
**Version**: 2.0 (Enhanced Arrays + OP_RESET)  
**Tested**: 30+ depth, 6 concurrent trails, all navigation patterns

