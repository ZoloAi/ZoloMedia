/**
 * CacheManager - Manages offline-first caching, storage, and session
 *
 * Responsibilities:
 * - Initialize StorageManager, SessionManager, CacheOrchestrator
 * - Register cache-related hooks (onConnectionInfo, onDisconnected, onConnected)
 * - Handle offline/online transitions
 * - Disable/enable forms during offline mode
 * - Dynamic script loading for cache modules
 *
 * Extracted from bifrost_client.js (Phase 3.1)
 */

export class CacheManager {
  constructor(client) {
    this.client = client;
    this.logger = client.logger;
    this.hooks = client.hooks;
    this._baseUrl = client._baseUrl;
  }

  /**
   * Initialize cache system (v1.6.0)
   * Loads StorageManager, SessionManager, and CacheOrchestrator
   */
  async initCacheSystem() {
    try {
      // Check if running in browser
      if (typeof window === 'undefined') {
        this.logger.log('[Cache] Skipping (not in browser)');
        return;
      }

      this.logger.log('[Cache] Loading cache modules...');

      // Dynamically load cache modules (maintains single-import philosophy)
      await this.loadScript(`${this._baseUrl}core/storage_manager.js`);
      await this.loadScript(`${this._baseUrl}core/session_manager.js`);
      await this.loadScript(`${this._baseUrl}core/cache_orchestrator.js`);

      // Verify modules loaded
      if (typeof window.StorageManager === 'undefined' ||
          typeof window.SessionManager === 'undefined' ||
          typeof window.CacheOrchestrator === 'undefined') {
        this.logger.log('[Cache] Module loading failed, cache disabled');
        return;
      }

      this.logger.log('[Cache] ✅ Cache modules loaded');

      // Initialize storage
      this.client.storage = new window.StorageManager('zBifrost');
      await this.client.storage.init();
      this.logger.log('[Cache] ✅ Storage initialized');

      // Initialize session
      this.client.session = new window.SessionManager(this.client.storage);
      await this.client.session.init();
      this.logger.log('[Cache] ✅ Session initialized');

      // Initialize cache orchestrator
      this.client.cache = new window.CacheOrchestrator(this.client.storage, this.client.session);
      await this.client.cache.init();
      this.logger.log('[Cache] ✅ Cache orchestrator initialized (5 tiers)');

    } catch (error) {
      this.logger.error('[Cache] Initialization error:', error);
      // Non-fatal: cache is optional, BifrostClient will work without it
    }
  }

  /**
   * Dynamically load a script (v1.6.0)
   * @param {string} src - Script URL
   */
  loadScript(src) {
    return new Promise((resolve, reject) => {
      // Check if already loaded
      if (document.querySelector(`script[src="${src}"]`)) {
        resolve();
        return;
      }

      // Note: Script loading uses native createElement (not a primitive, as scripts are not visual elements)
      const script = document.createElement('script');
      script.src = src;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error(`Failed to load ${src}`));
      document.head.appendChild(script);
    });
  }

  /**
   * Register cache-related hooks
   */
  registerCacheHooks() {
    // v1.6.0: Register hook to populate session from connection_info
    this.hooks.register('onConnectionInfo', async (data) => {
      try {
        if (!this.client.session) {
          this.logger.log('[Cache] Session not initialized yet, skipping');
          return;
        }

        const sessionData = data.session;
        if (!sessionData) {
          this.logger.log('[Cache] No session data in connection_info');
          return;
        }

        // Get OLD auth state before updating
        const wasAuthenticated = this.client.session.isAuthenticated();
        const oldSessionHash = this.client.session.getHash();

        // Populate session with backend data
        if (sessionData.authenticated && sessionData.session_hash) {
          await this.client.session.setPublicData({
            username: sessionData.username,
            role: sessionData.role,
            session_hash: sessionData.session_hash,
            app: sessionData.active_app
          });
          this.logger.log(`[Cache] ✅ Session populated: ${sessionData.username} (${sessionData.role})`);
        } else {
          this.logger.log('[Cache] User not authenticated, session remains anonymous');
        }

        // Get NEW auth state after updating
        const isNowAuthenticated = this.client.session.isAuthenticated();
        const newSessionHash = this.client.session.getHash();

        // v1.6.0: If auth state changed or session_hash changed, fetch fresh navbar (RBAC-aware)
        if (wasAuthenticated !== isNowAuthenticated || oldSessionHash !== newSessionHash) {
          this.logger.log('[NavBar] Auth state changed - fetching fresh navbar from API');
          await this.client._fetchAndPopulateNavBar();
          this.logger.log('[NavBar] ✅ Navbar updated after auth change');
        }
      } catch (error) {
        this.logger.error('[Cache] Error populating session:', error);
      }
    });

    // v1.6.0: Offline-first - Handle disconnect + Badge update (combined hook)
    this.hooks.register('onDisconnected', async (_reason) => {
      try {
        this.logger.log('[Cache] Connection lost, entering offline mode');

        // Update badge (v1.6.0: Combined with cache hook to avoid conflicts)
        await this.client._updateBadgeState('disconnected');

        // Cache zVaF content for offline access (badge/navbar are dynamic, re-populated on page load)
        if (this.client.cache && typeof document !== 'undefined') {
          const currentPage = window.location.pathname;
          const contentArea = this.client._zVaFElement;
          if (contentArea) {
            await this.client.cache.set(currentPage, contentArea.outerHTML, 'rendered');
            this.logger.log(`[Cache] ✅ Cached content for offline: ${currentPage}`);
          }
        }

        // Disable forms (prevent data loss)
        this.disableForms();

      } catch (error) {
        this.logger.error('[Cache] Error handling disconnect:', error);
      }
    });

    // v1.6.0: Offline-first - Handle reconnect + Badge update (combined hook)
    this.hooks.register('onConnected', async (_data) => {
      try {
        this.logger.log('[Cache] Connection restored, exiting offline mode');

        // Update badge (v1.6.0: Combined with cache hook to avoid conflicts)
        await this.client._updateBadgeState('connected');

        // Re-enable forms
        this.enableForms();

      } catch (error) {
        this.logger.error('[Cache] Error handling reconnect:', error);
      }
    });
  }

  /**
   * Disable all forms during offline mode (v1.6.0)
   */
  disableForms() {
    if (typeof document === 'undefined') {
      return;
    }

    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
      form.setAttribute('data-offline-disabled', 'true');
      const inputs = form.querySelectorAll('input, textarea, select, button');
      inputs.forEach(input => input.disabled = true);
    });

    this.logger.log('[Offline] ⚠️  Forms disabled (offline mode)');
  }

  /**
   * Re-enable forms after reconnecting (v1.6.0)
   */
  enableForms() {
    if (typeof document === 'undefined') {
      return;
    }

    const forms = document.querySelectorAll('form[data-offline-disabled]');
    forms.forEach(form => {
      form.removeAttribute('data-offline-disabled');
      const inputs = form.querySelectorAll('input, textarea, select, button');
      inputs.forEach(input => input.disabled = false);
    });

    this.logger.log('[Offline] ✅ Forms re-enabled (online mode)');
  }
}

export default CacheManager;

