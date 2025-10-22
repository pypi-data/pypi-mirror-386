"""
Configuration constants for JWT tools.
"""

# RSA Attack Tool Configuration
DEFAULT_MAX_PROCESSES = 8
DEFAULT_PRIME_LIMIT = 100
RSA_PUBLIC_EXPONENT = 65537

# Supported algorithms
SUPPORTED_HMAC_ALGORITHMS = {'HS256', 'HS384', 'HS512'}
SUPPORTED_RSA_ALGORITHMS = {'RS256', 'RS384', 'RS512', 'PS256', 'PS384', 'PS512'}
SUPPORTED_ECDSA_ALGORITHMS = {'ES256', 'ES384', 'ES512'}

ALL_SUPPORTED_ALGORITHMS = (
    SUPPORTED_HMAC_ALGORITHMS | 
    SUPPORTED_RSA_ALGORITHMS | 
    SUPPORTED_ECDSA_ALGORITHMS
)

# Logging configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO'
