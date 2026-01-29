/**
 * ═══════════════════════════════════════════════════════════════
 * Navigation Renderer - zTheme Navigation Components
 * ═══════════════════════════════════════════════════════════════
 *
 * Renders navigation components aligned with zTheme:
 * - zNav (navigation bars)
 * - zNavbar (top navigation)
 * - zBreadcrumb (breadcrumb trails)
 * - zTabs (tabbed navigation)
 * - zPagination (page navigation)
 * - Sidebar navigation
 * - Dropdown menus
 *
 * ✨ REFACTORED: Uses Layer 0 primitives
 *
 * @module rendering/navigation_renderer
 * @layer 3
 * @pattern Strategy (navigation components)
 *
 * @see https://github.com/ZoloAi/zTheme - zTheme Navigation
 */

// ─────────────────────────────────────────────────────────────────
// Imports
// ─────────────────────────────────────────────────────────────────
import { createNav } from './primitives/document_structure_primitives.js';
import { createList, createListItem } from './primitives/lists_primitives.js';
import { createLink, createButton } from './primitives/interactive_primitives.js';
import { createDiv, createSpan } from './primitives/generic_containers.js';
import { renderLink } from './primitives/link_primitives.js'; // NEW: Use link primitive
import { withErrorBoundary } from '../utils/error_boundary.js';

export class NavigationRenderer {
  constructor(logger = null, client = null) {
    this.logger = logger || console;
    this.client = client; // NEW: Store client for link rendering

    // Wrap renderNavBar method with error boundary
    // Note: We wrap it after the class is fully initialized
    const proto = Object.getPrototypeOf(this);
    if (proto.renderNavBar) {
      const originalRenderNavBar = proto.renderNavBar.bind(this);
      this.renderNavBar = withErrorBoundary(originalRenderNavBar, {
        component: 'NavigationRenderer.renderNavBar',
        logger: this.logger
      });
    }
  }

