/**
 * ZDisplayOrchestrator - Central orchestrator for all declarative rendering
 *
 * Handles:
 * - YAML → DOM rendering
 * - Progressive chunk rendering
 * - Block-level metadata
 * - Recursive item rendering
 * - zDisplay event routing
 * - Navbar rendering
 *
 * Extracted from bifrost_client.js (Phase 2.1)
 */

export class ZDisplayOrchestrator {
  constructor(client) {
    this.client = client;
    this.logger = client.logger;
    this.options = client.options;
  }

  /**
   * Render an entire zVaF block from YAML data
   * @param {Object} blockData - Block configuration from YAML
   */
  async renderBlock(blockData) {
    // Use stored reference (set by _initZVaFElements)
    const contentElement = this.client._zVaFElement;
    if (!contentElement) {
      throw new Error('zVaF element not initialized');
    }

    // Clear existing content
    contentElement.innerHTML = '';

    // Check if blockData has block-level metadata (_zClass) for cascading
    let blockWrapper = contentElement;
    if (blockData && typeof blockData === 'object' && blockData._zClass) {
      // Create wrapper div for the entire block with block-level classes (using primitive)
      const { createDiv } = await import('./primitives/generic_containers.js');
      const blockLevelDiv = createDiv();
      const blockName = this.options.zBlock || 'zBlock';

      // Apply block-level classes
      const classes = Array.isArray(blockData._zClass)
        ? blockData._zClass
        : blockData._zClass.split(',').map(c => c.trim());
      blockLevelDiv.className = classes.join(' ');
      blockLevelDiv.setAttribute('data-zblock', blockName);

      contentElement.appendChild(blockLevelDiv);
      blockWrapper = blockLevelDiv;  // Children render inside the block wrapper

      this.logger.log(`[ZDisplayOrchestrator] Created block-level wrapper with classes: ${blockData._zClass}`);
    }

    // Recursively render all items (await for navigation renderer loading)
    await this.renderItems(blockData, blockWrapper);

    // Enhance block-level zCard if present
    if (blockWrapper !== contentElement && blockWrapper.classList.contains('zCard')) {
      const cardRenderer = await this.client._ensureCardRenderer();
      cardRenderer.enhanceCard(blockWrapper);
      this.logger.log('[ZDisplayOrchestrator] Enhanced block-level zCard');
    }
  }

  /**
   * Progressive chunk rendering (Terminal First philosophy)
   * Appends chunks from backend as they arrive, stops at failed gates
   * @param {Object} message - Chunk message from backend
   */
  async renderChunkProgressive(message) {
    try {
      this.logger.log('[ZDisplayOrchestrator] 🎬 renderChunkProgressive called with:', message);
      const {chunk_num, keys, data, is_gate} = message;

      this.logger.log(`[ZDisplayOrchestrator] 📦 Rendering chunk #${chunk_num}: ${keys.join(', ')}`);
      this.logger.log(`[ZDisplayOrchestrator] 📦 Rendering chunk #${chunk_num}: ${keys.join(', ')}`);
      if (is_gate) {
        this.logger.log('[ZDisplayOrchestrator] 🚪 Chunk contains gate - backend will stop if gate fails');
      }

      // Check if we're rendering into a dashboard panel (zDash context)
      const dashboardPanelContent = document.getElementById('dashboard-panel-content');
      const contentDiv = dashboardPanelContent || this.client._zVaFElement;

      if (!contentDiv) {
        throw new Error('zVaF element not initialized. Ensure _initZVaFElements() was called.');
      }

      // Check if data has block-level metadata (_zClass, _zStyle, etc.)
      const hasBlockMetadata = data && Object.keys(data).some(k => k.startsWith('_'));

      // Determine the target container for rendering
      let targetContainer = contentDiv;

      // ALWAYS clear loading state on first chunk (regardless of metadata)
      if (chunk_num === 1) {
        contentDiv.innerHTML = '';
        this.logger.log('[ZDisplayOrchestrator] 📦 Cleared loading state for chunk #1');
      }

      if (hasBlockMetadata && chunk_num === 1) {
        // First chunk with block metadata: create a wrapper for the entire block
        const blockName = message.zBlock || 'progressive';  // Use block name from backend
        
        // Check for _zHTML parameter to determine element type
        const elementType = data._zHTML || 'div';
        const validElements = ['div', 'section', 'article', 'aside', 'nav', 'header', 'footer', 'main'];
        const tagName = validElements.includes(elementType) ? elementType : 'div';
        
        // Create the container with the specified element type
        const blockWrapper = document.createElement(tagName);
        blockWrapper.setAttribute('data-zblock', 'progressive');
        blockWrapper.setAttribute('id', blockName);

        // Apply block-level metadata to wrapper
        for (const [key, value] of Object.entries(data)) {
          if (key === '_zClass' && value) {
            blockWrapper.className = value;
          } else if (key === '_zStyle' && value) {
            blockWrapper.setAttribute('style', value);
          }
          // _zHTML is already handled above (element creation)
        }

        contentDiv.appendChild(blockWrapper);
        targetContainer = blockWrapper;
        this.logger.log(`[ZDisplayOrchestrator] 📦 Created block wrapper "${blockName}" with metadata for progressive rendering`);
      } else if (hasBlockMetadata && chunk_num > 1) {
        // Subsequent chunks: find existing block wrapper
        const existingWrapper = contentDiv.querySelector('[data-zblock="progressive"]');
        if (existingWrapper) {
          targetContainer = existingWrapper;
          this.logger.log(`[ZDisplayOrchestrator] 📦 Using existing block wrapper for chunk #${chunk_num}`);
        }
      }

      // Render YAML data using existing rendering pipeline
      // This preserves all styling, forms, zDisplay events, etc.
      if (data && typeof data === 'object') {
        // DEBUG: Log chunk data structure
        this.logger.log('[ZDisplayOrchestrator] 🔍 Chunk data keys:', Object.keys(data));
        for (const [key, value] of Object.entries(data)) {
          if (!key.startsWith('_')) {
            this.logger.log(`[ZDisplayOrchestrator] 🔍   ${key}:`, typeof value, Array.isArray(value) ? `array[${value.length}]` : (typeof value === 'object' ? `object{${Object.keys(value).join(',')}}` : value));
          }
        }
        await this.renderItems(data, targetContainer);
        this.logger.log(`[ZDisplayOrchestrator] ✅ Chunk #${chunk_num} rendered from YAML (${keys.length} keys)`);
        
        // Re-initialize zTheme components after rendering new content
        if (window.zTheme && typeof window.zTheme.initRangeSliders === 'function') {
          window.zTheme.initRangeSliders();
          this.logger.log('[ZDisplayOrchestrator] 🎨 Re-initialized range sliders');
        }
      } else {
        this.logger.warn(`[ZDisplayOrchestrator] ⚠️ Chunk #${chunk_num} has no YAML data to render`);
      }

      // If this is a gate chunk, log that we're waiting for backend
      if (is_gate) {
        this.logger.log('[ZDisplayOrchestrator] ⏸️  Waiting for gate completion (backend controls flow)');
      }

    } catch (error) {
      this.logger.error('Failed to render chunk:', error);
      throw error;
    }
  }

