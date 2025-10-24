"""DEPRECATED: Re-exports from global_object_factory for backward compatibility."""

import warnings

warnings.warn(
    "Importing from 'specrec.object_factory' is deprecated. "
    "Use 'from global_object_factory import ObjectFactory, get_instance, reset_instance' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from global-object-factory
from global_object_factory import (
    ObjectFactory,
    get_instance,
    reset_instance,
)

__all__ = [
    "ObjectFactory",
    "get_instance",
    "reset_instance",
]