  /**
   * Render a navigation bar from menu items (zTheme zNavbar component)
   * @param {Array<string|Object>} items - Array of navigation items (strings or {label, href})
   * @param {Object} options - Rendering options
   * @returns {HTMLElement} - Navigation element with zNavbar classes
   * @see https://github.com/ZoloAi/zTheme/blob/main/src/css/zNavbar.css
   */
  renderNavBar(items, options = {}) {
    if (!Array.isArray(items) || items.length === 0) {
      this.logger.warn('[NavigationRenderer] No items provided for navbar');
      return null;
    }

    const {
      className = 'zcli-navbar-meta',
      theme = 'light',
      activeIndex = null,
      href = '#',
      brand = null
    } = options;

    // Generate unique ID for collapse target
    const collapseId = `navbar-collapse-${Math.random().toString(36).substr(2, 9)}`;

    // Create nav container with zNavbar component classes (using primitive)
    const nav = createNav({
      class: `zNavbar zNavbar-${theme} ${className}`,
      role: 'navigation'
    });

    // Add brand/logo if provided (using primitive)
    if (brand) {
      const brandLink = createLink('/', { class: 'zNavbar-brand' });
      brandLink.textContent = brand;
      nav.appendChild(brandLink);
    }

    // Create mobile hamburger toggle button (using primitive)
    const toggleButton = createButton('button', {
      class: 'zNavbar-toggler',
      'data-bs-toggle': 'collapse',
      'data-bs-target': `#${collapseId}`,
      'aria-controls': collapseId,
      'aria-expanded': 'false',
      'aria-label': 'Toggle navigation'
    });

    // Add Bootstrap Icon (hamburger menu)
    toggleButton.innerHTML = `
      <i class="bi bi-list" style="font-size: 1.5rem;"></i>
    `;
    nav.appendChild(toggleButton);

    // Create navbar collapse wrapper (using primitive)
    const collapseDiv = createDiv({
      class: 'zNavbar-collapse',
      id: collapseId
    });

    // ✨ FIX: Add manual toggle handler (zTheme doesn't include Bootstrap JS)
    toggleButton.addEventListener('click', (e) => {
      e.preventDefault();
      const isExpanded = toggleButton.getAttribute('aria-expanded') === 'true';

      // Toggle aria state
      toggleButton.setAttribute('aria-expanded', !isExpanded);

      // Toggle visibility (try both 'show' and 'zShow' for compatibility)
      if (isExpanded) {
        collapseDiv.classList.remove('show', 'zShow');
        this.logger.log('[NavigationRenderer] 🍔 Navbar collapsed');
      } else {
        collapseDiv.classList.add('show', 'zShow');
        this.logger.log('[NavigationRenderer] 🍔 Navbar expanded');
      }
    });
    this.logger.log('[NavigationRenderer] ✅ Hamburger toggle handler attached to:', collapseId);

    // Create navigation list (using primitive)
    const ul = createList(false, { class: 'zNavbar-nav' });

    // ✨ REFACTORED: Use link_primitives.js for ALL navigation links
    // This ensures consistent behavior between navbar and content links
    items.forEach((item, index) => {
      const li = createListItem({ class: 'zNav-item' });

      // Check if this is a hierarchical item with zSub
      if (typeof item === 'object' && item !== null && !item.label && !item.href) {
        // Dict format: {"zProducts": {"zSub": ["zCLI", "zBifrost", ...]}}
        const itemName = Object.keys(item)[0];
        const itemData = item[itemName];
        
        if (itemData && typeof itemData === 'object' && itemData.zSub && Array.isArray(itemData.zSub)) {
          // This is a hierarchical menu item - render using zTheme's zDropdown component
          li.classList.add('zDropdown'); // zTheme dropdown container
          
          const parentLabel = itemName.replace(/^[$^~]+/, '');
          const parentHref = this._convertDeltaLinkToHref(itemName);
          
          // Create dropdown toggle link (zTheme adds caret automatically via ::after)
          const dropdownLink = createLink(parentHref, {
            class: `zNav-link zDropdown-toggle${activeIndex === index ? ' active' : ''}`,
            'data-toggle': 'dropdown',
            'aria-haspopup': 'true',
            'aria-expanded': 'false'
          });
          dropdownLink.textContent = parentLabel;
          
          // Create dropdown menu using zTheme classes
          const dropdownMenu = createDiv({ class: 'zDropdown-menu' });
          
          // Add sub-items using zTheme's zDropdown-item class
          itemData.zSub.forEach(subItem => {
            const subHref = `${parentHref}/${subItem}`;
            const subLink = createLink(subHref, { class: 'zDropdown-item' });
            subLink.textContent = subItem;
            
            // Add click handler for internal navigation
            subLink.addEventListener('click', (e) => {
              e.preventDefault();
              // Close dropdown after selection
              dropdownMenu.classList.remove('zShow');
              dropdownLink.setAttribute('aria-expanded', 'false');
              
              if (this.client && this.client.navigationManager) {
                this.client.navigationManager.navigateToRoute(subHref);
              } else {
                window.location.href = subHref;
              }
            });
            
            dropdownMenu.appendChild(subLink);
          });
          
          // Toggle dropdown on click (zTheme pattern)
          dropdownLink.addEventListener('click', (e) => {
            e.preventDefault();
            const isOpen = dropdownMenu.classList.contains('zShow');
            
            // Close all other dropdowns
            document.querySelectorAll('.zDropdown-menu.zShow').forEach(menu => {
              if (menu !== dropdownMenu) {
                menu.classList.remove('zShow');
                const toggle = menu.previousElementSibling;
                if (toggle) toggle.setAttribute('aria-expanded', 'false');
              }
            });
            
            // Toggle this dropdown
            if (isOpen) {
              dropdownMenu.classList.remove('zShow');
              dropdownLink.setAttribute('aria-expanded', 'false');
            } else {
              dropdownMenu.classList.add('zShow');
              dropdownLink.setAttribute('aria-expanded', 'true');
            }
          });
          
          li.appendChild(dropdownLink);
          li.appendChild(dropdownMenu);
          ul.appendChild(li);
          
          this.logger.log(`[NavigationRenderer] 🔽 Created zTheme dropdown for ${parentLabel} with ${itemData.zSub.length} sub-items`);
          return; // Continue to next item
        }
      }

      // Handle simple item as string or object {label, href}
      let itemLabel, itemHref, originalItem;
      if (typeof item === 'string') {
        // Strip navigation prefixes for clean display
        // $ (delta link), ^ (bounce-back), ~ (anchor)
        // Example: "$^zLogin" → "zLogin"
        originalItem = item;
        itemLabel = item.replace(/^[$^~]+/, '');
        // Convert delta links ($zBlock) to web routes (/zBlock)
        itemHref = this._convertDeltaLinkToHref(item);
      } else if (typeof item === 'object' && item !== null) {
        originalItem = item.label || item.text || '';
        itemLabel = originalItem.replace(/^[$^~]+/, '');
        itemHref = item.href || this._convertDeltaLinkToHref(itemLabel);
      } else {
        originalItem = String(item);
        itemLabel = originalItem;
        itemHref = href;
      }

      // Detect link type for renderLink primitive
      const linkType = this._detectLinkType(itemHref, originalItem);

      // Prepare link data for renderLink primitive
      const linkData = {
        label: itemLabel,
        href: itemHref,
        target: '_self',
        link_type: linkType,
        _zClass: `zNav-link${activeIndex === index ? ' active' : ''}`,
        color: '',
        window: {}
      };

      this.logger.log('[NavigationRenderer] 🎯 Creating navbar link:', linkData);

      // ✅ Use renderLink primitive (now returns element directly)
      const link = renderLink(linkData, null, this.client);

      if (link) {
        li.appendChild(link);
      } else {
        this.logger.error('[NavigationRenderer] ❌ renderLink returned no link element');
      }

      ul.appendChild(li);
    });

    // Assemble: ul -> collapseDiv -> nav
    collapseDiv.appendChild(ul);
    nav.appendChild(collapseDiv);

    // Close dropdowns when clicking outside (zTheme pattern)
    const closeDropdowns = (e) => {
      if (!nav.contains(e.target)) {
        nav.querySelectorAll('.zDropdown-menu.zShow').forEach(menu => {
          menu.classList.remove('zShow');
          const toggle = menu.previousElementSibling;
          if (toggle) {
            toggle.setAttribute('aria-expanded', 'false');
          }
        });
      }
    };
    
    // Use setTimeout to avoid immediate triggering
    setTimeout(() => {
      document.addEventListener('click', closeDropdowns);
    }, 100);

    this.logger.log('[NavigationRenderer] ✅ Rendered navbar with', items.length, 'items (using zTheme classes)');

    return nav;
  }