  /**
   * Extract plural shorthands (zURLs, zTexts, zImages, etc.) and transform to items array
   * @param {Object} value - The zUL/zOL value object
   * @param {string} listStyle - 'bullet' or 'number' (for logging)
   * @returns {{items: Array, otherProps: Object}} - Transformed items and remaining properties
   * @private
   */
  _extractPluralShorthands(value, listStyle) {
    const items = [];
    const otherProps = {};
    
    // Map plural shorthand keys to their singular event types
    const pluralMap = {
      'zURLs': 'zURL',
      'zTexts': 'zText',
      'zImages': 'zImage',
      'zH1s': 'zH1',
      'zH2s': 'zH2',
      'zH3s': 'zH3',
      'zH4s': 'zH4',
      'zH5s': 'zH5',
      'zH6s': 'zH6',
      'zMDs': 'zMD'
    };
    
    // Iterate through value properties
    for (const [key, val] of Object.entries(value)) {
      if (pluralMap[key] && val && typeof val === 'object' && !Array.isArray(val)) {
        // Found a plural shorthand (e.g., zURLs)
        const singularEvent = pluralMap[key];
        
        // Transform each nested object into a zDisplay item
        for (const [itemKey, itemProps] of Object.entries(val)) {
          if (itemProps && typeof itemProps === 'object') {
            items.push({
              zDisplay: {
                event: singularEvent,
                ...itemProps
              }
            });
          }
        }
        
        this.logger.log(`[ZDisplayOrchestrator] 🔄 Transformed ${key} into ${items.length} ${singularEvent} items`);
      } else {
        // Not a plural shorthand, copy to otherProps (e.g., _zClass, indent)
        otherProps[key] = val;
      }
    }
    
    return { items, otherProps };
  }

