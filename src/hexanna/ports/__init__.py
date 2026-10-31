"""Ports / Abstract protocols for Hexanna IIVX."""

from hexanna.ports.data_engine import IDataEngine
from hexanna.ports.llm_gateway import ILLMGateway
from hexanna.ports.telemetry import ITelemetrySampler
from hexanna.ports.chat_history import IChatHistoryRepository

__all__ = ["IDataEngine", "ILLMGateway", "ITelemetrySampler", "IChatHistoryRepository"]
