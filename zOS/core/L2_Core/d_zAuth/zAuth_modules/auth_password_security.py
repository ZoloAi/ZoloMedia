"""
Password Security Module - bcrypt hashing and verification (v1.5.4+)

This module provides cryptographically secure password hashing and verification
using the bcrypt algorithm. It is intentionally isolated from zCLI dependencies
to ensure maximum testability, reusability, and security auditing.

ARCHITECTURE - Pure Security Module

Isolation Strategy:
    - No zCLI dependencies (only bcrypt and standard library)
    - Pure functions with explicit dependencies (logger is optional)
    - Testable in complete isolation from the zCLI framework
    - Reusable in other Python projects without modification

Design Pattern:
    - Stateless operations (no instance state beyond logger)
    - Dependency injection via constructor (logger)
    - Explicit error handling with graceful degradation
    - Industry-standard bcrypt implementation

BCRYPT ALGORITHM - Adaptive Hash Function

Algorithm: Blowfish cipher + Eksblowfish key schedule
    - Based on the Blowfish cipher (Bruce Schneier, 1993)
    - Modified with "Expensive Key Setup" (Eksblowfish)
    - Designed specifically for password hashing
    - Adaptive: cost factor increases hash time exponentially

Security Properties:
    1. One-Way Hash:
       - Cannot recover plaintext from hash (irreversible)
       - Pre-image resistance (computationally infeasible to reverse)
       
    2. Rainbow Table Resistance:
       - Random salt per hash (22-character base64 salt)
       - Same password produces different hashes
       - Salt is embedded in the hash output ($2b$12$<salt><hash>)
       
    3. Brute-Force Protection:
       - Adaptive cost factor (2^rounds iterations)
       - 12 rounds = 4,096 iterations (~0.3s per hash)
       - Moore's Law mitigation: increase rounds as hardware improves
       
    4. Timing-Safe Comparison:
       - bcrypt.checkpw() uses constant-time comparison
       - Prevents timing attacks during verification

Hash Format: $2b$12$<22-char-salt><31-char-hash>
    - $2b$: bcrypt algorithm identifier (version 2b)
    - 12: cost factor (2^12 = 4,096 iterations)
    - Salt: 22 characters base64-encoded (128 bits)
    - Hash: 31 characters base64-encoded (184 bits)

PERFORMANCE CHARACTERISTICS

Hash Time (12 rounds):
    - Modern CPU (2020+): ~0.3 seconds per hash
    - Intentionally slow to prevent brute-force attacks
    - Acceptable for user login (human time scale)
    - NOT suitable for high-frequency operations (use caching)

Cost Factor Selection:
    - 12 rounds: Good balance for production (2020s)
    - 10 rounds: Faster, less secure (testing/development)
    - 14 rounds: Slower, more secure (high-security applications)
    - Rule: Hash should take ~0.5-1.0 seconds on current hardware

Memory Usage:
    - Minimal per-hash memory (~4KB)
    - No memory-hard properties (unlike Argon2)
    - Suitable for constrained environments

BCRYPT LIMITATIONS

72-Byte Password Limit:
    - bcrypt truncates passwords to 72 bytes
    - This module explicitly handles truncation with warnings
    - UTF-8 encoding: multibyte characters count as multiple bytes
    - Example: "密码" (2 chars) = 6 bytes in UTF-8

Recommendation:
    - For passwords > 72 bytes, consider pre-hashing with SHA-256
    - Current implementation: truncate and log warning
    - Future consideration: SHA-256 pre-hash for long passwords

THREAD SAFETY

Thread Safety: YES (with caveats)
    - bcrypt operations are thread-safe
    - No shared state between instances
    - Logger must be thread-safe (standard Python logging is)

Concurrency Considerations:
    - Each hash takes ~0.3s: use thread pool for multiple hashes
    - bcrypt releases GIL during computation
    - Suitable for async/await patterns (use run_in_executor)

USAGE EXAMPLES

Basic Usage:
    >>> from zOS.L2_Core.d_zAuth.zAuth_modules.auth_password_security import PasswordSecurity
    >>> pwd_security = PasswordSecurity()
    >>> 
    >>> # Hash a password
    >>> hashed = pwd_security.hash_password("my_secure_password")
    >>> print(hashed[:7])
    '$2b$12$'
    >>> 
    >>> # Verify password
    >>> is_valid = pwd_security.verify_password("my_secure_password", hashed)
    >>> print(is_valid)
    True

With Logger (Production):
    >>> import logging
    >>> logger = logging.getLogger(__name__)
    >>> pwd_security = PasswordSecurity(logger=logger)
    >>> 
    >>> # Long password warning will be logged
    >>> long_password = "x" * 100
    >>> hashed = pwd_security.hash_password(long_password)

Integration with zAuth:
    >>> # Used by auth_authentication.py for user login
    >>> from zOS.L2_Core.d_zAuth.zAuth_modules import PasswordSecurity
    >>> pwd_security = PasswordSecurity(logger=zcli.logger)
    >>> 
    >>> # Store hashed password in database
    >>> user_password_hash = pwd_security.hash_password(user_input)
    >>> 
    >>> # Verify during login
    >>> if pwd_security.verify_password(user_input, stored_hash):
    >>>     # Grant access
    >>>     pass

Performance Testing:
    >>> import time
    >>> pwd_security = PasswordSecurity()
    >>> 
    >>> start = time.time()
    >>> hashed = pwd_security.hash_password("test_password")
    >>> elapsed = time.time() - start
    >>> print(f"Hash time: {elapsed:.2f}s")
    Hash time: 0.31s
"""

