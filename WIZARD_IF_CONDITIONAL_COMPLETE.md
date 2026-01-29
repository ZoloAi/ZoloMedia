# zWizard Conditional Rendering (`if` Parameter) - Implementation Complete

**Date**: 2026-01-28  
**Status**: ✅ Complete  
**Scope**: Conditional rendering with `if` parameter in zWizard shorthand syntax

---

## Overview

Implemented full support for conditional rendering in zWizard using the `if` parameter. This enables dynamic UI where form elements appear/disappear based on user selections (e.g., showing different input fields based on a radio button selection).

**Example Usage**:
```yaml
zWizard:
    select_section:
        zSelect:
            options: [low, medium, high]
            type: radio
        zInput:
            if: "zHat[0] == 'low'"
            prompt: low input
        zInput:
            if: "zHat[0] == 'medium'"
            prompt: medium input
        zInput:
            if: "zHat[0] == 'high'"
            prompt: high input
```

---

## Implementation Details

### Terminal Mode (Sequential Execution)

In Terminal mode, the wizard executes steps sequentially, evaluating `if` conditions in real-time as zHat gets populated.

**Changes Made:**

1. **Organizational Handler** (`zOS/core/L2_Core/e_zDispatch/dispatch_modules/organizational_handler.py`):
   - Removed premature `if` condition evaluation during preprocessing
   - Added detection for "wizard input containers" (containers with only input events)
   - Routes wizard input containers as **implicit wizards** for sequential execution
   - Key change: Routes to `_handle_implicit_wizard()` instead of recursing

2. **Wizard Interpolation** (`zOS/core/L3_Abstraction/m_zWizard/zWizard_modules/wizard_interpolation.py`):
   - Updated `interpolate_zhat()` to **skip interpolating `if` parameters**
   - The `if` key is preserved as a raw Python expression for evaluation
   - Prevents `zHat[0]` from being replaced with "None" before condition evaluation

3. **Wizard** (`zOS/core/L3_Abstraction/m_zWizard/zWizard.py`):
   - Already had logic to evaluate `if` conditions inside `zDisplay` wrappers (lines 1314-1324)
   - Now receives conditions intact thanks to changes #1 and #2
   - Evaluates conditions during sequential execution with current zHat state

**Terminal Mode Flow**:
```
1. User selects "medium" from radio buttons
2. zHat[0] = "medium"
3. Wizard evaluates each step:
   - zInput (if: zHat[0] == 'low') → FALSE → Skip
   - zInput (if: zHat[0] == 'medium') → TRUE → Show "medium input"
   - zInput (if: zHat[0] == 'high') → FALSE → Skip
```

### Bifrost Mode (Client-Side Rendering)

In Bifrost mode, the entire UI structure is sent upfront as a chunk. Conditional rendering must happen **client-side** with JavaScript.

**Changes Made**:

1. **ZDisplay Orchestrator** (`zOS/bifrost/src/rendering/zdisplay_orchestrator.js`):
   - Fixed JavaScript syntax error (missing closing brace at line 1542)
   - Added `condition` parameter extraction from `eventData.if` in `read_string` case
   - Sets `data-zif` attribute on conditional elements
   - Initially hides elements with conditions (`display: none`)
   - Initializes wizard conditional renderer after each chunk renders

2. **Wizard Conditional Renderer** (`zOS/bifrost/src/rendering/wizard_conditional_renderer.js`):
   - **NEW MODULE** for client-side conditional logic
   - Tracks zHat state per wizard container using WeakMap
   - Attaches change event listeners to radio/select/checkbox inputs
   - Evaluates `data-zif` conditions when selections change
   - Shows/hides elements based on condition results
   - Safe eval using Function constructor (no global access)

3. **Bifrost Client** (`zOS/bifrost/src/bifrost_client.js`):
   - Added `_ensureWizardConditionalRenderer()` lazy loader method
   - Loads and initializes wizard conditional renderer on demand

**Bifrost Mode Flow**:
```
1. Backend sends entire chunk with all three input fields
2. Each input field has data-zif="zHat[0] == 'value'" and display:none
3. WizardConditionalRenderer initializes on page load
4. User clicks "medium" radio button
5. Change event fires → updateWizardState() → zHat[0] = "medium"
6. evaluateConditions() checks all data-zif attributes:
   - data-zif="zHat[0] == 'low'" → FALSE → display:none
   - data-zif="zHat[0] == 'medium'" → TRUE → display:''
   - data-zif="zHat[0] == 'high'" → FALSE → display:none
7. Only "medium input" field visible
```

---

## Testing Results

### Terminal Mode Tests ✅

All three conditions tested and working:

```bash
# Test 1: Low selection
$ echo -e "1\ntest low value\n" | python3 zTest.py @.UI.zProducts.zTheme.zUI.zFormInputGroup:With_Checkboxes_Radios_Section.Task_radio
✅ Shows "low input" prompt

# Test 2: Medium selection  
$ echo -e "2\ntest medium value\n" | python3 zTest.py @.UI.zProducts.zTheme.zUI.zFormInputGroup:With_Checkboxes_Radios_Section.Task_radio
✅ Shows "medium input" prompt

# Test 3: High selection
$ echo -e "3\ntest high value\n" | python3 zTest.py @.UI.zProducts.zTheme.zUI.zFormInputGroup:With_Checkboxes_Radios_Section.Task_radio
✅ Shows "high input" prompt
```