  /**
   * Recursively render YAML items (handles nested structures like implicit wizards)
   * @param {Object} data - YAML data to render
   * @param {HTMLElement} parentElement - Parent element to render into
   */
  async renderItems(data, parentElement) {
    if (!data || typeof data !== 'object') {
      this.logger.log('[ZDisplayOrchestrator] renderItems: No data or not an object');
      return;
    }

    this.logger.log('[ZDisplayOrchestrator] 🔄 renderItems called with keys:', Object.keys(data));

    // Check if parent already has block-level metadata applied (data-zblock attribute)
    const _parentIsBlockWrapper = parentElement.hasAttribute && parentElement.hasAttribute('data-zblock');

    // Extract metadata first (underscore-prefixed keys like _zClass)
    const metadata = {};
    for (const [key, value] of Object.entries(data)) {
      if (key.startsWith('_')) {
        metadata[key] = value;
      }
    }

    // ═══════════════════════════════════════════════════════════════════════
    // SHORTHAND SYNTAX EXPANSION (zH1-zH6, zText, zUL, zOL, zTable, zMD, zImage, zURL)
    // ═══════════════════════════════════════════════════════════════════════
    // Transform shorthand syntax into full zDisplay format before rendering
    // Examples: 
    //   {zH2: {label: "Title"}} → {zDisplay: {event: "header", indent: 2, label: "Title"}}
    //   {zText: {content: "..."}} → {zDisplay: {event: "text", content: "..."}}
    //   {zUL: {items: [...]}} → {zDisplay: {event: "list", style: "bullet", items: [...]}}
    //   {zOL: {items: [...]}} → {zDisplay: {event: "list", style: "number", items: [...]}}
    //   {zTable: {columns: [...], rows: [...]}} → {zDisplay: {event: "zTable", ...}}
    //   {zMD: {content: "..."}} → {zDisplay: {event: "rich_text", content: "..."}}
    //   {zImage: {src: "...", alt_text: "..."}} → {zDisplay: {event: "image", src: "...", alt_text: "..."}}
    //   {zURL: {label: "...", href: "..."}} → {zDisplay: {event: "zURL", label: "...", href: "..."}}
    // NOTE: Keys may have __dup{N} suffix from LSP parser to preserve duplicate UI events
    //   {zText__dup2: {content: "..."}} → Strip suffix before matching shorthand patterns
    // ═══════════════════════════════════════════════════════════════════════
    for (const [key, value] of Object.entries(data)) {
      // Strip __dup{N} suffix for shorthand matching (LSP duplicate key handling)
      const cleanKey = key.includes('__dup') ? key.split('__dup')[0] : key;
      
      if (cleanKey.startsWith('zH') && cleanKey.length === 3 && /^[1-6]$/.test(cleanKey[2])) {
        const indent = parseInt(cleanKey[2], 10);
        if (value && typeof value === 'object' && !Array.isArray(value)) {
          // Skip expansion if already expanded by backend (has zDisplay key)
          if (!value.zDisplay) {
            // Transform shorthand to full zDisplay format
            data[key] = {
              zDisplay: {
                event: 'header',
                indent: indent,
                ...value
              }
            };
            this.logger.log(`[ZDisplayOrchestrator] ✨ Expanded ${key} shorthand to zDisplay header (indent: ${indent})`);
          } else {
            this.logger.log(`[ZDisplayOrchestrator] ⏭️  Skipped ${key} expansion (already expanded by backend)`);
          }
        }
      } else if (cleanKey === 'zText') {
        if (value && typeof value === 'object' && !Array.isArray(value)) {
          // Skip expansion if already expanded by backend (has zDisplay key)
          if (!value.zDisplay) {
            // Transform shorthand to full zDisplay format
            data[key] = {
              zDisplay: {
                event: 'text',
                ...value
              }
            };
            this.logger.log(`[ZDisplayOrchestrator] ✨ Expanded ${key} (${cleanKey}) shorthand to zDisplay text`);
          } else {
            this.logger.log(`[ZDisplayOrchestrator] ⏭️  Skipped ${key} expansion (already expanded by backend)`);
          }
        }
      } else if (cleanKey === 'zUL') {
        if (value && typeof value === 'object' && !Array.isArray(value)) {
          // Skip expansion if already expanded by backend (has zDisplay key)
          if (!value.zDisplay) {
            // Check for plural shorthands and transform them
            const { items, otherProps } = this._extractPluralShorthands(value, 'bullet');
            
            // Transform shorthand to full zDisplay format (unordered/bullet list)
            data[key] = {
              zDisplay: {
                event: 'list',
                style: 'bullet',
                ...otherProps,
                ...(items.length > 0 && { items })  // Only add items if plural shorthand found
              }
            };
            this.logger.log(`[ZDisplayOrchestrator] ✨ Expanded zUL shorthand to zDisplay list (bullet)${items.length > 0 ? ` with ${items.length} items from plural shorthand` : ''}`);
          } else {
            this.logger.log(`[ZDisplayOrchestrator] ⏭️  Skipped zUL expansion (already expanded by backend)`);
          }
        }
      } else if (cleanKey === 'zOL') {
        if (value && typeof value === 'object' && !Array.isArray(value)) {
          // Skip expansion if already expanded by backend (has zDisplay key)
          if (!value.zDisplay) {
            // Check for plural shorthands and transform them
            const { items, otherProps } = this._extractPluralShorthands(value, 'number');
            
            // Transform shorthand to full zDisplay format (ordered/numbered list)
            data[key] = {
              zDisplay: {
                event: 'list',
                style: 'number',
                ...otherProps,
                ...(items.length > 0 && { items })  // Only add items if plural shorthand found
              }
            };
            this.logger.log(`[ZDisplayOrchestrator] ✨ Expanded zOL shorthand to zDisplay list (number)${items.length > 0 ? ` with ${items.length} items from plural shorthand` : ''}`);
          } else {
            this.logger.log(`[ZDisplayOrchestrator] ⏭️  Skipped zOL expansion (already expanded by backend)`);
          }
        }
      } else if (cleanKey === 'zTable') {
        if (value && typeof value === 'object' && !Array.isArray(value)) {
          // Skip expansion if already expanded by backend (has zDisplay key)
          if (!value.zDisplay) {
            // Transform shorthand to full zDisplay format (table)
            data[key] = {
              zDisplay: {
                event: 'zTable',
                ...value
              }
            };
            this.logger.log(`[ZDisplayOrchestrator] ✨ Expanded zTable shorthand to zDisplay zTable`);
          } else {
            this.logger.log(`[ZDisplayOrchestrator] ⏭️  Skipped zTable expansion (already expanded by backend)`);
          }
        }
      } else if (cleanKey === 'zMD') {
        if (value && typeof value === 'object' && !Array.isArray(value)) {
          // Skip expansion if already expanded by backend (has zDisplay key)
          if (!value.zDisplay) {
            // Transform shorthand to full zDisplay format (rich_text/markdown)
            data[key] = {
              zDisplay: {
                event: 'rich_text',
                ...value
              }
            };
            this.logger.log(`[ZDisplayOrchestrator] ✨ Expanded zMD shorthand to zDisplay rich_text`);
          } else {
            this.logger.log(`[ZDisplayOrchestrator] ⏭️  Skipped zMD expansion (already expanded by backend)`);
          }
        }
      } else if (cleanKey === 'zImage') {
        if (value && typeof value === 'object' && !Array.isArray(value)) {
          // Skip expansion if already expanded by backend (has zDisplay key)
          if (!value.zDisplay) {
            // Transform shorthand to full zDisplay format (image)
            data[key] = {
              zDisplay: {
                event: 'image',
                ...value
              }
            };
            this.logger.log(`[ZDisplayOrchestrator] ✨ Expanded ${key} (${cleanKey}) shorthand to zDisplay image`);
          } else {
            this.logger.log(`[ZDisplayOrchestrator] ⏭️  Skipped zImage expansion (already expanded by backend)`);
          }
        }
      } else if (cleanKey === 'zURL') {
        if (value && typeof value === 'object' && !Array.isArray(value)) {
          // Skip expansion if already expanded by backend (has zDisplay key)
          if (!value.zDisplay) {
            // Transform shorthand to full zDisplay format (link/URL)
            data[key] = {
              zDisplay: {
                event: 'zURL',
                ...value
              }
            };
            this.logger.log(`[ZDisplayOrchestrator] ✨ Expanded ${key} (${cleanKey}) shorthand to zDisplay zURL`);
          } else {
            this.logger.log(`[ZDisplayOrchestrator] ⏭️  Skipped zURL expansion (already expanded by backend)`);
          }
        }
      }
    }

    // ═══════════════════════════════════════════════════════════════════════
    // NEW: _zGroup Support - Grouped Rendering for Bifrost
    // ═══════════════════════════════════════════════════════════════════════
    // If _zGroup metadata is present, render all children into a single
    // grouped container (e.g., flex row for buttons, grid for cards)
    // This allows Terminal to process items sequentially while Bifrost
    // groups them visually - metadata-driven optimization!
    // ═══════════════════════════════════════════════════════════════════════
    if (metadata._zGroup) {
      this.logger.log(`[ZDisplayOrchestrator] 🎯 _zGroup detected: "${metadata._zGroup}" - rendering as grouped container`);
      this.logger.log(`🎯 _zGroup detected: "${metadata._zGroup}"`);

      // Create group container with zTheme classes based on _zGroup type
      const groupContainer = document.createElement('div');
      groupContainer.setAttribute('data-zgroup', metadata._zGroup);

      // Apply zTheme container class based on group type
      if (metadata._zGroup === 'list-group') {
        groupContainer.classList.add('zList-group');
        this.logger.log('  Applied zTheme class: zList-group');
      }

      // Apply additional _zClass styling if provided (from YAML)
      if (metadata._zClass) {
        const classes = metadata._zClass.split(' ').filter(c => c.trim());
        if (classes.length > 0) {
          groupContainer.classList.add(...classes);
          this.logger.log(`  Applied additional _zClass: ${metadata._zClass}`);
        }
      }

      // Iterate through all non-metadata children and render into group
      for (const [key, value] of Object.entries(data)) {
        // Skip ONLY metadata keys (not organizational containers like _Visual_Progression)
        const METADATA_KEYS = ['_zClass', '_zStyle', '_zHTML', '_zId', '_zScripts', '_zGroup', 'zId'];
        if (METADATA_KEYS.includes(key) || key.startsWith('~')) {
          continue;
        }

        this.logger.log(`  Rendering grouped item: ${key}`);

        // Handle list/array values (zDisplay events)
        if (Array.isArray(value)) {
          for (const item of value) {
            if (item && item.zDisplay) {
              // ✅ SEPARATION OF CONCERNS: Render element without group context
              const element = await this.renderZDisplayEvent(item.zDisplay);
              if (element) {
                // Apply group-specific styling AFTER rendering
                this._applyGroupStyling(element, metadata._zGroup, item.zDisplay);
                groupContainer.appendChild(element);
              }
            }
          }
        } else if (value && value.zDisplay) {
          // Handle direct zDisplay event
          // ✅ SEPARATION OF CONCERNS: Render element without group context
          const element = await this.renderZDisplayEvent(value.zDisplay);
          if (element) {
            // Apply group-specific styling AFTER rendering
            this._applyGroupStyling(element, metadata._zGroup, value.zDisplay);
            groupContainer.appendChild(element);
          }
        } else if (value && typeof value === 'object') {
          // Handle nested objects (recurse)
          // DEBUG: Log organizational containers
          if (key.startsWith('_')) {
            this.logger.log(`🏗️  [GROUP] Processing organizational container: ${key}`);
          }
          
          // Check for _zHTML parameter to determine element type
          const elementType = value._zHTML || 'div';
          const validElements = ['div', 'section', 'article', 'aside', 'nav', 'header', 'footer', 'main'];
          const tagName = validElements.includes(elementType) ? elementType : 'div';
          const itemDiv = document.createElement(tagName);
          itemDiv.setAttribute('data-zkey', key);
          
          // Apply metadata to the organizational container
          if (value._zClass) {
            itemDiv.className = value._zClass;
          }
          if (value._zStyle) {
            itemDiv.setAttribute('style', value._zStyle);
          }
          
          await this.renderItems(value, itemDiv);
          
          if (itemDiv.children.length > 0) {
            // BUG FIX: If wrapper has only 1 child and no classes, unwrap it
            // This handles zText with semantic:div where the div itself has styling
            if (itemDiv.children.length === 1 && !itemDiv.className) {
              const child = itemDiv.children[0];
              // Transfer data-zkey and id to the child
              child.setAttribute('data-zkey', key);
              if (!child.id) {
                child.setAttribute('id', key);
              }
              groupContainer.appendChild(child);
            } else {
              groupContainer.appendChild(itemDiv);
            }
            
            if (key.startsWith('_')) {
              this.logger.log(`✅ [GROUP] Rendered organizational container ${key} with ${itemDiv.children.length} children`);
            }
          }
        }
      }

      // Append group to parent
      if (groupContainer.children.length > 0) {
        parentElement.appendChild(groupContainer);
        this.logger.log(`[ZDisplayOrchestrator] ✅ Grouped container rendered with ${groupContainer.children.length} items`);
        this.logger.log(`✅ Grouped container rendered with ${groupContainer.children.length} items`);
      }

      // Exit early - we've handled all children in the group
      return;
    }

    // ═══════════════════════════════════════════════════════════════════════
    // Regular (non-grouped) rendering continues below
    // ═══════════════════════════════════════════════════════════════════════

    // Iterate through all keys in this level
    for (const [key, value] of Object.entries(data)) {
      // Handle metadata keys BEFORE skipping
      if (key.startsWith('~')) {
        // Navigation metadata: ~zNavBar*
        if (key.startsWith('~zNavBar')) {
          await this.renderNavBar(value, parentElement);
          continue;
        }
        // Other metadata keys - skip for now
        continue;
      }

      // Skip ONLY metadata attributes (not terminal-suppressed elements)
      // _zClass, _zStyle, _zHTML, _zId, _zScripts are metadata attributes applied to parent
      // But _Demo_Stack, _Live_Demo_Section are terminal-suppressed elements that SHOULD render in Bifrost
      const METADATA_KEYS = ['_zClass', '_zStyle', '_zHTML', '_zId', '_zScripts', 'zId'];
      if (METADATA_KEYS.includes(key)) {
        continue;
      }

      this.logger.log(`Rendering item: ${key}`, value);

      // Check if this value has its own metadata (for nested _zClass support)
      let itemMetadata = {};

      // Each zKey container should ONLY use its OWN _zClass/_zStyle/_zHTML/zId, never inherit from parent
      // This ensures ProfilePicture doesn't get ProfileHeader's classes
      if (value && typeof value === 'object' && !Array.isArray(value)) {
        if (value._zClass !== undefined || value._zStyle !== undefined || value._zHTML !== undefined || value.zId !== undefined) {
          itemMetadata = {
            _zClass: value._zClass,
            _zStyle: value._zStyle,
            _zHTML: value._zHTML,
            zId: value.zId
          };
          this.logger.log(`  Found nested metadata for ${key}:`, itemMetadata);
          // DEBUG: Log organizational container metadata
          if (key.startsWith('_Box_') || key.startsWith('_Visual_')) {
            console.log(`🎨 [METADATA] ${key}:`, {
              _zClass: value._zClass,
              _zStyle: value._zStyle,
              hasZDisplay: !!value.zDisplay,
              allKeys: Object.keys(value)
            });
          }
        }
      }

      // Create container wrapper for this zKey (zTheme responsive layout)
      const containerDiv = await this.createContainer(key, itemMetadata);

      // Give container a data attribute for debugging
      containerDiv.setAttribute('data-zkey', key);
      // Set id for DevTools navigation and CSS targeting (unless custom zId provided)
      if (!itemMetadata.zId) {
        containerDiv.setAttribute('id', key);
      }

      // Handle list/array values (sequential zDisplay events, zDialog forms, OR menus)
      if (Array.isArray(value)) {
        this.logger.log(`[ZDisplayOrchestrator] ✅ Detected list/array for key: ${key}, items: ${value.length}`);
        this.logger.log(`✅ Detected list/array for key: ${key}, items: ${value.length}`);

        // Check if this is a menu (has * modifier and array of strings)
        const isMenu = key.includes('*') && value.every(item => typeof item === 'string');

        if (isMenu) {
          this.logger.log(`[ZDisplayOrchestrator] 🎯 Detected MENU: ${key}`);
          this.logger.log(`🎯 Detected menu with ${value.length} options`);

          // Load menu renderer and render the menu
          const menuRenderer = await this.client._ensureMenuRenderer();
          if (menuRenderer) {
            // Prepare menu data (matching backend zMenu event format)
            const menuData = {
              menu_key: key,
              options: value,
              title: key.replace(/[*~^$]/g, '').trim() || 'Menu',
              allow_back: true
            };

            // Render menu into container
            menuRenderer.renderMenuInline(menuData, containerDiv);
            this.logger.log(`✅ Menu rendered for ${key}`);
          } else {
            this.logger.error('[ZDisplayOrchestrator] ❌ MenuRenderer not available');
          }
        } else {
          // Regular list/array - iterate through items
          for (const item of value) {
            if (item && item.zDisplay) {
              this.logger.log('[ZDisplayOrchestrator]   ✅ Rendering zDisplay event:', item.zDisplay.event);
              this.logger.log('  ✅ Rendering zDisplay from list item:', item.zDisplay);
              const element = await this.renderZDisplayEvent(item.zDisplay);
              if (element) {
                this.logger.log('  ✅ Appended element to container');
                containerDiv.appendChild(element);
              }
            } else if (item && item.zDialog) {
              this.logger.log('  ✅ Rendering zDialog from list item:', item.zDialog);
              const formRenderer = await this.client._ensureFormRenderer();
              const formElement = formRenderer.renderForm(item.zDialog);
              if (formElement) {
                this.logger.log('  ✅ Appended zDialog form to container');
                containerDiv.appendChild(formElement);
              }
            } else if (item && typeof item === 'object') {
              // Nested object in list - recurse
              await this.renderItems(item, containerDiv);
            }
          }
        }
      } else if (value && value.zDisplay) {
        // Check if this has a direct zDisplay event
        this.logger.log(`[renderItems] 🎯 Direct zDisplay for ${key}, containerDiv classes: "${containerDiv.className}"`);
        const element = await this.renderZDisplayEvent(value.zDisplay);
        if (element) {
          // BUG FIX: For direct UI events (zText, zH*, zMD, etc.), apply classes ONLY to the element
          // This prevents double-wrapping and ensures grid classes work correctly
          // Check if element has the same classes as containerDiv (indicating double-application)
          if (containerDiv.className && element.className && containerDiv.className === element.className) {
            this.logger.log(`[renderItems] 🔓 Unwrapping ${key}: element already has classes "${element.className}", skipping wrapper`);
            // Transfer data-zkey and id to the element
            element.setAttribute('data-zkey', key);
            if (!element.id) {
              element.setAttribute('id', key);
            }
            // Append element directly to parent (skip containerDiv)
            parentElement.appendChild(element);
            continue; // Skip the rest of the loop (don't append containerDiv)
          } else if (!containerDiv.className || containerDiv.className === '') {
            this.logger.log(`[renderItems] 🔓 Unwrapping ${key}: no container classes, appending element directly to parent`);
            // Transfer data-zkey and id to the element
            element.setAttribute('data-zkey', key);
            if (!element.id) {
              element.setAttribute('id', key);
            }
            // Append element directly to parent (skip containerDiv)
            parentElement.appendChild(element);
            continue; // Skip the rest of the loop (don't append containerDiv)
          } else {
            this.logger.log(`[renderItems] 🔒 Keeping wrapper for ${key}: container has classes "${containerDiv.className}", element has "${element.className}"`);
            containerDiv.appendChild(element);
          }
        }
      } else if (value && value.event && typeof value.event === 'string') {
        // 🆕 Backend now sends unwrapped zDisplay events (direct event key, no zDisplay wrapper)
        // Example: {event: 'zCrumbs', show: 'static', ...}
        this.logger.log(`[renderItems] 🎯 Found direct event key: ${value.event} for ${key}, containerDiv classes: "${containerDiv.className}"`);
        const element = await this.renderZDisplayEvent(value);
        if (element) {
          // BUG FIX: For direct UI events, apply classes ONLY to the element
          // Check if element has the same classes as containerDiv (indicating double-application)
          if (containerDiv.className && element.className && containerDiv.className === element.className) {
            this.logger.log(`[renderItems] 🔓 Unwrapping ${key}: element already has classes "${element.className}", skipping wrapper`);
            // Transfer data-zkey and id to the element
            element.setAttribute('data-zkey', key);
            if (!element.id) {
              element.setAttribute('id', key);
            }
            // Append element directly to parent (skip containerDiv)
            parentElement.appendChild(element);
            continue; // Skip the rest of the loop (don't append containerDiv)
          } else if (!containerDiv.className || containerDiv.className === '') {
            this.logger.log(`[renderItems] 🔓 Unwrapping ${key}: no container classes, appending element directly to parent`);
            // Transfer data-zkey and id to the element
            element.setAttribute('data-zkey', key);
            if (!element.id) {
              element.setAttribute('id', key);
            }
            // Append element directly to parent (skip containerDiv)
            parentElement.appendChild(element);
            continue; // Skip the rest of the loop (don't append containerDiv)
          } else {
            this.logger.log(`[renderItems] 🔒 Keeping wrapper for ${key}: container has classes "${containerDiv.className}", element has "${element.className}"`);
            containerDiv.appendChild(element);
          }
        }
      } else if (value && value.zDialog) {
        // Check if this has a direct zDialog form
        this.logger.log('  ✅ Rendering zDialog from direct value:', value.zDialog);
        const formRenderer = await this.client._ensureFormRenderer();
        const formElement = formRenderer.renderForm(value.zDialog);
        if (formElement) {
          containerDiv.appendChild(formElement);
        }
      } else if (value && typeof value === 'object' && Object.keys(value).length > 0) {
        // Check if this is a shorthand UI element (zCheckbox, zText, zImage, etc.)
        // A shorthand has exactly ONE non-metadata key that's a recognized UI element
        const allKeys = Object.keys(value);
        const nonMetadataKeys = allKeys.filter(k => !k.startsWith('_'));
        const isShorthand = nonMetadataKeys.length === 1 && 
                           nonMetadataKeys[0].startsWith('z') && 
                           nonMetadataKeys[0].length > 1 && 
                           nonMetadataKeys[0][1] === nonMetadataKeys[0][1].toUpperCase();
        
        if (isShorthand) {
          const shorthandKey = nonMetadataKeys[0];
          // This is a shorthand UI element (zCheckbox, zText, zImage, etc.)
          this.logger.log(`[renderItems] 🎯 Found shorthand UI element: ${shorthandKey} for ${key}`);
          
          // Map shorthand keys to event types
          const shorthandToEvent = {
            'zCheckbox': 'read_bool',
            'zText': 'text',
            'zH1': 'header', 'zH2': 'header', 'zH3': 'header', 
            'zH4': 'header', 'zH5': 'header', 'zH6': 'header',
            'zMD': 'rich_text',
            'zImage': 'image',
            'zURL': 'zURL',
            'zUL': 'list',
            'zOL': 'list',
            'zTable': 'zTable',
            'zInput': 'read_string',
            'zBtn': 'button',
            'zCrumbs': 'zCrumbs'
          };
          
          const eventType = shorthandToEvent[shorthandKey];
          if (eventType) {
            // Expand shorthand to event data inline
            const eventData = { event: eventType, ...value[shorthandKey] };
            
            // For headers, add indent from key name
            if (eventType === 'header') {
              eventData.indent = parseInt(shorthandKey.substring(2)); // Extract number from zH1, zH2, etc.
            }
            
            this.logger.log(`[renderItems] 🔄 Expanding ${shorthandKey} to event ${eventType}:`, eventData);
            const element = await this.renderZDisplayEvent(eventData);
            if (element) {
              // Unwrap if no container classes
              if (!containerDiv.className || containerDiv.className === '') {
                element.setAttribute('data-zkey', key);
                if (!element.id) {
                  element.setAttribute('id', key);
                }
                parentElement.appendChild(element);
                continue;
              } else {
                containerDiv.appendChild(element);
              }
            }
          } else {
            // Unknown shorthand, recurse normally
            await this.renderItems(value, containerDiv);
          }
        } else {
          // If it's an object with nested keys (implicit wizard), recurse
          // DEBUG: Log organizational containers
          if (key.startsWith('_')) {
            this.logger.log(`🏗️  [NON-GROUP] Processing organizational container: ${key}, nested keys:`, Object.keys(value));
          } else {
            this.logger.log(`[ZDisplayOrchestrator] 🔄 Recursing into nested object for key: ${key}, nested keys:`, Object.keys(value));
          }
          // Nested structure - render children recursively
          await this.renderItems(value, containerDiv);
          if (key.startsWith('_') && containerDiv.children.length > 0) {
            this.logger.log(`✅ [NON-GROUP] Rendered organizational container ${key} with ${containerDiv.children.length} children`);
          }
        }
      }

      // Enhance zCard containers with proper zTheme structure
      if (containerDiv.children.length > 0) {
        if (containerDiv.classList.contains('zCard')) {
          const cardRenderer = await this.client._ensureCardRenderer();
          cardRenderer.enhanceCard(containerDiv);
        }

        // Append container to parent
        parentElement.appendChild(containerDiv);
      }
    }
  }

