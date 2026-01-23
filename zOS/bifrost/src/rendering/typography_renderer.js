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
   * Convert newlines to <br> tags for Bifrost GUI
   * Handles BOTH literal \n strings (from YAML without quotes) AND actual newlines (from YAML with quotes)
   * @param {string} text - Text with potential newlines
   * @returns {string} HTML-safe text with <br> tags
   * @private
   */
  _convertNewlinesToBr(text) {
    // STEP 1: Process zText semantic distinction
    // \x1E (YAML multilines) → space (for readability)
    // \n (explicit escapes) → <br> (line break)
    const processedText = text.replace(/\x1E/g, ' ');
    
    // STEP 2: Escape HTML entities for XSS safety
    const escaped = processedText
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
    
    // STEP 3: Convert explicit \n to <br> tags
    return escaped.replace(/\n/g, '<br>');
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
      const content = this._decodeUnicodeEscapes(eventData.content || '');
      element.innerHTML = this._convertNewlinesToBr(content);
    } else if (semantic === 'span') {
      // Use <span> for inline content
      element = document.createElement('span');
      if (attrs.class) element.className = attrs.class;
      if (attrs.id) element.id = attrs.id;
      const content = this._decodeUnicodeEscapes(eventData.content || '');
      element.innerHTML = this._convertNewlinesToBr(content);
    } else {
      // Default: <p> with optional semantic wrapper
      const p = createParagraph(attrs);
      const content = this._decodeUnicodeEscapes(eventData.content || '');
      
      if (semantic && semantic !== 'p') {
        // Wrap content in semantic element (<code>, <strong>, etc.)
        const wrapper = document.createElement(semantic);
        wrapper.innerHTML = this._convertNewlinesToBr(content);
        p.appendChild(wrapper);
      } else {
        p.innerHTML = this._convertNewlinesToBr(content);
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
    // Decode Unicode escapes and convert newlines to <br> for Bifrost
    const content = eventData.label || eventData.content || '';
    const decoded = this._decodeUnicodeEscapes(content);
    h.innerHTML = this._convertNewlinesToBr(decoded);
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
   * Supports: \uXXXX (standard) and \UXXXXXXXX (extended) formats
   * 
   * Note: Basic escape sequences (\n, \t, etc.) are handled by JSON.parse()
   * automatically when receiving data from backend. We only need to decode
   * custom Unicode formats that JSON doesn't handle.
   * 
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
    
    // Replace basic escape sequences (literal strings like \\n, \\t, etc.)
    // These come from JSON where Python sends "\n" which becomes "\\n" in JSON
    text = text
      .replace(/\\n/g, '\n')   // Newline
      .replace(/\\t/g, '\t')   // Tab
      .replace(/\\r/g, '\r')   // Carriage return
      .replace(/\\'/g, "'")    // Single quote
      .replace(/\\"/g, '"')    // Double quote
      .replace(/\\\\/g, '\\'); // Backslash (must be last!)
    
    return text;
  }
}

export default TypographyRenderer;

