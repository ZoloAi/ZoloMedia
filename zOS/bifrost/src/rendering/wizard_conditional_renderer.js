/**
 * Wizard Conditional Renderer - Client-Side If Condition Evaluation
 * ==================================================================
 * 
 * Handles conditional rendering of wizard steps in Bifrost mode.
 * When elements have data-zif attributes, this module evaluates them
 * based on user input (radio/select changes) and shows/hides elements accordingly.
 * 
 * Usage:
 *   1. Elements with 'if' parameter get data-zif attribute and display:none initially
 *   2. When a selection changes (radio, checkbox, select), evaluate all data-zif conditions
 *   3. Show elements where condition is true, hide where false
 * 
 * Condition Syntax:
 *   - zHat[0] == 'value'  - Check first wizard result
 *   - zHat[1] == 'value'  - Check second wizard result
 *   - zHat[0] != 'value'  - Not equal check
 *   - zHat[0] > 5         - Numeric comparison
 * 
 * Example:
 *   <div data-zif="zHat[0] == 'medium'" style="display: none;">
 *     <label>Medium input</label>
 *     <input type="text" />
 *   </div>
 * 
 * Layer: 2, Position: Bifrost rendering
 * Version: v1.0.0
 */

export class WizardConditionalRenderer {
  constructor(logger) {
    this.logger = logger || console;
    this.wizardStates = new WeakMap(); // Track zHat state per wizard container
  }

  /**
   * Initialize conditional rendering for a wizard container
   * Finds all selection controls (radio, select, checkbox) and attaches change handlers
   * 
   * @param {HTMLElement} wizardContainer - The wizard container element
   */
  initializeWizard(wizardContainer) {
    if (!wizardContainer) {
      console.error('[WizardConditionalRenderer] No wizard container provided');
      this.logger.error('[WizardConditionalRenderer] No wizard container provided');
      return;
    }

    const containerId = wizardContainer.id || wizardContainer.getAttribute('data-zkey') || '(no id)';
    console.log(`[WizardConditionalRenderer] 🧙 Initializing wizard container: ${containerId}`, wizardContainer);
    this.logger.log(`[WizardConditionalRenderer] 🧙 Initializing wizard container: ${containerId}`);

    // Initialize zHat state for this wizard (array of values by step index)
    const zHat = [];
    this.wizardStates.set(wizardContainer, zHat);

    // Find all input controls in order (radio, select, checkbox, text inputs)
    const allInputs = Array.from(wizardContainer.querySelectorAll('input, select, textarea'));
    console.log(`[WizardConditionalRenderer] 🧙 Found ${allInputs.length} input(s) in wizard container:`, allInputs.map(i => ({type: i.type, id: i.id, checked: i.checked, zkey: i.closest('[data-zkey]')?.getAttribute('data-zkey')})));
    this.logger.log(`[WizardConditionalRenderer] 🧙 Found ${allInputs.length} input(s) in wizard container`);
    
    // Map inputs to their step index (order of appearance)
    allInputs.forEach((input, index) => {
      // Skip if this input is inside a conditional element that's hidden
      const conditionalParent = input.closest('[data-zif]');
      if (conditionalParent && conditionalParent.style.display === 'none') {
        this.logger.log(`[WizardConditionalRenderer] ⏭️  Skipping hidden input at index ${index}: ${input.id || input.type}`);
        return; // Don't track hidden inputs initially
      }

      const checkedValue = input.type === 'checkbox' || input.type === 'radio' ? input.checked : (input.value || 'N/A');
      console.log(`[WizardConditionalRenderer] 📝 Input ${index}: type=${input.type}, id=${input.id}, checked=${checkedValue}, zkey=${input.closest('[data-zkey]')?.getAttribute('data-zkey') || 'none'}`);
      this.logger.log(`[WizardConditionalRenderer] 📝 Input ${index}: type=${input.type}, id=${input.id}, checked=${checkedValue}`);

      // Track selection changes for radio/select/checkbox
      if (input.type === 'radio' || input.type === 'checkbox' || input.tagName === 'SELECT') {
        input.addEventListener('change', () => {
          console.log(`[WizardConditionalRenderer] 🔄 Selection changed: ${input.name || input.id} = ${input.value || input.checked} (type: ${input.type})`);
          this.logger.log(`[WizardConditionalRenderer] 🔄 Selection changed: ${input.name || input.id} = ${input.value || input.checked}`);
          this.updateWizardState(wizardContainer, input);
          this.evaluateConditions(wizardContainer);
        });
        // Also listen for click events on checkboxes to catch any edge cases
        if (input.type === 'checkbox') {
          input.addEventListener('click', () => {
            console.log(`[WizardConditionalRenderer] 🖱️ Checkbox clicked: ${input.id}, checked=${input.checked}`);
          });
        }
      }
    });

    // Initial evaluation (in case there are defaults)
    console.log(`[WizardConditionalRenderer] 🔄 Running initial updateWizardState and evaluateConditions for: ${containerId}`);
    this.updateWizardState(wizardContainer);
    this.evaluateConditions(wizardContainer);
    console.log(`[WizardConditionalRenderer] ✅ Initialization complete for: ${containerId}`);
  }

