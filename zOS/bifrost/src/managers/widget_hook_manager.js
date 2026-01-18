/**
 * WidgetHookManager - Registers all default widget hooks
 *
 * Responsibilities:
 * - Register onDisplay hook (auto-rendering)
 * - Register onRenderChunk hook (progressive rendering)
 * - Register onInput hook (input rendering)
 * - Register onProgressBar/onProgressComplete hooks
 * - Register onSpinnerStart/onSpinnerStop hooks
 * - Register onSwiperInit/onSwiperUpdate/onSwiperComplete hooks
 * - Register onZDash hook (dashboard rendering)
 *
 * Extracted from bifrost_client.js (Phase 3.4)
 */

export class WidgetHookManager {
  constructor(client) {
    this.client = client;
    this.logger = client.logger;
    this.hooks = client.hooks;
  }

  /**
   * Register all default widget hooks
   */
  async registerAllWidgetHooks() {
    await this.registerDisplayHook();
    await this.registerRenderChunkHook();
    await this.registerInputHook();
    await this.registerProgressBarHooks();
    await this.registerSpinnerHooks();
    await this.registerSwiperHooks();
    await this.registerDashboardHook();
  }

  /**
   * Register onDisplay hook for auto-rendering
   */
  async registerDisplayHook() {
    if (!this.hooks.has('onDisplay')) {
      this.hooks.register('onDisplay', async (event) => {
        this.logger.log('[WidgetHookManager] 📨 onDisplay hook triggered with event:', event);
        this.logger.log('[WidgetHookManager] Auto-rendering zDisplay event:', event);

        // Check if this is a zDialog event (form)
        if (event.event === 'zDialog' || event.display_event === 'zDialog') {
          this.logger.log('[WidgetHookManager] ✅ DETECTED zDialog event - routing to FormRenderer');
          await this.client._ensureFormRenderer();

          const formData = event.data || event;
          const formElement = this.client.formRenderer.renderForm(formData);

          // Append form to appropriate container
          const rootZone = document.getElementById(this.client.zDisplayRenderer.defaultZone);
          const containers = rootZone ? rootZone.querySelectorAll('.zContainer') : [];
          const targetZone = containers.length > 0 ? containers[containers.length - 1] : rootZone;

          if (targetZone) {
            targetZone.appendChild(formElement);
            this.logger.log('[WidgetHookManager] ✅ Form appended to DOM');
          }
        } else {
          // Regular zDisplay event
          this.client.zDisplayRenderer.render(event);
        }
      });
      this.logger.log('[WidgetHookManager] Registered onDisplay hook');
    }
  }

  /**
   * Register onRenderChunk hook for progressive rendering
   */
  async registerRenderChunkHook() {
    if (!this.hooks.has('onRenderChunk')) {
      this.hooks.register('onRenderChunk', async (message) => {
        this.logger.log('[WidgetHookManager] 📦 onRenderChunk hook triggered:', message);
        this.logger.log('[WidgetHookManager] Processing chunk:', message);

        await this.client._renderChunkProgressive(message);

        // Load _zScripts after first chunk renders (ensures DOM elements exist)
        if (!this.client._zScriptsLoaded && message.chunk_num === 1) {
          this.logger.log('[WidgetHookManager] 📦 First chunk rendered - loading _zScripts now');
          this.client._loadZScripts();
          this.client._zScriptsLoaded = true;
        }

        // Cache page after render (debounced)
        if (this.client._cachePageTimeout) {
          clearTimeout(this.client._cachePageTimeout);
        }

        this.client._cachePageTimeout = setTimeout(async () => {
          if (this.client.cache && typeof document !== 'undefined') {
            try {
              const currentPage = window.location.pathname;
              const contentArea = this.client._zVaFElement;
              if (contentArea) {
                await this.client.cache.set(currentPage, contentArea.outerHTML, 'rendered');
                this.logger.log(`[Cache] ✅ Cached content: ${currentPage}`);
              }
            } catch (error) {
              this.logger.error('[Cache] Error caching content:', error);
            }
          }
        }, 500);
      });
      this.logger.log('[WidgetHookManager] Registered onRenderChunk hook');
    }
  }

