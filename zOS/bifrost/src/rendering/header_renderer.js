/**
 * ═══════════════════════════════════════════════════════════════
 * Header Renderer - Semantic Headers (h1-h6)
 * ═══════════════════════════════════════════════════════════════
 *
 * Renders header events from zCLI backend. Converts indent levels
 * to semantic HTML header tags (h1-h6) with optional colors.
 *
 * @module rendering/header_renderer
 * @layer 3
 * @pattern Strategy (single event type)
 *
 * Philosophy:
 * - "Terminal first" - headers structure all zCLI output
 * - Pure rendering (no WebSocket, no state, no side effects)
 * - Semantic HTML (indent → h1-h6)
 * - Uses Layer 2 utilities exclusively (no inline logic)
 *
 * Dependencies:
 * - Layer 2: dom_utils.js, ztheme_utils.js
 *
 * Exports:
 * - HeaderRenderer: Class for rendering header events
 *
 * Example:
 * ```javascript
 * import { HeaderRenderer } from './header_renderer.js';
 *
 * const renderer = new HeaderRenderer(logger);
 * renderer.render({
 *   label: 'Welcome to zCLI',
 *   color: 'primary',
 *   indent: 1  // h1
 * }, 'zVaF');
 * ```
 */

// ─────────────────────────────────────────────────────────────────
// Imports
// ─────────────────────────────────────────────────────────────────
import { createElement } from '../utils/dom_utils.js';
import { getTextColorClass, indentToHeaderTag } from '../utils/ztheme_utils.js';
import { withErrorBoundary } from '../utils/error_boundary.js';

// ─────────────────────────────────────────────────────────────────
// Header Renderer Class
// ─────────────────────────────────────────────────────────────────

/**
 * HeaderRenderer - Renders semantic header events
 *
 * Handles the 'header' zDisplay event. Converts indent levels
 * to semantic HTML header tags (h1-h6) for proper document structure.
 *
 * Indent Mapping:
 * - indent 0: Reserved for special cases (flush/hero layouts) - NOT a header
 * - indent 1 → h1 (main title)
 * - indent 2 → h2 (section)
 * - indent 3 → h3 (subsection)
 * - indent 4 → h4
 * - indent 5 → h5
 * - indent 6 → h6
 * - indent 7+ → h6 (capped at h6)
 */
export class HeaderRenderer {
  /**
   * Create a HeaderRenderer instance
   * @param {Object} logger - Logger instance for debugging
   */
  constructor(logger) {
    this.logger = logger || console;
    this.logger.log('[HeaderRenderer] ✅ Initialized');

    // Wrap render method with error boundary
    const originalRender = this.render.bind(this);
    this.render = withErrorBoundary(originalRender, {
      component: 'HeaderRenderer',
      logger: this.logger
    });
  }

  /**
   * Render a header event
   *
   * @param {Object} data - Header event data
   * @param {string} data.label - Header text (backend sends 'label' not 'content')
   * @param {string} [data.color] - Header color (primary, secondary, info, success, warning, error)
   * @param {number} [data.indent=1] - Indent level (1-6, where 1=h1, 6=h6)
   *                                    Note: indent 0 is reserved for special cases
   * @param {string} [data.class] - Custom CSS class (optional)
   * @param {string} zone - Target DOM element ID
   * @returns {HTMLElement|null} Created header element or null if failed
   *
   * @example
   * renderer.render({ label: 'Main Title', indent: 1 }, 'zVaF');  // h1
   * renderer.render({ label: 'Section', indent: 2, color: 'primary' }, 'zVaF');  // h2
   * renderer.render({ label: 'Subsection', indent: 3 }, 'zVaF');  // h3
   */
  render(data, zone) {
    // Backend sends 'label' for headers (not 'content')
    const { label, color, indent = 1, class: customClass } = data;

    // Validate required parameters
    if (!label) {
      this.logger.error('[HeaderRenderer] ❌ Missing required parameter: label');
      return null;
    }

    // Handle indent 0 as special case (reserved for flush/hero layouts)
    if (indent === 0) {
      this.logger.warn('[HeaderRenderer] ⚠️ indent=0 is reserved for special cases, treating as indent=1 (h1)');
      // Could also skip rendering or return null, but treating as h1 is safer
    }

    // Get target container
    const container = document.getElementById(zone);
    if (!container) {
      this.logger.error(`[HeaderRenderer] ❌ Zone not found: ${zone}`);
      return null;
    }

    // Convert indent to header tag (h1-h6) using Layer 2 utility
    // This automatically clamps indent between 1-6
    const headerTag = indentToHeaderTag(indent);

    // Build CSS classes array
    const classes = [];

    // Add custom class if provided (from YAML)
    if (customClass) {
      classes.push(customClass);
    }

    // Add color class if provided (uses Layer 2 utility)
    if (color) {
      const colorClass = getTextColorClass(color);
      if (colorClass) {
        classes.push(colorClass);
      }
    }

    // Create header element (using Layer 2 utility)
    const header = createElement(headerTag, classes);
    header.textContent = label; // Use textContent for XSS safety

    // Append to container
    container.appendChild(header);

    // Log success
    this.logger.log(`[HeaderRenderer] ✅ Rendered ${headerTag} (${label.length} chars, indent: ${indent})`);

    return header;
  }
}

// ─────────────────────────────────────────────────────────────────
// Default Export
// ─────────────────────────────────────────────────────────────────
export default HeaderRenderer;

