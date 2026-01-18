/**
 * DashboardRenderer - Render dashboard with sidebar navigation
 *
 * Extracted from bifrost_client.js (lines 2270-2423)
 * Refactored to use primitives-first architecture
 *
 * Features:
 * - Sidebar navigation with Bootstrap Icons
 * - Panel switching and loading
 * - Metadata fetching from backend
 * - Active state management
 * - WebSocket-based panel loading
 */

import { createDiv } from './primitives/generic_containers.js';
import { createList, createListItem } from './primitives/lists_primitives.js';
import { createLink } from './primitives/interactive_primitives.js';

export default class DashboardRenderer {
  /**
   * @param {Object} logger - Logger instance
   * @param {Object} client - BifrostClient instance (for WebSocket communication)
   */
  constructor(logger, client) {
    this.logger = logger;
    this.client = client;
  }

  /**
   * Render dashboard with sidebar navigation
   * @param {Object} config - Dashboard configuration
   * @param {string} config.folder - Base folder for panel discovery
   * @param {Array<string>} config.sidebar - List of panel names
   * @param {string} config.default - Default panel to load
   * @param {HTMLElement} targetElement - Target element to render into
   * @returns {HTMLElement} Dashboard container element
   */
  async render(config, targetElement) {
    const { folder, sidebar, default: defaultPanel } = config;

    this.logger.log('[DashboardRenderer] Rendering with config:', config);

    // Load panel metadata to get icons/labels
    const panelMeta = await this._loadPanelMetadata(folder, sidebar);

    // Create dashboard structure using primitives
    const dashboardContainer = this._createDashboardStructure(sidebar, defaultPanel, panelMeta);

    // Determine how to insert dashboard (preserve existing content or replace)
    if (targetElement) {
      const existingContent = targetElement.innerHTML.trim();
      const hasLoadingSpinner = existingContent.includes('zSpinner');

      // If there's real content (not just loading state), preserve it
      if (existingContent && !hasLoadingSpinner) {
        this.logger.log('[DashboardRenderer] Preserving existing content from chunk');
        targetElement.appendChild(dashboardContainer);
      } else {
        // No existing content or only spinner, replace normally
        targetElement.innerHTML = '';
        targetElement.appendChild(dashboardContainer);
      }
    }

    // Set up click handlers for sidebar navigation
    this._setupNavigationHandlers(dashboardContainer, folder);

    // Auto-load default panel
    await this._loadDashboardPanel(folder, defaultPanel);

    return dashboardContainer;
  }

  /**
   * Create dashboard structure using primitives
   * @private
   */
  _createDashboardStructure(sidebar, defaultPanel, panelMeta) {
    // Main container (using primitive)
    const container = createDiv({ class: 'zContainer' });

    // Vertical layout wrapper (using primitive)
    const layout = createDiv({ class: 'zVertical-layout' });

    // Sidebar navigation (using primitives)
    const nav = this._createSidebar(sidebar, defaultPanel, panelMeta);

    // Content area for panels (using primitive)
    const content = createDiv({
      id: 'dashboard-panel-content',
      class: 'zTab-content'
    });

    // Assemble structure
    layout.appendChild(nav);
    layout.appendChild(content);
    container.appendChild(layout);

    return container;
  }

  /**
   * Create sidebar navigation using primitives
   * @private
   */
  _createSidebar(sidebar, defaultPanel, panelMeta) {
    // Create nav list (using primitive)
    const ul = createList(false, {
      class: 'zNav zNav-pills zFlex-column zDash-sidebar',
      role: 'tablist'
    });

    // Create nav items for each panel
    sidebar.forEach(panelName => {
      const meta = panelMeta[panelName] || { icon: 'bi-file-text', label: panelName };
      const isActive = panelName === defaultPanel;

      // Create list item (using primitive)
      const li = createListItem({
        class: 'zNav-item',
        role: 'presentation'
      });

      // Create link (using primitive)
      const link = createLink('#', {
        class: `zNav-link ${isActive ? 'zActive' : ''}`,
        role: 'tab',
        'aria-selected': isActive ? 'true' : 'false'
      });
      link.dataset.panel = panelName;

      // Add Bootstrap Icon if provided
      if (meta.icon) {
        const icon = document.createElement('i');
        icon.className = `bi ${meta.icon}`;
        link.appendChild(icon);
        link.appendChild(document.createTextNode(' '));
      }

      // Add label text
      link.appendChild(document.createTextNode(meta.label));

      // Assemble nav item
      li.appendChild(link);
      ul.appendChild(li);
    });

    return ul;
  }

