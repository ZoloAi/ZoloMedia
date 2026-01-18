/**
 * ═══════════════════════════════════════════════════════════════
 * BifrostClient - Production JavaScript Client for zBifrost
 * ═══════════════════════════════════════════════════════════════
 *
 * A production-ready WebSocket client for zCLI's zBifrost bridge.
 * Modular architecture with lazy loading and automatic zTheme integration.
 *
 * @version 1.5.5
 * @author Gal Nachshon
 * @license MIT
 *
 * ───────────────────────────────────────────────────────────────
 * Quick Start
 * ───────────────────────────────────────────────────────────────
 *
 * // Swiper-Style Elegance (One declaration, everything happens automatically):
 * const client = new BifrostClient('ws://localhost:8765', {
 *   autoConnect: true,        // Auto-connect on instantiation
 *   zTheme: true,             // Enable zTheme CSS & rendering
 *   // targetElement: 'zVaF', // Optional: default is 'zVaF' (zView and Function)
 *   autoRequest: 'show_hello',// Auto-send on connect
 *   onConnected: (info) => this.logger.log('✅ Connected!', info)
 * });
 *
 * // Traditional (More control):
 * const client = new BifrostClient('ws://localhost:8765', {
 *   zTheme: true,
 *   hooks: {
 *     onConnected: (info) => this.logger.log('Connected!'),
 *     onDisconnected: (reason) => this.logger.log('Disconnected:', reason),
 *     onMessage: (msg) => this.logger.log('Message:', msg),
 *     onError: (error) => this.logger.error('Error:', error)
 *   }
 * });
 * await client.connect();
 * client.send({event: 'my_event'});
 * const users = await client.read('users');
 *
 * ───────────────────────────────────────────────────────────────
 * Lazy Loading Architecture
 * ───────────────────────────────────────────────────────────────
 *
 * Modules are loaded dynamically only when needed:
 * - Logger/Hooks: Loaded immediately (lightweight)
 * - Connection: Loaded on connect()
 * - MessageHandler: Loaded on connect()
 * - Renderer: Loaded on first renderTable/renderMenu/etc call
 * - ThemeLoader: Loaded on connect() if zTheme enabled
 *
 * Benefits:
 * - CDN-friendly (no import resolution at load time)
 * - Progressive loading (only load what you use)
 * - Stays modular (source files remain separate)
 *
 * ───────────────────────────────────────────────────────────────
 */

