/**
 * ═══════════════════════════════════════════════════════════════
 * Link Primitives - Semantic Link Rendering with Target Support
 * ═══════════════════════════════════════════════════════════════
 *
 * Renders semantic HTML links with proper href, target, and security
 * attributes for zDisplay link events.
 *
 * @module rendering/link_primitives
 * @layer 1.0 (Event-aware primitive renderer)
 * @pattern Factory + Event Handler Pattern
 *
 * Philosophy:
 * - Semantic HTML (use <a> for navigation, not <button>)
 * - Security-first (auto-add rel="noopener noreferrer" for _blank)
 * - Target support (_blank, _self, _parent, _top, custom window.open())
 * - Mode-aware (handles internal vs external vs anchor links)
 *
 * Link Types:
 * - Internal Delta: $zAbout → Client-side routing
 * - Internal zPath: @.UI.zUI.zAbout → Client-side routing
 * - External: https://example.com → Native browser navigation
 * - Anchor: #section → Smooth scroll to element
 * - Placeholder: # → No navigation (styled text)
 *
 * Target Behavior:
 * - _self: Navigate in current tab (default)
 * - _blank: Open in new tab/window (auto-add security)
 * - _parent: Navigate parent frame
 * - _top: Navigate top-level frame
 * - Custom window: Use window.open() with features
 *
 * Security:
 * - External _blank links: Auto-add rel="noopener noreferrer"
 * - Prevents window.opener exploitation (Tabnabbing attack)
 * - User can override via explicit rel parameter
 *
 * Dependencies:
 * - utils/dom_utils.js (createElement, setAttributes)
 * - bifrost_client.js (for client-side navigation)
 *
 * Exports:
 * - renderLink(linkData, container, client) → void
 *
 * Example:
 * ```javascript
 * import { renderLink } from './link_primitives.js';
 *
 * // Internal link
 * renderLink({
 *   label: 'About',
 *   href: '$zAbout',
 *   target: '_self'
 * }, container, bifrostClient);
 *
 * // External link (new tab)
 * renderLink({
 *   label: 'GitHub',
 *   href: 'https://github.com',
 *   target: '_blank',
 *   _zClass: 'zBtn zBtn-primary'
 * }, container, bifrostClient);
 * ```
 */

import { createElement } from '../../utils/dom_utils.js';

// Link type constants (must match backend)
const LINK_TYPE_INTERNAL_DELTA = 'delta';
const LINK_TYPE_INTERNAL_ZPATH = 'zpath';
const LINK_TYPE_EXTERNAL = 'external';
const LINK_TYPE_ANCHOR = 'anchor';
const LINK_TYPE_PLACEHOLDER = 'placeholder';

// Target constants
const TARGET_BLANK = '_blank';
const TARGET_SELF = '_self';

// ─────────────────────────────────────────────────────────────────
// Helper: Fallback Link Type Detection (Frontend Safety)
// ─────────────────────────────────────────────────────────────────

/**
 * Detect link type from href when backend doesn't provide it.
 *
 * This is a fallback mechanism to ensure robust link rendering even
 * when the backend omits the link_type field. It mirrors the backend's
 * detection logic in display_event_links.py.
 *
 * @param {string} href - Link destination
 * @returns {string} Detected link type constant
 * @private
 */
function _detectLinkTypeFromHref(href) {
  if (!href || href === '#') {
    return LINK_TYPE_PLACEHOLDER;
  }

  // External URLs (http, https, www)
  if (href.startsWith('http://') || href.startsWith('https://') || href.startsWith('www.')) {
    return LINK_TYPE_EXTERNAL;
  }

  // Anchor links (#section)
  if (href.startsWith('#') && href !== '#') {
    return LINK_TYPE_ANCHOR;
  }

  // Internal delta links ($zBlock)
  if (href.startsWith('$') || href.includes('$')) {
    return LINK_TYPE_INTERNAL_DELTA;
  }

  // Internal zPath links (@.UI.zUI.zBlock)
  if (href.startsWith('@')) {
    return LINK_TYPE_INTERNAL_ZPATH;
  }

  // Default: treat web routes (/path) as internal delta
  if (href.startsWith('/')) {
    return LINK_TYPE_INTERNAL_DELTA;
  }

  // Fallback: placeholder
  return LINK_TYPE_PLACEHOLDER;
}

// ─────────────────────────────────────────────────────────────────
// Main Link Renderer
// ─────────────────────────────────────────────────────────────────

