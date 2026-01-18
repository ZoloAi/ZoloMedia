/**
 * Menu Integration for Bifrost Client
 *
 * This module registers the onMenu hook with the BifrostClient to enable
 * menu rendering and interaction in Bifrost mode.
 *
 * Usage:
 *   <script type="module" src="/bifrost/src/menu_integration.js"></script>
 *
 * Or dynamically:
 *   import { registerMenuHook } from './menu_integration.js';
 *   registerMenuHook(bifrostClient);
 */

import { MenuRenderer } from './rendering/menu_renderer.js';

/**
 * Register the onMenu hook with a BifrostClient instance
 * @param {BifrostClient} client - The Bifrost client instance
 */
export function registerMenuHook(client) {
  console.log('[MenuIntegration] Registering onMenu hook');

  // Create menu renderer
  const menuRenderer = new MenuRenderer(client);

  // Register the onMenu hook
  client.registerHook('onMenu', (message) => {
    console.log('[MenuIntegration] onMenu hook called with message:', message);
    menuRenderer.renderMenu(message);
  });

  console.log('[MenuIntegration] ✅ onMenu hook registered successfully');
}

/**
 * Auto-register if BifrostClient is already initialized
 * This allows the script to be loaded after the client is created
 */
if (typeof window !== 'undefined' && window.bifrostClient) {
  console.log('[MenuIntegration] Auto-registering with existing BifrostClient');
  registerMenuHook(window.bifrostClient);
}

