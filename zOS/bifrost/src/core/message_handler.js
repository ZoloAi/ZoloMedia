/**
 * ═══════════════════════════════════════════════════════════════
 * Message Handler Module - Message Processing & Correlation
 * ═══════════════════════════════════════════════════════════════
 */

export class MessageHandler {
  constructor(logger, hooks, client = null) {
    this.logger = logger;
    this.hooks = hooks;
    this.client = client; // Store reference to BifrostClient for client-side navigation

    // Pass logger to hooks for better error handling
    if (this.hooks && typeof this.hooks.logger === 'undefined') {
      this.hooks.logger = logger;
    }

    this.requestId = 0;
    this.callbacks = new Map();
    this.timeout = 30000; // Default timeout
  }

  /**
   * Set timeout for requests
   */
  setTimeout(timeout) {
    this.timeout = timeout;
  }

  /**
   * Extract session ID from HTTP cookie for session sync
   * @private
   * @returns {string|null} Session ID or null if not found
   */
  _getSessionIdFromCookie() {
    // Parse all cookies
    const cookies = document.cookie.split(';');

    // Look for 'session' cookie (Flask default) or 'sessionid' (Django)
    for (const cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === 'session' || name === 'sessionid') {
        this.logger.log(`[MessageHandler] 🔐 Found session cookie: ${name}=${value.substring(0, 10)}...`);
        return value;
      }
    }

