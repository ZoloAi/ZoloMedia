/**
 * ═══════════════════════════════════════════════════════════════
 * zDisplay Event Renderer - Convert zDisplay Events to HTML
 * ═══════════════════════════════════════════════════════════════
 *
 * Renders zDisplay events from the Python backend into HTML elements.
 * Supports: header, text, list, error, warning, success, info
 *
 * Special indent behavior:
 * - indent 0: Flush (clear the zone)
 * - indent 1: h1
 * - indent 2: h2
 * - indent 3: h3
 * - indent 4+: h4 (capped)
 */

export class ZDisplayRenderer {
  constructor(logger = null) {
    this.logger = logger || console;
    this.defaultZone = 'zVaF-content'; // Default zCLI content area (the div inside zVaF tag)
  }

  /**
   * Render a zDisplay event to HTML
   * @param {Object} event - zDisplay event object
   * @param {string} targetZone - Target DOM element ID (default: 'zVaF')
   * @returns {HTMLElement|null} - Created element or null if flushed
   */
  render(event, targetZone = null) {
    try {
      // Normalize event format (support both old and new formats)
      // Old: {event: 'success', content: '...', indent: 0}
      // New: {display_event: 'success', data: {content: '...', indent: 0}}
      const eventType = event.display_event || event.event;
      const eventData = event.data || event;  // Use data if present, otherwise use event itself

      const zone = targetZone || eventData.target || this.defaultZone;
      const container = document.getElementById(zone);

      if (!container) {
        this.logger.error(`[ZDisplayRenderer] Target zone not found: ${zone}`);
        return null;
      }

      // Handle explicit flush event (not just indent 0)
      if (eventType === 'flush' || eventData.flush === true) {
        this._flush(container);
        this.logger.log(`[ZDisplayRenderer] Flushed zone: ${zone}`);
        return null;
      }

      // Route to appropriate renderer based on event type
      let element = null;

      switch (eventType) {
        case 'header':
          element = this._renderHeader(eventData);
          break;
        case 'text':
          element = this._renderText(eventData);
          break;
        case 'list':
          element = this._renderList(eventData);
          break;
        case 'outline':
          element = this._renderOutline(eventData);
          break;
        case 'table':
        case 'zTable':  // Backend sends 'zTable' (camelCase)
          element = this._renderTable(eventData);
          break;
        case 'json':
        case 'json_data':  // Backend sends 'json' or 'json_data'
          element = this._renderJSON(eventData);
          break;
        case 'progress_bar':
          element = this._renderProgressBar(eventData);
          break;
        case 'error':
          element = this._renderAlert(eventData, 'danger');
          break;
        case 'warning':
          element = this._renderAlert(eventData, 'warning');
          break;
        case 'success':
          element = this._renderAlert(eventData, 'success');
          break;
        case 'info':
          element = this._renderAlert(eventData, 'info');
          break;
        default:
          this.logger.warn(`[ZDisplayRenderer] Unknown event type: ${eventType}`);
          element = this._renderText(eventData); // Fallback to text
      }

      if (element) {
        // For interactive tables, replace existing table with same ID instead of appending
        if (eventType === 'table' || eventType === 'zTable') {
          const isInteractive = element.getAttribute('data-interactive') === 'true';
          const tableId = element.getAttribute('data-table-id');

          if (isInteractive && tableId) {
            // Find existing interactive table with same ID
            const existingTable = container.querySelector(`[data-table-id="${tableId}"][data-interactive="true"]`);

            if (existingTable) {
              // Replace existing table
              existingTable.replaceWith(element);
              this.logger.log(`[ZDisplayRenderer] Replaced interactive table '${tableId}' in ${zone}`);
              return element;
            }
          }
        }

        // Default: append element
        container.appendChild(element);
        this.logger.log(`[ZDisplayRenderer] Rendered ${eventType} to ${zone}`);
      }

      return element;
    } catch (error) {
      this.logger.error('[ZDisplayRenderer] Render error:', error);
      throw error; // Let error boundaries handle it
    }
  }

  /**
   * Flush (clear) a zone
   * @private
   */
  _flush(container) {
    container.innerHTML = '';
  }

  /**
   * Render a header element (zTheme pure - NO Bootstrap!)
   * indent=0 → HERO (centered, large, prominent)
   * indent=1-6 → h1-h6 (semantic HTML headers)
   * @private
   */
  _renderHeader(event) {
    const indent = event.indent !== undefined ? event.indent : 1;

    // Python sends 'label' field for headers (not 'content')
    const content = event.label || event.content || '';
    const color = event.color || null;
    const customClass = event.class || null;  // New: Accept custom CSS classes from YAML

    // indent=0 → HERO header (special centered title)
    if (indent === 0) {
      const hero = document.createElement('div');
      hero.className = 'zHero';

      // Apply custom classes if provided
      if (customClass) {
        hero.className += ` ${customClass}`;
      }

      hero.innerHTML = this._sanitizeHTML(content);
      return hero;
    }

    // indent=1-6 → h1-h6 (semantic HTML headers)
    const level = Math.min(indent, 6);
    const tag = `h${level}`;

    const header = document.createElement(tag);
    header.innerHTML = this._sanitizeHTML(content);

    // Apply custom classes if provided (from YAML `class` parameter)
    if (customClass) {
      header.className = customClass;
    }

    // Pure zTheme - all styling handled by zTypography.css (h1-h6 rules)
    // No inline styles needed! 🎨
    // Apply color classes (case-insensitive for PRIMARY/SECONDARY)
    if (color) {
      const colorLower = color.toLowerCase();
      if (colorLower === 'primary') {
        header.classList.add('zText-primary');
      } else if (colorLower === 'secondary') {
        header.classList.add('zText-secondary');
      } else if (colorLower === 'zinfo') {
        header.classList.add('zText-info');
      } else if (colorLower === 'zsuccess') {
        header.classList.add('zText-success');
      } else if (colorLower === 'zwarning') {
        header.classList.add('zText-warning');
      } else if (colorLower === 'zerror') {
        header.classList.add('zText-error');
      }
    }

    return header;
  }

