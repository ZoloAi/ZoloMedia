/**
 * ═══════════════════════════════════════════════════════════════
 * Button Renderer - Interactive Button Input Events
 * ═══════════════════════════════════════════════════════════════
 *
 * Terminal-First Design (Refactored Micro-Step 8):
 * - Backend sends semantic color (danger, success, warning, etc.)
 * - Terminal displays colored prompts matching semantic meaning
 * - Bifrost renders buttons using zTheme button variants (.zBtn-primary, etc.)
 *
 * Renders button input events from zCLI backend. Creates interactive
 * button elements with zTheme button component classes and WebSocket
 * response handling.
 *
 * @module rendering/button_renderer
 * @layer 3
 * @pattern Strategy (single event type)
 *
 * Dependencies:
 * - Layer 0: primitives/interactive_primitives.js (createButton)
 * - Layer 2: dom_utils.js (createElement, replaceElement)
 * - zTheme: Button component classes (.zBtn, .zBtn-primary, etc.)
 *
 * Exports:
 * - ButtonRenderer: Class for rendering button events
 *
 * Example:
 * ```javascript
 * import ButtonRenderer from './button_renderer.js';
 *
 * const renderer = new ButtonRenderer(logger, client);
 * renderer.render({
 *   label: 'Submit',
 *   action: 'process_form',
 *   color: 'primary',
 *   requestId: '123'
 * }, 'zVaF');
 * ```
 */

// ─────────────────────────────────────────────────────────────────
// Imports
// ─────────────────────────────────────────────────────────────────
import { createButton } from './primitives/interactive_primitives.js';

// ─────────────────────────────────────────────────────────────────
// Main Implementation
// ─────────────────────────────────────────────────────────────────

/**
 * Renders button input events for zDisplay
 *
 * Handles the 'button' event type from zCLI backend, creating
 * interactive button elements with zTheme styling and WebSocket
 * response handling.
 *
 * @class
 */
export default class ButtonRenderer {
  /**
   * Create a button renderer
   * @param {Object} logger - Logger instance for debugging
   * @param {Object} client - BifrostClient instance for sending responses
   */
  constructor(logger, client = null) {
    if (!logger) {
      throw new Error('[ButtonRenderer] logger is required');
    }

    this.logger = logger;
    this.client = client;
    this.defaultZone = 'zVaF-content';
  }

  /**
   * Render a button input request
   *
   * Terminal-First Design:
   * - Backend sends semantic color (danger, success, warning, primary, info, secondary)
   * - Bifrost renders button with matching zTheme color class
   *
   * @param {Object} data - Button configuration
   * @param {string} data.label - Button label text (or 'prompt')
   * @param {string} data.action - Action identifier (or '#' for placeholder)
   * @param {string} [data.color='primary'] - Button semantic color
   *   - primary: Default action (blue)
   *   - danger: Destructive action (red)
   *   - success: Positive action (green)
   *   - warning: Cautious action (yellow)
   *   - info: Informational (cyan)
   *   - secondary: Neutral (gray)
   * @param {string} data.requestId - Request ID for response correlation
   * @param {string} zone - Target DOM element ID
   * @returns {HTMLElement|null} Created button container, or null if zone not found
   */
  render(data, zone) {
    // Validate inputs
    if (!data) {
      this.logger.error('[ButtonRenderer] data is required');
      return null;
    }

    // Extract data (support both direct and nested formats)
    const requestId = data.requestId || data.data?.requestId;
    const label = data.label || data.prompt || data.data?.prompt || 'Click Me';
    const action = data.action || data.data?.action || null;
    const rawColor = data.color || data.data?.color || 'primary';
    const color = rawColor.toLowerCase(); // Normalize to lowercase for consistency

    this.logger.log('[ButtonRenderer] Rendering button:', { requestId, label, action, color });

    // Create button primitive (just the button, no container)
    const button = this._createButton(label, color, data._zClass, data._id);
    this._attachClickHandler(button, requestId, label, true);

    // ✅ NO cancel button in Bifrost! (Terminal-first: y/n, GUI: click or ignore)
    // In terminal, button is y/n prompt. In GUI, button is click or don't click.
    // We're asynchronous - user can just ignore the button.

    // If zone is provided, append to DOM (legacy behavior for direct calls)
    // If no zone, just return element (orchestrator pattern)
    if (zone) {
      const targetZone = zone || data.target || this.defaultZone;
      const container = document.getElementById(targetZone);

      if (!container) {
        this.logger.error(`[ButtonRenderer] Zone not found: ${targetZone}`);
        return button; // Still return element even if zone not found
      }

      // Add to page
      container.appendChild(button);
      this.logger.log('[ButtonRenderer] Button rendered and appended to zone');
    }

    this.logger.log('[ButtonRenderer] Button rendered successfully');
    return button;
  }