  /**
   * Create container wrapper for a zKey with zTheme responsive classes
   * Supports _zClass, _zStyle, and zId metadata for customization
   * @param {string} zKey - Key name for debugging
   * @param {Object} metadata - Metadata object with _zClass, _zStyle, zId
   * @returns {HTMLElement}
   */
  async createContainer(zKey, metadata) {
    // Check for _zHTML parameter to determine element type
    const elementType = metadata._zHTML || 'div';
    const validElements = ['div', 'section', 'article', 'aside', 'nav', 'header', 'footer', 'main', 'form', 'fieldset'];
    const tagName = validElements.includes(elementType) ? elementType : 'div';
    
    // Create the container with the specified element type
    const container = document.createElement(tagName);

    // Check for custom classes in metadata
    if (metadata._zClass !== undefined) {
      if (metadata._zClass === '' || metadata._zClass === null) {
        // Empty string or null = no container classes
        container.className = '';
      } else if (Array.isArray(metadata._zClass)) {
        // Array of classes
        container.className = metadata._zClass.join(' ');
      } else if (typeof metadata._zClass === 'string') {
        // String: comma-separated or space-separated classes
        const classes = metadata._zClass.includes(',')
          ? metadata._zClass.split(',').map(c => c.trim())
          : metadata._zClass.split(' ').filter(c => c.trim());
        container.className = classes.join(' ');
      }
    } else {
      // Default: NO classes (bare div, following HTML/CSS convention)
      // Organizational divs should be styled explicitly via _zClass when needed
      container.className = '';
    }

    // Apply inline styles if provided
    if (metadata._zStyle !== undefined && metadata._zStyle !== '' && metadata._zStyle !== null) {
      container.setAttribute('style', metadata._zStyle);
    }

    // Apply custom ID if provided (no underscore = passed to both Bifrost & Terminal)
    if (metadata.zId !== undefined && metadata.zId !== '' && metadata.zId !== null) {
      container.setAttribute('id', metadata.zId);
    }

    // Add data attribute for debugging/testing
    container.setAttribute('data-zkey', zKey);

    // Add form submit logging for debugging
    if (tagName === 'form') {
      container.addEventListener('submit', (event) => {
        console.log(`[ZDisplayOrchestrator] 📋 Form submitted: ${zKey}`);
        console.log('[ZDisplayOrchestrator] Form data:', new FormData(container));
        console.log('[ZDisplayOrchestrator] Form validity:', container.checkValidity());
        
        // Log individual field values
        const formData = new FormData(container);
        const formValues = {};
        for (const [key, value] of formData.entries()) {
          formValues[key] = value;
        }
        console.log('[ZDisplayOrchestrator] Field values:', formValues);
        
        this.logger.log(`[ZDisplayOrchestrator] Form "${zKey}" submitted with data:`, formValues);
        
        // For now, prevent actual submission (would normally POST to server)
        // In a real app, you'd either allow the POST or handle via WebSocket
        event.preventDefault();
        console.log('[ZDisplayOrchestrator] ⚠️  Form submission prevented (demo mode)');
        alert(`Form "${zKey}" submitted!\n\nCheck console for form data.`);
      });
      
      console.log(`[ZDisplayOrchestrator] ✅ Added submit listener to form: ${zKey}`);
      this.logger.log(`[ZDisplayOrchestrator] Added submit listener to form: ${zKey}`);
    }

    return container;
  }

