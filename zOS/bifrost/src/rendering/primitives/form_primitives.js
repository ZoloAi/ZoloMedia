/**
 * ═══════════════════════════════════════════════════════════════
 * Form Primitives - Data Input Elements
 * ═══════════════════════════════════════════════════════════════
 *
 * HTML form elements for user data input and submission.
 * Covers all 18 input types plus form structure elements.
 *
 * @module rendering/form_primitives
 * @layer 0.0 (RAWEST - form elements)
 * @pattern Pure Factory Functions
 *
 * Philosophy:
 * - Semantic data input (type enforcement)
 * - Accessibility (labels, fieldsets, ARIA)
 * - Native validation (email, url, number, etc.)
 * - NO styling, NO classes (dress up later)
 *
 * Input Types Supported (18 total):
 * - Text-based: text, email, password, search, tel, url
 * - Numeric: number, range
 * - Date/Time: date, datetime-local, month, week, time
 * - Selection: checkbox, radio
 * - File: file
 * - Special: color, hidden
 *
 * Form Structure:
 * - <form>: Container with submit handling
 * - <fieldset> + <legend>: Group related inputs
 * - <label>: Associate text with input (accessibility)
 * - <input>: 18 different types
 * - <textarea>: Multi-line text
 * - <select> + <option> + <optgroup>: Dropdown menus
 *
 * Dependencies:
 * - utils/dom_utils.js (createElement, setAttributes)
 *
 * Exports:
 * - createInput(type, attributes) → HTMLInputElement
 * - createTextarea(attributes) → HTMLTextAreaElement
 * - createSelect(attributes) → HTMLSelectElement
 * - createOption(value, text, attributes) → HTMLOptionElement
 * - createOptgroup(label, attributes) → HTMLOptGroupElement
 * - createLabel(forId, attributes) → HTMLLabelElement
 * - createForm(attributes) → HTMLFormElement
 * - createFieldset(attributes) → HTMLFieldSetElement
 * - createLegend(attributes) → HTMLLegendElement
 *
 * Example:
 * ```javascript
 * import { createForm, createInput, createLabel } from './form_primitives.js';
 *
 * const form = createForm({ id: 'login' });
 * const label = createLabel('email');
 * label.textContent = 'Email:';
 * const input = createInput('email', { id: 'email', required: true });
 * form.appendChild(label);
 * form.appendChild(input);
 * ```
 */

import { createElement, setAttributes } from '../../utils/dom_utils.js';

// ─────────────────────────────────────────────────────────────────
// Input Element (18 Types)
// ─────────────────────────────────────────────────────────────────

/**
 * Valid HTML5 input types (18 total)
 * Button-like types (submit, reset, button, image) are EXCLUDED - use <button> instead
 */
const VALID_INPUT_TYPES = [
  // Text-based inputs
  'text', 'email', 'password', 'search', 'tel', 'url',
  // Numeric inputs
  'number', 'range',
  // Date/Time inputs
  'date', 'datetime-local', 'month', 'week', 'time',
  // Selection inputs
  'checkbox', 'radio',
  // File input
  'file',
  // Special inputs
  'color', 'hidden'
];

