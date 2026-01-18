/**
 * ═══════════════════════════════════════════════════════════════
 * Table Primitives - Tabular Data Structure Elements
 * ═══════════════════════════════════════════════════════════════
 *
 * HTML table elements for displaying structured tabular data.
 * Used for data tables, grids, and any row/column data structure.
 *
 * @module rendering/table_primitives
 * @layer 0.0 (RAWEST - table structure)
 * @pattern Pure Factory Functions
 *
 * Philosophy:
 * - Semantic table structure (thead/tbody/tfoot separation)
 * - Row-oriented organization (tr contains th/td)
 * - Accessibility (proper header associations)
 * - NO styling, NO classes (dress up later)
 *
 * Table Structure:
 * - <table>: Container for tabular data
 * - <caption>: Table title/description
 * - <colgroup> + <col>: Column grouping and styling
 * - <thead>: Header rows
 * - <tbody>: Data rows (main content)
 * - <tfoot>: Footer rows (totals, summaries)
 * - <tr>: Table row (contains th or td)
 * - <th>: Header cell (for row/column headers)
 * - <td>: Data cell (for actual data)
 *
 * Semantic Meaning:
 * - Use <th> for headers (scope="col" or scope="row")
 * - Use <td> for data cells
 * - Separate header, body, and footer for clarity
 * - Use <caption> for table title (accessibility)
 *
 * Accessibility:
 * - <th> elements should have scope attribute (col/row)
 * - Complex tables may need headers/id associations
 * - <caption> provides context for screen readers
 *
 * Dependencies:
 * - utils/dom_utils.js (createElement, setAttributes)
 *
 * Exports:
 * - createTable(attributes) → HTMLTableElement
 * - createCaption(attributes) → HTMLTableCaptionElement
 * - createColgroup(attributes) → HTMLTableColElement
 * - createCol(attributes) → HTMLTableColElement
 * - createThead(attributes) → HTMLTableSectionElement
 * - createTbody(attributes) → HTMLTableSectionElement
 * - createTfoot(attributes) → HTMLTableSectionElement
 * - createTr(attributes) → HTMLTableRowElement
 * - createTh(scope, attributes) → HTMLTableCellElement
 * - createTd(attributes) → HTMLTableCellElement
 *
 * Example:
 * ```javascript
 * import { createTable, createThead, createTbody, createTr, createTh, createTd } from './table_primitives.js';
 *
 * // Build a simple table
 * const table = createTable({ id: 'users' });
 * const thead = createThead();
 * const headerRow = createTr();
 * headerRow.appendChild(createTh('col').textContent = 'Name');
 * headerRow.appendChild(createTh('col').textContent = 'Age');
 * thead.appendChild(headerRow);
 *
 * const tbody = createTbody();
 * const dataRow = createTr();
 * dataRow.appendChild(createTd()).textContent = 'Alice';
 * dataRow.appendChild(createTd()).textContent = '30';
 * tbody.appendChild(dataRow);
 *
 * table.appendChild(thead);
 * table.appendChild(tbody);
 * ```
 */

import { createElement, setAttributes } from '../../utils/dom_utils.js';

// ─────────────────────────────────────────────────────────────────
// Table Container
// ─────────────────────────────────────────────────────────────────

/**
 * Create a <table> element
 *
 * The main container for tabular data. Should contain thead, tbody,
 * and optionally tfoot and caption elements.
 *
 * Semantic Meaning:
 * - Represents data in rows and columns
 * - Should be used for actual tabular data (not layout!)
 * - Contains structured header, body, and footer sections
 *
 * Structure:
 * - <caption> (optional, first child if present)
 * - <colgroup> (optional, for column styling)
 * - <thead> (optional but recommended)
 * - <tbody> (required, main data)
 * - <tfoot> (optional, for summaries)
 *
 * @param {Object} [attributes={}] - HTML attributes (id, class, role, etc.)
 * @returns {HTMLTableElement} The created table element
 *
 * @example
 * // Basic table
 * const table = createTable({ id: 'data-table' });
 *
 * @example
 * // Table with ARIA attributes
 * const accessibleTable = createTable({
 *   role: 'table',
 *   'aria-label': 'User data table',
 *   'aria-describedby': 'table-description'
 * });
 */