  /**
   * Convert delta link notation ($zBlock) to web route (/zBlock)
   *
   * Delta links ($) are used in YAML for intra-file navigation.
   * Navigation modifiers (^, ~) are stripped for clean URLs.
   * In Bifrost mode, these are converted to web routes for proper navigation.
   *
   * @param {string} item - Item text (may contain $^zBlock notation with modifiers)
   * @returns {string} - Web-friendly href
   * @private
   */
  _convertDeltaLinkToHref(item) {
    if (typeof item !== 'string') {
      return '#';
    }

    // Strip all navigation prefixes: $ (delta), ^ (bounce-back), ~ (anchor)
    // Example: "$^zLogin" → "zLogin" → "/zLogin"
    const cleanBlock = item.replace(/^[$^~]+/, '');

    // Check if original item had $ (delta link) or other navigation prefixes
    if (item !== cleanBlock) {
      // Had navigation prefixes - convert to web route
      return `/${cleanBlock}`;
    }

    // Default: use item as-is (for explicit /path or # links)
    return item.startsWith('/') || item.startsWith('#') ? item : `/${item}`;
  }

  /**
   * Detect link type from href and original item.
   *
   * This mirrors the logic in link_primitives.js to ensure consistent
   * link type detection across navbar and content links.
   *
   * @param {string} href - Converted href (e.g., "/zBlock")
   * @param {string} originalItem - Original item with prefixes (e.g., "$zBlock")
   * @returns {string} - Link type: 'delta', 'zpath', 'external', 'anchor', 'placeholder'
   * @private
   */
  _detectLinkType(href, originalItem) {
    // Check original item for navigation prefixes
    if (originalItem && typeof originalItem === 'string') {
      // Delta link ($) - internal navigation
      if (originalItem.startsWith('$') || originalItem.includes('$')) {
        return 'delta';
      }
      // zPath (@) - absolute path navigation
      if (originalItem.startsWith('@')) {
        return 'zpath';
      }
    }

    // Check href for external URLs
    if (href.startsWith('http://') || href.startsWith('https://') || href.startsWith('www.')) {
      return 'external';
    }

    // Check for anchor links
    if (href.startsWith('#') && href !== '#') {
      return 'anchor';
    }

    // Placeholder link
    if (!href || href === '#') {
      return 'placeholder';
    }

    // Default: treat as delta (internal navigation)
    return 'delta';
  }