  /**
   * Create a single button element from primitives + zTheme button variants
   *
   * Architecture:
   * - Layer 0.0: createButton() - Raw <button> element
   * - Layer 3 (here): Apply zTheme button variant classes (.zBtn-primary, etc.)
   *
   * Terminal-First Design:
   * - Uses semantic color from backend (matches terminal prompt color)
   * - Maps to zTheme button variant classes for consistent styling
   *
   * @private
   * @param {string} label - Button text
   * @param {string} color - Button semantic color (primary, danger, success, warning, info, secondary)
   * @param {string} [customClass] - Optional custom classes for layout (_zClass from YAML)
   * @param {string} [customId] - Optional custom id for targeting (_id from YAML)
   * @returns {HTMLElement} Button element
   */
  _createButton(label, color, customClass, customId) {
    this.logger.log(`[ButtonRenderer] Creating button "${label}" with color: ${color}`);

    // ✅ Layer 0.0: Create raw button primitive with attributes
    const attrs = { class: 'zBtn' }; // Base button styling only (padding, border, etc.)
    if (customId) {
      attrs.id = customId;
    }  // Pass _id to primitive
    const button = createButton('button', attrs);

    button.textContent = label;

    // ✅ Apply semantic button variant classes (zTheme button components)
    // Map zCLI semantic colors to zTheme button variant classes (.zBtn-primary, etc.)
    const colorMap = {
      'primary': 'zBtn-primary',       // Green (zCLI brand)
      'danger': 'zBtn-danger',         // Red (destructive action)
      'success': 'zBtn-success',       // Green (positive action)
      'warning': 'zBtn-warning',       // Orange (cautious action)
      'info': 'zBtn-info',             // Blue (informational)
      'secondary': 'zBtn-secondary'    // Purple (secondary action)
    };

    const btnClass = colorMap[color] || 'zBtn-primary';
    button.classList.add(btnClass);
    this.logger.log(`[ButtonRenderer] Applied button variant class: ${btnClass}`);

    // Apply custom classes if provided (_zClass from YAML - for layout/spacing)
    if (customClass) {
      button.className += ` ${customClass}`;
      this.logger.log(`[ButtonRenderer] Applied custom classes: ${customClass}`);
    }

    if (customId) {
      this.logger.log(`[ButtonRenderer] Applied custom id: ${customId}`);
    }

    // ✅ Proper composition: Primitive + zTheme Button Variant = Styled Button
    // Uses semantic button classes (.zBtn-primary) per zTheme conventions

    return button;
  }

  /**
   * Attach click handler to button
   * @private
   * @param {HTMLElement} button - Button element
   * @param {string} requestId - Request ID for response
   * @param {string} originalLabel - Original button label
   * @param {boolean} value - Response value (true for primary, false for cancel)
   */
  _attachClickHandler(button, requestId, originalLabel, value) {
    button.addEventListener('click', () => {
      this.logger.log(`[ButtonRenderer] Button clicked: ${button.textContent} (value: ${value})`);

      // Send response to backend via WebSocket
      this._sendResponse(requestId, value);

      // Disable button after click to prevent double-submission
      button.disabled = true;
      button.textContent = `✓ ${originalLabel}`;
    });
  }

  /**
   * Send button response to backend
   * @private
   * @param {string} requestId - Request ID
   * @param {boolean} value - Response value
   */
  _sendResponse(requestId, value) {
    // Try to get connection from client or global window object
    const connection = this.client?.connection || window.bifrostClient?.connection;

    if (!connection) {
      this.logger.error('[ButtonRenderer] No WebSocket connection available');
      return;
    }

    try {
      connection.send(JSON.stringify({
        event: 'input_response',
        requestId: requestId,
        value: value
      }));

      this.logger.log('[ButtonRenderer] Response sent:', { requestId, value });
    } catch (error) {
      this.logger.error('[ButtonRenderer] Failed to send response:', error);
    }
  }

}