**Debug logs confirm**:
- Conditions are not interpolated: `'if': "zHat[0] == 'medium'"` (not `"None == 'medium'"`)
- Wizard routes container as implicit wizard
- Sequential execution evaluates each condition correctly
- Only matching input is displayed

### Bifrost Mode Tests 🔄

**Implementation Complete**:
- ✅ JavaScript syntax fixed
- ✅ Conditional rendering module created
- ✅ Data-zif attributes set on conditional elements
- ✅ Elements initially hidden
- ✅ Change event listeners attached
- ✅ Condition evaluator implemented

**User Testing Required**:
- Refresh page: `http://127.0.0.1:8080/zProducts/zTheme/zFormInputGroup`
- Scroll to "With Checkboxes & Radios" section
- Click each radio option (low, medium, high)
- Verify correct input field appears for each selection

---

## Files Modified

### Python Backend:
1. `zOS/core/L2_Core/e_zDispatch/dispatch_modules/organizational_handler.py`
   - Routes wizard input containers as implicit wizards
   - Removed premature `if` evaluation

2. `zOS/core/L3_Abstraction/m_zWizard/zWizard_modules/wizard_interpolation.py`
   - Skips interpolating `if` parameters

3. `zOS/core/L2_Core/e_zDispatch/dispatch_modules/shorthand_expander.py`
   - Updated docstrings to clarify `if` parameter passes through to wizard

### JavaScript Frontend:
4. `zOS/bifrost/src/rendering/zdisplay_orchestrator.js`
   - Fixed syntax error (missing closing brace)
   - Added conditional rendering support for `read_string` event
   - Initializes wizard conditional renderer after chunks render

5. `zOS/bifrost/src/rendering/wizard_conditional_renderer.js` (NEW)
   - Client-side conditional evaluation engine
   - Manages zHat state per wizard
   - Shows/hides elements based on data-zif conditions

6. `zOS/bifrost/src/bifrost_client.js`
   - Added `_ensureWizardConditionalRenderer()` method

---

## Architecture

### Execution Flow

**Terminal Mode** (Server-Side Sequential):
```
zLoader → zWizard → Organizational Handler → Wizard Subsystem
                                          ↓
                            Route as Implicit Wizard
                                          ↓
                            Sequential Step Execution
                                          ↓
                            Evaluate 'if' (zHat available)
                                          ↓
                            Skip if false, execute if true
```

**Bifrost Mode** (Client-Side Reactive):
```
zLoader → zWizard → Organizational Handler → Chunk Message
                                          ↓
                            Send all elements with data-zif
                                          ↓
                            ZDisplayOrchestrator renders
                                          ↓
                            WizardConditionalRenderer initializes
                                          ↓
                            User selects radio → Change event
                                          ↓
                            Update zHat state → Evaluate conditions
                                          ↓
                            Show/hide elements dynamically
```

### Key Concepts

**zHat Context**:
- Array of values collected from previous wizard steps
- Indexed access: `zHat[0]` = first result, `zHat[1]` = second result
- Updated as each step completes

**Condition Syntax**:
- Python expressions in Terminal mode: `zHat[0] == 'value'`
- JavaScript expressions in Bifrost mode: `'value' == 'medium'` (after substitution)
- Supports: `==`, `!=`, `>`, `<`, `>=`, `<=`

**Implicit Wizards**:
- Containers with multiple input events but no explicit `zWizard` key
- Detected by organizational handler
- Routed to wizard subsystem for sequential/conditional execution

---

## Backward Compatibility

✅ **No breaking changes**:
- Existing wizards without `if` conditions work unchanged
- `if` parameter is optional
- Terminal and Bifrost modes both supported
- Longhand `zDisplay` format also supports `if` parameter

---

## Future Enhancements

Potential improvements (not required for current implementation):

1. **Complex Conditions**: Support `and`/`or` logic (e.g., `zHat[0] == 'high' and zHat[1] > 10`)
2. **Dynamic Defaults**: Set default values based on conditions
3. **Smooth Animations**: Add CSS transitions when showing/hiding elements
4. **Validation**: Check that referenced zHat indices exist
5. **Error UI**: Show user-friendly messages for failed condition evaluations

---

## Testing Checklist

- [x] Terminal mode: low selection shows "low input"
- [x] Terminal mode: medium selection shows "medium input"
- [x] Terminal mode: high selection shows "high input"
- [x] Terminal mode: conditions are not interpolated prematurely
- [x] Terminal mode: wizard routes as implicit wizard correctly
- [x] JavaScript syntax validation passed
- [x] Bifrost mode: data-zif attributes set correctly
- [x] Bifrost mode: elements initially hidden
- [ ] Bifrost mode: User testing required (refresh page and test interactions)

---

## Conclusion

The `if` conditional rendering system is now fully implemented for both Terminal and Bifrost modes. Terminal mode works via sequential execution with real-time evaluation, while Bifrost mode uses client-side JavaScript for reactive conditional rendering. The system is backward compatible, well-tested in Terminal mode, and ready for user testing in Bifrost mode.

**Next Step**: Refresh the Bifrost page and verify radio button interactions trigger the correct conditional inputs.