/**
 * Render a semantic link with mode-aware behavior and target support.
 *
 * Handles internal navigation (client-side routing), external links
 * (native browser), anchor links (smooth scroll), and placeholder links
 * (styled text only).
 *
 * Security: Auto-adds rel="noopener noreferrer" for external _blank links.
 *
 * @param {Object} linkData - Link configuration from backend
 * @param {string} linkData.label - Link text to display
 * @param {string} linkData.href - Link destination
 * @param {string} linkData.target - Target behavior (_self, _blank, etc.)
 * @param {string} linkData.link_type - Detected link type (delta, external, etc.)
 * @param {string} [linkData.rel] - Link relationship (security)
 * @param {string} [linkData._zClass] - CSS classes for styling
 * @param {string} [linkData.color] - Color theme
 * @param {Object} [linkData.window] - Window.open() features
 * @param {HTMLElement} container - DOM element to append link to
 * @param {Object} client - BifrostClient instance for navigation
 *
 * @example
 * // Internal navigation
 * renderLink({
 *   label: 'About',
 *   href: '$zAbout',
 *   target: '_self',
 *   link_type: 'delta'
 * }, containerDiv, bifrostClient);
 *
 * @example
 * // External link with new tab
 * renderLink({
 *   label: 'Documentation',
 *   href: 'https://docs.example.com',
 *   target: '_blank',
 *   link_type: 'external',
 *   _zClass: 'zBtn zBtn-primary'
 * }, containerDiv, bifrostClient);
 *
 * @example
 * // Anchor link (smooth scroll)
 * renderLink({
 *   label: 'Features',
 *   href: '#features',
 *   target: '_self',
 *   link_type: 'anchor'
 * }, containerDiv, bifrostClient);
 */
export function renderLink(linkData, container, client) {
  const {
    label,
    href,
    target = TARGET_SELF,
    link_type,
    rel = '',
    _zClass = '',
    color = '',
    window: windowFeatures = {}
  } = linkData;

  // 🔧 FIX: Detect link type if missing (fallback for backend omissions)
  let detectedLinkType = link_type;
  if (!detectedLinkType || detectedLinkType === 'undefined') {
    console.warn('[LinkPrimitives] ⚠️  link_type missing, detecting from href:', href);
    detectedLinkType = _detectLinkTypeFromHref(href);
    console.log('[LinkPrimitives] ✅ Detected link type:', detectedLinkType, 'for href:', href);
  }

  // Debug: Log incoming link data with detected type
  console.log('[LinkPrimitives] 🎨 renderLink called:', {
    label,
    href,
    link_type: link_type,
    detectedLinkType: detectedLinkType,
    target,
    _zClass,  // ✅ Show _zClass for debugging
    color,    // ✅ Show color for debugging
    hasClient: !!client,
    hasContainer: !!container
  });

  // Create semantic <a> element
  const link = createElement('a');
  link.textContent = label;

  // ✅ TERMINAL-FIRST PATTERN: color is the source of truth
  // Smart class inference based on context:
  // - If _zClass has 'zBtn' → add zBtn-{color}
  // - If plain link (no zBtn) → add zText-{color}
  // - Group styling handled by orchestrator

  // Apply custom _zClass if provided (from YAML)
  let hasButtonClass = false;
  if (_zClass) {
    const classes = _zClass.split(' ').filter(c => c.trim());
    if (classes.length > 0) {
      link.classList.add(...classes);
      hasButtonClass = classes.some(c => c === 'zBtn' || c.startsWith('zBtn-'));
      console.log('[LinkPrimitives] ✅ Applied _zClass:', classes, { hasButtonClass });
    }
  } else {
    console.log('[LinkPrimitives] ⚠️  No _zClass provided');
  }

  // 🎨 DRY MAGIC: Auto-infer color class based on context (Terminal-first)
  if (color) {
    const colorLower = color.toLowerCase();

    if (hasButtonClass) {
      // Button context: add zBtn-{color} if not already present
      const colorClass = `zBtn-${colorLower}`;
      if (!link.classList.contains(colorClass)) {
        link.classList.add(colorClass);
        console.log('[LinkPrimitives] 🎨 Auto-added button color:', colorClass);
      }
    } else {
      // Plain link context: add zText-{color} for text coloring
      const colorClass = `zText-${colorLower}`;
      link.classList.add(colorClass);
      console.log('[LinkPrimitives] 🎨 Auto-added text color:', colorClass);
    }
  }

  // Debug: Show final classes applied
  console.log('[LinkPrimitives] 🎨 Final classList:', Array.from(link.classList));

  // Handle different link types using DETECTED type (fallback-safe)
  switch (detectedLinkType) {
    case LINK_TYPE_INTERNAL_DELTA:
    case LINK_TYPE_INTERNAL_ZPATH:
    case 'internal_delta':  // Backend sends with underscore prefix
    case 'internal_zpath':  // Backend sends with underscore prefix
      _setupInternalLink(link, href, target, windowFeatures, client);
      break;

    case LINK_TYPE_EXTERNAL:
      _setupExternalLink(link, href, target, rel, windowFeatures);
      break;

    case LINK_TYPE_ANCHOR:
      _setupAnchorLink(link, href);
      break;

    case LINK_TYPE_PLACEHOLDER:
      _setupPlaceholderLink(link);
      break;

    default:
      console.warn('[LinkPrimitives] Unknown link type after detection:', detectedLinkType);
      _setupPlaceholderLink(link);
  }

  // Append to container if provided (legacy), otherwise return element
  if (container) {
    container.appendChild(link);
  }
  return link;  // ✅ Return link element for direct use
}