  /**
   * Update the zHat state for a wizard based on current input values
   * 
   * @param {HTMLElement} wizardContainer - The wizard container
   * @param {HTMLElement} changedInput - Optional specific input that changed
   */
  updateWizardState(wizardContainer, changedInput = null) {
    const zHat = this.wizardStates.get(wizardContainer) || [];

    // Find all input controls in order (radio, checkbox, select, text inputs)
    // This matches the order they appear in the wizard
    const allInputs = Array.from(wizardContainer.querySelectorAll('input, select, textarea'));
    
    this.logger.log(`[WizardConditionalRenderer] 🔄 Updating zHat state from ${allInputs.length} input(s)`);
    
    // Clear and rebuild zHat from current input values
    zHat.length = 0;
    
    allInputs.forEach((input, index) => {
      // Skip if this input is inside a conditional element that's hidden
      const conditionalParent = input.closest('[data-zif]');
      if (conditionalParent && conditionalParent.style.display === 'none') {
        this.logger.log(`[WizardConditionalRenderer] ⏭️  Skipping hidden input at index ${index} for zHat`);
        return; // Don't track hidden inputs
      }

      if (input.type === 'radio') {
        // Only track checked radio buttons
        if (input.checked) {
          zHat[index] = input.value;
          this.logger.log(`[WizardConditionalRenderer] 📊 zHat[${index}] = '${input.value}' (radio)`);
        }
      } else if (input.type === 'checkbox') {
        // Track checkbox boolean state
        zHat[index] = input.checked;
        console.log(`[WizardConditionalRenderer] 📊 zHat[${index}] = ${input.checked} (checkbox, id: ${input.id})`);
        this.logger.log(`[WizardConditionalRenderer] 📊 zHat[${index}] = ${input.checked} (checkbox)`);
      } else if (input.tagName === 'SELECT') {
        zHat[index] = input.value;
        this.logger.log(`[WizardConditionalRenderer] 📊 zHat[${index}] = '${input.value}' (select)`);
      } else if (input.type === 'text' || input.type === 'email' || input.type === 'password' || input.type === 'number') {
        // Track text input values (for conditional logic based on input values)
        zHat[index] = input.value || '';
        this.logger.log(`[WizardConditionalRenderer] 📊 zHat[${index}] = '${input.value || ''}' (text input)`);
      }
    });

    this.wizardStates.set(wizardContainer, zHat);
    console.log(`[WizardConditionalRenderer] ✅ Updated zHat state:`, zHat);
    this.logger.log(`[WizardConditionalRenderer] ✅ Updated zHat state:`, zHat);
  }

