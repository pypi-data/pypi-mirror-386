"""
Pydantic Compatibility Layer

Provides a unified API for both Pydantic v1 and v2, allowing the code to work
with whichever version is installed in the environment.

Usage:
    from lfcdemolib._pydantic_compat import (
        BaseModel, Field, field_validator, model_validator, ConfigDict
    )
"""

import sys
from typing import Any, Callable, Optional, Type

try:
    import pydantic
    PYDANTIC_VERSION = int(pydantic.VERSION.split('.')[0])
except ImportError:
    raise ImportError("pydantic is required but not installed")

# Determine if we're using Pydantic v1 or v2
IS_PYDANTIC_V2 = PYDANTIC_VERSION >= 2

print(f"ℹ️  Using Pydantic v{pydantic.VERSION} (v{PYDANTIC_VERSION})", file=sys.stderr)

if IS_PYDANTIC_V2:
    # Pydantic v2 imports
    from pydantic import BaseModel as _BaseModel, Field
    from pydantic import field_validator as _field_validator
    from pydantic import model_validator as _model_validator
    from pydantic import ConfigDict
    
    # Wrapper to make v2 API work like v1
    def field_validator(*fields, pre: bool = False, always: bool = False, check_fields: bool = True):
        """Wrapper for field_validator that works like v1 validator"""
        mode = 'before' if pre else 'after'
        return _field_validator(*fields, mode=mode)
    
    def model_validator(mode: str = 'after'):
        """Wrapper for model_validator that works like v1 root_validator"""
        return _model_validator(mode=mode)
    
    class BaseModel(_BaseModel):
        """BaseModel with v2 configuration"""
        model_config = ConfigDict(
            extra='allow',
            str_strip_whitespace=True,
            populate_by_name=True,
        )

else:
    # Pydantic v1 imports
    from pydantic import BaseModel as _BaseModel, Field
    from pydantic import validator as _validator
    from pydantic import root_validator as _root_validator
    
    # ConfigDict doesn't exist in v1, create dummy
    ConfigDict = dict
    
    # Wrapper to make v1 API work with v2-style calls
    def field_validator(*fields, pre: bool = False, always: bool = False, check_fields: bool = True):
        """Wrapper for validator that works like v2 field_validator"""
        return _validator(*fields, pre=pre, always=always, check_fields=check_fields)
    
    def model_validator(mode: str = 'after'):
        """Wrapper for root_validator that works like v2 model_validator"""
        pre = (mode == 'before')
        return _root_validator(pre=pre, allow_reuse=True)
    
    class BaseModel(_BaseModel):
        """BaseModel with v1 configuration"""
        class Config:
            extra = 'allow'
            anystr_strip_whitespace = True
            allow_population_by_field_name = True


__all__ = [
    'BaseModel',
    'Field',
    'field_validator',
    'model_validator',
    'ConfigDict',
    'IS_PYDANTIC_V2',
    'PYDANTIC_VERSION',
]