(function(root, factory) {
  // UMD (Universal Module Definition) for maximum compatibility
  if (typeof define === 'function' && define.amd) {
    // AMD
    define([], factory);
  } else if (typeof module === 'object' && module.exports) {
    // CommonJS
    module.exports = factory();
  } else {
    // Browser globals
    root.BifrostClient = factory();
  }
}(typeof self !== 'undefined' ? self : this, () => {
  'use strict';

  /**
   * Get base URL for module imports
   */
  function getBaseUrl() {
    if (typeof document !== 'undefined') {
      const scripts = document.querySelectorAll('script[src*="bifrost_client"]');
      if (scripts.length > 0) {
        const src = scripts[scripts.length - 1].src;
        return src.substring(0, src.lastIndexOf('/') + 1);
      }
    }
    return './';
  }

  /**
   * BifrostClient - Main class for WebSocket communication with zBifrost
   */
  class BifrostClient {
    /**
     * Create a new BifrostClient instance
     * @param {string} url - WebSocket server URL (e.g., 'ws://localhost:8765')
     * @param {Object} options - Configuration options
     * @param {boolean} options.autoConnect - Auto-connect on instantiation (default: false)
     * @param {boolean} options.zTheme - Load zTheme CSS + JS from CDN (default: false)
     * @param {string} options.zThemeCDN - CDN base URL for zTheme (default: jsdelivr ZoloAi/zTheme)
     * Note: Bootstrap Icons are ALWAYS loaded automatically (unchangeable default)
     * @param {string} options.targetElement - Target DOM selector for rendering (default: 'zVaF')
     * @param {string|Object} options.autoRequest - Auto-send request on connect (event name or full request object)
     * @param {boolean} options.autoReconnect - Auto-reconnect on disconnect (default: true)
     * @param {number} options.reconnectDelay - Delay between reconnect attempts in ms (default: 3000)
     * @param {number} options.timeout - Request timeout in ms (default: 30000)
     * @param {boolean} options.debug - Enable debug logging (default: false)
     * @param {string} options.token - Authentication token (optional)
     * @param {Object} options.hooks - Event hooks for customization
     */
    constructor(url, options = {}) {
      // Read zUI config from page FIRST (server-injected WebSocket SSL config)
      let zuiConfigEarly = {};
      if (typeof document !== 'undefined' && !url) {
        const zuiConfigEl = document.getElementById('zui-config');
        if (zuiConfigEl) {
          try {
            zuiConfigEarly = JSON.parse(zuiConfigEl.textContent);
          } catch (e) {
            // Logger not initialized yet - use console directly
            console.warn('[BifrostClient] Failed to parse zui-config:', e);
          }
        }
      }

      // Auto-construct WebSocket URL from backend config (respects .zEnv SSL settings)
      if (!url) {
        const wsConfig = zuiConfigEarly.websocket || {};
        const protocol = wsConfig.ssl_enabled ? 'wss:' : 'ws:';
        const wsHost = wsConfig.host || '127.0.0.1';
        const wsPort = wsConfig.port || 8765;
        url = `${protocol}//${wsHost}:${wsPort}`;
        // Logger not initialized yet - use console directly
        console.log(`[BifrostClient] Auto-constructed WebSocket URL from backend config: ${url} (SSL: ${wsConfig.ssl_enabled})`);
      }

      // Validate URL
      if (typeof url !== 'string' || url.trim() === '') {
        throw new Error('BifrostClient: URL must be a non-empty string');
      }
      if (!url.startsWith('ws://') && !url.startsWith('wss://')) {
        throw new Error('BifrostClient: URL must start with ws:// or wss://');
      }

      this.url = url;

      // Validate and set options
      const reconnectDelay = options.reconnectDelay || 3000;
      const timeout = options.timeout || 30000;

      if (typeof reconnectDelay !== 'number' || reconnectDelay <= 0) {
        throw new Error('BifrostClient: reconnectDelay must be a positive number');
      }
      if (typeof timeout !== 'number' || timeout <= 0) {
        throw new Error('BifrostClient: timeout must be a positive number');
      }

      // Auto-read zUI config from page (server-injected zSession values)
      let zuiConfig = {};
      if (typeof document !== 'undefined') {
        const zuiConfigEl = document.getElementById('zui-config');
        if (zuiConfigEl) {
          try {
            zuiConfig = JSON.parse(zuiConfigEl.textContent);
            if (this.logger) {
              this.logger.log('[BifrostClient] Auto-loaded zUI config from page:', zuiConfig);
            }
          } catch (e) {
            this.logger.warn('[BifrostClient] Failed to parse zui-config:', e);
          }
        }
      }

      // Store zuiConfig on instance for later access (e.g., navbar resolution)
      this.zuiConfig = zuiConfig;

      // Determine autoRequest based on zui-config
      let autoRequest = options.autoRequest || null;

      // If zBlock is specified (from zui-config or options), auto-generate walker execution request
      const zBlock = options.zBlock || zuiConfig.zBlock || null;
      const zVaFile = options.zVaFile || zuiConfig.zVaFile || null;
      const zVaFolder = options.zVaFolder || zuiConfig.zVaFolder || null;

      if (zBlock && !autoRequest) {
        autoRequest = {
          event: 'execute_walker',
          zBlock: zBlock,
          zVaFile: zVaFile,
          zVaFolder: zVaFolder
        };
        // Logger not initialized yet - use console directly
        console.log('[BifrostClient] 🚀 Auto-generated walker execution request from zui-config:', autoRequest);
      }

      this.options = {
        autoConnect: options.autoConnect || false, // Default false
        zTheme: options.zTheme || false, // Load zTheme from CDN (CSS + JS)
        zIcons: options.zIcons || false, // Load zTheme icons from CDN (SVG sprite)
        targetElement: options.targetElement || 'zVaF', // Default zCLI parent tag (zView and Function)
        autoRequest: autoRequest, // Auto-send on connect (generated or explicit)
        autoReconnect: options.autoReconnect !== false, // Default true
        reconnectDelay: reconnectDelay,
        timeout: timeout,
        debug: options.debug || false,
        token: options.token || null,
        hooks: options.hooks || {},
        zThemeCDN: options.zThemeCDN || 'https://cdn.jsdelivr.net/gh/ZoloAi/zTheme@main/dist', // CDN base URL (commit hash bypasses cache)
        // Full declarative mode - auto-read from page config, fallback to explicit options
        zVaFile: zVaFile,   // YAML file to load
        zVaFolder: zVaFolder, // Folder path
        zBlock: zBlock,      // Block to render
        title: options.title || zuiConfig.title || null          // zSpark title for navbar brand
      };

      // Module cache (lazy loaded)
      this._modules = {};
      this._baseUrl = getBaseUrl();

      // Pre-initialize lightweight modules synchronously (MUST BE FIRST - initializes logger)
      this._initLightweightModules();

      // v1.6.0: Initialize cache system (async, must complete before connect)
      this.cache = null;
      this.session = null;
      this.storage = null;
      this._cacheReady = this._initCacheSystem().then(() => {
        // Register hooks after cache is initialized
        this._registerCacheHooks();
        this.logger.log('[Cache] ✅ Ready for connection');
      }).catch(err => {
        this.logger.error('[Cache] Initialization failed:', err);
        // Non-fatal: allow connection without cache
      });

      // Debug: confirm which declarative UI options were actually received
      this.logger.log('[BifrostClient] init options:', {
        targetElement: this.options.targetElement,
        zVaFile: this.options.zVaFile,
        zVaFolder: this.options.zVaFolder,
        zBlock: this.options.zBlock
      });

      // Load zTheme from CDN if enabled
      if (this.options.zTheme) {
        this._loadZThemeCDN();
      }

      // Bootstrap Icons are ALWAYS loaded (unchangeable default for zBifrost)
      this._loadBootstrapIcons();

      // _zScripts are now loaded AFTER first chunk renders (see widget_hook_manager.js)
      // This ensures DOM elements exist before plugins run
      this._zScriptsLoaded = false;

      // v1.6.0: Initialize zVaF elements (now synchronous - elements exist in HTML)
      // Just populate content, don't create structure
      this._initZVaFElements();

      // Auto-load declarative UI if zVaFile is provided
      // SKIP for walker-based pages (progressive chunk rendering from backend)
      const isWalkerMode = autoRequest && autoRequest.event === 'execute_walker';
      if (this.options.zVaFile && !isWalkerMode) {
        this._loadDeclarativeUI().catch(err => {
          this.logger.error('Failed to load declarative UI:', err);
        });
      } else if (isWalkerMode) {
        this.logger.log('🎬 Walker mode detected - waiting for progressive chunks from backend');
        // v1.6.0: Navbar is now fetched by _initZVaFElements (no need for redundant call)
      }

      // Auto-connect if requested (Swiper-style elegance!)
      // v1.6.0: Wait for cache initialization before connecting (zVaF elements are now sync)
      if (this.options.autoConnect) {
        this._cacheReady.finally(() => {
          this.logger.log('[BifrostClient] ✅ Cache ready - connecting...');
          this.connect().catch(err => {
            this.logger.error('Auto-connect failed:', err);
            this.hooks.call('onError', { type: 'autoconnect_failed', error: err });
          });
        });
      }

      // Part 2: Browser lifecycle awareness - cleanup on page unload
      // Track if we're doing client-side navigation (to avoid false page_unload events)
      this._isClientSideNav = false;

      window.addEventListener('beforeunload', (_e) => {
        // Only send page_unload if this is a real page unload (not client-side nav)
        if (this._isClientSideNav) {
          this.logger.log('[BifrostClient] Client-side navigation detected - skipping page_unload');
          this._isClientSideNav = false;
          return;
        }

        this.logger.log('[BifrostClient] 🔄 Page unloading (leaving site) - notifying backend');
        // Send cleanup notification (best effort - may not complete if page closes quickly)
        if (this.connection && this.connection.isConnected()) {
          try {
            this.connection.send(JSON.stringify({
              event: 'page_unload',
              reason: 'navigation',
              timestamp: Date.now()
            }));
          } catch (err) {
            // Ignore errors during unload (connection might already be closing)
            this.logger.warn('[BifrostClient] Could not send page_unload message:', err);
          }
        }
      });
    }

    /**
     * Initialize lightweight modules that don't require imports
     */
    _initLightweightModules() {
      // Inline Logger (lightweight, no dependencies)
      this.logger = {
        debug: this.options.debug,
        log: (message, ...args) => {
          if (this.logger.debug) {
            console.log(`[BifrostClient] ${message}`, ...args);
          }
        },
        error: (message, ...args) => {
          // Always show errors, regardless of debug mode
          console.error(`[BifrostClient ERROR] ${message}`, ...args);

          // Also show in ErrorDisplay for user-facing errors (if initialized)
          if (this.errorDisplay && this.options.showErrors !== false) {
            // Extract error object if present in args
            const errorObj = args.find(arg => arg instanceof Error);
            this.errorDisplay.show({
              title: 'Error',
              message: message,
              error: errorObj || new Error(message),
              timestamp: new Date().toISOString()
            });
          }
        },
        warn: (message, ...args) => {
          if (this.logger.debug) {
            console.warn(`[BifrostClient WARN] ${message}`, ...args);
          }
        },
        enable: () => {
          this.logger.debug = true;
        },
        disable: () => {
          this.logger.debug = false;
        },
        isEnabled: () => {
          return this.logger.debug;
        }
      };

      // Inline HookManager (lightweight, no dependencies)
      this.hooks = {
        hooks: this.options.hooks || {},
        errorHandler: null, // Set by _initErrorDisplay()
        call: (hookName, ...args) => {
          const hook = this.hooks.hooks[hookName];
          this.logger.log(`[Hooks] 🎣 Calling hook: ${hookName}, exists: ${typeof hook === 'function'}`);
          if (typeof hook === 'function') {
            try {
              return hook(...args);
            } catch (error) {
              // Log to console
              this.logger.error(`[BifrostClient] Error in ${hookName} hook:`, error);

              // Log via logger
              this.logger.error(`Error in ${hookName} hook:`, error);

              // Display in UI if error handler is set
              if (this.hooks.errorHandler) {
                try {
                  this.hooks.errorHandler({
                    type: 'hook_error',
                    hookName,
                    error,
                    message: error.message,
                    stack: error.stack
                  });
                } catch (displayError) {
                  this.logger.error('[BifrostClient] Error handler itself failed:', displayError);
                }
              }

              // Call onError hook if it exists and isn't the one that failed
              if (hookName !== 'onError' && this.hooks.hooks.onError) {
                try {
                  this.hooks.hooks.onError(error);
                } catch (onErrorError) {
                  this.logger.error('[BifrostClient] onError hook failed:', onErrorError);
                }
              }
            }
          }
        },
        has: (hookName) => {
          return typeof this.hooks.hooks[hookName] === 'function';
        },
        register: (hookName, fn) => {
          if (typeof fn === 'function') {
            this.hooks.hooks[hookName] = fn;
            this.logger.log(`[Hooks] ✅ Registered hook: ${hookName}`);
          } else {
            this.logger.error(`[Hooks] ❌ Failed to register hook ${hookName}: not a function`);
          }
        },
        unregister: (hookName) => {
          delete this.hooks.hooks[hookName];
        },
        list: () => Object.keys(this.hooks.hooks),

        // Dark mode utilities
        initBuiltInHooks: () => {
          // Initialize dark mode from localStorage
          const savedTheme = localStorage.getItem('zTheme-mode');
          if (savedTheme === 'dark') {
            this.hooks._applyDarkMode(true);
          }
        },

        _applyDarkMode: (isDark) => {
          const body = document.body;
          const navbars = document.querySelectorAll('.zNavbar');
          const togglers = document.querySelectorAll('.zNavbar-toggler');

          this.logger.log(`[DarkMode] Applying ${isDark ? 'DARK' : 'LIGHT'} mode`);
          this.logger.log(`[DarkMode] Found ${navbars.length} navbar(s), ${togglers.length} toggler(s)`);

          if (isDark) {
            // Apply dark background to body
            body.classList.add('zBg-dark');
            // Apply white text ONLY to direct children of body that need it (not cards)
            // Cards keep their light background and dark text for readability
            const contentArea = this._zVaFElement;
            if (contentArea) {
              // Apply white text to headers/titles outside cards
              contentArea.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(header => {
                // Only if not inside a card
                if (!header.closest('.zCard')) {
                  header.classList.add('zText-light');
                }
              });
              // Apply white text to paragraphs outside cards
              contentArea.querySelectorAll('p').forEach(p => {
                // Only if not inside a card
                if (!p.closest('.zCard')) {
                  p.classList.add('zText-light');
                }
              });
            }
            body.style.backgroundColor = 'var(--color-dark)';
            // DON'T set body.style.color - let it cascade properly to preserve card readability
            navbars.forEach(nav => {
              nav.classList.remove('zNavbar-light');
              nav.classList.add('zNavbar-dark');
              this.logger.log('[DarkMode] Navbar classes:', nav.className);
            });
            // Apply dark mode to hamburger icon (makes it white)
            togglers.forEach((toggler, idx) => {
              toggler.classList.add('zNavbar-toggler-dark');
              // Bootstrap Icons inherit color from parent, set explicitly to white
              const icon = toggler.querySelector('i.bi');
              if (icon) {
                icon.style.color = '#ffffff';  // Direct color value instead of CSS var
              }
              const computedColor = icon ? window.getComputedStyle(icon).color : 'not found';
              this.logger.log(`[DarkMode] Toggler ${idx} classes:`, toggler.className);
              this.logger.log(`[DarkMode] Toggler ${idx} icon color (after):`, computedColor);
              this.logger.log(`[DarkMode] Toggler ${idx} icon element:`, icon);
            });

            // Apply dark mode to theme toggle button icon (sun icon should be white)
            const themeToggleBtn = document.querySelector('.zTheme-toggle');
            if (themeToggleBtn) {
              const icon = themeToggleBtn.querySelector('i.bi');
              if (icon) {
                icon.style.color = '#ffffff';  // Direct color value instead of CSS var
                this.logger.log('[DarkMode] Theme toggle icon color set to white');
              }
            } else {
              this.logger.log('[DarkMode] Theme toggle button not found yet');
            }
          } else {
            // Remove dark background from body
            body.classList.remove('zBg-dark');
            // Remove white text from all elements
            const contentArea = this._zVaFElement;
            if (contentArea) {
              contentArea.querySelectorAll('.zText-light').forEach(el => {
                el.classList.remove('zText-light');
              });
            }
            body.style.backgroundColor = '';
            body.style.color = '';
            navbars.forEach(nav => {
              nav.classList.remove('zNavbar-dark');
              nav.classList.add('zNavbar-light');
              this.logger.log('[DarkMode] Navbar classes:', nav.className);
            });
            // Remove dark mode from hamburger icon
            togglers.forEach((toggler, idx) => {
              toggler.classList.remove('zNavbar-toggler-dark');
              // Clear inline styles to restore default color
              const icon = toggler.querySelector('i.bi');
              if (icon) {
                icon.style.color = '';
              }
              const computedColor = icon ? window.getComputedStyle(icon).color : 'not found';
              this.logger.log(`[DarkMode] Toggler ${idx} classes:`, toggler.className);
              this.logger.log(`[DarkMode] Toggler ${idx} icon color (after):`, computedColor);
            });

            // Clear theme toggle button icon color
            const themeToggleBtn = document.querySelector('.zTheme-toggle');
            if (themeToggleBtn) {
              const icon = themeToggleBtn.querySelector('i.bi');
              if (icon) {
                icon.style.color = '';
                this.logger.log('[DarkMode] Theme toggle icon color cleared');
              }
            }
          }
        },

        addDarkModeToggle: async (navElement) => {
          // Use DarkModeToggle widget (extracted for modularity)
          const { DarkModeToggle } = await import('./widgets/dark_mode_toggle.js');
          const darkModeWidget = new DarkModeToggle(this.logger);

          // Create toggle with theme change callback
          darkModeWidget.create(navElement, (newTheme) => {
            // Apply theme
            this.hooks._applyDarkMode(newTheme === 'dark');

            // Call onThemeChange hook if registered
            this.hooks.call('onThemeChange', newTheme);
          });
        }
      };

      // Initialize built-in hooks (dark mode)
      this.hooks.initBuiltInHooks();

      // Register default widget hooks (Week 4.2)
      this._registerDefaultWidgetHooks();

      this.logger.log('BifrostClient initialized', { url: this.url, options: this.options });
    }

    /**
     * Register default hooks for widget events
     *
     * Registers hooks for progress bars, spinners, and swipers.
     * These hooks use the new modular renderer architecture.
     */
    _registerDefaultWidgetHooks() {
      // Widget hooks are now registered in the widget handler (lines ~1900+)
      // This method is kept for backward compatibility
    }

    async _registerCacheHooks() {
      // Delegate to CacheManager
      await this._ensureCacheManager();
      return this.cacheManager.registerCacheHooks();
    }

    /**
     * Disable all forms during offline mode (v1.6.0)
     * @private
     */
    async _disableForms() {
      await this._ensureCacheManager();
      return this.cacheManager.disableForms();
    }

    /**
     * Re-enable forms after reconnecting (v1.6.0)
     * @private
     */
    async _enableForms() {
      await this._ensureCacheManager();
      return this.cacheManager.enableForms();
    }

    /**
     * Initialize cache system (v1.6.0)
     * Loads StorageManager, SessionManager, and CacheOrchestrator
     * @private
     */
    async _initCacheSystem() {
      await this._ensureCacheManager();
      return this.cacheManager.initCacheSystem();
    }

    /**
     * Dynamically load a script (v1.6.0)
     * @private
     */
    async _loadScript(src) {
      await this._ensureCacheManager();
      return this.cacheManager.loadScript(src);
    }

    /**
     * Initialize zVaF elements (connection badges, dynamic content)
     *
     * DECLARATIVE APPROACH: The zVaF element is an empty canvas.
     * This method populates it entirely, including connection badge and content area.
     */
    /**
     * Load zTheme CSS and JS from CDN
     * @private
     */
    _loadZThemeCDN() {
      if (typeof document === 'undefined') {
        return;
      }

      const cdnBase = this.options.zThemeCDN;

      // Show which version/URL is being loaded
      this.logger.log(`[BifrostClient] 🎨 Loading zTheme from CDN: ${cdnBase}`);

      // Check if CSS already loaded
      if (!document.querySelector(`link[href="${cdnBase}/ztheme.css"]`)) {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = `${cdnBase}/ztheme.css`;
        document.head.appendChild(link);
        this.logger.log(`[BifrostClient] ✅ zTheme CSS loaded: ${cdnBase}/ztheme.css`);
        this.logger.log('✅ zTheme CSS loaded from CDN');
      } else {
        this.logger.log(`[BifrostClient] ℹ️  zTheme CSS already loaded from: ${cdnBase}/ztheme.css`);
      }

      // Check if JS already loaded
      if (!document.querySelector(`script[src="${cdnBase}/ztheme.js"]`)) {
        const script = document.createElement('script');
        script.src = `${cdnBase}/ztheme.js`;
        document.head.appendChild(script);
        this.logger.log(`[BifrostClient] ✅ zTheme JS loaded: ${cdnBase}/ztheme.js`);
        this.logger.log('✅ zTheme JS loaded from CDN');
      } else {
        this.logger.log(`[BifrostClient] ℹ️  zTheme JS already loaded from: ${cdnBase}/ztheme.js`);
      }
    }

    /**
     * Load _zScripts from YAML metadata (plugin scripts)
     * @private
     */
    _loadZScripts() {
      if (typeof document === 'undefined') {
        return;
      }

      // Extract _zScripts from zuiConfig.zMeta (v1.5.13: Server passes zMeta section from YAML)
      const zScripts = this.zuiConfig?.zMeta?._zScripts || [];
      
      if (!Array.isArray(zScripts) || zScripts.length === 0) {
        this.logger.log('[BifrostClient] No _zScripts found in YAML metadata');
        return;
      }

      this.logger.log(`[BifrostClient] 📜 Loading ${zScripts.length} _zScripts from YAML metadata`);

      zScripts.forEach(scriptRef => {
        // Resolve plugin reference: &.plugin_name → /plugins/plugin_name.js
        let scriptUrl = scriptRef;
        if (scriptRef.startsWith('&.')) {
          const pluginName = scriptRef.substring(2);
          scriptUrl = `/plugins/${pluginName}.js`;
          this.logger.log(`[BifrostClient] Resolving plugin: ${scriptRef} → ${scriptUrl}`);
        }

        // Check if script already loaded
        if (!document.querySelector(`script[src="${scriptUrl}"]`)) {
          const script = document.createElement('script');
          script.src = scriptUrl;
          script.async = true;
          script.onload = () => {
            this.logger.log(`[BifrostClient] ✅ Loaded _zScript: ${scriptUrl}`);
          };
          script.onerror = () => {
            this.logger.error(`[BifrostClient] ❌ Failed to load _zScript: ${scriptUrl}`);
          };
          document.head.appendChild(script);
        } else {
          this.logger.log(`[BifrostClient] ℹ️  _zScript already loaded: ${scriptUrl}`);
        }
      });
    }

    /**
     * Load Bootstrap Icons from CDN (ALWAYS loaded, unchangeable default)
     * @private
     */
    _loadBootstrapIcons() {
      if (typeof document === 'undefined') {
        return;
      }

      const bootstrapIconsCDN = 'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css';

      // Check if Bootstrap Icons already loaded
      if (!document.querySelector(`link[href="${bootstrapIconsCDN}"]`)) {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = bootstrapIconsCDN;
        document.head.appendChild(link);
        this.logger.log('✅ Bootstrap Icons loaded from CDN (v1.11.3)');
      }
    }

    /**
     * Load and render declarative UI from zVaFile (client-side YAML parsing)
     * @private
     */
    async _loadDeclarativeUI() {
      // Delegate to DeclarativeUILoader
      await this._ensureDeclarativeUILoader();
      return this.declarativeUILoader.loadDeclarativeUI();
    }

    /**
     * Render a zVaF block declaratively (convert YAML to DOM)
     * @private
     */
    async _renderBlock(blockData) {
      // Delegate to ZDisplayOrchestrator
      await this._ensureZDisplayOrchestrator();
      return this.zDisplayOrchestrator.renderBlock(blockData);
    }

    /**
     * Progressive chunk rendering (Option A: Terminal First philosophy)
     * Appends chunks from backend as they arrive, stops at failed gates
     * @private
     */
    async _renderChunkProgressive(message) {
      // Delegate to ZDisplayOrchestrator
      await this._ensureZDisplayOrchestrator();
      return this.zDisplayOrchestrator.renderChunkProgressive(message);
    }

    /**
     * Recursively render YAML items (handles nested structures like implicit wizards)
     * @private
     */
    async _renderItems(data, parentElement) {
      // Delegate to ZDisplayOrchestrator
      await this._ensureZDisplayOrchestrator();
      return this.zDisplayOrchestrator.renderItems(data, parentElement);
    }

    /**
     * Create container wrapper for a zKey with zTheme responsive classes
     * Supports _zClass metadata for customization
     * @private
     */
    async _createContainer(zKey, metadata) {
      // Delegate to ZDisplayOrchestrator
      await this._ensureZDisplayOrchestrator();
      return this.zDisplayOrchestrator.createContainer(zKey, metadata);
    }

    /**
     * Render meta.zNavBar at the top of zVaF (website-style main navigation)
     * @private
     */
    /**
     * Render navbar HTML string (v1.6.0: Returns HTML, doesn't inject into DOM)
     * @param {Array} items - Navbar items (e.g., ['zVaF', 'zAbout', '^zLogin'])
     * @returns {Promise<string>} Navbar HTML
     */
    async _renderMetaNavBarHTML(items) {
      // Delegate to ZDisplayOrchestrator
      await this._ensureZDisplayOrchestrator();
      return this.zDisplayOrchestrator.renderMetaNavBarHTML(items);
    }

    /**
     * Render navigation bar from metadata (~zNavBar* in content)
     * @private
     */
    async _renderNavBar(items, parentElement) {
      // Delegate to ZDisplayOrchestrator
      await this._ensureZDisplayOrchestrator();
      return this.zDisplayOrchestrator.renderNavBar(items, parentElement);
    }

    /**
     * Render a single zDisplay event as DOM element
     * @private
     */
    async _renderZDisplayEvent(eventData) {
      // Delegate to ZDisplayOrchestrator
      await this._ensureZDisplayOrchestrator();
      return this.zDisplayOrchestrator.renderZDisplayEvent(eventData);
    }

    /**
     * Initialize zVaF-specific DOM elements (connection badges, etc.)
     * @private
     */
    /**
     * Initialize zVaF elements (v1.6.0: Simplified - elements exist in HTML, just populate)
     *
     * HTML structure (declared in zVaF.html):
     *   <zBifrostBadge></zBifrostBadge>  ← Dynamic, always fresh
     *   <zNavBar></zNavBar>              ← Dynamic, RBAC-aware
     *   <zVaF>...</zVaF>                 ← Cacheable content area
     */
    async _initZVaFElements() {
      await this._ensureZVaFManager();
      return this.zvafManager.initZVaFElements();
    }

    /**
     * Populate connection badge content (v1.6.0: Simplified - element exists, just set content)
     */
    async _populateConnectionBadge() {
      await this._ensureZVaFManager();
      return this.zvafManager.populateConnectionBadge();
    }

    /**
     * Update badge state (v1.6.0: Helper method called from hooks)
     * @param {string} state - 'connecting', 'connected', 'disconnected', 'error'
     */
    async _updateBadgeState(state) {
      await this._ensureZVaFManager();
      return this.zvafManager.updateBadgeState(state);
    }

    /**
     * Populate navbar from embedded config (v1.6.0: Use zuiConfig from server, fetch fresh on auth change)
     */
    async _populateNavBar() {
      await this._ensureZVaFManager();
      return this.zvafManager.populateNavBar();
    }

    /**
     * Fetch fresh navbar from API and populate (used after auth state changes)
     */
    async _fetchAndPopulateNavBar() {
      await this._ensureZVaFManager();
      return this.zvafManager.fetchAndPopulateNavBar();
    }

    /**
     * Enable client-side navigation (SPA-style) for navbar links
     * Intercepts clicks to prevent full page reloads and uses WebSocket instead
     */
    async _enableClientSideNavigation() {
      await this._ensureNavigationManager();
      return this.navigationManager.enableClientSideNavigation();
    }

    /**
     * Navigate to a route via WebSocket (client-side navigation)
     * @param {string} routePath - Path to navigate to (e.g., '/zAbout', '/zAccount')
     * @param {Object} options - Navigation options
     */
    async _navigateToRoute(routePath, options = {}) {
      await this._ensureNavigationManager();
      return this.navigationManager.navigateToRoute(routePath, options);
    }


    /**
     * Lazy load a module
     * @param {string} moduleName - Name of the module (connection, message_handler, renderer, zdisplay_renderer)
     * @returns {Promise<any>}
     */
    async _loadModule(moduleName) {
      if (this._modules[moduleName]) {
        return this._modules[moduleName];
      }

      // Determine module subfolder based on module type
      const coreModules = ['connection', 'hooks', 'logger', 'message_handler', 'error_display'];
      const renderingModules = ['renderer', 'zdisplay_renderer', 'navigation_renderer', 'form_renderer', 'menu_renderer'];

      let subfolder = '';
      if (coreModules.includes(moduleName)) {
        subfolder = 'core/';
      } else if (renderingModules.includes(moduleName)) {
        subfolder = 'rendering/';
      }

      const modulePath = `${this._baseUrl}${subfolder}${moduleName}.js`;
      this.logger.log(`Loading module: ${moduleName} from ${modulePath}`);

      try {
        const module = await import(modulePath);
        this._modules[moduleName] = module;
        return module;
      } catch (error) {
        this.logger.error(`Failed to load module ${moduleName}:`, error);
        throw new Error(`Failed to load BifrostClient module: ${moduleName}`);
      }
    }

    /**
     * Ensure connection module is loaded
     */
    async _ensureConnection() {
      if (!this.connection) {
        const { BifrostConnection } = await this._loadModule('connection');
        this.connection = new BifrostConnection(
          this.url,
          this.options,
          this.logger,
          this.hooks
        );
      }
      return this.connection;
    }

    /**
     * Ensure message handler module is loaded
     */
    async _ensureMessageHandler() {
      if (!this.messageHandler) {
        const { MessageHandler } = await this._loadModule('message_handler');
        this.messageHandler = new MessageHandler(this.logger, this.hooks, this);
        this.messageHandler.setTimeout(this.options.timeout);
      }
      return this.messageHandler;
    }

    /**
     * Ensure renderer module is loaded
     */
    async _ensureRenderer() {
      if (!this.renderer) {
        const { Renderer } = await this._loadModule('renderer');
        this.renderer = new Renderer(this.logger);
      }
      return this.renderer;
    }

    /**
     * Ensure navigation renderer module is loaded
     */
    async _ensureNavigationRenderer() {
      if (!this.navigationRenderer) {
        const { NavigationRenderer } = await this._loadModule('navigation_renderer');
        // Pass 'this' (BifrostClient) so NavigationRenderer can use link primitives with client context
        this.navigationRenderer = new NavigationRenderer(this.logger, this);
      }
      return this.navigationRenderer;
    }

    /**
     * Ensure TypographyRenderer module is loaded
     */
    async _ensureTypographyRenderer() {
      if (!this.typographyRenderer) {
        const module = await import('./rendering/typography_renderer.js');
        const TypographyRenderer = module.default;
        this.typographyRenderer = new TypographyRenderer(this.logger);
        this.logger.log('[BifrostClient] TypographyRenderer loaded and initialized');
      }
      return this.typographyRenderer;
    }

    /**
     * Ensure TextRenderer module is loaded
     */
    async _ensureTextRenderer() {
      if (!this.textRenderer) {
        const module = await import('./rendering/text_renderer.js');
        const TextRenderer = module.default;
        this.textRenderer = new TextRenderer(this.logger);
        this.logger.log('[BifrostClient] TextRenderer loaded and initialized');
      }
      return this.textRenderer;
    }

    /**
     * Ensure CardRenderer module is loaded
     */
    async _ensureCardRenderer() {
      if (!this.cardRenderer) {
        const module = await import('./rendering/card_renderer.js');
        const CardRenderer = module.default;
        this.cardRenderer = new CardRenderer(this.logger);
        this.logger.log('[BifrostClient] CardRenderer loaded and initialized');
      }
      return this.cardRenderer;
    }

    /**
     * Ensure ButtonRenderer module is loaded
     */
    async _ensureButtonRenderer() {
      if (!this.buttonRenderer) {
        const module = await import('./rendering/button_renderer.js');
        const ButtonRenderer = module.default;
        this.buttonRenderer = new ButtonRenderer(this.logger, this);
        this.logger.log('[BifrostClient] ButtonRenderer loaded and initialized');
      }
      return this.buttonRenderer;
    }

    /**
     * Ensure TableRenderer module is loaded
     */
    async _ensureTableRenderer() {
      if (!this.tableRenderer) {
        const module = await import('./rendering/table_renderer.js');
        const TableRenderer = module.default;
        this.tableRenderer = new TableRenderer(this.logger);
        this.logger.log('[BifrostClient] TableRenderer loaded and initialized');
      }
      return this.tableRenderer;
    }

    /**
     * Lazy-load the ListRenderer module
     * @private
     */
    async _ensureListRenderer() {
      if (!this.listRenderer) {
        const module = await import('./rendering/list_renderer.js');
        const ListRenderer = module.default;
        this.listRenderer = new ListRenderer(this);
        this.logger.log('[BifrostClient] ListRenderer loaded and initialized');
      }
      return this.listRenderer;
    }

    /**
     * Ensure image renderer module is loaded
     */
    async _ensureImageRenderer() {
      if (!this.imageRenderer) {
        const module = await import('./rendering/image_renderer.js');
        const ImageRenderer = module.default;
        this.imageRenderer = new ImageRenderer(this.logger);
        this.logger.log('[BifrostClient] ImageRenderer loaded and initialized');
      }
      return this.imageRenderer;
    }

    /**
     * Ensure dashboard renderer module is loaded
     */
    async _ensureDashboardRenderer() {
      if (!this.dashboardRenderer) {
        const module = await import('./rendering/dashboard_renderer.js');
        const DashboardRenderer = module.default;
        this.dashboardRenderer = new DashboardRenderer(this.logger, this);
        this.logger.log('[BifrostClient] DashboardRenderer loaded and initialized');
      }
      return this.dashboardRenderer;
    }

    /**
     * Ensure spinner renderer module is loaded
     */
    async _ensureSpinnerRenderer() {
      if (!this.spinnerRenderer) {
        const module = await import('./rendering/spinner_renderer.js');
        const SpinnerRenderer = module.default;
        this.spinnerRenderer = new SpinnerRenderer(this.logger);
        this.logger.log('[BifrostClient] SpinnerRenderer loaded and initialized');
      }
      return this.spinnerRenderer;
    }

    /**
     * Ensure progress bar renderer module is loaded
     */
    async _ensureProgressBarRenderer() {
      if (!this.progressBarRenderer) {
        const module = await import('./rendering/progressbar_renderer.js');
        const ProgressBarRenderer = module.default;
        this.progressBarRenderer = new ProgressBarRenderer(this.logger);
        this.logger.log('[BifrostClient] ProgressBarRenderer loaded and initialized');
      }
      return this.progressBarRenderer;
    }

    /**
     * Ensure swiper renderer module is loaded
     */
    async _ensureSwiperRenderer() {
      if (!this.swiperRenderer) {
        const module = await import('./rendering/swiper_renderer.js');
        const SwiperRenderer = module.default;
        this.swiperRenderer = new SwiperRenderer(this.logger);
        this.logger.log('[BifrostClient] SwiperRenderer loaded and initialized');
      }
      return this.swiperRenderer;
    }

    /**
     * Ensure ZDisplayOrchestrator is loaded
     */
    async _ensureZDisplayOrchestrator() {
      if (!this.zDisplayOrchestrator) {
        const { ZDisplayOrchestrator } = await import('./rendering/zdisplay_orchestrator.js');
        this.zDisplayOrchestrator = new ZDisplayOrchestrator(this);
        this.logger.log('[BifrostClient] ZDisplayOrchestrator loaded and initialized');
      }
      return this.zDisplayOrchestrator;
    }

    /**
     * Ensure DeclarativeUILoader is loaded
     */
    async _ensureDeclarativeUILoader() {
      if (!this.declarativeUILoader) {
        const { DeclarativeUILoader } = await import('./rendering/declarative_ui_loader.js');
        this.declarativeUILoader = new DeclarativeUILoader(this);
        this.logger.log('[BifrostClient] DeclarativeUILoader loaded and initialized');
      }
      return this.declarativeUILoader;
    }

    /**
     * Ensure CacheManager is loaded
     */
    async _ensureCacheManager() {
      if (!this.cacheManager) {
        const { CacheManager } = await import('./managers/cache_manager.js');
        this.cacheManager = new CacheManager(this);
        this.logger.log('[BifrostClient] CacheManager loaded and initialized');
      }
      return this.cacheManager;
    }

    /**
     * Ensure ZVaFManager is loaded
     */
    async _ensureZVaFManager() {
      if (!this.zvafManager) {
        const { ZVaFManager } = await import('./managers/zvaf_manager.js');
        this.zvafManager = new ZVaFManager(this);
        this.logger.log('[BifrostClient] ZVaFManager loaded and initialized');
      }
      return this.zvafManager;
    }

    /**
     * Ensure NavigationManager is loaded
     */
    async _ensureNavigationManager() {
      if (!this.navigationManager) {
        const { NavigationManager } = await import('./managers/navigation_manager.js');
        this.navigationManager = new NavigationManager(this);
        this.logger.log('[BifrostClient] NavigationManager loaded and initialized');
      }
      return this.navigationManager;
    }

    /**
     * Ensure WidgetHookManager is loaded
     */
    async _ensureWidgetHookManager() {
      if (!this.widgetHookManager) {
        const { WidgetHookManager } = await import('./managers/widget_hook_manager.js');
        this.widgetHookManager = new WidgetHookManager(this);
        this.logger.log('[BifrostClient] WidgetHookManager loaded and initialized');
      }
      return this.widgetHookManager;
    }

    /**
     * Ensure zDisplay renderer module is loaded
     */
    async _ensureZDisplayRenderer() {
      if (!this.zDisplayRenderer) {
        const { ZDisplayRenderer } = await this._loadModule('zdisplay_renderer');
        this.zDisplayRenderer = new ZDisplayRenderer(this.logger);

        // Pass client reference for interactive features (navigation buttons, etc.)
        this.zDisplayRenderer.client = this;

        // Set target element - render directly into zVaF (no nested wrapper)
        this.zDisplayRenderer.defaultZone = this.options.targetElement;

        this.logger.log(`[BifrostClient] zDisplay target set to: ${this.zDisplayRenderer.defaultZone}`);

        // Delegate all hook registration to WidgetHookManager
        await this._ensureWidgetHookManager();
        await this.widgetHookManager.registerAllWidgetHooks();
      }
      return this.zDisplayRenderer;
    }

    /**
     * Ensure form renderer module is loaded
     */
    async _ensureFormRenderer() {
      if (!this.formRenderer) {
        const { FormRenderer } = await this._loadModule('form_renderer');
        this.formRenderer = new FormRenderer(this);
        this.logger.log('[BifrostClient] FormRenderer loaded and initialized');
      }
      return this.formRenderer;
    }

    /**
     * Lazy-load the MenuRenderer module
     * @private
     */
    async _ensureMenuRenderer() {
      if (!this.menuRenderer) {
        const { MenuRenderer } = await this._loadModule('menu_renderer');
        this.menuRenderer = new MenuRenderer(this);
        this.logger.log('[BifrostClient] MenuRenderer loaded and initialized');
      }
      return this.menuRenderer;
    }


    // ═══════════════════════════════════════════════════════════
    // Connection Management
    // ═══════════════════════════════════════════════════════════

    /**
     * Initialize error display (if not disabled)
     */
    async _ensureErrorDisplay() {
      if (this.options.showErrors === false) {
        return;
      } // Allow disabling

      if (!this.errorDisplay) {
        const { ErrorDisplay } = await this._loadModule('error_display');
        this.errorDisplay = new ErrorDisplay({
          position: this.options.errorPosition || 'top-right',
          maxErrors: this.options.maxErrors || 5,
          autoDismiss: this.options.autoDismiss || 10000
        });

        // Set error handler for hooks
        this.hooks.errorHandler = (errorInfo) => {
          this.errorDisplay.show(errorInfo);
        };

        this.logger.log('Error display initialized');
      }
      return this.errorDisplay;
    }

    /**
     * Check if running on file:// protocol (which doesn't support ES6 module imports)
     * @private
     */
    _isFileProtocol() {
      return typeof window !== 'undefined' && window.location.protocol === 'file:';
    }

    /**
     * Connect to the WebSocket server
     * @returns {Promise<void>}
     */
    async connect() {
      // Skip module loading for file:// protocol (ES6 imports not supported)
      const isFileProtocol = this._isFileProtocol();

      if (isFileProtocol) {
        this.logger.log('[BifrostClient] Running on file:// protocol - skipping module loading');
        this.logger.log('[BifrostClient] Error display and auto-rendering disabled (use HTTP server to enable)');
      }

      // Initialize error display (for visual error boundaries) - skip on file://
      if (!isFileProtocol && this.options.showErrors !== false) {
        try {
          await this._ensureErrorDisplay();
        } catch (error) {
          this.logger.warn('[BifrostClient] Error display failed to load:', error.message);
        }
      }

      // Initialize zDisplay renderer (for auto-rendering zDisplay events) - skip on file://
      if (!isFileProtocol) {
        try {
          await this._ensureZDisplayRenderer();
        } catch (error) {
          this.logger.warn('[BifrostClient] zDisplay renderer failed to load:', error.message);
        }
      }

      // Load theme BEFORE connecting to prevent FOUC (Flash of Unstyled Content)
      // Load required modules
      await this._ensureConnection();
      await this._ensureMessageHandler();

      await this.connection.connect();

      // Set up message handler
      this.connection.onMessage((event) => {
        this.messageHandler.handleMessage(event.data);
      });

      // Auto-send request if specified (Swiper-style elegance!)
      if (this.options.autoRequest) {
        const request = typeof this.options.autoRequest === 'string'
          ? { event: this.options.autoRequest }
          : this.options.autoRequest;

        // For execute_walker requests, use fire-and-forget (chunks come asynchronously)
        // For other requests, use send() to wait for response
        if (request.event === 'execute_walker') {
          this.logger.log('📤 Auto-sending walker request (fire-and-forget):', request);
          this.connection.send(JSON.stringify(request));
        } else {
          this.logger.log('📤 Auto-sending request:', request);
          this.send(request);
        }
      }
    }

    /**
     * Disconnect from the server
     */
    disconnect() {
      if (this.connection) {
        this.connection.disconnect();
      }
    }

    /**
     * Check if connected
     * @returns {boolean}
     */
    isConnected() {
      return this.connection ? this.connection.isConnected() : false;
    }

    // ═══════════════════════════════════════════════════════════
    // Message Sending
    // ═══════════════════════════════════════════════════════════

    /**
     * Send a message and wait for response
     * @param {Object} payload - Message payload
     * @param {number} timeout - Custom timeout (optional)
     * @returns {Promise<any>}
     */
    async send(payload, timeout = null) {
      if (!this.isConnected()) {
        throw new Error('Not connected to server. Call connect() first.');
      }

      await this._ensureMessageHandler();

      return this.messageHandler.send(
        payload,
        (msg) => this.connection.send(msg),
        timeout
      );
    }

    /**
     * Send input response to server
     * @param {string} requestId - Request ID from input event
     * @param {any} value - Input value
     */
    sendInputResponse(requestId, value) {
      if (!this.isConnected()) {
        this.logger.log('❌ Cannot send input response: not connected');
        return;
      }

      // Use new event protocol
      const message = JSON.stringify({
        event: 'input_response',
        requestId: requestId,
        value: value
      });

      this.connection.send(message);
    }

    // ═══════════════════════════════════════════════════════════
    // CRUD Operations
    // ═══════════════════════════════════════════════════════════

    /**
     * Create a new record
     * @param {string} model - Table/model name
     * @param {Object} data - Field values
     * @returns {Promise<Object>}
     */
    async create(model, data) {
      return this.send({
        event: 'dispatch',
        zKey: `^Create ${model}`,
        model: model,
        data: data
      });
    }

    /**
     * Read records
     * @param {string} model - Table/model name
     * @param {Object} filters - WHERE conditions (optional)
     * @param {Object} options - Additional options (fields, order_by, limit, offset)
     * @returns {Promise<Array>}
     */
    async read(model, filters = null, options = {}) {
      const payload = {
        event: 'dispatch',
        zKey: `^List ${model}`,
        model: model
      };

      if (filters) {
        payload.where = filters;
      }
      if (options.fields) {
        payload.fields = options.fields;
      }
      if (options.order_by) {
        payload.order_by = options.order_by;
      }
      if (options.limit !== undefined) {
        payload.limit = options.limit;
      }
      if (options.offset !== undefined) {
        payload.offset = options.offset;
      }

      return this.send(payload);
    }

    /**
     * Update record(s)
     * @param {string} model - Table/model name
     * @param {Object|number} filters - WHERE conditions or ID
     * @param {Object} data - Fields to update
     * @returns {Promise<Object>}
     */
    async update(model, filters, data) {
      if (typeof filters === 'number') {
        filters = { id: filters };
      }

      return this.send({
        event: 'dispatch',
        zKey: `^Update ${model}`,
        model: model,
        where: filters,
        data: data
      });
    }

    /**
     * Delete record(s)
     * @param {string} model - Table/model name
     * @param {Object|number} filters - WHERE conditions or ID
     * @returns {Promise<Object>}
     */
    async delete(model, filters) {
      if (typeof filters === 'number') {
        filters = { id: filters };
      }

      return this.send({
        event: 'dispatch',
        zKey: `^Delete ${model}`,
        model: model,
        where: filters
      });
    }

    // ═══════════════════════════════════════════════════════════
    // zCLI Operations
    // ═══════════════════════════════════════════════════════════

    /**
     * Execute a zFunc command
     * @param {string} command - zFunc command string
     * @returns {Promise<any>}
     */
    async zFunc(command) {
      return this.send({
        zKey: 'zFunc',
        zHorizontal: command
      });
    }

    /**
     * Navigate to a zLink path
     * @param {string} path - zLink navigation path
     * @returns {Promise<any>}
     */
    async zLink(path) {
      return this.send({
        zKey: 'zLink',
        zHorizontal: `zLink(${path})`
      });
    }

    /**
     * Execute a zOpen command
     * @param {string} command - zOpen command string
     * @returns {Promise<any>}
     */
    async zOpen(command) {
      return this.send({
        zKey: 'zOpen',
        zHorizontal: `zOpen(${command})`
      });
    }


    // ═══════════════════════════════════════════════════════════
    // Auto-Rendering Methods (Using zTheme)
    // ═══════════════════════════════════════════════════════════

    /**
     * Render data as a table with zTheme styling
     * @param {Array} data - Array of objects to render
     * @param {string|HTMLElement} container - Container selector or element
     * @param {Object} options - Rendering options
     */
    async renderTable(data, container, options = {}) {
      await this._ensureRenderer();
      this.renderer.renderTable(data, container, options);
    }

    /**
     * Render a menu with buttons
     * @param {Array} items - Array of menu items {label, action, icon, variant}
     * @param {string|HTMLElement} container - Container selector or element
     */
    async renderMenu(items, container) {
      await this._ensureRenderer();
      this.renderer.renderMenu(items, container);
    }

    /**
     * Render a form with zTheme styling
     * @param {Array} fields - Array of field definitions
     * @param {string|HTMLElement} container - Container selector or element
     * @param {Function} onSubmit - Submit handler
     */
    async renderForm(fields, container, onSubmit) {
      await this._ensureRenderer();
      this.renderer.renderForm(fields, container, onSubmit);
    }

    /**
     * Render a message/alert
     * @param {string} text - Message text
     * @param {string} type - Message type (success, error, warning, info)
     * @param {string|HTMLElement} container - Container selector or element
     * @param {number} duration - Auto-hide duration in ms (0 = no auto-hide)
     */
    async renderMessage(text, type = 'info', container, duration = 5000) {
      await this._ensureRenderer();
      this.renderer.renderMessage(text, type, container, duration);
    }

    // ═══════════════════════════════════════════════════════════
    // Dashboard Rendering (zDash Event)
    // ═══════════════════════════════════════════════════════════

    // NOTE: Dashboard rendering has been extracted to dashboard_renderer.js
    // The onZDash hook now uses the DashboardRenderer class (see _ensureZDisplayRenderer)
    // Legacy methods below are kept for backward compatibility but should not be used directly

    // ═══════════════════════════════════════════════════════════
    // Hook Management
    // ═══════════════════════════════════════════════════════════

    /**
     * Register a new hook at runtime
     * @param {string} hookName - Name of the hook
     * @param {Function} fn - Hook function
     */
    registerHook(hookName, fn) {
      this.hooks.register(hookName, fn);
    }

    /**
     * Unregister a hook
     * @param {string} hookName - Name of the hook
     */
    unregisterHook(hookName) {
      this.hooks.unregister(hookName);
    }

    /**
     * List all registered hooks
     * @returns {Array<string>}
     */
    listHooks() {
      return this.hooks.list();
    }
  }

  // ═══════════════════════════════════════════════════════════
  // Export
  // ═══════════════════════════════════════════════════════════

  return BifrostClient;
}));