  /**
   * Render a text element (pure zTheme - NO Bootstrap!)
   * @private
   */
  _renderText(event) {
    const p = document.createElement('p');
    // Decode Unicode escapes (U+XXXX format) from ASCII-safe storage
    const decodedContent = this._decodeUnicodeEscapes(event.content);
    p.innerHTML = this._sanitizeHTML(decodedContent);

    // Apply custom classes if provided (from YAML `class` parameter)
    const customClass = event.class || null;
    if (customClass) {
      p.className = customClass;
    }

    // Minimal inline styling (margin-bottom for spacing)
    p.style.marginBottom = '0.5rem';

    // Apply indent as left margin (1rem per indent level)
    if (event.indent && event.indent > 0) {
      p.style.marginLeft = `${event.indent}rem`;
    }

    // Apply color classes (case-insensitive)
    const color = event.color;
    if (color) {
      const colorLower = color.toLowerCase();
      if (colorLower === 'primary') {
        p.classList.add('zText-primary');
      } else if (colorLower === 'secondary') {
        p.classList.add('zText-secondary');
      } else if (colorLower === 'zinfo') {
        p.classList.add('zText-info');
      } else if (colorLower === 'zsuccess') {
        p.classList.add('zText-success');
      } else if (colorLower === 'zwarning') {
        p.classList.add('zText-warning');
      } else if (colorLower === 'zerror') {
        p.classList.add('zText-error');
      }
    }

    return p;
  }