export function createTable(attributes = {}) {
  const table = createElement('table');

  if (Object.keys(attributes).length > 0) {
    setAttributes(table, attributes);
  }

  return table;
}

// ─────────────────────────────────────────────────────────────────
// Table Caption
// ─────────────────────────────────────────────────────────────────

/**
 * Create a <caption> element
 *
 * Provides a title or description for the table. Should be the first
 * child of the <table> element if present.
 *
 * Semantic Meaning:
 * - Describes the purpose/content of the table
 * - Read by screen readers for context
 * - Acts as a heading for the table
 *
 * Accessibility:
 * - Highly recommended for screen reader users
 * - Provides context before table content
 * - Can replace need for separate heading
 *
 * @param {Object} [attributes={}] - HTML attributes (id, class, etc.)
 * @returns {HTMLTableCaptionElement} The created caption element
 *
 * @example
 * const caption = createCaption();
 * caption.textContent = 'Monthly Sales Data - 2024';
 * table.appendChild(caption);
 */
export function createCaption(attributes = {}) {
  const caption = createElement('caption');

  if (Object.keys(attributes).length > 0) {
    setAttributes(caption, attributes);
  }

  return caption;
}

// ─────────────────────────────────────────────────────────────────
// Column Group Elements
// ─────────────────────────────────────────────────────────────────

/**
 * Create a <colgroup> element
 *
 * Groups columns together for styling or semantic purposes.
 * Contains <col> elements that define column properties.
 *
 * Semantic Meaning:
 * - Groups related columns
 * - Allows column-wide styling
 * - Can span multiple columns
 *
 * Usage:
 * - Must come before thead/tbody/tfoot
 * - Contains <col> elements
 * - Can have span attribute for grouping
 *
 * @param {Object} [attributes={}] - HTML attributes (span, class, etc.)
 * @returns {HTMLTableColElement} The created colgroup element
 *
 * @example
 * const colgroup = createColgroup();
 * colgroup.appendChild(createCol({ style: 'width: 100px' }));
 * colgroup.appendChild(createCol({ style: 'width: 200px' }));
 * table.appendChild(colgroup);
 */
export function createColgroup(attributes = {}) {
  const colgroup = createElement('colgroup');

  if (Object.keys(attributes).length > 0) {
    setAttributes(colgroup, attributes);
  }

  return colgroup;
}

/**
 * Create a <col> element
 *
 * Defines properties for a column within a colgroup.
 * Does not contain any content - it's a void element.
 *
 * Semantic Meaning:
 * - Represents a column
 * - Can span multiple columns
 * - Used for column-wide styling
 *
 * Usage:
 * - Child of <colgroup>
 * - Can have span attribute
 * - Used for styling, not content
 *
 * @param {Object} [attributes={}] - HTML attributes (span, style, class, etc.)
 * @returns {HTMLTableColElement} The created col element
 *
 * @example
 * // Single column
 * const col1 = createCol({ style: 'width: 150px' });
 *
 * @example
 * // Column spanning 3 columns
 * const col2 = createCol({ span: '3', class: 'highlight-cols' });
 */
export function createCol(attributes = {}) {
  const col = createElement('col');

  if (Object.keys(attributes).length > 0) {
    setAttributes(col, attributes);
  }

  return col;
}

// ─────────────────────────────────────────────────────────────────
// Table Sections
// ─────────────────────────────────────────────────────────────────

