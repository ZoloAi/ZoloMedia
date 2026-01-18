/**
 * InputRenderer - Interactive Input Rendering for zDisplay in Bifrost Mode
 *
 * This renderer handles individual interactive inputs that the backend sends one at a time
 * (similar to Terminal mode prompts but rendered as GUI elements).
 *
 * Input Types:
 * - Basic: text, password, email, number, tel, url
 * - Choice: selection (radio/checkbox), range, color
 * - Date/Time: date, time, datetime-local, month, week
 * - File: file (single/multiple)
 *
 * Selection Modes:
 * - GUI mode (default): Radio buttons (single) or checkboxes (multi)
 * - Terminal mode (opt-in): Number input like "1 3 5" (terminal_style: true)
 *
 * Flow:
 * 1. Backend sends input_request event with type and prompt
 * 2. InputRenderer displays appropriate input UI
 * 3. User enters value and submits
 * 4. InputRenderer validates input (frontend validation)
 * 5. InputRenderer sends input_response WebSocket message
 * 6. Backend receives response and resolves Future
 *
 * Architecture:
 * - Uses form_primitives.js for raw HTML element creation
 * - Uses dom_utils.js for DOM manipulation
 * - Uses validation_utils.js for frontend validation
 * - Applies zTheme classes for styling
 * - Handles WebSocket communication for responses
 *
 * @module InputRenderer
 */

import { createElement } from '../utils/dom_utils.js';
import { createInput, createLabel } from './primitives/form_primitives.js';
import { validateRequired } from '../utils/validation_utils.js';

export class InputRenderer {
  constructor(client) {
    this.client = client;
    this.logger = client.logger;
    this.defaultZone = 'zVaF';
  }

  /**
   * Render an input request (router method)
   * @param {Object} inputRequest - Input request from backend
   * @param {string} inputRequest.requestId - Unique request identifier
   * @param {string} inputRequest.type - Input type
   * @param {string} inputRequest.prompt - Input prompt text
   * @param {Array} inputRequest.options - Options for selection type (optional)
   * @param {boolean} inputRequest.multi - Multi-select mode for selection (optional)
   * @param {boolean} inputRequest.terminal_style - Use terminal-style number input (optional)
   * @param {string|Array} inputRequest.default - Default value(s) (optional)
   * @param {number} inputRequest.min - Min value for range/number (optional)
   * @param {number} inputRequest.max - Max value for range/number (optional)
   * @param {number} inputRequest.step - Step value for range/number (optional)
   * @param {string} targetZone - Target DOM element ID (default: 'zVaF')
   * @returns {HTMLElement} Input container element
   */
  renderInput(inputRequest, targetZone = null) {
    const zone = targetZone || this.defaultZone;
    const container = document.getElementById(zone);

    if (!container) {
      this.logger.error(`[InputRenderer] Target zone '${zone}' not found`);
      return null;
    }

    const {
      type = 'text',
      requestId,
      prompt,
      options,
      multi,
      terminal_style = false,
      default: defaultValue,
      min,
      max,
      step
    } = inputRequest;

    this.logger.log(`[InputRenderer] Rendering ${type} input:`, { requestId, prompt });

    // Route to appropriate renderer based on type
    let inputElement;
    if (type === 'selection') {
      inputElement = terminal_style
        ? this._renderSelectionTerminal(requestId, prompt, options, multi, defaultValue)
        : this._renderSelectionGUI(requestId, prompt, options, multi, defaultValue);
    } else if (type === 'password') {
      inputElement = this._renderPassword(requestId, prompt);
    } else if (type === 'range') {
      inputElement = this._renderRange(requestId, prompt, min, max, step, defaultValue);
    } else if (type === 'color') {
      inputElement = this._renderColor(requestId, prompt, defaultValue);
    } else if (['date', 'time', 'datetime-local', 'month', 'week'].includes(type)) {
      inputElement = this._renderDateTime(requestId, prompt, type, defaultValue);
    } else if (type === 'file') {
      inputElement = this._renderFile(requestId, prompt, multi);
    } else {
      // Default: text, email, number, tel, url, etc.
      inputElement = this._renderText(requestId, prompt, type, defaultValue);
    }

    // Append to zone
    container.appendChild(inputElement);

    // Auto-focus the first input field
    const input = inputElement.querySelector('input, select, textarea');
    if (input) {
      setTimeout(() => input.focus(), 100);
    }

    return inputElement;
  }