/**
 * Create an <input> element
 *
 * Supports all 18 semantic HTML5 input types.
 * Type is validated and defaults to 'text'.
 *
 * INPUT TYPE REFERENCE:
 *
 * TEXT-BASED (6 types):
 * - text: Plain text input (default)
 * - email: Email address (native validation, keyboard optimized on mobile)
 * - password: Hidden text (shows dots/asterisks)
 * - search: Search queries (may show clear button)
 * - tel: Telephone number (numeric keyboard on mobile)
 * - url: URL input (native validation, keyboard optimized on mobile)
 *
 * NUMERIC (2 types):
 * - number: Numeric input with steppers (supports min, max, step)
 * - range: Slider control (supports min, max, step, value)
 *
 * DATE/TIME (5 types):
 * - date: Date picker (YYYY-MM-DD)
 * - datetime-local: Date + time picker (no timezone)
 * - month: Month picker (YYYY-MM)
 * - week: Week picker (YYYY-W##)
 * - time: Time picker (HH:MM or HH:MM:SS)
 *
 * SELECTION (2 types):
 * - checkbox: Toggle checkbox (supports checked)
 * - radio: Radio button (group via same name attribute)
 *
 * FILE (1 type):
 * - file: File upload (supports accept, multiple)
 *
 * SPECIAL (2 types):
 * - color: Color picker (returns hex #RRGGBB)
 * - hidden: Hidden input (no UI, stores value)
 *
 * @param {string} [type='text'] - Input type (one of 18 valid types)
 * @param {Object} [attributes={}] - HTML attributes (id, name, required, placeholder, etc.)
 * @returns {HTMLInputElement} The created input element
 *
 * @example
 * // Text input
 * const username = createInput('text', { id: 'username', name: 'username', required: true });
 *
 * // Email input (native validation)
 * const email = createInput('email', { id: 'email', placeholder: 'you@example.com' });
 *
 * // Password input
 * const password = createInput('password', { id: 'pwd', autocomplete: 'current-password' });
 *
 * // Number input with constraints
 * const age = createInput('number', { min: 18, max: 120, step: 1 });
 *
 * // Date input
 * const birthday = createInput('date', { id: 'dob', min: '1900-01-01', max: '2024-12-31' });
 *
 * // Checkbox
 * const agree = createInput('checkbox', { id: 'agree', name: 'agree', value: 'yes' });
 *
 * // Radio button (group by same name)
 * const radio1 = createInput('radio', { name: 'plan', value: 'basic', checked: true });
 * const radio2 = createInput('radio', { name: 'plan', value: 'pro' });
 *
 * // File upload (multiple files, accept images only)
 * const fileInput = createInput('file', { accept: 'image/*', multiple: true });
 *
 * // Color picker
 * const colorPicker = createInput('color', { value: '#ff0000' });
 *
 * // Hidden input
 * const hiddenToken = createInput('hidden', { name: 'csrf_token', value: 'abc123' });
 */
export function createInput(type = 'text', attributes = {}) {
  const input = createElement('input');

  // Validate input type (default to 'text')
  const validType = VALID_INPUT_TYPES.includes(type) ? type : 'text';

  if (type && !VALID_INPUT_TYPES.includes(type)) {
    console.warn(`[form_primitives] createInput: Invalid type "${type}", defaulting to "text". Valid types: ${VALID_INPUT_TYPES.join(', ')}`);
  }

  // Sensible defaults
  const defaults = {
    type: validType,
    autocomplete: 'off'  // Can be overridden by attributes
  };

  // Merge defaults with user attributes (user attributes take precedence)
  setAttributes(input, { ...defaults, ...attributes });

  return input;
}

// ─────────────────────────────────────────────────────────────────
// Textarea Element (Multi-line Text)
// ─────────────────────────────────────────────────────────────────

/**
 * Create a <textarea> element
 *
 * Used for multi-line text input (comments, messages, descriptions).
 * Separate element from <input>, NOT an input type.
 *
 * Common Attributes:
 * - rows: Number of visible text rows (default browser behavior ~2)
 * - cols: Width in characters (default browser behavior ~20)
 * - maxlength: Maximum character count
 * - placeholder: Placeholder text
 * - required: Make field required
 * - wrap: Text wrapping (soft/hard)
 *
 * @param {Object} [attributes={}] - HTML attributes (id, name, rows, cols, placeholder, etc.)
 * @returns {HTMLTextAreaElement} The created textarea element
 *
 * @example
 * // Basic textarea
 * const comments = createTextarea({ id: 'comments', name: 'comments' });
 *
 * // Textarea with size constraints
 * const message = createTextarea({
 *   rows: 5,
 *   cols: 50,
 *   maxlength: 500,
 *   placeholder: 'Enter your message...'
 * });
 *
 * // Required textarea
 * const feedback = createTextarea({ id: 'feedback', required: true });
 */
export function createTextarea(attributes = {}) {
  const textarea = createElement('textarea');

  if (Object.keys(attributes).length > 0) {
    setAttributes(textarea, attributes);
  }

  return textarea;
}

// ─────────────────────────────────────────────────────────────────
// Select Element (Dropdown Menu)
// ─────────────────────────────────────────────────────────────────