/**
 * Create a <thead> element
 *
 * Contains header rows for the table. Typically contains <th> cells.
 *
 * Semantic Meaning:
 * - Groups header content
 * - Distinguishes headers from data
 * - Can repeat on printed pages (print CSS)
 *
 * Usage:
 * - Contains <tr> elements
 * - Should come before <tbody>
 * - Optional but highly recommended
 *
 * @param {Object} [attributes={}] - HTML attributes (id, class, etc.)
 * @returns {HTMLTableSectionElement} The created thead element
 *
 * @example
 * const thead = createThead();
 * const headerRow = createTr();
 * headerRow.appendChild(createTh('col'));
 * thead.appendChild(headerRow);
 * table.appendChild(thead);
 */
export function createThead(attributes = {}) {
  const thead = createElement('thead');

  if (Object.keys(attributes).length > 0) {
    setAttributes(thead, attributes);
  }

  return thead;
}

/**
 * Create a <tbody> element
 *
 * Contains the main data rows of the table. This is where the actual
 * tabular data goes.
 *
 * Semantic Meaning:
 * - Groups body/data content
 * - Main content of the table
 * - Can have multiple tbody elements for grouping
 *
 * Usage:
 * - Contains <tr> elements with <td> cells
 * - Required (implicit if omitted)
 * - Can have multiple tbody sections
 *
 * @param {Object} [attributes={}] - HTML attributes (id, class, etc.)
 * @returns {HTMLTableSectionElement} The created tbody element
 *
 * @example
 * const tbody = createTbody();
 * const dataRow = createTr();
 * dataRow.appendChild(createTd());
 * tbody.appendChild(dataRow);
 * table.appendChild(tbody);
 */
export function createTbody(attributes = {}) {
  const tbody = createElement('tbody');

  if (Object.keys(attributes).length > 0) {
    setAttributes(tbody, attributes);
  }

  return tbody;
}

/**
 * Create a <tfoot> element
 *
 * Contains footer rows for the table. Typically used for summaries,
 * totals, or footnotes.
 *
 * Semantic Meaning:
 * - Groups footer content
 * - For summaries and totals
 * - Can repeat on printed pages (print CSS)
 *
 * Usage:
 * - Contains <tr> elements
 * - Should come after <tbody> (HTML5)
 * - Optional
 *
 * @param {Object} [attributes={}] - HTML attributes (id, class, etc.)
 * @returns {HTMLTableSectionElement} The created tfoot element
 *
 * @example
 * const tfoot = createTfoot();
 * const totalRow = createTr();
 * totalRow.appendChild(createTd()).textContent = 'Total:';
 * totalRow.appendChild(createTd()).textContent = '$500';
 * tfoot.appendChild(totalRow);
 * table.appendChild(tfoot);
 */
export function createTfoot(attributes = {}) {
  const tfoot = createElement('tfoot');

  if (Object.keys(attributes).length > 0) {
    setAttributes(tfoot, attributes);
  }

  return tfoot;
}

// ─────────────────────────────────────────────────────────────────
// Table Row
// ─────────────────────────────────────────────────────────────────

/**
 * Create a <tr> element
 *
 * Represents a row in the table. Contains <th> or <td> cells.
 *
 * Semantic Meaning:
 * - Groups cells into a row
 * - Can contain header cells (<th>) or data cells (<td>)
 * - Defines horizontal grouping of data
 *
 * Usage:
 * - Child of <thead>, <tbody>, or <tfoot>
 * - Contains <th> or <td> elements
 * - Each row should have same number of cells (or use colspan)
 *
 * @param {Object} [attributes={}] - HTML attributes (id, class, role, etc.)
 * @returns {HTMLTableRowElement} The created tr element
 *
 * @example
 * const row = createTr({ id: 'row-1' });
 * row.appendChild(createTd()).textContent = 'Data';
 * tbody.appendChild(row);
 *
 * @example
 * // Row with ARIA attributes
 * const accessibleRow = createTr({ role: 'row', 'aria-selected': 'false' });
 */
