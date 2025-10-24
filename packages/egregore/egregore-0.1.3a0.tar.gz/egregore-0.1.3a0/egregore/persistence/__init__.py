"""Persistence engines and bridges for the Egregore core.

The persistence layer provides automatic state persistence for scaffolds through
a simple mixin pattern with pluggable backends.
"""

from .mixin import PersistenceMixin
from .backends import PersistenceBackend
from .backends.local import LocalStorage

__all__ = ['PersistenceMixin', 'PersistenceBackend', 'LocalStorage']
