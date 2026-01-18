/**
 * ═══════════════════════════════════════════════════════════════
 * Lists Primitives - Enumerated Content Elements
 * ═══════════════════════════════════════════════════════════════
 *
 * HTML list elements for ordered, unordered, and description lists.
 * Used for grouping related items with semantic meaning.
 *
 * @module rendering/lists_primitives
 * @layer 0.0 (RAWEST - list structure)
 * @pattern Pure Factory Functions
 *
 * Philosophy:
 * - Semantic enumeration (ordered vs unordered)
 * - Description lists for key-value pairs
 * - NO styling, NO classes (dress up later)
 * - Parent-child relationship (list → items)
 *
 * List Types:
 * - <ul> + <li>: Unordered list (bullets, no sequence importance)
 * - <ol> + <li>: Ordered list (numbers, sequence matters)
 * - <dl> + <dt> + <dd>: Description list (term-definition pairs)
 *
 * zReboot Defaults:
 * - Lists: margin-top: 0, margin-bottom: 1rem, padding-left: 2rem
 * - Nested lists: margin-bottom: 0
 *
 * Dependencies:
 * - utils/dom_utils.js (createElement, setAttributes)
 *
 * Exports:
 * - createList(ordered, attributes) → HTMLUListElement | HTMLOListElement
 * - createListItem(attributes) → HTMLLIElement
 * - createDescriptionList(attributes) → HTMLDListElement
 * - createDescriptionTerm(attributes) → HTMLElement (dt)
 * - createDescriptionDetails(attributes) → HTMLElement (dd)
 *
 * Example:
 * ```javascript
 * import { createList, createListItem } from './lists_primitives.js';
 *
 * // Unordered list
 * const ul = createList(false, { id: 'features' });
 * const li1 = createListItem();
 * li1.textContent = 'Feature 1';
 * ul.appendChild(li1);
 *
 * // Ordered list
 * const ol = createList(true, { id: 'steps' });
 * const step1 = createListItem();
 * step1.textContent = 'Step 1';
 * ol.appendChild(step1);
 * ```
 */

import { createElement, setAttributes } from '../../utils/dom_utils.js';

// ─────────────────────────────────────────────────────────────────
// Ordered & Unordered Lists
// ─────────────────────────────────────────────────────────────────

/**
 * Create a list element (<ul> or <ol>)
 *
 * Used for grouping related items in a list structure.
 * - Unordered (<ul>): Items where order doesn't matter (features, tags, bullets)
 * - Ordered (<ol>): Items where sequence is important (steps, rankings, instructions)
 *
 * zReboot Defaults:
 * - margin-top: 0
 * - margin-bottom: 1rem
 * - padding-left: 2rem (for bullets/numbers)
 *
 * @param {boolean} [ordered=false] - If true, creates <ol>; otherwise <ul>
 * @param {Object} [attributes={}] - HTML attributes (id, class, start, type, etc.)
 * @returns {HTMLUListElement|HTMLOListElement} The created list element
 *
 * @example
 * // Unordered list (bullets)
 * const features = createList(false, { id: 'features-list' });
 *
 * // Ordered list (numbers)
 * const steps = createList(true, { id: 'instructions' });
 *
 * // Ordered list starting at 5
 * const continuation = createList(true, { start: 5 });
 *
 * // Roman numerals (type="I", "i", "A", "a")
 * const romanList = createList(true, { type: 'I' });
 */
export function createList(ordered = false, attributes = {}) {
  const tag = ordered ? 'ol' : 'ul';
  const list = createElement(tag);

  if (Object.keys(attributes).length > 0) {
    setAttributes(list, attributes);
  }

  return list;
}

/**
 * Create a <li> (list item) element
 *
 * Used as children of <ul> or <ol> lists.
 * Represents a single item in the list.
 *
 * Best Practice:
 * - Must be a direct child of <ul>, <ol>, or <menu>
 * - Can contain flow content (text, images, nested lists, etc.)
 *
 * @param {Object} [attributes={}] - HTML attributes (id, class, value, data-*, etc.)
 * @returns {HTMLLIElement} The created list item element
 *
 * @example
 * // Basic list item
 * const item = createListItem();
 * item.textContent = 'First item';
 *
 * // List item with custom value (for <ol>)
 * const customItem = createListItem({ value: 10 });
 *
 * // List item with data attribute
 * const dataItem = createListItem({ 'data-item-id': '123' });
 */
