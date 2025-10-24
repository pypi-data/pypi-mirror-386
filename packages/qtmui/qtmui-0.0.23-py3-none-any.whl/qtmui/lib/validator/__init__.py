"""
    Extensible validation for Python dictionaries.

    :copyright: 2012-2023 by Nicola Iarocci.
    :license: ISC, see LICENSE for more details.

    Full documentation is available at https://python-cerberus.org/

"""

from __future__ import absolute_import

from .platform import importlib_metadata
from .schema import rules_set_registry, schema_registry, SchemaError
from .utils import TypeDefinition
from .validator import DocumentError, Validator


try:
    __version__ = importlib_metadata.version("Cerberus")
except importlib_metadata.PackageNotFoundError:
    __version__ = "unknown"

__all__ = [
    DocumentError.__name__,
    SchemaError.__name__,
    TypeDefinition.__name__,
    Validator.__name__,
    "schema_registry",
    "rules_set_registry",
    "__version__",
]
