/**
 * Validation Utilities for Bifrost Forms and Inputs
 *
 * Provides reusable validation functions for frontend input validation.
 * These complement backend validation by providing immediate UX feedback.
 *
 * Validation Philosophy:
 * - Frontend: UX feedback, basic checks (required, format, range)
 * - Backend: Security, business logic, data integrity
 *
 * @module validation_utils
 */

/**
 * Validate required field
 * @param {string} value - Field value
 * @param {string} fieldName - Field name for error message
 * @returns {Object} { valid: boolean, message: string }
 */
export function validateRequired(value, fieldName = 'Field') {
  if (!value || value.trim() === '') {
    return {
      valid: false,
      message: `${fieldName} is required`
    };
  }
  return { valid: true, message: '' };
}

/**
 * Validate email format
 * @param {string} email - Email address
 * @returns {Object} { valid: boolean, message: string }
 */
export function validateEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  if (!email || email.trim() === '') {
    return { valid: false, message: 'Email is required' };
  }

  if (!emailRegex.test(email)) {
    return { valid: false, message: 'Please enter a valid email address' };
  }

  return { valid: true, message: '' };
}

/**
 * Validate minimum length
 * @param {string} value - Field value
 * @param {number} minLength - Minimum length
 * @param {string} fieldName - Field name for error message
 * @returns {Object} { valid: boolean, message: string }
 */
export function validateMinLength(value, minLength, fieldName = 'Field') {
  if (!value || value.length < minLength) {
    return {
      valid: false,
      message: `${fieldName} must be at least ${minLength} characters`
    };
  }
  return { valid: true, message: '' };
}

/**
 * Validate maximum length
 * @param {string} value - Field value
 * @param {number} maxLength - Maximum length
 * @param {string} fieldName - Field name for error message
 * @returns {Object} { valid: boolean, message: string }
 */
export function validateMaxLength(value, maxLength, fieldName = 'Field') {
  if (value && value.length > maxLength) {
    return {
      valid: false,
      message: `${fieldName} must not exceed ${maxLength} characters`
    };
  }
  return { valid: true, message: '' };
}

/**
 * Validate numeric value
 * @param {string} value - Field value
 * @param {string} fieldName - Field name for error message
 * @returns {Object} { valid: boolean, message: string }
 */
export function validateNumeric(value, fieldName = 'Field') {
  if (!value || value.trim() === '') {
    return { valid: false, message: `${fieldName} is required` };
  }

  if (isNaN(value)) {
    return { valid: false, message: `${fieldName} must be a number` };
  }

  return { valid: true, message: '' };
}

/**
 * Validate numeric range
 * @param {string|number} value - Field value
 * @param {number} min - Minimum value (inclusive)
 * @param {number} max - Maximum value (inclusive)
 * @param {string} fieldName - Field name for error message
 * @returns {Object} { valid: boolean, message: string }
 */
export function validateRange(value, min, max, fieldName = 'Field') {
  const num = parseFloat(value);

  if (isNaN(num)) {
    return { valid: false, message: `${fieldName} must be a number` };
  }

  if (num < min || num > max) {
    return {
      valid: false,
      message: `${fieldName} must be between ${min} and ${max}`
    };
  }

  return { valid: true, message: '' };
}

/**
 * Validate URL format
 * @param {string} url - URL string
 * @returns {Object} { valid: boolean, message: string }
 */
export function validateURL(url) {
  if (!url || url.trim() === '') {
    return { valid: false, message: 'URL is required' };
  }

  try {
    new URL(url);
    return { valid: true, message: '' };
  } catch (error) {
    return { valid: false, message: 'Please enter a valid URL' };
  }
}

/**
 * Validate password strength
 * @param {string} password - Password string
 * @param {Object} options - Validation options
 * @param {number} options.minLength - Minimum length (default: 8)
 * @param {boolean} options.requireUppercase - Require uppercase letter (default: false)
 * @param {boolean} options.requireLowercase - Require lowercase letter (default: false)
 * @param {boolean} options.requireNumber - Require number (default: false)
 * @param {boolean} options.requireSpecial - Require special character (default: false)
 * @returns {Object} { valid: boolean, message: string }
 */
export function validatePassword(password, options = {}) {
  const {
    minLength = 8,
    requireUppercase = false,
    requireLowercase = false,
    requireNumber = false,
    requireSpecial = false
  } = options;

  if (!password || password.trim() === '') {
    return { valid: false, message: 'Password is required' };
  }

  if (password.length < minLength) {
    return {
      valid: false,
      message: `Password must be at least ${minLength} characters`
    };
  }

  if (requireUppercase && !/[A-Z]/.test(password)) {
    return {
      valid: false,
      message: 'Password must contain at least one uppercase letter'
    };
  }

  if (requireLowercase && !/[a-z]/.test(password)) {
    return {
      valid: false,
      message: 'Password must contain at least one lowercase letter'
    };
  }

  if (requireNumber && !/\d/.test(password)) {
    return { valid: false, message: 'Password must contain at least one number' };
  }

  if (requireSpecial && !/[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(password)) {
    return {
      valid: false,
      message: 'Password must contain at least one special character'
    };
  }

  return { valid: true, message: '' };
}

/**
 * Validate pattern match (regex)
 * @param {string} value - Field value
 * @param {RegExp} pattern - Regular expression pattern
 * @param {string} fieldName - Field name for error message
 * @param {string} patternDescription - Description of expected pattern
 * @returns {Object} { valid: boolean, message: string }
 */
export function validatePattern(value, pattern, fieldName = 'Field', patternDescription = 'valid format') {
  if (!value || value.trim() === '') {
    return { valid: false, message: `${fieldName} is required` };
  }

  if (!pattern.test(value)) {
    return {
      valid: false,
      message: `${fieldName} must match ${patternDescription}`
    };
  }

  return { valid: true, message: '' };
}

/**
 * Combine multiple validation results
 * @param {...Object} validations - Validation result objects
 * @returns {Object} { valid: boolean, message: string } - First error or success
 */
export function combineValidations(...validations) {
  for (const validation of validations) {
    if (!validation.valid) {
      return validation;
    }
  }
  return { valid: true, message: '' };
}