/**
 * Create a <select> element
 *
 * Dropdown menu for selecting one or multiple options.
 * Contains <option> elements (and optionally <optgroup>).
 *
 * Common Attributes:
 * - multiple: Allow multiple selections (changes to listbox)
 * - size: Number of visible options (for listbox mode)
 * - required: Make selection required
 * - disabled: Disable entire select
 *
 * @param {Object} [attributes={}] - HTML attributes (id, name, multiple, required, etc.)
 * @returns {HTMLSelectElement} The created select element
 *
 * @example
 * // Basic dropdown
 * const country = createSelect({ id: 'country', name: 'country' });
 *
 * // Multiple selection listbox
 * const skills = createSelect({ id: 'skills', name: 'skills', multiple: true, size: 5 });
 *
 * // Required select
 * const plan = createSelect({ id: 'plan', name: 'plan', required: true });
 */
export function createSelect(attributes = {}) {
  const select = createElement('select');

  if (Object.keys(attributes).length > 0) {
    setAttributes(select, attributes);
  }

  return select;
}

/**
 * Create an <option> element
 *
 * Individual option within a <select> dropdown.
 * Must be a child of <select> or <optgroup>.
 *
 * @param {string} value - The option value (submitted with form)
 * @param {string} text - The visible text for the option
 * @param {Object} [attributes={}] - HTML attributes (selected, disabled, etc.)
 * @returns {HTMLOptionElement} The created option element
 *
 * @example
 * // Basic option
 * const opt1 = createOption('us', 'United States');
 *
 * // Selected option
 * const opt2 = createOption('ca', 'Canada', { selected: true });
 *
 * // Disabled option
 * const opt3 = createOption('', '-- Select Country --', { disabled: true, selected: true });
 */
export function createOption(value, text, attributes = {}) {
  const option = createElement('option');

  // Set value and text
  option.value = value;
  option.textContent = text;

  if (Object.keys(attributes).length > 0) {
    setAttributes(option, attributes);
  }

  return option;
}

/**
 * Create an <optgroup> element
 *
 * Groups related options within a <select> dropdown.
 * Must be a child of <select>, contains <option> elements.
 *
 * @param {string} label - The visible label for the group
 * @param {Object} [attributes={}] - HTML attributes (disabled, etc.)
 * @returns {HTMLOptGroupElement} The created optgroup element
 *
 * @example
 * // Option group
 * const northAmerica = createOptgroup('North America');
 * northAmerica.appendChild(createOption('us', 'United States'));
 * northAmerica.appendChild(createOption('ca', 'Canada'));
 *
 * const select = createSelect({ id: 'country' });
 * select.appendChild(northAmerica);
 */
export function createOptgroup(label, attributes = {}) {
  const optgroup = createElement('optgroup');

  // Set label
  optgroup.label = label;

  if (Object.keys(attributes).length > 0) {
    setAttributes(optgroup, attributes);
  }

  return optgroup;
}

// ─────────────────────────────────────────────────────────────────
// Label Element (Accessibility)
// ─────────────────────────────────────────────────────────────────

/**
 * Create a <label> element
 *
 * Associates descriptive text with form inputs (critical for accessibility).
 * Two association methods:
 * 1. "for" attribute pointing to input id (recommended)
 * 2. Wrapping the input element (implicit association)
 *
 * Best Practice:
 * - ALWAYS provide labels for inputs (except hidden)
 * - Use "for" attribute for explicit association
 * - Clicking label focuses/toggles associated input
 *
 * @param {string} [forId=''] - ID of the associated input element
 * @param {Object} [attributes={}] - HTML attributes (id, class, etc.)
 * @returns {HTMLLabelElement} The created label element
 *
 * @example
 * // Explicit association (recommended)
 * const label = createLabel('email', { class: 'form-label' });
 * label.textContent = 'Email Address:';
 * const input = createInput('email', { id: 'email' });
 *
 * // Implicit association (wrapping)
 * const wrapperLabel = createLabel();
 * wrapperLabel.textContent = 'Username: ';
 * wrapperLabel.appendChild(createInput('text', { name: 'username' }));
 */
export function createLabel(forId = '', attributes = {}) {
  const label = createElement('label');

  if (forId) {
    setAttributes(label, { for: forId, ...attributes });
  } else if (Object.keys(attributes).length > 0) {
    setAttributes(label, attributes);
  }

  return label;
}

