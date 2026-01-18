/**
 * ═══════════════════════════════════════════════════════════════
 * DOM Utilities - Pure DOM Manipulation Functions
 * ═══════════════════════════════════════════════════════════════
 *
 * Pure functions for DOM manipulation. Zero dependencies, zero state,
 * zero side effects (except the DOM operations themselves).
 *
 * @module utils/dom_utils
 * @layer 2
 * @pattern Pure Functions
 *
 * Dependencies:
 * - Layer 0: Browser DOM APIs only
 *
 * Exports:
 * - createElement: Create element with classes and attributes
 * - safeQuery: Safe querySelector (returns null instead of throwing)
 * - safeQueryAll: Safe querySelectorAll (returns array instead of NodeList)
 * - clearElement: Clear element content safely
 * - appendChildren: Append multiple children at once
 * - removeElement: Remove element safely (checks parent exists)
 * - replaceElement: Replace element with another
 * - setAttributes: Set multiple attributes at once
 * - toggleClasses: Toggle multiple classes at once
 * - createTextNode: Create text node (safe alternative to textContent)
 *
 * Example:
 * ```javascript
 * import { createElement, appendChildren } from './dom_utils.js';
 *
 * const button = createElement('button', ['zBtn', 'zBtnPrimary'], { type: 'button' });
 * const icon = createElement('i', ['bi', 'bi-check']);
 * appendChildren(button, [icon, createTextNode('Submit')]);
 * ```
 */

// ─────────────────────────────────────────────────────────────────
// DOM Creation & Manipulation
// ─────────────────────────────────────────────────────────────────

/**
 * Create an HTML element with classes and attributes
 *
 * @param {string} tag - HTML tag name (e.g., 'div', 'button', 'input')
 * @param {string[]} [classNames=[]] - Array of CSS class names to add
 * @param {Object} [attributes={}] - HTML attributes to set {id, type, disabled, etc}
 * @returns {HTMLElement} Created element
 *
 * @example
 * const button = createElement('button', ['zBtn', 'zBtnPrimary'], {
 *   type: 'button',
 *   id: 'submit-btn',
 *   disabled: false
 * });
 *
 * @throws {Error} If tag is empty or invalid
 */
export function createElement(tag, classNames = [], attributes = {}) {
  if (!tag || typeof tag !== 'string') {
    throw new Error('[createElement] tag must be a non-empty string');
  }

  const element = document.createElement(tag);

  // Add classes
  if (classNames && classNames.length > 0) {
    element.classList.add(...classNames);
  }

  // Set attributes
  if (attributes && typeof attributes === 'object') {
    setAttributes(element, attributes);
  }

  return element;
}

/**
 * Create a text node (safe alternative to textContent)
 *
 * @param {string} text - Text content
 * @returns {Text} Text node
 *
 * @example
 * const textNode = createTextNode('Hello, World!');
 * element.appendChild(textNode);
 */
export function createTextNode(text) {
  return document.createTextNode(text || '');
}

// ─────────────────────────────────────────────────────────────────
// DOM Querying
// ─────────────────────────────────────────────────────────────────

/**
 * Safe querySelector (returns null instead of throwing)
 *
 * @param {string} selector - CSS selector
 * @param {Element|Document} [context=document] - Search context
 * @returns {Element|null} Found element or null
 *
 * @example
 * const element = safeQuery('#my-element');
 * if (element) {
 *   element.classList.add('active');
 * }
 */
export function safeQuery(selector, context = document) {
  try {
    return context.querySelector(selector);
  } catch (error) {
    this.logger.warn(`[safeQuery] Invalid selector: ${selector}`, error);
    return null;
  }
}

/**
 * Safe querySelectorAll (returns array instead of NodeList)
 *
 * @param {string} selector - CSS selector
 * @param {Element|Document} [context=document] - Search context
 * @returns {Element[]} Array of found elements (empty if none found)
 *
 * @example
 * const buttons = safeQueryAll('.zBtn');
 * buttons.forEach(btn => btn.disabled = true);
 */
export function safeQueryAll(selector, context = document) {
  try {
    return Array.from(context.querySelectorAll(selector));
  } catch (error) {
    this.logger.warn(`[safeQueryAll] Invalid selector: ${selector}`, error);
    return [];
  }
}

// ─────────────────────────────────────────────────────────────────
// DOM Modification
// ─────────────────────────────────────────────────────────────────

/**
 * Clear element content safely
 *
 * @param {Element} element - Element to clear
 *
 * @example
 * const container = document.getElementById('content');
 * clearElement(container);
 */