    this.logger.log('[MessageHandler] ⚠️  No session cookie found (user not logged in)');
    return null;
  }

  /**
   * Validate outgoing message follows protocol
   * @private
   */
  _validateOutgoingMessage(payload) {
    // Warn if using deprecated 'action' field
    if (payload.action && !payload.event) {
      this.logger.warn(
        'Using deprecated "action" field. Please use "event" instead.',
        { action: payload.action }
      );
      // Auto-migrate: copy action to event
      payload.event = payload.action;
    }

    // Warn if message has both 'action' and 'event'
    if (payload.action && payload.event && payload.action !== payload.event) {
      this.logger.warn(
        'Message has both "action" and "event" fields with different values. Using "event".',
        { action: payload.action, event: payload.event }
      );
      delete payload.action;
    }
  }

  /**
   * Handle incoming message
   */
  handleMessage(data) {
    try {
      const message = JSON.parse(data);
      this.logger.log('📨 [MessageHandler] Received message:', message);
      this.logger.log('📨 [MessageHandler] Message keys:', Object.keys(message));
      this.logger.log('📨 [MessageHandler] display_event:', message.display_event);
      this.logger.log('📨 [MessageHandler] event:', message.event);

      this.logger.log('📨 Received message', message);

      // Call general message hook (with error boundary)
      try {
        this.hooks.call('onMessage', message);
      } catch (hookError) {
        this.logger.error('[MessageHandler] Error in onMessage hook:', hookError);
        // Continue processing - don't let hook errors break message handling
      }

      // Progressive chunk rendering (zWizard chunked execution for Bifrost)
      // MUST be checked BEFORE response correlation (chunks have _requestId but are NOT responses)
      if (message.event === 'render_chunk') {
        this.logger.log('📦 [MessageHandler] ✅ CHUNK EVENT DETECTED - calling onRenderChunk hook');
        this.logger.log('📦 [MessageHandler] Chunk message:', message);
        try {
          this.hooks.call('onRenderChunk', message);
        } catch (hookError) {
          this.logger.error('[MessageHandler] Error rendering chunk:', hookError);
          this.hooks.call('onError', { type: 'chunk_render_error', error: hookError, message });
        }
        return;
      }

      // Connection info event (session data from backend) - v1.6.0
      if (message.event === 'connection_info') {
        this.logger.log('🔗 [MessageHandler] ✅ CONNECTION_INFO DETECTED - calling onConnectionInfo hook');
        this.hooks.call('onConnectionInfo', message.data);
        // Also trigger onConnected for backward compatibility
        this.hooks.call('onConnected', message.data);
        return;
      }

      // Navigate back event (^ bounce-back after block completion)
      if (message.event === 'navigate_back') {
        this.logger.log('↩️ [MessageHandler] ✅ NAVIGATE_BACK EVENT - triggering browser back');
        this.logger.log('↩️ [MessageHandler] Reason:', message.reason);

        // For bounce-back completions (e.g., after login/logout), always navigate to home via client-side nav
        // This avoids double-back issues and ensures correct block loading
        if (message.reason === 'bounce_back_block_completed') {
          this.logger.log('↩️ [MessageHandler] Bounce-back - navigating to home via client-side nav');
          if (this.client && typeof this.client._navigateToRoute === 'function') {
            // Navigate to home
            this.client._navigateToRoute('/').then(() => {
              // Refresh NavBar after navigation (for RBAC updates after login/logout)
              if (typeof this.client._fetchAndPopulateNavBar === 'function') {
                this.logger.log('↩️ [MessageHandler] ✅ Refreshing NavBar after bounce-back');
                this.client._fetchAndPopulateNavBar().catch(err => {
                  this.logger.error('↩️ [MessageHandler] Failed to refresh NavBar:', err);
                });
              }
            }).catch(err => {
              this.logger.error('↩️ [MessageHandler] Navigation failed:', err);
            });
          } else {
            // Fallback: use window.location (will cause reload)
            window.location.href = '/';
          }
          return;
        }

        // For RBAC denials, use history.back() if we have app history
        if (message.reason === 'rbac_denied') {
          const hasAppHistory = window.history.length > 2 ||
                                (window.history.length > 1 && document.referrer.includes(window.location.hostname));

          if (hasAppHistory) {
            this.logger.log('↩️ [MessageHandler] RBAC denied - using history.back()');
            window.history.back();
          } else {
            this.logger.log('↩️ [MessageHandler] RBAC denied, no history - navigating to home');
            if (this.client && typeof this.client._navigateToRoute === 'function') {
              this.client._navigateToRoute('/');
            } else {
              window.location.href = '/';
            }
          }
          return;
        }

        // Default: attempt history.back() for other navigate_back reasons
        this.logger.log('↩️ [MessageHandler] Other reason - using history.back()');
        window.history.back();
        return;
      }

      // Dashboard event (zDash display event for sidebar navigation)
      if (message.event === 'zDash') {
        this.logger.log('📊 [MessageHandler] ✅ ZDASH EVENT DETECTED - calling onZDash hook');
        this.logger.log('📊 [MessageHandler] Dashboard config:', message);
        this.hooks.call('onZDash', message);
        return;
      }

      // Menu event (menu navigation in Bifrost mode)
      // Note: Backend sends 'zMenu' not 'menu' (matches zDash, zDialog pattern)
      if (message.event === 'zMenu') {
        this.logger.log('📋 [MessageHandler] ✅ zMENU EVENT DETECTED - calling onMenu hook');
        this.logger.log('📋 [MessageHandler] Menu config:', message);
        this.hooks.call('onMenu', message);
        return;
      }

      // RBAC denial event (access denied)
      if (message.event === 'rbac_denied') {
        this.logger.log('🚫 [MessageHandler] ✅ RBAC ACCESS DENIED');
        this.logger.log('🚫 RBAC Access Denied:', message.message);

        // Display the denial message
        if (message.message) {
          // Create a styled error display using zTheme classes
          const errorDiv = document.createElement('div');
          errorDiv.className = 'zAlert zAlert-danger zmt-4 zp-4';
          errorDiv.innerHTML = `
            <h3 class="zAlert-heading zmb-2">🚫 Access Denied</h3>
            <div class="zAlert-body">${message.message.replace(/\n/g, '<br>')}</div>
            <hr class="zmy-3">
            <p class="zmb-0 zText-muted"><small>You will be redirected back in a moment...</small></p>
          `;

          // Clear content area and show error
          const contentArea = document.getElementById('zVaF-content');
          if (contentArea) {
            contentArea.innerHTML = '';  // Clear blank content
            contentArea.appendChild(errorDiv);
          }
        }

        return;
      }

      // Check if this is a response to a request
      const requestId = message._requestId;
      if (requestId !== undefined && this.callbacks.has(requestId)) {
        this._handleResponse(requestId, message);
        return;
      }

      // If message looks like a response but has no _requestId, log error
      if ((message.result !== undefined || message.error !== undefined) && this.callbacks.size > 0) {
        this.logger.error(
          'Received response without _requestId! Backend must echo _requestId in all responses.',
          { message, pendingRequests: this.callbacks.size }
        );
        // Don't try to correlate - this is a backend bug that must be fixed
      }

      // Check for specific event types
      if (message.event === 'input_response') {
        return; // Handled internally by zDisplay
      }

      // Handle execute_code_response for zTerminal
      if (message.event === 'execute_code_response') {
        this.logger.log('[MessageHandler] 🖥️ execute_code_response received:', message.requestId);
        // Route to TerminalRenderer's static handler
        const TerminalRenderer = window._TerminalRenderer;
        if (TerminalRenderer && TerminalRenderer.handleExecutionResponse) {
          TerminalRenderer.handleExecutionResponse(message.requestId, message);
        } else if (window._zTerminalResponses && window._zTerminalResponses[message.requestId]) {
          // Fallback to direct promise resolution
          window._zTerminalResponses[message.requestId](message);
          delete window._zTerminalResponses[message.requestId];
        }
        return;
      }

      // Handle request_input for zTerminal interactive input
      if (message.event === 'request_input') {
        this.logger.log('[MessageHandler] 🖥️ request_input received:', message.requestId, message.prompt, 'isPassword:', message.isPassword);
        // Route to TerminalRenderer's static handler
        const TerminalRenderer = window._TerminalRenderer;
        if (TerminalRenderer && TerminalRenderer.handleInputRequest) {
          TerminalRenderer.handleInputRequest(message.requestId, message.prompt, message.isPassword || false);
        }
        return;
      }

      // Check for display events (supports multiple formats)
      // - Old: {event: 'display', data: {...}}
      // - New: {display_event: 'success', data: {...}}
      // - Progress: {event: 'progress_bar', ...} → treated as display event
      if (message.event === 'display' || message.type === 'display' || message.display_event) {
        this.logger.log('📨 [MessageHandler] ✅ DISPLAY EVENT DETECTED - calling onDisplay hook');
        this.logger.log('📨 [MessageHandler] display_event value:', message.display_event);
        try {
          this.hooks.call('onDisplay', message);  // Pass full message with display_event
        } catch (hookError) {
          this.logger.error('[MessageHandler] Error in display event handler:', hookError);
          this.hooks.call('onError', { type: 'display_error', error: hookError, message });
        }
        return;
      }

      // Progress bar events - also route to display renderer
      if (message.event === 'progress_bar' || message.event === 'progress_complete') {
        // Convert to display_event format for renderer
        message.display_event = 'progress_bar';
        this.hooks.call('onDisplay', message);
        this.hooks.call('onProgressBar', message);  // Also call specific hook for backwards compat
        return;
      }

      if (message.event === 'input_request' || message.type === 'input_request') {
        this.hooks.call('onInput', message);
        return;
      }

      if (message.event === 'progress_update') {
        this.hooks.call('onProgressUpdate', message);
        return;
      }

      if (message.event === 'progress_complete') {
        this.hooks.call('onProgressComplete', message);
        return;
      }

      // Spinner events
      if (message.event === 'spinner_start') {
        this.hooks.call('onSpinnerStart', message);
        return;
      }

      if (message.event === 'spinner_stop') {
        this.hooks.call('onSpinnerStop', message);
        return;
      }

      if (message.event === 'swiper_init') {
        this.hooks.call('onSwiperInit', message);
        return;
      }

      // Otherwise, treat as broadcast
      this._handleBroadcast(message);

    } catch (error) {
      this.logger.error('❌❌❌ [MessageHandler] CRITICAL ERROR:', error);
      this.logger.error('❌❌❌ [MessageHandler] Error stack:', error.stack);
      this.logger.error('❌❌❌ [MessageHandler] Raw data:', data);
      this.logger.log('❌ Failed to parse message', { data, error });
      this.hooks.call('onError', error);
    }
  }

  /**
   * Send a message and wait for response
   */
  async send(payload, sendFn, timeout = null) {
    try {
      // Validate message follows protocol
      this._validateOutgoingMessage(payload);

      // Attach session ID from HTTP cookie for session sync (WebSocket/HTTP bridge)
      // Only attach for walker execution requests, not for form submissions
      // (forms don't need session sync until AFTER successful login)
      const sessionId = this._getSessionIdFromCookie();
      if (sessionId && payload.event === 'execute_walker') {
        payload._sessionId = sessionId;
        this.logger.log('[MessageHandler] 🔐 Attached session ID to walker execution');
      }

      const requestId = this.requestId++;
      payload._requestId = requestId;

      const timeoutMs = timeout || this.timeout;

      return new Promise((resolve, reject) => {
        const callback = { resolve, reject };

        // Set timeout
        callback.timeoutId = setTimeout(() => {
          if (this.callbacks.has(requestId)) {
            this.callbacks.delete(requestId);
            reject(new Error(`Request timeout after ${timeoutMs}ms`));
          }
        }, timeoutMs);

        this.callbacks.set(requestId, callback);

        try {
          // Send message
          const message = JSON.stringify(payload);
          this.logger.log('📤 Sending message', payload);
          sendFn(message);
        } catch (sendError) {
          // Clean up callback on send failure
          this.callbacks.delete(requestId);
          if (callback.timeoutId) {
            clearTimeout(callback.timeoutId);
          }
          reject(new Error(`Failed to send message: ${sendError.message}`));
        }
      });
    } catch (error) {
      this.logger.error('[MessageHandler] Error in send():', error);
      throw error; // Propagate to caller
    }
  }

  /**
   * Handle response to a request
   * @private
   */
  _handleResponse(requestId, message) {
    try {
      const callback = this.callbacks.get(requestId);
      if (!callback) {
        return;
      }

      this.callbacks.delete(requestId);

      // Clear timeout
      if (callback.timeoutId) {
        clearTimeout(callback.timeoutId);
      }

      // Resolve or reject
      if (message.error) {
        callback.reject(new Error(message.error));
      } else {
        // Return entire message (minus _requestId) for flexibility
        // Some responses use 'result' field, others use 'success', 'data', etc.
        const { _requestId, ...response } = message;
        callback.resolve(response.result !== undefined ? response.result : response);
      }
    } catch (error) {
      this.logger.error('[MessageHandler] Error handling response:', error);
      // Attempt to reject the callback if it still exists
      const callback = this.callbacks.get(requestId);
      if (callback) {
        this.callbacks.delete(requestId);
        if (callback.timeoutId) {
          clearTimeout(callback.timeoutId);
        }
        callback.reject(new Error(`Response handling error: ${error.message}`));
      }
    }
  }

  /**
   * Handle broadcast message
   * @private
   */
  _handleBroadcast(message) {
    try {
      this.logger.log('📢 Broadcast received', message);
      this.hooks.call('onBroadcast', message);
    } catch (error) {
      this.logger.error('[MessageHandler] Error handling broadcast:', error);
      this.hooks.call('onError', { type: 'broadcast_error', error, message });
    }
  }

  /**
   * Send input response to server
   */
  sendInputResponse(requestId, value, sendFn) {
    const response = {
      event: 'input_response',
      requestId: requestId,
      value: value
    };

    sendFn(JSON.stringify(response));
    this.logger.log('📤 Sent input response', response);
  }
}

