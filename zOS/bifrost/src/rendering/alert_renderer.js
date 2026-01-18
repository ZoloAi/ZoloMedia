/**
 * ═══════════════════════════════════════════════════════════════
 * Alert Renderer - Signal/Feedback Messages
 * ═══════════════════════════════════════════════════════════════
 *
 * Renders alert/signal events from zCLI backend (zSignals subsystem).
 * Provides visual feedback for success, info, warning, and error states.
 *
 * @module rendering/alert_renderer
 * @layer 3
 * @pattern Strategy (single event family)
 *
 * Philosophy:
 * - "Terminal first" - alerts are visual feedback primitives
 * - Pure rendering (no auto-dismiss, no complex animations)
 * - Semantic colors (success=green, info=blue, warning=orange, error=red)
 * - Uses Layer 2 utilities exclusively (no inline logic)
 *
 * Dependencies:
 * - Layer 2: dom_utils.js, ztheme_utils.js
 *
 * Exports:
 * - AlertRenderer: Class for rendering alert/signal events
 *
 * Example:
 * ```javascript
 * import { AlertRenderer } from './alert_renderer.js';
 *
 * const renderer = new AlertRenderer(logger);
 * renderer.render({
 *   content: 'Operation successful!',
 *   eventType: 'success'
 * }, 'zVaF');
 * ```
 */

// ─────────────────────────────────────────────────────────────────
// Imports
// ─────────────────────────────────────────────────────────────────
import { createElement, setAttributes } from '../utils/dom_utils.js';
import { getAlertColorClass } from '../utils/ztheme_utils.js';
import { withErrorBoundary } from '../utils/error_boundary.js';

// ─────────────────────────────────────────────────────────────────
// Alert Renderer Class
// ─────────────────────────────────────────────────────────────────

/**
 * AlertRenderer - Renders signal/alert events
 *
 * Handles zCLI signal events (error, warning, success, info) which
 * provide visual feedback to users. Maps to zTheme's zSignal components.
 *
 * Event Mapping:
 * - error   → zSignal-error   (red)
 * - warning → zSignal-warning (orange)
 * - success → zSignal-success (green)
 * - info    → zSignal-info    (blue)
 */
export class AlertRenderer {
  /**
   * Create an AlertRenderer instance
   * @param {Object} logger - Logger instance for debugging
   */
  constructor(logger) {
    this.logger = logger || console;
    this.logger.log('[AlertRenderer] ✅ Initialized');

    // Wrap render method with error boundary
    const originalRender = this.render.bind(this);
    this.render = withErrorBoundary(originalRender, {
      component: 'AlertRenderer',
      logger: this.logger
    });
  }

  /**
   * Render an alert/signal event
   *
   * @param {Object} data - Alert event data
   * @param {string} data.content - Alert message text
   * @param {string} data.eventType - Event type (error, warning, success, info)
   * @param {number} [data.indent=0] - Indentation level (0 = no indent)
   * @param {string} [data.class] - Custom CSS class (optional)
   * @param {string} zone - Target DOM element ID
   * @returns {HTMLElement|null} Created alert element or null if failed
   *
   * @example
   * renderer.render({ content: 'Success!', eventType: 'success' }, 'zVaF');
   * renderer.render({ content: 'Warning!', eventType: 'warning', indent: 1 }, 'zVaF');
   * renderer.render({ content: 'Error!', eventType: 'error' }, 'zVaF');
   */
  render(data, zone) {
    const { content, eventType, indent = 0, class: customClass } = data;

    // Validate required parameters
    if (!content) {
      this.logger.error('[AlertRenderer] ❌ Missing required parameter: content');
      return null;
    }

    if (!eventType) {
      this.logger.error('[AlertRenderer] ❌ Missing required parameter: eventType');
      return null;
    }

    // Get target container
    const container = document.getElementById(zone);
    if (!container) {
      this.logger.error(`[AlertRenderer] ❌ Zone not found: ${zone}`);
      return null;
    }

    // Build CSS classes array
    const classes = ['zSignal'];

    // Add alert color class (uses Layer 2 utility)
    const alertClass = getAlertColorClass(eventType);
    if (alertClass) {
      classes.push(alertClass);
    }

    // Add custom class if provided (from YAML)
    if (customClass) {
      classes.push(customClass);
    }

    // Create alert element (using Layer 2 utility)
    const alert = createElement('div', classes);
    alert.textContent = content; // Use textContent for XSS safety

    // Apply attributes
    const attributes = {
      role: 'alert' // ARIA role for accessibility
    };

    // Apply indent as inline style (zTheme doesn't have indent utilities)
    // Each indent level = 1rem left margin
    if (indent > 0) {
      attributes.style = `margin-left: ${indent}rem;`;
    }

    setAttributes(alert, attributes);

    // Append to container
    container.appendChild(alert);

    // Log success
    this.logger.log(`[AlertRenderer] ✅ Rendered ${eventType} alert (${content.length} chars, indent: ${indent})`);

    return alert;
  }
}

// ─────────────────────────────────────────────────────────────────
// Default Export
// ─────────────────────────────────────────────────────────────────
export default AlertRenderer;

