/**
 * ZVaFManager - Manages zVaF elements (badge, navbar, content area)
 *
 * Responsibilities:
 * - Initialize zVaF elements (zBifrostBadge, zNavBar, zVaF)
 * - Populate connection badge
 * - Update badge state (connecting, connected, disconnected, error)
 * - Populate navbar from embedded config or API
 * - Fetch fresh navbar after auth state changes
 *
 * Extracted from bifrost_client.js (Phase 3.2)
 */

export class ZVaFManager {
  constructor(client) {
    this.client = client;
    this.logger = client.logger;
    this.options = client.options;
    this.zuiConfig = client.zuiConfig;
  }

  /**
   * Initialize zVaF elements (v1.6.0: Simplified - elements exist in HTML, just populate)
   */
  initZVaFElements() {
    this.logger.log('[ZVaFManager] 🔧 Starting initialization...');

    if (typeof document === 'undefined') {
      this.logger.warn('[ZVaFManager] Not in browser environment');
      return;
    }

    // Step 1: Find badge element (created by template)
    const badgeElement = document.querySelector('zBifrostBadge');
    if (badgeElement) {
      this.client._zConnectionBadge = badgeElement;
      this.populateConnectionBadge();
      this.logger.log('[ZVaFManager] ✅ Badge element found and populated');
    } else {
      this.logger.error('[ZVaFManager] ❌ <zBifrostBadge> not found in DOM');
    }

    // Step 2: Find navbar element (created by template)
    const navElement = document.querySelector('zNavBar');
    if (navElement) {
      this.client._zNavBarElement = navElement;
      // Fetch and populate navbar asynchronously (don't block initialization)
      this.populateNavBar().catch(err => {
        this.logger.error('[ZVaFManager] Failed to populate navbar:', err);
      });
      this.logger.log('[ZVaFManager] ✅ NavBar element found, populating...');
    } else {
      this.logger.error('[ZVaFManager] ❌ <zNavBar> not found in DOM');
    }

    // Step 3: Find zVaF element (content renders directly into it)
    const zVaFElement = document.querySelector(this.options.targetElement) ||
                        document.getElementById(this.options.targetElement);
    if (zVaFElement) {
      this.client._zVaFElement = zVaFElement;
      this.logger.log('[ZVaFManager] ✅ zVaF element found (content will render here)');
    } else {
      this.logger.error(`[ZVaFManager] ❌ <${this.options.targetElement}> not found in DOM`);
    }

    this.logger.log('[ZVaFManager] ✅ All elements initialized (badge will be updated by onConnected hook)');
  }

  /**
   * Populate connection badge content (v1.6.0: Simplified - element exists, just set content)
   */
  populateConnectionBadge() {
    if (!this.client._zConnectionBadge) {
      return;
    }

    // Set initial badge content (will be updated by connection hooks)
    this.client._zConnectionBadge.className = 'zConnection zBadge zBadge-connection zBadge-pending';
    this.client._zConnectionBadge.innerHTML = `
      <svg class="zIcon zIcon-sm zBadge-dot" aria-hidden="true">
        <use xlink:href="#icon-circle-fill"></use>
      </svg>
      <span class="zBadge-text">Connecting...</span>
    `;

    this.logger.log('[ConnectionBadge] ✅ Badge populated with initial state');
  }