  /**
   * Render navbar DOM element (v1.6.1: Returns DOM element to preserve event listeners)
   * @param {Array} items - Navbar items (e.g., ['zVaF', 'zAbout', '^zLogin'])
   * @returns {Promise<HTMLElement|null>} Navbar DOM element
   */
  async renderMetaNavBarHTML(items) {
    this.logger.log('[ZDisplayOrchestrator] 🎯 renderMetaNavBarHTML called with items:', items);

    if (!Array.isArray(items) || items.length === 0) {
      this.logger.warn('[ZDisplayOrchestrator] ⚠️ No navbar items provided');
      return null;
    }

    try {
      // Load navigation renderer
      const navRenderer = await this.client._ensureNavigationRenderer();

      // Render navbar element
      const navElement = navRenderer.renderNavBar(items, {
        className: 'zcli-navbar-meta',
        theme: 'light',
        href: (item) => {
          // Strip modifiers (^ for bounce-back, ~ for anchor) from URL
          const cleanItem = item.replace(/^[\^~]+/, '');
          return `/${cleanItem}`;
        },
        brand: this.options.title
      });

      // 🔧 FIX v1.6.1: Return DOM element directly (NOT outerHTML!)
      // This preserves event listeners attached by link_primitives.js
      // The caller (zvaf_manager.js) will append the element instead of setting innerHTML
      this.logger.log('[ZDisplayOrchestrator] ✅ Returning navbar DOM element (preserves event listeners)');
      return navElement;
    } catch (error) {
      this.logger.error('[ZDisplayOrchestrator] Failed to render navbar element:', error);
      return null;
    }
  }

