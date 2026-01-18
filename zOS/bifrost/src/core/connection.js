/**
 * ═══════════════════════════════════════════════════════════════
 * Connection Module - WebSocket Connection Management
 * ═══════════════════════════════════════════════════════════════
 */

export class BifrostConnection {
  constructor(url, options, logger, hooks) {
    this.url = url;
    this.options = options;
    this.logger = logger;
    this.hooks = hooks;

    this.ws = null;
    this.connected = false;
    this.reconnectAttempt = 0;
  }

  /**
   * Connect to WebSocket server
   */
  async connect() {
    return new Promise((resolve, reject) => {
      this.logger.log('Attempting to connect...', this.url);
      this.hooks.call('onConnecting', this.url);

      const connectUrl = this.options.token
        ? `${this.url}?token=${this.options.token}`
        : this.url;

      try {
        this.ws = new WebSocket(connectUrl);

        this.ws.onopen = () => {
          this.connected = true;
          this.reconnectAttempt = 0;
          this.logger.log('✅ Connected to server');

          const info = {
            url: this.ws.url,
            protocol: this.ws.protocol,
            readyState: this.ws.readyState
          };

          this.hooks.call('onConnected', info);
          resolve();
        };

        this.ws.onerror = (error) => {
          this.logger.log('❌ WebSocket error', error);
          this.hooks.call('onError', error);
          if (!this.connected) {
            reject(error);
          }
        };

        this.ws.onclose = (event) => {
          this.connected = false;
          this.logger.log('⚠️ Disconnected', {
            code: event.code,
            reason: event.reason,
            wasClean: event.wasClean
          });

          const reason = {
            code: event.code,
            reason: event.reason,
            wasClean: event.wasClean
          };

          this.hooks.call('onDisconnected', reason);

          // Auto-reconnect if enabled
          if (this.options.autoReconnect && event.code !== 1000) {
            this._scheduleReconnect();
          }
        };

      } catch (error) {
        this.logger.log('💥 Connection failed', error);
        this.hooks.call('onError', error);
        reject(error);
      }
    });
  }

  /**
   * Disconnect from server
   */
  disconnect() {
    if (this.ws) {
      this.options.autoReconnect = false;
      this.connected = false;
      this.ws.close(1000, 'Client disconnect');
      this.logger.log('🔌 Disconnected by client');
    }
  }

  /**
   * Check if connected
   */
  isConnected() {
    return this.connected && this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Send raw message
   */
  send(message) {
    if (this.ws && this.isConnected()) {
      this.ws.send(message);
    } else {
      throw new Error('WebSocket not connected');
    }
  }

  /**
   * Set message handler
   */
  onMessage(handler) {
    if (this.ws) {
      this.ws.onmessage = handler;
    }
  }

  /**
   * Schedule reconnection
   * @private
   */
  _scheduleReconnect() {
    this.reconnectAttempt++;
    const delay = this.options.reconnectDelay;

    this.logger.log(`🔄 Reconnecting in ${delay}ms (attempt ${this.reconnectAttempt})...`);

    setTimeout(() => {
      this.logger.log('🔄 Reconnecting...');
      this.connect().catch(err => {
        this.logger.log('❌ Reconnect failed', err);
      });
    }, delay);
  }
}