export function createListItem(attributes = {}) {
  const li = createElement('li');

  if (Object.keys(attributes).length > 0) {
    setAttributes(li, attributes);
  }

  return li;
}

// ─────────────────────────────────────────────────────────────────
// Description Lists (Key-Value Pairs)
// ─────────────────────────────────────────────────────────────────

/**
 * Create a <dl> (description list) element
 *
 * Used for name-value groups (glossaries, metadata, key-value pairs).
 * Contains <dt> (term) and <dd> (description/definition) pairs.
 *
 * Common Uses:
 * - Glossaries (term → definition)
 * - Metadata (key → value)
 * - FAQ (question → answer)
 * - Product specs (feature → value)
 *
 * Structure:
 * - One or more <dt> followed by one or more <dd>
 * - Can have multiple <dt> for one <dd> (synonyms)
 * - Can have multiple <dd> for one <dt> (multiple definitions)
 *
 * @param {Object} [attributes={}] - HTML attributes (id, class, data-*, etc.)
 * @returns {HTMLDListElement} The created description list element
 *
 * @example
 * // Glossary
 * const glossary = createDescriptionList({ id: 'glossary' });
 *
 * // Product specifications
 * const specs = createDescriptionList({ class: 'product-specs' });
 *
 * // FAQ
 * const faq = createDescriptionList({ 'aria-label': 'Frequently Asked Questions' });
 */
export function createDescriptionList(attributes = {}) {
  const dl = createElement('dl');

  if (Object.keys(attributes).length > 0) {
    setAttributes(dl, attributes);
  }

  return dl;
}

/**
 * Create a <dt> (description term) element
 *
 * Represents the term/name in a description list.
 * Must be a child of <dl> and paired with <dd>.
 *
 * @param {Object} [attributes={}] - HTML attributes (id, class, data-*, etc.)
 * @returns {HTMLElement} The created description term element
 *
 * @example
 * // Glossary term
 * const term = createDescriptionTerm();
 * term.textContent = 'HTML';
 *
 * // Product feature name
 * const feature = createDescriptionTerm({ class: 'spec-name' });
 * feature.textContent = 'Weight';
 *
 * // FAQ question
 * const question = createDescriptionTerm({ id: 'faq-1' });
 * question.textContent = 'What is zCLI?';
 */
export function createDescriptionTerm(attributes = {}) {
  const dt = createElement('dt');

  if (Object.keys(attributes).length > 0) {
    setAttributes(dt, attributes);
  }

  return dt;
}

/**
 * Create a <dd> (description details) element
 *
 * Represents the description/value in a description list.
 * Must be a child of <dl> and paired with <dt>.
 *
 * zReboot Defaults:
 * - margin-left: 0 (reset browser default indent)
 *
 * @param {Object} [attributes={}] - HTML attributes (id, class, data-*, etc.)
 * @returns {HTMLElement} The created description details element
 *
 * @example
 * // Glossary definition
 * const definition = createDescriptionDetails();
 * definition.textContent = 'HyperText Markup Language';
 *
 * // Product feature value
 * const value = createDescriptionDetails({ class: 'spec-value' });
 * value.textContent = '1.2 kg';
 *
 * // FAQ answer
 * const answer = createDescriptionDetails({ 'data-answer-id': '1' });
 * answer.textContent = 'zCLI is a command-line interface framework.';
 */
export function createDescriptionDetails(attributes = {}) {
  const dd = createElement('dd');

  if (Object.keys(attributes).length > 0) {
    setAttributes(dd, attributes);
  }

  return dd;
}

// ─────────────────────────────────────────────────────────────────
// Default Export (for convenience)
// ─────────────────────────────────────────────────────────────────
export default {
  createList,
  createListItem,
  createDescriptionList,
  createDescriptionTerm,
  createDescriptionDetails
};