// ─────────────────────────────────────────────────────────────────
// Form Element (Container)
// ─────────────────────────────────────────────────────────────────

/**
 * Create a <form> element
 *
 * Container for form inputs and submission handling.
 * Provides native validation and submit events.
 *
 * Common Attributes:
 * - action: URL to submit form data (default: current page)
 * - method: HTTP method (GET or POST, default: GET)
 * - enctype: Encoding type (for file uploads: multipart/form-data)
 * - novalidate: Disable native HTML5 validation
 * - autocomplete: Enable/disable autocomplete (on/off)
 *
 * Best Practice:
 * - Use method="POST" for data modification
 * - Use method="GET" for searches (idempotent)
 * - Add enctype="multipart/form-data" for file uploads
 * - Listen to 'submit' event, call preventDefault() for AJAX
 *
 * @param {Object} [attributes={}] - HTML attributes (action, method, enctype, etc.)
 * @returns {HTMLFormElement} The created form element
 *
 * @example
 * // Basic POST form
 * const loginForm = createForm({
 *   id: 'login',
 *   method: 'POST',
 *   action: '/api/login'
 * });
 *
 * // Search form (GET)
 * const searchForm = createForm({
 *   method: 'GET',
 *   action: '/search'
 * });
 *
 * // File upload form
 * const uploadForm = createForm({
 *   method: 'POST',
 *   enctype: 'multipart/form-data'
 * });
 *
 * // AJAX form (prevent default submission)
 * const ajaxForm = createForm({ id: 'contact' });
 * ajaxForm.addEventListener('submit', (e) => {
 *   e.preventDefault();
 *   // Handle with fetch/AJAX
 * });
 */
export function createForm(attributes = {}) {
  const form = createElement('form');

  if (Object.keys(attributes).length > 0) {
    setAttributes(form, attributes);
  }

  return form;
}

// ─────────────────────────────────────────────────────────────────
// Fieldset + Legend (Form Grouping)
// ─────────────────────────────────────────────────────────────────

/**
 * Create a <fieldset> element
 *
 * Groups related form controls with a visual border.
 * Used for semantic grouping and accessibility.
 * First child is typically <legend> (the group's caption).
 *
 * Best Practice:
 * - Group related inputs (e.g., address fields, payment info)
 * - Use <legend> as first child for the group title
 * - Can be disabled (disables all contained inputs)
 *
 * @param {Object} [attributes={}] - HTML attributes (id, disabled, etc.)
 * @returns {HTMLFieldSetElement} The created fieldset element
 *
 * @example
 * // Address fieldset
 * const addressFields = createFieldset({ id: 'address' });
 * const legend = createLegend();
 * legend.textContent = 'Shipping Address';
 * addressFields.appendChild(legend);
 *
 * // Disabled fieldset (disables all inputs inside)
 * const disabledFields = createFieldset({ disabled: true });
 */
export function createFieldset(attributes = {}) {
  const fieldset = createElement('fieldset');

  if (Object.keys(attributes).length > 0) {
    setAttributes(fieldset, attributes);
  }

  return fieldset;
}

/**
 * Create a <legend> element
 *
 * Caption/title for a <fieldset> group.
 * Must be the first child of <fieldset>.
 *
 * @param {Object} [attributes={}] - HTML attributes (id, class, etc.)
 * @returns {HTMLLegendElement} The created legend element
 *
 * @example
 * // Fieldset with legend
 * const fieldset = createFieldset();
 * const legend = createLegend({ class: 'fieldset-title' });
 * legend.textContent = 'Personal Information';
 * fieldset.appendChild(legend);
 */
export function createLegend(attributes = {}) {
  const legend = createElement('legend');

  if (Object.keys(attributes).length > 0) {
    setAttributes(legend, attributes);
  }

  return legend;
}

// ─────────────────────────────────────────────────────────────────
// Default Export (for convenience)
// ─────────────────────────────────────────────────────────────────
export default {
  createInput,
  createTextarea,
  createSelect,
  createOption,
  createOptgroup,
  createLabel,
  createForm,
  createFieldset,
  createLegend
};

