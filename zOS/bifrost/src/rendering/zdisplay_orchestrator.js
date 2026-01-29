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
    
    // NOTE: zCard-body auto-enhancement REMOVED (2026-01-28)
    // Users should explicitly declare _zClass: zCard-body when needed.
    // The renderer should not be "smarter" than the declarative .zolo file.
  }

  /**
   * Progressive chunk rendering (Terminal First philosophy)
   * Appends chunks from backend as they arrive, stops at failed gates
   * @param {Object} message - Chunk message from backend
   */
  async renderChunkProgressive(message) {
    try {
      console.log('[ZDisplayOrchestrator] 🎬 renderChunkProgressive called with:', message);
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
        
        // Initialize conditional rendering for any wizards with if conditions
        console.log(`[ZDisplayOrchestrator] 🔍 Checking for wizard containers in targetContainer:`, targetContainer);
        console.log(`[ZDisplayOrchestrator] 🔍 targetContainer HTML (first 500 chars):`, targetContainer.innerHTML.substring(0, 500));
        this.logger.log(`[ZDisplayOrchestrator] 🔍 Checking for wizard containers in targetContainer:`, targetContainer);
        this.logger.log(`[ZDisplayOrchestrator] 🔍 targetContainer HTML (first 500 chars):`, targetContainer.innerHTML.substring(0, 500));
        try {
          await this.client._ensureWizardConditionalRenderer();
          this.logger.log(`[ZDisplayOrchestrator] ✅ WizardConditionalRenderer ensured`);
        } catch (err) {
          this.logger.error(`[ZDisplayOrchestrator] ❌ Failed to ensure WizardConditionalRenderer:`, err);
        }
        
        // Find wizard containers: elements with data-zkey containing "Wizard" or elements with data-zgroup="input-group" that contain conditional elements
        const wizardContainers = targetContainer.querySelectorAll('[data-zkey*="Wizard"], [data-zgroup="input-group"]');
        console.log(`[ZDisplayOrchestrator] 🔍 Found ${wizardContainers.length} wizard container(s) with selector '[data-zkey*="Wizard"], [data-zgroup="input-group"]'`);
        console.log(`[ZDisplayOrchestrator] 🔍 Wizard containers:`, Array.from(wizardContainers).map(c => ({id: c.id, zkey: c.getAttribute('data-zkey'), zgroup: c.getAttribute('data-zgroup')})));
        this.logger.log(`[ZDisplayOrchestrator] 🔍 Found ${wizardContainers.length} wizard container(s) with selector '[data-zkey*="Wizard"], [data-zgroup="input-group"]'`);
        
        if (wizardContainers.length > 0) {
          this.logger.log(`[ZDisplayOrchestrator] 🧙 Initializing ${wizardContainers.length} wizard container(s) for conditional rendering`);
          wizardContainers.forEach((container, idx) => {
            const containerId = container.id || container.getAttribute('data-zkey') || container.getAttribute('data-zgroup') || `container-${idx}`;
            this.logger.log(`[ZDisplayOrchestrator] 🧙 [${idx + 1}/${wizardContainers.length}] Initializing wizard: ${containerId}`);
            this.logger.log(`[ZDisplayOrchestrator] 🧙 Container element:`, container);
            try {
              this.client.wizardConditionalRenderer.initializeWizard(container);
            } catch (err) {
              this.logger.error(`[ZDisplayOrchestrator] ❌ Failed to initialize wizard container ${containerId}:`, err);
            }
          });
        } else {
          // Also check for any elements with data-zif (conditional elements) - their parent might be the wizard
          const conditionalElements = targetContainer.querySelectorAll('[data-zif]');
          console.log(`[ZDisplayOrchestrator] 🔍 No wizard containers found, checking for conditional elements: found ${conditionalElements.length}`);
          console.log(`[ZDisplayOrchestrator] 🔍 Conditional elements:`, Array.from(conditionalElements).map(el => ({id: el.id, zkey: el.getAttribute('data-zkey'), zif: el.getAttribute('data-zif')})));
          this.logger.log(`[ZDisplayOrchestrator] 🔍 No wizard containers found, checking for conditional elements: found ${conditionalElements.length}`);
          
          if (conditionalElements.length > 0) {
            this.logger.log(`[ZDisplayOrchestrator] 🧙 Found ${conditionalElements.length} conditional element(s), initializing parent containers`);
            const parentContainers = new Set();
            conditionalElements.forEach((el, idx) => {
              this.logger.log(`[ZDisplayOrchestrator] 🔍 Conditional element ${idx + 1}:`, el, `data-zif="${el.getAttribute('data-zif')}"`);
              // Find the closest container with data-zgroup or data-zkey containing "Wizard"
              const parent = el.closest('[data-zgroup], [data-zkey*="Wizard"]');
              if (parent && !parentContainers.has(parent)) {
                parentContainers.add(parent);
                const parentId = parent.id || parent.getAttribute('data-zkey') || parent.getAttribute('data-zgroup') || `parent-${idx}`;
                this.logger.log(`[ZDisplayOrchestrator] 🧙 Initializing parent wizard container: ${parentId}`, parent);
                try {
                  this.client.wizardConditionalRenderer.initializeWizard(parent);
                } catch (err) {
                  this.logger.error(`[ZDisplayOrchestrator] ❌ Failed to initialize parent wizard container ${parentId}:`, err);
                }
              } else {
                this.logger.log(`[ZDisplayOrchestrator] ⚠️  No suitable parent found for conditional element ${idx + 1}`);
              }
            });
          } else {
            this.logger.log(`[ZDisplayOrchestrator] ⚠️  No wizard containers and no conditional elements found`);
          }
        }
        
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
    // Also support _zClass containing zInputGroup as input-group context
    // (for zWizard with _zClass: zInputGroup instead of _zGroup: input-group)
    // ═══════════════════════════════════════════════════════════════════════
    const isInputGroupContext = metadata._zGroup === 'input-group' || 
                                (metadata._zClass && metadata._zClass.includes('zInputGroup'));
    
    if (metadata._zGroup || isInputGroupContext) {
      // If _zClass contains zInputGroup but no _zGroup, treat as input-group
      if (isInputGroupContext && !metadata._zGroup) {
        metadata._zGroup = 'input-group';
      }
      this.logger.log(`[ZDisplayOrchestrator] 🎯 _zGroup detected: "${metadata._zGroup}" - rendering as grouped container`);
      this.logger.log(`🎯 _zGroup detected: "${metadata._zGroup}"`);

      // Create group container with zTheme classes based on _zGroup type
      const groupContainer = document.createElement('div');
      groupContainer.setAttribute('data-zgroup', metadata._zGroup);

      // Apply zTheme container class based on group type
      if (metadata._zGroup === 'list-group') {
        groupContainer.classList.add('zList-group');
        this.logger.log('  Applied zTheme class: zList-group');
      } else if (metadata._zGroup === 'input-group') {
        groupContainer.classList.add('zInputGroup');
        this.logger.log('  Applied zTheme class: zInputGroup');
      }

      // Apply additional _zClass styling if provided (from YAML)
      if (metadata._zClass) {
        const classes = metadata._zClass.split(' ').filter(c => c.trim());
        if (classes.length > 0) {
          groupContainer.classList.add(...classes);
          this.logger.log(`  Applied additional _zClass: ${metadata._zClass}`);
        }
      }

      // Add prefix label for input-group if _zGroupLabel is provided
      if (metadata._zGroup === 'input-group' && metadata._zGroupLabel) {
        const labelSpan = document.createElement('span');
        labelSpan.classList.add('zInputGroup-text');
        labelSpan.textContent = metadata._zGroupLabel;
        groupContainer.appendChild(labelSpan);
        this.logger.log(`  Added input group label: ${metadata._zGroupLabel}`);
      }

      // DEBUG: Log what we're about to iterate
      if (metadata._zGroup === 'input-group') {
        this.logger.log('🔍 [INPUT-GROUP DEBUG] Data keys:', Object.keys(data));
        this.logger.log('🔍 [INPUT-GROUP DEBUG] Full data:', JSON.stringify(data, null, 2));
      }

      // Track matched conditional inputs (for radio zSelect splitting)
      const matchedInputKeys = new Set();

      // Iterate through all non-metadata children and render into group
      for (const [key, value] of Object.entries(data)) {
        // Skip ONLY metadata keys (not organizational containers like _Visual_Progression)
        const METADATA_KEYS = ['_zClass', '_zStyle', '_zHTML', '_zId', '_zScripts', '_zGroup', '_zGroupLabel', 'zId'];
        if (METADATA_KEYS.includes(key) || key.startsWith('~')) {
          continue;
        }

        // Skip if this input was already matched and rendered by radio zSelect splitting
        if (matchedInputKeys.has(key)) {
          this.logger.log(`  ⏭️  Skipping already-matched conditional input: ${key}`);
          continue;
        }
        
        this.logger.log(`  Rendering grouped item: ${key}`);
        
        // DEBUG for input-group
        if (metadata._zGroup === 'input-group') {
          this.logger.log(`🔍 [INPUT-GROUP] Processing child: ${key}`);
          this.logger.log(`🔍 [INPUT-GROUP] Value type: ${Array.isArray(value) ? 'Array' : typeof value}`);
          if (value && typeof value === 'object' && !Array.isArray(value)) {
            this.logger.log(`🔍 [INPUT-GROUP] Value keys: ${Object.keys(value).join(', ')}`);
            if (value.event) {
              this.logger.log(`🔍 [INPUT-GROUP] Event: ${value.event}, type: ${value.type}`);
            }
            if (value.zSelect) {
              this.logger.log(`🔍 [INPUT-GROUP] zSelect found, type: ${value.zSelect.type}`);
            }
          }
        }

        // Handle list/array values (zDisplay events)
        if (Array.isArray(value)) {
          for (const item of value) {
            if (item && item.zDisplay) {
              // ✅ SEPARATION OF CONCERNS: Render element without group context
              const element = await this.renderZDisplayEvent(item.zDisplay, groupContainer);
              if (element) {
                // Apply group-specific styling AFTER rendering
                this._applyGroupStyling(element, metadata._zGroup, item.zDisplay);
                groupContainer.appendChild(element);
              }
            }
          }
        } else if (value && value.zDisplay && value.zDisplay.event === 'selection' && value.zDisplay.type === 'radio' && metadata._zGroup === 'input-group') {
          // Backend sent expanded zSelect as value.zDisplay: run same radio+input split logic
          const sel = value.zDisplay;
          const options = sel.options || [];
          const zCross = sel.zCross !== undefined ? sel.zCross : false;
          const groupName = sel.zId || sel._zId || sel._id || `radio_${Math.random().toString(36).substr(2, 9)}`;
          const conditionalInputs = [];
          for (const [childKey, childValue] of Object.entries(data)) {
            if (childValue && childValue.zInput && childValue.zInput.if) {
              conditionalInputs.push({ key: childKey, value: childValue, condition: (childValue.zInput.if || '').replace(/#.*$/gm, '').trim(), payload: childValue.zInput });
            } else if (childValue && childValue.zDisplay && childValue.zDisplay.event === 'read_string' && childValue.zDisplay.if) {
              conditionalInputs.push({ key: childKey, value: childValue, condition: (childValue.zDisplay.if || '').replace(/#.*$/gm, '').trim(), payload: childValue.zDisplay });
            }
          }
          const parseSuffixN = (s) => {
            if (s == null) return null;
            if (typeof s === 'number' && s > 0) return s;
            const m = String(s).trim().match(/^\+(\d+)$/);
            return m ? parseInt(m[1], 10) : null;
          };
          const suffixN = parseSuffixN(sel.suffix);
          for (let i = 0; i < options.length; i++) {
            const optionValue = typeof options[i] === 'string' ? options[i] : (options[i].value || options[i].label || '');
            const optionLabel = typeof options[i] === 'string' ? options[i] : (options[i].label || options[i].value || '');
            let matchingInput;
            if (suffixN != null && i < suffixN && i < conditionalInputs.length) {
              matchingInput = conditionalInputs[i];
            } else {
              matchingInput = conditionalInputs.find(input => {
                const condition = (input.condition || '').trim();
                const valueMatch = condition.match(/==\s*['"]?([^'"\s]+)['"]?\s*(?:#|$)/);
                if (valueMatch && valueMatch[1].trim() === optionValue) return true;
                return [`== '${optionValue}'`, `== "${optionValue}"`, `=='${optionValue}'`, `=="${optionValue}"`, `== ${optionValue}`, `==${optionValue}`].some(p => condition.includes(p));
              });
            }
            const inputGroupDiv = document.createElement('div');
            inputGroupDiv.classList.add('zInputGroup');
            if (sel._zClass) {
              const classes = sel._zClass.split(' ').filter(c => c.trim() && c !== 'zCheck-input');
              if (classes.length) inputGroupDiv.classList.add(...classes);
            }
            const textWrapper = document.createElement('div');
            textWrapper.classList.add('zInputGroup-text');
            const { createInput } = await import('./primitives/form_primitives.js');
            const radioInput = createInput('radio', { id: `${groupName}_${i}`, name: groupName, value: optionValue, class: 'zCheck-input', 'aria-label': optionLabel });
            if (sel.default === optionValue) radioInput.checked = true;
            radioInput.setAttribute('data-zcross', zCross.toString());
            textWrapper.appendChild(radioInput);
            inputGroupDiv.appendChild(textWrapper);
            if (matchingInput) {
              matchedInputKeys.add(matchingInput.key);
              const payload = matchingInput.payload || matchingInput.value.zInput || matchingInput.value.zDisplay || {};
              const inputEventData = { event: 'read_string', ...payload };
              if (matchingInput.value.zCross !== undefined) inputEventData.zCross = matchingInput.value.zCross;
              delete inputEventData.prompt;
              const inputElement = await this.renderZDisplayEvent(inputEventData, inputGroupDiv);
              if (inputElement) {
                if (inputElement.tagName === 'INPUT' || inputElement.tagName === 'TEXTAREA') {
                  inputGroupDiv.appendChild(inputElement);
                } else {
                  const actualInput = inputElement.querySelector('input, textarea');
                  inputGroupDiv.appendChild(actualInput || inputElement);
                }
              }
            }
            groupContainer.appendChild(inputGroupDiv);
          }
          continue;
        } else if (value && value.zDisplay) {
          // Handle direct zDisplay event
          // ✅ SEPARATION OF CONCERNS: Render element without group context
          const element = await this.renderZDisplayEvent(value.zDisplay, groupContainer);
          if (element) {
            // Apply group-specific styling AFTER rendering
            this._applyGroupStyling(element, metadata._zGroup, value.zDisplay);
            groupContainer.appendChild(element);
          }
        } else if (value && typeof value === 'object') {
          // Check if this is already a zDisplay event object
          if (value.event) {
            // This is a zDisplay event that was already expanded by the backend
            this.logger.log(`  Found pre-expanded zDisplay event '${value.event}' in grouped item: ${key}`);
            
            // Special handling for radio selection events in input-group: split into separate zInputGroup containers
            this.logger.log(`  🔍 Checking for radio selection: key=${key}, event=${value.event}, type=${value.type}, _zGroup=${metadata._zGroup}`);
            if (value.event === 'selection' && metadata._zGroup === 'input-group' && value.type === 'radio') {
              this.logger.log(`  ✅ Radio selection detected! Processing ${value.options?.length || 0} options`);
              // Radio buttons in input-group: create separate zInputGroup for each option
              const options = value.options || [];
              const zCross = value.zCross !== undefined ? value.zCross : false;
              const groupName = value.zId || value._zId || value._id || `radio_${Math.random().toString(36).substr(2, 9)}`;
              
              // Find all conditional zInput elements (shorthand or expanded zDisplay) in declaration order
              const conditionalInputs = [];
              for (const [childKey, childValue] of Object.entries(data)) {
                if (childValue && childValue.zInput && childValue.zInput.if) {
                  conditionalInputs.push({ key: childKey, value: childValue, condition: (childValue.zInput.if || '').replace(/#.*$/gm, '').trim(), payload: childValue.zInput });
                  this.logger.log(`  📝 Found conditional input: ${childKey} with condition: "${childValue.zInput.if}"`);
                } else if (childValue && childValue.zDisplay && childValue.zDisplay.event === 'read_string' && childValue.zDisplay.if) {
                  conditionalInputs.push({ key: childKey, value: childValue, condition: (childValue.zDisplay.if || '').replace(/#.*$/gm, '').trim(), payload: childValue.zDisplay });
                  this.logger.log(`  📝 Found conditional input (zDisplay): ${childKey} with condition: "${childValue.zDisplay.if}"`);
                }
              }
              this.logger.log(`  📊 Found ${conditionalInputs.length} conditional input(s) total`);
              // Parse suffix +N (e.g. "+3" => pair with next N inputs by position)
              const parseSuffixN = (s) => {
                if (s == null) return null;
                if (typeof s === 'number' && s > 0) return s;
                const m = String(s).trim().match(/^\+(\d+)$/);
                return m ? parseInt(m[1], 10) : null;
              };
              const suffixN = parseSuffixN(value.suffix);
              if (suffixN != null) this.logger.log(`  📌 suffix: ${value.suffix} → suffixN=${suffixN} (position-based pairing)`);
              
              // Create a separate zInputGroup for each radio option
              for (let i = 0; i < options.length; i++) {
                const optionValue = typeof options[i] === 'string' ? options[i] : (options[i].value || options[i].label || '');
                const optionLabel = typeof options[i] === 'string' ? options[i] : (options[i].label || options[i].value || '');
                
                // Pair by position when suffix +N is set; else match by condition
                let matchingInput;
                if (suffixN != null && i < suffixN && i < conditionalInputs.length) {
                  matchingInput = conditionalInputs[i];
                  this.logger.log(`  📌 Position-based pair: option[${i}] "${optionValue}" → ${matchingInput.key}`);
                } else {
                  matchingInput = conditionalInputs.find(input => {
                    const condition = (input.condition || '').trim();
                    const valueMatch = condition.match(/==\s*['"]?([^'"\s]+)['"]?\s*(?:#|$)/);
                    if (valueMatch && valueMatch[1].trim() === optionValue) return true;
                    const patterns = [
                      `== '${optionValue}'`,
                      `== "${optionValue}"`,
                      `=='${optionValue}'`,
                      `=="${optionValue}"`,
                      `== ${optionValue}`,
                      `==${optionValue}`
                    ];
                    return patterns.some(pattern => condition.includes(pattern));
                  });
                }
                if (!suffixN) this.logger.log(`  🔍 Looking for input matching option "${optionValue}": ${matchingInput ? `Found: ${matchingInput.key}` : 'Not found'}`);
                
                // Create zInputGroup container for this radio + input pair
                const inputGroupDiv = document.createElement('div');
                inputGroupDiv.classList.add('zInputGroup');
                if (value._zClass) {
                  const classes = value._zClass.split(' ').filter(c => c.trim() && c !== 'zCheck-input');
                  if (classes.length > 0) {
                    inputGroupDiv.classList.add(...classes);
                  }
                }
                
                // Create zInputGroup-text wrapper for radio
                const textWrapper = document.createElement('div');
                textWrapper.classList.add('zInputGroup-text');
                
                // Create radio input
                const { createInput } = await import('./primitives/form_primitives.js');
                const radioInput = createInput('radio', {
                  id: `${groupName}_${i}`,
                  name: groupName,
                  value: optionValue,
                  class: 'zCheck-input',
                  'aria-label': optionLabel
                });
                
                // Set checked state if default matches
                if (value.default === optionValue) {
                  radioInput.checked = true;
                }
                
                // Store zCross flag on radio element (for conditional rendering)
                radioInput.setAttribute('data-zcross', zCross.toString());
                
                textWrapper.appendChild(radioInput);
                inputGroupDiv.appendChild(textWrapper);
                
                // Add matching conditional input if found
                if (matchingInput) {
                  // Mark this input as matched so we don't process it again
                  matchedInputKeys.add(matchingInput.key);
                  // Support both shorthand (zInput) and expanded (zDisplay) payloads
                  const payload = matchingInput.payload || matchingInput.value.zInput || matchingInput.value.zDisplay || {};
                  const inputEventData = { event: 'read_string', ...payload };
                  if (matchingInput.value.zCross !== undefined) {
                    inputEventData.zCross = matchingInput.value.zCross;
                  }
                  {
                    // Remove prompt to prevent wrapper div creation
                    delete inputEventData.prompt;
                    // Render input directly into the zInputGroup (no wrapper needed)
                    // Pass inputGroupDiv as parent so it detects input-group context
                    const inputElement = await this.renderZDisplayEvent(inputEventData, inputGroupDiv);
                    if (inputElement) {
                      // If renderZDisplayEvent returns a wrapper, extract the actual input
                      // Otherwise use the element directly
                      if (inputElement.tagName === 'INPUT' || inputElement.tagName === 'TEXTAREA') {
                        inputGroupDiv.appendChild(inputElement);
                      } else {
                        // Wrapper returned - find the input inside and move it
                        const actualInput = inputElement.querySelector('input, textarea');
                        if (actualInput) {
                          inputGroupDiv.appendChild(actualInput);
                        } else {
                          inputGroupDiv.appendChild(inputElement);
                        }
                      }
                    }
                  }
                }
                
                groupContainer.appendChild(inputGroupDiv);
                this.logger.log(`  ✅ Created zInputGroup for radio option: ${optionValue}`);
              }
              
              // Skip normal rendering for this zSelect
              continue;
            }
            
            // Special handling for checkboxes in input-group: wrap in zInputGroup-text
            if (value.event === 'read_bool' && metadata._zGroup === 'input-group') {
              const wrapperDiv = document.createElement('div');
              wrapperDiv.classList.add('zInputGroup-text');
              wrapperDiv.setAttribute('data-zkey', key);
              
              // Render checkbox inside wrapper, passing wrapper as parent so it detects input-group context
              const checkboxElement = await this.renderZDisplayEvent(value, wrapperDiv);
              if (checkboxElement) {
                wrapperDiv.appendChild(checkboxElement);
              }
              groupContainer.appendChild(wrapperDiv);
              this.logger.log(`  ✅ Wrapped read_bool checkbox in zInputGroup-text for input-group`);
            } else {
              // Normal rendering for other events
              const element = await this.renderZDisplayEvent(value, groupContainer);
              if (element) {
                groupContainer.appendChild(element);
              }
            }
          } else {
            // Check for shorthand keys (zInput, zButton, etc.) that need expansion
            const shorthandKeys = ['zInput', 'zButton', 'zCheckbox', 'zSelect', 'zText', 'zMD', 'zH1', 'zH2', 'zH3', 'zH4', 'zH5', 'zH6', 'zURL', 'zImage'];
            const foundShorthand = shorthandKeys.find(sk => value[sk]);
            
            if (foundShorthand) {
              // This is a shorthand that needs to be rendered as a zDisplay event
              this.logger.log(`  Found shorthand '${foundShorthand}' in grouped item: ${key}`);
              
              // Special handling for radio zSelect in input-group: split into separate zInputGroup containers
              this.logger.log(`  🔍 Checking for radio zSelect shorthand: foundShorthand=${foundShorthand}, _zGroup=${metadata._zGroup}, zSelect.type=${value.zSelect?.type}`);
              if (foundShorthand === 'zSelect' && metadata._zGroup === 'input-group' && value.zSelect && value.zSelect.type === 'radio') {
                this.logger.log(`  ✅ Radio zSelect shorthand detected! Processing ${value.zSelect.options?.length || 0} options`);
                // Radio buttons in input-group: create separate zInputGroup for each option
                const options = value.zSelect.options || [];
                const zCross = value.zCross !== undefined ? value.zCross : false;
                const groupName = value.zSelect.zId || value.zSelect._zId || value.zSelect._id || `radio_${Math.random().toString(36).substr(2, 9)}`;
                
                // Find all conditional zInput elements (shorthand or expanded zDisplay) in declaration order
                const conditionalInputs = [];
                for (const [childKey, childValue] of Object.entries(data)) {
                  if (childValue && childValue.zInput && childValue.zInput.if) {
                    conditionalInputs.push({ key: childKey, value: childValue, condition: (childValue.zInput.if || '').replace(/#.*$/gm, '').trim(), payload: childValue.zInput });
                  } else if (childValue && childValue.zDisplay && childValue.zDisplay.event === 'read_string' && childValue.zDisplay.if) {
                    conditionalInputs.push({ key: childKey, value: childValue, condition: (childValue.zDisplay.if || '').replace(/#.*$/gm, '').trim(), payload: childValue.zDisplay });
                  }
                }
                // Parse suffix +N (e.g. "+3" => pair with next N inputs by position)
                const parseSuffixN = (s) => {
                  if (s == null) return null;
                  if (typeof s === 'number' && s > 0) return s;
                  const m = String(s).trim().match(/^\+(\d+)$/);
                  return m ? parseInt(m[1], 10) : null;
                };
                const suffixN = parseSuffixN(value.zSelect.suffix);
                this.logger.log(`  📌 suffix: ${value.zSelect.suffix} → suffixN=${suffixN}, conditionalInputs=${conditionalInputs.length}`);
                
                // Create a separate zInputGroup for each radio option
                for (let i = 0; i < options.length; i++) {
                  const optionValue = typeof options[i] === 'string' ? options[i] : (options[i].value || options[i].label || '');
                  const optionLabel = typeof options[i] === 'string' ? options[i] : (options[i].label || options[i].value || '');
                  
                  // Pair by position when suffix +N is set; else match by condition
                  let matchingInput;
                  if (suffixN != null && i < suffixN && i < conditionalInputs.length) {
                    matchingInput = conditionalInputs[i];
                    this.logger.log(`  📌 Position-based pair: option[${i}] "${optionValue}" → ${matchingInput.key}`);
                  } else {
                    matchingInput = conditionalInputs.find(input => {
                      const condition = (input.condition || '').trim();
                      const valueMatch = condition.match(/==\s*['"]?([^'"\s]+)['"]?\s*(?:#|$)/);
                      if (valueMatch && valueMatch[1].trim() === optionValue) return true;
                      const patterns = [
                        `== '${optionValue}'`,
                        `== "${optionValue}"`,
                        `=='${optionValue}'`,
                        `=="${optionValue}"`,
                        `== ${optionValue}`,
                        `==${optionValue}`
                      ];
                      return patterns.some(pattern => condition.includes(pattern));
                    });
                  }
                  
                  // Create zInputGroup container for this radio + input pair
                  const inputGroupDiv = document.createElement('div');
                  inputGroupDiv.classList.add('zInputGroup');
                  if (value.zSelect._zClass) {
                    const classes = value.zSelect._zClass.split(' ').filter(c => c.trim() && c !== 'zCheck-input');
                    if (classes.length > 0) {
                      inputGroupDiv.classList.add(...classes);
                    }
                  }
                  
                  // Create zInputGroup-text wrapper for radio
                  const textWrapper = document.createElement('div');
                  textWrapper.classList.add('zInputGroup-text');
                  
                  // Create radio input
                  const { createInput } = await import('./primitives/form_primitives.js');
                  const radioInput = createInput('radio', {
                    id: `${groupName}_${i}`,
                    name: groupName,
                    value: optionValue,
                    class: 'zCheck-input',
                    'aria-label': optionLabel
                  });
                  
                  // Set checked state if default matches
                  if (value.zSelect.default === optionValue) {
                    radioInput.checked = true;
                  }
                  
                  // Store zCross flag on radio element (for conditional rendering)
                  radioInput.setAttribute('data-zcross', zCross.toString());
                  
                  textWrapper.appendChild(radioInput);
                  inputGroupDiv.appendChild(textWrapper);
                  
                  // Add matching conditional input if found
                  if (matchingInput) {
                    // Mark this input as matched so we don't process it again
                    matchedInputKeys.add(matchingInput.key);
                    // Support both shorthand (zInput) and expanded (zDisplay) payloads from backend
                    const payload = matchingInput.payload || matchingInput.value.zInput || matchingInput.value.zDisplay || {};
                    const inputEventData = { event: 'read_string', ...payload };
                    if (matchingInput.value.zCross !== undefined) {
                      inputEventData.zCross = matchingInput.value.zCross;
                    }
                    // Remove prompt to prevent wrapper div creation
                    delete inputEventData.prompt;
                    const inputElement = await this.renderZDisplayEvent(inputEventData, inputGroupDiv);
                    if (inputElement) {
                      // Extract actual input/textarea if renderZDisplayEvent returned a wrapper
                      if (inputElement.tagName === 'INPUT' || inputElement.tagName === 'TEXTAREA') {
                        inputGroupDiv.appendChild(inputElement);
                      } else {
                        const actualInput = inputElement.querySelector('input, textarea');
                        if (actualInput) {
                          inputGroupDiv.appendChild(actualInput);
                        } else {
                          inputGroupDiv.appendChild(inputElement);
                        }
                      }
                    }
                  }
                  
                  groupContainer.appendChild(inputGroupDiv);
                  this.logger.log(`  ✅ Created zInputGroup for radio option: ${optionValue}`);
                }
                
                // Skip normal rendering for zSelect
                continue;
              }
              
              // Special handling for checkboxes in input-group: wrap in zInputGroup-text
              if (foundShorthand === 'zCheckbox' && metadata._zGroup === 'input-group') {
                // Check if already wrapped in a container with zInputGroup-text
                const hasInputGroupTextWrapper = value._zClass && value._zClass.includes('zInputGroup-text');
                
                if (!hasInputGroupTextWrapper) {
                  // Wrap checkbox in zInputGroup-text container
                  const wrapperDiv = document.createElement('div');
                  wrapperDiv.classList.add('zInputGroup-text');
                  wrapperDiv.setAttribute('data-zkey', key);
                  
                  // Expand zCheckbox to read_bool event and render directly into wrapper
                  // Pass zCross from parent value if present
                  const eventData = { event: 'read_bool', ...value.zCheckbox };
                  if (value.zCross !== undefined) {
                    eventData.zCross = value.zCross;
                  }
                  const checkboxElement = await this.renderZDisplayEvent(eventData, wrapperDiv);
                  if (checkboxElement) {
                    wrapperDiv.appendChild(checkboxElement);
                  }
                  groupContainer.appendChild(wrapperDiv);
                  this.logger.log(`  ✅ Wrapped checkbox in zInputGroup-text for input-group`);
                } else {
                  // Already wrapped, render normally
                  const element = await this.renderChunk({ [key]: value });
                  if (element && element.firstChild) {
                    const actualElement = element.firstChild;
                    groupContainer.appendChild(actualElement);
                  }
                }
              } else {
                // Recursively render the entire structure for other shorthands
                const element = await this.renderChunk({ [key]: value });
                if (element && element.firstChild) {
                  // Extract the actual rendered element (skip wrapper if present)
                  const actualElement = element.firstChild;
                  groupContainer.appendChild(actualElement);
                }
              }
            } else {
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
              const element = await this.renderZDisplayEvent(item.zDisplay, containerDiv);
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
        const element = await this.renderZDisplayEvent(value.zDisplay, containerDiv);
        if (element) {
          // BUG FIX: For direct UI events (zText, zH*, zMD, etc.), apply classes ONLY to the element
          // This prevents double-wrapping and ensures grid classes work correctly
          // Check if element has the same classes as containerDiv (indicating double-application)
          // Also check if element contains all containerDiv classes (handles class order differences)
          const containerClasses = containerDiv.className ? containerDiv.className.split(' ').filter(c => c.trim()) : [];
          const elementClasses = element.className ? element.className.split(' ').filter(c => c.trim()) : [];
          const hasAllContainerClasses = containerClasses.length > 0 && containerClasses.every(cls => elementClasses.includes(cls));
          
          if (containerDiv.className && element.className && (containerDiv.className === element.className || hasAllContainerClasses)) {
            this.logger.log(`[renderItems] 🔓 Unwrapping ${key}: element already has classes "${element.className}", skipping wrapper`);
            // Transfer data-zkey and id to the element
            element.setAttribute('data-zkey', key);
            if (!element.id) {
              element.setAttribute('id', key);
            }
            // Append element directly to parent (skip containerDiv)
            parentElement.appendChild(element);
            continue; // Skip the rest of the loop (don't append containerDiv)
          } else if ((!containerDiv.className || containerDiv.className === '') && !containerDiv.getAttribute('style')) {
            // Only unwrap if NO classes AND NO style (preserve _zStyle containers)
            this.logger.log(`[renderItems] 🔓 Unwrapping ${key}: no container classes or style, appending element directly to parent`);
            // Transfer data-zkey and id to the element
            element.setAttribute('data-zkey', key);
            if (!element.id) {
              element.setAttribute('id', key);
            }
            // Append element directly to parent (skip containerDiv)
            parentElement.appendChild(element);
            continue; // Skip the rest of the loop (don't append containerDiv)
          } else {
            this.logger.log(`[renderItems] 🔒 Keeping wrapper for ${key}: container has classes "${containerDiv.className}" or style "${containerDiv.getAttribute('style') || ''}"`);
            containerDiv.appendChild(element);
          }
        }
      } else if (value && value.event && typeof value.event === 'string') {
        // 🆕 Backend now sends unwrapped zDisplay events (direct event key, no zDisplay wrapper)
        // Example: {event: 'zCrumbs', show: 'static', ...}
        this.logger.log(`[renderItems] 🎯 Found direct event key: ${value.event} for ${key}, containerDiv classes: "${containerDiv.className}"`);
        const element = await this.renderZDisplayEvent(value, containerDiv);
        if (element) {
          // BUG FIX: For direct UI events, apply classes ONLY to the element
          // Check if element has the same classes as containerDiv (indicating double-application)
          // Also check if element contains all containerDiv classes (handles class order differences)
          const containerClasses = containerDiv.className ? containerDiv.className.split(' ').filter(c => c.trim()) : [];
          const elementClasses = element.className ? element.className.split(' ').filter(c => c.trim()) : [];
          const hasAllContainerClasses = containerClasses.length > 0 && containerClasses.every(cls => elementClasses.includes(cls));
          
          if (containerDiv.className && element.className && (containerDiv.className === element.className || hasAllContainerClasses)) {
            this.logger.log(`[renderItems] 🔓 Unwrapping ${key}: element already has classes "${element.className}", skipping wrapper`);
            // Transfer data-zkey and id to the element
            element.setAttribute('data-zkey', key);
            if (!element.id) {
              element.setAttribute('id', key);
            }
            // Append element directly to parent (skip containerDiv)
            parentElement.appendChild(element);
            continue; // Skip the rest of the loop (don't append containerDiv)
          } else if ((!containerDiv.className || containerDiv.className === '') && !containerDiv.getAttribute('style')) {
            // Only unwrap if NO classes AND NO style (preserve _zStyle containers)
            this.logger.log(`[renderItems] 🔓 Unwrapping ${key}: no container classes or style, appending element directly to parent`);
            // Transfer data-zkey and id to the element
            element.setAttribute('data-zkey', key);
            if (!element.id) {
              element.setAttribute('id', key);
            }
            // Append element directly to parent (skip containerDiv)
            parentElement.appendChild(element);
            continue; // Skip the rest of the loop (don't append containerDiv)
          } else {
            this.logger.log(`[renderItems] 🔒 Keeping wrapper for ${key}: container has classes "${containerDiv.className}" or style "${containerDiv.getAttribute('style') || ''}"`);
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
            'zSelect': 'selection',
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
            // ═══════════════════════════════════════════════════════════════
            // SCALAR SHORTHAND SUPPORT (2026-01-28)
            // Allows: zText: "string" instead of zText: {content: "string"}
            // ═══════════════════════════════════════════════════════════════
            let shorthandValue = value[shorthandKey];
            if (typeof shorthandValue === 'string') {
              // Normalize scalar to object
              if (shorthandKey === 'zText' || shorthandKey === 'zMD') {
                shorthandValue = { content: shorthandValue };
              } else if (shorthandKey.startsWith('zH') && shorthandKey.length === 3) {
                shorthandValue = { label: shorthandValue };
              } else {
                shorthandValue = { content: shorthandValue }; // Default fallback
              }
              this.logger.log(`[renderItems] 📝 Normalized scalar shorthand: ${shorthandKey} = "${value[shorthandKey]}"`);
            }
            
            // Expand shorthand to event data inline
            const eventData = { event: eventType, ...shorthandValue };
            
            // For headers, add indent from key name
            if (eventType === 'header') {
              eventData.indent = parseInt(shorthandKey.substring(2)); // Extract number from zH1, zH2, etc.
            }
            
            this.logger.log(`[renderItems] 🔄 Expanding ${shorthandKey} to event ${eventType}:`, eventData);
            const element = await this.renderZDisplayEvent(eventData, containerDiv);
            if (element) {
              // Unwrap if no container classes AND no style (preserve _zStyle containers)
              if ((!containerDiv.className || containerDiv.className === '') && !containerDiv.getAttribute('style')) {
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

      // Append container to parent (if it has children)
      // NOTE: zCard-body auto-enhancement REMOVED (2026-01-28)
      // Users should explicitly declare _zClass: zCard-body when needed.
      if (containerDiv.children.length > 0) {
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
   * @param {HTMLElement} [parentElement=null] - Optional parent element for context detection
   * @returns {Promise<HTMLElement>}
   */
  async renderZDisplayEvent(eventData, parentElement = null) {
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
        
        // Conditional rendering support (if parameter from zWizard)
        const condition = eventData.if || null;
        if (condition) {
          console.log(`[renderZDisplayEvent] 🔍 Found 'if' condition in read_string event: "${condition}"`);
        }
        
        // Support zId (universal), _zId (Bifrost-only), and _id (legacy)
        const inputId = eventData.zId || eventData._zId || eventData._id || `input_${Math.random().toString(36).substr(2, 9)}`;
        
        // Generate datalist ID if datalist exists
        const datalistId = datalist ? `${inputId}_datalist` : null;
        
        // Support aria-describedby for accessibility (link to help text)
        const ariaDescribedBy = eventData.aria_described_by || eventData.ariaDescribedBy || eventData['aria-describedby'];
        
        // Detect if we're inside a zInputGroup context (parent or ancestor has zInputGroup class)
        let isInsideInputGroup = false;
        let checkParent = parentElement;
        while (checkParent && checkParent !== document.body) {
          if (checkParent.classList && checkParent.classList.contains('zInputGroup')) {
            isInsideInputGroup = true;
            break;
          }
          checkParent = checkParent.parentElement;
        }
        
        // Create wrapper div only if prompt exists AND not inside input group
        // Otherwise return input directly to avoid double-nesting in grid layouts or input groups
        let wrapper = null;
        let wrapperClasses = null; // Track _zClass for wrapper (not input element)
        
        // Create label if prompt exists (connected to input via for/id)
        if (prompt && !isInsideInputGroup) {
          wrapper = document.createElement('div');
          
          // Apply _zClass to wrapper (not input element) to avoid double-nesting
          // When wrapper exists, _zClass applies to the wrapper container
          if (eventData._zClass) {
            const classes = eventData._zClass.split(' ').filter(c => c.trim());
            wrapper.classList.add(...classes);
            wrapperClasses = eventData._zClass;
            this.logger.log(`[renderZDisplayEvent] Applied _zClass to wrapper: ${eventData._zClass}`);
          }
          
          // Use zLabel class for styled inputs, no class for basic semantic HTML
          // Check if wrapper has zInput class (from _zClass) to determine label styling
          const hasZInputClass = wrapperClasses && wrapperClasses.includes('zInput');
          const labelClass = hasZInputClass ? 'zLabel' : '';
          const labelAttrs = labelClass ? { class: labelClass } : {};
          const label = createLabel(inputId, labelAttrs);
          label.textContent = prompt;
          wrapper.appendChild(label);
          // Add line break after label (semantic HTML pattern)
          wrapper.appendChild(document.createElement('br'));
        }
        
        // Check if we'll have prefix/suffix (which creates zInputGroup)
        // Helper to format prefix/suffix values (defined early for class determination)
        const formatAffix = (value) => {
          if (!value && value !== 0) return '';
          if (typeof value === 'string') return value;
          if (typeof value === 'boolean') return String(value);
          if (typeof value === 'number') {
            if (value >= 0 && value < 1) {
              return value.toFixed(2).replace(/^0/, '') || '0';
            }
            return String(value);
          }
          return String(value);
        };
        
        const prefix = formatAffix(eventData.prefix);
        const suffix = formatAffix(eventData.suffix);
        const hasInputGroup = !!(prefix || suffix);
        
        // Build input classes: 
        // - If inside zInputGroup, use 'zInput' (required by CSS: .zInputGroup > .zInput)
        // - If wrapper exists, use default 'zForm-control' (wrapper has _zClass)
        // - Otherwise use _zClass or default 'zForm-control'
        let inputClasses;
        if (isInsideInputGroup) {
          // If inside zInputGroup, use 'zInput' class (required by CSS: .zInputGroup > .zInput)
          inputClasses = 'zInput';
        } else if (hasInputGroup) {
          // Input groups require 'zInput' class for proper flex styling
          inputClasses = 'zInput';
        } else if (wrapperClasses) {
          // Wrapper has _zClass, input gets default styling
          inputClasses = 'zForm-control';
        } else {
          // No wrapper, use _zClass if provided, otherwise default
          inputClasses = eventData._zClass || 'zForm-control';
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
        
        // Handle input groups (prefix/suffix pattern) - Terminal-first design
        // Note: prefix and suffix were already determined above for class selection
        if (hasInputGroup) {
          // Create .zInputGroup wrapper for prefix/suffix pattern
          const inputGroup = document.createElement('div');
          inputGroup.classList.add('zInputGroup');
          
          // Add prefix text before input
          if (prefix) {
            const prefixSpan = document.createElement('span');
            prefixSpan.classList.add('zInputGroup-text');
            prefixSpan.textContent = prefix;
            inputGroup.appendChild(prefixSpan);
          }
          
          // Add input element
          inputGroup.appendChild(inputElement);
          
          // Add suffix text after input
          if (suffix) {
            const suffixSpan = document.createElement('span');
            suffixSpan.classList.add('zInputGroup-text');
            suffixSpan.textContent = suffix;
            inputGroup.appendChild(suffixSpan);
          }
          
          // Replace inputElement with the input group
          inputElement = inputGroup;
          
          this.logger.log(`[renderZDisplayEvent] Created input group with prefix='${prefix}', suffix='${suffix}'`);
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
          
          // Apply _zStyle to wrapper if present (when wrapper exists, styles go on wrapper)
          if (eventData._zStyle) {
            wrapper.setAttribute('style', eventData._zStyle);
          }
          
          // Handle conditional rendering (if parameter from zWizard)
          if (condition) {
            wrapper.setAttribute('data-zif', condition);
            wrapper.style.display = 'none'; // Initially hidden
            this.logger.log(`[renderZDisplayEvent] Input with condition: ${condition} (initially hidden)`);
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
            
            // Handle conditional rendering
            if (condition) {
              container.setAttribute('data-zif', condition);
              container.style.display = 'none'; // Initially hidden
              this.logger.log(`[renderZDisplayEvent] Input with condition: ${condition} (initially hidden)`);
            }
            
            element = container;
          } else {
            // Handle conditional rendering for bare input
            if (condition) {
              inputElement.setAttribute('data-zif', condition);
              inputElement.style.display = 'none'; // Initially hidden
              this.logger.log(`[renderZDisplayEvent] Input with condition: ${condition} (initially hidden)`);
            }
            
            element = inputElement;
          }
        }
        
        this.logger.log(`[renderZDisplayEvent] Rendered ${event} ${inputType} (id=${inputId}, aria-describedby=${ariaDescribedBy || 'none'}, condition=${condition || 'none'})`);
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
        
        // Detect if we're inside a zInputGroup context (parent has zInputGroup-text class)
        const isInsideInputGroup = parentElement && parentElement.classList && parentElement.classList.contains('zInputGroup-text');
        
        // Create checkbox input (type='checkbox')
        const checkbox = createInput('checkbox', {
          checked: checked,
          required: required,
          class: checkboxClasses,
          id: checkboxId
        });
        
        // Store zCross flag on checkbox element (defaults to false if not set)
        // zCross: true = terminal-first behavior (conditional rendering)
        // zCross: false = HTML-like behavior (always visible)
        const zCross = eventData.zCross !== undefined ? eventData.zCross : false;
        checkbox.setAttribute('data-zcross', zCross.toString());
        
        // If inside input group, render checkbox directly without wrapper
        if (isInsideInputGroup) {
          element = checkbox;
          this.logger.log(`[renderZDisplayEvent] Rendered ${event} checkbox (input-group mode, no wrapper): (id=${checkboxId}, checked=${checked})`);
        } else {
          // Normal mode: Create form check container (Bootstrap-style checkbox)
          const formCheck = createDiv({ class: 'zForm-check zmb-3' });
          
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
        }
        
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
        
        // Detect if we're inside a zInputGroup context (for compact rendering)
        const isInsideInputGroup = parentElement && parentElement.classList && parentElement.classList.contains('zInputGroup-text');
        
        // Render based on type
        if (type === 'radio' || (type === 'checkbox' && multi)) {
          // Radio button group or checkbox group
          const inputType = type === 'radio' ? 'radio' : 'checkbox';
          const groupName = baseId; // Use baseId as group name for radio buttons
          
          // CHUNK MODE: When inside zInputGroup-text, render raw radios without labels/wrappers
          if (isInsideInputGroup) {
            // Just render the first radio input directly (for single-option-per-group pattern)
            // Or all radios stacked if multiple options
            const firstOptionValue = options[0];
            const optionVal = typeof firstOptionValue === 'string' ? firstOptionValue : (firstOptionValue.value || firstOptionValue.label || '');
            
            const input = createInput(inputType, {
              id: `${baseId}_0`,
              name: groupName,
              value: optionVal,
              disabled: disabled,
              required: required,
              class: elementClasses || 'zCheck-input'
            });
            
            // Set checked state
            if (defaultValue !== null && (optionVal === defaultValue || (Array.isArray(defaultValue) && defaultValue.includes(optionVal)))) {
              input.checked = true;
            }
            
            element = input;
            this.logger.log(`[renderZDisplayEvent] Rendered ${event} ${inputType} (input-group mode, no wrapper): (id=${baseId}, value=${optionVal})`);
          } else {
            // NORMAL MODE: Standard radio/checkbox group with labels
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
          }
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

      case 'zTerminal': {
        // Code execution sandbox with syntax highlighting and Run button
        const terminalRenderer = await this.client._ensureTerminalRenderer();
        element = terminalRenderer.render(eventData);
        this.logger.log(`[renderZDisplayEvent] Rendered zTerminal: ${eventData.title || 'untitled'}`);
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

