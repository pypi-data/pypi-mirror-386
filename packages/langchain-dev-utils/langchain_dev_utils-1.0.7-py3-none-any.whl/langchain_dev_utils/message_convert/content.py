from functools import reduce
from typing import AsyncIterator, Iterator, Sequence, Tuple, cast

from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessageChunk


def convert_reasoning_content_for_ai_message(
    model_response: AIMessage,
    think_tag: Tuple[str, str] = ("<think>", "</think>"),
) -> AIMessage:
    """Convert reasoning content in AI message to visible content.

    This function extracts reasoning content from the additional_kwargs of an AI message
    and merges it into the visible content, wrapping it with the specified tags.

    Args:
        model_response: AI message response from model
        think_tag: Tuple of (opening_tag, closing_tag) to wrap reasoning content

    Returns:
        AIMessage: Modified AI message with reasoning content in visible content

    Example:
        Basic usage with default tags:
        >>> from langchain_dev_utils.message_convert import convert_reasoning_content_for_ai_message
        >>> response = model.invoke("Explain quantum computing")
        >>> response = convert_reasoning_content_for_ai_message(response)
        >>> response.content

        Custom tags for reasoning content:
        >>> response = convert_reasoning_content_for_ai_message(
        ...     response, think_tag=('<reasoning>', '</reasoning>')
        ... )
        >>> response.content
    """
    if "reasoning_content" in model_response.additional_kwargs:
        model_response.content = f"{think_tag[0]}{model_response.additional_kwargs['reasoning_content']}{think_tag[1]}{model_response.content}"
    return model_response


def convert_reasoning_content_for_chunk_iterator(
    model_response: Iterator[BaseMessageChunk],
    think_tag: Tuple[str, str] = ("<think>", "</think>"),
) -> Iterator[BaseMessageChunk]:
    """Convert reasoning content for streaming response chunks.

    This function processes streaming response chunks and merges reasoning content
    into the visible content, wrapping it with the specified tags. It handles
    the first chunk, middle chunks, and last chunk differently to properly
    format the reasoning content.

    Args:
        model_response: Iterator of message chunks from streaming response
        think_tag: Tuple of (opening_tag, closing_tag) to wrap reasoning content

    Yields:
        BaseMessageChunk: Modified message chunks with reasoning content

    Example:
        Process streaming response:
        >>> from langchain_dev_utils.message_convert import convert_reasoning_content_for_chunk_iterator
        >>> for chunk in convert_reasoning_content_for_chunk_iterator(
        ...     model.stream("What is the capital of France?")
        ... ):
        ...     print(chunk.content, end="", flush=True)

        Custom tags for streaming:
        >>> for chunk in convert_reasoning_content_for_chunk_iterator(
        ...     model.stream("Explain quantum computing"),
        ...     think_tag=('<reasoning>', '</reasoning>')
        ... ):
        ...     print(chunk.content, end="", flush=True)
    """
    isfirst = True
    isend = True

    for chunk in model_response:
        if (
            isinstance(chunk, AIMessageChunk)
            and "reasoning_content" in chunk.additional_kwargs
        ):
            if isfirst:
                chunk.content = (
                    f"{think_tag[0]}{chunk.additional_kwargs['reasoning_content']}"
                )
                isfirst = False
            else:
                chunk.content = chunk.additional_kwargs["reasoning_content"]
        elif (
            isinstance(chunk, AIMessageChunk)
            and "reasoning_content" not in chunk.additional_kwargs
            and chunk.content
            and isend
        ):
            chunk.content = f"{think_tag[1]}{chunk.content}"
            isend = False
        yield chunk


async def aconvert_reasoning_content_for_chunk_iterator(
    model_response: AsyncIterator[BaseMessageChunk],
    think_tag: Tuple[str, str] = ("<think>", "</think>"),
) -> AsyncIterator[BaseMessageChunk]:
    """Async convert reasoning content for streaming response chunks.

    This is the async version of convert_reasoning_content_for_chunk_iterator.
    It processes async streaming response chunks and merges reasoning content
    into the visible content, wrapping it with the specified tags.

    Args:
        model_response: Async iterator of message chunks from streaming response
        think_tag: Tuple of (opening_tag, closing_tag) to wrap reasoning content

    Yields:
        BaseMessageChunk: Modified message chunks with reasoning content

    Example:
        Process async streaming response:
        >>> from langchain_dev_utils.message_convert import aconvert_reasoning_content_for_chunk_iterator
        >>> async for chunk in aconvert_reasoning_content_for_chunk_iterator(
        ...     model.astream("What is the capital of France?")
        ... ):
        ...     print(chunk.content, end="", flush=True)

        Custom tags for async streaming:
        >>> async for chunk in aconvert_reasoning_content_for_chunk_iterator(
        ...     model.astream("Explain quantum computing"),
        ...     think_tag=('<reasoning>', '</reasoning>')
        ... ):
        ...     print(chunk.content, end="", flush=True)
    """
    isfirst = True
    isend = True

    async for chunk in model_response:
        if (
            isinstance(chunk, AIMessageChunk)
            and "reasoning_content" in chunk.additional_kwargs
        ):
            if isfirst:
                chunk.content = (
                    f"{think_tag[0]}{chunk.additional_kwargs['reasoning_content']}"
                )
                isfirst = False
            else:
                chunk.content = chunk.additional_kwargs["reasoning_content"]
        elif (
            isinstance(chunk, AIMessageChunk)
            and "reasoning_content" not in chunk.additional_kwargs
            and chunk.content
            and isend
        ):
            chunk.content = f"{think_tag[1]}{chunk.content}"
            isend = False
        yield chunk


def merge_ai_message_chunk(chunks: Sequence[AIMessageChunk]) -> AIMessage:
    """Merge a sequence of AIMessageChunk into a single AIMessage.

    This function combines multiple message chunks into a single message,
    preserving the content and metadata while handling tool calls appropriately.

    Args:
        chunks: Sequence of AIMessageChunk to merge

    Returns:
        AIMessage: Merged AIMessage

    Example:
        Merge streaming chunks:
        >>> from langchain_dev_utils.message_convert import merge_ai_message_chunk
        >>> chunks = []
        >>> for chunk in model.stream("What is the capital of France?"):
        ...     chunks.append(chunk)
        >>> merged_message = merge_ai_message_chunk(chunks)
        >>> merged_message.content
    """
    ai_message_chunk = cast(AIMessageChunk, reduce(lambda x, y: x + y, chunks))
    ai_message_chunk.additional_kwargs.pop("tool_calls", None)

    data = {
        "id": ai_message_chunk.id,
        "content": ai_message_chunk.content,
        "response_metadata": ai_message_chunk.response_metadata,
        "additional_kwargs": ai_message_chunk.additional_kwargs,
    }
    if hasattr(ai_message_chunk, "tool_calls") and len(ai_message_chunk.tool_calls):
        data["tool_calls"] = ai_message_chunk.tool_calls
    return AIMessage.model_validate(data)