  /**
   * Register onInput hook for input rendering
   */
  async registerInputHook() {
    if (!this.hooks.has('onInput')) {
      this.hooks.register('onInput', (inputRequest) => {
        this.logger.log('[WidgetHookManager] Rendering input request:', inputRequest);
        const inputType = inputRequest.type || inputRequest.data?.type || 'string';

        if (inputType === 'selection') {
          this.client.zDisplayRenderer.renderSelectionRequest(inputRequest);
        } else if (inputType === 'button') {
          this.client.zDisplayRenderer.renderButtonRequest(inputRequest);
        } else {
          this.client.zDisplayRenderer.renderInputRequest(inputRequest);
        }
      });
      this.logger.log('[WidgetHookManager] Registered onInput hook');
    }
  }

  /**
   * Register progress bar hooks
   */
  async registerProgressBarHooks() {
    if (!this.hooks.has('onProgressBar')) {
      this.hooks.register('onProgressBar', async (event) => {
        this.logger.log('[WidgetHookManager] Progress bar update:', event);
        await this.client._ensureProgressBarRenderer();
        this.client.progressBarRenderer.render(event);
      });
      this.logger.log('[WidgetHookManager] Registered onProgressBar hook');
    }

    if (!this.hooks.has('onProgressComplete')) {
      this.hooks.register('onProgressComplete', async (event) => {
        this.logger.log('[WidgetHookManager] Progress complete:', event);
        await this.client._ensureProgressBarRenderer();
        this.client.progressBarRenderer.complete(event);
      });
      this.logger.log('[WidgetHookManager] Registered onProgressComplete hook');
    }
  }

  /**
   * Register spinner hooks
   */
  async registerSpinnerHooks() {
    if (!this.hooks.has('onSpinnerStart')) {
      this.hooks.register('onSpinnerStart', async (event) => {
        this.logger.log('[WidgetHookManager] Spinner start:', event);
        await this.client._ensureSpinnerRenderer();
        this.client.spinnerRenderer.start(event);
      });
      this.logger.log('[WidgetHookManager] Registered onSpinnerStart hook');
    }

    if (!this.hooks.has('onSpinnerStop')) {
      this.hooks.register('onSpinnerStop', async (event) => {
        this.logger.log('[WidgetHookManager] Spinner stop:', event);
        await this.client._ensureSpinnerRenderer();
        this.client.spinnerRenderer.stop(event);
      });
      this.logger.log('[WidgetHookManager] Registered onSpinnerStop hook');
    }
  }

  /**
   * Register swiper hooks
   */
  async registerSwiperHooks() {
    if (!this.hooks.has('onSwiperInit')) {
      this.hooks.register('onSwiperInit', async (event) => {
        this.logger.log('[WidgetHookManager] Swiper init:', event);
        await this.client._ensureSwiperRenderer();
        this.client.swiperRenderer.init(event);
      });
      this.logger.log('[WidgetHookManager] Registered onSwiperInit hook');
    }

    if (!this.hooks.has('onSwiperUpdate')) {
      this.hooks.register('onSwiperUpdate', async (event) => {
        this.logger.log('[WidgetHookManager] Swiper update:', event);
        await this.client._ensureSwiperRenderer();
        this.client.swiperRenderer.update(event);
      });
      this.logger.log('[WidgetHookManager] Registered onSwiperUpdate hook');
    }

    if (!this.hooks.has('onSwiperComplete')) {
      this.hooks.register('onSwiperComplete', async (event) => {
        this.logger.log('[WidgetHookManager] Swiper complete:', event);
        await this.client._ensureSwiperRenderer();
        this.client.swiperRenderer.complete(event);
      });
      this.logger.log('[WidgetHookManager] Registered onSwiperComplete hook');
    }
  }

  /**
   * Register dashboard hook
   */
  async registerDashboardHook() {
    if (!this.hooks.has('onZDash')) {
      this.hooks.register('onZDash', async (dashConfig) => {
        this.logger.log('[WidgetHookManager] 📊 onZDash hook triggered:', dashConfig);
        await this.client._ensureDashboardRenderer();
        await this.client.dashboardRenderer.render(dashConfig, this.client._zVaFElement);
      });
      this.logger.log('[WidgetHookManager] Registered onZDash hook');
    }
  }
}

export default WidgetHookManager;

