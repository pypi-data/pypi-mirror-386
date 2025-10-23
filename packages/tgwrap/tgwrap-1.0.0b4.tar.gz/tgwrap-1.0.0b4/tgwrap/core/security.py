"""Security validation utilities for tgwrap."""

import os
import re
from typing import List, Optional


class SecurityValidator:
    """Validates user inputs to prevent security vulnerabilities."""

    # Patterns for detecting potentially dangerous characters
    DANGEROUS_PATTERNS = [
        r'[;&|`$(){}[\]\\]',  # Command injection characters
        r'\$\(',  # Command substitution
        r'`',     # Backticks for command execution
        r'\.\./+',  # Path traversal attempts
    ]

    # Safe patterns for resource identifiers
    SAFE_RESOURCE_PATTERN = r'^[a-zA-Z0-9._/-]+$'
    SAFE_MODULE_PATTERN = r'^[a-zA-Z0-9._/-]+$'

    @staticmethod
    def validate_command_args(args: List[str]) -> bool:
        """Validate terragrunt arguments for safety."""
        if not args:
            return True

        for arg in args:
            if not isinstance(arg, str):
                return False

            # Check for dangerous patterns
            for pattern in SecurityValidator.DANGEROUS_PATTERNS:
                if re.search(pattern, arg):
                    return False

            # Ensure reasonable length
            if len(arg) > 1000:
                return False

        return True

    @staticmethod
    def validate_working_dir(working_dir: Optional[str]) -> bool:
        """Validate working directory path for safety."""
        if not working_dir:
            return True

        # Resolve and normalize path
        try:
            normalized = os.path.normpath(working_dir)

            # Check for path traversal attempts
            if '..' in normalized:
                return False

            # Ensure it's not trying to access system directories
            system_dirs = ['/etc', '/bin', '/sbin', '/usr/bin', '/usr/sbin']
            if any(normalized.startswith(sys_dir) for sys_dir in system_dirs):
                return False

            return True

        except (OSError, ValueError):
            return False

    @staticmethod
    def validate_resource_identifier(identifier: str) -> bool:
        """Validate resource identifier for safety."""
        if not identifier or not isinstance(identifier, str):
            return False

        # Check length
        if len(identifier) > 255:
            return False

        # Check pattern
        return re.match(SecurityValidator.SAFE_RESOURCE_PATTERN, identifier) is not None

    @staticmethod
    def validate_module_name(module_name: Optional[str]) -> bool:
        """Validate module name for safety."""
        if not module_name:
            return True

        if not isinstance(module_name, str):
            return False

        # Check length
        if len(module_name) > 255:
            return False

        # Check for dangerous patterns
        for pattern in SecurityValidator.DANGEROUS_PATTERNS:
            if re.search(pattern, module_name):
                return False

        # Check pattern
        return re.match(SecurityValidator.SAFE_MODULE_PATTERN, module_name) is not None

    @staticmethod
    def sanitize_for_logging(text: str) -> str:
        """Sanitize text for safe logging (remove potentially sensitive info)."""
        if not text:
            return text

        # Remove potential secrets/tokens
        sanitized = re.sub(r'(token|password|key|secret)=[^\s&]+', r'\1=***', text, flags=re.IGNORECASE)

        # Limit length for logging
        if len(sanitized) > 500:
            sanitized = sanitized[:497] + "..."

        return sanitized
