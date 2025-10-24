"""DEPRECATED: Re-exports from global_object_factory for backward compatibility."""

import warnings

warnings.warn(
    "Importing from 'specrec.interfaces' is deprecated. "
    "Use 'from global_object_factory import ConstructorParameterInfo, IConstructorCalledWith, IObjectWithId' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from global-object-factory
from global_object_factory import (
    ConstructorParameterInfo,
    IConstructorCalledWith,
    IObjectWithId,
)

__all__ = [
    "ConstructorParameterInfo",
    "IConstructorCalledWith",
    "IObjectWithId",
]