  /**
   * Render breadcrumb navigation (zTheme-styled)
   * @param {Array<string>} trail - Breadcrumb trail items
   * @param {Object} options - Rendering options
   * @returns {HTMLElement} - Breadcrumb element with zTheme classes
   */
  renderBreadcrumb(trail, options = {}) {
    if (!Array.isArray(trail) || trail.length === 0) {
      return null;
    }

    const {
      separator = '>',
      className = 'zcli-breadcrumb'
    } = options;

    const nav = createNav({
      class: `${className} zmb-3`,
      'aria-label': 'breadcrumb'
    });

    const ol = createList(true, {
      class: 'zD-flex zFlex-row zFlex-items-center zGap-2'
    });
    ol.style.listStyle = 'none';
    ol.style.padding = '0';
    ol.style.margin = '0';

    trail.forEach((item, index) => {
      const li = createListItem({ class: 'breadcrumb-item' });

      if (index === trail.length - 1) {
        // Last item (current page) - use muted text, bold weight (using primitive)
        const span = createSpan({
          class: 'zText-muted zFw-bold',
          'aria-current': 'page'
        });
        span.textContent = item;
        li.appendChild(span);
      } else {
        // Link to parent pages - use primary color (using primitive)
        const a = createLink('#', { class: 'zText-primary zText-decoration-none' });
        a.textContent = item;
        li.appendChild(a);
      }

      ol.appendChild(li);

      // Add separator (except after last item) (using primitive)
      if (index < trail.length - 1) {
        const sep = createSpan({ class: 'breadcrumb-separator zText-muted' });
        sep.textContent = ` ${separator} `;
        ol.appendChild(sep);
      }
    });

    nav.appendChild(ol);
    return nav;
  }