import bcrypt

from zOS import Optional, Any

# Import centralized constants
from .auth_constants import (
    # Public constants
    BCRYPT_ROUNDS,
    BCRYPT_MAX_PASSWORD_BYTES,
    BCRYPT_PREFIX,
    # Internal constants (private)
    _SALT_LENGTH,
    _HASH_TIME_SECONDS,
    _ENCODING_UTF8,
    _LOG_PREFIX_PASSWORD,
    _LOG_TRUNCATION_WARNING,
    _LOG_VERIFICATION_ERROR,
    _ERR_EMPTY_PASSWORD,
)

# Module uses _LOG_PREFIX_PASSWORD as LOG_PREFIX for compatibility
LOG_PREFIX = _LOG_PREFIX_PASSWORD


# Password Security Class

class PasswordSecurity:
    """
    Cryptographically secure password hashing and verification using bcrypt.
    
    This class provides a clean, production-ready interface to the bcrypt
    password hashing algorithm. It handles all edge cases (empty passwords,
    long passwords, encoding) and provides comprehensive error handling.
    
    Architecture:
        - Stateless operations (no instance state beyond logger)
        - Pure security module (no zCLI dependencies)
        - Dependency injection pattern (optional logger)
        - Industry-standard bcrypt implementation
    
    Security Features:
        1. Adaptive Hashing:
           - 12 rounds (4,096 iterations) by default
           - ~0.3s per hash on modern hardware
           - Configurable via BCRYPT_ROUNDS constant
        
        2. Automatic Salting:
           - Random 22-character salt per hash
           - Salt embedded in output ($2b$12$<salt><hash>)
           - Same password produces different hashes
        
        3. One-Way Hashing:
           - Cannot recover plaintext from hash
           - Pre-image resistance (computationally infeasible)
        
        4. Timing-Safe Comparison:
           - Constant-time comparison via bcrypt.checkpw()
           - Prevents timing attacks during verification
        
        5. 72-Byte Limit Handling:
           - Automatic truncation with optional warning
           - Consistent behavior between hash and verify
    
    Performance:
        - Hash time: ~0.3s per password (12 rounds)
        - Memory: ~4KB per hash operation
        - Thread-safe: Yes (bcrypt releases GIL)
        - Suitable for: User login, password changes
        - NOT suitable for: High-frequency operations
    
    Methods:
        hash_password(password): Hash a plaintext password
        verify_password(password, hash): Verify password against hash
        _truncate_password(password): Helper for 72-byte truncation (private)
    
    Usage:
        >>> pwd_security = PasswordSecurity()
        >>> hashed = pwd_security.hash_password("my_password")
        >>> is_valid = pwd_security.verify_password("my_password", hashed)
        >>> print(is_valid)
        True
    
    Integration:
        - Used by auth_authentication.py for user login
        - Can be used standalone in other projects
        - Thread-safe for concurrent operations
        - Logger is optional (graceful degradation)
    
    Thread Safety:
        - Yes: bcrypt operations are thread-safe
        - No shared state between instances
        - Logger must be thread-safe (Python logging is)
    
    Attributes:
        logger: Optional[Any] - Logger for warnings/errors (optional)
    """
    
    # Class-level type declarations
    logger: Optional[Any]
    
    def __init__(self, logger: Optional[Any] = None):
        """Initialize password security module with optional logger.
        
        Args:
            logger: Optional logger instance for warnings and errors.
                   If None, no logging occurs (graceful degradation).
                   Should support .warning() and .error() methods.
        
        Example:
            >>> # Without logger (silent mode)
            >>> pwd_security = PasswordSecurity()
            >>> 
            >>> # With logger (production mode)
            >>> import logging
            >>> logger = logging.getLogger(__name__)
            >>> pwd_security = PasswordSecurity(logger=logger)
        
        Thread Safety:
            - Each instance is independent and thread-safe
            - Logger must be thread-safe (standard Python logging is)
        """
        self.logger = logger
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Private Helper Methods
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _truncate_password(self, plain_password: str) -> bytes:
        """Truncate password to 72 bytes if necessary (bcrypt limit).
        
        This helper method consolidates password truncation logic to eliminate
        code duplication and ensure consistent behavior between hash_password()
        and verify_password().
        
        Args:
            plain_password: Plaintext password string to truncate
        
        Returns:
            bytes: Password encoded as UTF-8, truncated to 72 bytes if necessary
        
        Notes:
            - bcrypt has a hard 72-byte limit (algorithm constraint)
            - UTF-8 encoding: multibyte characters count as multiple bytes
            - Logs warning if truncation occurs (if logger is available)
            - Consistent truncation ensures verify_password() matches hash_password()
        
        Example:
            >>> pwd_security = PasswordSecurity()
            >>> short = pwd_security._truncate_password("test")
            >>> len(short)
            4
            >>> 
            >>> long = pwd_security._truncate_password("x" * 100)
            >>> len(long)
            72
        """
        password_bytes = plain_password.encode(ENCODING_UTF8)
        if len(password_bytes) > BCRYPT_MAX_PASSWORD_BYTES:
            if self.logger:
                self.logger.warning(f"{LOG_PREFIX} {LOG_TRUNCATION_WARNING}")
            password_bytes = password_bytes[:BCRYPT_MAX_PASSWORD_BYTES]
        return password_bytes
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Public API Methods
    # ═══════════════════════════════════════════════════════════════════════════
    
    def hash_password(self, plain_password: str) -> str:
        """Hash a plaintext password using bcrypt with automatic salting.
        
        This method generates a cryptographically secure hash of the provided
        password using the bcrypt algorithm with BCRYPT_ROUNDS (12) iterations.
        Each hash includes a random salt, ensuring the same password produces
        different hashes.
        
        Args:
            plain_password: Plaintext password string to hash
        
        Returns:
            str: bcrypt hashed password in format $2b$12$<salt><hash>
                - $2b$: bcrypt algorithm version identifier
                - 12: cost factor (2^12 = 4,096 iterations)
                - <salt>: 22-character base64 salt
                - <hash>: 31-character base64 hash
        
        Raises:
            ValueError: If password is empty or None
        
        Performance:
            - Hash time: ~HASH_TIME_SECONDS (0.3s) on modern hardware
            - Memory: ~4KB per hash operation
            - Thread-safe: Yes (bcrypt releases GIL)
        
        Example:
            >>> pwd_security = PasswordSecurity()
            >>> hashed = pwd_security.hash_password("my_secure_password")
            >>> print(hashed[:7])
            '$2b$12$'
            >>> print(len(hashed))
            60
            >>> 
            >>> # Same password produces different hashes (salted)
            >>> hash1 = pwd_security.hash_password("password")
            >>> hash2 = pwd_security.hash_password("password")
            >>> print(hash1 == hash2)
            False
        
        Security:
            - Uses bcrypt with BCRYPT_ROUNDS (12) rounds
            - Random salt per hash (rainbow table resistance)
            - One-way hash (cannot recover plaintext)
            - Passwords > BCRYPT_MAX_PASSWORD_BYTES (72) are truncated with warning
        
        Integration:
            >>> # Store in database (auth_authentication.py)
            >>> user_password_hash = pwd_security.hash_password(user_input)
            >>> db.save_user(username, user_password_hash)
        
        Constants Used:
            - BCRYPT_ROUNDS: Cost factor (12 = 4,096 iterations)
            - BCRYPT_MAX_PASSWORD_BYTES: Truncation limit (72 bytes)
            - ENCODING_UTF8: Text encoding ("utf-8")
            - ERR_EMPTY_PASSWORD: Error message for empty passwords
        """
        if not plain_password:
            raise ValueError(ERR_EMPTY_PASSWORD)
        
        # Truncate to 72 bytes if necessary (bcrypt limit)
        password_bytes = self._truncate_password(plain_password)
        
        # Generate salt and hash (BCRYPT_ROUNDS = ~HASH_TIME_SECONDS on modern hardware)
        salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        # Return as string (bcrypt returns bytes)
        return hashed.decode(ENCODING_UTF8)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plaintext password against a bcrypt hash with timing-safe comparison.
        
        This method performs constant-time comparison of the provided password
        against the stored hash using bcrypt.checkpw(). It handles all edge cases
        gracefully and never exposes password details in error messages.
        
        Args:
            plain_password: Plaintext password to verify (user input)
            hashed_password: bcrypt hashed password from database/storage
        
        Returns:
            bool: True if password matches hash, False otherwise
                - True: Password is correct (grants access)
                - False: Password is wrong, hash is invalid, or error occurred
        
        Performance:
            - Verify time: ~HASH_TIME_SECONDS (0.3s) on modern hardware
            - Same performance as hash_password() (by design)
            - Thread-safe: Yes (bcrypt releases GIL)
        
        Example:
            >>> pwd_security = PasswordSecurity()
            >>> hashed = pwd_security.hash_password("correct_password")
            >>> 
            >>> # Correct password
            >>> pwd_security.verify_password("correct_password", hashed)
            True
            >>> 
            >>> # Wrong password
            >>> pwd_security.verify_password("wrong_password", hashed)
            False
            >>> 
            >>> # Invalid hash (graceful failure)
            >>> pwd_security.verify_password("password", "invalid_hash")
            False
        
        Security:
            - Timing-safe comparison via bcrypt.checkpw() (constant time)
            - Prevents timing attacks (cannot deduce password from timing)
            - Handles invalid hashes gracefully (returns False)
            - Logs errors without exposing password details
            - Truncates passwords > BCRYPT_MAX_PASSWORD_BYTES (72) to match hash_password()
        
        Error Handling:
            - Empty password: Returns False (no exception)
            - Empty hash: Returns False (no exception)
            - Invalid hash format: Returns False (logs error)
            - Exception during verification: Returns False (logs error)
            - Never exposes password in logs or exceptions
        
        Integration:
            >>> # User login (auth_authentication.py)
            >>> stored_hash = db.get_user_password_hash(username)
            >>> if pwd_security.verify_password(user_input, stored_hash):
            >>>     # Grant access
            >>>     grant_access(username)
            >>> else:
            >>>     # Deny access
            >>>     log_failed_attempt(username)
        
        Constants Used:
            - BCRYPT_MAX_PASSWORD_BYTES: Truncation limit (72 bytes)
            - ENCODING_UTF8: Text encoding ("utf-8")
            - LOG_PREFIX: Log message prefix
            - LOG_VERIFICATION_ERROR: Error message for verification failures
        """
        if not plain_password or not hashed_password:
            return False
        
        try:
            # Truncate to 72 bytes (same as hash_password for consistency)
            password_bytes = self._truncate_password(plain_password)
            
            # Timing-safe comparison (constant time, prevents timing attacks)
            return bcrypt.checkpw(
                password_bytes,
                hashed_password.encode(ENCODING_UTF8)
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f"{LOG_PREFIX} {LOG_VERIFICATION_ERROR}: {e}")
            return False
