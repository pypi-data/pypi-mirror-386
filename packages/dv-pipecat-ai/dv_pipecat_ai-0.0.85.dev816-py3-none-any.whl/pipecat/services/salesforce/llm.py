#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Salesforce Agent API LLM service implementation."""

import asyncio
import json
import os
import time
from typing import Any, Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass

import httpx
from loguru import logger

from pipecat.frames.frames import (
    Frame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    LLMMessagesFrame,
    LLMTextFrame,
    LLMUpdateSettingsFrame,
)
from pipecat.processors.aggregators.openai_llm_context import (
    OpenAILLMContext,
    OpenAILLMContextFrame,
)
from pipecat.processors.frame_processor import FrameDirection
from pipecat.services.llm_service import LLMService
from pipecat.services.openai.llm import (
    OpenAIAssistantContextAggregator,
    OpenAIContextAggregatorPair,
    OpenAIUserContextAggregator,
)
from pipecat.processors.aggregators.llm_response import (
    LLMAssistantAggregatorParams,
    LLMUserAggregatorParams,
)
from env_config import api_config


@dataclass
class SalesforceSessionInfo:
    """Information about an active Salesforce Agent session."""

    session_id: str
    agent_id: str
    created_at: float
    last_used: float


class SalesforceAgentLLMService(LLMService):
    """Salesforce Agent API LLM service implementation.

    This service integrates with Salesforce Agent API to provide conversational
    AI capabilities using Salesforce's Agentforce platform. It follows the same
    pattern as Vistaar LLM service for proper frame processing.
    """

    def __init__(
        self,
        *,
        model: str = "salesforce-agent",
        session_timeout_secs: float = 3600.0,
        **kwargs,
    ):
        """Initialize Salesforce Agent LLM service.

        Reads configuration from environment variables:
        - SALESFORCE_AGENT_ID: The Salesforce agent ID to interact with
        - SALESFORCE_API_KEY: OAuth access token (optional, will use client credentials if not provided)
        - SALESFORCE_ORG_DOMAIN: Salesforce org domain (e.g., https://myorg.my.salesforce.com)
        - SALESFORCE_CLIENT_ID: Connected app client ID for OAuth
        - SALESFORCE_CLIENT_SECRET: Connected app client secret for OAuth
        - SALESFORCE_API_HOST: Salesforce API host (default: https://api.salesforce.com)

        Args:
            model: The model name (defaults to "salesforce-agent").
            session_timeout_secs: Session timeout in seconds (default: 1 hour).
            **kwargs: Additional arguments passed to parent LLMService.
        """
        # Initialize parent LLM service
        super().__init__(**kwargs)
            
        self._agent_id = api_config.SALESFORCE_AGENT_ID
        self._api_key = api_config.SALESFORCE_API_KEY
        self._org_domain = api_config.SALESFORCE_ORG_DOMAIN
        self._client_id = api_config.SALESFORCE_CLIENT_ID
        self._client_secret = api_config.SALESFORCE_CLIENT_SECRET
        self._api_host = api_config.SALESFORCE_API_HOST


        # Validate required environment variables
        required_vars = {
            "SALESFORCE_AGENT_ID": self._agent_id,
            "SALESFORCE_ORG_DOMAIN": self._org_domain,
            "SALESFORCE_CLIENT_ID": self._client_id,
            "SALESFORCE_CLIENT_SECRET": self._client_secret,
        }

        missing_vars = [var for var, value in required_vars.items() if not value]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        logger.info(f"Salesforce LLM initialized - Agent ID: {self._agent_id}")

        self._session_timeout_secs = session_timeout_secs

        # Session management
        self._sessions: Dict[str, SalesforceSessionInfo] = {}
        self._current_session_id: Optional[str] = None

        # HTTP client for API calls
        self._http_client = httpx.AsyncClient(timeout=30.0)
        

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._cleanup_sessions()
        await self._http_client.aclose()

    def can_generate_metrics(self) -> bool:
        """Check if this service can generate processing metrics."""
        return True

    async def _get_access_token(self) -> str:
        """Get OAuth access token using client credentials."""
        if self._api_key and not self._api_key.startswith("Bearer"):
            return self._api_key

        token_url = f"{self._org_domain}/services/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }

        try:
            response = await self._http_client.post(token_url, data=data)
            response.raise_for_status()
            token_data = response.json()
            return token_data["access_token"]
        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            raise

    async def _create_session(self) -> str:
        """Create a new Salesforce Agent session."""
        access_token = await self._get_access_token()
        session_url = f"{self._api_host}/einstein/ai-agent/v1/agents/{self._agent_id}/sessions"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        external_session_key = f"pipecat-{int(time.time())}-{id(self)}"

        payload = {
            "externalSessionKey": external_session_key,
            "instanceConfig": {"endpoint": self._org_domain},
            "tz": "America/Los_Angeles",
            "variables": [{"name": "$Context.EndUserLanguage", "type": "Text", "value": "en_US"}],
            "featureSupport": "Streaming",
            "streamingCapabilities": {"chunkTypes": ["Text"]},
            "bypassUser": True,
        }

        try:
            response = await self._http_client.post(session_url, headers=headers, json=payload)
            response.raise_for_status()
            session_data = response.json()
            session_id = session_data["sessionId"]

            # Store session info
            current_time = time.time()
            self._sessions[session_id] = SalesforceSessionInfo(
                session_id=session_id,
                agent_id=self._agent_id,
                created_at=current_time,
                last_used=current_time,
            )

            logger.debug(f"Created Salesforce Agent session: {session_id}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to create Salesforce Agent session: {e}")
            raise

    async def _get_or_create_session(self) -> str:
        """Get existing session or create a new one."""
        current_time = time.time()

        # Check if current session is still valid
        if self._current_session_id and self._current_session_id in self._sessions:
            session = self._sessions[self._current_session_id]
            if current_time - session.last_used < self._session_timeout_secs:
                session.last_used = current_time
                return self._current_session_id
            else:
                # Session expired, remove it
                del self._sessions[self._current_session_id]
                self._current_session_id = None

        # Create new session
        self._current_session_id = await self._create_session()
        return self._current_session_id

    async def _cleanup_sessions(self):
        """Clean up expired sessions."""
        current_time = time.time()
        expired_sessions = []

        for session_id, session in self._sessions.items():
            if current_time - session.last_used > self._session_timeout_secs:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            try:
                # End the session via API
                access_token = await self._get_access_token()
                url = f"{self._api_host}/einstein/ai-agent/v1/sessions/{session_id}"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "x-session-end-reason": "UserRequest",
                }
                await self._http_client.delete(url, headers=headers)
            except Exception as e:
                logger.warning(f"Failed to end session {session_id}: {e}")
            finally:
                del self._sessions[session_id]
                if self._current_session_id == session_id:
                    self._current_session_id = None

    def _extract_user_message(self, context: OpenAILLMContext) -> str:
        """Extract the last user message from context.
        
        Similar to Vistaar pattern - extract only the most recent user message.
        
        Args:
            context: The OpenAI LLM context containing messages.
            
        Returns:
            The last user message as a string.
        """
        messages = context.get_messages()
        
        # Find the last user message (iterate in reverse for efficiency)
        for message in reversed(messages):
            if message.get("role") == "user":
                content = message.get("content", "")
                
                # Handle content that might be a list (for multimodal messages)
                if isinstance(content, list):
                    text_parts = [
                        item.get("text", "") for item in content if item.get("type") == "text"
                    ]
                    content = " ".join(text_parts)
                
                if isinstance(content, str):
                    return content.strip()
        
        return ""

    def _generate_sequence_id(self) -> int:
        """Generate a sequence ID for the message."""
        return int(time.time() * 1000) % 2147483647  # Keep within int32 range

    async def _stream_salesforce_response(self, session_id: str, user_message: str) -> AsyncGenerator[str, None]:
        """Stream response from Salesforce Agent API."""
        access_token = await self._get_access_token()
        url = f"{self._api_host}/einstein/ai-agent/v1/sessions/{session_id}/messages/stream"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

        message_data = {
            "message": {
                "sequenceId": self._generate_sequence_id(),
                "type": "Text",
                "text": user_message
            },
            "variables": [
                {
                    "name": "$Context.EndUserLanguage",
                    "type": "Text",
                    "value": "en_US"
                }
            ]
        }

        try:
            logger.info(f"🌐 Salesforce API request: {user_message[:50]}...")
            async with self._http_client.stream("POST", url, headers=headers, json=message_data) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if not line:
                        continue

                    # Parse SSE format
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            message = data.get("message", {})
                            message_type = message.get("type")

                            if message_type == "TextChunk":
                                content = message.get("text", "") or message.get("message", "")
                                if content:
                                    yield content
                            elif message_type == "EndOfTurn":
                                logger.info("🏁 Salesforce response complete")
                                break
                            elif message_type == "Inform":
                                # Skip INFORM events to avoid duplication
                                continue

                        except json.JSONDecodeError as e:
                            logger.warning(f"JSON decode error: {e}, line: {line}")
                            continue

        except Exception as e:
            logger.error(f"Failed to stream from Salesforce Agent API: {e}")
            raise

    async def _process_context(self, context: OpenAILLMContext):
        """Process the LLM context and generate streaming response.
        
        Following Vistaar pattern for simple, direct processing.

        Args:
            context: The OpenAI LLM context containing messages to process.
        """
        logger.info(f"🔄 Salesforce processing context with {len(context.get_messages())} messages")
        
        # Extract user message from context first
        user_message = self._extract_user_message(context)
        
        if not user_message:
            logger.warning("Salesforce: No user message found in context")
            return
        
        try:
            logger.info(f"🎯 Salesforce extracted query: {user_message}")
            
            # Start response 
            await self.push_frame(LLMFullResponseStartFrame())
            await self.push_frame(LLMFullResponseStartFrame(),FrameDirection.UPSTREAM)
            await self.start_processing_metrics()
            await self.start_ttfb_metrics()
            
            # Get or create session
            session_id = await self._get_or_create_session()
            
            first_chunk = True
            
            # Stream the response
            async for text_chunk in self._stream_salesforce_response(session_id, user_message):
                if first_chunk:
                    await self.stop_ttfb_metrics()
                    first_chunk = False
                
                # Push each text chunk as it arrives
                await self.push_frame(LLMTextFrame(text=text_chunk))
            
        except Exception as e:
            logger.error(f"Salesforce context processing error: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Salesforce traceback: {traceback.format_exc()}")
            raise
        finally:
            await self.stop_processing_metrics()
            await self.push_frame(LLMFullResponseEndFrame())
            await self.push_frame(LLMFullResponseEndFrame(), FrameDirection.UPSTREAM)

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Process frames for LLM completion requests.
        
        Following the exact Vistaar pattern - call super() for non-context frames only.

        Args:
            frame: The frame to process.
            direction: The direction of frame processing.
        """
        context = None
        if isinstance(frame, OpenAILLMContextFrame):
            context = frame.context
            logger.info(f"🔍 Received OpenAILLMContextFrame with {len(context.get_messages())} messages")
        elif isinstance(frame, LLMMessagesFrame):
            context = OpenAILLMContext.from_messages(frame.messages)
            logger.info(f"🔍 Received LLMMessagesFrame with {len(frame.messages)} messages")
        elif isinstance(frame, LLMUpdateSettingsFrame):
            # Call super for settings frames and update settings
            await super().process_frame(frame, direction)
            settings = frame.settings
            logger.debug(f"Updated Salesforce settings: {settings}")
        else:
            # For non-context frames, call super and push them downstream
            await super().process_frame(frame, direction)
            await self.push_frame(frame, direction)

        if context:
            try:
                await self._process_context(context)
            except httpx.TimeoutException:
                logger.error("Timeout while processing Salesforce request")
                await self._call_event_handler("on_completion_timeout")
            except Exception as e:
                logger.error(f"Error processing Salesforce request: {e}")
                raise

    def create_context_aggregator(
        self,
        context: OpenAILLMContext,
        *,
        user_params: LLMUserAggregatorParams = LLMUserAggregatorParams(),
        assistant_params: LLMAssistantAggregatorParams = LLMAssistantAggregatorParams(),
    ) -> OpenAIContextAggregatorPair:
        """Create context aggregators for Salesforce LLM.

        Since Salesforce uses OpenAI-compatible message format, we reuse OpenAI's
        context aggregators directly, similar to how Vistaar works.

        Args:
            context: The LLM context to create aggregators for.
            user_params: Parameters for user message aggregation.
            assistant_params: Parameters for assistant message aggregation.

        Returns:
            OpenAIContextAggregatorPair: A pair of OpenAI context aggregators,
            compatible with Salesforce's OpenAI-like message format.
        """
        context.set_llm_adapter(self.get_llm_adapter())
        user = OpenAIUserContextAggregator(context, params=user_params)
        assistant = OpenAIAssistantContextAggregator(context, params=assistant_params)
        return OpenAIContextAggregatorPair(_user=user, _assistant=assistant)

    def get_llm_adapter(self):
        """Get the LLM adapter for this service."""
        from pipecat.adapters.services.open_ai_adapter import OpenAILLMAdapter
        return OpenAILLMAdapter()

    async def close(self):
        """Close the HTTP client when the service is destroyed."""
        await self._cleanup_sessions()
        await self._http_client.aclose()

    def __del__(self):
        """Ensure the client is closed on deletion."""
        try:
            asyncio.create_task(self._http_client.aclose())
        except:
            pass