from abc import ABC, abstractmethod
from typing import Any

from dhenara.ai.types.genai.ai_model import AIModelEndpoint
from dhenara.ai.types.genai.dhenara.request import (
    FormattedPrompt,
    FunctionDefinition,
    FunctionParameter,
    FunctionParameters,
    MessageItem,
    Prompt,
    PromptMessageRoleEnum,
    StructuredOutputConfig,
    SystemInstruction,
    ToolChoice,
    ToolDefinition,
)
from dhenara.ai.types.shared.file import GenericFile


class BaseFormatter(ABC):
    """
    Formatter for converting Dhenara types to provider-specific formats and vice versa.
    This decouples the conversion logic from the data classes themselves.
    """

    role_map = None

    @classmethod
    def format_prompt(
        cls,
        prompt: str | dict | Prompt,
        model_endpoint: AIModelEndpoint | None = None,
        **kwargs,
    ) -> FormattedPrompt:
        # First convert a prompt to Dhenara Prompt format
        if isinstance(prompt, str):
            # Formatted Prompt
            formatted_prompt = FormattedPrompt(
                role=PromptMessageRoleEnum.USER,
                text=prompt,
            )
            files = []
            max_words_file = None
        else:
            if isinstance(prompt, dict):
                pyd_prompt = Prompt(**prompt)
            elif isinstance(prompt, Prompt):
                pyd_prompt = prompt
            else:
                raise ValueError(f"format_prompt: unknown prompt type {type(prompt)}. prompt={prompt}")

            files = pyd_prompt.files
            max_words_text = pyd_prompt.config.max_words_text if pyd_prompt.config else None
            max_words_file = pyd_prompt.config.max_words_file if pyd_prompt.config else None

            role = pyd_prompt.role
            formatted_text = pyd_prompt.get_formatted_text(
                max_words=max_words_text,
                **kwargs,
            )
            # Formatted Prompt
            formatted_prompt = FormattedPrompt(
                role=role,
                text=formatted_text,
            )

            # Do files sanity checks
            if (files and not isinstance(files, list)) or not all(isinstance(f, GenericFile) for f in files):
                raise ValueError(f"Invalid type {type(files)} for files. Should be list of GenericFile")

        # Convert dhenara formated prompt and files to provider format
        return cls.convert_prompt(
            formatted_prompt=formatted_prompt,
            model_endpoint=model_endpoint,
            files=files,
            max_words_file=max_words_file,
        )

    @classmethod
    def format_context(
        cls,
        context: list[str | dict | Prompt],
        model_endpoint: AIModelEndpoint | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        if not context:
            return []

        formatted_context = [
            cls.format_prompt(
                prompt=prompt,
                model_endpoint=model_endpoint,
                **kwargs,
            )
            for prompt in context
        ]
        return formatted_context

    @classmethod
    def join_instructions(
        cls,
        instructions: list[str | SystemInstruction] | str,
        model_endpoint: AIModelEndpoint | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        if not instructions:
            return None

        if isinstance(instructions, str):
            return instructions

        def _process_single_instruction(instr):
            if isinstance(instr, str):
                formatted = instr
            else:
                if isinstance(instr, SystemInstruction):
                    _pyd_instr = instr
                elif isinstance(instr, dict):
                    _pyd_instr = SystemInstruction(**instr)
                else:
                    raise ValueError(f"Illegal instruction type {type(instr)}")

                formatted = _pyd_instr.get_formatted_text(**kwargs)
            return formatted

        formatted_instructions = [_process_single_instruction(instr, **kwargs) for instr in instructions]

        joined = " ".join(formatted_instructions)

        return joined

    @classmethod
    def format_instructions(
        cls,
        instructions: list[str | dict | Prompt] | str,
        model_endpoint: AIModelEndpoint | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        if not instructions:
            return None

        # Convert instructions to  Dhenara Promot
        joined_instructions = cls.join_instructions(instructions, **kwargs)

        # Formatted Prompt
        formatted_prompt = FormattedPrompt(
            role=PromptMessageRoleEnum.SYSTEM,
            text=joined_instructions,
        )

        # Convert Dhenara prompt to provider prompt
        # NOTE: Not using `convert_prompt` as some models ( Eg: Beta models) need special handling for instruction
        return cls.convert_instruction_prompt(
            formatted_prompt=formatted_prompt,
            model_endpoint=model_endpoint,
        )

    @classmethod
    def format_messages(
        cls,
        messages: list[MessageItem],
        model_endpoint: AIModelEndpoint | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Convert a list of MessageItem objects to provider-specific message format.

        MessageItem can be:
        - Prompt: New user/system messages (may expand to multiple messages)
        - ChatResponseContentItem: Previous assistant responses (text, reasoning, tool calls, etc.)
        - ToolCallResult: Tool execution results
        - ToolCallResultsMessage: Grouped tool execution results emitted together

            This method delegates to provider-specific convert_dai_message_item_to_provider for each item.
            Note: convert_dai_message_item_to_provider can return either a single dict or a list of dicts
            (e.g., Prompt objects may expand to multiple messages like system + user).
        """
        if not messages:
            return []

        formatted_messages = []
        for msg_item in messages:
            formatted = cls.convert_dai_message_item_to_provider(
                message_item=msg_item,
                model_endpoint=model_endpoint,
                **kwargs,
            )
            # Handle both single dict and list of dicts
            if isinstance(formatted, list):
                formatted_messages.extend(formatted)
            else:
                formatted_messages.append(formatted)

        return formatted_messages

    @classmethod
    @abstractmethod
    def convert_dai_message_item_to_provider(
        cls,
        message_item: MessageItem,
        model_endpoint: AIModelEndpoint | None = None,
        **kwargs,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Convert a single MessageItem to provider-specific message format.

            This method should handle:
            - Prompt objects (via format_prompt internally) - may return list for system + user
            - ChatResponseContentItem union types (text, reasoning, tool calls, structured output, generic)
        - ToolCallResult objects (and grouped variants)

            Each provider must implement this to match their specific message format.

            Returns:
                Single dict or list of dicts (Prompt can expand to multiple messages)
        """
        pass

    @classmethod
    def format_tools(
        cls,
        tools: list[ToolDefinition] | None,
        model_endpoint: AIModelEndpoint | None = None,
    ):
        if tools:
            return [
                cls.format_tool(
                    tool=tool,
                    model_endpoint=model_endpoint,
                )
                for tool in tools
            ]

    @classmethod
    def format_tool(
        cls,
        tool: ToolDefinition,
        model_endpoint: AIModelEndpoint | None = None,
    ) -> Any:
        return cls.convert_tool(
            tool=tool,
            model_endpoint=model_endpoint,
        )

    @classmethod
    def format_tool_choice(
        cls,
        tool_choice: ToolChoice,
        model_endpoint: AIModelEndpoint | None = None,
    ) -> Any:
        return cls.convert_tool_choice(
            tool_choice=tool_choice,
            model_endpoint=model_endpoint,
        )

    @classmethod
    def format_structured_output(
        cls,
        structured_output: StructuredOutputConfig,
        model_endpoint: AIModelEndpoint | None = None,
    ) -> dict[str, Any]:
        return cls.convert_structured_output(
            structured_output=structured_output,
            model_endpoint=model_endpoint,
        )

    # Abstract methods
    @classmethod
    @abstractmethod
    def convert_prompt(
        cls,
        formatted_prompt: FormattedPrompt,
        model_endpoint: AIModelEndpoint | None = None,
        files: list[GenericFile] | None = None,
        max_words_file: int | None = None,
    ) -> dict[str, Any]:
        """Convert prompt to provider format"""
        pass

    @classmethod
    @abstractmethod
    def convert_instruction_prompt(
        cls,
        formatted_prompt: FormattedPrompt,
        model_endpoint: AIModelEndpoint | None = None,
    ) -> dict[str, Any]:
        """Convert instruction prompt to provider format"""
        pass

    @classmethod
    @abstractmethod
    def convert_files_to_provider_content(
        cls,
        files: list[GenericFile],
        model_endpoint: AIModelEndpoint | None = None,
        max_words: int | None = None,
    ) -> list[dict[str, Any]]:
        """Convert File content to provider format"""
        pass

    # -------------------------------------------------------------------------
    # Tools & Structured output (INPUT to model - tool/function DEFINITIONS)
    #
    # These methods convert tool/function/structured-output SCHEMAS that we send
    # TO the model in API requests (not tool CALLS from model responses).
    #
    # For converting tool CALLS from ChatResponseChoice (model's response),
    # see message converters (e.g., OpenAIMessageConverter.dai_choice_to_provider_message).
    # -------------------------------------------------------------------------
    @classmethod
    @abstractmethod
    def convert_function_parameter(
        cls,
        param: FunctionParameter,
        model_endpoint: AIModelEndpoint | None = None,
    ) -> dict[str, Any]:
        """Convert a single FunctionParameter to provider format (for API request input)"""
        pass

    @classmethod
    @abstractmethod
    def convert_function_parameters(
        cls,
        params: FunctionParameters,
        model_endpoint: AIModelEndpoint | None = None,
    ) -> dict[str, Any]:
        """Convert FunctionParameters to provider format (for API request input)"""
        pass

    @classmethod
    @abstractmethod
    def convert_function_definition(
        cls,
        func_def: FunctionDefinition,
        model_endpoint: AIModelEndpoint | None = None,
    ) -> dict[str, Any]:
        """Convert FunctionDefinition to provider format (for API request input)"""
        pass

    @classmethod
    @abstractmethod
    def convert_tool(
        cls,
        tool: ToolDefinition,
        model_endpoint: AIModelEndpoint | None = None,
    ) -> Any:
        """Convert ToolDefinition to provider format (for API request input)"""
        pass

    @classmethod
    @abstractmethod
    def convert_tool_choice(
        cls,
        tool_choice: ToolChoice,
        model_endpoint: AIModelEndpoint | None = None,
    ) -> Any:
        """Convert ToolChoice to provider format (for API request input)"""
        pass

    @classmethod
    @abstractmethod
    def convert_structured_output(
        cls,
        structured_output: StructuredOutputConfig,
        model_endpoint: AIModelEndpoint | None = None,
    ) -> dict[str, Any]:
        """Convert StructuredOutputConfig to provider format (for API request input)"""
        pass
