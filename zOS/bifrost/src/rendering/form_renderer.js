/**
 * FormRenderer - Async Form Rendering for zDialog in Bifrost Mode
 *
 * This renderer handles the display and submission of zDialog forms in the browser.
 * Unlike Terminal mode (which collects input field-by-field), Bifrost displays the
 * entire form at once with all fields visible.
 *
 * Key Differences from Terminal:
 * - Terminal: Blocking, field-by-field, synchronous
 * - Bifrost: Non-blocking, all-at-once, asynchronous
 *
 * Flow:
 * 1. Backend sends zDialog event with form context
 * 2. FormRenderer displays full HTML form
 * 3. User fills and clicks Submit
 * 4. FormRenderer sends form_submit WebSocket message
 * 5. Backend validates and executes onSubmit
 * 6. Backend sends result back to frontend
 *
 * Architecture:
 * - Uses form_primitives.js for raw HTML element creation
 * - Uses dom_utils.js for DOM manipulation
 * - Applies zTheme classes for styling
 * - Handles WebSocket communication for submission
 *
 * @module FormRenderer
 */

import { createElement, clearElement } from '../utils/dom_utils.js';
import { withErrorBoundary } from '../utils/error_boundary.js';
import {
  createForm,
  createInput,
  createTextarea,
  createLabel
} from './primitives/form_primitives.js';

export class FormRenderer {
  constructor(client) {
    this.client = client;
    this.logger = client.logger;
    this.currentForm = null;

    // Wrap render method with error boundary
    const originalRender = this.render.bind(this);
    this.render = withErrorBoundary(originalRender, {
      component: 'FormRenderer',
      logger: this.logger
    });
  }

