/**
 * ═══════════════════════════════════════════════════════════════
 * Terminal Renderer - zTerminal Code Execution Sandbox
 * ═══════════════════════════════════════════════════════════════
 *
 * Renders zTerminal events as code blocks with optional execution.
 * Displays code with syntax highlighting and a Run button for
 * sandboxed execution.
 *
 * @module rendering/terminal_renderer
 * @layer 3
 * @pattern Strategy (single event type)
 *
 * Dependencies:
 * - Layer 0: primitives/interactive_primitives.js (createButton)
 * - Prism.js: Syntax highlighting (already loaded by BifrostClient)
 * - zTheme: Card and button component classes
 *
 * Exports:
 * - TerminalRenderer: Class for rendering terminal events
 *
 * Example:
 * ```javascript
 * import TerminalRenderer from './terminal_renderer.js';
 *
 * const renderer = new TerminalRenderer(logger, client);
 * renderer.render({
 *   title: 'Python Demo',
 *   content: '```python\nprint("Hello!")\n```'
 * });
 * ```
 */

// ─────────────────────────────────────────────────────────────────
// Imports
// ─────────────────────────────────────────────────────────────────
import { createButton } from './primitives/interactive_primitives.js';

// ─────────────────────────────────────────────────────────────────
// Main Implementation
// ─────────────────────────────────────────────────────────────────

/**
 * Renders zTerminal code execution sandbox for zDisplay
 *
 * Handles the 'zTerminal' event type from zCLI backend, creating
 * code blocks with syntax highlighting and interactive Run button.
 *
 * @class
 */
export default class TerminalRenderer {
  /**
   * Create a terminal renderer
   * @param {Object} logger - Logger instance for debugging
   * @param {Object} client - BifrostClient instance for sending responses
   */
  constructor(logger, client = null) {
    if (!logger) {
      throw new Error('[TerminalRenderer] logger is required');
    }

    this.logger = logger;
    this.client = client;
  }

  /**
   * Render a zTerminal code block
   *
   * @param {Object} data - Terminal configuration
   * @param {string} data.title - Title for the terminal block
   * @param {string} data.content - Code content with code fences (```language ... ```)
   * @param {string} [data._zClass] - Optional custom classes
   * @returns {HTMLElement} Created terminal container
   */
  render(data) {
    const title = data.title || 'Terminal';
    const rawContent = data.content || '';
    const customClass = data._zClass || '';
    const terminalId = data._id || `terminal_${Math.random().toString(36).substr(2, 9)}`;

    // Extract language and code from code fences (```language ... ```)
    const { language, code } = this._parseCodeFences(rawContent);


    // Create main container
    const container = document.createElement('div');
    container.className = `zTerminal-container zCard zMb-3 ${customClass}`.trim();
    container.id = terminalId;

    // Create header with title and Run button
    const header = this._createHeader(title, language, terminalId);
    container.appendChild(header);

    // Create code block with syntax highlighting (display extracted code)
    const codeBlock = this._createCodeBlock(code, language);
    container.appendChild(codeBlock);

    // Create output area (initially hidden)
    const outputArea = this._createOutputArea(terminalId);
    container.appendChild(outputArea);

    // Store raw content and title for execution (backend parses fences)
    container.dataset.content = rawContent;
    container.dataset.title = title;

    return container;
  }

