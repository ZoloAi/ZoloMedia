/**
 * TypographyRenderer - Renders text, headers, and dividers
 *
 * Uses typography primitives for DOM creation
 */

import { createHeading, createParagraph } from './primitives/typography_primitives.js';

export class TypographyRenderer {
  constructor(logger) {
    this.logger = logger;
  }

  /**
   * Render text element
   * @param {Object} eventData - Event data with content, color, indent, zId, etc.
   * @returns {HTMLElement}
   */
  renderText(eventData) {
    const classes = this._buildTextClasses(eventData);
    const attrs = {};
    if (classes) {
      attrs.class = classes;
    }
    // Support zId (universal), _zId (from zUI files), and _id (legacy)
    if (eventData.zId || eventData._zId || eventData._id) {
      attrs.id = eventData.zId || eventData._zId || eventData._id;
    }
    const p = createParagraph(attrs);
    p.textContent = eventData.content || '';
    return p;
  }

  /**
   * Render header element
   * @param {Object} eventData - Event data with label, level, zId, etc.
   * @returns {HTMLElement}
   */
  renderHeader(eventData) {
    const level = eventData.level || 1;
    const classes = this._buildTextClasses(eventData);
    const attrs = {};
    if (classes) {
      attrs.class = classes;
    }
    // Support zId (universal), _zId (from zUI files), and _id (legacy)
    if (eventData.zId || eventData._zId || eventData._id) {
      attrs.id = eventData.zId || eventData._zId || eventData._id;
    }
    const h = createHeading(level, attrs);
    h.textContent = eventData.label || eventData.content || '';
    return h;
  }

  /**
   * Render divider element
   * @param {Object} eventData - Event data with color, zId, etc.
   * @returns {HTMLElement}
   */
  renderDivider(eventData) {
    const hr = document.createElement('hr');
    const classes = ['zDivider'];
    if (eventData.color) {
      classes.push(`zBorder-${eventData.color}`);
    }
    hr.className = classes.join(' ');
    // Support zId (universal), _zId (from zUI files), and _id (legacy)
    if (eventData.zId || eventData._zId || eventData._id) {
      hr.setAttribute('id', eventData.zId || eventData._zId || eventData._id);
    }
    return hr;
  }

  /**
   * Build text classes from event data
   * @private
   */
  _buildTextClasses(eventData) {
    const classes = [];

    // Color: normalize to lowercase for zTheme consistency
    if (eventData.color) {
      const color = eventData.color.toLowerCase();
      classes.push(`zText-${color}`);
    }

    // Indent: use margin-start (zms) for text indentation
    if (eventData.indent) {
      classes.push(`zms-${eventData.indent}`);
    }

    // Custom classes from YAML (_zClass parameter - ignored by terminal)
    if (eventData._zClass) {
      classes.push(eventData._zClass);
    }

    return classes.length > 0 ? classes.join(' ') : '';
  }
}

export default TypographyRenderer;

