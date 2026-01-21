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
   * @param {Object} eventData - Event data with content, color, indent, zId, semantic, etc.
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
    
    // Check semantic parameter to determine container type
    const semantic = eventData.semantic;
    let element;
    
    if (semantic === 'div') {
      // Use <div> instead of <p> (for grid demos, badges, etc.)
      element = document.createElement('div');
      if (attrs.class) element.className = attrs.class;
      if (attrs.id) element.id = attrs.id;
      element.textContent = this._decodeUnicodeEscapes(eventData.content || '');
    } else if (semantic === 'span') {
      // Use <span> for inline content
      element = document.createElement('span');
      if (attrs.class) element.className = attrs.class;
      if (attrs.id) element.id = attrs.id;
      element.textContent = this._decodeUnicodeEscapes(eventData.content || '');
    } else {
      // Default: <p> with optional semantic wrapper
      const p = createParagraph(attrs);
      const content = this._decodeUnicodeEscapes(eventData.content || '');
      
      if (semantic && semantic !== 'p') {
        // Wrap content in semantic element (<code>, <strong>, etc.)
        const wrapper = document.createElement(semantic);
        wrapper.textContent = content;
        p.appendChild(wrapper);
      } else {
        p.textContent = content;
      }
      element = p;
    }
    
    return element;
  }

  /**
   * Render header element
   * @param {Object} eventData - Event data with label, indent (level), zId, etc.
   * @returns {HTMLElement}
   */
  renderHeader(eventData) {
    // Backend sends 'indent' with header level (zH1=1, zH2=2, etc.)
    const level = eventData.indent || eventData.level || 1;
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
    // Decode Unicode escapes from ASCII-safe storage
    const content = eventData.label || eventData.content || '';
    h.textContent = this._decodeUnicodeEscapes(content);
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

    // Custom classes from YAML (_zClass parameter - ignored by terminal)
    if (eventData._zClass) {
      classes.push(eventData._zClass);
    }

    return classes.length > 0 ? classes.join(' ') : '';
  }

  /**
   * Decode Unicode escape sequences to actual characters
   * Supports: \uXXXX (standard) and \UXXXXXX (extended) formats
   * @param {string} text - Text containing Unicode escapes
   * @returns {string} - Decoded text
   * @private
   */
  _decodeUnicodeEscapes(text) {
    if (!text || typeof text !== 'string') return text;
    
    // Replace \uXXXX format (standard 4-digit Unicode escape)
    text = text.replace(/\\u([0-9A-Fa-f]{4})/g, (match, hexCode) => {
      return String.fromCodePoint(parseInt(hexCode, 16));
    });
    
    // Replace \UXXXXXXXX format (extended 4-8 digit for supplementary characters & emojis)
    text = text.replace(/\\U([0-9A-Fa-f]{4,8})/g, (match, hexCode) => {
      return String.fromCodePoint(parseInt(hexCode, 16));
    });
    
    return text;
  }
}

export default TypographyRenderer;

