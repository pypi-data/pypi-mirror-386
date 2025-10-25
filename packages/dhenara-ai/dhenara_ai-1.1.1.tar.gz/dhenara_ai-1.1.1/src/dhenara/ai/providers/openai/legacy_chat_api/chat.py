import logging
from typing import Any

from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk, ChoiceDelta

from dhenara.ai.providers.openai import OpenAIClientBase
from dhenara.ai.providers.openai.message_converter import OpenAIMessageConverter
from dhenara.ai.types.genai import (
    AIModelCallResponse,
    AIModelCallResponseMetaData,
    ChatResponse,
    ChatResponseChoice,
    ChatResponseChoiceDelta,
    ChatResponseContentItem,
    ChatResponseContentItemDelta,
    ChatResponseReasoningContentItemDelta,
    ChatResponseTextContentItemDelta,
    ChatResponseUsage,
    StreamingChatResponse,
)
from dhenara.ai.types.genai.ai_model import AIModelAPIProviderEnum, AIModelProviderEnum
from dhenara.ai.types.shared.api import SSEErrorResponse

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
class OpenAIChatLEGACY(OpenAIClientBase):
    def get_api_call_params(
        self,
        prompt: dict | None,
        context: list[dict] | None = None,
        instructions: dict | None = None,
        messages: list | None = None,
    ) -> AIModelCallResponse:
        if not self._client:
            raise RuntimeError("Client not initialized. Use with 'async with' context manager")

        if self._input_validation_pending:
            raise ValueError("inputs must be validated with `self.validate_inputs()` before api calls")

        messages_list = []
        user = self.config.get_user()

        # Process instructions
        if instructions:
            messages_list.append(instructions)

        # Add previous messages and current prompt
        if messages is not None:
            # Convert MessageItem objects to OpenAI format
            formatted_messages = self.formatter.format_messages(
                messages=messages,
                model_endpoint=self.model_endpoint,
            )
            messages_list.extend(formatted_messages)
        else:
            if context:
                messages_list.extend(context)
            if prompt is not None:
                messages_list.append(prompt)

        # Prepare API call arguments
        chat_args: dict[str, Any] = {
            "model": self.model_name_in_api_calls,
            "messages": messages_list,
            "stream": self.config.streaming,
        }

        if user:
            if self.model_endpoint.api.provider != AIModelAPIProviderEnum.MICROSOFT_AZURE_AI:
                chat_args["safety_identifier"] = user

        max_output_tokens, _max_reasoning_tokens = self.config.get_max_output_tokens(self.model_endpoint.ai_model)

        if max_output_tokens is not None:
            if self.model_endpoint.api.provider != AIModelAPIProviderEnum.MICROSOFT_AZURE_AI:
                # NOTE: With resasoning models, max_output_tokens Deprecated in favour of max_completion_tokens
                chat_args["max_completion_tokens"] = max_output_tokens

            else:
                chat_args["max_tokens"] = max_output_tokens

        if self.config.reasoning and self.config.reasoning_effort is not None:
            chat_args["reasoning_effort"] = self.config.reasoning_effort

        if self.config.streaming:
            if self.model_endpoint.api.provider != AIModelAPIProviderEnum.MICROSOFT_AZURE_AI:
                chat_args["stream_options"] = {"include_usage": True}

        if self.config.options:
            chat_args.update(self.config.options)

        # ---  Tools ---
        if self.config.tools:
            chat_args["tools"] = self.formatter.format_tools(
                tools=self.config.tools,
                model_endpoint=self.model_endpoint,
            )

        if self.config.tool_choice:
            chat_args["tool_choice"] = self.formatter.format_tool_choice(
                tool_choice=self.config.tool_choice,
                model_endpoint=self.model_endpoint,
            )

        # --- Structured Output ---
        if self.config.structured_output:
            chat_args["response_format"] = self.formatter.format_structured_output(
                structured_output=self.config.structured_output,
                model_endpoint=self.model_endpoint,
            )

        return {"chat_args": chat_args}

    def do_api_call_sync(
        self,
        api_call_params: dict,
    ) -> AIModelCallResponse:
        chat_args = api_call_params["chat_args"]
        if self.model_endpoint.api.provider != AIModelAPIProviderEnum.MICROSOFT_AZURE_AI:
            response = self._client.chat.completions.create(**chat_args)
        else:
            response = self._client.complete(**chat_args)
        return response

    async def do_api_call_async(
        self,
        api_call_params: dict,
    ) -> AIModelCallResponse:
        chat_args = api_call_params["chat_args"]
        if self.model_endpoint.api.provider != AIModelAPIProviderEnum.MICROSOFT_AZURE_AI:
            response = await self._client.chat.completions.create(**chat_args)
        else:
            response = await self._client.complete(**chat_args)
        return response

    def do_streaming_api_call_sync(
        self,
        api_call_params,
    ) -> AIModelCallResponse:
        chat_args = api_call_params["chat_args"]
        if self.model_endpoint.api.provider != AIModelAPIProviderEnum.MICROSOFT_AZURE_AI:
            stream = self._client.chat.completions.create(**chat_args)
        else:
            stream = self._client.complete(**chat_args)

        return stream

    async def do_streaming_api_call_async(
        self,
        api_call_params,
    ) -> AIModelCallResponse:
        chat_args = api_call_params["chat_args"]
        if self.model_endpoint.api.provider != AIModelAPIProviderEnum.MICROSOFT_AZURE_AI:
            stream = await self._client.chat.completions.create(**chat_args)
        else:
            stream = await self._client.complete(**chat_args)

        return stream

    # -------------------------------------------------------------------------
    def parse_stream_chunk(
        self,
        chunk: ChatCompletionChunk,
    ) -> StreamingChatResponse | SSEErrorResponse | None:
        """Handle streaming response with progress tracking and final response"""
        processed_chunks = []

        self.streaming_manager.provider_metadata = None
        self.streaming_manager.persistant_choice_metadata_list = []

        if not self.streaming_manager.provider_metadata:  # Grab the metadata once
            self.streaming_manager.provider_metadata = {
                "id": chunk.id,
                "created": str(chunk.created),  # Microsoft sdk returns datetim obj
                "object": chunk.object if hasattr(chunk, "object") else None,
                "system_fingerprint": chunk.system_fingerprint if hasattr(chunk, "system_fingerprint") else None,
            }

        # Process usage
        if hasattr(chunk, "usage") and chunk.usage:  # Microsoft is slow in adopting openai changes 😶
            usage = ChatResponseUsage(
                total_tokens=chunk.usage.total_tokens,
                prompt_tokens=chunk.usage.prompt_tokens,
                completion_tokens=chunk.usage.completion_tokens,
            )
            self.streaming_manager.update_usage(usage)

        # Process content
        if chunk.choices:
            choice_deltas = []
            for choice in chunk.choices:
                # Only first chunk has few fields
                if len(self.streaming_manager.persistant_choice_metadata_list) < choice.index + 1:
                    self.streaming_manager.persistant_choice_metadata_list.append(
                        {
                            "role": choice.delta.role,
                            "refusal": choice.delta.refusal if hasattr(choice.delta, "refusal") else None,
                        }
                    )

                role = choice.delta.role or self.streaming_manager.persistant_choice_metadata_list[choice.index]["role"]

                choice_deltas.append(
                    ChatResponseChoiceDelta(
                        index=choice.index,
                        finish_reason=choice.finish_reason if hasattr(choice, "finish_reason") else None,
                        stop_sequence=None,
                        content_deltas=[
                            self.process_content_item_delta(
                                index=0,  # Only one content item. Might change with reasoing response?
                                role=role,
                                delta=choice.delta,
                            ),
                        ],
                        metadata={},
                    )
                )

            response_chunk = self.streaming_manager.update(choice_deltas=choice_deltas)
            stream_response = StreamingChatResponse(
                id=chunk.id,
                data=response_chunk,
            )

            processed_chunks.append(stream_response)

        return processed_chunks

    # -------------------------------------------------------------------------
    def _get_usage_from_provider_response(
        self,
        response: ChatCompletion,
    ) -> ChatResponseUsage:
        return ChatResponseUsage(
            total_tokens=response.usage.total_tokens,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
        )

    # -------------------------------------------------------------------------
    def parse_response(
        self,
        response: ChatCompletion,
    ) -> ChatResponse:
        """Parse the OpenAI response into our standard format"""
        usage, usage_charge = self.get_usage_and_charge(response)

        choices = []
        for choice in response.choices:
            content_items = self.process_content_item(
                index=0,  # Only one content item. Might change with reasoing response?
                role=choice.message.role,
                content_item=choice.message,
            )

            contents = content_items if isinstance(content_items, list) else [content_items]

            choice_obj = ChatResponseChoice(
                index=choice.index,
                finish_reason=choice.finish_reason if hasattr(choice, "finish_reason") else None,
                stop_sequence=None,
                contents=contents,
                metadata={},
            )
            choices.append(choice_obj)

        return ChatResponse(
            model=response.model,
            provider=self.model_endpoint.ai_model.provider,
            api_provider=self.model_endpoint.api.provider,
            usage=usage,
            usage_charge=usage_charge,
            choices=choices,
            metadata=AIModelCallResponseMetaData(
                streaming=False,
                duration_seconds=0,  # TODO
                provider_metadata={
                    "id": response.id,
                    "created": str(response.created),  # Microsoft sdk returns datetim obj
                    "object": response.object if hasattr(response, "object") else None,
                    # TODO: Move to choice
                    "system_fingerprint": response.system_fingerprint
                    if hasattr(response, "system_fingerprint")
                    else None,
                },
            ),
        )

    def process_content_item(
        self,
        index: int,
        role: str,
        content_item: ChatCompletionMessage,
    ) -> ChatResponseContentItem | list[ChatResponseContentItem]:
        # INFO: response type will vary with API/Model providers.
        # if isinstance(content_item, (ChatCompletionMessage, AzureChatResponseMessage)):

        converted_items = OpenAIMessageConverter.provider_message_to_content_items(
            message=content_item,
            role=role,
            index_start=index,
            ai_model_provider=self.model_endpoint.ai_model.provider,
            structured_output_config=self.config.structured_output,
        )

        if not converted_items:
            return self.get_unknown_content_type_item(
                index=index,
                role=role,
                unknown_item=content_item,
                streaming=False,
            )

        if len(converted_items) == 1:
            return converted_items[0]

        return converted_items

    # Streaming
    def process_content_item_delta(
        self,
        index: int,
        role: str,
        delta: ChoiceDelta,
    ) -> ChatResponseContentItemDelta:
        # if isinstance(delta, (ChoiceDelta, AzureStreamingChatResponseMessageUpdate)):
        if hasattr(delta, "content"):
            if self.model_endpoint.ai_model.provider == AIModelProviderEnum.DEEPSEEK:
                content = delta.content

                # Check for think tag markers
                think_start = "<think>" in content
                think_end = "</think>" in content

                # If we see a start tag, everything after it goes to reasoning
                if think_start:
                    self.streaming_manager.progress.in_thinking_block = True
                    # Split content at the tag
                    _, reasoning_part = content.split("<think>", 1)
                    return ChatResponseReasoningContentItemDelta(
                        index=index,
                        role=role,
                        thinking_text_delta=reasoning_part,
                    )

                # If we see an end tag, everything before it goes to reasoning
                elif think_end:
                    self.streaming_manager.progress.in_thinking_block = False
                    reasoning_part, answer_part = content.split("</think>", 1)
                    return (
                        ChatResponseReasoningContentItemDelta(
                            index=index,
                            role=role,
                            thinking_text_delta=reasoning_part,
                        )
                        if reasoning_part
                        else ChatResponseTextContentItemDelta(
                            index=index + 1,
                            role=role,
                            text_delta=answer_part,
                        )
                    )

                # If we're inside a thinking block, content goes to reasoning
                elif self.streaming_manager.progress.in_thinking_block:
                    return ChatResponseReasoningContentItemDelta(
                        index=index,
                        role=role,
                        thinking_text_delta=content,
                    )

                # Otherwise it's regular text content
                else:
                    return ChatResponseTextContentItemDelta(
                        index=index + 1,
                        role=role,
                        text_delta=content,
                    )
            else:
                return ChatResponseTextContentItemDelta(
                    index=index,
                    role=role,
                    text_delta=delta.content,
                )
        # TODO: Tools Not supported in streaming yet
        # elif hasattr(delta, "tool_calls") and delta.tool_calls:
        #    tool_call_deltas = []

        #    for tool_call in delta.tool_calls:
        #        tool_call_delta = {
        #            "id": tool_call.id if hasattr(tool_call, "id") else None,
        #            "type": "function",  # OpenAI currently only supports function type
        #            "function": {},
        #        }

        #        # Handle function name
        #        if hasattr(tool_call, "function") and hasattr(tool_call.function, "name"):
        #            tool_call_delta["function"]["name"] = tool_call.function.name

        #        # Handle function arguments (can be streamed)
        #        if hasattr(tool_call, "function") and hasattr(tool_call.function, "arguments"):
        #            tool_call_delta["function"]["arguments"] = tool_call.function.arguments

        #        tool_call_deltas.append(tool_call_delta)

        #    return ChatResponseToolCallContentItemDelta(
        #        index=index,
        #        role=role,
        #        tool_call_deltas=tool_call_deltas,
        #        metadata={},
        #    )

        else:
            # NOTE: There is no way to identify content type for OpenAI streaming response.
            # Also they sends few extra chuckw with no content.
            # Eg: The very first chunk will only have the `role` set (and role in other chunks will be None)
            # Therefore, dont't send a `ChatResponseGenericContentItemDelta`  here,
            # asit will messup streaming manager content updation

            return self.get_unknown_content_type_item(
                index=index,
                role=role,
                unknown_item=delta,
                streaming=True,
            )