  /**
   * Update badge state (v1.6.0: Helper method called from hooks)
   * @param {string} state - 'connecting', 'connected', 'disconnected', 'error'
   */
  updateBadgeState(state) {
    if (!this.client._zConnectionBadge) {
      this.logger.warn('[ConnectionBadge] Cannot update - badge element not found');
      return;
    }

    const badge = this.client._zConnectionBadge;
    const badgeText = badge.querySelector('.zBadge-text');

    if (!badgeText) {
      this.logger.warn('[ConnectionBadge] Cannot update - badge text element not found');
      return;
    }

    this.logger.log(`[ConnectionBadge] 🔧 Updating badge to: ${state}`);

    // Remove all state classes
    badge.classList.remove('zBadge-pending', 'zBadge-success', 'zBadge-error');

    // Apply new state
    switch (state) {
      case 'connected':
        badge.classList.add('zBadge-success');
        badgeText.textContent = 'Connected';
        this.logger.log('[ConnectionBadge] ✅ Badge updated to Connected');
        break;
      case 'disconnected':
        badge.classList.add('zBadge-pending');
        badgeText.textContent = 'Disconnected';
        this.logger.log('[ConnectionBadge] ⚠️ Badge updated to Disconnected');
        break;
      case 'error':
        badge.classList.add('zBadge-error');
        badgeText.textContent = 'Error';
        this.logger.log('[ConnectionBadge] ❌ Badge updated to Error');
        break;
      case 'connecting':
      default:
        badge.classList.add('zBadge-pending');
        badgeText.textContent = 'Connecting...';
        this.logger.log('[ConnectionBadge] 🔄 Badge updated to Connecting');
        break;
    }
  }

  /**
   * Populate navbar from embedded config (v1.6.0: Use zuiConfig from server, fetch fresh on auth change)
   */
  async populateNavBar() {
    if (!this.client._zNavBarElement) {
      return;
    }

    try {
      // Use embedded zuiConfig (already RBAC-filtered by backend on page load)
      if (this.zuiConfig && this.zuiConfig.zNavBar) {
        const navElement = await this.client._renderMetaNavBarHTML(this.zuiConfig.zNavBar);

        // 🔧 FIX v1.6.1: Append DOM element directly (NOT innerHTML!)
        // This preserves event listeners attached by link_primitives.js
        this.client._zNavBarElement.innerHTML = ''; // Clear first
        if (navElement) {
          this.client._zNavBarElement.appendChild(navElement);
          this.logger.log('[NavBar] ✅ NavBar populated from embedded config (DOM element):', this.zuiConfig.zNavBar);
        } else {
          this.logger.warn('[NavBar] renderMetaNavBarHTML returned null');
        }

        // Enable client-side navigation after navbar is rendered
        await this.client._enableClientSideNavigation();
      } else {
        this.logger.warn('[NavBar] No zNavBar in embedded zuiConfig, navbar will be empty');
      }
    } catch (error) {
      this.logger.error('[NavBar] Failed to populate:', error);
    }
  }

  /**
   * Fetch fresh navbar from API and populate (used after auth state changes)
   */
  async fetchAndPopulateNavBar() {
    if (!this.client._zNavBarElement) {
      return;
    }

    try {
      // Fetch fresh navbar config from backend (RBAC-filtered!)
      const response = await fetch('/api/zui/config');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const freshConfig = await response.json();
      this.logger.log('[NavBar] ✅ Fetched fresh config from API:', freshConfig);

      // Update zuiConfig with fresh navbar
      if (freshConfig.zNavBar) {
        this.zuiConfig.zNavBar = freshConfig.zNavBar;
        this.client.zuiConfig.zNavBar = freshConfig.zNavBar;

        // Render navbar element and append it (preserves event listeners!)
        const navElement = await this.client._renderMetaNavBarHTML(freshConfig.zNavBar);

        // 🔧 FIX v1.6.1: Append DOM element directly (NOT innerHTML!)
        this.client._zNavBarElement.innerHTML = ''; // Clear first
        if (navElement) {
          this.client._zNavBarElement.appendChild(navElement);
          this.logger.log('[NavBar] ✅ NavBar populated with fresh RBAC-filtered items (DOM element)');
        } else {
          this.logger.warn('[NavBar] renderMetaNavBarHTML returned null');
        }

        // Re-enable client-side navigation after navbar is re-rendered
        await this.client._enableClientSideNavigation();
      } else {
        this.logger.warn('[NavBar] No zNavBar in API response, skipping');
      }
    } catch (error) {
      this.logger.error('[NavBar] Failed to fetch from API:', error);
    }
  }
}

export default ZVaFManager;

