"""OJIN Persona message definitions and handlers.

This module contains message classes and utilities for handling communication
with the OJIN Persona service, including audio input messages, cancellation
messages, and video response messages.
"""
import base64
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from ojin.entities.interaction_messages import (
    EndInteraction,
    EndInteractionMessage,
    CancelInteractionInput,
    InteractionInput,
    InteractionInputMessage,
    InteractionResponseMessage,
)


class OjinPersonaMessage(BaseModel):
    """Base class for all Ojin Persona messages.

    All messages exchanged with the Ojin Persona backend inherit from this class.
    """

    def to_proxy_message(self) -> BaseModel:
        """Convert the message to a proxy message format.
   
        This method must be implemented by subclasses to define how the specific
        message type should be converted to its corresponding proxy message format.
   
        Returns:
        BaseModel: The proxy message representation of this message.
       
        Raises:
        NotImplementedError: Always raised as this method must be implemented
                          by concrete subclasses.

        """
        raise NotImplementedError


class OjinPersonaSessionReadyMessage(OjinPersonaMessage):
    """Message to start a new interaction with an Ojin Persona.

    Contains the ID of the persona to interact with.
    """
    parameters: Dict[str, Any]|None

class OjinPersonaSessionReadyPing(OjinPersonaMessage):
    """Ping message used to check session readiness with the Ojin Persona backend."""


class OjinPersonaInteractionResponseMessage(OjinPersonaMessage):
    """Response message containing video data from the persona.

    Contains the interaction ID, persona ID, and the video data as bytes.
    """

    interaction_id: str
    video_frame_bytes: bytes
    is_final_response: bool = False
    index: int

    @classmethod
    def from_proxy_message(cls, proxy_message: InteractionResponseMessage):
        """Create an instance from a proxy message response.
   
        Extracts video frame data and metadata from an InteractionResponseMessage
        to construct a new instance of this class.
   
        Args:
        proxy_message (InteractionResponseMessage): The proxy message containing
                                                  interaction response data with
                                                  video payload and metadata.
   
        Returns:
        cls: A new instance created from the proxy message data, containing
            the interaction ID, video frame bytes, and final response flag.

        """
        return cls(
            interaction_id=proxy_message.payload.interaction_id,
            video_frame_bytes=proxy_message.payload.payload,
            is_final_response=proxy_message.payload.is_final_response,
            index=proxy_message.payload.index
        )


class OjinPersonaCancelInteractionMessage(OjinPersonaMessage):
    """Message to cancel an interaction."""

    def to_proxy_message(self) -> CancelInteractionInput:
        """Convert the cancel message to a proxy message format.
   
        Creates a CancelInteractionInput message with the interaction ID and
        current timestamp to request cancellation of an ongoing interaction.
           
        Returns:
            CancelInteractionInput: A cancellation message containing the
                                   interaction ID and timestamp for the proxy
                                   service to process the cancellation request.

        """
        return CancelInteractionInput(
            timestamp=int(time.monotonic() * 1000),
        )

class OjinPersonaEndInteractionMessage(OjinPersonaMessage):
    """Message to cancel an interaction."""

    def to_proxy_message(self) -> EndInteractionMessage:
        """Convert the cancel message to a proxy message format.
   
        Creates a CancelInteractionInput message with the interaction ID and
        current timestamp to request cancellation of an ongoing interaction.
           
        Returns:
            CancelInteractionInput: A cancellation message containing the
                                   interaction ID and timestamp for the proxy
                                   service to process the cancellation request.

        """
        return EndInteractionMessage(
            payload=EndInteraction(
                timestamp=int(time.monotonic() * 1000),
            )
        )


class OjinPersonaInteractionInputMessage(OjinPersonaMessage):
    """Message containing audio input for the persona.

    Contains the audio data as bytes and a flag indicating if this is the last input.
    """

    audio_int16_bytes: bytes
    params: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional. Additional parameters for the interaction",
    )

    def to_proxy_message(self) -> BaseModel:
        """Convert the audio message to a proxy message format.
   
        Creates an InteractionInputMessage containing audio data encoded as base64,
        along with metadata such as interaction ID, timing information, and optional
        frame parameters.
   
        Returns:
        BaseModel: An InteractionInputMessage instance containing the encoded
                 audio data and associated metadata for transmission to the
                 proxy service.

        """        
        payload = InteractionInput(
            payload_type="audio",
            payload=self.audio_int16_bytes,
            timestamp=int(time.monotonic() * 1000),
            params=self.params,
        )
        return InteractionInputMessage(
            payload=payload,
        )



class IOjinPersonaClient(ABC):
    """Interface for Ojin Persona client communication.

    Defines the contract for sending and receiving messages to/from the Ojin Persona
    client.
    """

    @abstractmethod
    async def connect(self) -> None:
        """Connect the client to the proxy."""

    @abstractmethod
    async def send_message(self, message: BaseModel) -> None:
        """Send a message to the server.

        Args:
           message: The message to send.

        """

    @abstractmethod 
    async def start_interaction(self):
        """Create a UUID for server interactions.

        Returns:
            The UUID.

        """

    @abstractmethod
    async def receive_message(self) -> BaseModel|None:
        """Receive a message from the server.

        Returns:
            The received message.

        """

    @abstractmethod
    async def close(self) -> None:
        """Close the client."""
