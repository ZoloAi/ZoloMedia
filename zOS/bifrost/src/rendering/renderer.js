/**
 * ═══════════════════════════════════════════════════════════════
 * Renderer Module - Auto-Rendering with zTheme
 * ═══════════════════════════════════════════════════════════════
 */

export class Renderer {
  constructor(logger) {
    this.logger = logger;
  }

  /**
   * Render data as a table with zTheme styling
   */
  renderTable(data, container, _options = {}) {
    const element = this._getElement(container);
    if (!element) {
      return;
    }

    if (!Array.isArray(data) || data.length === 0) {
      element.innerHTML = '<p class="zEmpty">No data to display</p>';
      return;
    }

    const columns = Object.keys(data[0]);
    let html = '<table class="zTable zTable-striped zTable-hover">';

    // Table header
    html += '<thead><tr>';
    columns.forEach(col => {
      html += `<th>${this._formatColumnName(col)}</th>`;
    });
    html += '</tr></thead>';

    // Table body
    html += '<tbody>';
    data.forEach(row => {
      html += '<tr>';
      columns.forEach(col => {
        html += `<td>${this._escapeHtml(row[col])}</td>`;
      });
      html += '</tr>';
    });
    html += '</tbody></table>';

    element.innerHTML = html;
    this.logger.log('✅ Table rendered', { rows: data.length, columns: columns.length });
  }

  /**
   * Render a menu with buttons
   */
  renderMenu(items, container) {
    const element = this._getElement(container);
    if (!element) {
      return;
    }

    let html = '<div class="zMenu">';
    items.forEach((item, index) => {
      const icon = item.icon || '';
      const variant = item.variant || '';
      html += `<button class="zoloButton ${variant}" data-action="${index}">
        ${icon} ${item.label}
      </button>`;
    });
    html += '</div>';

    element.innerHTML = html;

    // Attach event listeners
    element.querySelectorAll('button[data-action]').forEach((btn, index) => {
      btn.addEventListener('click', () => {
        if (items[index].action) {
          items[index].action();
        }
      });
    });

    this.logger.log('✅ Menu rendered', { items: items.length });
  }