  /**
   * Render breadcrumbs from zCrumbs display event (handles multiple trails)
   * Uses zTheme breadcrumb structure: nav > ol.zBreadcrumb > li.zBreadcrumb-item
   * 
   * Single trail: Returns <nav> directly (no wrapper div) - semantic HTML like zH1
   * Multi-trail: Returns container div with multiple navs + scope labels
   * 
   * @param {Object} eventData - Event data from backend zCrumbs event
   * @returns {HTMLElement|null} - nav element (single trail) or container div (multi-trail)
   * @see zOS/zTheme/Manual/ztheme-breadcrumb.html
   */
  renderBreadcrumbs(eventData) {
    // Extract crumbs data from event (backend sends in _KEY_CRUMBS or crumbs)
    this.logger.log('[NavigationRenderer] renderBreadcrumbs called with eventData:', eventData);
    
    const crumbsData = eventData.crumbs || eventData._KEY_CRUMBS || {};
    this.logger.log('[NavigationRenderer] Extracted crumbsData:', crumbsData);
    
    const trails = crumbsData.trails || {};
    this.logger.log('[NavigationRenderer] Extracted trails:', trails);
    
    // Filter out internal metadata (_context, _depth_map)
    const visibleTrails = Object.entries(trails).filter(([key]) => !key.startsWith('_'));
    this.logger.log('[NavigationRenderer] Visible trails:', visibleTrails);
    
    if (visibleTrails.length === 0) {
      this.logger.log('[NavigationRenderer] No visible breadcrumb trails - returning null');
      return null; // No breadcrumbs to display
    }
    
    this.logger.log(`[NavigationRenderer] Rendering ${visibleTrails.length} breadcrumb trails`);
    
    // Helper: build trail items into an <ol>
    const buildTrailOl = (scope, trail) => {
      const ol = createList(true, { class: 'zBreadcrumb' });
      
      if (trail.length === 0) {
        // Empty trail: show just the scope name (like Terminal: "scope[]")
        const li = createListItem({ class: 'zBreadcrumb-item zActive' });
        li.setAttribute('aria-current', 'page');
        li.textContent = `${scope}[]`;
        ol.appendChild(li);
      } else {
        trail.forEach((item, index) => {
          const isLast = (index === trail.length - 1);
          const li = createListItem({ 
            class: isLast ? 'zBreadcrumb-item zActive' : 'zBreadcrumb-item'
          });
          
          if (isLast) {
            li.setAttribute('aria-current', 'page');
            li.textContent = item;
          } else {
            // Parent pages - clickable links with navigation
            const cumulativePath = trail.slice(0, index + 1).join('.');
            const routePath = '/' + cumulativePath.replace(/\./g, '/');
            
            const a = createLink('#', {});
            a.textContent = item;
            a.onclick = async (e) => {
              e.preventDefault();
              this.logger.log(`[Breadcrumbs] Navigating to: ${routePath}`);
              
              if (this.client && this.client.navigationManager) {
                try {
                  await this.client.navigationManager.navigateToRoute(routePath);
                } catch (error) {
                  this.logger.error('[Breadcrumbs] Navigation failed:', error);
                }
              } else {
                this.logger.warn('[Breadcrumbs] No navigationManager available');
              }
            };
            li.appendChild(a);
          }
          
          ol.appendChild(li);
        });
      }
      
      return ol;
    };
    
    // ═══════════════════════════════════════════════════════════════
    // SINGLE TRAIL: Return <nav> directly (no wrapper div)
    // This treats zCrumbs like zH1 - semantic element is the root
    // ═══════════════════════════════════════════════════════════════
    if (visibleTrails.length === 1) {
      const [scope, trail] = visibleTrails[0];
      if (!Array.isArray(trail)) return null;
      
      const nav = createNav({
        'aria-label': `${scope} breadcrumb`,
        'class': 'zmb-3'  // Margin on nav directly
      });
      
      nav.appendChild(buildTrailOl(scope, trail));
      this.logger.log('[NavigationRenderer] Single trail - returning nav directly (no wrapper div)');
      return nav;
    }
    
    // ═══════════════════════════════════════════════════════════════
    // MULTI-TRAIL: Keep container div for multiple navs + scope labels
    // ═══════════════════════════════════════════════════════════════
    const container = createDiv({ class: 'zBreadcrumbs-container zmb-3' });
    
    visibleTrails.forEach(([scope, trail]) => {
      if (!Array.isArray(trail)) return;
      
      // Add scope label for multi-trail displays
      const scopeLabel = createSpan({ class: 'zText-muted zSmall zFw-bold zD-block' });
      scopeLabel.textContent = `${scope}:`;
      scopeLabel.style.marginBottom = '0.25rem';
      container.appendChild(scopeLabel);
      
      const nav = createNav({ 'aria-label': `${scope} breadcrumb` });
      nav.appendChild(buildTrailOl(scope, trail));
      container.appendChild(nav);
    });
    
    this.logger.log('[NavigationRenderer] Multi-trail - returning container div');
    return container;
  }

  /**
   * Render vertical sidebar navigation (zTheme-styled)
   * @param {Array<string>} items - Navigation item labels
   * @param {Object} options - Rendering options
   * @returns {HTMLElement} - Sidebar nav element with zTheme classes
   */
  renderSidebarNav(items, options = {}) {
    if (!Array.isArray(items) || items.length === 0) {
      return null;
    }

    const {
      className = 'zcli-sidebar-nav',
      activeIndex = null
    } = options;

    // Sidebar container with zTheme utilities (using primitive)
    const nav = createNav({ class: `${className} zBg-light zP-3 zRounded` });
    nav.style.width = '200px';

    const ul = createList(false, { class: 'zD-flex zFlex-column zGap-2' });
    ul.style.listStyle = 'none';
    ul.style.padding = '0';
    ul.style.margin = '0';

    items.forEach((item, index) => {
      const li = createListItem({ class: 'sidebar-item' });

      const a = createLink('#');
      a.textContent = item;

      // zTheme sidebar link: padding, display block, rounded
      a.className = 'sidebar-link zText-dark zText-decoration-none zP-2 zD-block zRounded';

      // Active state with zTheme classes
      if (activeIndex === index) {
        a.classList.add('zBg-primary', 'zText-white', 'zFw-bold');
      }

      // Hover effect via zTheme classes
      a.addEventListener('mouseenter', () => {
        if (activeIndex !== index) {
          a.classList.add('zBg-white');
        }
      });
      a.addEventListener('mouseleave', () => {
        if (activeIndex !== index) {
          a.classList.remove('zBg-white');
        }
      });

      li.appendChild(a);
      ul.appendChild(li);
    });

    nav.appendChild(ul);
    return nav;
  }
}