  /**
   * Render navigation bar from metadata (~zNavBar* in content)
   * @param {Array} items - Navbar items
   * @param {HTMLElement} parentElement - Parent element to append to
   */
  async renderNavBar(items, parentElement) {
    if (!Array.isArray(items) || items.length === 0) {
      this.logger.warn('[ZDisplayOrchestrator] ~zNavBar* has no items or is not an array');
      return;
    }

    try {
      // Load navigation renderer
      const navRenderer = await this.client._ensureNavigationRenderer();

      // Render navbar with zTheme zNavbar component
      const navElement = navRenderer.renderNavBar(items, {
        theme: 'light'
      });

      if (navElement) {
        parentElement.appendChild(navElement);

        // Re-initialize zTheme collapse now that navbar is in DOM
        if (window.zTheme && typeof window.zTheme.initCollapse === 'function') {
          window.zTheme.initCollapse();
          this.logger.log('[ZDisplayOrchestrator] Re-initialized zTheme collapse for navbar');
        }

        this.logger.log('[ZDisplayOrchestrator] Rendered navigation bar with items:', items);
      }
    } catch (error) {
      this.logger.error('[ZDisplayOrchestrator] Failed to render navigation bar:', error);
    }
  }

  /**
   * Render a single zDisplay event as DOM element
   * @param {Object} eventData - Event data with event type and content
   * @returns {Promise<HTMLElement>}
   */
  async renderZDisplayEvent(eventData) {
    const event = eventData.event;
    this.logger.log(`[renderZDisplayEvent] 🎯 Rendering event: ${event}`, eventData);
    let element;

    switch (event) {
      case 'text': {
        // Use modular TypographyRenderer for text
        const textRenderer = await this.client._ensureTypographyRenderer();
        element = textRenderer.renderText(eventData);
        this.logger.log('[renderZDisplayEvent] Rendered text element');
        break;
      }

      case 'rich_text': {
        // Use TextRenderer for rich text with markdown parsing
        const textRenderer = await this.client._ensureTextRenderer();
        element = textRenderer.renderRichText(eventData);
        this.logger.log('[renderZDisplayEvent] Rendered rich_text element with markdown');
        break;
      }

      case 'header': {
        // Use modular TypographyRenderer for headers
        const headerRenderer = await this.client._ensureTypographyRenderer();
        element = headerRenderer.renderHeader(eventData);
        this.logger.log(`[renderZDisplayEvent] Rendered header element with level: ${eventData.level || 1}`);
        break;
      }

      case 'divider': {
        // Use modular TypographyRenderer for dividers
        const dividerRenderer = await this.client._ensureTypographyRenderer();
        element = dividerRenderer.renderDivider(eventData);
        break;
      }

      case 'button': {
        // Use modular ButtonRenderer for buttons
        const buttonRenderer = await this.client._ensureButtonRenderer();
        element = buttonRenderer.render(eventData);
        this.logger.log(`[renderZDisplayEvent] Rendered button element: ${eventData.label}`);
        break;
      }

      case 'zURL': {
        // Use modular LinkRenderer for semantic links
        // Renamed from 'link' to distinguish from zLink (inter-file navigation)
        const { renderLink } = await import('./primitives/link_primitives.js');
        // ✅ SEPARATION OF CONCERNS: Primitive renders element, orchestrator handles grouping
        element = renderLink(eventData, null, this.client);
        this.logger.log(`[renderZDisplayEvent] Rendered zURL element: ${eventData.label}`);
        break;
      }

      case 'zTable': {
        // Use modular TableRenderer for tables
        const tableRenderer = await this.client._ensureTableRenderer();
        element = tableRenderer.render(eventData);
        this.logger.log(`[renderZDisplayEvent] Rendered table element: ${eventData.title || 'untitled'}`);
        break;
      }

      case 'list': {
        // Use modular ListRenderer for lists
        const listRenderer = await this.client._ensureListRenderer();
        element = listRenderer.render(eventData);
        this.logger.log(`[renderZDisplayEvent] Rendered list element with ${eventData.items?.length || 0} items`);
        break;
      }

      case 'dl': {
        // Use ZDisplayRenderer for description lists
        const zdisplayRenderer = await this.client._ensureZDisplayRenderer();
        element = zdisplayRenderer._renderDL(eventData);
        this.logger.log(`[renderZDisplayEvent] Rendered description list with ${eventData.items?.length || 0} items`);
        break;
      }

      case 'image': {
        // Use modular ImageRenderer for images
        const imageRenderer = await this.client._ensureImageRenderer();
        element = imageRenderer.render(eventData);
        this.logger.log(`[renderZDisplayEvent] Rendered image element: ${eventData.src}`);
        break;
      }

      case 'card': {
        // Use modular CardRenderer for cards
        const cardRenderer = await this.client._ensureCardRenderer();
        element = cardRenderer.renderCard(eventData);
        this.logger.log('[renderZDisplayEvent] Rendered card element');
        break;
      }

      case 'zCrumbs': {
        // Breadcrumb navigation (multi-trail support)
        this.logger.log('[renderZDisplayEvent] 🍞 zCrumbs case hit! eventData:', eventData);
        const navRenderer = await this.client._ensureNavigationRenderer();
        this.logger.log('[renderZDisplayEvent] 🍞 NavRenderer ready, calling renderBreadcrumbs...');
        element = navRenderer.renderBreadcrumbs(eventData);
        this.logger.log('[renderZDisplayEvent] 🍞 Rendered breadcrumbs element:', element);
        break;
      }

      case 'zDash': {
        // Dashboard with sidebar navigation
        const DashboardRenderer = (await import('./dashboard_renderer.js')).default;
        const dashRenderer = new DashboardRenderer(this.logger, this.client);
        element = await dashRenderer.render(eventData, this.targetElement || null);
        this.logger.log('[renderZDisplayEvent] Rendered dashboard element');
        break;
      }

      case 'read_string':
      case 'read_password': {
        // Input fields - render as bare semantic HTML (reboot style)
        const { createLabel, createInput, createTextarea } = await import('./primitives/form_primitives.js');
        
        const inputType = event === 'read_password' ? 'password' : (eventData.type || 'text');
        const prompt = eventData.prompt || '';
        const placeholder = eventData.placeholder || '';
        const required = eventData.required || false;
        const defaultValue = eventData.default || '';
        const disabled = eventData.disabled || false;
        const readonly = eventData.readonly || false;
        const multiple = eventData.multiple || false;
        const title = eventData.title || '';
        const datalist = eventData.datalist || null;
        
        // Build input classes from _zClass (defaults to zForm-control if not specified)
        const inputClasses = eventData._zClass || 'zForm-control';
        
        // Support zId (universal), _zId (Bifrost-only), and _id (legacy)
        const inputId = eventData.zId || eventData._zId || eventData._id || `input_${Math.random().toString(36).substr(2, 9)}`;
        
        // Generate datalist ID if datalist exists
        const datalistId = datalist ? `${inputId}_datalist` : null;
        
        // Support aria-describedby for accessibility (link to help text)
        const ariaDescribedBy = eventData.aria_described_by || eventData.ariaDescribedBy || eventData['aria-describedby'];
        
        // Create wrapper div only if prompt exists (for label + input grouping)
        // Otherwise return input directly to avoid double-nesting in grid layouts
        let wrapper = null;
        
        // Create label if prompt exists (connected to input via for/id)
        if (prompt) {
          wrapper = document.createElement('div');
          // Use zLabel class for styled inputs, no class for basic semantic HTML
          const labelClass = inputClasses.includes('zInput') ? 'zLabel' : '';
          const labelAttrs = labelClass ? { class: labelClass } : {};
          const label = createLabel(inputId, labelAttrs);
          label.textContent = prompt;
          wrapper.appendChild(label);
          // Add line break after label (semantic HTML pattern)
          wrapper.appendChild(document.createElement('br'));
        }
        
        // Handle textarea vs input
        let inputElement;
        if (inputType === 'textarea') {
          // Multi-line textarea
          const rows = eventData.rows || 3;
          const textareaAttrs = {
            id: inputId,
            placeholder: placeholder,
            required: required,
            rows: rows,
            class: inputClasses
          };
          
          if (ariaDescribedBy) {
            textareaAttrs['aria-describedby'] = ariaDescribedBy;
          }
          
          if (disabled) {
            textareaAttrs.disabled = true;
          }
          
          if (readonly) {
            textareaAttrs.readonly = true;
          }
          
          if (title) {
            textareaAttrs.title = title;
          }
          
          inputElement = createTextarea(textareaAttrs);
          inputElement.textContent = defaultValue; // Use textContent for textarea, not value
        } else {
          // Single-line input
          const inputAttrs = {
            id: inputId,
            placeholder: placeholder,
            required: required,
            value: defaultValue,
            class: inputClasses
          };
          
          // Add list attribute if datalist exists
          if (datalistId) {
            inputAttrs.list = datalistId;
          }
          
          if (ariaDescribedBy) {
            inputAttrs['aria-describedby'] = ariaDescribedBy;
          }
          
          if (disabled) {
            inputAttrs.disabled = true;
          }
          
          if (readonly) {
            inputAttrs.readonly = true;
          }
          
          if (multiple) {
            inputAttrs.multiple = true;
          }
          
          if (title) {
            inputAttrs.title = title;
          }
          
          inputElement = createInput(inputType, inputAttrs);
        }
        
        // If wrapper exists (has prompt), append input to wrapper and return wrapper
        // Otherwise return input/textarea directly to avoid double-nesting in grid layouts
        if (wrapper) {
          wrapper.appendChild(inputElement);
          
          // Add datalist element if datalist exists
          if (datalist && Array.isArray(datalist)) {
            const datalistElement = document.createElement('datalist');
            datalistElement.id = datalistId;
            
            datalist.forEach(optionValue => {
              const option = document.createElement('option');
              option.value = optionValue;
              datalistElement.appendChild(option);
            });
            
            wrapper.appendChild(datalistElement);
          }
          
          element = wrapper;
        } else {
          // When returning input/textarea directly, apply _zStyle if present
          // This allows inline styles for grid layout adjustments (e.g., padding-top)
          if (eventData._zStyle) {
            inputElement.setAttribute('style', eventData._zStyle);
          }
          
          // If datalist exists but no wrapper, create minimal wrapper for datalist
          if (datalist && Array.isArray(datalist)) {
            const container = document.createElement('div');
            container.appendChild(inputElement);
            
            const datalistElement = document.createElement('datalist');
            datalistElement.id = datalistId;
            
            datalist.forEach(optionValue => {
              const option = document.createElement('option');
              option.value = optionValue;
              datalistElement.appendChild(option);
            });
            
            container.appendChild(datalistElement);
            element = container;
          } else {
            element = inputElement;
          }
        }
        
        this.logger.log(`[renderZDisplayEvent] Rendered ${event} ${inputType} (id=${inputId}, aria-describedby=${ariaDescribedBy || 'none'})`);
        break;
      }

      case 'read_bool': {
        // Checkbox input (inline form checkbox)
        const { createDiv } = await import('./primitives/generic_containers.js');
        const { createLabel, createInput } = await import('./primitives/form_primitives.js');
        
        const prompt = eventData.prompt || eventData.label || '';
        const checked = eventData.checked || false;
        const required = eventData.required || false;
        
        // Build checkbox classes from _zClass (defaults to zForm-check-input)
        const checkboxClasses = eventData._zClass || 'zForm-check-input';
        
        // Support zId (universal), _zId (Bifrost-only), and _id (legacy)
        const checkboxId = eventData.zId || eventData._zId || eventData._id || `checkbox_${Math.random().toString(36).substr(2, 9)}`;
        
        // Create form check container (Bootstrap-style checkbox)
        const formCheck = createDiv({ class: 'zForm-check zmb-3' });
        
        // Create checkbox input (type='checkbox')
        const checkbox = createInput('checkbox', {
          checked: checked,
          required: required,
          class: checkboxClasses,
          id: checkboxId
        });
        
        // Create label for checkbox (wraps around or uses 'for' attribute)
        if (prompt) {
          const label = createLabel(checkboxId, { class: 'zForm-check-label' });
          label.textContent = prompt;
          
          // Add checkbox first, then label (Bootstrap convention)
          formCheck.appendChild(checkbox);
          formCheck.appendChild(label);
        } else {
          // No label, just the checkbox
          formCheck.appendChild(checkbox);
        }
        
        element = formCheck;
        
        this.logger.log(`[renderZDisplayEvent] Rendered ${event} checkbox: ${prompt} (id=${checkboxId}, checked=${checked})`);
        break;
      }

      case 'selection': {
        // Selection control - render based on type (dropdown, radio, checkbox)
        const { createLabel, createInput } = await import('./primitives/form_primitives.js');
        
        const prompt = eventData.prompt || '';
        const options = eventData.options || [];
        const multi = eventData.multi || false;
        const defaultValue = eventData.default || null;
        const disabled = eventData.disabled || false;
        const required = eventData.required || false;
        const type = eventData.type || 'dropdown'; // Default to dropdown
        
        // Build classes from _zClass
        const elementClasses = eventData._zClass || '';
        
        // Support zId (universal), _zId (Bifrost-only), and _id (legacy)
        const baseId = eventData.zId || eventData._zId || eventData._id || `select_${Math.random().toString(36).substr(2, 9)}`;
        
        // Support aria-label for accessibility
        const ariaLabel = eventData['_aria-label'] || eventData.ariaLabel || eventData['aria-label'];
        
        // Render based on type
        if (type === 'radio' || (type === 'checkbox' && multi)) {
          // Radio button group or checkbox group
          const inputType = type === 'radio' ? 'radio' : 'checkbox';
          const groupName = baseId; // Use baseId as group name for radio buttons
          
          // Create container
          const container = document.createElement('div');
          if (elementClasses) {
            container.className = elementClasses;
          }
          if (eventData._zStyle) {
            container.setAttribute('style', eventData._zStyle);
          }
          
          // Create prompt label if exists (fieldset legend style)
          if (prompt) {
            const promptLabel = document.createElement('div');
            promptLabel.textContent = prompt;
            promptLabel.style.marginBottom = '0.5rem';
            promptLabel.style.fontWeight = '500';
            container.appendChild(promptLabel);
          }
          
          // Create radio/checkbox inputs for each option
          options.forEach((optionValue, index) => {
            const optionId = `${baseId}_${index}`;
            const optionLabel = typeof optionValue === 'string' ? optionValue : (optionValue.label || optionValue.value || '');
            const optionVal = typeof optionValue === 'string' ? optionValue : (optionValue.value || optionValue.label || '');
            
            // Create wrapper div for input + label
            const optionWrapper = document.createElement('div');
            optionWrapper.style.marginBottom = '0.5rem';
            
            // Create input
            const input = createInput(inputType, {
              id: optionId,
              name: groupName,
              value: optionVal,
              disabled: disabled,
              required: required && index === 0 // Only first input has required
            });
            
            // Set checked state based on default value
            if (defaultValue !== null) {
              if (multi && Array.isArray(defaultValue)) {
                // Multi-select (checkbox): check if option is in default array
                if (defaultValue.includes(optionVal) || defaultValue.includes(optionLabel)) {
                  input.checked = true;
                }
              } else {
                // Single-select (radio): check if option matches default
                if (optionVal === defaultValue || optionLabel === defaultValue) {
                  input.checked = true;
                }
              }
            }
            
            // Create label
            const label = createLabel(optionId, {});
            label.textContent = optionLabel;
            label.style.marginLeft = '0.5rem';
            
            // Assemble option
            optionWrapper.appendChild(input);
            optionWrapper.appendChild(label);
            container.appendChild(optionWrapper);
          });
          
          element = container;
          this.logger.log(`[renderZDisplayEvent] Rendered ${event} ${inputType} group (id=${baseId}, options=${options.length})`);
        } else {
          // Dropdown select (default behavior)
          let wrapper = null;
          
          // Create label if prompt exists
          if (prompt) {
            wrapper = document.createElement('div');
            // Use zLabel class for styled selects
            const labelClass = elementClasses.includes('zSelect') ? 'zLabel' : '';
            const labelAttrs = labelClass ? { class: labelClass } : {};
            const label = createLabel(baseId, labelAttrs);
            label.textContent = prompt;
            wrapper.appendChild(label);
            // Add line break after label (semantic HTML pattern)
            wrapper.appendChild(document.createElement('br'));
          }
          
          // Create select element
          const selectElement = document.createElement('select');
          selectElement.id = baseId;
          
          if (elementClasses) {
            selectElement.className = elementClasses;
          }
          
          if (disabled) {
            selectElement.disabled = true;
          }
          
          if (required) {
            selectElement.required = true;
          }
          
          if (multi) {
            selectElement.multiple = true;
          }
          
          // Support size attribute (number of visible options)
          const size = eventData.size || null;
          if (size !== null) {
            selectElement.size = size;
          }
          
          if (ariaLabel) {
            selectElement.setAttribute('aria-label', ariaLabel);
          }
          
          // Add autocomplete="off" to prevent browser from remembering selections
          selectElement.setAttribute('autocomplete', 'off');
          
          // Apply inline styles if no wrapper (to avoid nesting issues)
          if (!wrapper && eventData._zStyle) {
            selectElement.setAttribute('style', eventData._zStyle);
          }
          
          // Create option elements
          options.forEach((optionValue, index) => {
            const optionElement = document.createElement('option');
            
            // Handle both string options and object options {label: '', value: ''}
            if (typeof optionValue === 'string') {
              optionElement.textContent = optionValue;
              optionElement.value = optionValue;
            } else {
              optionElement.textContent = optionValue.label || optionValue.value || '';
              optionElement.value = optionValue.value || optionValue.label || '';
            }
            
            // Set selected state based on default value
            if (defaultValue !== null) {
              if (multi && Array.isArray(defaultValue)) {
                // Multi-select: check if option is in default array
                if (defaultValue.includes(optionElement.value)) {
                  optionElement.selected = true;
                }
              } else {
                // Single-select: check if option matches default
                if (optionElement.value === defaultValue || optionElement.textContent === defaultValue) {
                  optionElement.selected = true;
                }
              }
            }
            
            selectElement.appendChild(optionElement);
          });
          
          // Assemble final element
          if (wrapper) {
            wrapper.appendChild(selectElement);
            // Apply wrapper styles if specified
            if (eventData._zStyle) {
              wrapper.setAttribute('style', eventData._zStyle);
            }
            element = wrapper;
          } else {
            element = selectElement;
          }
          
          this.logger.log(`[renderZDisplayEvent] Rendered ${event} select (id=${baseId}, options=${options.length}, multi=${multi})`);
        }
        
        break;
      }

      default: {
        this.logger.warn(`Unknown zDisplay event: ${event}`);
        const { createDiv } = await import('./primitives/generic_containers.js');
        element = createDiv({
          class: 'zDisplay-unknown'
        });
        element.textContent = `[${event}] ${eventData.content || ''}`;
      }
    }

    return element;
  }

