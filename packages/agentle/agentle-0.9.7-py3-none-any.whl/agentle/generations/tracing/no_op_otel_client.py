"""
Implementação no-op do cliente OTel para casos onde telemetria está desabilitada.

Este módulo fornece uma implementação que não realiza nenhuma operação real,
servindo como um stub quando a telemetria não está configurada ou foi desabilitada.
"""

from typing import Any, Literal, Optional, AsyncGenerator
from datetime import datetime
from collections.abc import Mapping, Sequence

from rsb.models.base_model import BaseModel

from .otel_client import OtelClient, TraceContext, GenerationContext


class NoOpOtelClient(BaseModel, OtelClient):
    """
    Implementação no-op do OtelClient para casos onde telemetria está desabilitada.

    Esta implementação não realiza nenhuma operação real, servindo como um
    stub quando a telemetria não está configurada ou foi desabilitada.
    """

    type: Literal["no-op"] = "no-op"

    async def trace_context(
        self,
        *,
        name: str,
        input_data: Mapping[str, Any],
        metadata: Optional[Mapping[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[Sequence[str]] = None,
    ) -> AsyncGenerator[Optional[TraceContext], None]:
        """Contexto no-op que não faz nada."""
        yield None

    async def generation_context(
        self,
        *,
        trace_context: Optional[TraceContext] = None,
        name: str,
        model: str,
        provider: str,
        input_data: Mapping[str, Any],
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> AsyncGenerator[Optional[GenerationContext], None]:
        """Contexto no-op que não faz nada."""
        yield None

    async def update_generation(
        self,
        generation_context: GenerationContext,
        *,
        output_data: Mapping[str, Any],
        usage_details: Optional[Mapping[str, Any]] = None,
        cost_details: Optional[Mapping[str, Any]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        end_time: Optional[datetime] = None,
    ) -> None:
        """Atualização no-op."""
        pass

    async def update_trace(
        self,
        trace_context: TraceContext,
        *,
        output_data: Any,
        success: bool = True,
        metadata: Optional[Mapping[str, Any]] = None,
        end_time: Optional[datetime] = None,
    ) -> None:
        """Atualização no-op."""
        pass

    async def add_trace_score(
        self,
        trace_context: TraceContext,
        *,
        name: str,
        value: float | str,
        comment: Optional[str] = None,
    ) -> None:
        """Pontuação no-op."""
        pass

    async def handle_error(
        self,
        trace_context: Optional[TraceContext],
        generation_context: Optional[GenerationContext],
        error: Exception,
        start_time: datetime,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> None:
        """Tratamento de erro no-op."""
        pass

    async def flush(self) -> None:
        """Flush no-op."""
        pass

    @property
    def is_enabled(self) -> bool:
        """Sempre retorna False para no-op client."""
        return False
