/**
 * DeclarativeUILoader - Handles loading and parsing of declarative YAML UI files
 *
 * Responsible for:
 * - Fetching YAML files from server
 * - Parsing YAML using js-yaml
 * - Resolving meta.zNavBar (global vs local)
 * - Delegating rendering to ZDisplayOrchestrator
 *
 * Extracted from bifrost_client.js (Phase 2.2)
 */

export class DeclarativeUILoader {
  constructor(client) {
    this.client = client;
    this.logger = client.logger;
    this.options = client.options;
    this.zuiConfig = client.zuiConfig;
  }

  /**
   * Load and render declarative UI from zVaFile (client-side YAML parsing)
   */
  async loadDeclarativeUI() {
    try {
      this.logger.log('🎨 Loading declarative UI...');

      // Construct URL from zVaFolder and zVaFile
      const folder = this.options.zVaFolder || 'UI';
      const file = this.options.zVaFile;
      const block = this.options.zBlock || 'zVaF';

      // Convert zPath (@.UI) to URL path
      const urlPath = folder.startsWith('@.') ? folder.substring(2) : folder;
      const yamlUrl = `/${urlPath}/${file}.yaml`;

      this.logger.log(`📥 Fetching: ${yamlUrl}`);

      // Fetch YAML file
      const response = await fetch(yamlUrl);
      if (!response.ok) {
        throw new Error(`Failed to fetch ${yamlUrl}: ${response.status} ${response.statusText}`);
      }

      const yamlText = await response.text();
      this.logger.log('✅ YAML fetched, parsing...');

      // Parse YAML (using js-yaml from CDN)
      if (typeof jsyaml === 'undefined') {
        throw new Error('js-yaml library not loaded');
      }

      const yamlData = jsyaml.load(yamlText);
      this.logger.log('✅ YAML parsed:', yamlData);

      // Check for meta.zNavBar and render it at the top (website-style navigation)
      if (yamlData.meta && yamlData.meta.zNavBar) {
        this.logger.log('🔗 Resolving meta.zNavBar...');

        // Resolve navbar: true → global, array → local override
        let navbarItems = yamlData.meta.zNavBar;

        if (navbarItems === true) {
          // Opt-in to global navbar from zuiConfig
          this.logger.log('[DeclarativeUILoader] 🎯 meta.zNavBar: true, checking zuiConfig...');
          this.logger.log('[DeclarativeUILoader] 🎯 this.zuiConfig:', this.zuiConfig);

          if (this.zuiConfig && this.zuiConfig.zNavBar) {
            navbarItems = this.zuiConfig.zNavBar;
            this.logger.log('[DeclarativeUILoader] ✅ Using global navbar from config:', navbarItems);
            this.logger.log('✅ Using global navbar from config:', navbarItems);
          } else {
            this.logger.warn('[DeclarativeUILoader] ⚠️ meta.zNavBar: true but no global navbar in zuiConfig');
            this.logger.warn('[DeclarativeUILoader] meta.zNavBar: true but no global navbar in zuiConfig');
            navbarItems = null;
          }
        } else if (Array.isArray(navbarItems)) {
          this.logger.log('[DeclarativeUILoader] ✅ Using local navbar override:', navbarItems);
          this.logger.log('✅ Using local navbar override:', navbarItems);
        } else {
          this.logger.warn('[DeclarativeUILoader] ⚠️ Invalid meta.zNavBar value:', navbarItems);
          this.logger.warn('[DeclarativeUILoader] Invalid meta.zNavBar value:', navbarItems);
          navbarItems = null;
        }

        if (navbarItems && Array.isArray(navbarItems)) {
          // Render navbar using ZDisplayOrchestrator
          await this.client._ensureZDisplayOrchestrator();
          const renderedNavbar = await this.client.zDisplayOrchestrator.renderMetaNavBarHTML(navbarItems);

          // 🔧 FIX v1.6.1: Append DOM element directly (NOT innerHTML!)
          const navContainer = document.querySelector('zNavBar');
          if (navContainer && renderedNavbar) {
            navContainer.innerHTML = ''; // Clear first
            navContainer.appendChild(renderedNavbar);
            this.logger.log('[DeclarativeUILoader] ✅ Navbar rendered to page (DOM element)');
          } else if (!renderedNavbar) {
            this.logger.warn('[DeclarativeUILoader] renderMetaNavBarHTML returned null');
          }
        }
      }

      // Extract the specified block
      const blockData = yamlData[block];
      if (!blockData) {
        throw new Error(`Block "${block}" not found in ${yamlUrl}`);
      }

      this.logger.log(`✅ Rendering block: ${block}`);

      // Render the block declaratively (preserves _zClass and all styling)
      await this.client._ensureZDisplayOrchestrator();
      await this.client.zDisplayOrchestrator.renderBlock(blockData);

      this.logger.log('✅ Declarative UI loaded successfully');

    } catch (error) {
      this.logger.error('Failed to load declarative UI:', error);
      throw error;
    }
  }
}

export default DeclarativeUILoader;