  /**
   * Parse code fences to extract language and code
   * Handles nested code fences: if content has nested ```, closing will have 6+ backticks
   * Example: ```zolo\n  content: ```python\n    print("hi")``````
   * @private
   * @param {string} content - Raw content possibly with code fences
   * @returns {{language: string, code: string}} Extracted language and code
   */
  _parseCodeFences(content) {
    // Match opening fence and handle nested closings (3, 6, 9+ backticks)
    const fenceMatch = content.match(/^```(\w+)?\s*\n?([\s\S]*?)(`{3,})\s*$/);
    if (fenceMatch) {
      const language = (fenceMatch[1] || 'text').toLowerCase();
      let innerContent = fenceMatch[2];
      const closingBackticks = fenceMatch[3];
      
      // If closing has more than 3 backticks, there's nested content
      // Strip one level of fence (3 backticks) from display, keep for execution
      if (closingBackticks.length > 3) {
        // Nested fences - append remaining backticks to inner content
        const remainingBackticks = '`'.repeat(closingBackticks.length - 3);
        innerContent = innerContent.trimEnd() + remainingBackticks;
      }
      
      return {
        language: language,
        code: innerContent.trim()
      };
    }
    // No code fence - treat as plain text
    return {
      language: 'text',
      code: content
    };
  }

  /**
   * Create terminal header with title and Run button
   * @private
   */
  _createHeader(title, language, terminalId) {
    const header = document.createElement('div');
    header.style.cssText = `
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #1e1e2e;
      border-bottom: 1px solid #333;
      border-radius: 8px 8px 0 0;
      padding: 8px 12px;
      margin: 0;
    `;

    // Left side: title + badge
    const leftContainer = document.createElement('div');
    leftContainer.style.cssText = 'display: flex; align-items: center; gap: 10px; margin: 0;';

    // Title
    const titleEl = document.createElement('span');
    titleEl.style.cssText = 'color: #e0e0e0; font-weight: 500; font-size: 0.9rem; margin: 0;';
    titleEl.textContent = title;

    // Language badge
    const langBadge = document.createElement('span');
    langBadge.style.cssText = `
      background: rgba(59, 130, 246, 0.2);
      color: #60a5fa;
      border: 1px solid rgba(59, 130, 246, 0.3);
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 500;
      margin: 0;
    `;
    langBadge.textContent = language;

    leftContainer.appendChild(titleEl);
    leftContainer.appendChild(langBadge);

    // Right side: Run button
    const buttonContainer = document.createElement('div');
    buttonContainer.style.cssText = 'margin: 0;';
    
    if (language === 'python' || language === 'zolo') {
      const runButton = createButton('button', {});
      runButton.innerHTML = '<i class="bi bi-play-fill"></i> Run';
      runButton.style.cssText = `
        background: #22c55e;
        border: none;
        color: white;
        font-weight: 500;
        font-size: 0.8rem;
        padding: 5px 12px;
        border-radius: 4px;
        cursor: pointer;
        transition: background 0.2s;
      `;
      runButton.addEventListener('mouseenter', () => {
        runButton.style.background = '#16a34a';
      });
      runButton.addEventListener('mouseleave', () => {
        runButton.style.background = '#22c55e';
      });
      runButton.addEventListener('click', () => this._executeCode(terminalId));
      buttonContainer.appendChild(runButton);
    } else if (language === 'bash') {
      const blockedBadge = document.createElement('span');
      blockedBadge.style.cssText = `
        background: rgba(234, 179, 8, 0.2);
        color: #fbbf24;
        border: 1px solid rgba(234, 179, 8, 0.3);
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
      `;
      blockedBadge.innerHTML = '<i class="bi bi-shield-lock"></i> Sandbox';
      buttonContainer.appendChild(blockedBadge);
    }

    header.appendChild(leftContainer);
    header.appendChild(buttonContainer);

    return header;
  }

  /**
   * Create code block with syntax highlighting
   * @private
   */
  _createCodeBlock(content, language) {
    const codeWrapper = document.createElement('div');
    codeWrapper.className = 'zCard-body zP-0';
    codeWrapper.style.backgroundColor = 'var(--zs-dark, #1e1e2e)';

    const pre = document.createElement('pre');
    pre.className = 'zM-0 zP-3';
    pre.style.backgroundColor = 'transparent';
    pre.style.overflow = 'auto';
    pre.style.maxHeight = '300px';

    const code = document.createElement('code');
    
    // Map language to Prism.js language class
    const prismLang = this._mapToPrismLanguage(language);
    code.className = `language-${prismLang}`;
    code.textContent = content;

    pre.appendChild(code);
    codeWrapper.appendChild(pre);

    // Apply Prism syntax highlighting if available
    if (typeof Prism !== 'undefined') {
      try {
        Prism.highlightElement(code);
      } catch (e) {
        this.logger.warn('[TerminalRenderer] Prism highlighting failed:', e.message);
      }
    }

    return codeWrapper;
  }

  /**
   * Create output area for execution results
   * @private
   */
  _createOutputArea(terminalId) {
    const outputArea = document.createElement('div');
    outputArea.id = `${terminalId}_output`;
    outputArea.className = 'zTerminal-output zCard-footer zP-3';
    outputArea.style.display = 'none';
    outputArea.style.backgroundColor = 'var(--zs-dark, #0d0d14)';
    outputArea.style.borderTop = '1px solid var(--zs-border-color, #333)';
    outputArea.style.fontFamily = 'monospace';
    outputArea.style.whiteSpace = 'pre-wrap';
    outputArea.style.maxHeight = '200px';
    outputArea.style.overflow = 'auto';

    return outputArea;
  }

  /**
   * Map language to Prism.js language identifier
   * @private
   */
  _mapToPrismLanguage(language) {
    const langMap = {
      'python': 'python',
      'bash': 'bash',
      'zolo': 'yaml',  // zolo is YAML-like
      'javascript': 'javascript',
      'js': 'javascript',
      'typescript': 'typescript',
      'ts': 'typescript',
      'json': 'json',
      'yaml': 'yaml',
      'html': 'html',
      'css': 'css'
    };
    return langMap[language.toLowerCase()] || 'plaintext';
  }

  /**
   * Execute code via WebSocket and display output
   * @private
   */
  async _executeCode(terminalId) {
    const container = document.getElementById(terminalId);
    if (!container) {
      this.logger.error('[TerminalRenderer] Container not found:', terminalId);
      return;
    }

    const content = container.dataset.content;
    const outputArea = document.getElementById(`${terminalId}_output`);

    if (!outputArea) {
      this.logger.error('[TerminalRenderer] Output area not found');
      return;
    }

    // Show output area with loading state
    outputArea.style.display = 'block';
    outputArea.innerHTML = '<span class="zText-info"><i class="bi bi-hourglass-split"></i> Executing...</span>';

    // Send execute request via WebSocket
    if (!window.bifrostClient || !window.bifrostClient.connection) {
      outputArea.innerHTML = '<span class="zText-danger"><i class="bi bi-exclamation-triangle"></i> Not connected to server</span>';
      return;
    }

    try {
      const requestId = `zterminal_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      // Create a promise that will be resolved when we receive the response
      const responsePromise = new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('Execution timeout'));
        }, 30000); // 30 second timeout

        // Store resolver for this request
        if (!window._zTerminalResponses) {
          window._zTerminalResponses = {};
        }
        window._zTerminalResponses[requestId] = (response) => {
          clearTimeout(timeout);
          resolve(response);
        };
      });

      // Send execution request - language is extracted from code fences by backend
      // Include title for zolo swap file naming
      const title = container.dataset.title || 'Terminal';
      window.bifrostClient.connection.send(JSON.stringify({
        event: 'execute_code',
        requestId: requestId,
        content: content,
        title: title
      }));


      // Wait for response
      const response = await responsePromise;
      
      // Display output (strip ANSI codes for clean web display)
      if (response.success) {
        if (response.output) {
          outputArea.innerHTML = `<span class="zText-success"><i class="bi bi-check-circle"></i> Output:</span>\n<span class="zText-light">${this._cleanOutput(response.output)}</span>`;
        } else {
          outputArea.innerHTML = '<span class="zText-muted"><i class="bi bi-info-circle"></i> (no output)</span>';
        }
      } else {
        outputArea.innerHTML = `<span class="zText-danger"><i class="bi bi-x-circle"></i> Error:</span>\n<span class="zText-warning">${this._cleanOutput(response.error || 'Unknown error')}</span>`;
      }

    } catch (error) {
      this.logger.error('[TerminalRenderer] Execution failed:', error);
      outputArea.innerHTML = `<span class="zText-danger"><i class="bi bi-x-circle"></i> ${this._cleanOutput(error.message)}</span>`;
    }
  }

  /**
   * Handle execution response from backend
   * Called by message handler when execute_code_response is received
   * @static
   */
  static handleExecutionResponse(requestId, response) {
    if (window._zTerminalResponses && window._zTerminalResponses[requestId]) {
      window._zTerminalResponses[requestId](response);
      delete window._zTerminalResponses[requestId];
    }
  }

  /**
   * ANSI color code to CSS color mapping
   * Maps terminal ANSI codes to web colors (mirroring colors.py)
   * @private
   */
  _ansiColorMap = {
    // Standard bright colors (90-97 range)
    '91': '#ff6b6b',   // RED - bright red
    '92': '#52B788',   // GREEN - bright green (zSuccess)
    '93': '#FFB347',   // YELLOW - bright yellow (zWarning)
    '94': '#5CA9FF',   // BLUE - bright blue
    '95': '#c678dd',   // MAGENTA - bright magenta
    '96': '#56b6c2',   // CYAN - bright cyan
    '97': '#abb2bf',   // WHITE - bright white
    
    // 256-color mode (38;5;N)
    '38;5;75': '#5CA9FF',   // zInfo - light blue
    '38;5;78': '#52B788',   // zSuccess - green
    '38;5;98': '#9370DB',   // SECONDARY - medium purple
    '38;5;150': '#A2D46E',  // PRIMARY - light green (intention)
    '38;5;203': '#E63946',  // zError - red
    '38;5;215': '#FFB347',  // zWarning - orange/yellow
    
    // Reset
    '0': null,  // Reset to default
  };

  /**
   * Convert ANSI escape codes to HTML spans with CSS colors
   * Mimics terminal color experience in web GUI
   * @private
   */
  _ansiToHtml(text) {
    if (!text) return '';
    
    // First escape HTML to prevent XSS
    const escaped = this._escapeHtml(text);
    
    let result = '';
    let currentColor = null;
    let i = 0;
    
    // Match ANSI escape sequences: ESC[ followed by params and 'm'
    const ansiRegex = /\x1b\[([0-9;]+)m/g;
    let lastIndex = 0;
    let match;
    
    // We need to work with the original text for ANSI matching
    // but escape each segment individually
    const segments = [];
    let pos = 0;
    
    while ((match = ansiRegex.exec(text)) !== null) {
      // Add text before this ANSI code
      if (match.index > pos) {
        const segment = text.substring(pos, match.index);
        segments.push({ text: segment, color: currentColor });
      }
      
      // Parse the ANSI code
      const code = match[1];
      if (code === '0') {
        currentColor = null;  // Reset
      } else if (this._ansiColorMap[code]) {
        currentColor = this._ansiColorMap[code];
      } else {
        // Try to match partial codes (e.g., just the color number)
        const parts = code.split(';');
        const lastPart = parts[parts.length - 1];
        if (this._ansiColorMap[lastPart]) {
          currentColor = this._ansiColorMap[lastPart];
        }
      }
      
      pos = match.index + match[0].length;
    }
    
    // Add remaining text
    if (pos < text.length) {
      segments.push({ text: text.substring(pos), color: currentColor });
    }
    
    // Build HTML output
    for (const seg of segments) {
      const escapedText = this._escapeHtml(seg.text);
      if (seg.color) {
        result += `<span style="color: ${seg.color}">${escapedText}</span>`;
      } else {
        result += escapedText;
      }
    }
    
    return result;
  }

  /**
   * Escape HTML to prevent XSS
   * @private
   */
  _escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Clean and render output for web display
   * Converts ANSI codes to HTML colors
   * @private
   */
  _cleanOutput(text) {
    return this._ansiToHtml(text);
  }

  /**
   * Handle input request from backend
   * Shows an input field in the terminal output area
   * Called by message handler when request_input is received
   * @static
   * @param {string} requestId - The request ID for this input
   * @param {string} prompt - The prompt text to display
   * @param {boolean} isPassword - Whether this is a password/secret input (masked)
   */
  static handleInputRequest(requestId, prompt, isPassword = false) {
    // Find the output area for this terminal (based on requestId prefix)
    // requestId format: zterminal_timestamp_random
    const outputAreas = document.querySelectorAll('.zTerminal-output');
    
    // Find the visible/active output area
    let targetOutput = null;
    for (const area of outputAreas) {
      if (area.style.display !== 'none') {
        targetOutput = area;
        break;
      }
    }
    
    if (!targetOutput) {
      console.error('[TerminalRenderer] No active output area for input request');
      return;
    }
    
    // Create input UI
    const inputContainer = document.createElement('div');
    inputContainer.className = 'zTerminal-input-container';
    inputContainer.style.cssText = 'display: flex; align-items: center; gap: 8px; margin-top: 8px; padding: 8px; background: rgba(255,255,255,0.05); border-radius: 4px;';
    
    // Prompt label
    const promptLabel = document.createElement('span');
    promptLabel.className = 'zText-info';
    promptLabel.innerHTML = `<i class="bi bi-keyboard"></i> ${prompt || 'Input:'}`;
    
    // Input field (password-aware)
    const inputField = document.createElement('input');
    inputField.type = isPassword ? 'password' : 'text';
    inputField.className = 'zForm-control zForm-control-sm';
    inputField.style.cssText = 'flex: 1; background: #1e1e2e; border: 1px solid #444; color: #e0e0e0; padding: 4px 8px;';
    inputField.placeholder = isPassword ? 'Enter secure value...' : 'Type your input...';
    
    // Submit button
    const submitBtn = document.createElement('button');
    submitBtn.type = 'button';
    submitBtn.className = 'zBtn zBtn-sm zBtn-primary';
    submitBtn.innerHTML = '<i class="bi bi-arrow-return-left"></i> Submit';
    
    // Handle submit
    const submitInput = () => {
      const value = inputField.value;
      
      // Send input response via WebSocket
      if (window.bifrostClient && window.bifrostClient.connection) {
        window.bifrostClient.connection.send(JSON.stringify({
          event: 'input_response',
          requestId: requestId,
          value: value
        }));
      }
      
      // Replace input UI with submitted value display (mask password values)
      const displayValue = isPassword ? '•'.repeat(value.length || 8) : value;
      const icon = isPassword ? 'bi-shield-lock' : 'bi-keyboard';
      inputContainer.innerHTML = `<span class="zText-muted"><i class="bi ${icon}"></i> ${prompt || 'Input:'}</span> <span class="zText-light">${displayValue}</span>`;
    };
    
    // Submit on Enter key
    inputField.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        submitInput();
      }
    });
    
    // Submit on button click
    submitBtn.addEventListener('click', submitInput);
    
    // Assemble and append
    inputContainer.appendChild(promptLabel);
    inputContainer.appendChild(inputField);
    inputContainer.appendChild(submitBtn);
    targetOutput.appendChild(inputContainer);
    
    // Focus the input field
    inputField.focus();
  }
}
