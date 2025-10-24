"""
DEPRECATED: Use 'global-object-factory' instead.

This package has been renamed to 'global-object-factory' and now re-exports
all functionality from that package with deprecation warnings.

This module provides a clean API for object creation with test double injection
capabilities, making legacy code testable with minimal changes.

Main exports:
    create: Curried function for object creation
    ObjectFactory: Main factory class for advanced usage
    get_instance: Get the global factory instance
"""

import warnings

warnings.warn(
    "\n⚠️  DEPRECATION WARNING ⚠️\n\n"
    "The 'specrec' package has been renamed to 'global-object-factory'.\n\n"
    "Please update your dependencies:\n"
    "  pip uninstall specrec\n"
    "  pip install global-object-factory\n\n"
    "Update your imports:\n"
    "  Old: from specrec import create, set_one, context\n"
    "  New: from global_object_factory import create, set_one, context\n\n"
    "For more information, visit: https://github.com/ivettordog/global-object-factory",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from global-object-factory
from global_object_factory import (
    # Main classes
    ObjectFactory,
    get_instance,
    reset_instance,

    # Primary API functions
    create,
    create_direct,

    # Test double management
    set_one,
    set_always,
    clear_one,
    clear_all,
    context,

    # Object registration
    register_object,
    get_registered_object,

    # Protocols and types
    IConstructorCalledWith,
    IObjectWithId,
    ConstructorParameterInfo,
)

# Export key types and protocols
__all__ = [
    # Main classes
    "ObjectFactory",
    "get_instance",
    "reset_instance",

    # Primary API functions
    "create",
    "create_direct",

    # Test double management
    "set_one",
    "set_always",
    "clear_one",
    "clear_all",
    "context",

    # Object registration
    "register_object",
    "get_registered_object",

    # Protocols and types
    "IConstructorCalledWith",
    "IObjectWithId",
    "ConstructorParameterInfo",
]
