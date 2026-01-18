/**
 * ═══════════════════════════════════════════════════════════════
 * Interactive Primitives - User Action Elements
 * ═══════════════════════════════════════════════════════════════
 *
 * HTML elements that respond to user interaction.
 * Used for buttons, links, and disclosure widgets.
 *
 * @module rendering/interactive_primitives
 * @layer 0.0 (RAWEST - interactive elements)
 * @pattern Pure Factory Functions
 *
 * Philosophy:
 * - Semantic interaction (buttons for actions, links for navigation)
 * - Type enforcement (button types, link hrefs)
 * - Accessibility (proper roles, keyboard support)
 * - NO styling, NO classes (dress up later)
 *
 * Interactive Types:
 * - <button>: Triggers an action (submit, reset, generic button)
 * - <a>: Navigation/hyperlink (internal, external, anchor)
 * - <details> + <summary>: Collapsible disclosure widget
 *
 * Accessibility:
 * - Buttons have implicit role="button", keyboard accessible
 * - Links have implicit role="link", keyboard accessible
 * - Details/Summary native disclosure, keyboard accessible (Space/Enter)
 *
 * Dependencies:
 * - utils/dom_utils.js (createElement, setAttributes)
 *
 * Exports:
 * - createButton(type, attributes) → HTMLButtonElement
 * - createLink(href, attributes) → HTMLAnchorElement
 * - createDetails(attributes) → HTMLDetailsElement
 * - createSummary(attributes) → HTMLElement
 *
 * Example:
 * ```javascript
 * import { createButton, createLink } from './interactive_primitives.js';
 *
 * const btn = createButton('button', { id: 'action-btn' });
 * btn.textContent = 'Click Me';
 * btn.onclick = () => console.log('Clicked!');
 *
 * const link = createLink('/about', { class: 'nav-link' });
 * link.textContent = 'About';
 * ```
 */

import { createElement, setAttributes } from '../../utils/dom_utils.js';

// ─────────────────────────────────────────────────────────────────
// Button Element
// ─────────────────────────────────────────────────────────────────

/**
 * Create a <button> element
 *
 * Used for triggering actions (submit forms, open modals, toggle state).
 * Default type is "button" to prevent accidental form submissions.
 *
 * Button Types:
 * - "button": Generic clickable button (default, safest)
 * - "submit": Submits a form
 * - "reset": Resets form inputs to defaults
 *
 * Best Practice:
 * - Use <button> for actions (not <a> styled as button)
 * - Always specify type="button" unless submitting a form
 * - Add aria-label for icon-only buttons
 * - Use disabled attribute (not aria-disabled) for true disabling
 *
 * @param {string} [type='button'] - Button type: 'button', 'submit', or 'reset'
 * @param {Object} [attributes={}] - HTML attributes (id, class, disabled, aria-*, etc.)
 * @returns {HTMLButtonElement} The created button element
 *
 * @example
 * // Generic action button (safest default)
 * const actionBtn = createButton('button', { id: 'save-btn' });
 * actionBtn.textContent = 'Save';
 *
 * // Submit button for forms
 * const submitBtn = createButton('submit', { form: 'login-form' });
 * submitBtn.textContent = 'Log In';
 *
 * // Reset button
 * const resetBtn = createButton('reset');
 * resetBtn.textContent = 'Clear';
 *
 * // Icon-only button (needs aria-label)
 * const iconBtn = createButton('button', { 'aria-label': 'Close dialog' });
 *
 * // Disabled button
 * const disabledBtn = createButton('button', { disabled: true });
 */
export function createButton(type = 'button', attributes = {}) {
  const button = createElement('button');

  // Validate button type (default to 'button' for safety)
  const validTypes = ['button', 'submit', 'reset'];
  const validType = validTypes.includes(type) ? type : 'button';

  if (type && !validTypes.includes(type)) {
    console.warn(`[interactive_primitives] createButton: Invalid type "${type}", defaulting to "button"`);
  }

  // Extract class attribute separately (needs special handling)
  const { class: classString, ...otherAttributes } = attributes;

  // Set type first, then other attributes
  setAttributes(button, { type: validType, ...otherAttributes });

  // Handle class separately using classList.add() to avoid overwriting
  if (classString) {
    const classes = classString.split(' ').filter(c => c.trim());
    if (classes.length > 0) {
      button.classList.add(...classes);
    }
  }

  return button;
}

// ─────────────────────────────────────────────────────────────────
// Link/Anchor Element
// ─────────────────────────────────────────────────────────────────

