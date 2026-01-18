/**
 * ═══════════════════════════════════════════════════════════════
 * Error Display Module - Visual Error Boundaries for UI
 * ═══════════════════════════════════════════════════════════════
 */

export class ErrorDisplay {
  constructor(options = {}) {
    this.containerId = options.containerId || 'bifrost-errors';
    this.autoCreate = options.autoCreate !== false; // Default true
    this.maxErrors = options.maxErrors || 5; // Max errors to show
    this.autoDismiss = options.autoDismiss || 10000; // Auto-dismiss after 10s
    this.position = options.position || 'top-right'; // top-right, top-left, bottom-right, bottom-left

    this.errors = [];
    this.container = null;

    if (this.autoCreate) {
      this._createContainer();
    }
  }

  /**
   * Create error container if it doesn't exist
   * @private
   */
  _createContainer() {
    // Check if container already exists
    this.container = document.getElementById(this.containerId);

    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = this.containerId;
      this.container.className = 'bifrost-error-container';

      // Position styles
      const positions = {
        'top-right': 'top: 1rem; right: 1rem;',
        'top-left': 'top: 1rem; left: 1rem;',
        'bottom-right': 'bottom: 1rem; right: 1rem;',
        'bottom-left': 'bottom: 1rem; left: 1rem;'
      };

      this.container.style.cssText = `
        position: fixed;
        ${positions[this.position] || positions['top-right']}
        z-index: 10000;
        max-width: 400px;
        pointer-events: none;
      `;

      document.body.appendChild(this.container);
    }
  }

  /**
   * Display an error in the UI
   */
  show(errorInfo) {
    if (!this.container) {
      this._createContainer();
    }

    // Create error element
    const errorEl = document.createElement('div');
    errorEl.className = 'bifrost-error';
    errorEl.style.cssText = `
      background: #fee;
      border-left: 4px solid #c33;
      padding: 1rem;
      margin-bottom: 0.5rem;
      border-radius: 4px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.15);
      pointer-events: auto;
      animation: slideIn 0.3s ease-out;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 0.875rem;
      line-height: 1.5;
    `;

    // Error title
    const title = document.createElement('div');
    title.style.cssText = `
      font-weight: 600;
      color: #c33;
      margin-bottom: 0.5rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    `;
    title.innerHTML = `
      <span>⚠️ ${this._getErrorTitle(errorInfo)}</span>
      <button style="
        background: none;
        border: none;
        color: #c33;
        cursor: pointer;
        font-size: 1.2rem;
        padding: 0;
        margin-left: 0.5rem;
        line-height: 1;
      " title="Dismiss">×</button>
    `;

    // Error message
    const message = document.createElement('div');
    message.style.cssText = 'color: #600; margin-bottom: 0.5rem;';
    message.textContent = errorInfo.message || 'An error occurred';

    // Error details (collapsible)
    const details = document.createElement('details');
    details.style.cssText = 'color: #800; font-size: 0.75rem; margin-top: 0.5rem;';
    details.innerHTML = `
      <summary style="cursor: pointer; user-select: none;">Show details</summary>
      <pre style="
        margin-top: 0.5rem;
        padding: 0.5rem;
        background: #fff;
        border-radius: 3px;
        overflow-x: auto;
        font-size: 0.7rem;
        white-space: pre-wrap;
        word-wrap: break-word;
      ">${this._formatStack(errorInfo)}</pre>
    `;

    errorEl.appendChild(title);
    errorEl.appendChild(message);
    errorEl.appendChild(details);

    // Add dismiss handler
    const dismissBtn = title.querySelector('button');
    dismissBtn.onclick = () => this._dismissError(errorEl);

    // Add to container
    this.container.appendChild(errorEl);
    this.errors.push(errorEl);

    // Remove oldest error if we exceed max
    if (this.errors.length > this.maxErrors) {
      const oldest = this.errors.shift();
      if (oldest && oldest.parentNode) {
        oldest.remove();
      }
    }

    // Auto-dismiss after timeout
    if (this.autoDismiss) {
      setTimeout(() => this._dismissError(errorEl), this.autoDismiss);
    }

    // Add slide-in animation
    this._addAnimationStyles();
  }

  /**
   * Dismiss an error
   * @private
   */
  _dismissError(errorEl) {
    if (!errorEl || !errorEl.parentNode) {
      return;
    }

    // Fade out animation
    errorEl.style.animation = 'fadeOut 0.3s ease-out';

    setTimeout(() => {
      if (errorEl.parentNode) {
        errorEl.remove();
      }
      const index = this.errors.indexOf(errorEl);
      if (index > -1) {
        this.errors.splice(index, 1);
      }
    }, 300);
  }

  /**
   * Get error title based on error type
   * @private
   */
  _getErrorTitle(errorInfo) {
    if (errorInfo.type === 'hook_error') {
      return `Hook Error: ${errorInfo.hookName}`;
    }
    if (errorInfo.type === 'render_error') {
      return 'Rendering Error';
    }
    if (errorInfo.type === 'connection_error') {
      return 'Connection Error';
    }
    return 'BifrostClient Error';
  }

  /**
   * Format error stack for display
   * @private
   */
  _formatStack(errorInfo) {
    if (errorInfo.stack) {
      return errorInfo.stack;
    }
    if (errorInfo.error && errorInfo.error.stack) {
      return errorInfo.error.stack;
    }
    return JSON.stringify(errorInfo, null, 2);
  }

  /**
   * Add animation styles to document
   * @private
   */
  _addAnimationStyles() {
    if (document.getElementById('bifrost-error-styles')) {
      return;
    }

    const style = document.createElement('style');
    style.id = 'bifrost-error-styles';
    style.textContent = `
      @keyframes slideIn {
        from {
          transform: translateX(100%);
          opacity: 0;
        }
        to {
          transform: translateX(0);
          opacity: 1;
        }
      }
      
      @keyframes fadeOut {
        from {
          opacity: 1;
        }
        to {
          opacity: 0;
        }
      }
    `;
    document.head.appendChild(style);
  }

  /**
   * Clear all errors
   */
  clearAll() {
    this.errors.forEach(errorEl => {
      if (errorEl.parentNode) {
        errorEl.remove();
      }
    });
    this.errors = [];
  }

  /**
   * Destroy error display (remove container)
   */
  destroy() {
    this.clearAll();
    if (this.container && this.container.parentNode) {
      this.container.remove();
    }
    this.container = null;
  }
}