  /**
   * Render a form with zTheme styling
   */
  renderForm(fields, container, onSubmit) {
    const element = this._getElement(container);
    if (!element) {
      return;
    }

    let html = '<form class="zForm">';

    fields.forEach(field => {
      html += '<div class="zForm-group">';
      html += `<label for="${field.name}">${field.label}</label>`;

      if (field.type === 'textarea') {
        html += `<textarea id="${field.name}" name="${field.name}" 
                  class="zInput" ${field.required ? 'required' : ''}
                  placeholder="${field.placeholder || ''}"></textarea>`;
      } else {
        html += `<input type="${field.type || 'text'}" id="${field.name}" 
                 name="${field.name}" class="zInput" 
                 ${field.required ? 'required' : ''}
                 placeholder="${field.placeholder || ''}">`;
      }

      html += '</div>';
    });

    html += '<button type="submit" class="zoloButton zBtn-primary">Submit</button>';
    html += '</form>';

    element.innerHTML = html;

    // Attach submit handler
    const form = element.querySelector('form');
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const formData = new FormData(form);
      const data = Object.fromEntries(formData.entries());
      if (onSubmit) {
        onSubmit(data);
      }
    });

    this.logger.log('✅ Form rendered', { fields: fields.length });
  }

  /**
   * Render a message/alert
   */
  renderMessage(text, type = 'info', container, duration = 5000) {
    const element = this._getElement(container);
    if (!element) {
      return;
    }

    const typeClass = {
      'success': 'zAlert-success',
      'error': 'zAlert-danger',
      'warning': 'zAlert-warning',
      'info': 'zAlert-info'
    }[type] || 'zAlert-info';

    const msgDiv = document.createElement('div');
    msgDiv.className = `zAlert ${typeClass}`;
    msgDiv.textContent = text;

    element.insertBefore(msgDiv, element.firstChild);

    if (duration > 0) {
      setTimeout(() => msgDiv.remove(), duration);
    }

    this.logger.log('✅ Message rendered', { type, text });
  }

  /**
   * Render a progress bar
   * @param {string} progressId - Unique ID for this progress bar
   * @param {number} current - Current progress value
   * @param {number} total - Total value (null for indeterminate)
   * @param {object} options - { label, color, showPercentage, showETA, size }
   * @param {string|Element} container - Container selector or element
   */
  renderProgressBar(progressId, current, total, options = {}, container) {
    const element = this._getElement(container);
    if (!element) {
      return;
    }

    const {
      label = 'Processing',
      color = '',
      showPercentage = true,
      showETA = false,
      size = '',
      eta = null
    } = options;

    // Calculate percentage
    const percentage = total > 0 ? Math.round((current / total) * 100) : 0;
    const isIndeterminate = total === null || total === 0;

    // Build classes
    const classes = ['zProgress'];
    if (color) {
      classes.push(`zProgress-${color}`);
    }
    if (size) {
      classes.push(`zProgress-${size}`);
    }
    if (isIndeterminate) {
      classes.push('zProgress-indeterminate');
    }

    // Check if progress bar already exists
    let progressDiv = element.querySelector(`[data-progress-id="${progressId}"]`);

    if (!progressDiv) {
      // Create new progress bar
      progressDiv = document.createElement('div');
      progressDiv.className = classes.join(' ');
      progressDiv.setAttribute('data-progress-id', progressId);

      let html = '<div class="zProgress-label">';
      html += `<span>${this._escapeHtml(label)}</span>`;
      html += '<span class="zProgress-stats"></span>';
      html += '</div>';
      html += '<div class="zProgress-track">';
      html += '<div class="zProgress-fill"></div>';
      html += '</div>';

      progressDiv.innerHTML = html;
      element.appendChild(progressDiv);
    } else {
      // Update existing progress bar classes
      progressDiv.className = classes.join(' ');
    }

    // Update stats
    const statsEl = progressDiv.querySelector('.zProgress-stats');
    let statsText = '';
    if (showPercentage && !isIndeterminate) {
      statsText += `${percentage}%`;
    }
    if (showETA && eta) {
      statsText += statsText ? ` • ETA: ${eta}` : `ETA: ${eta}`;
    }
    statsEl.textContent = statsText;

    // Update fill
    const fillEl = progressDiv.querySelector('.zProgress-fill');
    if (isIndeterminate) {
      fillEl.style.width = '100%';
    } else {
      fillEl.style.width = `${percentage}%`;
    }

    this.logger.log('✅ Progress bar rendered', { progressId, current, total, percentage });
  }

  /**
   * Update an existing progress bar
   * @param {string} progressId - Unique ID of the progress bar
   * @param {number} current - New current value
   * @param {object} options - Optional updates { eta }
   * @param {string|Element} container - Container selector or element
   */
  updateProgress(progressId, current, options = {}, container) {
    const element = this._getElement(container);
    if (!element) {
      return;
    }

    const progressDiv = element.querySelector(`[data-progress-id="${progressId}"]`);
    if (!progressDiv) {
      this.logger.log('❌ Progress bar not found:', progressId);
      return;
    }

    // Get total from data attribute or calculate from width
    const fillEl = progressDiv.querySelector('.zProgress-fill');
    const isIndeterminate = progressDiv.classList.contains('zProgress-indeterminate');

    if (!isIndeterminate) {
      // Try to extract total from current percentage
      const currentWidth = parseFloat(fillEl.style.width) || 0;
      const total = currentWidth > 0 ? Math.round((current * 100) / currentWidth) : 100;

      const percentage = Math.round((current / total) * 100);
      fillEl.style.width = `${percentage}%`;

      // Update stats
      const statsEl = progressDiv.querySelector('.zProgress-stats');
      let statsText = `${percentage}%`;
      if (options.eta) {
        statsText += ` • ETA: ${options.eta}`;
      }
      statsEl.textContent = statsText;
    }

    this.logger.log('✅ Progress updated', { progressId, current });
  }

  /**
   * Remove a progress bar
   * @param {string} progressId - Unique ID of the progress bar
   * @param {string|Element} container - Container selector or element
   */
  removeProgress(progressId, container) {
    const element = this._getElement(container);
    if (!element) {
      return;
    }

    const progressDiv = element.querySelector(`[data-progress-id="${progressId}"]`);
    if (progressDiv) {
      progressDiv.remove();
      this.logger.log('✅ Progress bar removed', { progressId });
    }
  }

  /**
   * Render a spinner
   * @param {string} spinnerId - Unique ID for this spinner
   * @param {string} label - Spinner label text
   * @param {string} style - Spinner style (dots, line, arc, arrow, bouncingBall, simple, circle)
   * @param {object} options - { size, center, inline }
   * @param {string|Element} container - Container selector or element
   */
  renderSpinner(spinnerId, label, style = 'dots', options = {}, container) {
    const element = this._getElement(container);
    if (!element) {
      return;
    }

    const {
      size = '',
      center = false,
      inline = false
    } = options;

    // Build classes
    const classes = ['zSpinner'];
    if (size) {
      classes.push(`zSpinner-${size}`);
    }
    if (center) {
      classes.push('zSpinner-center');
    }
    if (inline) {
      classes.push('zSpinner-inline');
    }

    // Check if spinner already exists
    let spinnerDiv = element.querySelector(`[data-spinner-id="${spinnerId}"]`);

    if (!spinnerDiv) {
      // Create new spinner
      spinnerDiv = document.createElement('div');
      spinnerDiv.className = classes.join(' ');
      spinnerDiv.setAttribute('data-spinner-id', spinnerId);

      let html = '';
      if (label) {
        html += `<div class="zSpinner-label">${this._escapeHtml(label)}</div>`;
      }

      // Add animation based on style
      if (style === 'circle') {
        html += '<div class="zSpinner-animation"><div class="zSpinner-circle"></div></div>';
      } else {
        html += `<div class="zSpinner-animation zSpinner-${style}"></div>`;
      }

      spinnerDiv.innerHTML = html;
      element.appendChild(spinnerDiv);
    }

    this.logger.log('✅ Spinner rendered', { spinnerId, label, style });
  }

  /**
   * Remove a spinner
   * @param {string} spinnerId - Unique ID of the spinner
   * @param {string|Element} container - Container selector or element
   */
  removeSpinner(spinnerId, container) {
    const element = this._getElement(container);
    if (!element) {
      return;
    }

    const spinnerDiv = element.querySelector(`[data-spinner-id="${spinnerId}"]`);
    if (spinnerDiv) {
      spinnerDiv.remove();
      this.logger.log('✅ Spinner removed', { spinnerId });
    }
  }

  /**
   * Get element from selector or element
   * @private
   */
  _getElement(container) {
    const element = typeof container === 'string'
      ? document.querySelector(container)
      : container;

    if (!element) {
      this.logger.log('❌ Container not found:', container);
    }

    return element;
  }

  /**
   * Format column name for display
   * @private
   */
  _formatColumnName(name) {
    return name
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase());
  }

  /**
   * Escape HTML to prevent XSS
   * @private
   */
  _escapeHtml(text) {
    if (text === null || text === undefined) {
      return '';
    }
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
  }
}

