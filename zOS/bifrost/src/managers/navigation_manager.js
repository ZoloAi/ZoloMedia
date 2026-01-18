/**
 * NavigationManager - Handles client-side navigation (SPA-style routing)
 *
 * Responsibilities:
 * - Enable client-side navigation (intercept clicks on navbar links)
 * - Handle browser back/forward buttons (popstate)
 * - Navigate to routes via WebSocket (no page reload)
 * - Fetch route configuration from backend
 * - Send walker execution requests
 * - Update browser URL without reload
 *
 * Extracted from bifrost_client.js (Phase 3.3)
 */

export class NavigationManager {
  constructor(client) {
    this.client = client;
    this.logger = client.logger;
  }

  /**
   * Enable client-side navigation (SPA-style routing)
   *
   * ✨ REFACTORED: Global click handler removed in favor of individual link handlers
   *
   * Previously, this method attached a global click handler to intercept ALL navbar links.
   * Now, individual links (rendered via link_primitives.js) have their own handlers.
   * This is cleaner, more maintainable, and aligns with primitive-driven architecture.
   *
   * The global handler was causing conflicts (stopPropagation prevented individual handlers).
   * Individual handlers are the single source of truth for link behavior.
   */
  enableClientSideNavigation() {
    if (typeof document === 'undefined') {
      return;
    }

    // Remove legacy global handler if it exists (cleanup from old implementation)
    if (this.client._navClickHandler) {
      document.removeEventListener('click', this.client._navClickHandler, true);
      this.client._navClickHandler = null;
      this.logger.log('[ClientNav] 🗑️  Removed legacy global click handler (now using individual link handlers)');
    }

    // ✅ Individual links now handle their own clicks via link_primitives.js
    // No global handler needed - each link has its own addEventListener('click', ...)
    // This is the primitive-driven way: each component manages its own behavior

    this.logger.log('[ClientNav] ✅ Client-side navigation enabled (using individual link handlers)');

    // Handle browser back/forward buttons
    if (!this.client._popstateHandler) {
      this.client._popstateHandler = async (_e) => {
        this.logger.log('[ClientNav] ⏪ Browser back/forward detected');
        const path = window.location.pathname;

        // Navigate to the new path via WebSocket
        await this.navigateToRoute(path, { skipHistory: true });
      };

      window.addEventListener('popstate', this.client._popstateHandler);
    }

    this.logger.log('[ClientNav] ✅ Client-side navigation enabled');
  }

  /**
   * Navigate to a route via WebSocket (client-side navigation)
   * @param {string} routePath - Path to navigate to (e.g., '/zAbout', '/zAccount')
   * @param {Object} options - Navigation options
   */
  async navigateToRoute(routePath, options = {}) {
    const { skipHistory = false } = options;

    // Mark as client-side navigation to prevent beforeunload from triggering
    this.client._isClientSideNav = true;

    try {
      // Extract route name from path (e.g., '/zAbout' -> 'zAbout')
      const cleanPath = routePath.replace(/^\//, '') || 'zVaF';

      this.logger.log('[ClientNav] 🚀 Navigating to route:', cleanPath);

      // Fetch route configuration from backend
      const response = await fetch('/api/zui/config');
      if (!response.ok) {
        throw new Error(`Failed to fetch route config: ${response.status}`);
      }

      const config = await response.json();

      // Parse route path to determine zBlock, zVaFile, zVaFolder
      // Supports both flat and nested routes:
      // - /zAbout → zUI.zAbout / @.UI / zAbout
      // - /zProducts/zCLI → zUI.zCLI / @.UI.zProducts / zCLI_Details
      const pathParts = cleanPath.split('/');
      let zVaFile, zVaFolder, zBlock, routeName;

      if (pathParts.length === 1) {
        // Flat route: /zAbout
        routeName = pathParts[0];
        zVaFile = `zUI.${routeName}`;
        zVaFolder = config.zVaFolder || '@.UI';
        zBlock = routeName;
      } else {
        // Nested route: /zProducts/zCLI
        const parentFolder = pathParts.slice(0, -1).join('.'); // e.g., "zProducts"
        const pageName = pathParts[pathParts.length - 1]; // e.g., "zCLI"
        routeName = pageName;
        
        zVaFile = `zUI.${pageName}`;
        zVaFolder = `@.UI.${parentFolder}`;
        zBlock = `${pageName}_Details`; // Convention: nested blocks have _Details suffix
        
        this.logger.log('[ClientNav] 📁 Nested route detected:', { parentFolder, pageName });
      }

      // Check if this route has special modifiers (^ for bounce-back)
      // Skip hierarchical items (objects with zSub)
      const navBarItem = config.zNavBar?.find(item => {
        // Skip non-string items (hierarchical objects)
        if (typeof item !== 'string') {
          return false;
        }
        const cleanItem = item.replace(/^[^~$]+/, '');
        return cleanItem === routeName;
      });

      if (navBarItem) {
        // Use the full item with modifiers as zBlock
        zBlock = navBarItem;
      }

      this.logger.log('[ClientNav] 📋 Route config:', { zVaFile, zVaFolder, zBlock });

      // Clear current content
      if (this.client._zVaFElement) {
        this.client._zVaFElement.innerHTML = '<div class="zText-center zp-4">Loading...</div>';
      }

      // Send walker execution request via WebSocket
      // NOTE: Walker execution is asynchronous - we don't wait for a response
      // The backend will send render_chunk events instead of a direct response
      const walkerRequest = {
        event: 'execute_walker',
        zBlock: zBlock,
        zVaFile: zVaFile,
        zVaFolder: zVaFolder
      };

      this.logger.log('[ClientNav] 📤 Sending walker request (fire-and-forget):', walkerRequest);
      this.client.connection.send(JSON.stringify(walkerRequest));

      // Scroll to top for SPA navigation (mimic full page reload UX)
      window.scrollTo({ top: 0, behavior: 'smooth' });
      this.logger.log('[ClientNav] ⬆️  Scrolled to top');

      // Update browser URL without reload (unless skipHistory is true for popstate)
      if (!skipHistory) {
        const newUrl = routePath.startsWith('/') ? routePath : `/${routePath}`;
        history.pushState({ route: routeName }, '', newUrl);
        this.logger.log('[ClientNav] ✅ Updated URL to:', newUrl);
      }

      this.logger.log('[ClientNav] ✅ Navigation complete');
    } catch (error) {
      this.logger.error('[ClientNav] ❌ Navigation failed:', error);

      // Reset flag on error
      this.client._isClientSideNav = false;

      // Show error in content area
      if (this.client._zVaFElement) {
        this.client._zVaFElement.innerHTML = `
          <div class="zAlert zAlert-danger zmt-4">
            <strong>Navigation Error:</strong> ${error.message}
          </div>
        `;
      }
    } finally {
      // Reset flag after navigation attempt (success or fail)
      setTimeout(() => {
        this.client._isClientSideNav = false;
      }, 100);
    }
  }
}

export default NavigationManager;