// ─────────────────────────────────────────────────────────────────
// zPath to URL Conversion
// ─────────────────────────────────────────────────────────────────

/**
 * Convert zPath to URL path for client-side routing.
 * 
 * Example conversions:
 * - @.UI.zProducts.zTheme.zUI.zGrid.zGrid_Details → /zProducts/zTheme/zGrid
 * - @.UI.zAbout.zAbout_Details → /zAbout
 * - $zBlock → $zBlock (delta links pass through)
 * - /regular/path → /regular/path (web paths pass through)
 * 
 * @private
 * @param {string} href - zPath or regular path
 * @returns {string} URL path for navigation
 */
function _convertZPathToURL(href) {
  // Pass through delta links ($) and web paths (/)
  if (!href.startsWith('@')) {
    return href;
  }
  
  // Parse zPath: @.UI.zProducts.zTheme.zUI.zGrid.zGrid_Details
  // 1. Remove @.UI. prefix
  // 2. Split remaining path by dots
  // 3. Remove zUI (file prefix marker)
  // 4. Remove final block name (ends with _Details or _Section)
  // 5. Convert to /path/format
  
  let path = href.replace(/^@\.UI\./, ''); // Remove @.UI.
  const parts = path.split('.');
  
  // Filter out zUI markers and block names (typically last segment with _)
  const pathParts = parts.filter((part, index) => {
    // Keep non-zUI parts
    if (part === 'zUI') return false;
    // Remove last segment if it looks like a block name (has underscore or ends in Details/Section)
    if (index === parts.length - 1 && (part.includes('_') || part.endsWith('Details') || part.endsWith('Section'))) {
      return false;
    }
    return true;
  });
  
  // Convert to /path format
  return '/' + pathParts.join('/');
}

// ─────────────────────────────────────────────────────────────────
// Internal Link Setup (Client-Side Routing)
// ─────────────────────────────────────────────────────────────────

/**
 * Setup internal link for client-side routing.
 *
 * Prevents default browser navigation and uses BifrostClient.navigate()
 * for SPA-style routing. Supports opening in new tab via window.open().
 *
 * @private
 * @param {HTMLAnchorElement} link - Link element to configure
 * @param {string} href - Internal path (delta or zPath)
 * @param {string} target - Target behavior
 * @param {Object} windowFeatures - Custom window features
 * @param {Object} client - BifrostClient instance
 */
function _setupInternalLink(link, href, target, windowFeatures, client) {
  link.href = '#'; // Prevent default navigation

  // Convert zPath to URL path if needed
  const navigationPath = _convertZPathToURL(href);

  // Debug: Verify click handler setup
  console.log('[LinkPrimitives] 🔗 Setting up internal link:', { 
    original: href, 
    converted: navigationPath,
    target, 
    hasClient: !!client 
  });

  link.addEventListener('click', (e) => {
    e.preventDefault();
    console.log('[LinkPrimitives] 👆 Link clicked:', navigationPath);

    if (target === TARGET_BLANK) {
      // Open in new tab/window using window.open()
      const newWindow = _openInNewWindow(navigationPath, windowFeatures, client);
      if (newWindow) {
        console.log(`[LinkPrimitives] Opened ${navigationPath} in new tab`);
      }
    } else {
      // Navigate in current tab via client-side routing
      // FIX: Use _navigateToRoute() instead of navigate() (actual method name)
      if (client && typeof client._navigateToRoute === 'function') {
        console.log('[LinkPrimitives] ✅ Navigating to:', navigationPath);
        client._navigateToRoute(navigationPath);
      } else {
        console.error('[LinkPrimitives] ❌ BifrostClient._navigateToRoute() not available:', {
          hasClient: !!client,
          clientKeys: client ? Object.keys(client).filter(k => k.includes('nav')) : []
        });
      }
    }
  });
}

// ─────────────────────────────────────────────────────────────────
// External Link Setup (Native Browser Navigation)
// ─────────────────────────────────────────────────────────────────

