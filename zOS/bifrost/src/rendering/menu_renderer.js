/**
 * MenuRenderer - Handles menu rendering and interaction in Bifrost mode
 *
 * This module provides:
 * - Menu HTML rendering with zTheme classes
 * - Click event handlers for menu options
 * - Keyboard navigation support
 * - WebSocket communication for menu selection
 *
 * Integrates with:
 * - zDisplay (via zdisplay_orchestrator.js)
 * - BifrostClient (for WebSocket messaging)
 * - zTheme (for consistent styling)
 */

export class MenuRenderer {
  constructor(client) {
    this.client = client;
    this.logger = client.logger;
  }

  /**
   * Render menu from backend menu event (full-page menu)
   * @param {Object} message - Menu event data from backend
   */
  renderMenu(message) {
    this.logger.log('[MenuRenderer] 📋 Rendering menu:', message);
    this.logger.log('[MenuRenderer] Rendering menu', message);

    const { menu_key, options, breadcrumbs, _current_file, _current_block } = message;

    // Get the zVaF content element
    const contentElement = this.client._zVaFElement;
    if (!contentElement) {
      this.logger.error('[MenuRenderer] ❌ zVaF element not found');
      return;
    }

    // Clear existing content
    contentElement.innerHTML = '';

    // Render breadcrumbs if available
    if (breadcrumbs && Object.keys(breadcrumbs).length > 0) {
      this._renderBreadcrumbs(breadcrumbs, contentElement);
    }

    // Render menu
    const menuHtml = this._createMenuHTML(menu_key, options);
    contentElement.innerHTML += menuHtml;

    // Attach event handlers
    this._attachMenuHandlers(menu_key, options);

    this.logger.log('[MenuRenderer] ✅ Menu rendered successfully');
  }

  /**
   * Render menu inline (within a specific container, e.g., dashboard panel)
   * @param {Object} menuData - Menu data { menu_key, options, title, allow_back }
   * @param {HTMLElement} container - Container element to render menu into
   */
  renderMenuInline(menuData, container) {
    this.logger.log('[MenuRenderer] 📋 Rendering inline menu:', menuData);
    this.logger.log('[MenuRenderer] Rendering inline menu', menuData);

    const { menu_key, options, title, _allow_back } = menuData;

    // Create menu HTML
    const menuHtml = this._createMenuHTML(menu_key || 'Menu', options, title);

    // Insert into container
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = menuHtml;
    const menuElement = tempDiv.firstElementChild;

    if (menuElement && container) {
      container.appendChild(menuElement);

      // Attach event handlers
      this._attachMenuHandlers(menu_key || 'Menu', options, menuElement);

      this.logger.log('[MenuRenderer] ✅ Inline menu rendered successfully');
    } else {
      this.logger.error('[MenuRenderer] ❌ Failed to render inline menu');
    }
  }

  /**
   * Create menu HTML with zTheme classes
   * @private
   */
  _createMenuHTML(menuKey, options, customTitle = null) {
    const menuTitle = customTitle || menuKey.replace(/[*~]/g, '').trim() || 'Menu';

    return `
      <div class="zMenu-container zCard zp-4 zmy-4" data-menu="${this._escapeHtml(menuKey)}">
        <h2 class="zCard-title zmb-4">${this._escapeHtml(menuTitle)}</h2>
        <div class="zMenu-options">
          ${options.map((opt, idx) => this._createOptionHTML(opt, idx)).join('')}
        </div>
      </div>
    `;
  }

  /**
   * Create HTML for a single menu option
   * @private
   */
  _createOptionHTML(option, index) {
    const label = option.label || option.key || option;
    const key = option.key || option;

    return `
      <div class="zMenu-option zmb-2" data-key="${this._escapeHtml(key)}">
        <button class="zBtn zBtn-outline-primary w-100 text-start zp-3" data-index="${index}">
          <span class="zBadge zBadge-secondary me-2">${index}</span>
          ${this._escapeHtml(label.replace(/[*~^$]/g, ''))}
        </button>
      </div>
    `;
  }

  /**
   * Render breadcrumbs
   * @private
   */
  _renderBreadcrumbs(breadcrumbs, container) {
    const breadcrumbsHtml = `
      <nav aria-label="breadcrumb" class="zmb-3">
        <ol class="breadcrumb">
          ${Object.entries(breadcrumbs).map(([_scope, trail]) => `
            <li class="breadcrumb-item active">${this._escapeHtml(trail)}</li>
          `).join('')}
        </ol>
      </nav>
    `;
    container.innerHTML = breadcrumbsHtml;
  }

  /**
   * Attach click and keyboard handlers to menu options
   * @private
   */
  _attachMenuHandlers(menuKey, options, containerElement = null) {
    // If container is provided, scope query to it; otherwise use document
    const root = containerElement || document;
    const optionButtons = root.querySelectorAll('.zMenu-option button');

    optionButtons.forEach((button, _idx) => {
      button.addEventListener('click', () => {
        const optionDiv = button.closest('.zMenu-option');
        const selectedKey = optionDiv.dataset.key;

        this.logger.log('[MenuRenderer] 🎯 Menu selection:', selectedKey);
        this.logger.log('[MenuRenderer] Menu selection', { menu: menuKey, selected: selectedKey });

        // Visual feedback
        button.classList.add('active');
        button.disabled = true;

        // Send selection to backend
        this._sendMenuSelection(menuKey, selectedKey);
      });
    });

    // Keyboard navigation (0-9 for options)
    const keydownHandler = (e) => {
      const num = parseInt(e.key);
      if (!isNaN(num) && num < optionButtons.length) {
        optionButtons[num].click();
        // Remove handler after selection
        document.removeEventListener('keydown', keydownHandler);
      }
    };

    document.addEventListener('keydown', keydownHandler);
    this.logger.log('[MenuRenderer] ⌨️  Keyboard navigation enabled (0-9)');
  }

  /**
   * Send menu selection to backend via WebSocket
   * @private
   */
  _sendMenuSelection(menuKey, selected) {
    const message = {
      event: 'menu_selection',
      menu_key: menuKey,
      selected: selected
    };

    this.logger.log('[MenuRenderer] 📤 Sending menu selection to backend:', message);
    this.client.send(message);
  }

  /**
   * Escape HTML to prevent XSS
   * @private
   */
  _escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