  /**
   * Render a list element (pure zTheme - NO Bootstrap!)
   * Supports both bulleted (ul) and numbered (ol) lists
   * @private
   */
  _renderList(event) {
    // Check style: "number" → <ol>, "bullet" → <ul> (default)
    const style = event.style || 'bullet';
    const listElement = style === 'number'
      ? document.createElement('ol')
      : document.createElement('ul');

    listElement.className = 'zList';

    // Apply custom classes if provided (from YAML `class` parameter)
    const customClass = event.class || null;
    if (customClass) {
      listElement.className += ` ${customClass}`;
    }

    // Apply indent as left margin (minimal inline style for dynamic indentation)
    if (event.indent && event.indent > 0) {
      listElement.style.marginLeft = `${event.indent}rem`;
    }

    // Render list items
    const items = event.items || [];
    items.forEach(item => {
      const li = document.createElement('li');

      // Support both string items and object items with content field
      const content = typeof item === 'string' ? item : (item.content || '');
      
      // Decode Unicode escapes (U+XXXX format) from ASCII-safe storage
      const decodedContent = this._decodeUnicodeEscapes(content);
      li.innerHTML = this._sanitizeHTML(decodedContent);

      listElement.appendChild(li);
    });

    return listElement;
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

  /**
   * Render hierarchical outline with multi-level numbering (Word-style)
   * Supports: number (1,2,3) → letter (a,b,c) → roman (i,ii,iii) → bullet
   * @private
   */
  _renderOutline(event) {
    const items = event.items || [];
    const styles = event.styles || ['number', 'letter', 'roman', 'bullet'];
    const baseIndent = event.indent || 0;

    // Create container for the outline
    const container = document.createElement('div');
    container.className = 'zOutline';

    // Apply custom classes if provided (from YAML `class` parameter)
    const customClass = event.class || null;
    if (customClass) {
      container.className += ` ${customClass}`;
    }

    // Apply base indent
    if (baseIndent > 0) {
      container.style.marginLeft = `${baseIndent}rem`;
    }

    // Render items recursively
    const listElement = this._renderOutlineItems(items, styles, 0);
    if (listElement) {
      container.appendChild(listElement);
    }

    return container;
  }

  /**
   * Recursively render outline items with proper nesting
   * @private
   */
  _renderOutlineItems(items, styles, level) {
    if (!items || items.length === 0) {
      return null;
    }

    // Determine style for this level
    const style = level < styles.length ? styles[level] : 'bullet';

    // Create list element based on style
    let listElement;
    if (style === 'bullet') {
      listElement = document.createElement('ul');
      listElement.className = 'zList';
    } else {
      listElement = document.createElement('ol');
      listElement.className = 'zList';

      // Set list-style-type for different numbering styles
      if (style === 'letter') {
        listElement.style.listStyleType = 'lower-alpha';  // a, b, c
      } else if (style === 'roman') {
        listElement.style.listStyleType = 'lower-roman';  // i, ii, iii
      }
      // 'number' uses default decimal (1, 2, 3)
    }

    // Render each item
    items.forEach(item => {
      const li = document.createElement('li');

      // Extract content and children
      let content, children;
      if (typeof item === 'string') {
        content = item;
        children = null;
      } else if (typeof item === 'object') {
        content = item.content || '';
        children = item.children || null;
      } else {
        content = String(item);
        children = null;
      }

      // Create text node for this item's content
      const contentSpan = document.createElement('span');
      contentSpan.innerHTML = this._sanitizeHTML(content);
      li.appendChild(contentSpan);

      // Recursively render children if they exist
      if (children && children.length > 0) {
        const childList = this._renderOutlineItems(children, styles, level + 1);
        if (childList) {
          li.appendChild(childList);
        }
      }

      listElement.appendChild(li);
    });

    return listElement;
  }

  /**
   * Render a table element (pure zTheme - NO Bootstrap!)
   * Uses zTheme's .zTable classes with automatic striping and hover effects
   * Supports three display modes:
   *   1. Basic: No pagination (limit=null)
   *   2. Simple truncation: limit only, shows "... N more rows"
   *   3. Interactive: limit + interactive=true, shows navigation buttons
   * @private
   */
  _renderTable(event) {
    // Extract table data and pagination metadata
    const title = event.title || '';
    const columns = event.columns || [];
    const allRows = event.rows || [];
    const limit = event.limit;  // Can be null/undefined (show all)
    const offset = event.offset || 0;
    const interactive = event.interactive || false;  // Enable navigation controls

    // Apply pagination if limit is specified
    let rows = allRows;
    let hasMore = false;
    let moreCount = 0;

    if (limit !== null && limit !== undefined && limit > 0) {
      // Slice rows: from offset to offset+limit
      rows = allRows.slice(offset, offset + limit);
      hasMore = (offset + limit) < allRows.length;
      moreCount = allRows.length - (offset + limit);
    }

    // Create container wrapper
    const container = document.createElement('div');
    container.style.marginBottom = '1.5rem';

    // For interactive tables, add a data attribute for replacement logic
    if (interactive) {
      container.setAttribute('data-table-id', title || 'table');
      container.setAttribute('data-interactive', 'true');

      // Add smooth fade-in animation for page transitions
      container.style.animation = 'fadeIn 0.3s ease-in';
    }

    // Apply indent as left margin (minimal inline style for dynamic indentation)
    if (event.indent && event.indent > 0) {
      container.style.marginLeft = `${event.indent}rem`;
    }

    // Add title with pagination info if provided
    if (title) {
      const titleElement = document.createElement('h4');

      // Show pagination range in title if limited
      if (limit !== null && limit !== undefined && limit > 0 && allRows.length > 0) {
        const showingStart = offset + 1;
        const showingEnd = Math.min(offset + rows.length, allRows.length);
        titleElement.textContent = `${title} (showing ${showingStart}-${showingEnd} of ${allRows.length})`;
      } else {
        titleElement.textContent = title;
      }

      titleElement.style.marginBottom = '0.75rem';
      titleElement.style.color = 'var(--color-darkgray)';
      container.appendChild(titleElement);
    }

    // Create table wrapper for responsiveness
    const tableWrapper = document.createElement('div');
    tableWrapper.className = 'zTable-responsive';

    // Create table
    const table = document.createElement('table');
    table.className = 'zTable zTable-striped zTable-hover zTable-bordered';

    // Create thead with columns
    if (columns.length > 0) {
      const thead = document.createElement('thead');
      const headerRow = document.createElement('tr');

      columns.forEach(column => {
        const th = document.createElement('th');
        th.textContent = column;
        headerRow.appendChild(th);
      });

      thead.appendChild(headerRow);
      table.appendChild(thead);
    }

    // Create tbody with (paginated) rows
    if (rows.length > 0) {
      const tbody = document.createElement('tbody');

      rows.forEach(row => {
        const tr = document.createElement('tr');

        // Handle both array and object rows
        if (Array.isArray(row)) {
          // Array row: [val1, val2, val3]
          row.forEach(value => {
            const td = document.createElement('td');
            td.innerHTML = this._sanitizeHTML(this._formatCellValue(value));
            tr.appendChild(td);
          });
        } else {
          // Object row: {col1: val1, col2: val2, ...}
          columns.forEach(column => {
            const td = document.createElement('td');
            const value = row[column];
            td.innerHTML = this._sanitizeHTML(this._formatCellValue(value));
            tr.appendChild(td);
          });
        }

        tbody.appendChild(tr);
      });

      table.appendChild(tbody);
    }

    tableWrapper.appendChild(table);
    container.appendChild(tableWrapper);

    // Footer: Interactive navigation OR simple "... N more rows" message
    if (interactive && limit && limit > 0) {
      // Interactive mode: Render navigation buttons
      this._renderNavigationControls(container, {
        title, columns, rows: allRows, limit, offset, totalRows: allRows.length
      });
    } else if (hasMore && moreCount > 0) {
      // Simple truncation: Show "... N more rows" footer
      const footer = document.createElement('p');
      footer.style.color = 'var(--color-info)';
      footer.style.marginTop = '0.5rem';
      footer.style.marginLeft = '1rem';
      footer.style.fontStyle = 'italic';
      footer.textContent = `... ${moreCount} more rows`;
      container.appendChild(footer);
    }

    return container;
  }

  /**
   * Render interactive navigation controls for paginated tables
   * Creates buttons that send navigation commands back to the server
   * @private
   */
  _renderNavigationControls(container, tableState) {
    const { limit, offset, totalRows } = tableState;

    // Calculate pagination metadata
    const totalPages = Math.ceil(totalRows / limit);
    const currentPage = Math.floor(offset / limit) + 1;
    const canGoPrev = currentPage > 1;
    const canGoNext = currentPage < totalPages;

    // Create navigation container
    const navContainer = document.createElement('div');
    navContainer.style.marginTop = '1rem';
    navContainer.style.display = 'flex';
    navContainer.style.gap = '0.5rem';
    navContainer.style.alignItems = 'center';
    navContainer.style.justifyContent = 'center';

    // Page info display
    const pageInfo = document.createElement('span');
    pageInfo.style.marginRight = '1rem';
    pageInfo.style.color = 'var(--color-darkgray)';
    pageInfo.style.fontWeight = '500';
    pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    navContainer.appendChild(pageInfo);

    // Helper to create navigation button
    const createNavButton = (label, command, enabled) => {
      const btn = document.createElement('button');
      btn.className = `zoloButton ${  enabled ? 'zBtnSecondary' : 'zBtnDisabled'}`;
      btn.textContent = label;
      btn.disabled = !enabled;

      if (enabled) {
        btn.onclick = () => {
          // Send navigation command back to server
          this.logger.log(`[ZDisplayRenderer] Sending navigation command: ${command}`);
          if (this.client && this.client.send) {
            this.client.send({
              event: 'table_navigate',
              data: {
                command,
                ...tableState
              }
            });
          }
        };
      }

      return btn;
    };

    // Navigation buttons
    navContainer.appendChild(createNavButton('⏮ First', 'f', canGoPrev));
    navContainer.appendChild(createNavButton('◀ Previous', 'p', canGoPrev));
    navContainer.appendChild(createNavButton('Next ▶', 'n', canGoNext));
    navContainer.appendChild(createNavButton('Last ⏭', 'l', canGoNext));

    // Jump to page input
    const jumpContainer = document.createElement('span');
    jumpContainer.style.marginLeft = '1rem';
    jumpContainer.style.display = 'flex';
    jumpContainer.style.gap = '0.5rem';
    jumpContainer.style.alignItems = 'center';

    const jumpLabel = document.createElement('span');
    jumpLabel.style.color = 'var(--color-darkgray)';
    jumpLabel.textContent = 'Jump to:';
    jumpContainer.appendChild(jumpLabel);

    const jumpInput = document.createElement('input');
    jumpInput.type = 'number';
    jumpInput.min = '1';
    jumpInput.max = totalPages.toString();
    jumpInput.placeholder = '#';
    jumpInput.style.width = '60px';
    jumpInput.style.padding = '0.25rem 0.5rem';
    jumpInput.style.border = '1px solid var(--color-gray)';
    jumpInput.style.borderRadius = '4px';
    jumpInput.style.textAlign = 'center';

    const jumpBtn = createNavButton('Go', 'jump', true);
    jumpBtn.onclick = () => {
      const pageNum = parseInt(jumpInput.value);
      if (pageNum >= 1 && pageNum <= totalPages) {
        this.logger.log(`[ZDisplayRenderer] Jumping to page: ${pageNum}`);
        if (this.client && this.client.send) {
          this.client.send({
            event: 'table_navigate',
            data: {
              command: pageNum.toString(),
              ...tableState
            }
          });
        }
        jumpInput.value = '';
      }
    };

    jumpInput.onkeypress = (e) => {
      if (e.key === 'Enter') {
        jumpBtn.click();
      }
    };

    jumpContainer.appendChild(jumpInput);
    jumpContainer.appendChild(jumpBtn);
    navContainer.appendChild(jumpContainer);

    container.appendChild(navContainer);
  }

  /**
   * Format cell value for display (handles booleans, nulls, etc.)
   * @private
   */
  _formatCellValue(value) {
    if (value === null || value === undefined) {
      return '<span style="color: var(--color-gray);">—</span>';
    }
    if (typeof value === 'boolean') {
      return value
        ? '<span style="color: var(--color-success);">✓</span>'
        : '<span style="color: var(--color-error);">✗</span>';
    }
    return String(value);
  }

  /**
   * Render JSON data (pretty-printed)
   * @private
   */
  _renderJSON(event) {
    // Extract JSON data
    const data = event.data || event.content || {};

    // Create container
    const container = document.createElement('div');
    container.style.marginBottom = '1rem';

    // Apply indent as left margin
    if (event.indent && event.indent > 0) {
      container.style.marginLeft = `${event.indent}rem`;
    }

    // Create pre element for JSON
    const pre = document.createElement('pre');
    pre.style.backgroundColor = 'var(--color-base)';
    pre.style.border = '1px solid var(--color-gray)';
    pre.style.borderRadius = '4px';
    pre.style.padding = '1rem';
    pre.style.overflow = 'auto';
    pre.style.fontFamily = 'monospace';
    pre.style.fontSize = '0.9em';
    pre.style.color = 'var(--color-darkgray)';

    // Pretty-print JSON
    try {
      pre.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
      pre.textContent = String(data);
    }

    container.appendChild(pre);
    return container;
  }

  /**
   * Render progress bar (simple text-based for now)
   * TODO: Implement CSS animated progress bar
   * @private
   */
  _renderProgressBar(event) {
    // Extract progress data
    const current = event.current || 0;
    const total = event.total || 100;
    const label = event.label || 'Processing';
    const percentage = Math.round((current / total) * 100);
    const showPercentage = event.showPercentage !== false;  // Default true
    const color = event.color || 'default';
    const progressId = event.progressId || `progress-${Date.now()}`;

    // Check if progress bar already exists (update existing)
    const existingProgress = document.querySelector(`[data-progress-id="${progressId}"]`);
    if (existingProgress) {
      // Update existing progress bar
      const fillElement = existingProgress.querySelector('.zProgress-fill');
      const statsElement = existingProgress.querySelector('.zProgress-stats');

      if (fillElement) {
        fillElement.style.width = `${percentage}%`;
      }
      if (statsElement && showPercentage) {
        statsElement.textContent = `${percentage}%`;
      }

      // Keep progress bar visible even when complete (for demo purposes)
      // TODO: Add option to auto-remove on complete if needed

      return null;  // Don't append, we updated existing
    }

    // Create new progress bar using zTheme classes
    const container = document.createElement('div');
    container.className = 'zProgress';
    container.setAttribute('data-progress-id', progressId);

    // Apply color variant
    const colorMap = {
      GREEN: 'success',
      RED: 'danger',
      YELLOW: 'warning',
      BLUE: 'info',
      PURPLE: 'purple'
    };
    const variant = colorMap[color] || 'info';
    container.classList.add(`zProgress-${variant}`);

    // Apply indent as left margin
    if (event.indent && event.indent > 0) {
      container.style.marginLeft = `${event.indent}rem`;
    }

    // Progress label and stats
    const labelDiv = document.createElement('div');
    labelDiv.className = 'zProgress-label';

    const labelText = document.createElement('span');
    labelText.textContent = label;
    labelDiv.appendChild(labelText);

    if (showPercentage) {
      const statsSpan = document.createElement('span');
      statsSpan.className = 'zProgress-stats';
      statsSpan.textContent = `${percentage}%`;
      labelDiv.appendChild(statsSpan);
    }

    container.appendChild(labelDiv);

    // Progress track (background)
    const track = document.createElement('div');
    track.className = 'zProgress-track';

    // Progress fill (animated bar)
    const fill = document.createElement('div');
    fill.className = 'zProgress-fill';
    fill.style.width = `${percentage}%`;

    track.appendChild(fill);
    container.appendChild(track);

    return container;
  }

  /**
   * Start a spinner (loading indicator)
   * @param {Object} event - Spinner event data
   * @param {string} targetZone - Target DOM element ID
   */
  renderSpinnerStart(event, targetZone = null) {
    const spinnerId = event.spinnerId || event.data?.spinnerId || `spinner-${Date.now()}`;
    const label = event.label || event.data?.label || 'Loading';
    const style = event.style || event.data?.style || 'dots';
    const zone = targetZone || this.defaultZone;
    const container = document.getElementById(zone);

    if (!container) {
      this.logger.error(`[ZDisplayRenderer] Cannot render spinner - zone not found: ${zone}`);
      return;
    }

    // Create spinner using zTheme classes
    const spinnerDiv = document.createElement('div');
    spinnerDiv.className = 'zSpinner';
    spinnerDiv.setAttribute('data-spinner-id', spinnerId);

    // Spinner animation
    const animationDiv = document.createElement('div');
    animationDiv.className = 'zSpinner-animation';

    // Map backend style names to CSS class names
    const styleMap = {
      dots: 'zSpinner-dots',
      line: 'zSpinner-line',
      arc: 'zSpinner-arc',
      arrow: 'zSpinner-arrow',
      bouncingBall: 'zSpinner-bouncingBall',
      simple: 'zSpinner-simple',
      circle: 'zSpinner-circle'
    };

    const spinnerClass = styleMap[style] || 'zSpinner-dots';
    const spinnerIcon = document.createElement('div');
    spinnerIcon.className = spinnerClass;
    animationDiv.appendChild(spinnerIcon);

    // Label
    const labelSpan = document.createElement('span');
    labelSpan.className = 'zSpinner-label';
    labelSpan.textContent = label;

    spinnerDiv.appendChild(animationDiv);
    spinnerDiv.appendChild(labelSpan);

    container.appendChild(spinnerDiv);
    this.logger.log(`[ZDisplayRenderer] Spinner started: ${spinnerId}`);
  }

  /**
   * Stop a spinner (loading indicator)
   * @param {Object} event - Spinner event data
   */
  renderSpinnerStop(event) {
    const spinnerId = event.spinnerId || event.data?.spinnerId;

    if (!spinnerId) {
      this.logger.warn('[ZDisplayRenderer] Cannot stop spinner - no spinnerId provided');
      return;
    }

    const spinner = document.querySelector(`[data-spinner-id="${spinnerId}"]`);

    if (spinner) {
      // Replace spinner with success checkmark
      spinner.style.transition = 'opacity 0.3s ease';
      spinner.style.opacity = '0';

      setTimeout(() => {
        const label = spinner.querySelector('.zSpinner-label');
        const labelText = label ? label.textContent : '';

        // Create success message
        const successDiv = document.createElement('p');
        successDiv.style.marginBottom = '0.5rem';
        successDiv.style.color = 'var(--mainGreen, #8FBE6D)';
        successDiv.innerHTML = `✓ ${labelText}`;

        spinner.replaceWith(successDiv);
        this.logger.log(`[ZDisplayRenderer] Spinner stopped: ${spinnerId}`);
      }, 300);
    }
  }

  /**
   * Render a signal alert (error, warning, success, info)
   * Toast-style dismissible alerts - pure zTheme, beats Bootstrap! 🎨
   * Auto-fades after 5 seconds, but can be manually dismissed with ×
   * @private
   */
  _renderAlert(event, type) {
    const signal = document.createElement('div');

    // Map type to zSignal classes (Bootstrap compatibility layer)
    const classMap = {
      danger: 'error',    // danger → zSignal-error
      warning: 'warning', // warning → zSignal-warning
      success: 'success', // success → zSignal-success
      info: 'info'        // info → zSignal-info
    };

    const signalType = classMap[type] || 'info';
    signal.className = `zSignal zSignal-${signalType}`;

    // Apply custom classes if provided (from YAML `class` parameter)
    const customClass = event.class || null;
    if (customClass) {
      signal.className += ` ${customClass}`;
    }

    signal.setAttribute('role', 'alert');

    // Add icon based on type
    const icons = {
      danger: '⚠️',
      warning: '⚡',
      success: '✅',
      info: 'ℹ️'
    };

    const icon = icons[type] || '';
    const content = this._sanitizeHTML(event.content);

    // Create content wrapper
    const contentDiv = document.createElement('div');
    contentDiv.innerHTML = icon ? `<strong style="margin-right: 0.5rem;">${icon}</strong>${content}` : content;

    // Create close button (dismissible like Bootstrap)
    const closeBtn = document.createElement('button');
    closeBtn.className = 'close';
    closeBtn.innerHTML = '×';
    closeBtn.setAttribute('aria-label', 'Close');
    closeBtn.onclick = () => {
      signal.style.animation = 'fadeOut 0.3s ease-out';
      setTimeout(() => signal.remove(), 300);
    };

    // Append content and close button
    signal.appendChild(contentDiv);
    signal.appendChild(closeBtn);

    // Apply indent as left margin (minimal inline style for dynamic indentation)
    if (event.indent && event.indent > 0) {
      signal.style.marginLeft = `${event.indent}rem`;
    }

    // Auto-dismiss after 5 seconds with fade-out animation
    setTimeout(() => {
      if (signal.parentElement) {  // Only fade if still in DOM (not manually closed)
        signal.style.animation = 'fadeOut 0.5s ease-out';
        setTimeout(() => signal.remove(), 500);
      }
    }, 5000);

    return signal;
  }

  /**
   * Sanitize HTML to prevent XSS while allowing safe tags
   * @private
   */
  _sanitizeHTML(html) {
    if (!html) {
      return '';
    }

    // Allow common safe tags: <strong>, <em>, <code>, <a>, <br>
    // This is a basic sanitizer - for production, consider using DOMPurify
    const allowedTags = ['strong', 'em', 'code', 'a', 'br', 'span'];

    // Create a temporary div to parse HTML
    const temp = document.createElement('div');
    temp.innerHTML = html;

    // Remove script tags and event handlers
    const scripts = temp.querySelectorAll('script');
    scripts.forEach(script => script.remove());

    // Remove event handler attributes (onclick, onerror, etc.)
    const allElements = temp.querySelectorAll('*');
    allElements.forEach(el => {
      Array.from(el.attributes).forEach(attr => {
        if (attr.name.startsWith('on')) {
          el.removeAttribute(attr.name);
        }
      });

      // Remove elements not in allowed list (except text nodes)
      if (!allowedTags.includes(el.tagName.toLowerCase())) {
        // Keep the text content but remove the tag
        const textContent = el.textContent;
        const textNode = document.createTextNode(textContent);
        el.parentNode.replaceChild(textNode, el);
      }
    });

    return temp.innerHTML;
  }

  /**
   * Render multiple events in sequence
   * @param {Array} events - Array of zDisplay events
   * @param {string} targetZone - Target DOM element ID
   */
  renderBatch(events, targetZone = null) {
    if (!Array.isArray(events)) {
      this.logger.error('[ZDisplayRenderer] renderBatch expects an array');
      return;
    }

    events.forEach(event => {
      try {
        this.render(event, targetZone);
      } catch (error) {
        this.logger.error('[ZDisplayRenderer] Error rendering event:', error, event);
        // Continue with next event
      }
    });
  }

  /**
   * Clear all content from a zone
   * @param {string} targetZone - Target DOM element ID
   */
  clear(targetZone = null) {
    const zone = targetZone || this.defaultZone;
    const container = document.getElementById(zone);

    if (container) {
      this._flush(container);
      this.logger.log(`[ZDisplayRenderer] Cleared zone: ${zone}`);
    } else {
      this.logger.error(`[ZDisplayRenderer] Zone not found: ${zone}`);
    }
  }

  /**
   * Render input request as HTML form
   * @param {Object} inputRequest - Input request event from backend
   * @param {string} targetZone - Target DOM element ID
   */
  renderInputRequest(inputRequest, targetZone = null) {
    const zone = targetZone || this.defaultZone;
    const container = document.getElementById(zone);

    if (!container) {
      this.logger.error(`[ZDisplayRenderer] Cannot render input - zone not found: ${zone}`);
      return;
    }

    // Extract input details
    const requestId = inputRequest.requestId || inputRequest.data?.requestId;
    const inputType = inputRequest.type || inputRequest.data?.type || 'string';
    const prompt = inputRequest.prompt || inputRequest.data?.prompt || 'Enter input:';
    const masked = inputRequest.masked || inputRequest.data?.masked || (inputType === 'password');

    this.logger.log('[ZDisplayRenderer] Rendering input form:', { requestId, inputType, prompt, masked });

    // Create form container
    const form = document.createElement('form');
    form.className = 'zInputForm';
    form.style.cssText = `
      margin: 1rem 0;
      padding: 1rem;
      border: 2px solid var(--color-primary, #00D4FF);
      border-radius: 8px;
      background-color: var(--color-base, #fff);
    `;

    // Create label
    const label = document.createElement('label');
    label.textContent = prompt;
    label.style.cssText = `
      display: block;
      margin-bottom: 0.5rem;
      font-weight: bold;
      color: var(--color-darkgray, #333);
    `;

    // Create input field
    const input = document.createElement('input');
    input.type = masked ? 'password' : 'text';
    input.placeholder = masked ? '••••••••' : 'Type here...';
    input.required = true;
    input.style.cssText = `
      width: 100%;
      padding: 0.5rem;
      margin-bottom: 1rem;
      border: 1px solid var(--color-gray, #ccc);
      border-radius: 4px;
      font-size: 1rem;
    `;

    // Create submit button
    const submitBtn = document.createElement('button');
    submitBtn.type = 'submit';
    submitBtn.textContent = '✓ Submit';
    submitBtn.className = 'zoloButton zBtnPrimary';
    submitBtn.style.cssText = `
      padding: 0.5rem 1.5rem;
      cursor: pointer;
    `;

    // Handle form submission
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const value = input.value.trim();

      this.logger.log('[ZDisplayRenderer] Input submitted:', { requestId, value: masked ? '***' : value });

      // Send input_response back to server (one-way, no response expected)
      if (window.bifrostClient && window.bifrostClient.connection) {
        try {
          const payload = {
            event: 'input_response',
            requestId: requestId,
            value: value
          };
          this.logger.log('[ZDisplayRenderer] Sending input_response:', payload);
          window.bifrostClient.connection.send(JSON.stringify(payload));
          this.logger.log('[ZDisplayRenderer] ✅ Input response sent successfully (one-way)');
        } catch (error) {
          this.logger.error('[ZDisplayRenderer] ❌ Failed to send input response:', error);
        }
      } else {
        this.logger.error('[ZDisplayRenderer] Cannot send input response - bifrostClient not found on window');
      }

      // Replace form with confirmation message
      const confirmation = document.createElement('p');
      confirmation.style.cssText = `
        margin: 1rem 0;
        padding: 0.75rem;
        background-color: var(--color-success-light, #d4edda);
        border: 1px solid var(--color-success, #28a745);
        border-radius: 4px;
        color: var(--color-success-dark, #155724);
      `;
      confirmation.textContent = masked
        ? `✓ Password submitted (${value.length} characters)`
        : `✓ Submitted: ${value}`;

      form.replaceWith(confirmation);
    });