  /**
   * Render text-based input (text, email, number, tel, url)
   * @private
   */
  _renderText(requestId, prompt, type = 'text', defaultValue = '') {
    const container = createElement('div', ['zCard', 'zp-3', 'zmb-3']);

    const label = createLabel({ for: `input-${requestId}`, class: 'zForm-label zmb-2' });
    label.textContent = prompt;

    const input = createInput(type, {
      id: `input-${requestId}`,
      name: 'value',
      class: 'zForm-control zmb-2',
      placeholder: this._getPlaceholder(type),
      required: true,
      value: defaultValue || ''
    });

    const submitBtn = createElement('button', ['zBtn', 'zBtn-primary']);
    submitBtn.type = 'button';
    submitBtn.textContent = '✓ Submit';

    const errorDiv = createElement('div', ['zAlert', 'zAlert-danger', 'zmt-2']);
    errorDiv.style.display = 'none';

    const handleSubmit = () => {
      const value = input.value.trim();
      const validation = validateRequired(value, 'Input');
      if (!validation.valid) {
        this._showError(errorDiv, validation.message);
        return;
      }
      this.logger.log(`[InputRenderer] ${type} input submitted:`, { requestId, value });
      this._sendResponse(requestId, value);
      this._replaceWithConfirmation(container, `✓ Submitted: ${value}`);
    };

    submitBtn.addEventListener('click', handleSubmit);
    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleSubmit();
      }
    });

    container.appendChild(label);
    container.appendChild(input);
    container.appendChild(submitBtn);
    container.appendChild(errorDiv);

    return container;
  }

  /**
   * Render password input
   * @private
   */
  _renderPassword(requestId, prompt) {
    const container = createElement('div', ['zCard', 'zp-3', 'zmb-3']);

    const label = createLabel({ for: `input-${requestId}`, class: 'zForm-label zmb-2' });
    label.textContent = prompt;

    const input = createInput('password', {
      id: `input-${requestId}`,
      name: 'value',
      class: 'zForm-control zmb-2',
      placeholder: 'Enter password...',
      required: true
    });

    const submitBtn = createElement('button', ['zBtn', 'zBtn-primary']);
    submitBtn.type = 'button';
    submitBtn.textContent = '✓ Submit';

    const errorDiv = createElement('div', ['zAlert', 'zAlert-danger', 'zmt-2']);
    errorDiv.style.display = 'none';

    const handleSubmit = () => {
      const value = input.value;
      const validation = validateRequired(value, 'Password');
      if (!validation.valid) {
        this._showError(errorDiv, validation.message);
        return;
      }
      this.logger.log('[InputRenderer] Password submitted:', { requestId, length: value.length });
      this._sendResponse(requestId, value);
      this._replaceWithConfirmation(container, `✓ Password submitted (${value.length} characters)`);
    };

    submitBtn.addEventListener('click', handleSubmit);
    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleSubmit();
      }
    });

    container.appendChild(label);
    container.appendChild(input);
    container.appendChild(submitBtn);
    container.appendChild(errorDiv);

    return container;
  }

  /**
   * Render GUI-style selection (radio buttons or checkboxes)
   * @private
   */
  _renderSelectionGUI(requestId, prompt, options = [], multi = false, defaultValue = null) {
    const container = createElement('div', ['zCard', 'zp-3', 'zmb-3']);

    const title = createElement('h4', ['zForm-label', 'zmb-3']);
    title.textContent = prompt;

    const optionsContainer = createElement('div', ['zmb-3']);
    const selectedValues = new Set(Array.isArray(defaultValue) ? defaultValue : (defaultValue ? [defaultValue] : []));

    options.forEach((option, index) => {
      const optionDiv = createElement('div', ['zForm-check', 'zmb-2']);

      const input = createInput(multi ? 'checkbox' : 'radio', {
        id: `option-${requestId}-${index}`,
        name: multi ? `option-${requestId}` : `selection-${requestId}`,
        class: 'zForm-check-input',
        value: option
      });

      if (selectedValues.has(option)) {
        input.checked = true;
      }

      const label = createLabel({
        for: `option-${requestId}-${index}`,
        class: 'zForm-check-label'
      });
      label.textContent = option;

      optionDiv.appendChild(input);
      optionDiv.appendChild(label);
      optionsContainer.appendChild(optionDiv);
    });

    const submitBtn = createElement('button', ['zBtn', 'zBtn-primary']);
    submitBtn.type = 'button';
    submitBtn.textContent = '✓ Submit';

    const errorDiv = createElement('div', ['zAlert', 'zAlert-danger', 'zmt-2']);
    errorDiv.style.display = 'none';

    const handleSubmit = () => {
      const inputs = container.querySelectorAll('input[type="checkbox"], input[type="radio"]');
      const selected = Array.from(inputs).filter(input => input.checked).map(input => input.value);

      if (selected.length === 0) {
        this._showError(errorDiv, 'Please select at least one option');
        return;
      }

      const result = multi ? selected : selected[0];
      this.logger.log('[InputRenderer] Selection submitted:', { requestId, result });
      this._sendResponse(requestId, result);

      const confirmationText = multi
        ? `✓ Selected: ${selected.join(', ')}`
        : `✓ Selected: ${result}`;
      this._replaceWithConfirmation(container, confirmationText);
    };

    submitBtn.addEventListener('click', handleSubmit);

    container.appendChild(title);
    container.appendChild(optionsContainer);
    container.appendChild(submitBtn);
    container.appendChild(errorDiv);

    return container;
  }

  /**
   * Render terminal-style selection (number input)
   * @private
   */
  _renderSelectionTerminal(requestId, prompt, options = [], multi = false, defaultValue = null) {
    const container = createElement('div', ['zCard', 'zp-3', 'zmb-3']);

    const title = createElement('h4', ['zForm-label', 'zmb-3']);
    title.textContent = prompt;

    const optionsList = createElement('div', ['zmb-3']);

    options.forEach((option, index) => {
      const optionDiv = createElement('div', ['zp-2', 'zmb-1', 'zBorder', 'zRounded']);
      optionDiv.textContent = `${index + 1}. ${option}`;
      optionsList.appendChild(optionDiv);
    });

    const instructions = createElement('p', ['zText-muted', 'zmb-2']);
    instructions.textContent = multi
      ? 'Enter numbers separated by spaces (e.g., "1 3 5"):'
      : `Enter choice (1-${options.length}):`;

    const input = createInput('text', {
      id: `input-${requestId}`,
      name: 'value',
      class: 'zForm-control zmb-2',
      placeholder: multi ? 'e.g., 1 3 5' : 'e.g., 1',
      required: true
    });

    if (defaultValue) {
      if (Array.isArray(defaultValue)) {
        const defaultIndices = defaultValue.map(val => options.indexOf(val) + 1).filter(idx => idx > 0);
        input.value = defaultIndices.join(' ');
      } else {
        const defaultIndex = options.indexOf(defaultValue) + 1;
        if (defaultIndex > 0) {
          input.value = String(defaultIndex);
        }
      }
    }

    const submitBtn = createElement('button', ['zBtn', 'zBtn-primary']);
    submitBtn.type = 'button';
    submitBtn.textContent = '✓ Submit';

    const errorDiv = createElement('div', ['zAlert', 'zAlert-danger', 'zmt-2']);
    errorDiv.style.display = 'none';

    const handleSubmit = () => {
      const value = input.value.trim();
      const validation = this._validateSelection(value, options.length, multi);
      if (!validation.valid) {
        this._showError(errorDiv, validation.message);
        return;
      }

      let result;
      if (multi) {
        const indices = value.split(/\s+/).map(n => parseInt(n, 10));
        result = indices.map(idx => options[idx - 1]);
      } else {
        const index = parseInt(value, 10);
        result = options[index - 1];
      }

      this.logger.log('[InputRenderer] Terminal-style selection submitted:', { requestId, result });
      this._sendResponse(requestId, result);

      const confirmationText = multi
        ? `✓ Selected: ${result.join(', ')}`
        : `✓ Selected: ${result}`;
      this._replaceWithConfirmation(container, confirmationText);
    };

    submitBtn.addEventListener('click', handleSubmit);
    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleSubmit();
      }
    });

    container.appendChild(title);
    container.appendChild(optionsList);
    container.appendChild(instructions);
    container.appendChild(input);
    container.appendChild(submitBtn);
    container.appendChild(errorDiv);

    return container;
  }

  /**
   * Render range input
   * @private
   */
  _renderRange(requestId, prompt, min = 0, max = 100, step = 1, defaultValue = 50) {
    const container = createElement('div', ['zCard', 'zp-3', 'zmb-3']);

    const label = createLabel({ for: `input-${requestId}`, class: 'zForm-label zmb-2' });
    label.textContent = prompt;

    const valueDisplay = createElement('span', ['zBadge', 'zBg-primary', 'zms-2']);
    valueDisplay.textContent = defaultValue || min;
    label.appendChild(valueDisplay);

    const input = createInput('range', {
      id: `input-${requestId}`,
      name: 'value',
      class: 'zForm-range zmb-2',
      min: String(min),
      max: String(max),
      step: String(step),
      value: String(defaultValue || min)
    });

    input.addEventListener('input', () => {
      valueDisplay.textContent = input.value;
    });

    const submitBtn = createElement('button', ['zBtn', 'zBtn-primary']);
    submitBtn.type = 'button';
    submitBtn.textContent = '✓ Submit';

    const handleSubmit = () => {
      const value = input.value;
      this.logger.log('[InputRenderer] Range submitted:', { requestId, value });
      this._sendResponse(requestId, parseFloat(value));
      this._replaceWithConfirmation(container, `✓ Selected: ${value}`);
    };

    submitBtn.addEventListener('click', handleSubmit);

    container.appendChild(label);
    container.appendChild(input);
    container.appendChild(submitBtn);

    return container;
  }

  /**
   * Render color input
   * @private
   */
  _renderColor(requestId, prompt, defaultValue = '#000000') {
    const container = createElement('div', ['zCard', 'zp-3', 'zmb-3']);

    const label = createLabel({ for: `input-${requestId}`, class: 'zForm-label zmb-2' });
    label.textContent = prompt;

    const inputGroup = createElement('div', ['zD-flex', 'zGap-2', 'zFlex-items-center', 'zmb-2']);

    const input = createInput('color', {
      id: `input-${requestId}`,
      name: 'value',
      class: 'zForm-control-color',
      value: defaultValue || '#000000'
    });

    const hexDisplay = createElement('code', ['zBg-light', 'zp-2', 'zRounded']);
    hexDisplay.textContent = defaultValue || '#000000';

    input.addEventListener('input', () => {
      hexDisplay.textContent = input.value;
    });

    inputGroup.appendChild(input);
    inputGroup.appendChild(hexDisplay);

    const submitBtn = createElement('button', ['zBtn', 'zBtn-primary']);
    submitBtn.type = 'button';
    submitBtn.textContent = '✓ Submit';

    const handleSubmit = () => {
      const value = input.value;
      this.logger.log('[InputRenderer] Color submitted:', { requestId, value });
      this._sendResponse(requestId, value);
      this._replaceWithConfirmation(container, `✓ Selected color: ${value}`);
    };

    submitBtn.addEventListener('click', handleSubmit);

    container.appendChild(label);
    container.appendChild(inputGroup);
    container.appendChild(submitBtn);

    return container;
  }

  /**
   * Render date/time input
   * @private
   */
  _renderDateTime(requestId, prompt, type, defaultValue = '') {
    const container = createElement('div', ['zCard', 'zp-3', 'zmb-3']);

    const label = createLabel({ for: `input-${requestId}`, class: 'zForm-label zmb-2' });
    label.textContent = prompt;

    const input = createInput(type, {
      id: `input-${requestId}`,
      name: 'value',
      class: 'zForm-control zmb-2',
      required: true,
      value: defaultValue || ''
    });

    const submitBtn = createElement('button', ['zBtn', 'zBtn-primary']);
    submitBtn.type = 'button';
    submitBtn.textContent = '✓ Submit';

    const errorDiv = createElement('div', ['zAlert', 'zAlert-danger', 'zmt-2']);
    errorDiv.style.display = 'none';

    const handleSubmit = () => {
      const value = input.value;
      const validation = validateRequired(value, 'Date/Time');
      if (!validation.valid) {
        this._showError(errorDiv, validation.message);
        return;
      }
      this.logger.log(`[InputRenderer] ${type} submitted:`, { requestId, value });
      this._sendResponse(requestId, value);
      this._replaceWithConfirmation(container, `✓ Selected: ${value}`);
    };

    submitBtn.addEventListener('click', handleSubmit);

    container.appendChild(label);
    container.appendChild(input);
    container.appendChild(submitBtn);
    container.appendChild(errorDiv);

    return container;
  }

  /**
   * Render file input
   * @private
   */
  _renderFile(requestId, prompt, multi = false) {
    const container = createElement('div', ['zCard', 'zp-3', 'zmb-3']);

    const label = createLabel({ for: `input-${requestId}`, class: 'zForm-label zmb-2' });
    label.textContent = prompt;

    const input = createInput('file', {
      id: `input-${requestId}`,
      name: 'value',
      class: 'zForm-control zmb-2',
      multiple: multi
    });

    const submitBtn = createElement('button', ['zBtn', 'zBtn-primary']);
    submitBtn.type = 'button';
    submitBtn.textContent = '✓ Submit';

    const errorDiv = createElement('div', ['zAlert', 'zAlert-danger', 'zmt-2']);
    errorDiv.style.display = 'none';

    const handleSubmit = () => {
      if (input.files.length === 0) {
        this._showError(errorDiv, 'Please select a file');
        return;
      }
      const fileNames = Array.from(input.files).map(f => f.name);
      this.logger.log('[InputRenderer] File(s) selected:', { requestId, files: fileNames });
      this._sendResponse(requestId, fileNames);
      this._replaceWithConfirmation(container, `✓ Selected: ${fileNames.join(', ')}`);
    };

    submitBtn.addEventListener('click', handleSubmit);

    container.appendChild(label);
    container.appendChild(input);
    container.appendChild(submitBtn);
    container.appendChild(errorDiv);

    return container;
  }

  /**
   * Get placeholder text for input type
   * @private
   */
  _getPlaceholder(type) {
    const placeholders = {
      text: 'Enter text...',
      email: 'Enter email address...',
      number: 'Enter number...',
      tel: 'Enter phone number...',
      url: 'Enter URL...'
    };
    return placeholders[type] || 'Enter value...';
  }

  /**
   * Validate terminal-style selection input
   * @private
   */
  _validateSelection(value, maxNum, multi) {
    if (!value) {
      return { valid: false, message: 'Please enter a selection' };
    }

    const numbers = value.split(/\s+/).map(n => parseInt(n, 10));

    if (numbers.some(n => isNaN(n))) {
      return { valid: false, message: 'Please enter valid numbers only' };
    }

    if (numbers.some(n => n < 1 || n > maxNum)) {
      return { valid: false, message: `Please enter numbers between 1 and ${maxNum}` };
    }

    if (!multi && numbers.length > 1) {
      return { valid: false, message: 'Please enter only one number' };
    }

    return { valid: true, message: '' };
  }

  /**
   * Send input response to backend
   * @private
   */
  _sendResponse(requestId, value) {
    const connection = this.client?.connection;

    if (!connection) {
      this.logger.error('[InputRenderer] No WebSocket connection available');
      return;
    }

    try {
      connection.send(JSON.stringify({
        event: 'input_response',
        requestId: requestId,
        value: value
      }));

      this.logger.log('[InputRenderer] Response sent:', { requestId, value });
    } catch (error) {
      this.logger.error('[InputRenderer] Failed to send response:', error);
    }
  }

  /**
   * Show error message
   * @private
   */
  _showError(errorDiv, message) {
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
  }

  /**
   * Replace input container with confirmation message
   * @private
   */
  _replaceWithConfirmation(container, message) {
    const confirmation = createElement('div', ['zAlert', 'zAlert-success', 'zp-3', 'zmb-3']);
    confirmation.textContent = message;
    container.replaceWith(confirmation);
  }
}