/**
 * Create an <a> (anchor/link) element
 *
 * Used for navigation and hyperlinks (pages, sections, external sites).
 * IMPORTANT: href is REQUIRED for semantic correctness and accessibility.
 *
 * Link Types:
 * - Internal: "/about", "/products/123" (same-origin navigation)
 * - External: "https://example.com" (cross-origin navigation)
 * - Anchor: "#section-id" (same-page jump)
 * - JavaScript: "javascript:void(0)" (NOT RECOMMENDED - use button instead)
 * - Download: href + download attribute
 *
 * Best Practice:
 * - Use <a> for navigation (not <button> styled as link)
 * - Always provide href (without href, it's not keyboard accessible)
 * - Add target="_blank" + rel="noopener noreferrer" for external links
 * - Use download attribute for file downloads
 * - For actions (not navigation), use <button> instead
 *
 * @param {string} href - Link destination (URL, #anchor, or relative path)
 * @param {Object} [attributes={}] - HTML attributes (target, rel, download, aria-*, etc.)
 * @returns {HTMLAnchorElement} The created link element
 *
 * @example
 * // Internal navigation
 * const aboutLink = createLink('/about', { class: 'nav-link' });
 * aboutLink.textContent = 'About Us';
 *
 * // External link (secure)
 * const externalLink = createLink('https://example.com', {
 *   target: '_blank',
 *   rel: 'noopener noreferrer'
 * });
 * externalLink.textContent = 'Visit Example';
 *
 * // Anchor link (same-page jump)
 * const anchorLink = createLink('#features', { 'aria-label': 'Jump to features' });
 * anchorLink.textContent = 'See Features';
 *
 * // Download link
 * const downloadLink = createLink('/files/report.pdf', { download: 'report.pdf' });
 * downloadLink.textContent = 'Download Report';
 *
 * // Email link
 * const emailLink = createLink('mailto:hello@example.com');
 * emailLink.textContent = 'Contact Us';
 */
export function createLink(href, attributes = {}) {
  // Validate href (required for semantic link)
  if (!href) {
    console.warn('[interactive_primitives] createLink: href is required for semantic links, defaulting to "#"');
    href = '#';
  }

  const link = createElement('a');

  // Set href first, then merge with user attributes
  setAttributes(link, { href, ...attributes });

  return link;
}

// ─────────────────────────────────────────────────────────────────
// Disclosure Widget (Details + Summary)
// ─────────────────────────────────────────────────────────────────

/**
 * Create a <details> element
 *
 * Native collapsible disclosure widget (accordion, FAQ, expandable section).
 * Works without JavaScript, fully keyboard accessible (Space/Enter to toggle).
 *
 * Structure:
 * - <details> is the container
 * - First child must be <summary> (the clickable toggle)
 * - Remaining children are the revealed content
 *
 * State:
 * - Closed by default (add `open` attribute to start expanded)
 * - Toggle event: 'toggle' fires on state change
 *
 * Best Practice:
 * - First child MUST be <summary>
 * - Use for progressive disclosure (FAQs, advanced options)
 * - Listen to 'toggle' event for custom behavior
 * - Can be styled with [open] selector
 *
 * @param {Object} [attributes={}] - HTML attributes (id, class, open, data-*, etc.)
 * @returns {HTMLDetailsElement} The created details element
 *
 * @example
 * // Collapsible FAQ item (closed by default)
 * const faq = createDetails({ id: 'faq-1' });
 * const question = createSummary();
 * question.textContent = 'What is zCLI?';
 * const answer = document.createElement('p');
 * answer.textContent = 'zCLI is a command-line interface framework.';
 * faq.appendChild(question);
 * faq.appendChild(answer);
 *
 * // Expandable section (open by default)
 * const section = createDetails({ open: true, class: 'expandable' });
 *
 * // With toggle event listener
 * const details = createDetails({ 'data-section': 'advanced' });
 * details.addEventListener('toggle', (e) => {
 *   console.log('Expanded:', e.target.open);
 * });
 */
export function createDetails(attributes = {}) {
  const details = createElement('details');

  if (Object.keys(attributes).length > 0) {
    setAttributes(details, attributes);
  }

  return details;
}

/**
 * Create a <summary> element
 *
 * The clickable heading/toggle for a <details> element.
 * MUST be the first child of <details>.
 * Acts as a button (keyboard accessible via Space/Enter).
 *
 * Behavior:
 * - Clicking toggles the <details> parent
 * - Has implicit disclosure triangle/marker (can be styled)
 * - Can contain phrasing content (text, icons, etc.)
 *
 * Best Practice:
 * - Must be first child of <details>
 * - Keep concise (it's a heading/label)
 * - Can style marker with ::marker pseudo-element
 *
 * @param {Object} [attributes={}] - HTML attributes (id, class, data-*, etc.)
 * @returns {HTMLElement} The created summary element
 *
 * @example
 * // Basic summary
 * const summary = createSummary();
 * summary.textContent = 'Click to expand';
 *
 * // Summary with icon
 * const iconSummary = createSummary({ class: 'summary-with-icon' });
 * iconSummary.innerHTML = '<i class="bi bi-chevron-down"></i> More Options';
 *
 * // Summary with data attribute
 * const dataSummary = createSummary({ 'data-section-id': '5' });
 */
export function createSummary(attributes = {}) {
  const summary = createElement('summary');

  if (Object.keys(attributes).length > 0) {
    setAttributes(summary, attributes);
  }

  return summary;
}

// ─────────────────────────────────────────────────────────────────
// Default Export (for convenience)
// ─────────────────────────────────────────────────────────────────
export default {
  createButton,
  createLink,
  createDetails,
  createSummary
};