/**
 * Setup external link with proper security and target attributes.
 *
 * Auto-adds rel="noopener noreferrer" for _blank to prevent window.opener
 * exploitation (Tabnabbing attack).
 *
 * @private
 * @param {HTMLAnchorElement} link - Link element to configure
 * @param {string} href - External URL
 * @param {string} target - Target behavior
 * @param {string} rel - Link relationship
 * @param {Object} windowFeatures - Custom window features
 */
function _setupExternalLink(link, href, target, rel, windowFeatures) {
  link.href = href;
  link.target = target;

  // Debug: Verify external link setup
  console.log('[LinkPrimitives] 🌐 Setting up external link:', { href, target, rel, hasWindowFeatures: Object.keys(windowFeatures).length > 0 });

  // Security: Auto-add rel="noopener noreferrer" for _blank
  if (target === TARGET_BLANK && !rel) {
    link.rel = 'noopener noreferrer';
  } else if (rel) {
    link.rel = rel;
  }

  // Custom window features (if specified)
  if (target === TARGET_BLANK && Object.keys(windowFeatures).length > 0) {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      console.log('[LinkPrimitives] 👆 External link clicked (custom window):', href);
      _openInNewWindow(href, windowFeatures, null);
    });
  } else {
    // Add click log for standard external links too
    link.addEventListener('click', (_e) => {
      console.log('[LinkPrimitives] 👆 External link clicked (native):', href);
      // No preventDefault - let browser handle normally
    });
  }
}

// ─────────────────────────────────────────────────────────────────
// Anchor Link Setup (Smooth Scroll)
// ─────────────────────────────────────────────────────────────────

/**
 * Setup anchor link for smooth scrolling to target element.
 *
 * Uses scrollIntoView with smooth behavior for better UX.
 * Warns if target element not found.
 *
 * @private
 * @param {HTMLAnchorElement} link - Link element to configure
 * @param {string} href - Anchor hash (e.g., "#features")
 */
function _setupAnchorLink(link, href) {
  link.href = href;
  link.addEventListener('click', (e) => {
    e.preventDefault();
    const targetElement = document.querySelector(href);
    if (targetElement) {
      targetElement.scrollIntoView({ behavior: 'smooth' });
    } else {
      console.warn(`[LinkPrimitives] Anchor target not found: ${href}`);
    }
  });
}

// ─────────────────────────────────────────────────────────────────
// Placeholder Link Setup (No Navigation)
// ─────────────────────────────────────────────────────────────────

/**
 * Setup placeholder link (no navigation action).
 *
 * Used for design/mock purposes or "coming soon" links.
 * Prevents default click behavior.
 *
 * @private
 * @param {HTMLAnchorElement} link - Link element to configure
 */
function _setupPlaceholderLink(link) {
  link.href = '#';

  // Debug: Verify placeholder link setup
  console.log('[LinkPrimitives] 📍 Setting up placeholder link:', link.textContent);

  link.addEventListener('click', (e) => {
    e.preventDefault();
    console.log('[LinkPrimitives] 👆 Placeholder link clicked (no action):', link.textContent);
    // No action - just styled text
  });
}

// ─────────────────────────────────────────────────────────────────
// Window.open() Helper
// ─────────────────────────────────────────────────────────────────

/**
 * Open URL in new window with custom features.
 *
 * Centers the window on screen and applies custom width, height, and
 * window features (menubar, toolbar, etc.).
 *
 * @private
 * @param {string} url - URL to open
 * @param {Object} features - Window features
 * @param {number} [features.width=800] - Window width
 * @param {number} [features.height=600] - Window height
 * @param {string} [features.features] - Custom window.open() features string
 * @param {Object} client - BifrostClient (for internal URLs)
 * @returns {Window|null} New window reference or null if blocked
 */
function _openInNewWindow(url, features = {}, client = null) {
  const { width = 800, height = 600, features: customFeatures = '' } = features;

  // Calculate center position
  const left = (screen.width - width) / 2;
  const top = (screen.height - height) / 2;

  // Build features string
  const featuresStr = customFeatures ||
    `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`;

  // For internal URLs with client, construct full URL
  let fullUrl = url;
  if (client && (url.startsWith('$') || url.startsWith('@'))) {
    // Convert zPath to URL path first
    const navigationPath = _convertZPathToURL(url);
    // Then construct full URL (same origin)
    fullUrl = `${window.location.origin}${navigationPath}`;
    console.log('[LinkPrimitives] 🪟 Opening internal link in new window:', { 
      original: url, 
      converted: navigationPath,
      fullUrl 
    });
  }

  // Open new window
  const newWindow = window.open(fullUrl, '_blank', featuresStr);

  if (newWindow) {
    newWindow.focus();
    return newWindow;
  } else {
    console.error('[LinkPrimitives] Popup blocked or failed to open');
    return null;
  }
}

export default { renderLink };

