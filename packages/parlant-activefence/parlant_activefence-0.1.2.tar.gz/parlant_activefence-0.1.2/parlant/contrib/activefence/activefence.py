"""
ActiveFence integration module.

This module provides the ActiveFence class for integrating with ActiveFence services.
"""

import os
from typing import Any, Optional

from activefence_client_sdk.client import ActiveFenceClient as SDKClient
from activefence_client_sdk.client import AnalysisContext
from activefence_client_sdk.models import Actions, EvaluateMessageResponse

import parlant.sdk as p

from .moderation_service import ActiveFenceNLPServiceWrapper


class ActiveFence:
    def __init__(
        self, api_key: Optional[str] = None, app_name: Optional[str] = None, blocked_message: Optional[str] = None
    ):
        """
        Initialize the ActiveFence client.

        Args:
            api_key: ActiveFence API key for authentication. If not provided, will be loaded from env var.
            app_name: Application name for identification. If not provided, will be loaded from env var.
            blocked_message: Message to display when content is blocked. If not provided, will be loaded from ACTIVEFENCE_BLOCKED_MESSAGE env var, or defaults to 'The generated message was blocked by guardrails.'
        """
        self.api_key = api_key
        self.app_name = app_name
        self.blocked_message = blocked_message or os.getenv(
            "ACTIVEFENCE_BLOCKED_MESSAGE", "The generated message was blocked by guardrails."
        )
        self._client = SDKClient(api_key=self.api_key, app_name=self.app_name)

    async def check_message(self, message: str, session_id: str, agent_id: str) -> EvaluateMessageResponse:
        analysis_context = AnalysisContext(
            user_id=agent_id,
            session_id=session_id,
        )
        try:
            analysis_result = await self._client.evaluate_response(message, analysis_context)
        except Exception as e:
            raise Exception("Moderation service failure (ActiveFence)") from e

        return analysis_result

    async def check_message_compliance(
        self, ctx: p.LoadedContext, payload: Any, exc: Exception | None
    ) -> p.EngineHookResult:
        generated_message = payload

        result = await self.check_message(generated_message, ctx.session.id, ctx.agent.id)
        if result.action == Actions.DETECT:
            ctx.logger.warning(f"Detected a non-compliant message: '{generated_message}': {result.detections}.")
        elif result.action in (Actions.BLOCK, Actions.MASK):
            message = result.action_text if result.action == Actions.MASK else self.blocked_message
            ctx.logger.warning(f"Prevented sending a non-compliant message: '{generated_message}'.")
            await ctx.session_event_emitter.emit_message_event(
                correlation_id=ctx.correlator.correlation_id,
                data=p.MessageEventData(
                    message=message,
                    participant={"id": ctx.agent.id, "display_name": ctx.agent.name},
                ),
            )
            await ctx.session_event_emitter.emit_status_event(
                correlation_id=ctx.correlator.correlation_id,
                data={
                    "status": "ready",
                    "data": {},
                },
            )
            return p.EngineHookResult.BAIL  # Do not send this message

        return p.EngineHookResult.CALL_NEXT  # Continue with the normal process

    async def configure_container(self, container: p.Container) -> p.Container:
        # Get the original NLPService and logger from the container
        original_nlp_service = container[p.NLPService]
        logger = container[p.Logger]

        # Create a wrapper that overrides get_moderation_service
        wrapped_nlp_service = ActiveFenceNLPServiceWrapper(original_nlp_service, self._client, logger)

        container[p.NLPService] = wrapped_nlp_service
        container[p.EngineHooks].on_message_generated.append(self.check_message_compliance)

        return container
