"""
Thread accessor for Agent.

Provides readonly access to current and historical thread states.
"""

from typing import TYPE_CHECKING, Optional
import logging

if TYPE_CHECKING:
    from egregore.core.messaging import ProviderThread

logger = logging.getLogger(__name__)


class ThreadAccessor:
    """
    Accessor for ProviderThread from Agent.

    Provides readonly access to current and historical thread states without
    side effects like episode incrementing.
    """

    def __init__(self, agent):
        """Initialize thread accessor with reference to agent."""
        self._agent = agent
        self._token_counter = None

    def _get_token_counter(self):
        """Lazy initialization of token counter."""
        if self._token_counter is None:
            from egregore.providers.core.token_counting import TokenCountingManager
            self._token_counter = TokenCountingManager()
        return self._token_counter

    def _populate_usage(self, thread: "ProviderThread") -> None:
        """
        Populate Usage objects for all messages in thread.

        Uses agent's configured model for token counting.

        Args:
            thread: ProviderThread to populate with usage data
        """
        from egregore.core.messaging import Usage, SystemHeader, ClientRequest, ProviderResponse

        # Get model and provider from agent
        provider = self._agent.provider
        if not provider or not provider.model:
            logger.warning("No model configured, skipping usage population")
            return

        model = provider.model
        provider_name = provider.name

        # Count tokens per message
        for message in thread.messages:
            try:
                # Extract text content from message for counting
                text_parts = []
                for content_block in message.content:
                    if hasattr(content_block, 'content') and isinstance(content_block.content, str):
                        text_parts.append(content_block.content)

                if not text_parts:
                    message.usage = Usage.empty()
                    continue

                full_text = '\n'.join(text_parts)

                # Count tokens
                counter = self._get_token_counter()
                tokens = counter.count_text(
                    full_text,
                    model=model,
                    provider=provider_name
                )

                # Populate usage based on message type
                if isinstance(message, (SystemHeader, ClientRequest)):
                    # Input messages
                    message.usage = Usage(
                        input_tokens=tokens,
                        output_tokens=0,
                        total_tokens=tokens
                    )
                elif isinstance(message, ProviderResponse):
                    # Output messages
                    message.usage = Usage(
                        input_tokens=0,
                        output_tokens=tokens,
                        total_tokens=tokens
                    )
                else:
                    message.usage = Usage.empty()

            except Exception as e:
                logger.warning(f"Failed to count tokens for message: {e}")
                message.usage = Usage.empty()

    @property
    def current(self) -> "ProviderThread":
        """
        Get current thread with usage populated.

        Returns what would be sent to LLM at this moment, with
        token usage calculated based on agent's configured model.

        Returns:
            Current ProviderThread with usage aggregation
        """
        from egregore.core.agent.message_scheduler import MessageScheduler

        scheduler = MessageScheduler(self._agent.context._context)
        thread = scheduler.render_readonly()
        self._populate_usage(thread)
        return thread

    def at_snapshot(self, snapshot_id: str) -> Optional["ProviderThread"]:
        """
        Get thread for a specific snapshot with usage populated.

        Args:
            snapshot_id: Snapshot identifier

        Returns:
            ProviderThread for that snapshot with usage data, or None if not found
        """
        if not hasattr(self._agent, 'history'):
            return None

        # Load snapshot
        snapshot = self._agent.history.get_snapshot_by_id(snapshot_id)
        if not snapshot:
            return None

        # Create scheduler from snapshot context
        from egregore.core.agent.message_scheduler import MessageScheduler
        scheduler = MessageScheduler(snapshot.full_context)
        thread = scheduler.render_readonly()
        self._populate_usage(thread)
        return thread