  /**
   * Set up click handlers for sidebar navigation
   * @private
   */
  _setupNavigationHandlers(dashboardContainer, folder) {
    const links = dashboardContainer.querySelectorAll('.zDash-sidebar .zNav-link');

    links.forEach(link => {
      link.addEventListener('click', async (e) => {
        e.preventDefault();
        const panelName = link.dataset.panel;

        // Update active state
        links.forEach(l => {
          l.classList.remove('zActive');
          l.setAttribute('aria-selected', 'false');
        });
        link.classList.add('zActive');
        link.setAttribute('aria-selected', 'true');

        // Load panel content
        await this._loadDashboardPanel(folder, panelName);
      });
    });
  }

  /**
   * Load panel metadata (icons, labels) from backend
   * @private
   */
  async _loadPanelMetadata(folder, sidebar) {
    const metadata = {};

    for (const panelName of sidebar) {
      try {
        // Request panel metadata from backend
        const zPath = `${folder}.zUI.${panelName}`;
        const response = await fetch(`/api/dashboard/panel/meta?zPath=${encodeURIComponent(zPath)}`);
        const data = await response.json();

        if (data.success && data.meta) {
          metadata[panelName] = {
            icon: data.meta.panel_icon || 'bi-file-text',
            label: data.meta.panel_label || panelName
          };
        }
      } catch (e) {
        this.logger.warn(`[DashboardRenderer] Could not load metadata for ${panelName}:`, e);
        metadata[panelName] = { icon: 'bi-file-text', label: panelName };
      }
    }

    return metadata;
  }

  /**
   * Load and render a dashboard panel
   * @private
   */
  async _loadDashboardPanel(folder, panelName) {
    this.logger.log(`[DashboardRenderer] Loading panel: ${panelName}`);

    const contentArea = document.getElementById('dashboard-panel-content');
    if (!contentArea) {
      this.logger.warn('[DashboardRenderer] Content area not found');
      return;
    }

    // Show loading state (using primitive)
    const spinner = createDiv({ class: 'zSpinner-border', role: 'status' });
    const spinnerLabel = document.createElement('span');
    spinnerLabel.className = 'zVisually-hidden';
    spinnerLabel.textContent = 'Loading...';
    spinner.appendChild(spinnerLabel);

    contentArea.innerHTML = '';
    contentArea.appendChild(spinner);

    try {
      // Request walker execution for the panel
      const requestData = {
        event: 'execute_walker',
        zBlock: panelName,
        zVaFile: `zUI.${panelName}`,
        zVaFolder: folder,
        _renderTarget: 'dashboard-panel-content' // Tell backend where to render
      };

      // Clear the panel content area to prepare for new chunk rendering
      contentArea.innerHTML = '';

      // Send the walker execution request via WebSocket (must be JSON string)
      if (this.client && this.client.connection) {
        await this.client.connection.send(JSON.stringify(requestData));
        this.logger.log('[DashboardRenderer] Panel load request sent');
      } else {
        throw new Error('WebSocket connection not available');
      }

    } catch (error) {
      this.logger.error(`[DashboardRenderer] Error loading panel ${panelName}:`, error);

      // Show error message (using primitive)
      const errorAlert = createDiv({ class: 'zAlert zAlert-danger' });
      errorAlert.textContent = 'Failed to load panel';
      contentArea.innerHTML = '';
      contentArea.appendChild(errorAlert);
    }
  }
}