    // Assemble form
    form.appendChild(label);
    form.appendChild(input);
    form.appendChild(submitBtn);

    // Add to container
    container.appendChild(form);

    // Focus input
    input.focus();

    this.logger.log('[ZDisplayRenderer] Input form rendered');
  }

  /**
   * Render selection request as HTML form with radio/checkboxes
   * @param {Object} selectionRequest - Selection request event from backend
   * @param {string} targetZone - Target DOM element ID
   */
  renderSelectionRequest(selectionRequest, targetZone = null) {
    const zone = targetZone || this.defaultZone;
    const container = document.getElementById(zone);

    if (!container) {
      this.logger.error(`[ZDisplayRenderer] Cannot render selection - zone not found: ${zone}`);
      return;
    }

    // Extract selection details
    const requestId = selectionRequest.requestId || selectionRequest.data?.requestId;
    const prompt = selectionRequest.prompt || selectionRequest.data?.prompt || 'Select:';
    const options = selectionRequest.options || selectionRequest.data?.options || [];
    const multi = selectionRequest.multi || selectionRequest.data?.multi || false;
    const defaultVal = selectionRequest.default || selectionRequest.data?.default;

    this.logger.log('[ZDisplayRenderer] Rendering selection form:', { requestId, prompt, options, multi });

    // Create form container
    const form = document.createElement('form');
    form.className = 'zSelectionForm';
    form.style.cssText = `
      margin: 1rem 0;
      padding: 1rem;
      border: 2px solid var(--color-primary, #00D4FF);
      border-radius: 8px;
      background-color: var(--color-base, #fff);
    `;

    // Create label
    const label = document.createElement('label');
    label.textContent = prompt;
    label.style.cssText = `
      display: block;
      margin-bottom: 1rem;
      font-weight: bold;
      color: var(--color-darkgray, #333);
    `;
    form.appendChild(label);

    // Create options container
    const optionsContainer = document.createElement('div');
    optionsContainer.style.cssText = `
      margin-bottom: 1rem;
      max-height: 300px;
      overflow-y: auto;
    `;

    // Create option elements
    const inputType = multi ? 'checkbox' : 'radio';
    const inputName = `selection_${requestId}`;

    options.forEach((option, index) => {
      const optionDiv = document.createElement('div');
      optionDiv.style.cssText = `
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-radius: 4px;
        cursor: pointer;
        display: flex;
        align-items: center;
      `;
      optionDiv.onmouseover = () => optionDiv.style.backgroundColor = 'var(--color-lightgray, #f8f9fa)';
      optionDiv.onmouseout = () => optionDiv.style.backgroundColor = 'transparent';

      const input = document.createElement('input');
      input.type = inputType;
      input.name = inputName;
      input.value = option;
      input.id = `${inputName}_${index}`;
      input.style.cssText = `
        margin-right: 0.5rem;
        cursor: pointer;
      `;

      // Set default selection
      if (defaultVal) {
        if (multi && Array.isArray(defaultVal)) {
          input.checked = defaultVal.includes(option);
        } else if (!multi && defaultVal === option) {
          input.checked = true;
        }
      }

      const optionLabel = document.createElement('label');
      optionLabel.htmlFor = input.id;
      optionLabel.textContent = option;
      optionLabel.style.cssText = `
        cursor: pointer;
        flex: 1;
      `;

      optionDiv.appendChild(input);
      optionDiv.appendChild(optionLabel);
      optionDiv.onclick = () => input.checked = !input.checked;

      optionsContainer.appendChild(optionDiv);
    });

    form.appendChild(optionsContainer);

    // Create submit button
    const submitBtn = document.createElement('button');
    submitBtn.type = 'submit';
    submitBtn.textContent = '✓ Submit';
    submitBtn.className = 'zoloButton zBtnPrimary';
    submitBtn.style.cssText = `
      padding: 0.5rem 1.5rem;
      cursor: pointer;
    `;
    form.appendChild(submitBtn);

    // Handle form submission
    form.addEventListener('submit', (e) => {
      e.preventDefault();

      // Get selected values
      const selectedInputs = form.querySelectorAll(`input[name="${inputName}"]:checked`);
      const selectedValues = Array.from(selectedInputs).map(input => input.value);

      // Return appropriate format
      const value = multi ? selectedValues : (selectedValues[0] || null);

      this.logger.log('[ZDisplayRenderer] Selection submitted:', { requestId, value });

      // Send selection_response back to server (one-way)
      if (window.bifrostClient && window.bifrostClient.connection) {
        try {
          const payload = {
            event: 'input_response',
            requestId: requestId,
            value: value
          };
          this.logger.log('[ZDisplayRenderer] Sending selection response:', payload);
          window.bifrostClient.connection.send(JSON.stringify(payload));
          this.logger.log('[ZDisplayRenderer] ✅ Selection response sent successfully');
        } catch (error) {
          this.logger.error('[ZDisplayRenderer] ❌ Failed to send selection response:', error);
        }
      } else {
        this.logger.error('[ZDisplayRenderer] Cannot send selection response - bifrostClient not found');
      }

      // Replace form with confirmation message
      const confirmation = document.createElement('p');
      confirmation.style.cssText = `
        margin: 1rem 0;
        padding: 0.75rem;
        background-color: var(--color-success-light, #d4edda);
        border: 1px solid var(--color-success, #28a745);
        border-radius: 4px;
        color: var(--color-success-dark, #155724);
      `;

      if (multi) {
        confirmation.textContent = selectedValues.length > 0
          ? `✓ Selected: ${selectedValues.join(', ')}`
          : '✓ No selections made';
      } else {
        confirmation.textContent = value ? `✓ Selected: ${value}` : '✓ No selection made';
      }

      form.replaceWith(confirmation);
    });

    // Add to container
    container.appendChild(form);

    this.logger.log('[ZDisplayRenderer] Selection form rendered');
  }

  renderButtonRequest(buttonRequest, targetZone = null) {
    const zone = targetZone || this.defaultZone;
    const container = document.getElementById(zone);

    if (!container) {
      this.logger.error(`[ZDisplayRenderer] Cannot render button - zone not found: ${zone}`);
      return;
    }

    // Extract button details
    const requestId = buttonRequest.requestId || buttonRequest.data?.requestId;
    const label = buttonRequest.prompt || buttonRequest.data?.prompt || 'Click Me';
    const action = buttonRequest.action || buttonRequest.data?.action || null;
    const color = buttonRequest.color || buttonRequest.data?.color || 'primary';
    const style = buttonRequest.style || buttonRequest.data?.style || 'default';

    this.logger.log('[ZDisplayRenderer] Rendering button:', { requestId, label, action, color, style });

    // Create button container
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'zButtonContainer';
    buttonContainer.style.cssText = `
      margin: 1rem 0;
      padding: 1rem;
      display: flex;
      align-items: center;
      gap: 1rem;
    `;

    // Create the button with zTheme classes
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = label;

    // Apply zTheme button classes based on color
    const colorClass = {
      'primary': 'zBtnPrimary',
      'success': 'zBtnSuccess',
      'danger': 'zBtnDanger',
      'warning': 'zBtnWarning',
      'info': 'zBtnInfo',
      'secondary': 'zBtnSecondary'
    }[color] || 'zBtnPrimary';

    button.className = `zoloButton ${colorClass}`;
    button.style.cssText = `
      padding: 0.5rem 1.5rem;
      font-size: 1rem;
      cursor: pointer;
      transition: transform 0.1s ease;
    `;

    // Add hover effect
    button.addEventListener('mouseenter', () => {
      button.style.transform = 'scale(1.02)';
    });
    button.addEventListener('mouseleave', () => {
      button.style.transform = 'scale(1)';
    });

    // Handle button click
    button.addEventListener('click', () => {
      this.logger.log('[ZDisplayRenderer] Button clicked:', label);

      // Send response back to server (True = clicked)
      if (window.bifrostClient && window.bifrostClient.connection) {
        window.bifrostClient.connection.send(JSON.stringify({
          event: 'input_response',
          requestId: requestId,
          value: true  // Button clicked = True
        }));
        this.logger.log('[ZDisplayRenderer] Button response sent');
      }

      // Replace button with confirmation
      const confirmation = document.createElement('p');
      confirmation.style.cssText = `
        margin: 0;
        padding: 0.5rem 1rem;
        color: var(--color-success, #10b981);
        font-weight: 500;
      `;
      confirmation.textContent = `✓ ${label} clicked!`;

      buttonContainer.replaceWith(confirmation);
    });

    // Add cancel button (optional - for explicit "No" response)
    const cancelBtn = document.createElement('button');
    cancelBtn.type = 'button';
    cancelBtn.textContent = 'Cancel';
    cancelBtn.className = 'zoloButton zBtnSecondary';
    cancelBtn.style.cssText = `
      padding: 0.5rem 1.5rem;
      font-size: 1rem;
      cursor: pointer;
      transition: transform 0.1s ease;
    `;

    cancelBtn.addEventListener('mouseenter', () => {
      cancelBtn.style.transform = 'scale(1.02)';
    });
    cancelBtn.addEventListener('mouseleave', () => {
      cancelBtn.style.transform = 'scale(1)';
    });

    cancelBtn.addEventListener('click', () => {
      this.logger.log('[ZDisplayRenderer] Button cancelled:', label);

      // Send response back to server (False = cancelled)
      if (window.bifrostClient && window.bifrostClient.connection) {
        window.bifrostClient.connection.send(JSON.stringify({
          event: 'input_response',
          requestId: requestId,
          value: false  // Button cancelled = False
        }));
        this.logger.log('[ZDisplayRenderer] Button cancel response sent');
      }

      // Replace button with confirmation
      const confirmation = document.createElement('p');
      confirmation.style.cssText = `
        margin: 0;
        padding: 0.5rem 1rem;
        color: var(--color-info, #3b82f6);
        font-weight: 500;
      `;
      confirmation.textContent = `○ ${label} cancelled`;

      buttonContainer.replaceWith(confirmation);
    });

    // Add buttons to container
    buttonContainer.appendChild(button);
    buttonContainer.appendChild(cancelBtn);

    // Add to page
    container.appendChild(buttonContainer);

    this.logger.log('[ZDisplayRenderer] Button rendered');
  }

  renderSwiperInit(swiperEvent) {
    const zone = this.defaultZone;
    const container = document.getElementById(zone);

    if (!container) {
      this.logger.error(`[ZDisplayRenderer] Cannot render swiper - zone not found: ${zone}`);
      return;
    }

    // Extract swiper data
    const swiperId = swiperEvent.swiperId || `swiper-${Date.now()}`;
    const label = swiperEvent.label || 'Swiper';
    const slides = swiperEvent.slides || [];
    const currentSlide = swiperEvent.currentSlide || 0;
    const totalSlides = swiperEvent.totalSlides || slides.length;
    const autoAdvance = swiperEvent.autoAdvance !== false;
    const delay = swiperEvent.delay || 3;
    const loop = swiperEvent.loop !== false;

    this.logger.log('[ZDisplayRenderer] Rendering swiper:', { swiperId, label, totalSlides });

    // Create swiper container
    const swiperContainer = document.createElement('div');
    swiperContainer.className = 'zSwiper';
    swiperContainer.setAttribute('data-swiper-id', swiperId);
    swiperContainer.style.cssText = `
      margin: 1.5rem 0;
      padding: 1.5rem;
      border: 2px solid var(--color-primary);
      border-radius: 8px;
      background-color: var(--color-base);
    `;

    // Swiper label
    if (label) {
      const labelElement = document.createElement('h4');
      labelElement.textContent = label;
      labelElement.style.cssText = `
        margin: 0 0 1rem 0;
        color: var(--color-primary);
        font-weight: 600;
      `;
      swiperContainer.appendChild(labelElement);
    }

    // Slide content container
    const slideContent = document.createElement('div');
    slideContent.className = 'zSwiper-content';
    slideContent.style.cssText = `
      min-height: 200px;
      padding: 1rem;
      background-color: var(--color-lightgray);
      border-radius: 4px;
      margin-bottom: 1rem;
      white-space: pre-wrap;
      font-family: monospace;
    `;
    slideContent.textContent = slides[currentSlide] || 'No content';
    swiperContainer.appendChild(slideContent);

    // Navigation controls
    const navContainer = document.createElement('div');
    navContainer.style.cssText = `
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 1rem;
    `;

    // Previous button
    const prevBtn = document.createElement('button');
    prevBtn.textContent = '◀ Previous';
    prevBtn.className = 'zoloButton zBtnSecondary';
    prevBtn.disabled = !loop && currentSlide === 0;
    prevBtn.onclick = () => {
      const newSlide = currentSlide > 0 ? currentSlide - 1 : (loop ? totalSlides - 1 : 0);
      this._updateSwiper(swiperId, slides, newSlide, totalSlides);
    };

    // Slide indicator
    const indicator = document.createElement('span');
    indicator.className = 'zSwiper-indicator';
    indicator.textContent = `${currentSlide + 1} / ${totalSlides}`;
    indicator.style.cssText = `
      color: var(--color-darkgray);
      font-weight: 500;
    `;

    // Next button
    const nextBtn = document.createElement('button');
    nextBtn.textContent = 'Next ▶';
    nextBtn.className = 'zoloButton zBtnPrimary';
    nextBtn.disabled = !loop && currentSlide === totalSlides - 1;
    nextBtn.onclick = () => {
      const newSlide = currentSlide < totalSlides - 1 ? currentSlide + 1 : (loop ? 0 : currentSlide);
      this._updateSwiper(swiperId, slides, newSlide, totalSlides);
    };

    navContainer.appendChild(prevBtn);
    navContainer.appendChild(indicator);
    navContainer.appendChild(nextBtn);
    swiperContainer.appendChild(navContainer);

    // Auto-advance
    if (autoAdvance) {
      const autoAdvanceInterval = setInterval(() => {
        const currentContainer = document.querySelector(`[data-swiper-id="${swiperId}"]`);
        if (!currentContainer) {
          clearInterval(autoAdvanceInterval);
          return;
        }
        const currentIndicator = currentContainer.querySelector('.zSwiper-indicator');
        const currentSlideNum = parseInt(currentIndicator.textContent.split('/')[0].trim()) - 1;
        const newSlide = currentSlideNum < totalSlides - 1 ? currentSlideNum + 1 : (loop ? 0 : currentSlideNum);
        this._updateSwiper(swiperId, slides, newSlide, totalSlides);
      }, delay * 1000);
    }

    // Add to container
    container.appendChild(swiperContainer);

    this.logger.log('[ZDisplayRenderer] Swiper rendered');
  }

  _updateSwiper(swiperId, slides, newSlideIndex, totalSlides) {
    const swiperContainer = document.querySelector(`[data-swiper-id="${swiperId}"]`);
    if (!swiperContainer) {
      return;
    }

    const slideContent = swiperContainer.querySelector('.zSwiper-content');
    const indicator = swiperContainer.querySelector('.zSwiper-indicator');
    const prevBtn = swiperContainer.querySelectorAll('button')[0];
    const nextBtn = swiperContainer.querySelectorAll('button')[1];

    // Update content
    slideContent.textContent = slides[newSlideIndex] || 'No content';
    indicator.textContent = `${newSlideIndex + 1} / ${totalSlides}`;

    // Update button states (if not looping)
    const loop = prevBtn.disabled === false && newSlideIndex === 0;
    prevBtn.disabled = !loop && newSlideIndex === 0;
    nextBtn.disabled = !loop && newSlideIndex === totalSlides - 1;

    this.logger.log('[ZDisplayRenderer] Swiper updated to slide:', newSlideIndex + 1);
  }
}

