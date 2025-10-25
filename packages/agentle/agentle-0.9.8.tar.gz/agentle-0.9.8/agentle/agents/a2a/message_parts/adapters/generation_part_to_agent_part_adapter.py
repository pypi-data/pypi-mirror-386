import base64

from rsb.adapters.adapter import Adapter

from agentle.agents.a2a.message_parts.file_part import FilePart
from agentle.agents.a2a.message_parts.text_part import TextPart
from agentle.agents.a2a.models.file import File
from agentle.generations.models.message_parts.file import (
    FilePart as GenerationFilePart,
)
from agentle.generations.models.message_parts.text import TextPart as GenerationTextPart
from agentle.generations.models.message_parts.tool_execution_suggestion import (
    ToolExecutionSuggestion as GenerationToolExecutionSuggestion,
)
from agentle.generations.tools.tool import (
    Tool as GenerationTool,
)
from agentle.generations.tools.tool_execution_result import (
    ToolExecutionResult as GenerationToolExecutionResult,
)


class GenerationPartToAgentPartAdapter(
    Adapter[
        GenerationFilePart
        | GenerationTextPart
        | GenerationTool
        | GenerationToolExecutionSuggestion
        | GenerationToolExecutionResult,
        FilePart | TextPart,
    ]
):
    def adapt(
        self,
        _f: GenerationFilePart
        | GenerationTextPart
        | GenerationTool
        | GenerationToolExecutionSuggestion
        | GenerationToolExecutionResult,
    ) -> FilePart | TextPart:
        match _f:
            case GenerationFilePart():
                data = _f.data
                if isinstance(data, str):
                    data = base64.b64decode(data)
                return FilePart(
                    type=_f.type,
                    file=File(
                        bytes=base64.b64encode(data).decode("utf-8"),
                    ),
                )
            case GenerationTextPart():
                return TextPart(text=_f.text)
            case GenerationTool():
                raise NotImplementedError("Tool declarations are not supported")
            case GenerationToolExecutionResult():
                raise NotImplementedError("Tool execution results are not supported.")
            case GenerationToolExecutionSuggestion():
                raise NotImplementedError("Tool executions are not supported")
