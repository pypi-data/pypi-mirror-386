"""Persistence mixin for automatic scaffold state persistence."""

from typing import Optional, Any, Dict
from .backends import PersistenceBackend
from .backends.local import LocalStorage
import logging

logger = logging.getLogger(__name__)


class PersistenceMixin:
    """Mixin for automatic scaffold state persistence.

    Usage:
        class MyScaffold(StateScaffold, PersistenceMixin):
            pass

        # Override class attributes to customize:
        class MyScaffold(StateScaffold, PersistenceMixin):
            _persistence_backend = CustomBackend()
            _auto_persist = False

        scaffold = MyScaffold()  # Uses LocalStorage by default
        scaffold.state.items.append("x")  # Auto-saves

    Integration:
        Hooks into BaseContextScaffold's post_state_change() lifecycle hook.
        This is called automatically after every state change.
    """

    # Class-level defaults (can be overridden in subclasses)
    _persistence_backend: Optional[PersistenceBackend] = None
    _auto_persist: bool = True
    _persistence_enabled: bool = True

    def __init_subclass__(cls, **kwargs):
        """Wrap post_state_change to inject persistence logic regardless of MRO."""
        super().__init_subclass__(**kwargs)

        # Find the original post_state_change from the MRO
        original_post_state_change = None
        for base in cls.__mro__[1:]:  # Skip cls itself
            if 'post_state_change' in base.__dict__ and base is not PersistenceMixin:
                original_post_state_change = base.__dict__['post_state_change']
                break

        if original_post_state_change:
            # Wrap it to add persistence logic
            def wrapped_post_state_change(self, old_state, new_state, source, metadata):
                # Call the original first
                original_post_state_change(self, old_state, new_state, source, metadata)

                # Then add persistence logic
                self._ensure_persistence_initialized()
                if self._auto_persist and self._persistence_enabled:
                    logger.debug(f"Auto-saving after state change for {self.id}")
                    self._safe_save()

            cls.post_state_change = wrapped_post_state_change

    def _ensure_persistence_initialized(self):
        """Lazy initialization of persistence attributes.

        Called on first state change to set up persistence if not already initialized.
        This avoids issues with metaclass __init__ replacement.
        """
        if not hasattr(self, '_persistence_initialized'):
            logger.debug(f"Lazy-initializing persistence for {getattr(self, 'id', 'unknown')}")

            # Use class-level defaults if not overridden
            backend = getattr(self.__class__, '_persistence_backend', None)
            auto_persist = getattr(self.__class__, '_auto_persist', True)

            object.__setattr__(self, '_persistence_backend', backend or LocalStorage())
            object.__setattr__(self, '_auto_persist', auto_persist)
            object.__setattr__(self, '_persistence_enabled', True)
            object.__setattr__(self, '_persistence_initialized', True)

            # Auto-load on first initialization
            if self._auto_persist:
                logger.debug(f"Auto-loading state for {self.id}")
                self._safe_load()

    def _safe_save(self):
        """Save state to backend with error handling."""
        try:
            # DRY: Use existing Pydantic serialization with JSON-compatible mode
            state_data = self.state.model_dump(mode='json', exclude={'_scaffold_ref', '_dirty', '_last_modified', '_change_stack'})

            # Use scaffold.id as storage key (DRY)
            key = self.id

            self._persistence_backend.save(key, state_data)
            logger.debug(f"Auto-saved scaffold {key}")

        except Exception as e:
            logger.error(f"Failed to auto-save scaffold {self.id}: {e}")
            # Don't break scaffold functionality on save errors

    def _safe_load(self):
        """Load state from backend with error handling."""
        try:
            key = self.id
            state_data = self._persistence_backend.load(key)

            if state_data:
                # DRY: Use existing Pydantic validation
                restored_state = self.state.__class__.model_validate(state_data)
                self._scaffold_state = restored_state
                logger.debug(f"Auto-loaded scaffold {key}")

        except Exception as e:
            logger.debug(f"No existing state for scaffold {self.id}: {e}")
            # First run or no saved state - that's fine

    # Public API

    def save(self):
        """Manually save current state to backend."""
        self._safe_save()

    def load(self):
        """Manually load state from backend."""
        self._safe_load()

    def clear_persisted_state(self):
        """Clear persisted state from backend."""
        try:
            self._persistence_backend.delete(self.id)
        except Exception as e:
            logger.error(f"Failed to clear persisted state for {self.id}: {e}")

    @property
    def persistence_backend(self) -> PersistenceBackend:
        """Get the persistence backend."""
        self._ensure_persistence_initialized()
        return self._persistence_backend