  /**
   * Apply group-specific styling to an element (Terminal-first pattern)
   * This is where zTheme group classes are applied based on _zGroup context
   * Color is auto-inferred from the YAML color parameter (DRY)
   *
   * @param {HTMLElement} element - The rendered element
   * @param {string} groupType - The type of group (e.g., 'list-group', 'button-group')
   * @param {Object} eventData - The original event data (for color handling)
   * @private
   */
  _applyGroupStyling(element, groupType, eventData) {
    if (!element || !groupType) {
      return;
    }

    this.logger.log(`[_applyGroupStyling] Applying group styling: ${groupType}, color: ${eventData.color || 'none'}`);

    // Apply group-specific zTheme classes based on group type and event type
    switch (groupType) {
      case 'list-group':
        // For links, buttons, or any interactive element in a list-group
        if (eventData.event === 'zURL' || eventData.event === 'button') {
          element.classList.add('zList-group-item', 'zList-group-item-action');

          // 🎨 Terminal-first: Auto-infer color variant from YAML color parameter
          if (eventData.color) {
            const colorClass = `zList-group-item-${eventData.color.toLowerCase()}`;
            element.classList.add(colorClass);
            this.logger.log(`[_applyGroupStyling] Applied list-group color: ${colorClass}`);
          }
        }
        break;

      case 'button-group':
        // For future: Button groups (horizontal button toolbar)
        // element.classList.add('zBtn-group-item');
        break;

      case 'card-group':
        // For future: Card groups (masonry/grid layout)
        // element.classList.add('zCard-group-item');
        break;

      default:
        this.logger.warn(`[_applyGroupStyling] Unknown group type: ${groupType}`);
    }
  }
}

export default ZDisplayOrchestrator;