export function createTr(attributes = {}) {
  const tr = createElement('tr');

  if (Object.keys(attributes).length > 0) {
    setAttributes(tr, attributes);
  }

  return tr;
}

// ─────────────────────────────────────────────────────────────────
// Table Cells
// ─────────────────────────────────────────────────────────────────

/**
 * Create a <th> element (header cell)
 *
 * Represents a header cell in the table. Used for column headers,
 * row headers, or both.
 *
 * Semantic Meaning:
 * - Defines header for column or row
 * - Typically bold and centered by default
 * - Associates data cells with their headers (accessibility)
 *
 * Scope Attribute:
 * - 'col': Header for a column (most common)
 * - 'row': Header for a row
 * - 'colgroup': Header for column group
 * - 'rowgroup': Header for row group
 *
 * Accessibility:
 * - Screen readers use <th> to identify headers
 * - scope attribute clarifies header relationship
 * - Critical for table accessibility
 *
 * @param {string} [scope='col'] - Scope of the header ('col', 'row', 'colgroup', 'rowgroup')
 * @param {Object} [attributes={}] - HTML attributes (id, class, colspan, rowspan, etc.)
 * @returns {HTMLTableCellElement} The created th element
 *
 * @example
 * // Column header
 * const colHeader = createTh('col');
 * colHeader.textContent = 'Name';
 *
 * @example
 * // Row header
 * const rowHeader = createTh('row');
 * rowHeader.textContent = 'Total';
 *
 * @example
 * // Header spanning 2 columns
 * const spanningHeader = createTh('col', { colspan: '2' });
 * spanningHeader.textContent = 'Full Name';
 */
export function createTh(scope = 'col', attributes = {}) {
  const th = createElement('th');

  // Set scope attribute (critical for accessibility)
  const validScopes = ['col', 'row', 'colgroup', 'rowgroup'];
  if (validScopes.includes(scope)) {
    th.scope = scope;
  } else {
    console.warn(`[table_primitives] createTh: Invalid scope "${scope}", defaulting to "col"`);
    th.scope = 'col';
  }

  // Set additional attributes
  if (Object.keys(attributes).length > 0) {
    setAttributes(th, attributes);
  }

  return th;
}

/**
 * Create a <td> element (data cell)
 *
 * Represents a data cell in the table. Contains the actual tabular data.
 *
 * Semantic Meaning:
 * - Contains table data (not headers)
 * - Associated with row/column headers via position
 * - Can span multiple rows or columns
 *
 * Cell Spanning:
 * - colspan: Span multiple columns
 * - rowspan: Span multiple rows
 * - Use sparingly for complex layouts
 *
 * Accessibility:
 * - Automatically associated with <th> headers
 * - Can use headers attribute for complex tables
 * - Should contain meaningful data
 *
 * @param {Object} [attributes={}] - HTML attributes (id, class, colspan, rowspan, headers, etc.)
 * @returns {HTMLTableCellElement} The created td element
 *
 * @example
 * // Simple data cell
 * const cell = createTd();
 * cell.textContent = 'Alice';
 *
 * @example
 * // Cell spanning 2 columns
 * const spanningCell = createTd({ colspan: '2' });
 * spanningCell.textContent = 'Merged data';
 *
 * @example
 * // Cell with explicit header association
 * const complexCell = createTd({ headers: 'header1 header2' });
 * complexCell.textContent = 'Data';
 */
export function createTd(attributes = {}) {
  const td = createElement('td');

  if (Object.keys(attributes).length > 0) {
    setAttributes(td, attributes);
  }

  return td;
}

// ─────────────────────────────────────────────────────────────────
// Default Export (for convenience)
// ─────────────────────────────────────────────────────────────────
export default {
  createTable,
  createCaption,
  createColgroup,
  createCol,
  createThead,
  createTbody,
  createTfoot,
  createTr,
  createTh,
  createTd
};