export function clearElement(element) {
  if (!element) {
    return;
  }

  // Remove all children
  while (element.firstChild) {
    element.removeChild(element.firstChild);
  }
}

/**
 * Append multiple children to a parent element at once
 *
 * @param {Element} parent - Parent element
 * @param {(Element|Text)[]} [children=[]] - Array of child elements or text nodes
 *
 * @example
 * const container = createElement('div');
 * const header = createElement('h1');
 * const paragraph = createElement('p');
 * appendChildren(container, [header, paragraph]);
 */
export function appendChildren(parent, children = []) {
  if (!parent || !Array.isArray(children)) {
    return;
  }

  children.forEach(child => {
    if (child) {
      parent.appendChild(child);
    }
  });
}

/**
 * Remove element from DOM safely (checks if parent exists)
 *
 * @param {Element} element - Element to remove
 *
 * @example
 * const button = document.getElementById('old-button');
 * removeElement(button);
 */
export function removeElement(element) {
  if (element && element.parentNode) {
    element.parentNode.removeChild(element);
  }
}

/**
 * Replace element with another element
 *
 * @param {Element} oldElement - Element to replace
 * @param {Element} newElement - Replacement element
 *
 * @example
 * const oldButton = document.getElementById('old-btn');
 * const newButton = createElement('button', ['zBtn', 'zBtnSuccess']);
 * replaceElement(oldButton, newButton);
 */
export function replaceElement(oldElement, newElement) {
  if (!oldElement || !newElement || !oldElement.parentNode) {
    return;
  }

  oldElement.parentNode.replaceChild(newElement, oldElement);
}

// ─────────────────────────────────────────────────────────────────
// Attributes & Classes
// ─────────────────────────────────────────────────────────────────

/**
 * Set multiple attributes on an element at once
 *
 * @param {Element} element - Target element
 * @param {Object} attributes - Attributes to set {name: value}
 *
 * @example
 * const input = createElement('input');
 * setAttributes(input, {
 *   type: 'text',
 *   id: 'username',
 *   placeholder: 'Enter username',
 *   required: true
 * });
 */
export function setAttributes(element, attributes = {}) {
  if (!element || !attributes) {
    return;
  }

  Object.entries(attributes).forEach(([key, value]) => {
    if (value === null || value === undefined) {
      element.removeAttribute(key);
    } else if (typeof value === 'boolean') {
      // Handle boolean attributes (disabled, required, etc)
      if (value) {
        element.setAttribute(key, '');
      } else {
        element.removeAttribute(key);
      }
    } else {
      element.setAttribute(key, value);
    }
  });
}

/**
 * Toggle multiple classes on an element at once
 *
 * @param {Element} element - Target element
 * @param {string[]} classes - Array of class names to toggle
 * @param {boolean|null} [force=null] - Force add (true) or remove (false), or toggle (null)
 *
 * @example
 * // Toggle classes
 * toggleClasses(button, ['active', 'highlighted']);
 *
 * // Force add classes
 * toggleClasses(button, ['disabled', 'inactive'], true);
 *
 * // Force remove classes
 * toggleClasses(button, ['active', 'highlighted'], false);
 */
export function toggleClasses(element, classes = [], force = null) {
  if (!element || !Array.isArray(classes)) {
    return;
  }

  classes.forEach(className => {
    if (className) {
      if (force === null) {
        element.classList.toggle(className);
      } else {
        element.classList.toggle(className, force);
      }
    }
  });
}

// ─────────────────────────────────────────────────────────────────
// Container Helpers (Layer 2 - Pure Utilities)
// ─────────────────────────────────────────────────────────────────

/**
 * Create a div element with optional attributes
 *
 * Utility function to create a div with attributes in one call.
 * This is a Layer 2 (Utilities) function - pure, no business logic.
 *
 * @param {Object} [attributes={}] - Attributes to set on the div
 * @returns {HTMLDivElement} The created div element
 *
 * @example
 * // Simple div
 * const container = createDiv();
 *
 * // Div with classes
 * const card = createDiv({ class: 'zCard zCard-primary' });
 *
 * // Div with multiple attributes
 * const item = createDiv({ 'data-item-id': '123', 'data-type': 'product' });
 *
 * // Div with ARIA attributes for accessibility
 * const alert = createDiv({ role: 'alert', 'aria-live': 'polite' });
 */
export function createDiv(attributes = {}) {
  const div = createElement('div');

  if (Object.keys(attributes).length > 0) {
    setAttributes(div, attributes);
  }

  return div;
}