  /**
   * Render a zDialog form
   * @param {Object} eventData - Form context from backend
   * @param {string} eventData.title - Form title
   * @param {string} eventData.model - Schema model path (optional)
   * @param {Array} eventData.fields - Field definitions
   * @param {Object} eventData.onSubmit - Submit action to execute
   * @param {string} eventData._dialogId - Unique form identifier
   * @returns {HTMLElement} Form container element
   */
  renderForm(eventData) {
    this.logger.log('[FormRenderer] Rendering form:', eventData.title);

    const {
      title = 'Form',
      model,
      fields = [],
      onSubmit,
      _dialogId
    } = eventData;

    // Store current form context for submission
    this.currentForm = {
      _dialogId,
      model,
      onSubmit,
      fields
    };

    // Create form container using primitives
    const formContainer = createElement('div', ['zDialog-container', 'zCard', 'zp-4'], {
      'data-dialog-id': _dialogId
    });

    // Form title
    if (title) {
      const titleElement = createElement('h2', ['zDialog-title', 'zCard-title', 'zmb-3']);
      titleElement.textContent = title;
      formContainer.appendChild(titleElement);
    }

    // Create HTML form element using primitive
    const form = createForm({
      class: 'zDialog-form',
      'data-dialog-id': _dialogId
    });

    // Render fields
    fields.forEach(fieldDef => {
      const fieldGroup = this._createFieldGroup(fieldDef);
      form.appendChild(fieldGroup);
    });

    // Error display area (hidden by default)
    const errorContainer = createElement('div', ['zDialog-errors', 'zAlert', 'zAlert-danger', 'zmt-3']);
    errorContainer.style.display = 'none';
    form.appendChild(errorContainer);

    // Submit button using primitive
    const submitButton = createElement('button', ['zBtn', 'zBtn-primary', 'zmt-3'], {
      type: 'submit'
    });
    submitButton.textContent = 'Submit';
    form.appendChild(submitButton);

    // Handle form submission
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      this._handleSubmit(form, _dialogId);
    });

    formContainer.appendChild(form);
    return formContainer;
  }

  /**
   * Create a form field group (label + input)
   * @private
   * @param {string|Object} fieldDef - Field definition (string or object)
   * @returns {HTMLElement} Field group element
   */
  _createFieldGroup(fieldDef) {
    // Handle both string and object field definitions
    const fieldName = typeof fieldDef === 'string' ? fieldDef : fieldDef.name;

    // Auto-detect field type from field name if not explicitly provided
    let fieldType = 'text';
    if (typeof fieldDef === 'object' && fieldDef.type) {
      // Explicit type provided
      fieldType = fieldDef.type;
    } else {
      // Auto-detect based on field name
      const lowerName = fieldName.toLowerCase();
      if (lowerName === 'password' || lowerName.includes('password')) {
        fieldType = 'password';
      } else if (lowerName === 'email' || lowerName.includes('email')) {
        fieldType = 'email';
      } else if (lowerName === 'phone' || lowerName === 'tel' || lowerName.includes('phone')) {
        fieldType = 'tel';
      }
    }

    const fieldLabel = typeof fieldDef === 'object' ? (fieldDef.label || fieldName) : fieldName;
    const required = typeof fieldDef === 'object' ? (fieldDef.required !== false) : true;

    // Field group container
    const fieldGroup = createElement('div', ['zmb-3']);

    // Label using primitive
    const label = createLabel(fieldName, { class: 'zLabel' });
    label.textContent = this._formatLabel(fieldLabel);

    if (required) {
      const requiredMark = createElement('span', ['zText-danger']);
      requiredMark.textContent = ' *';
      label.appendChild(requiredMark);
    }
    fieldGroup.appendChild(label);

    // Input field using primitive
    const input = this._createInput(fieldName, fieldType, required);
    fieldGroup.appendChild(input);

    return fieldGroup;
  }

  /**
   * Create an input element based on field type using primitives
   * @private
   * @param {string} fieldName - Field name
   * @param {string} fieldType - Field type (text, password, email, textarea, etc.)
   * @param {boolean} required - Whether field is required
   * @returns {HTMLElement} Input element
   */
  _createInput(fieldName, fieldType, required) {
    let input;

    if (fieldType === 'textarea') {
      // Use textarea primitive
      input = createTextarea({
        name: fieldName,
        class: 'zInput',
        rows: 4,
        required: required,
        placeholder: `Enter ${this._formatLabel(fieldName).toLowerCase()}`
      });
    } else {
      // Use input primitive with appropriate type
      let inputType = 'text';

      // Map field types to HTML5 input types
      if (fieldType === 'password') {
        inputType = 'password';
      } else if (fieldType === 'email') {
        inputType = 'email';
      } else if (fieldType === 'number') {
        inputType = 'number';
      } else if (fieldType === 'tel' || fieldType === 'phone') {
        inputType = 'tel';
      }

      input = createInput(inputType, {
        name: fieldName,
        class: 'zInput',
        required: required,
        placeholder: `Enter ${this._formatLabel(fieldName).toLowerCase()}`
      });
    }

    return input;
  }

  /**
   * Format field name to human-readable label
   * @private
   * @param {string} fieldName - Field name (snake_case or camelCase)
   * @returns {string} Formatted label (Title Case)
   */
  _formatLabel(fieldName) {
    // Convert snake_case or camelCase to Title Case
    return fieldName
      .replace(/_/g, ' ')
      .replace(/([A-Z])/g, ' $1')
      .replace(/^./, str => str.toUpperCase())
      .trim();
  }

  /**
   * Handle form submission
   * @private
   * @param {HTMLFormElement} formElement - Form element
   * @param {string} dialogId - Dialog identifier
   */
  async _handleSubmit(formElement, dialogId) {
    this.logger.log('[FormRenderer] Form submit triggered:', dialogId);

    // Clear previous errors
    const errorContainer = formElement.querySelector('.zDialog-errors');
    if (errorContainer) {
      errorContainer.style.display = 'none';
      clearElement(errorContainer);
    }

    // Collect form data
    const formData = new FormData(formElement);
    const data = {};
    for (const [key, value] of formData.entries()) {
      data[key] = value;
    }

    this.logger.log('[FormRenderer] Collected form data:', Object.keys(data));

    // Disable submit button during submission
    const submitButton = formElement.querySelector('button[type="submit"]');
    const originalText = submitButton.textContent;
    submitButton.disabled = true;
    submitButton.textContent = 'Submitting...';

    try {
      // Send form submission to backend via WebSocket
      const response = await this.client.send({
        event: 'form_submit',
        dialogId: dialogId,
        data: data,
        onSubmit: this.currentForm.onSubmit,
        model: this.currentForm.model
      });

      this.logger.log('[FormRenderer] Submission response:', response);

      // Handle response
      if (response.success) {
        this._handleSuccess(formElement, response);
      } else {
        this._handleError(formElement, response);
      }

    } catch (error) {
      this.logger.error('[FormRenderer] Submission error:', error);
      this._handleError(formElement, {
        success: false,
        message: 'Failed to submit form. Please try again.',
        errors: [error.message]
      });
    } finally {
      // Re-enable submit button
      submitButton.disabled = false;
      submitButton.textContent = originalText;
    }
  }

  /**
   * Handle successful form submission
   * @private
   * @param {HTMLFormElement} formElement - Form element
   * @param {Object} response - Server response
   */
  _handleSuccess(formElement, response) {
    this.logger.log('[FormRenderer] Form submission successful');

    // Display success message
    const successContainer = createElement('div', ['zAlert', 'zAlert-success', 'zmt-3']);
    successContainer.innerHTML = `
      <strong>Success!</strong> ${response.message || 'Form submitted successfully.'}
    `;

    // Replace form with success message
    const formContainer = formElement.closest('.zDialog-container');
    if (formContainer) {
      clearElement(formContainer);
      formContainer.appendChild(successContainer);
    }

    // Refresh navbar after successful submission (e.g., after login)
    // This ensures RBAC-filtered navbar items are updated
    if (this.client && typeof this.client._fetchAndPopulateNavBar === 'function') {
      this.logger.log('[FormRenderer] Refreshing navbar for RBAC update');
      this.client._fetchAndPopulateNavBar().catch(err => {
        this.logger.error('[FormRenderer] Failed to refresh navbar:', err);
      });
    }

    // Clear current form context
    this.currentForm = null;
  }

  /**
   * Handle form submission error
   * @private
   * @param {HTMLFormElement} formElement - Form element
   * @param {Object} response - Server error response
   */
  _handleError(formElement, response) {
    this.logger.error('[FormRenderer] Form submission failed:', response);

    const errorContainer = formElement.querySelector('.zDialog-errors');
    if (errorContainer) {
      errorContainer.style.display = 'block';

      const errorList = createElement('ul', ['zmb-0']);

      // Display validation errors
      if (response.errors && Array.isArray(response.errors)) {
        response.errors.forEach(error => {
          const errorItem = createElement('li');
          errorItem.textContent = error;
          errorList.appendChild(errorItem);
        });
      } else {
        const errorItem = createElement('li');
        errorItem.textContent = response.message || 'Validation failed. Please check your input.';
        errorList.appendChild(errorItem);
      }

      clearElement(errorContainer);
      const errorHeader = createElement('strong');
      errorHeader.textContent = 'Error:';
      errorContainer.appendChild(errorHeader);
      errorContainer.appendChild(errorList);
    }

    // Scroll to errors
    if (errorContainer) {
      errorContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }
}