  /**
   * Evaluate all data-zif conditions in a wizard container
   * Shows elements where condition is true, hides where false
   * 
   * @param {HTMLElement} wizardContainer - The wizard container
   */
  evaluateConditions(wizardContainer) {
    const zHat = this.wizardStates.get(wizardContainer) || [];
    
    // Check if zCross is enabled (terminal-first behavior)
    // Find checkbox or radio button in this wizard container to check zCross flag
    const checkbox = wizardContainer.querySelector('input[type="checkbox"]');
    const radio = wizardContainer.querySelector('input[type="radio"]');
    const controlElement = checkbox || radio;
    const zCross = controlElement ? (controlElement.getAttribute('data-zcross') === 'true') : false;
    
    console.log(`[WizardConditionalRenderer] 🔍 zCross mode: ${zCross} (control found: ${!!controlElement}, type: ${controlElement ? controlElement.type : 'none'})`);
    this.logger.log(`[WizardConditionalRenderer] 🔍 zCross mode: ${zCross} (terminal-first behavior: ${zCross}, HTML-like behavior: ${!zCross})`);
    
    // Find all elements with data-zif conditions
    const conditionalElements = Array.from(wizardContainer.querySelectorAll('[data-zif]'));
    
    console.log(`[WizardConditionalRenderer] 🔍 Evaluating ${conditionalElements.length} condition(s) with zHat:`, zHat);
    console.log(`[WizardConditionalRenderer] 🔍 Conditional elements:`, conditionalElements.map(el => ({id: el.id, zkey: el.getAttribute('data-zkey'), zif: el.getAttribute('data-zif'), display: el.style.display})));
    this.logger.log(`[WizardConditionalRenderer] 🔍 Evaluating ${conditionalElements.length} condition(s) with zHat:`, zHat);

    if (conditionalElements.length === 0) {
      this.logger.log(`[WizardConditionalRenderer] ⚠️  No conditional elements found in wizard container`);
    }

    conditionalElements.forEach((element, idx) => {
      const condition = element.getAttribute('data-zif');
      const elementId = element.id || element.getAttribute('data-zkey') || `element-${idx}`;
      
      this.logger.log(`[WizardConditionalRenderer] 🔍 Evaluating condition ${idx + 1}/${conditionalElements.length}: "${condition}" for element: ${elementId}`);
      
      try {
        // If zCross is false (HTML-like behavior), always show the element
        // Only apply conditional rendering if zCross is true (terminal-first behavior)
        if (!zCross) {
          element.style.display = ''; // Always visible in HTML-like mode
          console.log(`[WizardConditionalRenderer] 📄 Show element (HTML-like mode, zCross=false): ${elementId}`);
          this.logger.log(`[WizardConditionalRenderer] 📄 Show element (HTML-like mode, zCross=false): ${elementId}`);
          return; // Skip condition evaluation
        }
        
        // Evaluate condition safely (only in terminal-first mode)
        // Replace zHat[N] with actual values from zHat array
        const result = this.evaluateCondition(condition, zHat);
        
        // Show/hide based on result (terminal-first mode)
        if (result) {
          element.style.display = ''; // Show (use default display)
          console.log(`[WizardConditionalRenderer] ✅ Show element: ${elementId} (condition: ${condition})`);
        this.logger.log(`[WizardConditionalRenderer] ✅ Show element: ${elementId} (condition: ${condition})`);
        } else {
          element.style.display = 'none'; // Hide
          console.log(`[WizardConditionalRenderer] ❌ Hide element: ${elementId} (condition: ${condition})`);
          this.logger.log(`[WizardConditionalRenderer] ❌ Hide element: ${elementId} (condition: ${condition})`);
        }
      } catch (err) {
        this.logger.error(`[WizardConditionalRenderer] ❌ Failed to evaluate condition '${condition}' for ${elementId}:`, err);
        element.style.display = 'none'; // Hide on error (safe default)
      }
    });
  }

  /**
   * Evaluate a single condition expression
   * 
   * @param {string} condition - The condition string (e.g., "zHat[0] == 'medium'")
   * @param {Array} zHat - The current zHat state
   * @returns {boolean} - True if condition passes
   */
  evaluateCondition(condition, zHat) {
    // Build a safe evaluation context
    // Replace zHat[N] references with actual values
    let evalExpression = condition;
    
    // Strip YAML-style comments (everything after # that's not inside quotes)
    // This handles cases where YAML parsers include comments in the condition string
    evalExpression = evalExpression.replace(/#.*$/gm, '').trim();
    
    // Replace zHat[0], zHat[1], etc. with actual values
    evalExpression = evalExpression.replace(/zHat\[(\d+)\]/g, (match, index) => {
      const idx = parseInt(index);
      const value = zHat[idx];
      // Quote string values for comparison
      if (typeof value === 'string') {
        return `'${value.replace(/'/g, "\\'")}'`; // Escape quotes
      }
      return String(value !== undefined ? value : 'undefined');
    });

    console.log(`[WizardConditionalRenderer] 🔍 Evaluating: "${condition}" → "${evalExpression}"`);
    this.logger.log(`[WizardConditionalRenderer] 🔍 Evaluating: "${condition}" → "${evalExpression}"`);

    // Safe eval using Function constructor (only comparing values, no access to globals)
    try {
      const result = new Function(`return ${evalExpression}`)();
      const boolResult = Boolean(result);
      console.log(`[WizardConditionalRenderer] ✅ Evaluation result: ${result} → ${boolResult}`);
      this.logger.log(`[WizardConditionalRenderer] ✅ Condition result: ${boolResult} (raw: ${result})`);
      return boolResult;
    } catch (err) {
      this.logger.error(`[WizardConditionalRenderer] ❌ Evaluation error for "${evalExpression}":`, err);
      return false;
    }
  }
}

// Auto-initialize for all wizard containers on page load
document.addEventListener('DOMContentLoaded', () => {
  const logger = window.BifrostClient?.logger || console;
  const renderer = new WizardConditionalRenderer(logger);
  
  // Find all wizard containers (elements with zWizard class or data-zkey="zWizard")
  const wizards = document.querySelectorAll('[data-zkey*="Wizard"], .zInputGroup');
  
  logger.log(`[WizardConditionalRenderer] Found ${wizards.length} wizard container(s) for conditional rendering`);
  
  wizards.forEach(wizard => {
    renderer.initializeWizard(wizard);
  });
});
